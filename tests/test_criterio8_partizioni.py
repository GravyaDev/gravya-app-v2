"""Criterio 8 (sola parte di partizione, passo 2).

Le tabelle sono partizionate per tempo con `e1.partition_interval_months`
letto dall'istantanea E5 (nessun valore fisso: qui il campione di test e' un
parametro del test che cita il catalogo, DA-CV-04 (b)). La creazione e'
idempotente e una riga finisce nella partizione corretta per il suo
`started_at`.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.db import writer_transaction
from gravya_e1.partitions import ensure_partition, partition_bounds


def _registry_with_interval(tmp_path, signal_sink, months: int) -> SnapshotVariableRegistry:
    # Campione di test (catalogo-variabili.md §12, riga `e1.partition_interval_months`,
    # "proposta da validare"): qui si usa un valore diverso dal default (1) per
    # dimostrare che il codice non ha l'intervallo fisso (DX-22).
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            {
                "variables": {
                    "e1.partition_interval_months": {
                        "value": months,
                        "unit": "months",
                        "status": "proposta_da_validare",
                    }
                }
            }
        )
    )
    return SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)


def test_partizione_creata_ha_rls_abilitata_e_forzata(admin_conn, tmp_path, signal_sink):
    """CA minore / CR R-11: una partizione protegge anche l'accesso diretto, non solo via il padre."""
    reg = _registry_with_interval(tmp_path, signal_sink, months=1)
    ts = datetime(2029, 9, 10, tzinfo=timezone.utc)
    name = ensure_partition(admin_conn, "gravya_traces", ts, reg)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = %s", (name,))
        row_security, force_security = cur.fetchone()
    assert row_security is True
    assert force_security is True


def test_calcolo_confini_rispetta_intervallo_dalla_variabile(tmp_path, signal_sink):
    reg = _registry_with_interval(tmp_path, signal_sink, months=2)
    interval = reg.get("e1.partition_interval_months").value
    start, end = partition_bounds(datetime(2026, 3, 15, tzinfo=timezone.utc), interval)
    # bucket di 2 mesi allineato a gennaio (epoca 2000): marzo-aprile 2026
    assert start == datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert end == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_creazione_partizione_idempotente(admin_conn, tmp_path, signal_sink):
    reg = _registry_with_interval(tmp_path, signal_sink, months=1)
    ts = datetime(2027, 6, 10, tzinfo=timezone.utc)
    name1 = ensure_partition(admin_conn, "gravya_traces", ts, reg)
    name2 = ensure_partition(admin_conn, "gravya_traces", ts, reg)
    assert name1 == name2 == "gravya_traces_p202706_202707"


def test_riga_finisce_nella_partizione_corretta_per_il_tempo(admin_conn, tmp_path, signal_sink):
    reg = _registry_with_interval(tmp_path, signal_sink, months=1)
    tenant_id = uuid.uuid4()
    ts_in_month_a = datetime(2028, 1, 10, tzinfo=timezone.utc)
    ts_in_month_b = datetime(2028, 2, 10, tzinfo=timezone.utc)

    part_a = ensure_partition(admin_conn, "gravya_traces", ts_in_month_a, reg)
    part_b = ensure_partition(admin_conn, "gravya_traces", ts_in_month_b, reg)
    assert part_a != part_b

    trace_a = uuid.uuid4()
    trace_b = uuid.uuid4()
    with writer_transaction(admin_conn, str(tenant_id)) as tconn:
        with tconn.cursor() as cur:
            cur.execute(
                "INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at) "
                "VALUES (%s, %s, 'run-a', 'agent', %s)",
                (str(trace_a), str(tenant_id), ts_in_month_a),
            )
            cur.execute(
                "INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at) "
                "VALUES (%s, %s, 'run-b', 'agent', %s)",
                (str(trace_b), str(tenant_id), ts_in_month_b),
            )

    with admin_conn.cursor() as cur:
        cur.execute(f"SELECT trace_id FROM {part_a}")
        rows_a = {str(r[0]) for r in cur.fetchall()}
        cur.execute(f"SELECT trace_id FROM {part_b}")
        rows_b = {str(r[0]) for r in cur.fetchall()}
    assert str(trace_a) in rows_a
    assert str(trace_b) in rows_b
    assert str(trace_a) not in rows_b
    assert str(trace_b) not in rows_a
