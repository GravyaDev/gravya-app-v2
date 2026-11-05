"""Partizioni per tempo di `gravya_traces` / `gravya_trace_segments`.

L'intervallo delle partizioni e' `e1.partition_interval_months`, letto
dall'istantanea E5 (nessun valore fisso, DX-22, vincolo 2 del task
implementer). La creazione e' idempotente: puo' essere richiamata piu' volte
per lo stesso intervallo di tempo senza errore.

La gestione delle partizioni (quando crearle in anticipo, quando eliminarle
per retention) e' un job separato dal writer applicativo: qui c'e' solo il
calcolo dei confini e la creazione, usati dai test del criterio 8 (parte di
partizione) e, in futuro, dal passo 6 (fuori dal perimetro di questo task).
"""
from __future__ import annotations

from datetime import datetime, timezone

from psycopg import sql

from gravya_e1.config.variables import VariableRegistry

PARTITIONED_TABLES = ("gravya_traces", "gravya_trace_segments")


def _add_months(year: int, month0: int, months: int) -> tuple[int, int]:
    """month0 e' 0-based (0=gennaio). Ritorna (year, month0) dopo l'aggiunta."""
    total = year * 12 + month0 + months
    return total // 12, total % 12


def partition_bounds(for_timestamp: datetime, interval_months: int) -> tuple[datetime, datetime]:
    """Calcola i confini [start, end) della partizione che contiene `for_timestamp`.

    I bucket sono allineati a gennaio dell'anno di `for_timestamp.year`'s epoca
    fissa (anno 2000) in passi di `interval_months` mesi di calendario.
    """
    if for_timestamp.tzinfo is None:
        for_timestamp = for_timestamp.replace(tzinfo=timezone.utc)
    epoch_year = 2000
    months_since_epoch = (for_timestamp.year - epoch_year) * 12 + (for_timestamp.month - 1)
    bucket_index = months_since_epoch // interval_months
    bucket_start_months = bucket_index * interval_months
    start_year, start_month0 = _add_months(epoch_year, 0, bucket_start_months)
    end_year, end_month0 = _add_months(epoch_year, 0, bucket_start_months + interval_months)
    start = datetime(start_year, start_month0 + 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, end_month0 + 1, 1, tzinfo=timezone.utc)
    return start, end


def partition_suffix(start: datetime) -> str:
    return start.strftime("%Y%m")


def ensure_partition(admin_conn, table: str, for_timestamp: datetime, variables: VariableRegistry) -> str:
    """Crea (se assente) la partizione di `table` che copre `for_timestamp`.

    Ritorna il nome della partizione creata o gia' esistente. Richiede una
    connessione con privilegio di CREATE (ruolo amministrativo, non il
    writer applicativo).
    """
    if table not in PARTITIONED_TABLES:
        raise ValueError(f"tabella non partizionata da E1: {table}")
    interval_months = variables.get("e1.partition_interval_months").value
    start, end = partition_bounds(for_timestamp, interval_months)
    partition_name = f"{table}_p{partition_suffix(start)}"
    # PostgreSQL non ammette parametri bind nei confini "FOR VALUES FROM/TO"
    # (sono letterali valutati in fase di parse): si usano identificatori e
    # letterali tipizzati in modo sicuro con psycopg.sql, non interpolazione
    # di stringhe sui valori che arrivano da fuori (qui start/end sono
    # calcolati internamente da `partition_bounds`, mai da input esterno).
    query = sql.SQL(
        "CREATE TABLE IF NOT EXISTS {partition} PARTITION OF {table} "
        "FOR VALUES FROM ({start}) TO ({end});"
    ).format(
        partition=sql.Identifier(partition_name),
        table=sql.Identifier(table),
        start=sql.Literal(start),
        end=sql.Literal(end),
    )
    with admin_conn.cursor() as cur:
        cur.execute(query)
    admin_conn.commit()
    return partition_name
