"""Strumenti del job settimanale (pip-tools) fissati con versione e hash (compliance-auditor 3)."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("fornitura_locale", RADICE / "scripts" / "fornitura-locale.py")
fl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fl)

LOCK = (RADICE / fl.LOCKFILE_STRUMENTI).read_text(encoding="utf-8")


def _blocchi(testo: str) -> dict[str, str]:
    """{nome: righe del blocco} per le righe `nome==versione \\` a colonna 0."""
    out, nome = {}, None
    for riga in testo.splitlines():
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==(\S+)", riga)
        if m:
            nome = m.group(1)
            out[nome] = riga
        elif nome and riga.startswith(" "):
            out[nome] += "\n" + riga
    return out


def test_ogni_pacchetto_degli_strumenti_ha_versione_esatta_e_hash():
    blocchi = _blocchi(LOCK)
    assert fl.PACCHETTO_COMPILE in blocchi and len(blocchi) >= 2    # pip-tools e le sue dipendenze
    for nome, testo in blocchi.items():
        assert re.search(r"^[^\s]+==\d", testo), nome
        assert re.search(r"--hash=sha256:[0-9a-f]{64}", testo), f"{nome} senza hash"


def test_intestazione_con_il_comando_di_rigenerazione():
    m = re.search(r"^#\s+pip-compile\s+(.+)$", LOCK, re.M)
    assert m and "--generate-hashes" in m.group(1) and "--output-file=requirements-strumenti.lock.txt" in m.group(1)
    assert m.group(1).split()[-1] == "requirements-strumenti.in"
    assert (RADICE / "requirements-strumenti.in").read_text(encoding="utf-8").count("pip-tools==") == 1


def test_la_versione_per_la_traccia_e_quella_del_file():
    assert fl.versione_strumenti(RADICE) == _blocchi(LOCK)["pip-tools"].split("==")[1].split()[0]
    assert fl.versione_strumenti(RADICE / "inesistente") == "sconosciuta"


def test_il_file_degli_strumenti_e_tra_quelli_controllati_da_osv_e_dalla_base():
    assert fl.LOCKFILE_STRUMENTI in fl.LOCKFILE_CONTROLLATI and fl.LOCKFILE in fl.LOCKFILE_CONTROLLATI
    assert fl.LOCKFILE_STRUMENTI in fl.FILE_BASE_LOCKFILE and "pyproject.toml" in fl.FILE_BASE_LOCKFILE


def test_osv_e_chiamato_su_entrambi_i_lockfile():
    chiamate = []

    def run(cmd, cwd=None, timeout=0):
        import subprocess
        chiamate.append(cmd)
        return subprocess.CompletedProcess(cmd, 1 if cmd[-1].endswith(fl.LOCKFILE_STRUMENTI) else 0, "", "x==1: GHSA-x")

    e = fl.controlla_osv_tutti(RADICE, run)
    assert [Path(c[-1]).name for c in chiamate] == [fl.LOCKFILE, fl.LOCKFILE_STRUMENTI]
    assert e.codice == fl.VULNERABILITA and fl.LOCKFILE_STRUMENTI in e.problemi[0][1]
