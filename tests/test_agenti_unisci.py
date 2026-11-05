"""`scripts/agenti.py worktree-unisci`: controllo obbligatorio prima del merge in main.

Git reale su repository temporanei; i controlli (OSV e suite) sono sostituiti
da piccoli comandi Python che riescono o falliscono, perche' qui si prova la
logica del comando (rifiuta senza toccare main / unisce senza push), non OSV
ne' la suite.
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("agenti", RADICE / "scripts" / "agenti.py")
agenti = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agenti)

SUCCESSO = [sys.executable, "-c", "pass"]
FALLIMENTO = [sys.executable, "-c", "import sys; sys.exit(3)"]
# Riesce solo se le variabili del file .env del worktree sono arrivate al comando.
VUOLE_ENV = [sys.executable, "-c", "import os, sys; sys.exit(0 if os.environ.get('PGPORT') == '5433' and os.environ.get('GRAVYA_E1_TEST_DSN') == 'host=127.0.0.1 port=5433 user=root' else 9)"]


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *a], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    princ = tmp_path / "principale"
    princ.mkdir()
    git(princ, "init", "-q", "-b", "main")
    (princ / "a.txt").write_text("base\n")
    git(princ, "add", ".")
    git(princ, "commit", "-q", "-m", "base")
    (princ / ".worktrees").mkdir()
    git(princ, "worktree", "add", "-q", "-b", "impl/prova", str(princ / ".worktrees" / "prova"), "main")
    wt = princ / ".worktrees" / "prova"
    (wt / "b.txt").write_text("nuovo\n")
    git(wt, "add", ".")
    git(wt, "commit", "-q", "-m", "lavoro")
    (princ / ".worktrees" / "prova.env").write_text('PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development\n')
    monkeypatch.setattr(agenti, "RADICE", princ)
    monkeypatch.setattr(agenti, "WORKTREE", princ / ".worktrees")
    # `git()` ha cwd=RADICE legato come default alla definizione: lo rilego.
    monkeypatch.setattr(agenti, "git", lambda *a, cwd=None, check=True: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.org", *a], cwd=cwd or princ, text=True, capture_output=True, check=check))
    return princ, wt


def unisci(controlli, messaggio="merge di prova", monkeypatch=None):
    monkeypatch.setattr(agenti, "comandi_controllo", lambda dove: controlli)
    agenti.cmd_worktree_unisci(argparse.Namespace(nome="prova", messaggio=messaggio))


def test_controlli_riusciti_merge_no_ff_con_messaggio_senza_push(ambiente, monkeypatch, capsys):
    princ, _ = ambiente
    unisci([("a", SUCCESSO), ("b", VUOLE_ENV)], "merge: lavoro di prova", monkeypatch)
    assert git(princ, "log", "-1", "--format=%s").strip() == "merge: lavoro di prova"
    assert len(git(princ, "log", "-1", "--format=%P").split()) == 2  # --no-ff: due genitori
    assert (princ / "b.txt").is_file()
    assert "nessun push" in capsys.readouterr().out
    assert git(princ, "remote").strip() == ""  # e nessun remoto da cui spingere


@pytest.mark.parametrize("controlli", [
    [("osv", FALLIMENTO), ("suite", SUCCESSO)],
    [("osv", SUCCESSO), ("suite", FALLIMENTO)],
    [("osv", FALLIMENTO), ("suite", FALLIMENTO)],
])
def test_un_controllo_fallito_rifiuta_e_main_non_cambia(ambiente, monkeypatch, controlli):
    princ, _ = ambiente
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci(controlli, monkeypatch=monkeypatch)
    assert "RIFIUTATO" in str(e.value) and "non è stato toccato" in str(e.value)
    assert git(princ, "rev-parse", "main").strip() == prima
    assert not (princ / "b.txt").exists()


def test_se_osv_fallisce_la_suite_non_parte(ambiente, monkeypatch, tmp_path):
    traccia = tmp_path / "suite-partita"
    suite = [sys.executable, "-c", f"open({str(traccia)!r}, 'w').close()"]
    with pytest.raises(SystemExit):
        unisci([("osv", FALLIMENTO), ("suite", suite)], monkeypatch=monkeypatch)
    assert not traccia.exists()


def test_variabili_del_file_env_arrivano_ai_controlli(ambiente, monkeypatch):
    unisci([("env", VUOLE_ENV)], monkeypatch=monkeypatch)  # niente SystemExit: l'env c'era


def test_file_env_mancante_rifiuta(ambiente, monkeypatch):
    princ, _ = ambiente
    (princ / ".worktrees" / "prova.env").unlink()
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "prova.env" in str(e.value) and git(princ, "rev-parse", "main").strip() == prima


def test_worktree_con_modifiche_non_committate_rifiuta(ambiente, monkeypatch):
    princ, wt = ambiente
    (wt / "sporco.txt").write_text("x")
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "non committate" in str(e.value) and git(princ, "rev-parse", "main").strip() == prima


def test_principale_non_su_main_rifiuta(ambiente, monkeypatch):
    princ, _ = ambiente
    git(princ, "switch", "-q", "-c", "altro")
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "non su main" in str(e.value) and git(princ, "rev-parse", "main").strip() == prima


def test_conflitto_annulla_il_merge_e_main_resta_com_era(ambiente, monkeypatch):
    princ, wt = ambiente
    (wt / "a.txt").write_text("dal branch\n")
    git(wt, "commit", "-q", "-am", "tocca a")
    (princ / "a.txt").write_text("da main\n")
    git(princ, "commit", "-q", "-am", "main tocca a")
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "annullato" in str(e.value)
    assert git(princ, "rev-parse", "main").strip() == prima
    assert git(princ, "status", "--porcelain", "--untracked-files=no").strip() == ""  # nessun merge a metà


def test_messaggio_vuoto_rifiuta(ambiente, monkeypatch):
    with pytest.raises(SystemExit):
        unisci([("a", SUCCESSO)], messaggio="  ", monkeypatch=monkeypatch)


def test_i_controlli_reali_sono_osv_e_suite_nel_worktree(tmp_path):
    comandi = agenti.comandi_controllo(tmp_path)
    assert [c[0] for c in comandi] == ["controllo OSV del lockfile", "suite dei test"]
    osv, suite = comandi[0][1], comandi[1][1]
    assert osv == [str(tmp_path / ".venv/bin/python"), "scripts/osv-check.py", "requirements.lock.txt"]
    assert suite == [str(tmp_path / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp=.pytest_basetemp", "tests"]


def test_il_comando_e_registrato_e_richiede_il_messaggio():
    r = subprocess.run([sys.executable, str(RADICE / "scripts" / "agenti.py"), "worktree-unisci", "x"], text=True, capture_output=True)
    assert r.returncode == 2 and "--messaggio" in r.stderr
