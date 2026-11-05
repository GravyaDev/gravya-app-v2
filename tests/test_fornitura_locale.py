"""`scripts/fornitura-locale.py` (controlli settimanali in locale, DECISIONS §6).

Offline: i comandi esterni (`gh`, `docker`, OSV) sono sostituiti da un
esecutore finto che registra le chiamate; git e' reale, su repository
temporanei (origin = repository bare in `tmp_path`). Nessuna rete.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("fornitura_locale", RADICE / "scripts" / "fornitura-locale.py")
fl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fl)

REMOTO_GITHUB = "https://github.com/GravyaDev/gravya-app-v2.git"
REPO = "GravyaDev/gravya-app-v2"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
CI = f"""\
jobs:
  test:
    services: &servizi
      postgres:
        image: postgres:18@{DIGEST_A}
  altro:
    services: *servizi
"""
LOCK_VECCHIO = """\
# by the following command:
#
#    pip-compile --all-build-deps --generate-hashes --output-file=requirements.lock.txt --strip-extras pyproject.toml
#
alembic==1.0 \\
    --hash=sha256:aa
pytest==8.0 \\
    --hash=sha256:bb
"""
LOCK_NUOVO = LOCK_VECCHIO.replace("alembic==1.0", "alembic==1.1")


def cp(codice=0, out="", err=""):
    return subprocess.CompletedProcess([], codice, out, err)


def elenco_issue(*issue):
    """Risposta di `gh issue list --json number,title,body,comments`: (titolo, corpo[, [commenti]])."""
    return json.dumps([{"number": 10 + n, "title": i[0], "body": i[1], "comments": [{"body": c} for c in (i[2] if len(i) > 2 else [])]}
                       for n, i in enumerate(issue)])


class Finto:
    """Esecutore finto: `risposte` = {prefisso del comando: CompletedProcess}. Git passa al vero."""

    def __init__(self, risposte=None, reale_git=False):
        self.chiamate: list[list[str]] = []
        self.risposte = risposte or {}
        self.reale_git = reale_git

    def __call__(self, cmd, cwd=None, timeout=0):
        self.chiamate.append(list(cmd))
        riga = " ".join(cmd)
        for prefisso, r in self.risposte.items():
            # «~testo» = il comando contiene il testo; altrimenti = inizia con il prefisso
            if (prefisso[1:] in riga) if prefisso.startswith("~") else riga.startswith(prefisso):
                return r
        if "remote get-url" in riga:
            return cp(0, REMOTO_GITHUB + "\n")
        if self.reale_git and cmd[0] == "git":
            return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        return cp()

    def con(self, inizio):
        return [c for c in self.chiamate if " ".join(c).startswith(inizio)]


# --- Digest --------------------------------------------------------------------

def test_digest_fissato_dal_ci_yml_reale():
    tag, digest = fl.digest_fissato((RADICE / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    assert tag.startswith("postgres:") and "@" not in tag
    assert len(digest) == len("sha256:") + 64


@pytest.mark.parametrize("testo", ["nessuna immagine", CI + "        image: postgres:17@sha256:" + "c" * 64 + "\n"])
def test_digest_fissato_zero_o_due_immagini_e_errore(testo):
    with pytest.raises(fl.ErroreDigest):
        fl.digest_fissato(testo)


@pytest.fixture
def repo_ci(tmp_path):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text(CI)
    return tmp_path


def test_digest_uguale_ok(repo_ci):
    run = Finto({"docker buildx imagetools inspect postgres:18": cp(0, DIGEST_A + "\n")})
    e = fl.controlla_digest(repo_ci, run)
    assert e.codice == fl.OK and e.problemi == []


def test_digest_cambiato_da_docker(repo_ci):
    run = Finto({"docker buildx imagetools inspect postgres:18": cp(0, DIGEST_B + "\n")})
    e = fl.controlla_digest(repo_ci, run)
    assert e.codice == fl.DIGEST_CAMBIATO
    assert e.problemi[0][0] == "digest" and DIGEST_A in e.problemi[0][1] and DIGEST_B in e.problemi[0][1]


def test_digest_provato_su_un_digest_diverso_senza_docker(repo_ci):
    """Minore d: il ramo «digest cambiato» si prova con `attuale`, senza rete."""
    run = Finto()
    assert fl.controlla_digest(repo_ci, run, attuale=DIGEST_B).codice == fl.DIGEST_CAMBIATO
    assert fl.controlla_digest(repo_ci, run, attuale=DIGEST_A).codice == fl.OK
    assert run.chiamate == []


@pytest.mark.parametrize("risposta", [cp(1, "", "no"), cp(0, ""), cp(0, "non-un-digest")])
def test_digest_non_ottenuto_e_errore_non_ok(repo_ci, risposta):
    e = fl.controlla_digest(repo_ci, Finto({"docker": risposta}))
    assert e.codice == fl.ERRORE_CONTROLLO and e.problemi[0][0] == "controllo"


def test_digest_ci_yml_mancante_e_errore(tmp_path):
    assert fl.controlla_digest(tmp_path, Finto()).codice == fl.ERRORE_CONTROLLO


# --- OSV -----------------------------------------------------------------------

@pytest.mark.parametrize("rc,atteso,tipo", [(0, fl.OK, None), (1, fl.VULNERABILITA, "vulnerabilita"), (2, fl.ERRORE_CONTROLLO, "controllo"), (124, fl.ERRORE_CONTROLLO, "controllo")])
def test_osv_codici(rc, atteso, tipo):
    e = fl.controlla_osv(RADICE, Finto({"": cp(rc, "", "tomli==2.0.0: GHSA-x")}))
    assert e.codice == atteso
    assert [t for t, _ in e.problemi] == ([tipo] if tipo else [])
    if rc == 1:
        assert "GHSA-x" in e.problemi[0][1]


# --- Segnalazione ----------------------------------------------------------------

def test_issue_aperta_con_titolo_fisso_e_assegnatario():
    run = Finto({"gh issue list": cp(0, elenco_issue(("Altra issue", "x")))})
    codice, _ = fl.segnala([("vulnerabilita", "x==1: GHSA-x")], run)
    creazioni = run.con("gh issue create")
    assert codice == fl.OK and len(creazioni) == 1
    c = creazioni[0]
    assert c[c.index("--title") + 1] == fl.TITOLI["vulnerabilita"]
    assert c[c.index("--assignee") + 1] == "GravyaDev"
    assert "GHSA-x" in c[c.index("--body") + 1]


def test_issue_non_duplicata_se_gia_aperta_con_lo_stesso_titolo():
    run = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["digest"], "d")))})
    codice, msg = fl.segnala([("digest", "d"), ("vulnerabilita", "v")], run)
    creazioni = run.con("gh issue create")
    assert [c[c.index("--title") + 1] for c in creazioni] == [fl.TITOLI["vulnerabilita"]]  # solo quella nuova
    assert any("non duplicata" in m for m in msg)


def test_issue_titoli_distinti_per_tipo():
    assert len(set(fl.TITOLI.values())) == len(fl.TITOLI)


def test_issue_gh_che_fallisce_da_codice_32_non_silenzio():
    assert fl.segnala([("digest", "d")], Finto({"gh issue list": cp(1, "", "auth")}))[0] == fl.ERRORE_ISSUE
    run = Finto({"gh issue list": cp(0, "[]"), "gh issue create": cp(1, "", "boom")})
    assert fl.segnala([("digest", "d")], run)[0] == fl.ERRORE_ISSUE


def test_prova_non_apre_nulla():
    run = Finto()
    codice, msg = fl.segnala([("digest", "d")], run, prova=True)
    assert codice == fl.OK and run.chiamate == [] and "prova" in msg[0]


def test_esegui_controlli_combina_i_codici_e_segnala(repo_ci):
    run = Finto({"gh issue list": cp(0, "[]"), "docker": cp(0, DIGEST_B), fl.sys.executable: cp(1, "", "GHSA-x")})
    e = fl.esegui_controlli(repo_ci, ("digest",), False, run)
    assert e.codice == fl.DIGEST_CAMBIATO and len(run.con("gh issue create")) == 1
    e = fl.esegui_controlli(RADICE, ("osv", "digest"), False, run, digest=DIGEST_B)
    # OSV vulnerabile (1) + digest cambiato (2): due problemi, bit sommati
    assert e.codice == fl.VULNERABILITA | fl.DIGEST_CAMBIATO == 3


# --- Lockfile ---------------------------------------------------------------------

def test_comando_compile_dall_intestazione_del_lockfile_reale():
    testo = (RADICE / "requirements.lock.txt").read_text(encoding="utf-8")
    args = fl.comando_compile(testo)
    assert args[0] == "--upgrade" and "--generate-hashes" in args and args[-1] == "pyproject.toml"
    assert "--output-file=requirements.lock.txt" in args


def test_comando_compile_senza_intestazione_e_errore():
    with pytest.raises(fl.ErroreAggiornamento):
        fl.comando_compile("alembic==1.0 \\\n")


def test_differenze_tra_lockfile():
    nuovo = LOCK_NUOVO.replace("pytest==8.0 \\\n    --hash=sha256:bb\n", "") + "nuovo==2.0 \\\n    --hash=sha256:cc\n"
    assert fl.differenze(LOCK_VECCHIO, nuovo) == ["~ alembic: 1.0 -> 1.1", "+ nuovo 2.0 (nuovo)", "- pytest 8.0 (rimosso)"]
    assert fl.differenze(LOCK_VECCHIO, LOCK_VECCHIO) == []


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def repo(tmp_path):
    """Repository `principale` con origin bare, un commit su main con il lockfile."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    princ = tmp_path / "principale"
    git(tmp_path, "clone", "-q", str(origin), str(princ))
    (princ / "requirements.lock.txt").write_text(LOCK_VECCHIO)
    git(princ, "add", ".")
    git(princ, "commit", "-q", "-m", "base")
    git(princ, "push", "-q", "origin", "HEAD:main")
    git(princ, "fetch", "-q", "origin")
    return princ, origin


def compila_finto(nuovo):
    def _c(sorgente, lavoro, args):
        assert args[0] == "--upgrade"
        (sorgente / "requirements.lock.txt").write_text(nuovo)
    return _c


OGGI = dt.date(2026, 11, 9)


def test_lockfile_cambiato_branch_push_e_pr(repo):
    princ, origin = repo
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://example.org/pr/1\n")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.PR_APERTA, e.messaggi
    assert "impl/lockfile-2026-11-09" in git(origin, "branch", "--list")
    assert "alembic==1.1" in git(origin, "show", "impl/lockfile-2026-11-09:requirements.lock.txt")
    assert "alembic==1.0" in git(origin, "show", "main:requirements.lock.txt")  # main intatto
    pr = run.con("gh pr create")[0]
    assert pr[pr.index("--head") + 1] == "impl/lockfile-2026-11-09" and pr[pr.index("--base") + 1] == "main"
    assert "alembic: 1.0 -> 1.1" in pr[pr.index("--body") + 1] and "2026-11-09" in pr[pr.index("--title") + 1]
    assert len(git(princ, "worktree", "list").strip().splitlines()) == 1  # sorgente temporaneo rimosso


def test_lockfile_invariato_nessun_branch_nessuna_pr(repo):
    princ, origin = repo
    run = Finto(reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_VECCHIO))
    assert e.codice == fl.OK and run.con("gh") == []
    assert "lockfile" not in git(origin, "branch", "--list")


def test_lockfile_solo_intestazione_cambiata_non_e_un_aggiornamento(repo):
    princ, _ = repo
    run = Finto(reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_VECCHIO.replace("pip-compile --all", "pip-compile --all ")))
    assert e.codice == fl.OK and run.con("gh") == []


def test_lockfile_prova_non_pubblica_nulla(repo):
    princ, origin = repo
    run = Finto(reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, prova=True, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.OK and any("alembic: 1.0 -> 1.1" in m for m in e.messaggi)
    assert run.con("gh") == [] and run.con("git -C " + str(princ) + " push") == []
    assert "lockfile" not in git(origin, "branch", "--list")


def test_lockfile_pr_di_lockfile_gia_aperta_non_ne_apre_un_altra(repo):
    princ, origin = repo
    run = Finto({"gh pr list": cp(0, '[{"headRefName":"impl/lockfile-2026-11-02"}]')}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.OK and run.con("gh pr create") == []
    assert "lockfile" not in git(origin, "branch", "--list")


@pytest.mark.parametrize("guasto", ["compila", "pr"])
def test_lockfile_guasti_danno_errore_e_issue(repo, guasto):
    princ, _ = repo
    risposte = {"gh pr list": cp(0, "[]")}
    if guasto == "pr":
        risposte["gh pr create"] = cp(1, "", "boom")

    def rotta(s, l, a):
        raise fl.ErroreAggiornamento("pip-compile rotto")

    e = fl.aggiorna_lockfile(princ, Finto(risposte, reale_git=True), oggi=OGGI,
                             compila=rotta if guasto == "compila" else compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and e.problemi[0][0] == "aggiornamento"
    assert len(git(princ, "worktree", "list").strip().splitlines()) == 1


def test_main_opzioni_non_valide(capsys):
    assert fl.main(["--solo", "osv,boh"]) == fl.ERRORE_CONTROLLO
    assert "boh" in capsys.readouterr().err


def test_costanti_dichiarate():
    assert fl.ASSEGNATARIO == "GravyaDev"
    assert fl.PREFISSO_BRANCH_LOCKFILE == "impl/lockfile-"
    assert {fl.OK, fl.VULNERABILITA, fl.DIGEST_CAMBIATO, fl.ERRORE_CONTROLLO, fl.ERRORE_AGGIORNAMENTO, fl.PR_APERTA, fl.ERRORE_ISSUE} == {0, 1, 2, 4, 8, 16, 32}
    assert ".fornitura-lavoro/" in (RADICE / ".gitignore").read_text().splitlines()


# === Giro 2: percorsi di errore fail-closed, isolamento, base, traccia ====================
# I test sotto non leggono file del repository oltre a scripts/, ci.yml, lockfile e .gitignore:
# la prova a mutanti del code-reviewer li lancia in un albero minimo.

def _piccolo(cmd, timeout):
    return fl.esegui(cmd, timeout=timeout)


def test_esegui_timeout_e_errore_con_output_parziale_come_testo():
    r = _piccolo([sys.executable, "-c", "import time; print('parziale', flush=True); time.sleep(30)"], 1)
    assert r.returncode != 0
    assert isinstance(r.stdout, str) and isinstance(r.stderr, str)
    assert "tempo scaduto" in r.stderr


def test_esegui_comando_non_eseguibile_e_errore():
    r = fl.esegui(["/non/esiste/comando-xyz"])
    assert r.returncode != 0 and "non eseguibile" in r.stderr


def test_esegui_buon_esito_e_output_non_decodificabile_non_solleva():
    assert fl.esegui([sys.executable, "-c", "print('ok')"]).stdout.strip() == "ok"
    r = fl.esegui([sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\xff\\xfe')"])
    assert r.returncode == 0 and isinstance(r.stdout, str)


def test_timeout_dell_osv_e_errore_non_ok():
    """Il timeout di esegui (codice != 0, != 1) arriva al controllo come errore, non come «nessuna vulnerabilita'»."""
    r = fl.esegui([sys.executable, "-c", "import time; time.sleep(30)"], timeout=1)
    e = fl.controlla_osv(RADICE, Finto({"": r}))
    assert e.codice == fl.ERRORE_CONTROLLO and e.problemi[0][0] == "controllo"


def test_digest_attuale_con_formato_non_valido_e_errore_non_cambiato(repo_ci):
    for valore in ("non-un-digest", "sha256:abc", ""):
        e = fl.controlla_digest(repo_ci, Finto(), attuale=valore)
        assert e.codice == fl.ERRORE_CONTROLLO and e.problemi[0][0] == "controllo", valore


# --- compila_con_pip_tools (test propri, senza iniezione di `compila`) ---------------

@pytest.fixture
def radice_finta(tmp_path):
    """Radice con interprete finto e requisiti degli strumenti (i comandi sono simulati)."""
    (tmp_path / ".venv/bin").mkdir(parents=True)
    (tmp_path / ".venv/bin/python").write_text("")
    (tmp_path / "requirements-strumenti.lock.txt").write_text("pip-tools==7.6.2 \\\n    --hash=sha256:aa\n")
    return tmp_path


def _compila(radice, run):
    sorgente = radice / "s"
    sorgente.mkdir(exist_ok=True)
    fl.compila_con_pip_tools(sorgente, radice / "lavoro", ["--upgrade", "pyproject.toml"], run, radice)


def test_compila_con_pip_tools_sequenza_e_hash_obbligatori(radice_finta):
    run = Finto()
    _compila(radice_finta, run)
    assert [c[1:3] for c in run.chiamate] == [["-m", "venv"], ["-m", "pip"], ["-m", "piptools"]]
    install = run.chiamate[1]
    assert "--require-hashes" in install and install[install.index("-r") + 1] == str(radice_finta / "requirements-strumenti.lock.txt")
    assert "pip-tools" not in install and "--upgrade" not in install   # niente installazione libera dell'ultima versione
    assert run.chiamate[2][-2:] == ["--upgrade", "pyproject.toml"]


@pytest.mark.parametrize("cosa,risposta,messaggio", [
    ("-m venv", cp(1, "", "no venv"), "venv di lavoro"),
    ("-m pip install", cp(1, "", "no rete"), "installazione di pip-tools"),
    ("-m piptools compile", cp(2, "", "conflitto"), "pip-compile non riuscito"),
    ("-m piptools compile", cp(124, "", "tempo scaduto"), "pip-compile non riuscito"),
])
def test_compila_con_pip_tools_ogni_errore_solleva(radice_finta, cosa, risposta, messaggio):
    with pytest.raises(fl.ErroreAggiornamento, match=messaggio):
        _compila(radice_finta, Finto({"~" + cosa: risposta}))


def test_compila_con_pip_tools_senza_interprete_o_senza_requisiti_solleva(radice_finta):
    (radice_finta / "requirements-strumenti.lock.txt").unlink()
    run = Finto()
    with pytest.raises(fl.ErroreAggiornamento, match="requirements-strumenti"):
        _compila(radice_finta, run)
    (radice_finta / ".venv/bin/python").unlink()
    with pytest.raises(fl.ErroreAggiornamento, match="interprete"):
        _compila(radice_finta, run)
    assert run.chiamate == []   # nessun comando partito


def _repo_con_compile_reale(repo):
    """Il `princ` del fixture con interprete e requisiti degli strumenti, per usare la compila di default."""
    princ, origin = repo
    (princ / ".venv/bin").mkdir(parents=True)
    (princ / ".venv/bin/python").write_text("")
    (princ / "requirements-strumenti.lock.txt").write_text("pip-tools==7.6.2 \\\n    --hash=sha256:aa\n")
    return princ, origin


@pytest.mark.parametrize("cosa,messaggio", [
    ("-m venv", "venv di lavoro"),
    ("-m pip install", "installazione di pip-tools"),
    ("-m piptools compile", "pip-compile non riuscito"),
])
def test_lockfile_errore_degli_strumenti_non_diventa_gia_aggiornato(repo, cosa, messaggio):
    """Lockfile invariato + strumento fallito = ERRORE con issue, mai «già alle ultime versioni»."""
    princ, origin = _repo_con_compile_reale(repo)
    run = Finto({"~" + cosa: cp(1, "", "boom"), "gh pr list": cp(0, "[]")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI)
    assert e.codice == fl.ERRORE_AGGIORNAMENTO, e.messaggi
    assert e.problemi[0][0] == "aggiornamento" and messaggio in e.problemi[0][1]
    assert not any("già alle ultime" in m for m in e.messaggi)
    assert run.con("gh pr create") == []
    assert len(git(princ, "worktree", "list").strip().splitlines()) == 1


def test_lockfile_con_strumenti_riusciti_apre_la_pr(repo):
    """Percorso completo con la compila di default: gli strumenti (simulati) scrivono il lockfile nuovo."""
    princ, origin = _repo_con_compile_reale(repo)

    class ScriveLockfile(Finto):
        def __call__(self, cmd, cwd=None, timeout=0):
            r = super().__call__(cmd, cwd, timeout)
            if "piptools" in cmd:
                (cwd / "requirements.lock.txt").write_text(LOCK_NUOVO)
            return r

    run = ScriveLockfile({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://example.org/pr/2\n")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI)
    assert e.codice == fl.PR_APERTA, e.messaggi
    assert e.versioni["pip-tools"] == "7.6.2"


# --- Errori di git e di gh nell'aggiornamento --------------------------------------------

@pytest.mark.parametrize("pezzo,messaggio", [
    (" fetch origin main", "git fetch"),
    (" log --format", "git log"),
    (" worktree add --detach", "git worktree"),
    (" switch -c", "git switch"),
    (" add requirements.lock.txt", "git add"),
    (" commit -q", "git -c"),
    (" push origin", "git push"),
])
def test_lockfile_ogni_errore_di_git_e_errore_con_issue(repo, pezzo, messaggio):
    princ, origin = repo
    run = Finto({"~" + pezzo: cp(1, "", "git rotto"), "gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO, e.messaggi
    assert e.problemi[0][0] == "aggiornamento" and "git rotto" in e.problemi[0][1]
    assert run.con("gh pr create") == []
    assert "lockfile" not in git(origin, "branch", "--list")
    assert len(git(princ, "worktree", "list").strip().splitlines()) == 1


def test_lockfile_fetch_fallito_non_rigenera_su_una_base_vecchia(repo):
    princ, _ = repo
    chiamate_compila = []
    run = Finto({"~ fetch origin main": cp(128, "", "rete assente")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=lambda s, l, a: chiamate_compila.append(a))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and chiamate_compila == []
    assert run.con("git -C " + str(princ) + " worktree add") == []


def test_lockfile_gh_pr_list_fallito_non_apre_la_pr(repo):
    princ, origin = repo
    run = Finto({"gh pr list": cp(1, "", "non autenticato"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and "elenco delle PR non ottenuto" in e.problemi[0][1]
    assert run.con("gh pr create") == [] and "lockfile" not in git(origin, "branch", "--list")


def test_lockfile_branch_locale_gia_esistente_e_errore_con_spiegazione(repo):
    princ, origin = repo
    git(princ, "branch", "impl/lockfile-2026-11-09")
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and "esiste già in locale" in e.problemi[0][1]
    assert run.con("gh pr create") == []


def test_lockfile_gh_pr_create_con_timeout_e_errore(repo):
    princ, _ = repo
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": fl.esegui([sys.executable, "-c", "import time; time.sleep(30)"], timeout=1)}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO


def test_lockfile_eccezione_di_lettura_diventa_errore(repo):
    princ, _ = repo

    def rovina(s, l, a):
        (s / "requirements.lock.txt").write_bytes(b"\xff\xfe\x00")

    e = fl.aggiorna_lockfile(princ, Finto(reale_git=True), oggi=OGGI, compila=rovina)
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and e.problemi[0][0] == "aggiornamento"


# --- Base della rigenerazione: origin/main, commit locali non pubblicati ------------------

def test_lockfile_main_locale_con_commit_non_pubblicati_su_lockfile_nessuna_pr(repo):
    princ, origin = repo
    (princ / "requirements.lock.txt").write_text(LOCK_NUOVO.replace("1.1", "1.5"))
    git(princ, "commit", "-q", "-am", "lavoro locale sul lockfile")
    chiamate_compila = []
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=lambda s, l, a: chiamate_compila.append(a))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and chiamate_compila == []
    assert "non pubblicati" in e.problemi[0][1] and "lavoro locale sul lockfile" in e.problemi[0][1]
    assert run.con("gh pr create") == [] and "lockfile" not in git(origin, "branch", "--list")


def test_lockfile_main_locale_con_commit_non_pubblicati_su_pyproject_nessuna_pr(repo):
    princ, _ = repo
    (princ / "pyproject.toml").write_text("[project]\n")
    git(princ, "add", "pyproject.toml")
    git(princ, "commit", "-q", "-m", "tocca pyproject")
    e = fl.aggiorna_lockfile(princ, Finto(reale_git=True), oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and "pyproject.toml" in e.problemi[0][1]


def test_lockfile_commit_locali_su_altri_file_non_bloccano(repo):
    princ, _ = repo
    (princ / "altro.txt").write_text("x\n")
    git(princ, "add", "altro.txt")
    git(princ, "commit", "-q", "-m", "altro")
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    assert fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO)).codice == fl.PR_APERTA


def test_lockfile_parte_da_origin_main_dopo_il_fetch(repo):
    princ, origin = repo
    run = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    fetch = [c for c in run.chiamate if c[:2] == ["git", "-C"] and "fetch" in c]
    assert fetch and fetch[0][-2:] == ["origin", "main"]
    aggiunta = [c for c in run.chiamate if "worktree" in c and "add" in c][0]
    assert aggiunta[-1] == "origin/main"


# --- gh sempre con -R ricavato dal remoto -------------------------------------------------

@pytest.mark.parametrize("url,atteso", [
    ("https://github.com/GravyaDev/gravya-app-v2.git", "GravyaDev/gravya-app-v2"),
    ("https://github.com/GravyaDev/gravya-app-v2", "GravyaDev/gravya-app-v2"),
    ("git@github.com:GravyaDev/gravya-app-v2.git", "GravyaDev/gravya-app-v2"),
    ("ssh://git@github.com/o/r.git", "o/r"),
])
def test_repo_github_dal_remoto(url, atteso):
    assert fl.repo_github(RADICE, Finto({"~remote get-url": cp(0, url + "\n")})) == atteso


@pytest.mark.parametrize("risposta", [
    cp(1, "", "no such remote"), cp(0, ""), cp(0, "/percorso/locale/origin.git\n"),
    cp(0, "https://utente:" + "tok" + "@github.com/o/r.git\n"), cp(0, "https://example.org/o/r.git\n"),
])
def test_repo_github_non_riconosciuto_e_errore(risposta):
    with pytest.raises(fl.ErroreRepository) as e:
        fl.repo_github(RADICE, Finto({"~remote get-url": risposta}))
    assert "tok" not in str(e.value)


def test_ogni_comando_gh_ha_R_con_il_repository_del_remoto(repo):
    princ, _ = repo
    run = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["digest"], "vecchio"))), "gh pr list": cp(0, "[]"),
                 "gh pr create": cp(0, "https://x/1")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    fl.segnala([("vulnerabilita", "v"), ("digest", "nuovo")], run, radice=princ)
    gh = run.con("gh")
    assert {c[1] for c in gh} == {"pr", "issue"} and {c[2] for c in gh} == {"list", "create", "comment"}
    for c in gh:
        assert c[c.index("-R") + 1] == REPO, c


def test_remoto_non_github_nessuna_issue_e_codice_32():
    run = Finto({"~remote get-url": cp(0, "/locale/origin.git\n")})
    codice, msg = fl.segnala([("digest", "d")], run)
    assert codice == fl.ERRORE_ISSUE and run.con("gh") == [] and "repository" in msg[0]


def test_remoto_non_github_la_pr_non_parte(repo):
    princ, _ = repo
    run = Finto({"~remote get-url": cp(0, "/locale/origin.git\n")}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    assert e.codice == fl.ERRORE_AGGIORNAMENTO and run.con("gh") == []


# --- Isolamento dei controlli ------------------------------------------------------------

LOCK_STRANO = LOCK_VECCHIO + "pacchetto @ https://example.org/p.whl\n"


def test_osv_con_vulnerabilita_e_lockfile_non_conforme_aprono_entrambe_le_issue(repo):
    """Prima del giro 2 l'ErroreLockfile attraversava esegui_controlli e si perdevano entrambe le issue."""
    princ, _ = repo
    run = Finto({fl.sys.executable: cp(1, "", "x==1: GHSA-x"), "gh issue list": cp(0, "[]")}, reale_git=True)
    e = fl.esegui_controlli(princ, ("osv", "lockfile"), False, run, oggi=OGGI, compila=compila_finto(LOCK_STRANO))
    titoli = [c[c.index("--title") + 1] for c in run.con("gh issue create")]
    assert sorted(titoli) == sorted([fl.TITOLI["vulnerabilita"], fl.TITOLI["aggiornamento"]])
    assert e.codice & fl.VULNERABILITA and e.codice & fl.ERRORE_AGGIORNAMENTO
    assert e.per_controllo["osv"]["esito"] == ["vulnerabilita"] and e.per_controllo["lockfile"]["esito"] == ["errore"]
    assert len(git(princ, "worktree", "list").strip().splitlines()) == 1


def test_eccezione_inattesa_in_un_controllo_non_fa_perdere_le_issue_degli_altri(repo, monkeypatch):
    princ, _ = repo

    def esplode(*a, **k):
        raise RuntimeError("imprevisto")

    monkeypatch.setattr(fl, "controlla_digest", esplode)
    run = Finto({fl.sys.executable: cp(1, "", "x==1: GHSA-x"), "gh issue list": cp(0, "[]")}, reale_git=True)
    e = fl.esegui_controlli(princ, ("osv", "digest", "lockfile"), False, run, oggi=OGGI, compila=compila_finto(LOCK_VECCHIO))
    titoli = sorted(c[c.index("--title") + 1] for c in run.con("gh issue create"))
    assert titoli == sorted([fl.TITOLI["vulnerabilita"], fl.TITOLI["controllo"]])
    assert e.codice & fl.ERRORE_CONTROLLO and e.codice & fl.VULNERABILITA
    corpo = [c[c.index("--body") + 1] for c in run.con("gh issue create") if fl.TITOLI["controllo"] in c][0]
    assert "RuntimeError" in corpo and "imprevisto" in corpo and "digest" in corpo


def test_eccezione_inattesa_nel_lockfile_ha_la_sua_issue_di_aggiornamento(repo, monkeypatch):
    princ, _ = repo
    monkeypatch.setattr(fl, "aggiorna_lockfile", lambda *a, **k: (_ for _ in ()).throw(KeyError("boom")))
    run = Finto({"gh issue list": cp(0, "[]")})
    e = fl.esegui_controlli(princ, ("lockfile",), False, run)
    assert e.codice == fl.ERRORE_AGGIORNAMENTO | 0 and [c[c.index("--title") + 1] for c in run.con("gh issue create")] == [fl.TITOLI["aggiornamento"]]


def test_eccezione_in_segnala_non_si_propaga_e_da_codice_32(repo, monkeypatch):
    princ, _ = repo
    monkeypatch.setattr(fl, "segnala", lambda *a, **k: (_ for _ in ()).throw(ValueError("x")))
    e = fl.esegui_controlli(princ, ("digest",), False, Finto(), digest=DIGEST_A)
    assert e.codice & fl.ERRORE_ISSUE


def test_segnala_e_sempre_eseguita_per_tutti_gli_esiti(repo, monkeypatch):
    princ, _ = repo
    ricevuti = []
    monkeypatch.setattr(fl, "segnala", lambda problemi, *a, **k: (ricevuti.extend(problemi), (fl.OK, []))[1])
    monkeypatch.setattr(fl, "controlla_osv_tutti", lambda *a, **k: (_ for _ in ()).throw(OSError("disco")))
    monkeypatch.setattr(fl, "controlla_digest", lambda *a, **k: fl.Esito(fl.DIGEST_CAMBIATO, [("digest", "d")]))
    fl.esegui_controlli(princ, ("osv", "digest"), False, Finto())
    assert sorted(t for t, _ in ricevuti) == ["controllo", "digest"]


# --- Issue: commento se il contenuto cambia, credenziali tolte -------------------------------

def test_issue_aperta_con_contenuto_cambiato_riceve_un_commento():
    run = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["vulnerabilita"], "x==1: GHSA-1")))})
    codice, msg = fl.segnala([("vulnerabilita", "x==1: GHSA-1\ny==2: GHSA-2")], run)
    assert codice == fl.OK and run.con("gh issue create") == []
    c = run.con("gh issue comment")[0]
    assert c[3] == "10" and "GHSA-2" in c[c.index("--body") + 1] and "commento" in msg[0]


def test_issue_aperta_con_contenuto_invariato_nessun_commento():
    run = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["vulnerabilita"], "x==1: GHSA-1")))})
    codice, msg = fl.segnala([("vulnerabilita", "x==1: GHSA-1")], run)
    assert codice == fl.OK and run.con("gh issue comment") == [] and run.con("gh issue create") == []
    assert "non duplicata" in msg[0]


def test_issue_il_confronto_e_con_l_ultimo_commento_non_con_il_corpo():
    iss = (fl.TITOLI["digest"], "A", ["B"])
    run = Finto({"gh issue list": cp(0, elenco_issue(iss))})
    fl.segnala([("digest", "B")], run)
    assert run.con("gh issue comment") == []      # B e' gia' l'ultimo contenuto noto
    fl.segnala([("digest", "A")], run)
    assert len(run.con("gh issue comment")) == 1  # A non e' l'ultimo: lo si ripete


def test_issue_commento_fallito_e_codice_32():
    run = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["digest"], "A"))), "gh issue comment": cp(1, "", "no")})
    assert fl.segnala([("digest", "B")], run)[0] == fl.ERRORE_ISSUE


@pytest.mark.parametrize("risposta", [cp(0, "non json"), cp(0, '{"a": 1}'), cp(0, '[{"senza": "titolo"}]')])
def test_issue_elenco_illeggibile_e_codice_32_senza_aprire(risposta):
    run = Finto({"gh issue list": risposta})
    assert fl.segnala([("digest", "d")], run)[0] == fl.ERRORE_ISSUE and run.con("gh issue create") == []


def test_issue_elenco_al_limite_puo_essere_troncato_e_non_si_apre_nulla(monkeypatch):
    monkeypatch.setattr(fl, "LIMITE_ISSUE_LETTE", 2)
    run = Finto({"gh issue list": cp(0, elenco_issue(("a", ""), ("b", "")))})
    assert fl.segnala([("digest", "d")], run)[0] == fl.ERRORE_ISSUE and run.con("gh issue create") == []


TOKEN_CLASSICO = "ghp_" + "A1b2C3d4" * 5
TOKEN_FINE = "github_pat_" + "Z9y8X7w6_" * 4
TOKEN_OAUTH = "gho_" + "Q" * 30
URL_CON_CREDENZIALI = "https://utente:segreto123@github.com/o/r.git"


@pytest.mark.parametrize("segreto", [TOKEN_CLASSICO, TOKEN_FINE, TOKEN_OAUTH, "segreto123"])
def test_ripulisci_toglie_i_pattern_di_credenziali(segreto):
    testo = f"errore: {TOKEN_CLASSICO} {TOKEN_FINE} {TOKEN_OAUTH} push a {URL_CON_CREDENZIALI} fine"
    pulito = fl.ripulisci(testo)
    assert segreto not in pulito and "https://[credenziali rimosse]@github.com/o/r.git" in pulito
    assert fl.ripulisci("niente di segreto: x==1.0") == "niente di segreto: x==1.0"


def test_nessuna_credenziale_in_issue_commenti_e_pr(repo):
    princ, _ = repo
    veleno = f"fatal: {TOKEN_CLASSICO} {URL_CON_CREDENZIALI} {TOKEN_FINE}"
    # issue nuova
    run = Finto({"gh issue list": cp(0, "[]")})
    fl.segnala([("controllo", veleno)], run)
    # commento
    run2 = Finto({"gh issue list": cp(0, elenco_issue((fl.TITOLI["controllo"], "vecchio")))})
    fl.segnala([("controllo", veleno)], run2)
    # PR: l'errore di un comando entra nell'issue via _coda
    run3 = Finto({"gh pr list": cp(0, "[]"), "gh pr create": cp(1, "", veleno)}, reale_git=True)
    e = fl.aggiorna_lockfile(princ, run3, oggi=OGGI, compila=compila_finto(LOCK_NUOVO))
    testi = [c[c.index("--body") + 1] for c in run.con("gh issue create") + run2.con("gh issue comment")] + [e.problemi[0][1]]
    assert len(testi) == 3
    for testo in testi:
        for segreto in (TOKEN_CLASSICO, TOKEN_FINE, "segreto123"):
            assert segreto not in testo


# --- Traccia delle esecuzioni e --stato -------------------------------------------------------

ORA = dt.datetime(2026, 11, 9, 8, 0, tzinfo=dt.timezone.utc)


def _esito(codici):
    e = fl.Esito(versioni={"python": "3.15"})
    for nome, codice in codici.items():
        e.per_controllo[nome] = {"codice": codice, "esito": fl.etichette(codice)}
        e.codice |= codice
    return e


def test_registra_una_riga_json_per_esecuzione_in_coda(tmp_path):
    f = tmp_path / "stato" / "esiti.jsonl"
    fl.registra(_esito({"osv": 0, "digest": 2, "lockfile": 16}), fl.CONTROLLI, False, f, ORA)
    fl.registra(_esito({"osv": 4}), ("osv",), True, f, ORA + dt.timedelta(days=7))
    righe = [json.loads(r) for r in f.read_text().splitlines()]
    assert len(righe) == 2
    assert righe[0]["data"] == "2026-11-09T08:00:00+00:00" and righe[0]["prova"] is False
    assert righe[0]["esiti"]["digest"] == {"codice": 2, "esito": ["digest_cambiato"]}
    assert righe[0]["versioni"] == {"python": "3.15"} and righe[1]["prova"] is True and righe[1]["codice"] == 4


def test_main_registra_anche_l_esecuzione_fallita(tmp_path, repo_ci):
    f = tmp_path / "esiti.jsonl"
    run = Finto({"gh issue list": cp(0, "[]"), "docker": cp(1, "", "docker assente")})
    codice = fl.main(["--solo", "digest"], run, f, repo_ci, ORA)
    assert codice == fl.ERRORE_CONTROLLO
    riga = json.loads(f.read_text())
    assert riga["codice"] == fl.ERRORE_CONTROLLO and riga["esiti"]["digest"]["esito"] == ["errore"]
    assert not fl.e_riuscita(riga)


def test_main_traccia_non_scrivibile_e_errore(tmp_path, repo_ci, capsys):
    blocco = tmp_path / "file"
    blocco.write_text("x")
    run = Finto({"docker": cp(0, DIGEST_A)})
    codice = fl.main(["--solo", "digest"], run, blocco / "esiti.jsonl", repo_ci, ORA)
    assert codice & fl.ERRORE_CONTROLLO and "traccia" in capsys.readouterr().out


def test_main_digest_attuale_solo_con_prova(tmp_path, repo_ci, capsys):
    f = tmp_path / "esiti.jsonl"
    run = Finto({"gh issue list": cp(0, "[]")})
    assert fl.main(["--solo", "digest", "--digest-attuale", DIGEST_B], run, f, repo_ci, ORA) == fl.ERRORE_CONTROLLO
    assert run.chiamate == [] and not f.exists() and "--prova" in capsys.readouterr().err
    assert fl.main(["--solo", "digest", "--prova", "--digest-attuale", DIGEST_B], run, f, repo_ci, ORA) == fl.DIGEST_CAMBIATO
    assert run.con("gh issue create") == []


def _scrivi_riuscita(f, ora, **ritocchi):
    e = _esito({"osv": 0, "digest": 0, "lockfile": 0})
    fl.registra(e, fl.CONTROLLI, ritocchi.get("prova", False), f, ora)


def test_stato_esecuzione_recente_ok(tmp_path, capsys):
    f = tmp_path / "e.jsonl"
    _scrivi_riuscita(f, ORA)
    codice, righe = fl.stato(f, ORA + dt.timedelta(days=3))
    assert codice == fl.OK and "2026-11-09T08:00:00+00:00" in "\n".join(righe)
    assert fl.main(["--stato"], traccia=f, ora=ORA + dt.timedelta(days=3)) == fl.OK
    assert "ultima esecuzione riuscita" in capsys.readouterr().out


def test_stato_oltre_la_soglia_e_errore(tmp_path):
    f = tmp_path / "e.jsonl"
    _scrivi_riuscita(f, ORA)
    soglia = dt.timedelta(days=fl.SOGLIA_ESECUZIONE_GIORNI)
    assert fl.stato(f, ORA + soglia)[0] == fl.OK                                  # alla soglia ancora valida
    codice, righe = fl.stato(f, ORA + soglia + dt.timedelta(minutes=1))
    assert codice == fl.STATO_SCADUTO and "ATTENZIONE" in righe[-1]
    assert fl.main(["--stato"], traccia=f, ora=ORA + soglia + dt.timedelta(days=1)) == fl.STATO_SCADUTO


def test_stato_senza_traccia_o_senza_riuscite_e_errore(tmp_path):
    assert fl.stato(tmp_path / "manca.jsonl", ORA)[0] == fl.STATO_SCADUTO
    f = tmp_path / "e.jsonl"
    fl.registra(_esito({"osv": 0, "digest": 0, "lockfile": 0}), fl.CONTROLLI, True, f, ORA)        # prova
    fl.registra(_esito({"osv": 0, "digest": 4, "lockfile": 0}), fl.CONTROLLI, False, f, ORA)        # errore
    fl.registra(_esito({"osv": 0}), ("osv",), False, f, ORA)                                        # parziale
    f.write_text(f.read_text() + "riga corrotta\n{\"data\": \"non-una-data\"}\n")
    codice, righe = fl.stato(f, ORA)
    assert codice == fl.STATO_SCADUTO and "nessuna esecuzione riuscita" in righe[-1]


def test_stato_vulnerabilita_trovate_non_sono_un_fallimento_del_controllo(tmp_path):
    f = tmp_path / "e.jsonl"
    fl.registra(_esito({"osv": 1, "digest": 2, "lockfile": 16}), fl.CONTROLLI, False, f, ORA)
    assert fl.stato(f, ORA)[0] == fl.OK


def test_stato_usa_l_ultima_riuscita_anche_se_dopo_ce_una_fallita(tmp_path):
    f = tmp_path / "e.jsonl"
    _scrivi_riuscita(f, ORA)
    fl.registra(_esito({"osv": 4, "digest": 0, "lockfile": 0}), fl.CONTROLLI, False, f, ORA + dt.timedelta(days=2))
    codice, righe = fl.stato(f, ORA + dt.timedelta(days=3))
    assert codice == fl.OK and "NON riuscita" in righe[0] and fl.ultima_riuscita(f)["data"].startswith("2026-11-09")


def test_soglia_dichiarata_con_il_margine_sul_timer_settimanale():
    assert fl.SOGLIA_ESECUZIONE_GIORNI > 7
