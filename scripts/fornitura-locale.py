#!/usr/bin/env python3
"""Controlli settimanali sulla catena di fornitura, eseguiti in locale.

Sostituisce su questa macchina cio' che prima girava su GitHub Actions
(DECISIONS §6 «Catena di fornitura» e «Minuti di GitHub Actions»: i minuti
mensili di Actions sono limitati e sforarli blocca tutto). Solo libreria
standard piu' `git`, `gh`, `docker`. Tre controlli, indipendenti:

  osv        `scripts/osv-check.py` sul lockfile (vulnerabilita' note).
  digest     il digest di PostgreSQL fissato in `.github/workflows/ci.yml`
             contro quello attuale del tag (`docker buildx imagetools inspect`).
  lockfile   rigenera il lockfile alle ultime versioni (comando
             dell'intestazione del lockfile + `--upgrade`) in una cartella di
             lavoro ignorata da git; se cambia, apre un branch
             `impl/lockfile-AAAA-MM-GG` con il lockfile nuovo, lo pubblica e
             apre una PR con le differenze.

Un controllo fallito apre con `gh issue create --assignee <ASSEGNATARIO>` una
issue con titolo fisso per tipo. Se ce n'e' gia' una aperta con lo stesso
titolo e il contenuto e' cambiato, vi aggiunge un commento; se e' invariato non
fa nulla. Ogni controllo e' isolato: un'eccezione inattesa in uno diventa un
suo esito «errore» e non fa perdere le issue degli altri. `gh` parte sempre con
`-R <proprietario>/<repository>` ricavato dal remoto `origin`. Prima di scrivere
in una issue o in una PR si tolgono i pattern di credenziali dal testo.
Con `--prova` non si apre nessuna issue, nessun branch, nessun push, nessuna PR:
si legge e si riferisce soltanto.

A ogni esecuzione (anche fallita o di prova) si aggiunge una riga JSON a
`FILE_ESITI`, fuori dal repository: data, esito per controllo, versioni.
`--stato` stampa l'ultima esecuzione riuscita ed esce con errore se e' piu'
vecchia di `SOGLIA_ESECUZIONE_GIORNI` o se non ce n'e' nessuna.

Codici di uscita (somma bit a bit se piu' esiti insieme):
   0  tutto a posto, nessun aggiornamento
   1  vulnerabilita' note nel lockfile
   2  digest di PostgreSQL cambiato
   4  un controllo non e' riuscito (OSV non risponde, docker, ecc.)
   8  aggiornamento del lockfile non riuscito (pip-compile, git, gh)
  16  lockfile aggiornato: PR aperta (esito normale, non un guasto)
  32  non e' stato possibile aprire la issue di segnalazione

Uso: python3 scripts/fornitura-locale.py [--prova] [--solo osv,digest,lockfile]
                                         [--digest-attuale sha256:... (solo con --prova)]
     python3 scripts/fornitura-locale.py --stato
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

RADICE = Path(__file__).resolve().parent.parent

# --- Costanti dello strumento (DX-22: nessun valore nascosto nel codice) -----
# Destinatario delle issue: l'utente del progetto (decisione del 2026-11-05).
ASSEGNATARIO = "GravyaDev"
# Remoto e branch di partenza dell'aggiornamento: i merge in `main` si fanno in
# locale, `origin/main` e' cio' che GitHub conosce e su cui si apre la PR.
REMOTO = "origin"
BRANCH_PRINCIPALE = "main"
# Prefisso dei branch dell'aggiornamento (come i branch `impl/<nome>` di agenti.py).
PREFISSO_BRANCH_LOCKFILE = "impl/lockfile-"
# Data nel nome del branch: AAAA-MM-GG.
FORMATO_DATA = "%Y-%m-%d"
# Cartella di lavoro, ignorata da git (.gitignore): sorgente temporaneo e venv di pip-compile.
CARTELLA_LAVORO = ".fornitura-lavoro"
# File del repository letti o scritti.
LOCKFILE = "requirements.lock.txt"
# Strumenti del job (pip-tools e dipendenze), fissati con hash e installati con
# --require-hashes; anche questo file passa dal controllo OSV.
LOCKFILE_STRUMENTI = "requirements-strumenti.lock.txt"
LOCKFILE_CONTROLLATI = (LOCKFILE, LOCKFILE_STRUMENTI)
# File che, se `main` locale li ha cambiati senza push, rendono la base `origin/main` inaffidabile.
FILE_BASE_LOCKFILE = ("pyproject.toml", LOCKFILE, LOCKFILE_STRUMENTI)
WORKFLOW_CI = ".github/workflows/ci.yml"
SCRIPT_OSV = "scripts/osv-check.py"
# Strumento che genera il lockfile (nome del pacchetto PyPI): la versione e gli
# hash stanno in LOCKFILE_STRUMENTI. Il lockfile prodotto passa comunque dal
# controllo OSV e dalla CI prima del merge.
PACCHETTO_COMPILE = "pip-tools"
# Opzione che porta il lockfile alle ultime versioni.
OPZIONE_UPGRADE = "--upgrade"
# Tempi massimi: un comando appeso non deve bloccare il timer per sempre.
TIMEOUT_BREVE_SECONDI = 120
TIMEOUT_LUNGO_SECONDI = 1800
# Quante issue aperte leggere per cercare un titolo uguale.
LIMITE_ISSUE_LETTE = 200
# Quanti caratteri di output di un comando entrano nel corpo di una issue.
LIMITE_CORPO = 6000
# Identita' dei commit del branch del lockfile (la macchina puo' non averne una globale).
AUTORE_NOME = "Gravya fornitura locale"
AUTORE_EMAIL = "noreply@gravya.invalid"
# Titoli fissi delle issue, uno per tipo (servono anche a non duplicarle).
TITOLI = {
    "vulnerabilita": "Catena di fornitura: vulnerabilità note nel lockfile",
    "digest": "Catena di fornitura: il digest di PostgreSQL è cambiato",
    "controllo": "Catena di fornitura: un controllo non è riuscito",
    "aggiornamento": "Catena di fornitura: aggiornamento del lockfile non riuscito",
}
# Traccia delle esecuzioni: una riga JSON per esecuzione, fuori dal repository
# (fuori da git: non si pubblica per sbaglio e sopravvive ai worktree).
FILE_ESITI = Path.home() / ".local" / "state" / "gravya-fornitura" / "esiti.jsonl"
# Eta' massima dell'ultima esecuzione riuscita prima che `--stato` e
# `worktree-unisci` la considerino scaduta. Motivo: il timer e' settimanale
# (7 giorni) con Persistent=true; 2 giorni di margine coprono un riavvio di WSL2
# o un fine settimana a macchina spenta senza dare falsi allarmi; oltre, il
# controllo periodico non sta girando e nessuno se ne accorgerebbe.
SOGLIA_ESECUZIONE_GIORNI = 9
# Pattern di credenziali da togliere dal testo che va in una issue o in una PR.
PATTERN_CREDENZIALI = (
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{10,}"), "[token rimosso]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{10,}"), "[token rimosso]"),
    (re.compile(r"(https?://)[^/\s@]+@"), r"\1[credenziali rimosse]@"),
)
# Repository GitHub dal remoto: https o ssh, con o senza `.git`.
RE_REMOTO_GITHUB = re.compile(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+)/([\w.-]+?)(?:\.git)?/?")
# Codici di uscita.
OK = 0
VULNERABILITA = 1
DIGEST_CAMBIATO = 2
ERRORE_CONTROLLO = 4
ERRORE_AGGIORNAMENTO = 8
PR_APERTA = 16
ERRORE_ISSUE = 32
# Con `--stato`: nessuna esecuzione riuscita recente (non e' un bit dei controlli).
STATO_SCADUTO = 64
# Bit che indicano un controllo (o la segnalazione) non riuscito: l'esecuzione non e' «riuscita».
BIT_ERRORE = ERRORE_CONTROLLO | ERRORE_AGGIORNAMENTO | ERRORE_ISSUE
CONTROLLI = ("osv", "digest", "lockfile")

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def _testo(valore) -> str:
    """Testo anche per l'output parziale di un timeout, che subprocess da' come bytes."""
    if isinstance(valore, bytes):
        return valore.decode("utf-8", "replace")
    return valore or ""


def ripulisci(testo: str) -> str:
    """Toglie i pattern di credenziali prima che il testo esca (issue, PR, commenti)."""
    for regex, sostituto in PATTERN_CREDENZIALI:
        testo = regex.sub(sostituto, testo)
    return testo


def esegui(cmd: list[str], cwd: Path | None = None, timeout: int = TIMEOUT_BREVE_SECONDI) -> "subprocess.CompletedProcess[str]":
    """Esegue un comando senza mai sollevare: un guasto diventa returncode != 0."""
    try:
        return subprocess.run(cmd, cwd=cwd, text=True, errors="replace", capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as e:
        e.stdout, e.stderr = _testo(e.stdout), _testo(e.stderr)
        return subprocess.CompletedProcess(cmd, 124, e.stdout or "", f"tempo scaduto dopo {timeout} s: {e.stderr or ''}")
    except OSError as e:
        return subprocess.CompletedProcess(cmd, 127, "", f"comando non eseguibile: {e}")


def _carica_osv():
    spec = importlib.util.spec_from_file_location("osv_check", RADICE / SCRIPT_OSV)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@dataclass
class Esito:
    codice: int = OK
    # (tipo di issue, descrizione) per ogni problema da segnalare.
    problemi: list[tuple[str, str]] = field(default_factory=list)
    messaggi: list[str] = field(default_factory=list)
    # Per la traccia: versioni e valori rilevanti, e codice per controllo.
    versioni: dict[str, str] = field(default_factory=dict)
    per_controllo: dict[str, dict] = field(default_factory=dict)

    def aggiungi(self, altro: "Esito") -> None:
        self.codice |= altro.codice
        self.problemi += altro.problemi
        self.messaggi += altro.messaggi
        self.versioni.update(altro.versioni)
        self.per_controllo.update(altro.per_controllo)


def etichette(codice: int) -> list[str]:
    nomi = ((VULNERABILITA, "vulnerabilita"), (DIGEST_CAMBIATO, "digest_cambiato"), (ERRORE_CONTROLLO, "errore"),
            (ERRORE_AGGIORNAMENTO, "errore"), (PR_APERTA, "pr_aperta"), (ERRORE_ISSUE, "errore_issue"))
    trovate = []
    for bit, nome in nomi:
        if codice & bit and nome not in trovate:
            trovate.append(nome)
    return trovate or ["ok"]


def _coda(testo: str) -> str:
    testo = ripulisci((testo or "").strip())
    return testo if len(testo) <= LIMITE_CORPO else "[...]\n" + testo[-LIMITE_CORPO:]


# --- Controllo 1: OSV ---------------------------------------------------------

def controlla_osv(radice: Path, run: Runner = esegui, lockfile: str = LOCKFILE) -> Esito:
    r = run([sys.executable, str(radice / SCRIPT_OSV), str(radice / lockfile)], timeout=TIMEOUT_LUNGO_SECONDI)
    uscita = _testo(r.stdout) + _testo(r.stderr)
    if r.returncode == 0:
        return Esito(OK, messaggi=[f"osv: {uscita.strip()}"])
    if r.returncode == 1:
        return Esito(VULNERABILITA, [("vulnerabilita", f"{lockfile}:\n{_coda(uscita)}")], [f"osv: {lockfile}: VULNERABILITA' NOTE"])
    return Esito(ERRORE_CONTROLLO, [("controllo", "Controllo OSV non riuscito "
                                     f"({lockfile}, codice {r.returncode}).\n\n{_coda(uscita)}")], [f"osv: {lockfile}: ERRORE"])


def controlla_osv_tutti(radice: Path, run: Runner = esegui) -> Esito:
    """OSV su ogni lockfile controllato; il fallimento di uno non salta gli altri."""
    totale = Esito()
    for lockfile in LOCKFILE_CONTROLLATI:
        totale.aggiungi(controlla_osv(radice, run, lockfile))
    return totale


# --- Controllo 2: digest di PostgreSQL -----------------------------------------

class ErroreDigest(Exception):
    pass


def digest_fissato(testo_ci: str) -> tuple[str, str]:
    """(tag, digest) dell'unica immagine postgres fissata per digest in ci.yml."""
    righe = set(re.findall(r"^\s*image:\s*(postgres:[^@\s]+@sha256:[0-9a-f]{64})\s*$", testo_ci, re.M))
    if len(righe) != 1:
        raise ErroreDigest(f"in {WORKFLOW_CI} deve esserci una sola immagine postgres fissata per digest; "
                           f"trovate: {', '.join(sorted(righe)) or 'nessuna'}")
    tag, digest = righe.pop().split("@")
    return tag, digest


def digest_attuale(tag: str, run: Runner = esegui) -> str:
    r = run(["docker", "buildx", "imagetools", "inspect", tag, "--format", "{{.Manifest.Digest}}"])
    attuale = _testo(r.stdout).strip()
    if r.returncode != 0 or not re.fullmatch(r"sha256:[0-9a-f]{64}", attuale):
        raise ErroreDigest(f"digest attuale di {tag} non ottenuto (codice {r.returncode}): {_coda(_testo(r.stderr) + attuale)}")
    return attuale


def controlla_digest(radice: Path, run: Runner = esegui, attuale: str | None = None) -> Esito:
    """`attuale` permette di provare il confronto su un digest diverso senza rete."""
    try:
        tag, fissato = digest_fissato((radice / WORKFLOW_CI).read_text(encoding="utf-8"))
        ora = attuale if attuale is not None else digest_attuale(tag, run)
    except (ErroreDigest, OSError) as e:
        return Esito(ERRORE_CONTROLLO, [("controllo", f"Confronto del digest non riuscito: {e}")], ["digest: ERRORE"])
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ora):
        return Esito(ERRORE_CONTROLLO, [("controllo", f"Digest attuale non valido: {ora!r}")], ["digest: ERRORE"])
    if ora != fissato:
        return Esito(DIGEST_CAMBIATO, [("digest", (
            f"Il digest di `{tag}` è cambiato.\n\n- fissato in `{WORKFLOW_CI}`: `{fissato}`\n- attuale: `{ora}`\n\n"
            f"Provare la CI con la nuova immagine e aggiornare la riga `image:` dei servizi in `{WORKFLOW_CI}`."))],
            [f"digest: CAMBIATO ({fissato} -> {ora})"])
    return Esito(OK, messaggi=[f"digest: OK, {tag} è ancora {fissato}"], versioni={tag: ora})


# --- Controllo 3: lockfile alle ultime versioni ----------------------------------

class ErroreAggiornamento(Exception):
    pass


class ErroreRepository(ErroreAggiornamento):
    """Il remoto `origin` non indica un repository GitHub riconoscibile."""


def repo_github(radice: Path, run: Runner = esegui) -> str:
    """`proprietario/repository` dal remoto `origin`, per `gh -R` (mai dalla cartella di lancio)."""
    r = run(["git", "-C", str(radice), "remote", "get-url", REMOTO])
    if r.returncode != 0:
        raise ErroreRepository(f"remoto {REMOTO} non leggibile: {_coda(r.stderr)}")
    m = RE_REMOTO_GITHUB.fullmatch(_testo(r.stdout).strip())
    if not m:
        raise ErroreRepository(f"il remoto {REMOTO} non è un repository GitHub riconoscibile (https o ssh senza credenziali)")
    return f"{m.group(1)}/{m.group(2)}"


def versione_strumenti(radice: Path) -> str:
    """Versione di pip-tools fissata in LOCKFILE_STRUMENTI (per la traccia), o «sconosciuta»."""
    try:
        testo = (radice / LOCKFILE_STRUMENTI).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return "sconosciuta"
    m = re.search(rf"^{re.escape(PACCHETTO_COMPILE)}==(\S+)", testo, re.M)
    return m.group(1) if m else "sconosciuta"


def comando_compile(testo_lockfile: str) -> list[str]:
    """Argomenti di pip-compile presi dall'intestazione del lockfile, piu' --upgrade."""
    m = re.search(r"^#\s+pip-compile\s+(.+)$", testo_lockfile, re.M)
    if not m:
        raise ErroreAggiornamento(f"intestazione di {LOCKFILE} senza il comando pip-compile")
    argomenti = shlex.split(m.group(1))
    if OPZIONE_UPGRADE not in argomenti:
        argomenti.insert(0, OPZIONE_UPGRADE)
    return argomenti


def differenze(vecchio: str, nuovo: str) -> list[str]:
    """Righe leggibili `nome: a -> b`, `+ nome b`, `- nome a` tra due lockfile."""
    osv = _carica_osv()
    a, b = dict(osv.leggi_lockfile(vecchio)), dict(osv.leggi_lockfile(nuovo))
    out = []
    for nome in sorted(set(a) | set(b)):
        if nome not in b:
            out.append(f"- {nome} {a[nome]} (rimosso)")
        elif nome not in a:
            out.append(f"+ {nome} {b[nome]} (nuovo)")
        elif a[nome] != b[nome]:
            out.append(f"~ {nome}: {a[nome]} -> {b[nome]}")
    return out


def compila_con_pip_tools(sorgente: Path, lavoro: Path, argomenti: list[str], run: Runner = esegui,
                          radice: Path = RADICE) -> None:
    """Venv di lavoro (cache nella cartella ignorata) con pip-tools fissato e verificato per hash, poi pip-compile nel sorgente."""
    interprete = radice / ".venv" / "bin" / "python"
    if not interprete.is_file():
        raise ErroreAggiornamento(f"manca l'interprete del progetto ({interprete.relative_to(radice)})")
    requisiti = radice / LOCKFILE_STRUMENTI
    if not requisiti.is_file():
        raise ErroreAggiornamento(f"manca {LOCKFILE_STRUMENTI}: pip-tools non si installa senza versioni e hash fissati")
    venv = lavoro / "venv-compile"
    py = venv / "bin" / "python"
    if not py.is_file():
        r = run([str(interprete), "-m", "venv", str(venv)], timeout=TIMEOUT_LUNGO_SECONDI)
        if r.returncode != 0:
            raise ErroreAggiornamento(f"venv di lavoro non creata: {_coda(r.stderr)}")
    r = run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", "--require-hashes", "-r", str(requisiti)],
            timeout=TIMEOUT_LUNGO_SECONDI)
    if r.returncode != 0:
        raise ErroreAggiornamento(f"installazione di {PACCHETTO_COMPILE} non riuscita: {_coda(r.stderr)}")
    r = run([str(py), "-m", "piptools", "compile", *argomenti], cwd=sorgente, timeout=TIMEOUT_LUNGO_SECONDI)
    if r.returncode != 0:
        raise ErroreAggiornamento(f"pip-compile non riuscito (codice {r.returncode}): {_coda(r.stderr)}")


def _git(run: Runner, cwd: Path, *args: str, timeout: int = TIMEOUT_BREVE_SECONDI):
    r = run(["git", "-C", str(cwd), *args], timeout=timeout)
    if r.returncode != 0:
        raise ErroreAggiornamento(f"git {' '.join(args[:2])} non riuscito: {_coda(r.stderr)}")
    return r


def aggiorna_lockfile(
    radice: Path,
    run: Runner = esegui,
    prova: bool = False,
    oggi: dt.date | None = None,
    compila: Callable[[Path, Path, list[str]], None] | None = None,
) -> Esito:
    """Rigenera il lockfile su `origin/main`; se cambia, branch + push + PR (salvo `prova`).

    Se `main` locale ha commit non pubblicati su pyproject.toml o sui lockfile, la base
    `origin/main` sarebbe vecchia: nessuna PR, esito «errore» con la spiegazione."""
    oggi = oggi or dt.date.today()
    lavoro = radice / CARTELLA_LAVORO
    sorgente = lavoro / "sorgente"
    branch = PREFISSO_BRANCH_LOCKFILE + oggi.strftime(FORMATO_DATA)
    base = f"{REMOTO}/{BRANCH_PRINCIPALE}"
    compila = compila or (lambda s, l, a: compila_con_pip_tools(s, l, a, run, radice))
    creato = False
    try:
        lavoro.mkdir(exist_ok=True)
        if sorgente.exists():  # residuo di un'esecuzione interrotta
            run(["git", "-C", str(radice), "worktree", "remove", "--force", str(sorgente)])
            shutil.rmtree(sorgente, ignore_errors=True)
            run(["git", "-C", str(radice), "worktree", "prune"])
        _git(run, radice, "fetch", REMOTO, BRANCH_PRINCIPALE, timeout=TIMEOUT_LUNGO_SECONDI)
        locali = _git(run, radice, "log", "--format=%h %s", f"{base}..{BRANCH_PRINCIPALE}", "--", *FILE_BASE_LOCKFILE)
        if _testo(locali.stdout).strip():
            raise ErroreAggiornamento(
                f"{BRANCH_PRINCIPALE} locale ha commit non pubblicati che toccano {', '.join(FILE_BASE_LOCKFILE)}: "
                f"rigenerare su {base} ignorerebbe o scontrerebbe quel lavoro. Pubblicare {BRANCH_PRINCIPALE} "
                f"(push) e rieseguire; nessuna PR aperta.\n\n{_coda(locali.stdout)}")
        _git(run, radice, "worktree", "add", "--detach", str(sorgente), base)
        creato = True
        vecchio = (sorgente / LOCKFILE).read_text(encoding="utf-8")
        compila(sorgente, lavoro, comando_compile(vecchio))
        nuovo = (sorgente / LOCKFILE).read_text(encoding="utf-8")
        elenco = differenze(vecchio, nuovo)
        if not elenco:
            # Contano solo i pacchetti: l'intestazione (versione di pip-tools) non e' un aggiornamento.
            return Esito(OK, messaggi=["lockfile: già alle ultime versioni, nessun cambiamento"],
                         versioni={PACCHETTO_COMPILE: versione_strumenti(radice)})
        corpo = ripulisci("Il lockfile rigenerato alle ultime versioni (`pip-compile --upgrade`, comando dell'intestazione) "
                 f"è diverso da `{base}`:\n\n" + "\n".join(f"- `{r}`" for r in elenco) +
                 "\n\nPrima del merge: `python3 scripts/agenti.py worktree-unisci` esegue OSV e la suite. "
                 "Generata da `scripts/fornitura-locale.py`.")
        titolo = f"Aggiornamento del lockfile alle ultime versioni ({oggi.strftime(FORMATO_DATA)})"
        versioni = {PACCHETTO_COMPILE: versione_strumenti(radice), "pacchetti_cambiati": str(len(elenco))}
        if prova:
            return Esito(OK, messaggi=[f"lockfile: AGGIORNAMENTO POSSIBILE ({len(elenco)} pacchetti), prova: nessun branch né PR"]
                         + [f"  {r}" for r in elenco], versioni=versioni)
        repo = repo_github(radice, run)
        aperte = run(["gh", "pr", "list", "-R", repo, "--state", "open", "--limit", str(LIMITE_ISSUE_LETTE), "--json", "headRefName"])
        if aperte.returncode != 0:
            raise ErroreAggiornamento(f"elenco delle PR non ottenuto: {_coda(aperte.stderr)}")
        if PREFISSO_BRANCH_LOCKFILE in _testo(aperte.stdout):
            return Esito(OK, messaggi=["lockfile: aggiornamento disponibile ma c'è già una PR aperta di lockfile, non ne apro un'altra"],
                         versioni=versioni)
        if run(["git", "-C", str(radice), "rev-parse", "--verify", "--quiet", branch]).returncode == 0:
            raise ErroreAggiornamento(f"il branch {branch} esiste già in locale: da chiudere prima")
        _git(run, sorgente, "switch", "-c", branch)
        _git(run, sorgente, "add", LOCKFILE)
        _git(run, sorgente, "-c", f"user.name={AUTORE_NOME}", "-c", f"user.email={AUTORE_EMAIL}", "commit", "-q",
             "-m", titolo, "-m", "Rigenerazione con pip-compile --upgrade (scripts/fornitura-locale.py).")
        _git(run, sorgente, "push", REMOTO, branch, timeout=TIMEOUT_LUNGO_SECONDI)
        r = run(["gh", "pr", "create", "-R", repo, "--base", BRANCH_PRINCIPALE, "--head", branch, "--title", titolo, "--body", corpo],
                cwd=sorgente, timeout=TIMEOUT_LUNGO_SECONDI)
        if r.returncode != 0:
            raise ErroreAggiornamento(f"gh pr create non riuscito: {_coda(r.stderr)}")
        return Esito(PR_APERTA, messaggi=[f"lockfile: PR aperta dal branch {branch}: {_testo(r.stdout).strip()}"], versioni=versioni)
    except (ErroreAggiornamento, OSError, ValueError) as e:
        return Esito(ERRORE_AGGIORNAMENTO, [("aggiornamento", f"Aggiornamento del lockfile non riuscito: {_coda(str(e))}")],
                     ["lockfile: ERRORE"])
    finally:
        if creato:
            run(["git", "-C", str(radice), "worktree", "remove", "--force", str(sorgente)])
        run(["git", "-C", str(radice), "worktree", "prune"])


# --- Segnalazione -------------------------------------------------------------------

def _normalizza(testo: str) -> str:
    return (testo or "").replace("\r\n", "\n").strip()


def segnala(problemi: list[tuple[str, str]], run: Runner = esegui, prova: bool = False,
            radice: Path = RADICE) -> tuple[int, list[str]]:
    """Una issue per tipo. Se ce n'e' gia' una aperta con lo stesso titolo: commento col nuovo
    contenuto se e' cambiato, niente se e' invariato (l'ultimo contenuto noto e' l'ultimo commento,
    o il corpo se non ce ne sono)."""
    if not problemi or prova:
        return OK, [f"prova: issue non aperta ({TITOLI[t]})" for t, _ in problemi] if prova else []
    messaggi: list[str] = []
    codice = OK
    try:
        repo = repo_github(radice, run)
    except ErroreRepository as e:
        return ERRORE_ISSUE, [f"issue: repository non determinabile, nessuna issue aperta: {e}"]
    r = run(["gh", "issue", "list", "-R", repo, "--state", "open", "--limit", str(LIMITE_ISSUE_LETTE),
             "--json", "number,title,body,comments"])
    if r.returncode != 0:
        return ERRORE_ISSUE, [f"issue: elenco non ottenuto, nessuna issue aperta: {_coda(r.stderr)}"]
    try:
        elenco = json.loads(_testo(r.stdout) or "[]")
        aperti = {i["title"]: i for i in elenco}
    except (ValueError, TypeError, KeyError) as e:
        return ERRORE_ISSUE, [f"issue: elenco non leggibile ({type(e).__name__}), nessuna issue aperta"]
    if len(elenco) >= LIMITE_ISSUE_LETTE:
        return ERRORE_ISSUE, [f"issue: lette {len(elenco)} issue aperte (limite): l'elenco può essere troncato, nessuna issue aperta"]
    per_tipo: dict[str, list[str]] = {}
    for tipo, testo in problemi:
        per_tipo.setdefault(tipo, []).append(testo)
    for tipo, testi in per_tipo.items():
        titolo = TITOLI[tipo]
        corpo = ripulisci("\n\n".join(testi))
        if titolo in aperti:
            esistente = aperti[titolo]
            commenti = esistente.get("comments") or []
            ultimo = commenti[-1].get("body") if commenti else esistente.get("body")
            if _normalizza(ultimo) == _normalizza(corpo):
                messaggi.append(f"issue: già aperta, non duplicata ({titolo})")
                continue
            k = run(["gh", "issue", "comment", str(esistente.get("number")), "-R", repo, "--body", corpo])
            if k.returncode != 0:
                codice |= ERRORE_ISSUE
                messaggi.append(f"issue: commento non riuscito ({titolo}): {_coda(k.stderr)}")
            else:
                messaggi.append(f"issue: già aperta, contenuto cambiato: aggiunto un commento ({titolo})")
            continue
        c = run(["gh", "issue", "create", "-R", repo, "--title", titolo, "--body", corpo, "--assignee", ASSEGNATARIO])
        if c.returncode != 0:
            codice |= ERRORE_ISSUE
            messaggi.append(f"issue: apertura non riuscita ({titolo}): {_coda(c.stderr)}")
        else:
            messaggi.append(f"issue: aperta ({titolo}) {_testo(c.stdout).strip()}")
    return codice, messaggi


# --- Controlli isolati e traccia ----------------------------------------------------

def _isola(nome: str, funzione: Callable[[], Esito]) -> Esito:
    """Un'eccezione non prevista in un controllo e' il suo esito «errore» (con la sua issue):
    mai una traceback che faccia perdere le issue degli altri controlli."""
    try:
        e = funzione()
    except Exception as exc:  # noqa: BLE001 - il punto e' proprio non lasciarne passare nessuna
        dettaglio = _coda(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        if nome == "lockfile":
            e = Esito(ERRORE_AGGIORNAMENTO, [("aggiornamento", f"Aggiornamento del lockfile: eccezione inattesa.\n\n{dettaglio}")],
                      ["lockfile: ERRORE (eccezione inattesa)"])
        else:
            e = Esito(ERRORE_CONTROLLO, [("controllo", f"Controllo «{nome}»: eccezione inattesa.\n\n{dettaglio}")],
                      [f"{nome}: ERRORE (eccezione inattesa)"])
    e.per_controllo[nome] = {"codice": e.codice, "esito": etichette(e.codice)}
    return e


def esegui_controlli(radice: Path, quali: tuple[str, ...], prova: bool, run: Runner = esegui,
                     digest: str | None = None, **opzioni) -> Esito:
    passi: dict[str, Callable[[], Esito]] = {
        "osv": lambda: controlla_osv_tutti(radice, run),
        "digest": lambda: controlla_digest(radice, run, digest),
        "lockfile": lambda: aggiorna_lockfile(radice, run, prova, **opzioni),
    }
    totale = Esito()
    for nome in CONTROLLI:
        if nome in quali:
            totale.aggiungi(_isola(nome, passi[nome]))
    try:
        codice, messaggi = segnala(totale.problemi, run, prova, radice)
    except Exception as exc:  # noqa: BLE001
        codice, messaggi = ERRORE_ISSUE, [f"issue: eccezione inattesa nella segnalazione ({type(exc).__name__}): {_coda(str(exc))}"]
    totale.codice |= codice
    totale.messaggi += messaggi
    totale.versioni["python"] = platform.python_version()
    return totale


def _adesso() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def registra(esito: Esito, quali: tuple[str, ...], prova: bool, percorso: Path = FILE_ESITI,
             ora: dt.datetime | None = None) -> None:
    """Aggiunge una riga JSON alla traccia: data, esito per controllo, versioni. Solleva OSError se non scrive."""
    riga = {"data": (ora or _adesso()).isoformat(timespec="seconds"), "prova": prova, "controlli": list(quali),
            "codice": esito.codice, "esiti": esito.per_controllo, "versioni": esito.versioni}
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with percorso.open("a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def leggi_esecuzioni(percorso: Path = FILE_ESITI) -> list[dict]:
    """Righe valide della traccia, in ordine; file mancante = nessuna esecuzione; righe corrotte saltate."""
    try:
        testo = percorso.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return []
    righe = []
    for r in testo.splitlines():
        try:
            d = json.loads(r)
            dt.datetime.fromisoformat(d["data"])
            righe.append(d)
        except (ValueError, TypeError, KeyError):
            continue
    return righe


def e_riuscita(riga: dict) -> bool:
    """Riuscita = esecuzione vera (non di prova) di TUTTI i controlli, nessuno in errore.
    Trovare vulnerabilita' non e' un fallimento del controllo: il controllo ha girato."""
    esiti = riga.get("esiti")
    if riga.get("prova") or not isinstance(esiti, dict) or not all(c in esiti for c in CONTROLLI):
        return False
    return all(isinstance(esiti[c], dict) and isinstance(esiti[c].get("codice"), int) and not esiti[c]["codice"] & BIT_ERRORE
               for c in CONTROLLI) and isinstance(riga.get("codice"), int) and not riga["codice"] & BIT_ERRORE


def ultima_riuscita(percorso: Path = FILE_ESITI) -> dict | None:
    riuscite = [r for r in leggi_esecuzioni(percorso) if e_riuscita(r)]
    return max(riuscite, key=lambda r: dt.datetime.fromisoformat(r["data"])) if riuscite else None


def stato(percorso: Path = FILE_ESITI, ora: dt.datetime | None = None) -> tuple[int, list[str]]:
    """(codice, righe): STATO_SCADUTO se non c'e' un'esecuzione riuscita o e' piu' vecchia della soglia."""
    ora = ora or _adesso()
    righe = []
    esecuzioni = leggi_esecuzioni(percorso)
    if esecuzioni:
        u = esecuzioni[-1]
        righe.append(f"ultima esecuzione: {u['data']} ({'prova, ' if u.get('prova') else ''}codice {u.get('codice')}, "
                     f"{'riuscita' if e_riuscita(u) else 'NON riuscita'})")
    riuscita = ultima_riuscita(percorso)
    if riuscita is None:
        return STATO_SCADUTO, righe + [f"ATTENZIONE: nessuna esecuzione riuscita registrata in {percorso}: il controllo settimanale non sta girando"]
    eta = ora - dt.datetime.fromisoformat(riuscita["data"])
    giorni = eta.total_seconds() / 86400
    righe.append(f"ultima esecuzione riuscita: {riuscita['data']} ({giorni:.1f} giorni fa; soglia {SOGLIA_ESECUZIONE_GIORNI}); "
                 f"esiti: " + ", ".join(f"{c}={'+'.join(riuscita['esiti'][c]['esito'])}" for c in CONTROLLI))
    if giorni > SOGLIA_ESECUZIONE_GIORNI:
        return STATO_SCADUTO, righe + [f"ATTENZIONE: l'ultimo controllo riuscito ha più di {SOGLIA_ESECUZIONE_GIORNI} giorni: "
                                       f"verificare il timer (systemctl --user list-timers gravya-fornitura.timer)"]
    return OK, righe


def main(argv: list[str] | None = None, run: Runner = esegui, traccia: Path = FILE_ESITI,
         radice: Path = RADICE, ora: dt.datetime | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prova", action="store_true", help="non apre issue, branch, push né PR: riferisce soltanto")
    p.add_argument("--solo", default=",".join(CONTROLLI), help="controlli da eseguire, separati da virgola (osv,digest,lockfile)")
    p.add_argument("--digest-attuale", help="solo con --prova: usa questo digest al posto di quello letto da docker (prova del ramo «cambiato»)")
    p.add_argument("--stato", action="store_true", help="stampa l'ultima esecuzione riuscita; errore se più vecchia della soglia")
    a = p.parse_args(argv)
    if a.stato:
        codice, righe = stato(traccia, ora)
        print("\n".join(righe))
        return codice
    if a.digest_attuale is not None and not a.prova:
        print("ERRORE: --digest-attuale si usa solo con --prova (altrimenti si aprirebbe una issue su un digest inventato)", file=sys.stderr)
        return ERRORE_CONTROLLO
    quali = tuple(x.strip() for x in a.solo.split(",") if x.strip())
    sconosciuti = set(quali) - set(CONTROLLI)
    if sconosciuti or not quali:
        print(f"ERRORE: controlli non validi: {', '.join(sorted(sconosciuti)) or '(nessuno)'}; ammessi: {', '.join(CONTROLLI)}", file=sys.stderr)
        return ERRORE_CONTROLLO
    esito = esegui_controlli(radice, quali, a.prova, run, digest=a.digest_attuale)
    try:
        registra(esito, quali, a.prova, traccia, ora)
    except OSError as e:
        esito.codice |= ERRORE_CONTROLLO
        esito.messaggi.append(f"traccia: riga non scritta in {traccia}: {e}")
    for m in esito.messaggi:
        print(m)
    print(f"uscita: {esito.codice}")
    return esito.codice


if __name__ == "__main__":
    sys.exit(main())
