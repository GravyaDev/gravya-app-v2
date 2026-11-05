"""Unita' systemd utente della catena di fornitura e script di installazione (DECISIONS §6)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
INSTALLA = RADICE / "scripts" / "installa-timer-fornitura.sh"
SERVIZIO = (RADICE / "systemd" / "gravya-fornitura.service").read_text(encoding="utf-8")
TIMER = (RADICE / "systemd" / "gravya-fornitura.timer").read_text(encoding="utf-8")


def _installa(destinazione: Path, *extra: str):
    return subprocess.run(
        ["bash", str(INSTALLA), "--destinazione", str(destinazione), "--senza-systemctl", "--anche-da-worktree", *extra],
        text=True, capture_output=True,
    )


def test_timer_settimanale_persistente():
    assert re.search(r"^OnCalendar=Mon \*-\*-\* \d\d:\d\d:\d\d$", TIMER, re.M)  # un giorno della settimana, una volta
    assert "Persistent=true" in TIMER.splitlines()
    assert "Unit=gravya-fornitura.service" in TIMER.splitlines()
    assert "WantedBy=timers.target" in TIMER.splitlines()


def test_servizio_oneshot_nel_journal_e_codice_16_non_e_guasto():
    righe = SERVIZIO.splitlines()
    assert "Type=oneshot" in righe
    assert "StandardOutput=journal" in righe and "StandardError=journal" in righe
    assert "SuccessExitStatus=16" in righe  # PR aperta
    assert any(r.startswith("ExecStart=") and "scripts/fornitura-locale.py" in r for r in righe)


def test_installazione_sostituisce_il_percorso_ed_e_idempotente(tmp_path):
    dest = tmp_path / "user"
    r1 = _installa(dest)
    assert r1.returncode == 0, r1.stderr
    primo = {p.name: p.read_text() for p in dest.iterdir()}
    assert set(primo) == {"gravya-fornitura.service", "gravya-fornitura.timer"}  # nessun residuo .nuovo
    assert "@RADICE@" not in primo["gravya-fornitura.service"]
    assert f"{RADICE}/scripts/fornitura-locale.py" in primo["gravya-fornitura.service"]
    assert f"WorkingDirectory={RADICE}" in primo["gravya-fornitura.service"]
    r2 = _installa(dest)
    assert r2.returncode == 0
    assert {p.name: p.read_text() for p in dest.iterdir()} == primo


def test_installazione_da_worktree_si_rifiuta_senza_opzione(tmp_path):
    if (RADICE / ".git").is_dir():
        pytest.skip("non e' un worktree")
    r = subprocess.run(["bash", str(INSTALLA), "--destinazione", str(tmp_path), "--senza-systemctl"], text=True, capture_output=True)
    assert r.returncode == 2 and "worktree" in r.stderr
    assert list(tmp_path.iterdir()) == []


def test_opzione_sconosciuta(tmp_path):
    r = subprocess.run(["bash", str(INSTALLA), "--boh"], text=True, capture_output=True)
    assert r.returncode == 2


@pytest.mark.skipif(shutil.which("systemd-analyze") is None or bool(os.environ.get("GITHUB_ACTIONS")),
                    reason="systemd-analyze assente, o runner di GitHub senza sessione utente systemd: si verifica in locale")
def test_systemd_analyze_verify(tmp_path):
    dest = tmp_path / "user"
    assert _installa(dest).returncode == 0
    r = subprocess.run(["systemd-analyze", "--user", "verify", str(dest / "gravya-fornitura.service"), str(dest / "gravya-fornitura.timer")],
                       text=True, capture_output=True)
    assert r.returncode == 0 and r.stderr.strip() == "", r.stderr


def _installa_con_systemctl_finto(tmp_path: Path, attivo: bool):
    """Esegue lo script con un `systemctl` finto in testa al PATH: registra gli argomenti, `is-active` risponde come richiesto."""
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    registro = tmp_path / "systemctl.log"
    stub = bin_ / "systemctl"
    stub.write_text(
        "#!/bin/sh\n"
        'echo "$*" >> "%s"\n'
        'case "$*" in *is-active*) exit %d ;; esac\n'
        "exit 0\n" % (registro, 0 if attivo else 3)
    )
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}")
    r = subprocess.run(["bash", str(INSTALLA), "--destinazione", str(tmp_path / "user"), "--anche-da-worktree"],
                       text=True, capture_output=True, env=env)
    comandi = [riga.replace("--user ", "") for riga in registro.read_text().splitlines()] if registro.exists() else []
    return r, comandi


def test_installazione_su_timer_gia_attivo_rilegge_e_riavvia(tmp_path):
    r, comandi = _installa_con_systemctl_finto(tmp_path, attivo=True)
    assert r.returncode == 0, r.stderr
    assert comandi.index("daemon-reload") < comandi.index("enable --now gravya-fornitura.timer") < comandi.index("restart gravya-fornitura.timer")
    assert "riavviato" in r.stdout


def test_installazione_su_timer_non_attivo_non_riavvia(tmp_path):
    r, comandi = _installa_con_systemctl_finto(tmp_path, attivo=False)
    assert r.returncode == 0, r.stderr
    assert "daemon-reload" in comandi and "enable --now gravya-fornitura.timer" in comandi
    assert not any(c.startswith("restart") for c in comandi)


def test_senza_systemctl_non_chiama_systemctl(tmp_path):
    r, comandi = _installa_con_systemctl_finto(tmp_path, attivo=True)   # per avere il registro
    (tmp_path / "systemctl.log").unlink()
    env = dict(os.environ, PATH=f"{tmp_path / 'bin'}:{os.environ['PATH']}")
    r = subprocess.run(["bash", str(INSTALLA), "--destinazione", str(tmp_path / "u2"), "--senza-systemctl", "--anche-da-worktree"],
                       text=True, capture_output=True, env=env)
    assert r.returncode == 0 and not (tmp_path / "systemctl.log").exists()
