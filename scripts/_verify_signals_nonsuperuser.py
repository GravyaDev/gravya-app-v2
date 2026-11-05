"""Verifica G3-03 (giro 4): `PostgresSignalSink` da un ruolo non superuser
membro di `gravya_writer`: l'INSERT riesce (la policy `WITH CHECK` sul GUC
del tenant lo permette perche' il sink lo imposta lui stesso), il SELECT e'
negato (il writer non ha piu' `SELECT` su questa tabella, G15/G15b).

Invocato da `scripts/test-non-superuser.sh` dopo le migrazioni. Stesse
variabili d'ambiente di `scripts/_verify_nonsuperuser.py`. Esce con codice
diverso da 0 se una delle affermazioni e' falsa.
"""
from __future__ import annotations

import os
import secrets
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from gravya_e1.signals import PostgresSignalSink  # noqa: E402

SUPERUSER_DSN = os.environ["GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN"]
HOST = os.environ.get("GRAVYA_E1_CI_NONSUPER_HOST", "localhost")
PORT = os.environ.get("GRAVYA_E1_CI_NONSUPER_PORT", "5432")
DBNAME = os.environ["GRAVYA_E1_CI_NONSUPER_DB"]

ROLE = "gravya_e1_ci_nonsuper_signaler"


def main() -> None:
    admin = psycopg.connect(SUPERUSER_DSN)
    password = secrets.token_urlsafe(24)
    role_conn: psycopg.Connection | None = None
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
            cur.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(ROLE), sql.Literal(password)))
            cur.execute(f"GRANT gravya_writer TO {ROLE};")
            cur.execute(f"GRANT CONNECT ON DATABASE {DBNAME} TO {ROLE};")
        admin.commit()

        role_conn = psycopg.connect(host=HOST, port=PORT, user=ROLE, password=password, dbname=DBNAME)
        tenant_id = str(uuid.uuid4())
        sink = PostgresSignalSink(role_conn)
        sink.emit("trace.write_failed", tenant_id=tenant_id, table="gravya_traces", reason="verifica", count=1)

        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM gravya_signals_min_audit WHERE tenant_id = %s", (tenant_id,))
            assert cur.fetchone() is not None, "il segnale non e' stato inserito dal ruolo non superuser"
        admin.rollback()

        try:
            with role_conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM gravya_signals_min_audit")
            role_conn.rollback()
        except psycopg.errors.InsufficientPrivilege:
            role_conn.rollback()
        else:
            raise AssertionError("il ruolo non superuser (membro di gravya_writer) ha potuto leggere i segnali")

        print("OK: PostgresSignalSink da ruolo non superuser inserisce ma non legge (G3-03)")
    finally:
        if role_conn is not None:
            role_conn.close()
        try:
            with admin.cursor() as cur:
                cur.execute(f"DROP OWNED BY {ROLE};")
            admin.commit()
        except Exception:  # noqa: BLE001
            admin.rollback()
        try:
            with admin.cursor() as cur:
                cur.execute(f"DROP ROLE IF EXISTS {ROLE};")
            admin.commit()
        except Exception:  # noqa: BLE001
            admin.rollback()
        admin.close()


if __name__ == "__main__":
    main()
