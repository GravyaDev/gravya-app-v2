"""Prova del code-reviewer (giro 2): i test del branch non proteggono il controllo
dello stato HTTP (solo 2xx diversi da 200 con corpo valido) ne' il timeout.
Uso: OSV_SCRIPT=<percorso osv-check.py> python -I -m pytest -q -p no:cacheprovider <questo file>
"""
import http.server, importlib.util, os, threading
import pytest

spec = importlib.util.spec_from_file_location("osv_check", os.environ["OSV_SCRIPT"])
osv = importlib.util.module_from_spec(spec); spec.loader.exec_module(osv)
LOCK = "requests==2.0.0 \\\n    --hash=sha256:aa\n"
PULITO = b'{"results": [{}]}'


def server(stato, corpo, attesa=0):
    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if attesa:
                threading.Event().wait(attesa)
            self.send_response(stato)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        def log_message(self, *a): pass
    s = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def run(tmp_path, monkeypatch, s):
    monkeypatch.setattr(osv, "OSV_URL", f"http://127.0.0.1:{s.server_port}/q")
    lock = tmp_path / "l.txt"; lock.write_text(LOCK)
    try:
        return osv.main(["x", str(lock)])
    finally:
        s.shutdown(); s.server_close()


@pytest.mark.parametrize("stato", [201, 203, 206])
def test_stato_2xx_diverso_da_200_con_corpo_valido_e_errore(stato, tmp_path, monkeypatch):
    assert run(tmp_path, monkeypatch, server(stato, PULITO)) == 2


def test_timeout_scatta_anche_con_risposta_tardiva_valida(tmp_path, monkeypatch):
    monkeypatch.setattr(osv, "TIMEOUT_SECONDI", 0.2)
    assert run(tmp_path, monkeypatch, server(200, PULITO, attesa=2)) == 2
