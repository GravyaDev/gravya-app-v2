"""Passo 0 (ossatura del repository): il sistema di migrazioni esiste,
e' eseguibile dal comando di test della CI, e la migrazione si applica e si
annulla su un PostgreSQL di test (verifica del passo 0, §9).
"""
from __future__ import annotations

import os
import subprocess
import sys

import psycopg
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def scratch_database():
    name = "gravya_e1_migration_check"
    admin = psycopg.connect("dbname=postgres", autocommit=True)
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {name}")
        cur.execute(f"CREATE DATABASE {name} OWNER root")
    admin.close()
    yield name
    admin = psycopg.connect("dbname=postgres", autocommit=True)
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {name}")
    admin.close()


def _alembic(args: list[str], dsn: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DATABASE_URL"] = f"postgresql+psycopg://root@/{dsn}"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _user_tables(dsn: str) -> set[str]:
    conn = psycopg.connect(f"dbname={dsn}")
    with conn.cursor() as cur:
        cur.execute(
            "select table_name from information_schema.tables "
            "where table_schema = 'public' and table_type = 'BASE TABLE' "
            "and table_name != 'alembic_version'"
        )
        tables = {row[0] for row in cur.fetchall()}
    conn.close()
    return tables


def test_migrazioni_si_applicano_e_si_annullano(scratch_database):
    up = _alembic(["upgrade", "head"], scratch_database)
    assert up.returncode == 0, up.stderr

    down = _alembic(["downgrade", "base"], scratch_database)
    assert down.returncode == 0, down.stderr

    tables_after_downgrade = _user_tables(scratch_database)
    assert tables_after_downgrade == set()

    # riapplica, cosi' il comando di test della CI resta ripetibile
    up_again = _alembic(["upgrade", "head"], scratch_database)
    assert up_again.returncode == 0, up_again.stderr
