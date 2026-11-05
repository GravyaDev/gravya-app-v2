"""Criterio 5: fail-open solo per le tracce.

Scrittura delle tracce non riuscita (DB non disponibile): l'esecuzione
prosegue (non si solleva eccezione), la perdita e' contata e segnalata ad
A5. Il buffer di E1 non serve per l'audit dei tool o il record di decisione
di A3 (DA-B2-04, DA-A3-07): non sono implementati in questo perimetro, quindi
non sono simulati qui (vedi report, non_verificato).

Giro 2: oltre al sink in memoria, un test con `PostgresSignalSink` (sulla
stessa connessione gia' chiusa) dimostra che il fail-open non dipende dalla
disponibilita' del sink dei segnali (B2/R-08: l'eccezione del sink non deve
uscire dall'helper).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from _pgconn import pg_dsn
from gravya_e1.models import SegmentStart, TraceStart
from gravya_e1.signals import PostgresSignalSink
from gravya_e1.tracing import TracingHelper


def test_scrittura_traccia_non_riuscita_e_fail_open(variables, signal_sink, key_provider):
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    broken_conn = psycopg.connect(pg_dsn("gravya_e1_test"))
    broken_conn.close()  # connessione gia' chiusa: ogni operazione fallisce

    trace = TraceStart(
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        run_id="run_fail_open",
        root_kind="agent",
        started_at=datetime.now(timezone.utc),
    )

    helper.start_trace(broken_conn, trace)  # non deve sollevare (fail-open)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()


def test_scrittura_segmento_non_riuscita_e_fail_open(variables, signal_sink, key_provider):
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    broken_conn = psycopg.connect(pg_dsn("gravya_e1_test"))
    broken_conn.close()

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_1", "gen_ai.agent.name": "agent_researcher"},
    )

    helper.start_segment(broken_conn, segment)  # non deve sollevare (fail-open)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()


def test_sink_dei_segnali_non_scrivibile_non_blocca_il_fail_open(variables, key_provider):
    """B2/R-08: anche se il sink dei segnali stesso non funziona, l'helper non deve sollevare."""
    broken_conn = psycopg.connect(pg_dsn("gravya_e1_test"))
    broken_conn.close()
    helper = TracingHelper(variables, PostgresSignalSink(broken_conn), key_provider, production_override=False)

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_1"},
    )

    try:
        helper.start_segment(broken_conn, segment)  # non deve sollevare, nemmeno dal sink
        raised = False
    except Exception:  # noqa: BLE001
        raised = True
    assert raised is False
    assert helper.loss_count == 1
