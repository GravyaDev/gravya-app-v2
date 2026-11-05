"""Prove di rottura del giro 2. Uso: WT=<worktree> <python> -m pytest -q -p no:cacheprovider --basetemp=<cartella> test_rotture2.py
Un test che PASSA = difetto riprodotto (documentato nel nome)."""
import importlib.util, json, os, subprocess, datetime as dt
from pathlib import Path
import pytest

WT = Path(os.environ["WT"])
def carica(nome, file):
    s = importlib.util.spec_from_file_location(nome, WT / "scripts" / file)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fl = carica("fl", "fornitura-locale.py")

def riga(data, codice=0):
    esiti = {c: {"codice": 0, "esito": ["ok"]} for c in fl.CONTROLLI}
    return json.dumps({"data": data, "prova": False, "controlli": list(fl.CONTROLLI), "codice": codice, "esiti": esiti, "versioni": {}})

ORA = dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc)

def test_P1_data_senza_fuso_nella_traccia_rompe_stato_con_traceback(tmp_path):
    """Una riga con data ISO senza fuso orario passa il filtro di leggi_esecuzioni (fromisoformat ok)
    ma `ora - naive` solleva TypeError: --stato esce con traceback (codice 1), worktree-unisci idem."""
    f = tmp_path / "e.jsonl"; f.write_text(riga("2026-11-19T10:00:00") + "\n")
    with pytest.raises(TypeError):
        fl.stato(f, ORA)

def test_P2_riga_riuscita_senza_chiave_esito_rompe_stato(tmp_path):
    esiti = {c: {"codice": 0} for c in fl.CONTROLLI}
    f = tmp_path / "e.jsonl"
    f.write_text(json.dumps({"data": "2026-11-19T10:00:00+00:00", "prova": False, "codice": 0, "esiti": esiti}) + "\n")
    with pytest.raises(KeyError):
        fl.stato(f, ORA)

def test_P3_data_futura_vale_come_fresca(tmp_path):
    f = tmp_path / "e.jsonl"; f.write_text(riga("2027-12-31T00:00:00+00:00") + "\n")
    codice, _ = fl.stato(f, ORA)
    assert codice == fl.OK   # un orologio sbagliato (o una riga falsa) rende «fresca» la traccia per sempre

def test_P4_confine_esatto_della_soglia(tmp_path):
    f = tmp_path / "e.jsonl"
    f.write_text(riga((ORA - dt.timedelta(days=fl.SOGLIA_ESECUZIONE_GIORNI)).isoformat()) + "\n")
    assert fl.stato(f, ORA)[0] == fl.OK            # esattamente 9 giorni: ancora fresca
    f.write_text(riga((ORA - dt.timedelta(days=fl.SOGLIA_ESECUZIONE_GIORNI, seconds=1)).isoformat()) + "\n")
    assert fl.stato(f, ORA)[0] == fl.STATO_SCADUTO

def test_P5_ripulisci_casi_limite():
    assert "ghp_" not in fl.ripulisci("t ghp_" + "A" * 36)
    assert "secret" not in fl.ripulisci("https://user:secret@github.com/o/r")
    assert "secret" not in fl.ripulisci("git clone https://x-access-token:secret@github.com/o/r.git")
    print("Bearer:", fl.ripulisci("Authorization: Bearer abcdef0123456789abcdef"))
    print("ssh url:", fl.ripulisci("ssh://deploy:secret@host/r"))
    print("token corto:", fl.ripulisci("ghp_abc"))
