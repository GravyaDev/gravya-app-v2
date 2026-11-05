"""Prova del code-reviewer: lo strato di rete di scripts/osv-check.py non e' coperto dai test del branch.

Uso (dalla radice del worktree):
  OSV_SCRIPT=scripts/osv-check.py python -I -m pytest -q -p no:cacheprovider <questo file>
Su un mutante di osv-check.py in cui invia_http ingoia l'errore, la suite
tests/test_ci_osv_check.py resta verde (11 passed) e QUESTO test fallisce.
"""
import http.server, importlib.util, os, threading
from pathlib import Path

_spec = importlib.util.spec_from_file_location("osv_check", Path(os.environ["OSV_SCRIPT"]).resolve())
osv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(osv)

LOCK = "requests==2.0.0 \\\n    --hash=sha256:aa\n"


def _server(body_bytes, status=200, length=None):
    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            self.send_response(status)
            if length is not None:
                self.send_header("Content-Length", str(length))
            self.end_headers(); self.wfile.write(body_bytes)
        def log_message(self, *a): pass
    s = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_osv_irraggiungibile_esce_con_errore(tmp_path, monkeypatch):
    # porta chiusa: invia_http reale, nessuna finta
    monkeypatch.setattr(osv, "OSV_URL", "http://127.0.0.1:9/q")
    lock = tmp_path / "l.txt"; lock.write_text(LOCK)
    assert osv.main(["x", str(lock)]) == 2


def test_http_500_esce_con_errore(tmp_path, monkeypatch):
    s = _server(b"", status=500)
    monkeypatch.setattr(osv, "OSV_URL", f"http://127.0.0.1:{s.server_port}/q")
    lock = tmp_path / "l.txt"; lock.write_text(LOCK)
    assert osv.main(["x", str(lock)]) == 2


def test_risposta_troncata_esce_con_errore_controllato(tmp_path, monkeypatch):
    # Sul codice del branch FALLISCE: http.client.IncompleteRead non e' OSError/ValueError,
    # quindi esce con traceback (exit 1, lo stesso codice di "vulnerabilita' trovate").
    s = _server(b'{"res', length=500)
    monkeypatch.setattr(osv, "OSV_URL", f"http://127.0.0.1:{s.server_port}/q")
    lock = tmp_path / "l.txt"; lock.write_text(LOCK)
    assert osv.main(["x", str(lock)]) == 2
