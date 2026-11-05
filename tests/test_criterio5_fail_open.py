"""Criterio 5: fail-open solo per le tracce.

Scrittura delle tracce non riuscita (DB non disponibile): l'esecuzione
prosegue (non si solleva eccezione), la perdita e' contata e segnalata ad
A5. Il buffer di E1 non serve per l'audit dei tool o il record di decisione
di A3 (DA-B2-04, DA-A3-07): non sono implementati in questo perimetro, quindi
non sono simulati qui (vedi report, non_verificato).

Giro 3: con la connessione propria dell'helper (mai quella del chiamante,
G7/G14a), una connessione del chiamante gia' chiusa non causa piu' alcuna
perdita (il parametro `conn` non e' piu' usato per niente): lo dimostra
`test_connessione_del_chiamante_chiusa_non_causa_perdita_con_db_sano`. Il
fail-open vero si osserva invece quando la connessione **propria**
dell'helper (quella passata a `conninfo` alla costruzione) non riesce a
raggiungere il database.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg

from _pgconn import pg_dsn
from gravya_e1.models import SegmentStart, TraceStart
from gravya_e1.signals import PostgresSignalSink

TEST_DB = "gravya_e1_test"


def test_connessione_del_chiamante_chiusa_non_causa_perdita_con_db_sano(variables, signal_sink, key_provider, make_helper):
    """G14a: la connessione del chiamante non e' piu' usata per nulla."""
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)

    broken_conn = psycopg.connect(pg_dsn(TEST_DB))
    broken_conn.close()  # connessione del chiamante gia' chiusa: non deve avere alcun effetto

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_1"},
    )
    helper.start_segment(broken_conn, segment)  # conn ignorato: nessuna eccezione, nessuna perdita
    assert helper.flush(timeout=5)
    assert helper.loss_count == 0, "connessione del chiamante chiusa ha causato una perdita (G14a non risolto)"


def test_scrittura_traccia_non_riuscita_e_fail_open(signal_sink, key_provider, make_helper, tmp_path):
    """DB realmente irraggiungibile (conninfo della connessione propria verso una porta inesistente)."""
    helper = make_helper(
        _unreachable_variables(tmp_path),
        signal_sink,
        key_provider,
        production_override=False,
        conninfo="host=127.0.0.1 port=1 connect_timeout=1 dbname=postgres user=root",
    )

    trace = TraceStart(
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        run_id=str(uuid.uuid4()),
        root_kind="agent",
        started_at=datetime.now(timezone.utc),
    )

    helper.start_trace(None, trace)  # non deve sollevare (fail-open)
    assert helper.flush(timeout=10)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()


def test_scrittura_segmento_non_riuscita_e_fail_open(signal_sink, key_provider, make_helper, tmp_path):
    helper = make_helper(
        _unreachable_variables(tmp_path),
        signal_sink,
        key_provider,
        production_override=False,
        conninfo="host=127.0.0.1 port=1 connect_timeout=1 dbname=postgres user=root",
    )

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_1", "gen_ai.agent.name": "agent_researcher"},
    )

    helper.start_segment(None, segment)  # non deve sollevare (fail-open)
    assert helper.flush(timeout=10)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()


def test_sink_dei_segnali_non_scrivibile_non_blocca_il_fail_open(key_provider, make_helper, tmp_path):
    """B2/R-08: anche se il sink dei segnali stesso non funziona, l'helper non deve sollevare."""
    broken_conn = psycopg.connect(pg_dsn(TEST_DB))
    broken_conn.close()
    helper = make_helper(
        _unreachable_variables(tmp_path),
        PostgresSignalSink(broken_conn),
        key_provider,
        production_override=False,
        conninfo="host=127.0.0.1 port=1 connect_timeout=1 dbname=postgres user=root",
    )

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_1"},
    )

    try:
        helper.start_segment(None, segment)  # non deve sollevare, nemmeno dal sink
        helper.flush(timeout=10)
        raised = False
    except Exception:  # noqa: BLE001
        raised = True
    assert raised is False
    assert helper.loss_count == 1


def _unreachable_variables(tmp_path):
    from gravya_e1.config.variables import SnapshotVariableRegistry
    from gravya_e1.signals import InMemorySignalSink
    import json

    from _e1vars import snapshot_with

    # Giro 4 (CR N13): `tmp_path` (cancellato da pytest), mai un file in /tmp.
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_connect_timeout_ms": {"value": 1000, "unit": "ms", "status": "deciso"}})))
    return SnapshotVariableRegistry(signal_sink=InMemorySignalSink(), snapshot_path=path, production_override=False)
