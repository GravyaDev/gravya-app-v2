"""Criterio 6: overhead p95 per segmento non superiore a e1.overhead_p95_ms.

Campione di test (numero di esecuzioni, DA-CV-04 (b)): 50 segmenti, parametro
del test, non del catalogo. La soglia `e1.overhead_p95_ms` viene letta dal
registro delle variabili (nessun valore fisso nel codice, DX-22).

Giro 3: con la scrittura asincrona (coda + thread di sfondo), `start_segment`
nel chiamante fa solo validazione e accodamento, non I/O di rete: il test
misura questo costo, non piu' una scrittura sincrona su socket (rilievo del
code-reviewer sul test instabile del giro 2).
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from gravya_e1.models import SegmentStart

SAMPLE_SIZE = 50  # campione di test (DA-CV-04 (b)), non una soglia di catalogo


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round(pct * (len(ordered) - 1)))))
    return ordered[idx]


def test_overhead_p95_sotto_soglia_di_catalogo(variables, signal_sink, key_provider, make_helper):
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    threshold_ms = variables.get("e1.overhead_p95_ms").value
    tenant_id = uuid.uuid4()
    trace_id = uuid.uuid4()

    # riscaldamento
    warmup_segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=trace_id,
        tenant_id=tenant_id,
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.agent.id": "agent_warmup", "gen_ai.agent.name": "agent_warmup"},
    )
    helper.start_segment(None, warmup_segment)

    durations_ms: list[float] = []
    for _ in range(SAMPLE_SIZE):
        segment = SegmentStart(
            segment_id=uuid.uuid4(),
            trace_id=trace_id,
            tenant_id=tenant_id,
            kind="agent",
            started_at=datetime.now(timezone.utc),
            attributes={"gen_ai.agent.id": "agent_bench", "gen_ai.agent.name": "agent_bench"},
        )
        start = time.perf_counter()
        helper.start_segment(None, segment)
        durations_ms.append((time.perf_counter() - start) * 1000)

    helper.flush(timeout=5)
    p95 = _percentile(durations_ms, 0.95)
    assert p95 <= threshold_ms, f"overhead p95={p95:.2f}ms oltre la soglia {threshold_ms}ms"
