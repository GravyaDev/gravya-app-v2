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
issue con titolo fisso per tipo, senza duplicarla se ce n'e' gia' una aperta
con lo stesso titolo. Con `--prova` non si apre nessuna issue, nessun branch,
nessun push, nessuna PR: si legge e si riferisce soltanto.

Codici di uscita (somma bit a bit se piu' esiti insieme):
   0  tutto a posto, nessun aggiornamento
   1  vulnerabilita' note nel lockfile
   2  digest di PostgreSQL cambiato
   4  un controllo non e' riuscito (OSV non risponde, docker, ecc.)
   8  aggiornamento del lockfile non riuscito (pip-compile, git, gh)
  16  lockfile aggiornato: PR aperta (esito normale, non un guasto)
  32  non e' stato possibile aprire la issue di segnalazione

Uso: python3 scripts/fornitura-locale.py [--prova] [--solo osv,digest,lockfile]
                                         [--digest-attuale sha256:...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import re
import shlex
import shutil
import subprocess
import sys
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
WORKFLOW_CI = ".github/workflows/ci.yml"
SCRIPT_OSV = "scripts/osv-check.py"
# Strumento che genera il lockfile (nome del pacchetto PyPI): non e' nel
# lockfile, lo scarica la venv di lavoro. Il lockfile prodotto passa comunque
# dal controllo OSV e dalla CI prima del merge.
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
# Codici di uscita.
OK = 0
VULNERABILITA = 1
DIGEST_CAMBIATO = 2
ERRORE_CONTROLLO = 4
ERRORE_AGGIORNAMENTO = 8
PR_APERTA = 16
ERRORE_ISSUE = 32
CONTROLLI = ("osv", "digest", "lockfile")

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def esegui(cmd: list[str], cwd: Path | None = None, timeout: int = TIMEOUT_BREVE_SECONDI) -> "subprocess.CompletedProcess[str]":
    """Esegue un comando senza mai sollevare: un guasto diventa returncode != 0."""
    try:
        return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as e:
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

    def aggiungi(self, altro: "Esito") -> None:
        self.codice |= altro.codice
        self.problemi += altro.problemi
        self.messaggi += altro.messaggi


def _coda(testo: str) -> str:
    testo = (testo or "").strip()
    return testo if len(testo) <= LIMITE_CORPO else "[...]\n" + testo[-LIMITE_CORPO:]


# --- Controllo 1: OSV ---------------------------------------------------------

def controlla_osv(radice: Path, run: Runner = esegui) -> Esito:
    r = run([sys.executable, str(radice / SCRIPT_OSV), str(radice / LOCKFILE)], timeout=TIMEOUT_LUNGO_SECONDI)
    uscita = (r.stdout or "") + (r.stderr or "")
    if r.returncode == 0:
        return Esito(OK, messaggi=[f"osv: {uscita.strip()}"])
    if r.returncode == 1:
        return Esito(VULNERABILITA, [("vulnerabilita", _coda(uscita))], ["osv: VULNERABILITA' NOTE"])
    return Esito(ERRORE_CONTROLLO, [("controllo", "Controllo OSV non riuscito (codice "
                                     f"{r.returncode}).\n\n{_coda(uscita)}")], ["osv: ERRORE"])


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
    attuale = (r.stdout or "").strip()
    if r.returncode != 0 or not re.fullmatch(r"sha256:[0-9a-f]{64}", attuale):
        raise ErroreDigest(f"digest attuale di {tag} non ottenuto (codice {r.returncode}): {_coda((r.stderr or '') + attuale)}")
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
    return Esito(OK, messaggi=[f"digest: OK, {tag} è ancora {fissato}"])


# --- Controllo 3: lockfile alle ultime versioni ----------------------------------

class ErroreAggiornamento(Exception):
    pass


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


def compila_con_pip_tools(sorgente: Path, lavoro: Path, argomenti: list[str], run: Runner = esegui) -> None:
    """Venv di lavoro (cache nella cartella ignorata) con pip-tools, poi pip-compile nel sorgente."""
    interprete = RADICE / ".venv" / "bin" / "python"
    if not interprete.is_file():
        raise ErroreAggiornamento(f"manca l'interprete del progetto ({interprete.relative_to(RADICE)})")
    venv = lavoro / "venv-compile"
    py = venv / "bin" / "python"
    if not py.is_file():
        r = run([str(interprete), "-m", "venv", str(venv)], timeout=TIMEOUT_LUNGO_SECONDI)
        if r.returncode != 0:
            raise ErroreAggiornamento(f"venv di lavoro non creata: {_coda(r.stderr)}")
    r = run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", OPZIONE_UPGRADE, PACCHETTO_COMPILE],
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
    """Rigenera il lockfile su `origin/main`; se cambia, branch + push + PR (salvo `prova`)."""
    oggi = oggi or dt.date.today()
    lavoro = radice / CARTELLA_LAVORO
    sorgente = lavoro / "sorgente"
    branch = PREFISSO_BRANCH_LOCKFILE + oggi.strftime(FORMATO_DATA)
    base = f"{REMOTO}/{BRANCH_PRINCIPALE}"
    compila = compila or (lambda s, l, a: compila_con_pip_tools(s, l, a, run))
    creato = False
    try:
        lavoro.mkdir(exist_ok=True)
        if sorgente.exists():  # residuo di un'esecuzione interrotta
            run(["git", "-C", str(radice), "worktree", "remove", "--force", str(sorgente)])
            shutil.rmtree(sorgente, ignore_errors=True)
            run(["git", "-C", str(radice), "worktree", "prune"])
        _git(run, radice, "fetch", REMOTO, BRANCH_PRINCIPALE, timeout=TIMEOUT_LUNGO_SECONDI)
        _git(run, radice, "worktree", "add", "--detach", str(sorgente), base)
        creato = True
        vecchio = (sorgente / LOCKFILE).read_text(encoding="utf-8")
        compila(sorgente, lavoro, comando_compile(vecchio))
        nuovo = (sorgente / LOCKFILE).read_text(encoding="utf-8")
        elenco = differenze(vecchio, nuovo)
        if not elenco:
            # Contano solo i pacchetti: l'intestazione (versione di pip-tools) non e' un aggiornamento.
            return Esito(OK, messaggi=["lockfile: già alle ultime versioni, nessun cambiamento"])
        corpo = ("Il lockfile rigenerato alle ultime versioni (`pip-compile --upgrade`, comando dell'intestazione) "
                 f"è diverso da `{base}`:\n\n" + "\n".join(f"- `{r}`" for r in elenco) +
                 "\n\nPrima del merge: `python3 scripts/agenti.py worktree-unisci` esegue OSV e la suite. "
                 "Generata da `scripts/fornitura-locale.py`.")
        titolo = f"Aggiornamento del lockfile alle ultime versioni ({oggi.strftime(FORMATO_DATA)})"
        if prova:
            return Esito(OK, messaggi=[f"lockfile: AGGIORNAMENTO POSSIBILE ({len(elenco)} pacchetti), prova: nessun branch né PR"]
                         + [f"  {r}" for r in elenco])
        aperte = run(["gh", "pr", "list", "--state", "open", "--limit", str(LIMITE_ISSUE_LETTE), "--json", "headRefName"])
        if aperte.returncode != 0:
            raise ErroreAggiornamento(f"elenco delle PR non ottenuto: {_coda(aperte.stderr)}")
        if PREFISSO_BRANCH_LOCKFILE in (aperte.stdout or ""):
            return Esito(OK, messaggi=["lockfile: aggiornamento disponibile ma c'è già una PR aperta di lockfile, non ne apro un'altra"])
        if run(["git", "-C", str(radice), "rev-parse", "--verify", "--quiet", branch]).returncode == 0:
            raise ErroreAggiornamento(f"il branch {branch} esiste già in locale: da chiudere prima")
        _git(run, sorgente, "switch", "-c", branch)
        _git(run, sorgente, "add", LOCKFILE)
        _git(run, sorgente, "-c", f"user.name={AUTORE_NOME}", "-c", f"user.email={AUTORE_EMAIL}", "commit", "-q",
             "-m", titolo, "-m", "Rigenerazione con pip-compile --upgrade (scripts/fornitura-locale.py).")
        _git(run, sorgente, "push", REMOTO, branch, timeout=TIMEOUT_LUNGO_SECONDI)
        r = run(["gh", "pr", "create", "--base", BRANCH_PRINCIPALE, "--head", branch, "--title", titolo, "--body", corpo],
                cwd=sorgente, timeout=TIMEOUT_LUNGO_SECONDI)
        if r.returncode != 0:
            raise ErroreAggiornamento(f"gh pr create non riuscito: {_coda(r.stderr)}")
        return Esito(PR_APERTA, messaggi=[f"lockfile: PR aperta dal branch {branch}: {(r.stdout or '').strip()}"])
    except (ErroreAggiornamento, OSError) as e:
        return Esito(ERRORE_AGGIORNAMENTO, [("aggiornamento", f"Aggiornamento del lockfile non riuscito: {e}")],
                     ["lockfile: ERRORE"])
    finally:
        if creato:
            run(["git", "-C", str(radice), "worktree", "remove", "--force", str(sorgente)])
        run(["git", "-C", str(radice), "worktree", "prune"])


# --- Segnalazione -------------------------------------------------------------------

def segnala(problemi: list[tuple[str, str]], run: Runner = esegui, prova: bool = False) -> tuple[int, list[str]]:
    """Una issue per tipo, senza duplicati con lo stesso titolo ancora aperto."""
    if not problemi or prova:
        return OK, [f"prova: issue non aperta ({TITOLI[t]})" for t, _ in problemi] if prova else []
    messaggi: list[str] = []
    codice = OK
    r = run(["gh", "issue", "list", "--state", "open", "--limit", str(LIMITE_ISSUE_LETTE), "--json", "title", "--jq", ".[].title"])
    if r.returncode != 0:
        return ERRORE_ISSUE, [f"issue: elenco non ottenuto, nessuna issue aperta: {_coda(r.stderr)}"]
    aperti = set((r.stdout or "").splitlines())
    per_tipo: dict[str, list[str]] = {}
    for tipo, testo in problemi:
        per_tipo.setdefault(tipo, []).append(testo)
    for tipo, testi in per_tipo.items():
        titolo = TITOLI[tipo]
        if titolo in aperti:
            messaggi.append(f"issue: già aperta, non duplicata ({titolo})")
            continue
        c = run(["gh", "issue", "create", "--title", titolo, "--body", "\n\n".join(testi), "--assignee", ASSEGNATARIO])
        if c.returncode != 0:
            codice |= ERRORE_ISSUE
            messaggi.append(f"issue: apertura non riuscita ({titolo}): {_coda(c.stderr)}")
        else:
            messaggi.append(f"issue: aperta ({titolo}) {(c.stdout or '').strip()}")
    return codice, messaggi


def esegui_controlli(radice: Path, quali: tuple[str, ...], prova: bool, run: Runner = esegui,
                     digest: str | None = None, **opzioni) -> Esito:
    totale = Esito()
    if "osv" in quali:
        totale.aggiungi(controlla_osv(radice, run))
    if "digest" in quali:
        totale.aggiungi(controlla_digest(radice, run, digest))
    if "lockfile" in quali:
        totale.aggiungi(aggiorna_lockfile(radice, run, prova, **opzioni))
    codice, messaggi = segnala(totale.problemi, run, prova)
    totale.codice |= codice
    totale.messaggi += messaggi
    return totale


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prova", action="store_true", help="non apre issue, branch, push né PR: riferisce soltanto")
    p.add_argument("--solo", default=",".join(CONTROLLI), help="controlli da eseguire, separati da virgola (osv,digest,lockfile)")
    p.add_argument("--digest-attuale", help="usa questo digest al posto di quello letto da docker (prova del ramo «cambiato»)")
    a = p.parse_args(argv)
    quali = tuple(x.strip() for x in a.solo.split(",") if x.strip())
    sconosciuti = set(quali) - set(CONTROLLI)
    if sconosciuti or not quali:
        print(f"ERRORE: controlli non validi: {', '.join(sorted(sconosciuti)) or '(nessuno)'}; ammessi: {', '.join(CONTROLLI)}", file=sys.stderr)
        return ERRORE_CONTROLLO
    esito = esegui_controlli(RADICE, quali, a.prova, digest=a.digest_attuale)
    for m in esito.messaggi:
        print(m)
    print(f"uscita: {esito.codice}")
    return esito.codice


if __name__ == "__main__":
    sys.exit(main())
