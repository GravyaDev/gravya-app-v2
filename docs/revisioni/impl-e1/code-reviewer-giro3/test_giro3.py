"""Prove del giro 3 del code-reviewer (head d3cb476). Ogni test asserisce il comportamento CORRETTO:
FAIL = difetto dimostrato, PASS = tentativo di rottura fallito."""
from __future__ import annotations

import glob
import os
import socket
import threading
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1 import whitelist as wl
from gravya_e1.db import writer_transaction
from gravya_e1.models import SegmentStart, TraceStart
from gravya_e1.tracing import AttributeRejectedError, TracingHelper

DB = "gravya_e1_review3"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def seg(kind="agent", attrs=None, tenant=None, trace=None):
    return SegmentStart(segment_id=uuid.uuid4(), trace_id=trace or uuid.uuid4(), tenant_id=tenant or uuid.uuid4(),
                        kind=kind, started_at=NOW(), attributes=attrs if attrs is not None else {"gen_ai.agent.id": "agent_a"})


def row(conn, sid):
    conn.rollback()
    with conn.cursor() as cur:
        cur.execute("SELECT attributes FROM gravya_trace_segments WHERE segment_id=%s", (str(sid),))
        return cur.fetchone()


class _FreezableProxy:
    def __init__(self, target=("127.0.0.1", 5432)):
        self.frozen = False
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(8)
        self.port = self.srv.getsockname()[1]
        self.target = target
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
        psycopg.connect("host=127.0.0.1 user=root dbname=postgres").close()
        return True
    except Exception:
        return False


# ---- stallo di rete dopo la connessione, sul thread di sfondo (dichiarato non verificato dall'implementer) ----
def test_N1_stallo_di_rete_sul_thread_di_sfondo_il_chiamante_non_si_blocca_e_le_perdite_sono_contate(make_helper, partitions, signal_sink):
    """atteso: PASS. Rete bloccata dopo la connessione: 150 start_segment tornano subito, le eccedenze della coda sono perdite contate."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)           # connessione stabilita
    proxy.frozen = True
    t0 = time.perf_counter()
    for _ in range(150):
        h.start_segment(None, seg())
    elapsed = time.perf_counter() - t0
    proxy.frozen = False
    assert elapsed < 1.0, elapsed
    assert h.loss_count >= 49, h.loss_count


def test_N2_worker_di_sfondo_resta_bloccato_oltre_i_timeout_configurati(make_helper, partitions):
    """atteso: FAIL. Con la rete bloccata dopo la connessione ne' statement_timeout (lato server), ne' connect_timeout, ne' i keepalive
    (la connessione e' viva a livello TCP) sbloccano il thread: dopo 12 s (timeout configurati 2 s) la scrittura accodata e' ancora ferma.
    Nessun tcp_user_timeout ne' timeout di socket lato client: tracing fermo finche' il kernel non chiude la connessione."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)
    proxy.frozen = True
    h.start_segment(None, seg())
    done = h.flush(12)
    proxy.frozen = False
    assert done, "la scrittura accodata e' ancora bloccata dopo 12 s (timeout configurati: statement 2 s, connect 2 s)"


def test_N3_close_non_deve_bloccarsi_con_worker_fermo_e_coda_piena(make_helper, partitions):
    """atteso: FAIL. close() fa self._queue.put(_SENTINEL) bloccante e senza timeout: con il worker fermo e la coda piena
    close(timeout=2) non ritorna (spegnimento appeso)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)
    proxy.frozen = True
    for _ in range(150):
        h.start_segment(None, seg())
    done = threading.Event()
    threading.Thread(target=lambda: (h.close(timeout=2), done.set()), daemon=True).start()
    finished = done.wait(8)
    proxy.frozen = False
    assert finished, "close(timeout=2) ancora in corso dopo 8 s"


# ---- G8: controllo cross-tenant ------------------------------------------------------------------------------
def test_N4_oracolo_di_esistenza_resta_con_la_firma_a_un_parametro(admin_conn, partitions, make_helper):
    """atteso: FAIL (minore). Il tenant e' nel GUC, che il writer imposta liberamente: lo stesso oracolo di G8b con un solo parametro."""
    h = make_helper()
    victim, tid = uuid.uuid4(), uuid.uuid4()
    h.start_trace(None, TraceStart(trace_id=tid, tenant_id=victim, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()))
    assert h.flush(5)
    with writer_transaction(admin_conn, str(uuid.uuid4())) as c, c.cursor() as cur:
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(tid),)); exists_elsewhere = cur.fetchone()[0]
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(uuid.uuid4()),)); random_id = cur.fetchone()[0]
    assert not (exists_elsewhere and not random_id), "distingue trace_id esistenti presso altri tenant da quelli inesistenti"


def test_N5_funzione_definer_ha_owner_non_superuser_bypassrls_e_funziona_sotto_writer(admin_conn, partitions, make_helper):
    """atteso: PASS (rottura fallita). Owner dedicato non superuser con BYPASSRLS; la funzione vede la traccia dell'altro tenant
    anche chiamata come writer sotto RLS; EXECUTE non concesso a PUBLIC; search_path con pg_temp ultimo."""
    h = make_helper()
    a, b, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h.start_trace(None, TraceStart(trace_id=tid, tenant_id=a, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()))
    assert h.flush(5)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT r.rolsuper, r.rolbypassrls, r.rolcanlogin, p.proconfig FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                    "WHERE p.proname='gravya_e1_trace_owned_by_other_tenant'")
        sup, byp, login, cfg = cur.fetchone()
        cur.execute("SELECT has_function_privilege('public','gravya_e1_trace_owned_by_other_tenant(uuid)','EXECUTE')")
        public_exec = cur.fetchone()[0]
    assert (sup, byp, login) == (False, True, False) and cfg == ["search_path=pg_catalog, public, pg_temp"] and public_exec is False
    with writer_transaction(admin_conn, str(b)) as c, c.cursor() as cur:
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(tid),))
        assert cur.fetchone()[0] is True


def test_N6_start_trace_con_trace_id_di_altro_tenant_scartata_e_non_blocca_il_legittimo(admin_conn, partitions, make_helper, signal_sink):
    """atteso: PASS (G8a). A non puo' creare una traccia sul trace_id di B; i segmenti di B restano scritti."""
    h = make_helper()
    a, b, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h.start_trace(None, TraceStart(trace_id=tid, tenant_id=b, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()))
    assert h.flush(5)
    h.start_trace(None, TraceStart(trace_id=tid, tenant_id=a, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()))
    s = seg(tenant=b, trace=tid)
    h.start_segment(None, s)
    assert h.flush(5)
    assert row(admin_conn, s.segment_id) is not None
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_traces WHERE trace_id=%s", (str(tid),))
        assert cur.fetchone()[0] == 1


# ---- G11: trigger e privilegi con run_id valido (il G11 originale ora usa un run_id non valido) ----------------
def test_N7_trigger_e_privilegi_di_colonna_con_run_id_valido(admin_conn, partitions, make_helper):
    """atteso: PASS. UPDATE su riga chiusa rifiutato, UPDATE di tenant_id negato (equivale a G11 con run_id UUID)."""
    h = make_helper()
    t, tid = uuid.uuid4(), uuid.uuid4()
    h.start_trace(None, TraceStart(trace_id=tid, tenant_id=t, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()))
    assert h.flush(5)
    with admin_conn.cursor() as cur:
        cur.execute("UPDATE gravya_traces SET ended_at=now() WHERE trace_id=%s", (str(tid),))
    admin_conn.commit()
    with pytest.raises(psycopg.errors.IntegrityConstraintViolation):
        with writer_transaction(admin_conn, str(t)) as c, c.cursor() as cur:
            cur.execute("UPDATE gravya_traces SET status='failed' WHERE trace_id=%s", (str(tid),))
    admin_conn.rollback()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with writer_transaction(admin_conn, str(t)) as c, c.cursor() as cur:
            cur.execute("UPDATE gravya_traces SET tenant_id=%s WHERE trace_id=%s", (str(uuid.uuid4()), str(tid)))
    admin_conn.rollback()


# ---- G16: contesto del tenant ----------------------------------------------------------------------------------
def test_N8_tenant_context_scarta_in_produzione_e_non_scrive(admin_conn, partitions, make_helper, signal_sink):
    """atteso: PASS."""
    ctx, other = uuid.uuid4(), uuid.uuid4()
    h = make_helper(tenant_context=str(ctx))
    s = seg(tenant=other)
    h.start_segment(None, s); assert h.flush(5)
    assert row(admin_conn, s.segment_id) is None
    assert "trace.tenant_context_mismatch" in signal_sink.kinds()


def test_N9_tenant_context_in_maiuscolo_deve_essere_accettato(admin_conn, partitions, make_helper):
    """atteso: FAIL (minore). Il confronto e' tra stringhe: lo stesso UUID in maiuscolo come contesto rifiuta ogni scrittura legittima."""
    t = uuid.uuid4()
    h = make_helper(tenant_context=str(t).upper())
    s = seg(tenant=t)
    h.start_segment(None, s); assert h.flush(5)
    assert row(admin_conn, s.segment_id) is not None


def test_N10_senza_tenant_context_l_helper_scrive_per_qualunque_tenant_con_produzione_simulata(admin_conn, partitions, make_helper):
    """atteso: FAIL (informativo, scelta del coordinator). Con production_override=True e senza tenant_context nessun controllo di contesto:
    due tenant diversi scritti dallo stesso helper. Il controllo vale solo con API_ENV=production reale."""
    h = make_helper()
    a, b = uuid.uuid4(), uuid.uuid4()
    sa, sb = seg(tenant=a), seg(tenant=b)
    h.start_segment(None, sa); h.start_segment(None, sb); assert h.flush(5)
    assert row(admin_conn, sb.segment_id) is None, "scritto per un tenant senza alcun contesto"


# ---- DX-22 -----------------------------------------------------------------------------------------------------
def test_N11_connect_timeout_non_viene_alterato_in_silenzio(monkeypatch, make_registry, signal_sink, key_provider):
    """atteso: FAIL (minore). connect_timeout = max(1, round(ms/1000)): 400 ms diventa 1 s, 2500 ms diventa 2 s (round bancario)."""
    captured = {}

    def fake_connect(*a, **kw):
        captured.update(kw)
        raise psycopg.OperationalError("x")

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    for ms, expected in ((400, 0.4), (2500, 2.5)):
        reg = make_registry({"e1.write_connect_timeout_ms": {"value": ms, "unit": "ms", "status": "deciso"}})
        h = TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo="dbname=x")
        h.start_segment(None, seg()); h.flush(3); h.close(1)
        assert captured["connect_timeout"] == expected, (ms, captured["connect_timeout"])


def test_N12_flush_non_deve_restituire_true_con_scritture_ancora_accodate(make_helper, partitions):
    """atteso: PASS se non si osserva un contatore _pending negativo (race tra put_nowait e incremento)."""
    h = make_helper(conninfo="host=127.0.0.1 port=1 connect_timeout=1 dbname=x user=root")
    seen_min = [0]
    stop = threading.Event()

    def mon():
        while not stop.is_set():
            seen_min[0] = min(seen_min[0], h._pending)

    t = threading.Thread(target=mon, daemon=True); t.start()
    for _ in range(60):
        h.start_segment(None, seg())
    h.flush(30); stop.set(); t.join(1)
    assert seen_min[0] >= 0, f"_pending sceso a {seen_min[0]}"


# ---- mkstemp ---------------------------------------------------------------------------------------------------
def test_N13_i_test_del_branch_non_lasciano_file_temporanei_in_tmp():
    """atteso: FAIL. tests/test_criterio5_fail_open.py e tests/test_giro3_misc.py usano tempfile.mkstemp(...)[1]
    (fd aperto, file mai cancellato): ogni corsa lascia /tmp/tmp*.json."""
    import subprocess, sys
    before = set(glob.glob("/tmp/tmp*.json"))
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "--basetemp=/workspace/wt-impl-e1/docs/revisioni/impl-e1/code-reviewer-giro3/basetemp_sub",
                    "/workspace/wt-impl-e1/tests/test_criterio5_fail_open.py", "/workspace/wt-impl-e1/tests/test_giro3_misc.py"],
                   cwd="/workspace/wt-impl-e1", capture_output=True)
    left = set(glob.glob("/tmp/tmp*.json")) - before
    for f in left:
        os.unlink(f)
    assert not left, f"{len(left)} file lasciati in /tmp"
