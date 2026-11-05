"""Prove del giro 4 del code-reviewer (head 8dfb1de). Ogni test asserisce il comportamento CORRETTO:
FAIL = difetto dimostrato, PASS = tentativo di rottura fallito. Nessun file in /tmp."""
from __future__ import annotations

import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.models import SegmentEnd, SegmentStart
from gravya_e1.signals import PostgresSignalSink
from gravya_e1.tracing import TracingHelper

DB = "gravya_e1_review4"
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


def _signals_count(admin, tenant):
    admin.rollback()
    with admin.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_signals_min_audit WHERE tenant_id=%s", (str(tenant),))
        return cur.fetchone()[0]


# ---- guardiano per job, close() ---------------------------------------------------------------------
def test_W1_guardiano_sblocca_la_scrittura_e_il_worker_riprende(make_helper, partitions, admin_conn):
    """atteso: PASS. Rete bloccata dopo la connessione: entro ~tcp_user_timeout il job e' interrotto (perdita contata),
    poi, sbloccata la rete, le scritture successive riescono (riconnessione)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)
    proxy.frozen = True
    h.start_segment(None, seg())
    t0 = time.perf_counter(); ok = h.flush(10); dt = time.perf_counter() - t0
    proxy.frozen = False
    assert ok and dt < 6, dt
    assert h.loss_count >= 1
    s = seg(); h.start_segment(None, s); assert h.flush(10)
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id=%s", (str(s.segment_id),))
        assert cur.fetchone() is not None


def _stalled_helper(make_helper):
    proxy = _FreezableProxy()
    h = make_helper(conninfo=f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h.start_segment(None, seg()); assert h.flush(5)
    proxy.frozen = True
    for _ in range(150):
        h.start_segment(None, seg())
    return proxy, h


def test_W2a_close_ritorna_entro_il_timeout(make_helper, partitions):
    """atteso: FAIL. close(timeout=2) con worker fermo e coda piena impiega ~4 s: _invalidate_connection() prende _conn_lock,
    tenuto dal worker durante psycopg.connect() (riconnessione verso la rete bloccata, fino a connect_timeout)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy, h = _stalled_helper(make_helper)
    t0 = time.perf_counter(); h.close(timeout=2); dt = time.perf_counter() - t0
    proxy.frozen = False
    assert dt < 2.5, f"close(timeout=2) ha impiegato {dt:.1f}s"


def test_W2b_dopo_close_il_worker_non_deve_restare_attivo(make_helper, partitions):
    """atteso: FAIL. Il worker non controlla _closed: dopo close() continua a svuotare la coda e a riconnettersi."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy, h = _stalled_helper(make_helper)
    h.close(timeout=2)
    time.sleep(5)
    alive = h._worker_thread.is_alive() or h._signal_worker_thread.is_alive()
    proxy.frozen = False
    assert not alive, "worker ancora vivo 5 s dopo close()"


# ---- sink dei segnali -----------------------------------------------------------------------------------
def test_S1_sink_non_si_riprende_dopo_un_blocco_di_rete(make_helper, partitions, admin_conn):
    """atteso: FAIL. Il guardiano chiude il socket della connessione del sink (data dal chiamante); il sink non si riconnette:
    dopo lo sblocco della rete tutti i segnali successivi sono persi (solo log di ripiego)."""
    if not _tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = _FreezableProxy()
    sink_conn = psycopg.connect(f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    from gravya_e1.tracing import TracingHelper as TH
    h = make_helper(conninfo=f"dbname={DB}")
    h._signals = PostgresSignalSink(sink_conn)
    t = uuid.uuid4()
    bad = lambda: h.end_segment(None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=t, ended_at=NOW(), status="ok"), "kind_bogus")
    bad(); assert h.flush(10); assert _signals_count(admin_conn, t) >= 1          # il sink funziona
    proxy.frozen = True
    bad(); h.flush(12)                                                              # blocco: il guardiano uccide la connessione
    proxy.frozen = False
    before = _signals_count(admin_conn, t)
    bad(); assert h.flush(10)
    assert _signals_count(admin_conn, t) == before + 1, "segnale non scritto dopo lo sblocco: il sink non si riconnette"


def test_S2_sink_resta_in_transazione_fallita_dopo_un_errore(admin_conn):
    """atteso: FAIL. Un solo errore (tenant_id non UUID) lascia la connessione in transazione fallita: ogni segnale successivo fallisce."""
    c = psycopg.connect(f"dbname={DB}")
    sink = PostgresSignalSink(c)
    with pytest.raises(Exception):
        sink.emit("trace.write_failed", tenant_id="non-un-uuid", count=1)
    t = uuid.uuid4()
    sink.emit("trace.write_failed", tenant_id=str(t), count=1)         # deve riuscire
    assert _signals_count(admin_conn, t) == 1
    c.close()


def test_S3_kind_arbitrario_di_end_segment_finisce_nel_segnale(make_helper, partitions, signal_sink):
    """atteso: FAIL. Il campo 'kind' del segnale e' il parametro `kind` di end_segment, non validato: testo arbitrario del chiamante
    passa nel payload del segnale (campo ammesso, senza limite ne' formato)."""
    h = make_helper()
    sentinel = "Il cliente Mario Rossi chiede il rimborso SENTINELLA-GIRO4"
    h.end_segment(None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"), sentinel)
    assert h.flush(5)
    assert all(sentinel not in str(s.payload) for s in signal_sink.signals), [s.payload for s in signal_sink.signals]


# ---- variabili -------------------------------------------------------------------------------------------
def test_V1_variabile_nuova_non_e_nell_elenco_dei_tipi_attesi(make_registry, signal_sink, key_provider):
    """atteso: FAIL. e1.write_tcp_user_timeout_ms non e' in _EXPECTED_INT_VARIABLES: un'istantanea senza `min` accetta 0
    (Timer(0): il guardiano interrompe ogni job subito) e una stringa solleva TypeError non tipizzato (senza segnale)."""
    from gravya_e1.config.variables import VariableUnavailableError
    for bad in (0, "abc"):
        reg = make_registry({"e1.write_tcp_user_timeout_ms": {"value": bad, "unit": "ms", "status": "deciso"}})
        try:
            h = TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={DB}")
            h.close(1)
            raise AssertionError(f"avvio consentito con valore non valido {bad!r}")
        except VariableUnavailableError:
            pass


def test_V2_connect_timeout_sotto_il_secondo_disattiva_il_timeout():
    """atteso: FAIL. L'helper passa ms/1000 esatto (0.4): libpq lo legge come intero (0 = attesa infinita); 2.5 diventa 2 s;
    1.0 diventa 2 s. Il fix N11 sostituisce l'arrotondamento con un valore che libpq tronca o ignora."""
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(5)
    keep = []
    threading.Thread(target=lambda: [keep.append(srv.accept()) for _ in range(5)], daemon=True).start()
    res = {}

    def run():
        try:
            psycopg.connect(host="127.0.0.1", port=srv.getsockname()[1], user="root", dbname="x", connect_timeout=400 / 1000)
        except Exception as e:
            res["e"] = type(e).__name__
    th = threading.Thread(target=run, daemon=True); th.start(); th.join(6)
    assert not th.is_alive(), "connect_timeout=0.4 (400 ms): connessione ancora in attesa dopo 6 s (nessun timeout)"


# ---- migrazioni ------------------------------------------------------------------------------------------
def test_M1_migration_role_con_iniezione_rifiutato():
    """atteso: PASS. MIGRATION_ROLE non e' un identificatore: la migrazione si rifiuta di partire."""
    import os
    env = dict(os.environ, DATABASE_URL=f"postgresql+psycopg://root@/{DB}", MIGRATION_ROLE='x"; DROP TABLE gravya_traces; --')
    r = subprocess.run([sys.executable, "-m", "alembic", "current"], cwd="/workspace/wt-impl-e1", env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "MIGRATION_ROLE" in r.stderr


def test_M2_alembic_con_ruolo_non_superuser_non_puo_creare_bypassrls(admin_conn):
    """atteso: PASS (dimostra il limite). Un ruolo non superuser con CREATEROLE (gravya_migrator) non puo' creare un ruolo BYPASSRLS:
    il README, che parla di un ruolo con solo CREATEDB per `alembic upgrade head`, e' inesatto."""
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with admin_conn.transaction():
            admin_conn.execute("SET LOCAL ROLE gravya_migrator")
            admin_conn.execute("CREATE ROLE gravya_zz_prova_bypass NOLOGIN BYPASSRLS")
    admin_conn.rollback()


def test_R1_readme_tests_dipendono_dal_ruolo_root_per_i_test_con_proxy():
    """atteso: FAIL. Il README dice che tests/ non dipende dal ruolo 'root': tcp_ok() e il test del sink bloccato usano user=root
    fisso; senza quel ruolo i test con proxy si saltano (skip) in silenzio."""
    import pathlib, re
    hits = [str(p) for p in pathlib.Path("/workspace/wt-impl-e1/tests").glob("*.py")
            if re.search(r"user=root", p.read_text()) and p.name != "_pgconn.py"]
    assert not hits, hits
