#!/usr/bin/env python3
"""Script pronti per gli agenti di governance in Claude Code locale.

Due comandi:

  nuovo-task  Crea lo scheletro di un file di task in docs/revisioni/<cartella>/,
              con il template preso dalla descrizione dell'agente
              (.claude/agents/<agente>.md, unica fonte) e le clausole fisse.
              Il coordinator compila solo i campi tra graffe e il testo specifico.

  lancia      Lancia l'agente in modalità non interattiva (claude -p --agent),
              con modello, impegno e strumenti presi dall'intestazione del suo
              file; salva la risposta JSON accanto al task, controlla le chiavi
              rispetto allo schema dell'agente ed elenca i file comparsi o
              modificati durante il lancio (repository e /tmp).

  worktree-crea / worktree-elenco / worktree-chiudi
              Un worktree per task in .worktrees/<nome> sul branch impl/<nome>, con
              .venv e PostgreSQL in Docker propri (porta libera da 5433 in su), così
              più implementer lavorano in parallelo. Un task con la riga
              «Worktree: <nome>» viene lanciato dentro il suo worktree.
              `worktree-chiudi` cancella worktree, branch locale e remoto e container
              solo se il branch è già unito in main e il worktree è pulito.

  worktree-unisci
              Controllo obbligatorio prima del merge in main (DECISIONS §6 «Catena di
              fornitura»): nel worktree esegue il controllo OSV del lockfile e la suite
              `tests/` con le variabili di `.worktrees/<nome>.env`; solo se entrambi
              riescono fa `git merge --no-ff impl/<nome>` in main dal repository
              principale, con il messaggio passato. Altrimenti rifiuta e non tocca main.
              Non fa push.

Esempi:
  python3 scripts/agenti.py nuovo-task implementer impl-e1-chiusura --nome micro-api-env
  python3 scripts/agenti.py lancia docs/revisioni/impl-e1-chiusura/task-implementer-micro-api-env.md

Il file del task è il prompt: l'agente riceve il suo contenuto per intero.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
WORKTREE = RADICE / ".worktrees"
PREFISSO_BRANCH = "impl/"
PREFISSO_CONTAINER = "gravya-v2-wt-"
BRANCH_BASE = "main"
# Immagine PostgreSQL dei worktree: la stessa dei servizi della CI (unico punto, fissata
# per digest; DECISIONS §6 «Versioni di runtime»). Si cambia solo con --immagine.
def immagine_ci() -> str | None:
    try:
        testo = (RADICE / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    except OSError:
        return None
    immagini = set(re.findall(r"^\s*image:\s*(postgres:\S+@sha256:[0-9a-f]{64})\s*$", testo, re.M))
    return immagini.pop() if len(immagini) == 1 else None


IMMAGINE_PG = immagine_ci()
PORTA_INIZIALE = 5433
# Controllo prima del merge (`worktree-unisci`): percorsi relativi al worktree.
LOCKFILE = "requirements.lock.txt"
LOCKFILE_STRUMENTI = "requirements-strumenti.lock.txt"
SCRIPT_OSV = "scripts/osv-check.py"
CARTELLA_TEST = "tests"
# Prove con ruolo non superuser (job `test-non-superuser` della CI), con le variabili del worktree.
SCRIPT_NON_SUPERUSER = "scripts/test-non-superuser.sh"
# Job settimanale della catena di fornitura: la traccia e la soglia di eta' sono le sue.
SCRIPT_FORNITURA = "fornitura-locale.py"
# Argomenti di pytest come nel criterio di fine dei task (nessuna cache, basetemp nel worktree).
ARGOMENTI_PYTEST = ["-q", "-p", "no:cacheprovider", "--basetemp=.pytest_basetemp"]
AGENTI = RADICE / ".claude" / "agents"
REVISIONI = RADICE / "docs" / "revisioni"

# Clausole fisse per agente: vengono da stato/preferenze-e-lezioni.md (Lezioni).
# Se cambia una lezione, si aggiorna qui nello stesso commit.
CLAUSOLE_COMUNI = [
    "Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.",
    "Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).",
]
CLAUSOLE = {
    "implementer": [
        "Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).",
        "Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.",
        "Lavora sul branch indicato; non creare branch nuovi.",
    ],
    "registrar": [
        "Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.",
        "Non toccare legenda e intestazione dei registri.",
        "Il testo delle decisioni dell'utente va riportato alla lettera.",
    ],
    "doc-writer": [
        "Non riassumere né riscrivere le righe esistenti dello Storico modifiche: aggiungi solo la riga nuova.",
    ],
    "regulatory-researcher": [
        "Una norma per volta; ogni atto si legge una sola volta; il registro si aggiorna subito dopo ogni norma.",
    ],
}

CHIAVI_TASK = ("Agente:",)


def leggi_agente(nome: str) -> dict:
    """Intestazione YAML minima dei file in .claude/agents/ (senza dipendenze)."""
    percorso = AGENTI / f"{nome}.md"
    if not percorso.is_file():
        disponibili = ", ".join(sorted(p.stem for p in AGENTI.glob("*.md")))
        sys.exit(f"Agente «{nome}» non trovato in {AGENTI}. Disponibili: {disponibili}")
    testo = percorso.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", testo, re.S)
    if not m:
        sys.exit(f"Intestazione non trovata in {percorso}")
    testa = m.group(1)
    campi = {}
    for chiave in ("model", "effort", "tools"):
        mm = re.search(rf"^{chiave}:\s*(.+)$", testa, re.M)
        campi[chiave] = mm.group(1).strip() if mm else None
    descr = re.search(r"^description:\s*\|\n(.*?)(?=^\S)", testa, re.M | re.S)
    descr = descr.group(1) if descr else ""
    tmpl = re.search(r"Task \(template\):\n(.*?)\n\s*\n", descr, re.S)
    campi["template"] = (
        "\n".join(r[4:] if r.startswith("    ") else r.strip() for r in tmpl.group(1).splitlines())
        if tmpl else None
    )
    schema = re.search(r"```json\n(.*?)```", descr, re.S)
    campi["schema"] = schema.group(1) if schema else None
    return campi


def chiavi_schema(schema: str | None) -> list[str] | None:
    if not schema:
        return None
    # Chiavi di primo livello: righe con due spazi di rientro rispetto alla graffa.
    righe = schema.splitlines()
    base = None
    chiavi = []
    for r in righe:
        m = re.match(r'^(\s*)"([^"]+)"\s*:', r)
        if not m:
            continue
        if base is None:
            base = len(m.group(1))
        if len(m.group(1)) == base:
            chiavi.append(m.group(2))
    return chiavi


def cmd_nuovo_task(a: argparse.Namespace) -> None:
    ag = leggi_agente(a.agente)
    cartella = REVISIONI / a.cartella
    nome = f"task-{a.agente}" + (f"-{a.nome}" if a.nome else "") + ".md"
    dest = cartella / nome
    if dest.exists():
        sys.exit(f"Esiste già: {dest.relative_to(RADICE)} (non lo sovrascrivo)")
    cartella.mkdir(parents=True, exist_ok=True)
    oggi = dt.date.today().isoformat()
    clausole = CLAUSOLE_COMUNI + CLAUSOLE.get(a.agente, [])
    righe = [
        f"# Task per {a.agente}: {{titolo}}",
        "",
        f"Agente: {a.agente}",
        f"Preparato dal coordinator il {oggi}. Branch: {{branch}}.",
        "",
        "## Contesto",
        "{perché serve, decisioni dell'utente alla lettera, report da cui nasce}",
        "",
        "## Task",
        ag["template"] or "{template non trovato nella descrizione dell'agente: compilare a mano}",
        "",
        "## Regole fisse",
        *[f"- {c}" for c in clausole],
        "",
    ]
    dest.write_text("\n".join(righe), encoding="utf-8")
    print(dest.relative_to(RADICE))


def agente_dal_task(testo: str) -> str:
    m = re.search(r"^Agente:\s*([\w-]+)\s*$", testo, re.M)
    if not m:
        sys.exit("Nel task manca la riga «Agente: <nome>» (la crea `nuovo-task`).")
    return m.group(1)


def file_modificati_da(marcatore: float, cartelle: list[Path]) -> list[str]:
    trovati = []
    for base in cartelle:
        if not base.is_dir():
            continue
        for radice, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", ".pytest_cache", ".worktrees")
                       and not d.startswith("claude-")]  # file di servizio di Claude Code in /tmp
            for f in files:
                p = Path(radice) / f
                try:
                    if p.stat().st_mtime >= marcatore:
                        trovati.append(str(p))
                except OSError:
                    pass
    return sorted(trovati)


def estrai_json(testo: str):
    m = re.search(r"```(?:json)?\s*\n(.*?)```", testo, re.S)
    candidato = m.group(1) if m else testo
    inizio = candidato.find("{")
    fine = candidato.rfind("}")
    if inizio < 0 or fine < 0:
        return None
    try:
        return json.loads(candidato[inizio:fine + 1])
    except json.JSONDecodeError:
        return None


def cmd_lancia(a: argparse.Namespace) -> None:
    task = Path(a.task)
    if not task.is_absolute():
        task = (Path.cwd() / task).resolve()
    if not task.is_file():
        sys.exit(f"Task non trovato: {a.task}")
    testo = task.read_text(encoding="utf-8")
    nome = agente_dal_task(testo)
    ag = leggi_agente(nome)
    # Segnaposto del template = graffe fuori dal codice tra backtick (un JSON citato non conta).
    senza_codice = re.sub(r"`[^`\n]*`", "", testo.split("## Regole fisse")[0])
    if re.search(r"\{[^}\n]*\}", senza_codice) and not a.forza:
        sys.exit("Il task contiene ancora campi {da compilare}. Compilali o usa --forza.")
    if shutil.which("claude") is None:
        sys.exit("Comando `claude` non trovato nel PATH.")

    cmd = ["claude", "-p", "--agent", nome, "--output-format", "json",
           "--permission-mode", "acceptEdits"]
    if ag["model"]:
        cmd += ["--model", ag["model"]]
    if ag["effort"]:
        cmd += ["--effort", ag["effort"]]
    if ag["tools"]:
        cmd += ["--allowedTools", ag["tools"].replace(" ", "")]
    for d in a.add_dir or []:
        cmd += ["--add-dir", d]

    cwd = RADICE
    mw = re.search(r"^Worktree:\s*([\w-]+)\s*$", testo, re.M)
    if mw:
        cwd = WORKTREE / mw.group(1)
        if not cwd.is_dir():
            sys.exit(f"Worktree {cwd.relative_to(RADICE)} inesistente: crealo con `worktree-crea {mw.group(1)}`.")

    risposta_json = task.with_name(task.stem.replace("task-", "risposta-", 1) + ".json")
    risposta_txt = risposta_json.with_suffix(".txt")

    marcatore = time.time() - 1
    print(f"Lancio {nome} (modello {ag['model']}, impegno {ag['effort']}) con {task.relative_to(RADICE)}…",
          file=sys.stderr)
    proc = subprocess.run(cmd, input=testo, text=True, capture_output=True, cwd=cwd)
    if proc.returncode != 0:
        print(proc.stdout, proc.stderr, sep="\n", file=sys.stderr)
        sys.exit(f"claude è uscito con codice {proc.returncode}")
    try:
        involucro = json.loads(proc.stdout)
    except json.JSONDecodeError:
        involucro = {"result": proc.stdout}
    risultato = involucro.get("result", "")
    modelli = list((involucro.get("modelUsage") or {}).keys())

    dati = estrai_json(risultato)
    esclusi = {risposta_json, risposta_txt, task}
    if dati is not None:
        risposta_json.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        salvato = risposta_json
    else:
        risposta_txt.write_text(risultato, encoding="utf-8")
        salvato = risposta_txt

    print(f"Risposta: {salvato.relative_to(RADICE)}")
    print(f"Modelli usati: {', '.join(modelli) or 'non riportati'}")
    if involucro.get("is_error"):
        print("ATTENZIONE: claude segnala un errore nella sessione dell'agente.")

    attese = chiavi_schema(ag["schema"])
    if dati is None:
        print("ATTENZIONE: la risposta non è un JSON valido (salvata come testo).")
    elif attese and isinstance(dati, dict):
        extra = sorted(set(dati) - set(attese))
        mancanti = sorted(set(attese) - set(dati))
        if extra or mancanti:
            print(f"ATTENZIONE: chiavi fuori schema {extra or '-'}; chiavi mancanti {mancanti or '-'}")
        else:
            print("Chiavi della risposta conformi allo schema.")

    # Le cartelle --add-dir (clone di riferimento) non si controllano: sono in sola lettura
    # (hook .claude/hooks/riferimenti-sola-lettura.py) e cambiano per il lavoro dell'utente.
    cartelle = [RADICE, Path("/tmp")] + ([cwd] if cwd != RADICE else [])
    nuovi = [f for f in file_modificati_da(marcatore, cartelle) if Path(f) not in esclusi]
    print("File comparsi o modificati durante il lancio:" if nuovi else "Nessun altro file comparso o modificato.")
    for f in nuovi:
        try:
            print(f"  {Path(f).relative_to(RADICE)}")
        except ValueError:
            print(f"  {f}  (fuori dal repository)")


def git(*args: str, cwd: Path = RADICE, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def nome_valido(nome: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", nome):
        sys.exit("Nome del worktree: minuscole, cifre e trattini (es. e1-runtime).")
    return nome


def porta_libera() -> int:
    import socket
    usate = set()
    out = subprocess.run(["docker", "ps", "-a", "--format", "{{.Ports}}"], text=True, capture_output=True).stdout
    usate.update(int(p) for p in re.findall(r":(\d+)->", out))
    porta = PORTA_INIZIALE
    while True:
        if porta not in usate:
            with socket.socket() as so:
                try:
                    so.bind(("127.0.0.1", porta))
                    return porta
                except OSError:
                    pass
        porta += 1


def file_env(nome: str) -> Path:
    return WORKTREE / f"{nome}.env"


def cmd_worktree_crea(a: argparse.Namespace) -> None:
    nome = nome_valido(a.nome)
    dove = WORKTREE / nome
    branch = PREFISSO_BRANCH + nome
    container = PREFISSO_CONTAINER + nome
    if dove.exists():
        sys.exit(f"Esiste già: {dove.relative_to(RADICE)}")
    python = (RADICE / ".venv" / "bin" / "python").resolve()
    if not python.is_file():
        sys.exit("Manca il .venv del repository principale: il worktree usa lo stesso interprete.")
    WORKTREE.mkdir(exist_ok=True)
    git("worktree", "add", "-b", branch, str(dove), BRANCH_BASE)
    print(f"Worktree {dove.relative_to(RADICE)} sul branch {branch} (da {BRANCH_BASE})")

    venv = dove / ".venv"
    subprocess.run([str(python), "-m", "venv", str(venv)], check=True)
    pip = [str(venv / "bin" / "python"), "-m", "pip", "install", "-q", "--disable-pip-version-check"]
    subprocess.run(pip + ["--require-hashes", "-r", "requirements.lock.txt"], cwd=dove, check=True)
    subprocess.run(pip + ["--no-build-isolation", "--no-deps", "-e", "."], cwd=dove, check=True)
    print(f".venv con {python.name} dal lockfile")

    if not a.immagine:
        sys.exit("Immagine PostgreSQL non determinabile dalla CI (nessuna o più di una): usa --immagine.")
    porta = porta_libera()
    subprocess.run(["docker", "run", "-d", "--name", container, "-p", f"127.0.0.1:{porta}:5432",
                    "-e", "POSTGRES_USER=root", "-e", "POSTGRES_HOST_AUTH_METHOD=trust", a.immagine],
                   check=True, capture_output=True)
    for _ in range(60):
        if subprocess.run(["docker", "exec", container, "pg_isready", "-U", "root"],
                          capture_output=True).returncode == 0:
            break
        time.sleep(1)
    else:
        sys.exit(f"PostgreSQL nel container {container} non risponde.")
    time.sleep(1)
    subprocess.run(["docker", "exec", container, "createdb", "-U", "root", "-O", "root", "gravya_e1_test"],
                   check=True, capture_output=True)
    env = {
        "PGHOST": "127.0.0.1", "PGPORT": str(porta), "PGUSER": "root",
        "GRAVYA_E1_TEST_DSN": f"host=127.0.0.1 port={porta} user=root",
        "API_ENV": "development",
    }
    if (dove / "alembic.ini").is_file():
        url = f"postgresql+psycopg://root@127.0.0.1:{porta}/gravya_e1_test"
        subprocess.run([str(venv / "bin" / "alembic"), "upgrade", "head"], cwd=dove, check=True,
                       env=dict(os.environ, **env, DATABASE_URL=url), capture_output=True)
    riga = " ".join(f'{k}="{v}"' if " " in v else f"{k}={v}" for k, v in env.items())
    file_env(nome).write_text(riga + "\n", encoding="utf-8")
    print(f"PostgreSQL {a.immagine} nel container {container}, porta {porta}, database gravya_e1_test migrato")
    print("\nDa scrivere nel task:")
    print(f"Worktree: {nome}")
    print(f"Repository: .worktrees/{nome}; branch di lavoro: {branch}")
    print(f"Ambiente: `. .venv/bin/activate` (nel worktree) e variabili {riga}")


def stato_worktree(nome: str) -> dict:
    dove = WORKTREE / nome
    branch = PREFISSO_BRANCH + nome
    esiste_branch = git("rev-parse", "--verify", "--quiet", branch, check=False).returncode == 0
    unito = esiste_branch and git("merge-base", "--is-ancestor", branch, BRANCH_BASE, check=False).returncode == 0
    avanti = git("rev-list", "--count", f"{BRANCH_BASE}..{branch}", check=False).stdout.strip() if esiste_branch else "-"
    sporco = git("status", "--porcelain", cwd=dove, check=False).stdout.strip() if dove.is_dir() else ""
    cont = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", PREFISSO_CONTAINER + nome],
                          text=True, capture_output=True).stdout.strip() or "assente"
    return {"branch": branch, "esiste_branch": esiste_branch, "unito": unito, "avanti": avanti,
            "sporco": bool(sporco), "container": cont}


def cmd_worktree_elenco(a: argparse.Namespace) -> None:
    nomi = sorted(p.name for p in WORKTREE.iterdir() if p.is_dir()) if WORKTREE.is_dir() else []
    if not nomi:
        print("Nessun worktree aperto.")
        return
    for n in nomi:
        s = stato_worktree(n)
        print(f"{n}: branch {s['branch']}, commit non in {BRANCH_BASE}: {s['avanti']}, "
              f"{'unito' if s['unito'] else 'NON unito'}, {'modifiche non committate' if s['sporco'] else 'pulito'}, "
              f"container {s['container']}")


def cmd_worktree_chiudi(a: argparse.Namespace) -> None:
    nome = nome_valido(a.nome)
    dove = WORKTREE / nome
    s = stato_worktree(nome)
    if s["sporco"]:
        sys.exit(f"Il worktree {nome} ha modifiche non committate: non lo chiudo.")
    if s["esiste_branch"] and not s["unito"]:
        sys.exit(f"Il branch {s['branch']} non è unito in {BRANCH_BASE}: non lo chiudo (prima il merge).")
    if dove.is_dir():
        git("worktree", "remove", "--force", str(dove))  # --force solo per il .venv non tracciato; pulizia verificata sopra
        print(f"Worktree {dove.relative_to(RADICE)} rimosso")
    git("worktree", "prune")
    if s["esiste_branch"]:
        git("branch", "-d", s["branch"])
        print(f"Branch locale {s['branch']} cancellato")
    if git("ls-remote", "--exit-code", "--heads", "origin", s["branch"], check=False).returncode == 0:
        git("push", "origin", "--delete", s["branch"])
        print(f"Branch remoto {s['branch']} cancellato")
    if s["container"] != "assente":
        subprocess.run(["docker", "rm", "-fv", PREFISSO_CONTAINER + nome], check=True, capture_output=True)
        print(f"Container {PREFISSO_CONTAINER + nome} rimosso")
    file_env(nome).unlink(missing_ok=True)


def leggi_env_worktree(nome: str) -> dict[str, str]:
    """Variabili del worktree da `.worktrees/<nome>.env` (una riga `CHIAVE=valore ...`, come la scrive worktree-crea)."""
    f = file_env(nome)
    if not f.is_file():
        sys.exit(f"Manca {f.relative_to(RADICE)}: il worktree non ha le variabili di PostgreSQL (worktree-crea).")
    env = {}
    for token in shlex.split(f.read_text(encoding="utf-8")):
        chiave, sep, valore = token.partition("=")
        if not sep or not chiave:
            sys.exit(f"{f.relative_to(RADICE)}: voce non valida {token!r} (atteso CHIAVE=valore).")
        env[chiave] = valore
    return env


def comandi_controllo(dove: Path) -> list[tuple[str, list[str]]]:
    """Controlli prima del merge, in ordine, da eseguire con cwd = worktree."""
    py = str(dove / ".venv" / "bin" / "python")
    return [
        ("controllo OSV del lockfile", [py, SCRIPT_OSV, LOCKFILE]),
        ("controllo OSV dei lockfile degli strumenti", [py, SCRIPT_OSV, LOCKFILE_STRUMENTI]),
        ("suite dei test", [py, "-m", "pytest", *ARGOMENTI_PYTEST, CARTELLA_TEST]),
        ("prove con ruolo non superuser", ["bash", SCRIPT_NON_SUPERUSER]),
    ]


def modulo_fornitura():
    """Il job settimanale come modulo (nome con trattino): fonte unica di traccia e soglia."""
    spec = importlib.util.spec_from_file_location("fornitura_locale", Path(__file__).resolve().parent / SCRIPT_FORNITURA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def stato_fornitura() -> tuple[bool, str]:
    """(fresca, descrizione): l'ultima esecuzione riuscita del job settimanale e' entro la soglia?"""
    f = modulo_fornitura()
    codice, righe = f.stato(f.FILE_ESITI)
    return codice == f.OK, " | ".join(righe)


def cmd_worktree_unisci(a: argparse.Namespace) -> None:
    nome = nome_valido(a.nome)
    dove = WORKTREE / nome
    branch = PREFISSO_BRANCH + nome
    if not dove.is_dir():
        sys.exit(f"Il worktree {nome} non esiste.")
    if not a.messaggio.strip():
        sys.exit("Il messaggio di merge non può essere vuoto.")
    s = stato_worktree(nome)
    if not s["esiste_branch"]:
        sys.exit(f"Il branch {branch} non esiste.")
    if s["sporco"]:
        sys.exit(f"Il worktree {nome} ha modifiche non committate: non unisco (il controllo non le coprirebbe).")
    if s["unito"]:
        sys.exit(f"Il branch {branch} è già unito in {BRANCH_BASE}: niente da fare.")
    corrente = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if corrente != BRANCH_BASE:
        sys.exit(f"Il repository principale è su {corrente!r}, non su {BRANCH_BASE}: non unisco.")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        sys.exit("Il repository principale ha modifiche non committate: non unisco.")
    testa = git("rev-parse", "HEAD", cwd=dove, check=False)
    punta = git("rev-parse", "--verify", branch, check=False)
    if testa.returncode != 0 or punta.returncode != 0 or testa.stdout.strip() != punta.stdout.strip():
        sys.exit(f"RIFIUTATO: l'HEAD del worktree {nome} non coincide con la punta di {branch}: i controlli proverebbero "
                 f"altro da ciò che si unisce. Riportare il worktree su {branch}. {BRANCH_BASE} non è stato toccato.")
    if git("merge-base", "--is-ancestor", BRANCH_BASE, branch, check=False).returncode != 0:
        sys.exit(f"RIFIUTATO: {BRANCH_BASE} ha commit che {branch} non contiene: i controlli proverebbero il branch, non il "
                 f"risultato del merge. Prima si aggiorna il branch (merge di {BRANCH_BASE} in {branch}, nel worktree) e si "
                 f"rilanciano i controlli. {BRANCH_BASE} non è stato toccato.")
    messaggio = a.messaggio
    fresca, descrizione = stato_fornitura()
    if not fresca:
        if not getattr(a, "forza_fornitura", False):
            sys.exit(f"RIFIUTATO: il controllo settimanale della catena di fornitura non risulta eseguito di recente ({descrizione}). "
                     f"Eseguire `python3 scripts/fornitura-locale.py`, oppure forzare con --forza-fornitura "
                     f"(il messaggio di merge lo riporterà). {BRANCH_BASE} non è stato toccato.")
        messaggio = f"{a.messaggio.rstrip()}\n\nForzato: controllo di fornitura non recente ({descrizione})."
        print(f"ATTENZIONE: unione forzata, controllo di fornitura non recente ({descrizione}).", file=sys.stderr)
    env = dict(os.environ, **leggi_env_worktree(nome))
    for descrizione, cmd in comandi_controllo(dove):
        print(f"== {descrizione}: {' '.join(cmd)}", flush=True)
        if subprocess.run(cmd, cwd=dove, env=env).returncode != 0:
            sys.exit(f"RIFIUTATO: {descrizione} non riuscito. {BRANCH_BASE} non è stato toccato.")
    r = git("merge", "--no-ff", branch, "-m", messaggio, check=False)
    if r.returncode != 0:
        git("merge", "--abort", check=False)
        sys.exit(f"RIFIUTATO: il merge di {branch} in {BRANCH_BASE} non è riuscito ({r.stderr.strip() or r.stdout.strip()}); "
                 f"merge annullato, {BRANCH_BASE} com'era.")
    print(f"Unito {branch} in {BRANCH_BASE}: {git('rev-parse', '--short', 'HEAD').stdout.strip()} (nessun push).")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)

    n = sub.add_parser("nuovo-task", help="crea lo scheletro di un task")
    n.add_argument("agente")
    n.add_argument("cartella", help="sottocartella di docs/revisioni/")
    n.add_argument("--nome", help="suffisso del file (task-<agente>-<nome>.md)")
    n.set_defaults(f=cmd_nuovo_task)

    l = sub.add_parser("lancia", help="lancia l'agente su un task")
    l.add_argument("task", help="percorso del file del task")
    l.add_argument("--add-dir", action="append",
                   help="cartella in più leggibile dall'agente (es. un clone di riferimento); ripetibile")
    l.add_argument("--forza", action="store_true", help="lancia anche con campi {da compilare}")
    l.set_defaults(f=cmd_lancia)

    wc = sub.add_parser("worktree-crea", help="worktree, branch, .venv e PostgreSQL propri per un task")
    wc.add_argument("nome")
    wc.add_argument("--immagine", default=IMMAGINE_PG, help=f"immagine PostgreSQL (default {IMMAGINE_PG})")
    wc.set_defaults(f=cmd_worktree_crea)

    we = sub.add_parser("worktree-elenco", help="worktree aperti e loro stato")
    we.set_defaults(f=cmd_worktree_elenco)

    wx = sub.add_parser("worktree-chiudi", help="cancella worktree, branch e container dopo il merge")
    wx.add_argument("nome")
    wx.set_defaults(f=cmd_worktree_chiudi)

    wu = sub.add_parser("worktree-unisci", help="OSV, suite e prove non superuser nel worktree; solo se riescono, merge --no-ff in main (senza push)")
    wu.add_argument("nome")
    wu.add_argument("-m", "--messaggio", required=True, help="messaggio del commit di merge")
    wu.add_argument("--forza-fornitura", action="store_true",
                    help="unisce anche se l'ultima esecuzione riuscita del job settimanale e' piu' vecchia della soglia (scritto nel messaggio di merge)")
    wu.set_defaults(f=cmd_worktree_unisci)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
