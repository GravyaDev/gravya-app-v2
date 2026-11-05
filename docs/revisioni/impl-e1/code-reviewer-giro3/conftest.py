"""Fixture delle prove del giro 3 (code-reviewer, head d3cb476). DB scratch `gravya_e1_review3` creato con
`alembic upgrade head` (migrazioni del branch), eliminato a fine sessione. Non tocca `gravya_e1_test`.
Esecuzione: cd /workspace/wt-impl-e1 && . .venv/bin/activate &&
  pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro3/basetemp docs/revisioni/impl-e1/code-reviewer-giro3/test_giro3.py"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.keys import StaticTestKeyProvider
from gravya_e1.partitions import ensure_partition
from gravya_e1.signals import InMemorySignalSink

DB = "gravya_e1_review3"
REPO = "/workspace/wt-impl-e1"
HERE = pathlib.Path(__file__).parent
DSN = f"dbname={DB}"


@pytest.fixture(scope="session", autouse=True)
def scratch_db():
    adm = psycopg.connect("dbname=postgres", autocommit=True)
    adm.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid()", (DB,))
    adm.execute(f"DROP DATABASE IF EXISTS {DB}")
    adm.execute(f"CREATE DATABASE {DB} OWNER root")
    env = dict(os.environ, DATABASE_URL=f"postgresql+psycopg://root@/{DB}")
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=REPO, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    yield
    adm.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid <> pg_backend_pid()", (DB,))
    adm.execute(f"DROP DATABASE IF EXISTS {DB}")
    adm.close()


@pytest.fixture()
def admin_conn():
    c = psycopg.connect(DSN)
    yield c
    c.rollback()
    c.close()


@pytest.fixture()
def signal_sink():
    return InMemorySignalSink()


def _registry(sink, extra=None):
    d = HERE / "snap_tmp"
    d.mkdir(exist_ok=True)
    p = d / "snap.json"
    v = {
        "e1.write_buffer_size": {"value": 100, "unit": "count", "status": "deciso"},
        "e1.attributes.max_value_bytes": {"value": 2048, "unit": "bytes", "status": "deciso"},
        "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_connect_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_tcp_keepalives_idle_s": {"value": 10, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_interval_s": {"value": 5, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_count": {"value": 3, "unit": "count", "status": "deciso"},
        "e1.write_tcp_user_timeout_ms": {"value": 5000, "unit": "ms", "status": "deciso"},
        "e1.partition_interval_months": {"value": 1, "unit": "months", "status": "deciso"},
    }
    v.update(extra or {})
    p.write_text(json.dumps({"variables": v}))
    return SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=p, production_override=True)


@pytest.fixture()
def registry(signal_sink):
    return _registry(signal_sink)


@pytest.fixture()
def make_registry(signal_sink):
    return lambda extra=None: _registry(signal_sink, extra)


@pytest.fixture()
def key_provider():
    return StaticTestKeyProvider()


@pytest.fixture()
def make_helper(signal_sink, key_provider, registry):
    """Crea TracingHelper con conninfo esplicito e li chiude a fine test."""
    from gravya_e1.tracing import TracingHelper
    created = []

    def _make(conninfo=DSN, reg=None, **kw):
        kw.setdefault("production_override", True)
        h = TracingHelper(reg or registry, signal_sink, key_provider, conninfo=conninfo, **kw)
        created.append(h)
        return h

    yield _make
    for h in created:
        try:
            h.close(timeout=1)
        except Exception:
            pass


@pytest.fixture()
def partitions(admin_conn, registry):
    ts = datetime.now(timezone.utc)
    ensure_partition(admin_conn, "gravya_traces", ts, registry)
    ensure_partition(admin_conn, "gravya_trace_segments", ts, registry)
