"""Prove del giro 5 del code-reviewer (head 41607af). Ogni test asserisce il comportamento CORRETTO:
FAIL = difetto dimostrato, PASS = tentativo di rottura fallito. Nessun file in /tmp."""
from __future__ import annotations

import socket
import threading
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.config.variables import VariableUnavailableError
from gravya_e1.models import SegmentEnd, SegmentStart
from gravya_e1.tracing import EnvironmentInvalidError, TracingHelper

DB = "gravya_e1_review5"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def seg(tenant=None):
    return SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=tenant or uuid.uuid4(),
                        kind="agent", started_at=NOW(), attributes={"gen_ai.agent.id": "agent_a"})


class _FreezableProxy:
    def __init__(self, target=("127.0.0.1", 5432)):
        self.frozen = False
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(8)
        self.port = self.srv.getsockname()[1]; self.target = target
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            u = socket.create_connection(self.target)
            for a, b in ((c, u), (u, c)):
                threading.Thread(target=self._pipe, args=(a, b), daemon=True).start()

    def _pipe(self, a, b):
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                while self.frozen:
                    time.sleep(0.05)
                b.sendall(d)
        except OSError:
            pass


def _tcp_ok():
    try:
        psycopg.connect("host=127.0.0.1 user=root dbname=postgres").close(); return True
    except Exception:
        return False


def _signals(admin, tenant):
    admin.rollback()
    with admin.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_signals_min_audit WHERE tenant_id=%s", (str(tenant),))
        return cur.fetchone()[0]


def _backends(admin):
    admin.rollback()
    with admin.cursor() as cur:
        cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid()", (DB,))
        return cur.fetchone()[0]


# ---- V1 con il conftest corretto (sink al posto di signal_sink) -------------------------------------------------
@pytest.mark.parametrize("bad", [0, "abc"])
def test_V1_tcp_user_timeout_valore_non_valido_blocca_con_errore_tipizzato_e_segnale(make_registry, signal_sink, key_provider, bad):
    """atteso: PASS (il rilievo V1 e' risolto; il test V1 originale era ineseguibile per il refuso del mio conftest)."""
    reg = make_registry({"e1.write_tcp_user_timeout_ms": {"value": bad, "unit": "ms", "status": "deciso"}})
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={DB}")
    assert any(s.kind == "e5.variable_invalid" for s in signal_sink.signals)


def test_V1b_regola_relazionale_tcp_user_timeout_non_minore_dello_statement_timeout(make_registry, signal_sink, key_provider):
    """atteso: PASS."""
    reg = make_registry({"e1.write_tcp_user_timeout_ms": {"value": 1000, "unit": "ms", "status": "deciso"}})
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={DB}")


def test_V3_connect_timeout_minimo_2_e_nel_codice_non_solo_nei_dati(make_registry, signal_sink, key_provider):
    """atteso: FAIL (minore). La decisione dice 'minimo tecnico 2': il codice impone solo 1 (_EXPECTED_INT_VARIABLES); il 2 sta
    nel campo `min` dell'istantanea. Un'istantanea senza `min` accetta 1 (libpq lo alza a 2 in silenzio)."""
    reg = make_registry({"e1.write_connect_timeout_s": {"value": 1, "unit": "s", "status": "deciso"}})
    with pytest.raises(VariableUnavailableError):
        h = TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={DB}")
        h.close(1)


# ---- S1 riformulato: segnali con connessione propria dopo un blocco di rete ----------------------------------------
def test_S1b_segnali_riprendono_dopo_un_blocco_di_rete_sulla_connessione_propria(make_helper, partitions, admin_conn):
    """atteso: PASS. Il sink PostgreSQL passato e' solo un marcatore; l'helper scrive i segnali con la propria connessione
    (qui attraverso il proxy). Dopo il blocco e lo sblocco i segnali successivi arrivano."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    from gravya_e1.signals import PostgresSignalSink
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h._signals = PostgresSignalSink(psycopg.connect(f"dbname={DB}"))
    t = uuid.uuid4()
    bad = lambda: h.end_segment(None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=t, ended_at=NOW(), status="ok"), "kind_bogus")
    bad(); assert h.flush(10); assert _signals(admin_conn, t) >= 1
    proxy.frozen = True
    bad(); h.flush(12)
    proxy.frozen = False
    before = _signals(admin_conn, t)
    bad(); assert h.flush(15)
    assert _signals(admin_conn, t) > before


def test_S2b_sink_da_solo_resta_utilizzabile_dopo_un_errore(admin_conn):
    """atteso: PASS."""
    from gravya_e1.signals import PostgresSignalSink
    c = psycopg.connect(f"dbname={DB}")
    sink = PostgresSignalSink(c)
    with pytest.raises(Exception):
        sink.emit("trace.write_failed", tenant_id="non-un-uuid", count=1)
    t = uuid.uuid4()
    sink.emit("trace.write_failed", tenant_id=str(t), count=1)
    assert _signals(admin_conn, t) == 1
    c.close()


def test_S3b_kind_arbitrario_diventa_segnaposto(make_helper, partitions, signal_sink):
    """atteso: PASS."""
    h = make_helper()
    s = "Il cliente Mario Rossi chiede il rimborso SENTINELLA-GIRO5"
    h.end_segment(None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"), s)
    assert h.flush(5)
    assert all(s not in str(x.payload) for x in signal_sink.signals)


# ---- close(): scritture dopo la chiusura, connessione orfana ---------------------------------------------------------
def test_X1_dopo_close_nessuna_connessione_orfana_e_nessuna_scrittura(make_helper, partitions, admin_conn):
    """atteso: FAIL. Una connessione iniziata prima di close() e completata dopo (rete che si sblocca entro connect_timeout) viene
    assegnata a self._own_conn senza ricontrollare _closed e _invalidate_connection ha gia' rinunciato al lock: il job viene
    eseguito dopo close() e la connessione resta aperta (backend orfano)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    base = _backends(admin_conn)
    proxy = _FreezableProxy()
    proxy.frozen = True                                   # nessuna connessione ancora: il worker si bloccherà in connect()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    s = seg()
    h.start_segment(None, s)
    time.sleep(0.5)                                       # il worker e' dentro psycopg.connect() (con _conn_lock)
    h.close(timeout=0.5)
    proxy.frozen = False                                  # la connessione si completa DOPO close()
    time.sleep(3)
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id=%s", (str(s.segment_id),))
        written = cur.fetchone() is not None
    orphan = _backends(admin_conn) - base
    assert not written and orphan <= 0, f"scritto dopo close: {written}; backend orfani: {orphan}"


def test_X2_close_ritorna_entro_il_timeout_con_worker_fermo(make_helper, partitions):
    """atteso: PASS (W2a)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)
    proxy.frozen = True
    for _ in range(150):
        h.start_segment(None, seg())
    t0 = time.perf_counter(); h.close(timeout=2); dt = time.perf_counter() - t0
    proxy.frozen = False
    assert dt < 2.5, dt


# ---- API_ENV ---------------------------------------------------------------------------------------------------------
def test_E1_api_env_fuori_insieme_blocca_l_avvio(monkeypatch, registry, signal_sink, key_provider):
    """atteso: PASS (decisione dell'utente)."""
    monkeypatch.setenv("API_ENV", "Production")
    with pytest.raises(EnvironmentInvalidError):
        TracingHelper(registry, signal_sink, key_provider, tenant_context=str(uuid.uuid4()), conninfo=f"dbname={DB}")
    assert "e5.environment_invalid" in signal_sink.kinds()


def test_E2_api_env_fuori_insieme_blocca_anche_con_production_override(monkeypatch, registry, signal_sink, key_provider):
    """atteso: FAIL (minore). Il controllo e' dentro `if production_override is None`: chi passa production_override (anche True)
    avvia l'helper con API_ENV='Production' senza blocco ne' segnale."""
    monkeypatch.setenv("API_ENV", "Production")
    with pytest.raises(EnvironmentInvalidError):
        h = TracingHelper(registry, signal_sink, key_provider, production_override=True, tenant_context=str(uuid.uuid4()),
                          conninfo=f"dbname={DB}")
        h.close(1)


# ---- DX-22 -----------------------------------------------------------------------------------------------------------
def test_D1_nessuna_durata_fissa_nei_due_worker():
    """atteso: FAIL (minore). I due worker usano get(timeout=0.2) e close() ha timeout=5.0 di default: durate fisse nel codice."""
    import inspect, gravya_e1.tracing as t
    src = inspect.getsource(t)
    assert "timeout=0.2" not in src and "timeout: float = 5.0" not in src
