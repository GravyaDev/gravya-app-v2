"""Script di CI `scripts/osv-check.py` (catena di fornitura, DECISIONS §4).

Offline: la funzione di rete e' sostituita da una finta. Il caso reale
(esito su OSV) e' provato dalla CI e dal report.
"""
from __future__ import annotations

import http.server
import importlib.util
import socket
import threading
from pathlib import Path

import pytest

_PERCORSO = Path(__file__).resolve().parent.parent / "scripts" / "osv-check.py"
_spec = importlib.util.spec_from_file_location("osv_check", _PERCORSO)
osv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(osv)

LOCK = """\
# commento
alembic==1.20.1 \\
    --hash=sha256:aa \\
    --hash=sha256:bb
    # via gravya-e1 (pyproject.toml)
tomli==2.0.0 ; python_version < "3.11" \\
    --hash=sha256:cc
"""


def test_legge_solo_le_righe_dei_pacchetti():
    assert osv.leggi_lockfile(LOCK) == [("alembic", "1.20.1"), ("tomli", "2.0.0")]


def test_vulnerabile_elencato_e_pulito_no():
    def invia(url, corpo):
        assert url == osv.OSV_URL
        q = corpo["queries"]
        assert q[0]["package"] == {"name": "alembic", "ecosystem": osv.ECOSISTEMA}
        assert q[0]["version"] == "1.20.1"
        return {"results": [{}, {"vulns": [{"id": "GHSA-x"}]}]}

    ris = osv.interroga([("alembic", "1.20.1"), ("tomli", "2.0.0")], invia)
    assert ris == {("tomli", "2.0.0"): ["GHSA-x"]}


def test_paginazione_seguita():
    chiamate = []

    def invia(url, corpo):
        chiamate.append(corpo["queries"][0].get("page_token"))
        if len(chiamate) == 1:
            return {"results": [{"vulns": [{"id": "A"}], "next_page_token": "t2"}]}
        return {"results": [{"vulns": [{"id": "B"}]}]}

    assert osv.interroga([("x", "1")], invia) == {("x", "1"): ["A", "B"]}
    assert chiamate == [None, "t2"]


def test_blocchi_rispettano_il_limite(monkeypatch):
    monkeypatch.setattr(osv, "DIMENSIONE_BLOCCO", 2)
    dimensioni = []

    def invia(url, corpo):
        dimensioni.append(len(corpo["queries"]))
        return {"results": [{} for _ in corpo["queries"]]}

    osv.interroga([("a", "1"), ("b", "1"), ("c", "1")], invia)
    assert dimensioni == [2, 1]


@pytest.mark.parametrize(
    "risposta",
    [{}, {"results": []}, {"results": [{}, {}]}, {"results": ["x"]}, {"results": [{"vulns": [{}]}]}, []],
)
def test_risposta_non_valida_e_errore_non_pulito(risposta):
    with pytest.raises(osv.ErroreOsv):
        osv.interroga([("a", "1")], lambda u, c: risposta)


def test_main_vulnerabile_pulito_vuoto_e_rete(tmp_path, monkeypatch, capsys):
    lock = tmp_path / "l.txt"
    lock.write_text(LOCK)
    reale = osv.interroga

    def con(risposta):
        monkeypatch.setattr(osv, "interroga", lambda p: reale(p, lambda u, c: risposta))

    con({"results": [{}, {"vulns": [{"id": "GHSA-x"}]}]})
    assert osv.main(["x", str(lock)]) == 1
    assert "tomli==2.0.0: GHSA-x" in capsys.readouterr().err

    con({"results": [{}, {}]})
    assert osv.main(["x", str(lock)]) == 0

    vuoto = tmp_path / "v.txt"
    vuoto.write_text("# niente\n")
    assert osv.main(["x", str(vuoto)]) == 2
    assert osv.main(["x", str(tmp_path / "manca.txt")]) == 2

    def rete_giu(u, c):
        raise osv.ErroreOsv("giu")

    monkeypatch.setattr(osv, "interroga", lambda p: reale(p, rete_giu))
    assert osv.main(["x", str(lock)]) == 2


# --- Percorso di rete reale (invia_http): server locale su 127.0.0.1 ---------

LOCK_UNO = "requests==2.0.0 \\\n    --hash=sha256:aa\n"


def _server_locale(corpo: bytes, stato: int = 200, lunghezza: int | None = None, attesa: float = 0):
    class Gestore(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if attesa:
                threading.Event().wait(attesa)
            self.send_response(stato)
            if lunghezza is not None:
                self.send_header("Content-Length", str(lunghezza))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *a):
            pass

    s = http.server.HTTPServer(("127.0.0.1", 0), Gestore)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def _esegui(tmp_path, monkeypatch, url, capsys):
    monkeypatch.setattr(osv, "OSV_URL", url)
    lock = tmp_path / "l.txt"
    lock.write_text(LOCK_UNO)
    codice = osv.main(["x", str(lock)])
    return codice, capsys.readouterr().err


def _porta_chiusa() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


CASI_RETE = {
    "stato_500": dict(corpo=b"", stato=500),
    "stato_404": dict(corpo=b"{}", stato=404),
    "stato_204": dict(corpo=b"", stato=204),
    "corpo_non_json": dict(corpo=b"<html>no</html>"),
    "corpo_non_utf8": dict(corpo=b"\xff\xfe"),
    "risposta_troncata": dict(corpo=b'{"res', lunghezza=500),
}


@pytest.mark.parametrize("caso", sorted(CASI_RETE))
def test_invia_http_errori_danno_codice_2(caso, tmp_path, monkeypatch, capsys):
    s = _server_locale(**CASI_RETE[caso])
    try:
        codice, err = _esegui(tmp_path, monkeypatch, f"http://127.0.0.1:{s.server_port}/q", capsys)
    finally:
        s.shutdown()
        s.server_close()
    assert codice == 2
    assert "ERRORE:" in err and "Traceback" not in err


def test_invia_http_rete_non_raggiungibile_codice_2(tmp_path, monkeypatch, capsys):
    codice, err = _esegui(tmp_path, monkeypatch, f"http://127.0.0.1:{_porta_chiusa()}/q", capsys)
    assert codice == 2
    assert "ERRORE:" in err


def test_invia_http_timeout_codice_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(osv, "TIMEOUT_SECONDI", 0.2)
    s = _server_locale(b"{}", attesa=2)
    try:
        codice, err = _esegui(tmp_path, monkeypatch, f"http://127.0.0.1:{s.server_port}/q", capsys)
    finally:
        s.shutdown()
        s.server_close()
    assert codice == 2
    assert "ERRORE:" in err


def test_invia_http_risposta_valida_passa_per_la_rete_reale(tmp_path, monkeypatch, capsys):
    """Controprova: il percorso reale non fallisce sempre; vulnerabilita' => 1, pulito => 0."""
    for corpo, atteso in ((b'{"results": [{"vulns": [{"id": "GHSA-x"}]}]}', 1), (b'{"results": [{}]}', 0)):
        s = _server_locale(corpo)
        try:
            codice, _ = _esegui(tmp_path, monkeypatch, f"http://127.0.0.1:{s.server_port}/q", capsys)
        finally:
            s.shutdown()
            s.server_close()
        assert codice == atteso
