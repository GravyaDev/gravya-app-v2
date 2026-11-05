from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.keys import StaticTestKeyProvider
from gravya_e1.partitions import ensure_partition
from gravya_e1.signals import InMemorySignalSink

from _pgconn import pg_dsn

TEST_DB_NAME = "gravya_e1_test"


@pytest.fixture()
def admin_conn():
    """Connessione da superuser di sviluppo locale (ruolo di sviluppo, auth peer o PG*).

    Usata solo per compiti amministrativi nei test (creare partizioni,
    ispezionare dati bypassando RLS per verificare cosa e' stato scritto
    davvero). Le scritture applicative passano sempre da `writer_transaction`
    (ruolo `gravya_writer`, senza bypass di RLS). Il DSN si legge da
    `GRAVYA_E1_TEST_DSN`/variabili PG* (CR: niente socket Unix fisso).
    """
    conn = psycopg.connect(pg_dsn(TEST_DB_NAME))
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture()
def signal_sink():
    return InMemorySignalSink()


@pytest.fixture()
def variables(signal_sink):
    return SnapshotVariableRegistry(signal_sink=signal_sink, production_override=False)


@pytest.fixture()
def key_provider():
    return StaticTestKeyProvider()


@pytest.fixture()
def new_tenant_id():
    return uuid.uuid4()


@pytest.fixture()
def ensure_partitions_now(admin_conn, variables):
    """Crea le partizioni che coprono 'adesso' per entrambe le tabelle."""

    def _ensure(for_timestamp: datetime | None = None):
        ts = for_timestamp or datetime.now(timezone.utc)
        ensure_partition(admin_conn, "gravya_traces", ts, variables)
        ensure_partition(admin_conn, "gravya_trace_segments", ts, variables)

    _ensure()
    return _ensure
