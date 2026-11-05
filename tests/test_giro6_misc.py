"""Prove del giro 6 (definitivo): ultime correzioni dopo la verifica mirata
finale del code-reviewer. Vedi report, sezione "Giro 6", per il collegamento
rilievo -> modifica -> test.
"""
from __future__ import annotations

import inspect
import json
import socket
import threading
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

import gravya_e1.tracing as tracing_module
from _e1vars import snapshot_with
from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
from gravya_e1.models import SegmentStart
from gravya_e1.signals import InMemorySignalSink
from gravya_e1.tracing import TracingHelper

TEST_DB = "gravya_e1_test"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def seg(tenant=None):
    return SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=tenant or uuid.uuid4(),
                        kind="agent", started_at=NOW(), attributes={"gen_ai.agent.id": "agent_a"})


# --- V3: minimo tecnico 2 di e1.write_connect_timeout_s imposto dal codice -
# (code-reviewer-giro5/test_giro5.py::test_V3 verifica esattamente questo
# scenario, nessuna "min" nell'istantanea: qui lo stesso, come conferma
# propria, non in sostituzione.)


def test_connect_timeout_sotto_2_senza_min_dichiarato_blocca_comunque(tmp_path):
    """Senza il campo 'min' nell'istantanea, il minimo tecnico 2 deve
    comunque valere (imposto dal codice, non solo dal dato)."""
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_connect_timeout_s": {"value": 1, "unit": "s", "status": "deciso"}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    with pytest.raises(VariableUnavailableError):
        reg.get("e1.write_connect_timeout_s")
    assert "e5.variable_invalid" in signal_sink.kinds()


def test_connect_timeout_esattamente_2_senza_min_dichiarato_e_valido(tmp_path):
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_connect_timeout_s": {"value": 2, "unit": "s", "status": "deciso"}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    value = reg.get("e1.write_connect_timeout_s")
    assert value.value == 2
    assert "e5.variable_invalid" not in signal_sink.kinds()


# --- D1: close() e' un parametro obbligatorio, nessuna durata fissa nel codice ---


def test_close_richiede_il_timeout_esplicito():
    with pytest.raises(TypeError):
        TracingHelper.close(None)  # chiamata senza l'argomento obbligatorio solleverebbe TypeError


def test_nessuna_durata_fissa_nel_sorgente_di_tracing():
    src = inspect.getsource(tracing_module)
    assert "timeout=0.2" not in src
    assert "timeout: float = 5.0" not in src


# --- X1: nessuna connessione orfana e nessuna scrittura dopo close() -------
# (code-reviewer-giro5/test_giro5.py::test_X1 verifica esattamente questo
# scenario: qui una conferma propria, stesso meccanismo.)


class _FreezableProxy:
    def __init__(self, target=("127.0.0.1", 5432)):
        self.frozen = False
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(8)
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
    import os

    host = os.environ.get("PGHOST") or "127.0.0.1"
    port = os.environ.get("PGPORT") or "5432"
    user = os.environ.get("PGUSER") or "root"
    try:
        psycopg.connect(f"host={host} port={port} user={user} dbname=postgres").close()
        return True
    except Exception:  # noqa: BLE001
        return False


def _backends(admin_conn):
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid()", (TEST_DB,))
        return cur.fetchone()[0]


def test_X1_connessione_completata_dopo_close_non_scrive_e_non_resta_orfana(variables, signal_sink, key_provider, admin_conn, ensure_partitions_now):
    if not _tcp_ok():
        pytest.skip("TCP non disponibile: impostare PGHOST/PGPORT/PGUSER per un ruolo raggiungibile via TCP")
    base = _backends(admin_conn)
    proxy = _FreezableProxy()
    proxy.frozen = True  # nessuna connessione ancora: il worker si bloccherà dentro connect()
    helper = TracingHelper(
        variables, signal_sink, key_provider, production_override=True,
        conninfo=f"host=127.0.0.1 port={proxy.port} dbname={TEST_DB}",
    )
    s = seg()
    helper.start_segment(None, s)
    time.sleep(0.5)  # il worker e' dentro psycopg.connect()
    helper.close(0.5)
    proxy.frozen = False  # la connessione si completa DOPO close()
    time.sleep(3)
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id=%s", (str(s.segment_id),))
        written = cur.fetchone() is not None
    orphan = _backends(admin_conn) - base
    assert not written, "il job e' stato scritto dopo close()"
    assert orphan <= 0, f"connessione orfana dopo close(): {orphan} backend in piu'"
