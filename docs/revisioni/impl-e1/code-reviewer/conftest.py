"""Fixture per gli script di riproduzione del code-reviewer (E1 impl).

Usa un database scratch `gravya_e1_review` creato con `alembic upgrade head`
(stesse migrazioni del branch); non tocca il database dei test del branch.
Esecuzione: cd /workspace/wt-impl-e1 && . .venv/bin/activate &&
  pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer/basetemp docs/revisioni/impl-e1/code-reviewer/
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.keys import StaticTestKeyProvider
from gravya_e1.partitions import ensure_partition
from gravya_e1.signals import InMemorySignalSink

DB = "gravya_e1_review"
REPO = "/workspace/wt-impl-e1"


@pytest.fixture(scope="session", autouse=True)
def scratch_db():
    adm = psycopg.connect("dbname=postgres", autocommit=True)
    adm.execute(f"DROP DATABASE IF EXISTS {DB}")
    adm.execute(f"CREATE DATABASE {DB} OWNER root")
    env = dict(os.environ, DATABASE_URL=f"postgresql+psycopg://root@/{DB}")
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=REPO, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    yield
    adm.execute(f"DROP DATABASE IF EXISTS {DB}")
    adm.close()


@pytest.fixture()
def admin_conn():
    c = psycopg.connect(f"dbname={DB}")
    yield c
    c.rollback()
    c.close()


@pytest.fixture()
def signal_sink():
    return InMemorySignalSink()


@pytest.fixture()
def variables(signal_sink):
    return SnapshotVariableRegistry(signal_sink=signal_sink, production_override=False)


@pytest.fixture()
def prod_variables(signal_sink):
    # produzione: "da definire" bloccate; per questi script usiamo uno snapshot con valori "deciso"
    import json, pathlib, tempfile
    d = pathlib.Path(__file__).parent / "basetemp_snap"
    d.mkdir(exist_ok=True)
    p = d / "snap.json"
    p.write_text(json.dumps({"variables": {
        "e1.write_buffer_size": {"value": 100, "unit": "count", "status": "deciso"},
        "e1.attributes.max_value_bytes": {"value": 2048, "unit": "bytes", "status": "deciso"},
        "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_connect_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_tcp_keepalives_idle_s": {"value": 10, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_interval_s": {"value": 5, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_count": {"value": 3, "unit": "count", "status": "deciso"},
    }}))
    return SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=p, production_override=True)


@pytest.fixture()
def key_provider():
    return StaticTestKeyProvider()


@pytest.fixture()
def partitions(admin_conn, variables):
    ts = datetime.now(timezone.utc)
    ensure_partition(admin_conn, "gravya_traces", ts, variables)
    ensure_partition(admin_conn, "gravya_trace_segments", ts, variables)
