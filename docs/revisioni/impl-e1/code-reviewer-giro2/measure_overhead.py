"""Misura la distribuzione del p95 del test del criterio 6 (stessa logica), N ripetizioni, anche sotto carico CPU.
Uso: python measure_overhead.py [n_ripetizioni] ; usa il DB di test del branch (solo scritture sintetiche)."""
import sys, time, uuid, os
sys.path.insert(0, "/workspace/wt-impl-e1/tests")
from datetime import datetime, timezone
import psycopg
from _pgconn import pg_dsn
from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.keys import StaticTestKeyProvider
from gravya_e1.models import SegmentStart
from gravya_e1.signals import InMemorySignalSink
from gravya_e1.tracing import TracingHelper
from gravya_e1.partitions import ensure_partition

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
sink = InMemorySignalSink()
v = SnapshotVariableRegistry(signal_sink=sink, production_override=False)
thr = v.get("e1.overhead_p95_ms").value
conn = psycopg.connect(pg_dsn("gravya_e1_test"))
ensure_partition(conn, "gravya_trace_segments", datetime.now(timezone.utc), v)
res = []
for r in range(N):
    h = TracingHelper(v, sink, StaticTestKeyProvider(), production_override=False)
    t = uuid.uuid4(); tr = uuid.uuid4()
    def mk(): return SegmentStart(segment_id=uuid.uuid4(), trace_id=tr, tenant_id=t, kind="agent", started_at=datetime.now(timezone.utc), attributes={"gen_ai.agent.id": "agent_a", "gen_ai.agent.name": "agent_bench"})
    h.start_segment(conn, mk())
    d = []
    for _ in range(50):
        s = mk(); a = time.perf_counter(); h.start_segment(conn, s); d.append((time.perf_counter() - a) * 1000)
    d.sort(); res.append(d[int(round(0.95 * 49))])
print("soglia", thr, "p95 min/med/max", min(res), sorted(res)[len(res)//2], max(res), "superamenti", sum(x > thr for x in res), "su", N)
