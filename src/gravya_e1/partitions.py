"""Partizioni per tempo di `gravya_traces` / `gravya_trace_segments`.

L'intervallo delle partizioni e' `e1.partition_interval_months`, letto
dall'istantanea E5 (nessun valore fisso, DX-22, vincolo 2 del task
implementer). La creazione e' idempotente: puo' essere richiamata piu' volte
per lo stesso intervallo di tempo senza errore.

La gestione delle partizioni (quando crearle in anticipo, quando eliminarle
per retention) e' un job separato dal writer applicativo: qui c'e' solo il
calcolo dei confini e la creazione, usati dai test del criterio 8 (parte di
partizione) e, in futuro, dal passo 6 (fuori dal perimetro di questo task).

Giro 2:
- CR R14a: i timestamp con fuso orario diverso da UTC vengono convertiti in
  UTC prima del calcolo dei confini (non solo quelli "naive").
- CR R14b: se una partizione esistente copre gia' il timestamp richiesto
  (anche con confini diversi da quelli che l'intervallo corrente
  calcolerebbe, per esempio dopo un cambio di `e1.partition_interval_months`)
  si usa quella, senza dichiarare una copertura falsa; se nessuna partizione
  esistente copre il timestamp, i confini naturali dell'intervallo corrente
  sono ristretti per non sovrapporsi a partizioni gia' create con un
  intervallo diverso (PostgreSQL non ammette intervalli di partizione
  sovrapposti).
- CA minore/R-11: ogni partizione creata ha RLS abilitata e forzata (le
  policy del padre partizionato non si applicano automaticamente a un
  accesso diretto sulla partizione).
- `epoch_year` (2000) e' un'invariante di allineamento dei bucket mensili,
  non una variabile di piattaforma: fissa solo da quale mese si contano gli
  intervalli, non una soglia o una durata (da confermare nel report).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from psycopg import sql

from gravya_e1.config.variables import VariableRegistry

PARTITIONED_TABLES = ("gravya_traces", "gravya_trace_segments")

# Invariante di allineamento dei bucket (non una variabile di piattaforma,
# vedi report): da quale anno si contano i mesi per `e1.partition_interval_months`.
_EPOCH_YEAR = 2000

_BOUND_RE = re.compile(r"FOR VALUES FROM \('([^']+)'\) TO \('([^']+)'\)")


def _add_months(year: int, month0: int, months: int) -> tuple[int, int]:
    """month0 e' 0-based (0=gennaio). Ritorna (year, month0) dopo l'aggiunta."""
    total = year * 12 + month0 + months
    return total // 12, total % 12


def partition_bounds(for_timestamp: datetime, interval_months: int) -> tuple[datetime, datetime]:
    """Calcola i confini [start, end) della partizione che contiene `for_timestamp`.

    `for_timestamp` e' sempre convertito in UTC prima del calcolo (CR R14a),
    sia che sia "naive" (trattato come gia' UTC) sia che abbia un fuso
    orario diverso.
    """
    if for_timestamp.tzinfo is None:
        for_timestamp = for_timestamp.replace(tzinfo=timezone.utc)
    else:
        for_timestamp = for_timestamp.astimezone(timezone.utc)
    months_since_epoch = (for_timestamp.year - _EPOCH_YEAR) * 12 + (for_timestamp.month - 1)
    bucket_index = months_since_epoch // interval_months
    bucket_start_months = bucket_index * interval_months
    start_year, start_month0 = _add_months(_EPOCH_YEAR, 0, bucket_start_months)
    end_year, end_month0 = _add_months(_EPOCH_YEAR, 0, bucket_start_months + interval_months)
    start = datetime(start_year, start_month0 + 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, end_month0 + 1, 1, tzinfo=timezone.utc)
    return start, end


def partition_suffix(moment: datetime) -> str:
    return moment.strftime("%Y%m")


def _existing_partitions(conn, table: str) -> list[tuple[str, datetime, datetime]]:
    with conn.transaction():
        with conn.cursor() as cur:
            # Giro 3 (G12): `pg_get_expr` rende i timestamp nel TimeZone della
            # sessione, non in UTC. Si forza UTC solo per questa transazione,
            # cosi' il confine letto e' sempre in UTC indipendentemente dal
            # TimeZone del chiamante (per esempio 'Europe/Rome').
            cur.execute("SET LOCAL TimeZone = 'UTC'")
            cur.execute(
                """
                SELECT c.relname, pg_get_expr(c.relpartbound, c.oid)
                FROM pg_inherits i
                JOIN pg_class c ON c.oid = i.inhrelid
                JOIN pg_class p ON p.oid = i.inhparent
                WHERE p.relname = %s
                """,
                (table,),
            )
            rows = cur.fetchall()
    result = []
    for name, bound_text in rows:
        if not bound_text:
            continue
        m = _BOUND_RE.search(bound_text)
        if not m:
            continue
        start = datetime.strptime(m.group(1)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        end = datetime.strptime(m.group(2)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        result.append((name, start, end))
    return result


def ensure_partition(admin_conn, table: str, for_timestamp: datetime, variables: VariableRegistry) -> str:
    """Crea (se assente) la partizione di `table` che copre `for_timestamp`.

    Ritorna il nome della partizione creata o gia' esistente. Richiede una
    connessione con privilegio di CREATE (ruolo amministrativo, non il
    writer applicativo).
    """
    if table not in PARTITIONED_TABLES:
        raise ValueError(f"tabella non partizionata da E1: {table}")

    if for_timestamp.tzinfo is None:
        for_timestamp_utc = for_timestamp.replace(tzinfo=timezone.utc)
    else:
        for_timestamp_utc = for_timestamp.astimezone(timezone.utc)

    existing = _existing_partitions(admin_conn, table)
    for name, est_start, est_end in existing:
        if est_start <= for_timestamp_utc < est_end:
            return name  # gia' coperto, anche se i confini non sono quelli dell'intervallo corrente

    interval_months = variables.get("e1.partition_interval_months").value
    start, end = partition_bounds(for_timestamp_utc, interval_months)

    # Restringe i confini naturali per non sovrapporsi a partizioni gia'
    # create con un intervallo diverso (PostgreSQL non ammette intervalli di
    # partizione sovrapposti): CR R14b.
    for _name, est_start, est_end in existing:
        if est_start < end and start < est_end:
            if est_end <= for_timestamp_utc:
                start = max(start, est_end)
            if est_start > for_timestamp_utc:
                end = min(end, est_start)

    if start >= end:
        raise RuntimeError(
            f"nessun intervallo libero per {for_timestamp_utc.isoformat()} su {table}: "
            "partizioni esistenti incompatibili con l'intervallo corrente"
        )

    partition_name = f"{table}_p{partition_suffix(start)}_{partition_suffix(end)}"
    # PostgreSQL non ammette parametri bind nei confini "FOR VALUES FROM/TO"
    # (sono letterali valutati in fase di parse): si usano identificatori e
    # letterali tipizzati in modo sicuro con psycopg.sql, non interpolazione
    # di stringhe sui valori che arrivano da fuori (qui start/end sono
    # calcolati internamente, mai da input esterno).
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
        # RLS su ogni partizione (CA minore, CR R-11): le policy del padre
        # partizionato non proteggono un accesso diretto alla partizione.
        cur.execute(
            sql.SQL("ALTER TABLE {partition} ENABLE ROW LEVEL SECURITY;").format(
                partition=sql.Identifier(partition_name)
            )
        )
        cur.execute(
            sql.SQL("ALTER TABLE {partition} FORCE ROW LEVEL SECURITY;").format(
                partition=sql.Identifier(partition_name)
            )
        )
    admin_conn.commit()
    return partition_name
