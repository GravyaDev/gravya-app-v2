"""Criterio 3: RLS per tenant con WITH CHECK, ruolo writer senza bypass.

Ogni traccia e segmento ha tenant_id non nullo; un tenant non legge le
tracce di un altro; una scrittura con tenant_id diverso dal contesto e'
rifiutata dal WITH CHECK. Le query girano con SET LOCAL ROLE gravya_writer
(non superuser): un superuser salterebbe RLS e renderebbe questo test un
falso positivo (vincolo 7 del task implementer).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.db import writer_transaction

NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def _insert_trace(conn, tenant_id, trace_id, run_id="run-1"):
    with writer_transaction(conn, str(tenant_id)) as tconn:
        with tconn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at)
                VALUES (%s, %s, %s, 'agent', %s)
                """,
                (str(trace_id), str(tenant_id), run_id, NOW()),
            )


def test_writer_non_e_superuser(admin_conn):
    with admin_conn.cursor() as cur:
        cur.execute(
            "select rolsuper, rolbypassrls from pg_roles where rolname = 'gravya_writer'"
        )
        rolsuper, rolbypassrls = cur.fetchone()
    assert rolsuper is False
    assert rolbypassrls is False


def test_tenant_non_legge_tracce_di_un_altro(admin_conn, ensure_partitions_now):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    trace_a = uuid.uuid4()
    _insert_trace(admin_conn, tenant_a, trace_a)

    with writer_transaction(admin_conn, str(tenant_a)) as tconn:
        with tconn.cursor() as cur:
            cur.execute("SELECT trace_id FROM gravya_traces WHERE trace_id = %s", (str(trace_a),))
            assert cur.fetchone() is not None

    with writer_transaction(admin_conn, str(tenant_b)) as tconn:
        with tconn.cursor() as cur:
            cur.execute("SELECT trace_id FROM gravya_traces WHERE trace_id = %s", (str(trace_a),))
            assert cur.fetchone() is None


def test_scrittura_con_tenant_diverso_dal_contesto_rifiutata(admin_conn, ensure_partitions_now):
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    trace_id = uuid.uuid4()

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with writer_transaction(admin_conn, str(tenant_b)) as tconn:
            with tconn.cursor() as cur:
                # Sessione impostata come tenant_b, ma la riga dichiara tenant_a:
                # il WITH CHECK della policy deve rifiutarla.
                cur.execute(
                    """
                    INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at)
                    VALUES (%s, %s, 'run-x', 'agent', %s)
                    """,
                    (str(trace_id), str(tenant_a), NOW()),
                )
    admin_conn.rollback()

    # la riga non deve essere comparsa (ne' come tenant_a ne' come tenant_b)
    with admin_conn.cursor() as cur:  # admin_conn e' superuser: bypassa RLS solo per la verifica
        cur.execute("SELECT 1 FROM gravya_traces WHERE trace_id = %s", (str(trace_id),))
        assert cur.fetchone() is None


def test_tenant_id_non_nullo(admin_conn, ensure_partitions_now):
    trace_id = uuid.uuid4()
    with pytest.raises(psycopg.errors.NotNullViolation):
        with admin_conn.transaction():
            with admin_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at)
                    VALUES (%s, NULL, 'run-x', 'agent', %s)
                    """,
                    (str(trace_id), NOW()),
                )
    admin_conn.rollback()
