"""`scripts/fornitura-locale.py` (controlli settimanali in locale, DECISIONS §6).

Offline: i comandi esterni (`gh`, `docker`, OSV) sono sostituiti da un
esecutore finto che registra le chiamate; git e' reale, su repository
temporanei (origin = repository bare in `tmp_path`). Nessuna rete.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import subprocess
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("fornitura_locale", RADICE / "scripts" / "fornitura-locale.py")
fl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fl)

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


class Finto:
    """Esecutore finto: `risposte` = {prefisso del comando: CompletedProcess}. Git passa al vero."""

    def __init__(self, risposte=None, reale_git=False):
        self.chiamate: list[list[str]] = []
        self.risposte = risposte or {}
        self.reale_git = reale_git

    def __call__(self, cmd, cwd=None, timeout=0):
        self.chiamate.append(list(cmd))
        for prefisso, r in self.risposte.items():
            if " ".join(cmd).startswith(prefisso):
                return r
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
    run = Finto({"gh issue list": cp(0, "Altra issue\n")})
    codice, _ = fl.segnala([("vulnerabilita", "x==1: GHSA-x")], run)
    creazioni = run.con("gh issue create")
    assert codice == fl.OK and len(creazioni) == 1
    c = creazioni[0]
    assert c[c.index("--title") + 1] == fl.TITOLI["vulnerabilita"]
    assert c[c.index("--assignee") + 1] == "GravyaDev"
    assert "GHSA-x" in c[c.index("--body") + 1]


def test_issue_non_duplicata_se_gia_aperta_con_lo_stesso_titolo():
    run = Finto({"gh issue list": cp(0, fl.TITOLI["digest"] + "\n")})
    codice, msg = fl.segnala([("digest", "d"), ("vulnerabilita", "v")], run)
    creazioni = run.con("gh issue create")
    assert [c[c.index("--title") + 1] for c in creazioni] == [fl.TITOLI["vulnerabilita"]]  # solo quella nuova
    assert any("non duplicata" in m for m in msg)


def test_issue_titoli_distinti_per_tipo():
    assert len(set(fl.TITOLI.values())) == len(fl.TITOLI)


def test_issue_gh_che_fallisce_da_codice_32_non_silenzio():
    assert fl.segnala([("digest", "d")], Finto({"gh issue list": cp(1, "", "auth")}))[0] == fl.ERRORE_ISSUE
    run = Finto({"gh issue list": cp(0, ""), "gh issue create": cp(1, "", "boom")})
    assert fl.segnala([("digest", "d")], run)[0] == fl.ERRORE_ISSUE


def test_prova_non_apre_nulla():
    run = Finto()
    codice, msg = fl.segnala([("digest", "d")], run, prova=True)
    assert codice == fl.OK and run.chiamate == [] and "prova" in msg[0]


def test_esegui_controlli_combina_i_codici_e_segnala(repo_ci):
    run = Finto({"gh issue list": cp(0, ""), "docker": cp(0, DIGEST_B), fl.sys.executable: cp(1, "", "GHSA-x")})
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
