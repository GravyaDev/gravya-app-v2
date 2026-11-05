"""Criterio 5: fail-open solo per le tracce.

Scrittura delle tracce non riuscita (DB non disponibile): l'esecuzione
prosegue (non si solleva eccezione), la perdita e' contata e segnalata ad
A5. Il buffer di E1 non serve per l'audit dei tool o il record di decisione
di A3 (DA-B2-04, DA-A3-07): non sono implementati in questo perimetro, quindi
non sono simulati qui (vedi report, non_verificato).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg

from gravya_e1.models import SegmentStart, TraceStart
from gravya_e1.tracing import TracingHelper


def test_scrittura_traccia_non_riuscita_e_fail_open(variables, signal_sink, key_provider):
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    broken_conn = psycopg.connect("dbname=gravya_e1_test")
    broken_conn.close()  # connessione gia' chiusa: ogni operazione fallisce

    trace = TraceStart(
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        run_id="run-fail-open",
        root_kind="agent",
        started_at=datetime.now(timezone.utc),
    )

    helper.start_trace(broken_conn, trace)  # non deve sollevare (fail-open)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()


def test_scrittura_segmento_non_riuscita_e_fail_open(variables, signal_sink, key_provider):
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    broken_conn = psycopg.connect("dbname=gravya_e1_test")
    broken_conn.close()

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent-1", "gen_ai.agent.name": "ricercatore"},
    )

    helper.start_segment(broken_conn, segment)  # non deve sollevare (fail-open)

    assert helper.loss_count == 1
    assert "trace.write_failed" in signal_sink.kinds()
