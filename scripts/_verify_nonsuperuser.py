"""Verifica funzionale usata da `scripts/test-non-superuser.sh` (criterio di
fine 2, E1 v1.6): fa scrivere e leggere davvero l'applicazione (TracingHelper,
`writer_transaction`, la funzione SECURITY DEFINER cross-tenant) su uno schema
creato da `gravya_migrator` (ruolo non superuser), non da un superuser come
nei test ordinari di `tests/`.

Non e' un test pytest apposta: gira come script a se' nella pipeline di CI
(e localmente), dopo che lo schema e' gia' stato migrato con
`MIGRATION_ROLE=gravya_migrator`. Variabili d'ambiente attese (impostate dal
chiamante bash):
  GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN - DSN superuser sul database usa e getta
  GRAVYA_E1_CI_NONSUPER_HOST/_PORT/_DB - per costruire il DSN del ruolo di prova

Esce con codice diverso da 0 (eccezione non catturata) se una delle
affermazioni e' falsa.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from gravya_e1.config.variables import SnapshotVariableRegistry  # noqa: E402
from gravya_e1.db import writer_transaction  # noqa: E402
from gravya_e1.keys import StaticTestKeyProvider  # noqa: E402
from gravya_e1.models import SegmentStart, TraceStart  # noqa: E402
from gravya_e1.partitions import ensure_partition  # noqa: E402
from gravya_e1.signals import InMemorySignalSink  # noqa: E402
from gravya_e1.tracing import TracingHelper  # noqa: E402

NOW = lambda: datetime.now(timezone.utc)  # noqa: E731

SUPERUSER_DSN = os.environ["GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN"]
HOST = os.environ.get("GRAVYA_E1_CI_NONSUPER_HOST", "localhost")
PORT = os.environ.get("GRAVYA_E1_CI_NONSUPER_PORT", "5432")
DBNAME = os.environ["GRAVYA_E1_CI_NONSUPER_DB"]

ROLE = "gravya_e1_ci_nonsuper_writer"


def _build_variables(tmpdir: Path) -> SnapshotVariableRegistry:
    snapshot = {
        "variables": {
            "e1.partition_interval_months": {"value": 1, "unit": "months", "status": "deciso"},
            "e1.overhead_p95_ms": {"value": 5, "unit": "ms", "status": "deciso"},
            "e1.write_buffer_size": {"value": 100, "unit": "count", "status": "deciso"},
            "e1.attributes.max_value_bytes": {"value": 2048, "unit": "bytes", "status": "deciso"},
            "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
            "e1.write_connect_timeout_s": {"value": 2, "unit": "s", "status": "deciso", "min": 2},
            "e1.write_tcp_keepalives_idle_s": {"value": 10, "unit": "s", "status": "deciso"},
            "e1.write_tcp_keepalives_interval_s": {"value": 5, "unit": "s", "status": "deciso"},
            "e1.write_tcp_keepalives_count": {"value": 3, "unit": "count", "status": "deciso"},
            "e1.write_tcp_user_timeout_ms": {"value": 5000, "unit": "ms", "status": "deciso"},
        }
    }
    # Giro 4 (CR N13): directory temporanea cancellata da `main()` alla fine
    # (`TemporaryDirectory`), mai un file lasciato in /tmp.
    path = tmpdir / "snapshot.json"
    path.write_text(json.dumps(snapshot))
    return SnapshotVariableRegistry(signal_sink=InMemorySignalSink(), snapshot_path=path)


def main() -> None:
    admin = psycopg.connect(SUPERUSER_DSN)
    password = secrets.token_urlsafe(24)
    tmpdir_ctx = TemporaryDirectory()
    try:
        with admin.cursor() as cur:
            cur.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROLE}') THEN
                        CREATE ROLE {ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
                    END IF;
                END
                $$;
                """
            )
            from psycopg import sql

            cur.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(ROLE), sql.Literal(password)))
            cur.execute(f"GRANT gravya_writer TO {ROLE};")
            cur.execute(f"GRANT CONNECT ON DATABASE {DBNAME} TO {ROLE};")
        admin.commit()

        variables = _build_variables(Path(tmpdir_ctx.name))
        ensure_partition(admin, "gravya_traces", NOW(), variables)
        ensure_partition(admin, "gravya_trace_segments", NOW(), variables)
        admin.commit()

        conninfo = f"host={HOST} port={PORT} user={ROLE} password={password} dbname={DBNAME}"
        key_provider = StaticTestKeyProvider()
        signal_sink = InMemorySignalSink()
        helper = TracingHelper(variables, signal_sink, key_provider, conninfo=conninfo)
        try:
            tenant_a = uuid.uuid4()
            tenant_b = uuid.uuid4()
            trace_id = uuid.uuid4()
            segment_id = uuid.uuid4()

            helper.start_trace(
                admin,
                TraceStart(trace_id=trace_id, tenant_id=tenant_a, run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW()),
            )
            helper.start_segment(
                admin,
                SegmentStart(
                    segment_id=segment_id, trace_id=trace_id, tenant_id=tenant_a,
                    kind="agent", started_at=NOW(), attributes={"gen_ai.agent.id": "agent_cinonsuper"},
                ),
            )
            assert helper.flush(timeout=5), "la coda non si e' svuotata entro il timeout"
        finally:
            helper.close(timeout=5)

        admin.rollback()
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM gravya_traces WHERE trace_id=%s AND tenant_id=%s", (str(trace_id), str(tenant_a)))
            assert cur.fetchone() is not None, "la traccia non e' stata scritta (schema di gravya_migrator)"
            cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id=%s", (str(segment_id),))
            assert cur.fetchone() is not None, "il segmento non e' stato scritto (schema di gravya_migrator)"

        # Trigger anti-modifica su riga chiusa: anche sullo schema creato da
        # gravya_migrator deve rifiutare un UPDATE diretto su una traccia mai
        # aperta per la chiusura (status assente/aperta -> chiudiamola prima).
        with admin.cursor() as cur:
            cur.execute("UPDATE gravya_traces SET ended_at = now(), status = 'ok' WHERE trace_id=%s", (str(trace_id),))
        admin.commit()
        try:
            with admin.cursor() as cur:
                cur.execute("UPDATE gravya_traces SET ended_at = now() WHERE trace_id=%s", (str(trace_id),))
            admin.commit()
        except psycopg.errors.IntegrityConstraintViolation:
            admin.rollback()
        else:
            raise AssertionError("il trigger anti-modifica non ha bloccato l'UPDATE su una riga chiusa")

        # Funzione SECURITY DEFINER cross-tenant (a un parametro, legge il GUC):
        # sotto il ruolo non superuser gravya_writer, con app.tenant_id = tenant B,
        # deve rilevare che trace_id appartiene a un altro tenant (tenant A).
        with writer_transaction(admin, str(tenant_b)) as conn, conn.cursor() as cur:
            cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(trace_id),))
            owned_by_other = cur.fetchone()[0]
        admin.rollback()
        assert owned_by_other is True, "la funzione cross-tenant non ha rilevato il tenant diverso"

        print("OK: scrittura, trigger anti-modifica e funzione cross-tenant funzionano con schema non superuser")
    finally:
        # Giro 4 (CA G3-09): un ruolo LOGIN senza password, in un cluster con
        # autenticazione `trust`, resta utilizzabile da chiunque si connetta.
        # `DROP OWNED BY` + `DROP ROLE` (non solo azzerare la password) lo
        # elimina davvero: nessun ruolo residuo con privilegi su `gravya_writer`.
        try:
            with admin.cursor() as cur:
                cur.execute(f"DROP OWNED BY {ROLE};")
        except Exception:  # noqa: BLE001 - difensivo: la pulizia non deve mai far fallire lo script con un errore oscuro
            admin.rollback()
        else:
            admin.commit()
        try:
            with admin.cursor() as cur:
                cur.execute(f"DROP ROLE IF EXISTS {ROLE};")
            admin.commit()
        except Exception:  # noqa: BLE001
            admin.rollback()
        admin.close()
        tmpdir_ctx.cleanup()


if __name__ == "__main__":
    main()
