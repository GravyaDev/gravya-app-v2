"""Prove di rottura del code-reviewer su impl/ci-locale. Carica gli script dal worktree.
Uso: WT=<worktree> <python> -m pytest -q -p no:cacheprovider --basetemp=<cartella> test_rotture.py
"""
import argparse, importlib.util, os, subprocess, sys, datetime as dt
from pathlib import Path
import pytest

WT = Path(os.environ["WT"])

def carica(nome, file):
    s = importlib.util.spec_from_file_location(nome, WT / "scripts" / file)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

fl = carica("fl", "fornitura-locale.py")
ag = carica("ag", "agenti.py")
DIG = "sha256:" + "a" * 64
CI = f"jobs:\n  t:\n    services:\n      postgres:\n        image: postgres:18@{DIG}\n"
LOCK = "# pip-compile --generate-hashes --output-file=requirements.lock.txt pyproject.toml\nalembic==1.0 \\\n    --hash=sha256:aa\n"
LOCK_STRANO = LOCK + "pacchetto @ https://example.org/p.whl\n"   # formato che osv-check rifiuta (ErroreLockfile)

def cp(c=0, o="", e=""): return subprocess.CompletedProcess([], c, o, e)

def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.org", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout

class Finto:
    def __init__(self, risposte): self.chiamate, self.risposte = [], risposte
    def __call__(self, cmd, cwd=None, timeout=0):
        self.chiamate.append((list(cmd), cwd))
        for p, r in self.risposte.items():
            if " ".join(cmd).startswith(p): return r
        if cmd[0] == "git": return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        return cp()

@pytest.fixture
def repo(tmp_path):
    origin = tmp_path / "o.git"; git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    p = tmp_path / "p"; git(tmp_path, "clone", "-q", str(origin), str(p))
    (p / ".github/workflows").mkdir(parents=True); (p / ".github/workflows/ci.yml").write_text(CI)
    (p / "requirements.lock.txt").write_text(LOCK)
    git(p, "add", "."); git(p, "commit", "-q", "-m", "b"); git(p, "push", "-q", "origin", "HEAD:main"); git(p, "fetch", "-q", "origin")
    return p

def test_R1_eccezione_non_gestita_nel_lockfile_perde_la_issue_della_vulnerabilita(repo):
    """OSV trova una vulnerabilita' (rc 1); il lockfile rigenerato ha una riga in formato non atteso:
    differenze() solleva ErroreLockfile, non catturata -> esegui_controlli non arriva a segnala():
    nessuna issue per la vulnerabilita' gia' rilevata."""
    run = Finto({fl.sys.executable: cp(1, "", "x==1: GHSA-x"), "gh issue list": cp(0, "")})
    def compila(s, l, a): (s / "requirements.lock.txt").write_text(LOCK_STRANO)
    with pytest.raises(Exception) as e:
        fl.esegui_controlli(repo, ("osv", "lockfile"), False, run, oggi=dt.date(2026, 11, 9), compila=compila)
    print("ECCEZIONE:", type(e.value).__name__, e.value)
    assert [c for c, _ in run.chiamate if c[:3] == ["gh", "issue", "create"]] == []   # nessuna issue aperta
    # e il processo esce con la traceback (codice 1 = lo stesso di «vulnerabilita'»), non con un codice dello schema

def test_R2_gh_non_riceve_cwd_quindi_dipende_dalla_cartella_di_lancio(repo):
    """`gh issue list|create` e `gh pr list` partono senza cwd: se lo script e' lanciato a mano da un'altra
    cartella, gh sceglie il repository da QUELLA cartella (nel timer c'e' WorkingDirectory)."""
    run = Finto({"gh issue list": cp(0, ""), "gh pr list": cp(0, "[]")})
    fl.segnala([("digest", "d")], run)
    def compila(s, l, a): (s / "requirements.lock.txt").write_text(LOCK.replace("1.0", "1.1"))
    fl.aggiorna_lockfile(repo, run, oggi=dt.date(2026, 11, 9), compila=compila)
    gh = [(c[:3], cwd) for c, cwd in run.chiamate if c[0] == "gh"]
    print(gh)
    assert all(cwd is None for c, cwd in gh if c[1] in ("issue", ) or c[:3] == ["gh", "pr", "list"])

def test_R3_timeout_con_output_parziale_fa_TypeError_in_controlla_osv(tmp_path):
    """TimeoutExpired.stdout e' bytes anche con text=True: esegui() lo passa com'e'."""
    r = fl.esegui([sys.executable, "-c", "import time,sys; print('parziale', flush=True); time.sleep(5)"], timeout=1)
    print("tipo stdout:", type(r.stdout))
    assert isinstance(r.stdout, str)

@pytest.fixture
def amb(tmp_path, monkeypatch):
    princ = tmp_path / "pr"; princ.mkdir(); git(princ, "init", "-q", "-b", "main")
    (princ / "a.txt").write_text("b\n"); git(princ, "add", "."); git(princ, "commit", "-q", "-m", "b")
    (princ / ".worktrees").mkdir()
    git(princ, "worktree", "add", "-q", "-b", "impl/prova", str(princ / ".worktrees/prova"), "main")
    wt = princ / ".worktrees/prova"
    (wt / "cattivo.txt").write_text("x\n"); git(wt, "add", "."); git(wt, "commit", "-q", "-m", "commit con il difetto")
    (princ / ".worktrees/prova.env").write_text("A=1\n")
    monkeypatch.setattr(ag, "RADICE", princ); monkeypatch.setattr(ag, "WORKTREE", princ / ".worktrees")
    monkeypatch.setattr(ag, "git", lambda *a, cwd=None, check=True: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@e.org", *a], cwd=cwd or princ, text=True, capture_output=True, check=check))
    return princ, wt

def test_R4_worktree_unisci_prova_il_worktree_non_il_branch_che_unisce(amb, monkeypatch):
    """Il controllo «passa» se cattivo.txt non c'e' nella cartella del worktree. Il worktree e' stato
    messo in detached HEAD su main (branch impl/prova libero, con il commit difettoso): i controlli
    girano su main, il merge porta il commit difettoso in main."""
    princ, wt = amb
    git(wt, "switch", "-q", "--detach", "main")
    controllo = [sys.executable, "-c", "import os,sys; sys.exit(1 if os.path.exists('cattivo.txt') else 0)"]
    monkeypatch.setattr(ag, "comandi_controllo", lambda d: [("controllo", controllo)])
    ag.cmd_worktree_unisci(argparse.Namespace(nome="prova", messaggio="m"))
    assert (princ / "cattivo.txt").exists()      # unito in main nonostante il controllo avrebbe fallito sul branch
