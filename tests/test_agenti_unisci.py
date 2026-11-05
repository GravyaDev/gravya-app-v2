"""`scripts/agenti.py worktree-unisci`: controllo obbligatorio prima del merge in main.

Git reale su repository temporanei; i controlli (OSV e suite) sono sostituiti
da piccoli comandi Python che riescono o falliscono, perche' qui si prova la
logica del comando (rifiuta senza toccare main / unisce senza push), non OSV
ne' la suite.
"""
from __future__ import annotations

import argparse
import datetime as dt
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


def unisci(controlli, messaggio="merge di prova", monkeypatch=None, fornitura=(True, "eseguito di recente"), forza=False):
    monkeypatch.setattr(agenti, "comandi_controllo", lambda dove: controlli)
    monkeypatch.setattr(agenti, "stato_fornitura", lambda: fornitura)
    agenti.cmd_worktree_unisci(argparse.Namespace(nome="prova", messaggio=messaggio, forza_fornitura=forza))


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


def test_merge_che_fallisce_viene_annullato_e_main_resta_com_era(ambiente, monkeypatch):
    """Il merge fallisce (hook pre-merge-commit che rifiuta): merge annullato, nessun merge a meta'."""
    princ, _ = ambiente
    hook = princ / ".git" / "hooks" / "pre-merge-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "annullato" in str(e.value)
    assert git(princ, "rev-parse", "main").strip() == prima
    assert git(princ, "status", "--porcelain", "--untracked-files=no").strip() == ""


def test_main_andato_avanti_rifiuta_senza_eseguire_i_controlli(ambiente, monkeypatch, tmp_path):
    princ, wt = ambiente
    (princ / "c.txt").write_text("da main\n")
    git(princ, "add", "c.txt")
    git(princ, "commit", "-q", "-m", "main avanti")
    traccia = tmp_path / "controlli-partiti"
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", [sys.executable, "-c", f"open({str(traccia)!r}, 'w').close()"])], monkeypatch=monkeypatch)
    assert "RIFIUTATO" in str(e.value) and "aggiorna il branch" in str(e.value)
    assert not traccia.exists() and git(princ, "rev-parse", "main").strip() == prima
    # dopo l'aggiornamento del branch (merge di main nel worktree) l'unione riesce
    git(wt, "merge", "-q", "main", "-m", "aggiorna")
    unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert (princ / "b.txt").is_file() and (princ / "c.txt").is_file()


def test_head_del_worktree_diverso_dal_branch_rifiuta(ambiente, monkeypatch, tmp_path):
    """Prova R4 del code-reviewer: worktree in detached HEAD su main, branch con un commit difettoso."""
    princ, wt = ambiente
    git(wt, "checkout", "-q", "--detach", "main")
    traccia = tmp_path / "controlli-partiti"
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", [sys.executable, "-c", f"open({str(traccia)!r}, 'w').close()"])], monkeypatch=monkeypatch)
    assert "HEAD" in str(e.value) and "punta" in str(e.value)
    assert not traccia.exists() and git(princ, "rev-parse", "main").strip() == prima
    assert not (princ / "b.txt").exists()


def test_head_del_worktree_su_un_altro_commit_dello_stesso_branch_rifiuta(ambiente, monkeypatch):
    princ, wt = ambiente
    git(wt, "checkout", "-q", "--detach", "HEAD~1")
    with pytest.raises(SystemExit) as e:
        unisci([("a", SUCCESSO)], monkeypatch=monkeypatch)
    assert "HEAD" in str(e.value) and not (princ / "b.txt").exists()


def test_messaggio_vuoto_rifiuta(ambiente, monkeypatch):
    with pytest.raises(SystemExit):
        unisci([("a", SUCCESSO)], messaggio="  ", monkeypatch=monkeypatch)


def test_i_controlli_reali_sono_osv_e_suite_nel_worktree(tmp_path):
    comandi = agenti.comandi_controllo(tmp_path)
    assert [c[0] for c in comandi][:1] + [c[0] for c in comandi][2:3] == ["controllo OSV del lockfile", "suite dei test"]
    osv, suite = comandi[0][1], comandi[2][1]
    assert osv == [str(tmp_path / ".venv/bin/python"), "scripts/osv-check.py", "requirements.lock.txt"]
    assert suite == [str(tmp_path / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp=.pytest_basetemp", "tests"]


def test_il_comando_e_registrato_e_richiede_il_messaggio():
    r = subprocess.run([sys.executable, str(RADICE / "scripts" / "agenti.py"), "worktree-unisci", "x"], text=True, capture_output=True)
    assert r.returncode == 2 and "--messaggio" in r.stderr


def test_i_controlli_reali_includono_osv_degli_strumenti_e_le_prove_non_superuser(tmp_path):
    comandi = dict(agenti.comandi_controllo(tmp_path))
    py = str(tmp_path / ".venv/bin/python")
    assert comandi["controllo OSV dei lockfile degli strumenti"] == [py, "scripts/osv-check.py", "requirements-strumenti.lock.txt"]
    assert comandi["prove con ruolo non superuser"] == ["bash", "scripts/test-non-superuser.sh"]
    assert list(comandi)[-1] == "prove con ruolo non superuser"


def test_le_prove_non_superuser_ricevono_le_variabili_del_worktree(ambiente, monkeypatch):
    unisci([("prove con ruolo non superuser", VUOLE_ENV)], monkeypatch=monkeypatch)


def test_prove_non_superuser_fallite_rifiutano_e_main_non_cambia(ambiente, monkeypatch):
    princ, _ = ambiente
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("suite", SUCCESSO), ("prove con ruolo non superuser", FALLIMENTO)], monkeypatch=monkeypatch)
    assert "prove con ruolo non superuser" in str(e.value) and git(princ, "rev-parse", "main").strip() == prima


def test_fornitura_non_recente_rifiuta_e_main_non_cambia(ambiente, monkeypatch, tmp_path):
    princ, _ = ambiente
    traccia = tmp_path / "controlli-partiti"
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit) as e:
        unisci([("a", [sys.executable, "-c", f"open({str(traccia)!r}, 'w').close()"])], monkeypatch=monkeypatch,
               fornitura=(False, "ultimo riuscito 20 giorni fa"))
    assert "RIFIUTATO" in str(e.value) and "20 giorni" in str(e.value) and "--forza-fornitura" in str(e.value)
    assert not traccia.exists() and git(princ, "rev-parse", "main").strip() == prima


def test_fornitura_non_recente_con_forzatura_unisce_e_lo_scrive_nel_messaggio(ambiente, monkeypatch):
    princ, _ = ambiente
    unisci([("a", SUCCESSO)], "merge: lavoro", monkeypatch, fornitura=(False, "nessuna esecuzione riuscita"), forza=True)
    corpo = git(princ, "log", "-1", "--format=%B")
    assert corpo.startswith("merge: lavoro") and "Forzato" in corpo and "nessuna esecuzione riuscita" in corpo
    assert (princ / "b.txt").is_file()


def test_forzatura_non_salta_gli_altri_controlli(ambiente, monkeypatch):
    princ, _ = ambiente
    prima = git(princ, "rev-parse", "main").strip()
    with pytest.raises(SystemExit):
        unisci([("a", FALLIMENTO)], monkeypatch=monkeypatch, fornitura=(False, "x"), forza=True)
    assert git(princ, "rev-parse", "main").strip() == prima


def _traccia_con(home, giorni_fa, riuscita=True):
    """Scrive nella traccia del job (in `home`) una esecuzione di `giorni_fa` giorni fa."""
    f = agenti.modulo_fornitura()
    e = f.Esito()
    for c in f.CONTROLLI:
        codice = 0 if riuscita else f.ERRORE_CONTROLLO
        e.per_controllo[c] = {"codice": codice, "esito": f.etichette(codice)}
        e.codice |= codice
    f.registra(e, f.CONTROLLI, False, f.FILE_ESITI, dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=giorni_fa))
    return f


def test_stato_fornitura_legge_la_traccia_reale_del_job(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert agenti.stato_fornitura()[0] is False                                  # nessuna traccia
    f = _traccia_con(tmp_path, 1)
    assert f.FILE_ESITI == tmp_path / ".local/state/gravya-fornitura/esiti.jsonl"
    assert agenti.stato_fornitura()[0] is True
    (tmp_path / ".local/state/gravya-fornitura/esiti.jsonl").unlink()
    _traccia_con(tmp_path, f.SOGLIA_ESECUZIONE_GIORNI + 1)
    assert agenti.stato_fornitura()[0] is False                                  # oltre la soglia
    (tmp_path / ".local/state/gravya-fornitura/esiti.jsonl").unlink()
    _traccia_con(tmp_path, 1, riuscita=False)
    assert agenti.stato_fornitura()[0] is False                                  # recente ma fallita


def test_l_opzione_di_forzatura_e_registrata():
    r = subprocess.run([sys.executable, str(RADICE / "scripts" / "agenti.py"), "worktree-unisci", "--help"], text=True, capture_output=True)
    assert r.returncode == 0 and "--forza-fornitura" in r.stdout
