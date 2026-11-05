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
def make_helper():
    """Costruisce un TracingHelper con conninfo esplicito (DB di test) e lo
    chiude a fine test (ferma il thread di sfondo, giro 3)."""
    created = []

    def _make(variables, signal_sink, key_provider_, **kwargs):
        from gravya_e1.tracing import TracingHelper

        kwargs.setdefault("conninfo", pg_dsn(TEST_DB_NAME))
        helper = TracingHelper(variables, signal_sink, key_provider_, **kwargs)
        created.append(helper)
        return helper

    yield _make
    for helper in created:
        try:
            helper.close(timeout=5)
        except Exception:
            pass


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


@pytest.fixture()
def password_auth_conninfo(admin_conn):
    """Ruolo di test con autenticazione a password via TCP (giro 3, G7).

    Dimostra che l'helper puo' scrivere con una connessione propria
    autenticata a password, mai letta dalla connessione del chiamante:
    password generata a runtime (non un segreto nel codice/nei test), mai
    salvata su disco, valida solo per la sessione di questo processo. Usa la
    regola generica gia' presente in pg_hba.conf
    (`host all all 127.0.0.1/32 scram-sha-256`): nessuna riga nuova.
    """
    import secrets

    from psycopg import sql

    role = "gravya_e1_pwtest"
    password = secrets.token_urlsafe(24)
    with admin_conn.cursor() as cur:
        cur.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                    CREATE ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
                END IF;
            END
            $$;
            """
        )
        cur.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
        cur.execute(f"GRANT gravya_writer TO {role};")
        cur.execute(f"GRANT CONNECT ON DATABASE {TEST_DB_NAME} TO {role};")
    admin_conn.commit()
    try:
        yield f"host=127.0.0.1 user={role} password={password} dbname={TEST_DB_NAME}"
    finally:
        with admin_conn.cursor() as cur:
            cur.execute(f"ALTER ROLE {role} PASSWORD NULL;")
        admin_conn.commit()
