"""Fixture degli script di riproduzione del giro 2 (code-reviewer). DB scratch `gravya_e1_review2`
(alembic upgrade head con le migrazioni del branch, eliminato a fine sessione). Non tocca `gravya_e1_test`.
Esecuzione: cd /workspace/wt-impl-e1 && . .venv/bin/activate &&
  pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro2/basetemp docs/revisioni/impl-e1/code-reviewer-giro2/test_giro2.py
(una sola cartella alla volta: ha un conftest.py proprio, distinto da quello di code-reviewer/)."""
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

DB = "gravya_e1_review2"
REPO = "/workspace/wt-impl-e1"
HERE = pathlib.Path(__file__).parent


@pytest.fixture(scope="session", autouse=True)
def scratch_db():
    adm = psycopg.connect("dbname=postgres", autocommit=True)
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
    c = psycopg.connect(f"dbname={DB}")
    yield c
    c.rollback()
    c.close()


@pytest.fixture()
def signal_sink():
    return InMemorySignalSink()


def _prod_registry(sink, extra=None):
    d = HERE / "snap_tmp"
    d.mkdir(exist_ok=True)
    p = d / "snap.json"
    vars_ = {
        "e1.write_buffer_size": {"value": 100, "unit": "count", "status": "deciso"},
        "e1.attributes.max_value_bytes": {"value": 2048, "unit": "bytes", "status": "deciso"},
        "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.partition_interval_months": {"value": 1, "unit": "months", "status": "deciso"},
        "e1.write_connect_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_tcp_keepalives_idle_s": {"value": 10, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_interval_s": {"value": 5, "unit": "s", "status": "deciso"},
        "e1.write_tcp_keepalives_count": {"value": 3, "unit": "count", "status": "deciso"},
        "e1.write_tcp_user_timeout_ms": {"value": 5000, "unit": "ms", "status": "deciso"},
    }
    vars_.update(extra or {})
    p.write_text(json.dumps({"variables": vars_}))
    return SnapshotVariableRegistry(signal_sink=sink, snapshot_path=p, production_override=True)


@pytest.fixture()
def prod_variables(signal_sink):
    return _prod_registry(signal_sink)


@pytest.fixture()
def make_registry(signal_sink):
    return lambda extra=None: _prod_registry(signal_sink, extra)


@pytest.fixture()
def key_provider():
    return StaticTestKeyProvider()


@pytest.fixture()
def partitions(admin_conn, prod_variables):
    ts = datetime.now(timezone.utc)
    ensure_partition(admin_conn, "gravya_traces", ts, prod_variables)
    ensure_partition(admin_conn, "gravya_trace_segments", ts, prod_variables)
