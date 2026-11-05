#!/usr/bin/env bash
# Criterio di fine 2 (E1 v1.6): le migrazioni e l'applicazione devono
# funzionare quando lo schema e' di proprieta' di un ruolo non superuser.
#
# Procedura (stessa verifica manuale fatta nel giro 3, qui come script
# riusabile/versionato, invocato anche da CI):
#   1. database usa e getta, eliminato all'uscita (anche in caso di errore);
#   2. bootstrap UNA TANTUM, da superuser, dei due ruoli che richiedono
#      privilegi che un proprietario di migrazione non superuser non puo'
#      concedersi da solo (CREATEROLE non basta per BYPASSRLS):
#      `gravya_migrator` (NOLOGIN NOSUPERUSER CREATEROLE) e
#      `gravya_e1_so_owner` (NOLOGIN BYPASSRLS, proprietario della funzione
#      SECURITY DEFINER cross-tenant);
#   3. `alembic upgrade head` con MIGRATION_ROLE=gravya_migrator: tutte le
#      istruzioni di migrazione girano con i privilegi di gravya_migrator,
#      non del superuser che si e' autenticato;
#   4. verifica funzionale vera (scripts/_verify_nonsuperuser.py): un ruolo
#      non superuser autenticato a password scrive con TracingHelper, poi si
#      controlla che il trigger anti-modifica e la funzione cross-tenant
#      funzionino sullo schema cosi' creato.
#
# Variabili d'ambiente (connessione da SUPERUSER per bootstrap/migrazioni):
#   PGHOST (default: localhost), PGPORT (default: 5432), PGUSER (default:
#   utente corrente della shell). SCRATCH_DB: nome del database usa e getta
#   (default: gravya_e1_ci_nonsuper).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PGHOST_="${PGHOST:-localhost}"
PGPORT_="${PGPORT:-5432}"
PGUSER_="${PGUSER:-$(whoami)}"
SCRATCH_DB="${SCRATCH_DB:-gravya_e1_ci_nonsuper}"

SUPERUSER_ADMIN_DSN="postgresql://${PGUSER_}@${PGHOST_}:${PGPORT_}/postgres"
SCRATCH_DSN="postgresql://${PGUSER_}@${PGHOST_}:${PGPORT_}/${SCRATCH_DB}"

cleanup() {
    psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${SCRATCH_DB};" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== [1/4] database usa e getta: ${SCRATCH_DB} =="
psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${SCRATCH_DB};"
psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${SCRATCH_DB};"

echo "== [2/4] bootstrap una tantum (da superuser) di gravya_migrator/gravya_e1_so_owner =="
psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_migrator') THEN
        CREATE ROLE gravya_migrator NOLOGIN NOSUPERUSER NOBYPASSRLS CREATEROLE;
    END IF;
END
$$;

GRANT gravya_migrator TO CURRENT_USER;

DO $$
BEGIN
    -- BYPASSRLS richiede un superuser per essere creato: vincolo di
    -- PostgreSQL, non aggirabile da CREATEROLE (vedi migrations/versions/0005).
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_e1_so_owner') THEN
        CREATE ROLE gravya_e1_so_owner NOLOGIN BYPASSRLS;
    END IF;
END
$$;

GRANT gravya_e1_so_owner TO gravya_migrator;
GRANT CREATE ON SCHEMA public TO gravya_migrator;
GRANT USAGE, CREATE ON SCHEMA public TO gravya_e1_so_owner;

-- Solo se gravya_writer esiste gia' nel cluster (ambiente condiviso tra
-- database): su un cluster davvero nuovo lo crea gravya_migrator stesso
-- (migrations/versions/0002) e la membership con ADMIN OPTION e' automatica.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_writer') THEN
        EXECUTE 'GRANT gravya_writer TO gravya_migrator WITH ADMIN OPTION';
    END IF;
END
$$;
SQL

echo "== [3/4] alembic upgrade head con MIGRATION_ROLE=gravya_migrator (non superuser) =="
(
    cd "${ROOT_DIR}"
    DATABASE_URL="postgresql+psycopg://${PGUSER_}@${PGHOST_}:${PGPORT_}/${SCRATCH_DB}" \
    MIGRATION_ROLE=gravya_migrator \
        alembic upgrade head
)

echo "== [4/4] verifica funzionale con un ruolo non superuser autenticato a password =="
GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN="${SCRATCH_DSN}" \
GRAVYA_E1_CI_NONSUPER_HOST="${PGHOST_}" \
GRAVYA_E1_CI_NONSUPER_PORT="${PGPORT_}" \
GRAVYA_E1_CI_NONSUPER_DB="${SCRATCH_DB}" \
    python3 "${ROOT_DIR}/scripts/_verify_nonsuperuser.py"

echo "== OK: migrazioni e applicazione funzionano con proprietario di schema non superuser =="
