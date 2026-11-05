#!/usr/bin/env bash
# Criterio di fine 2 (E1 v1.6): le migrazioni e l'applicazione devono
# funzionare quando lo schema e' di proprieta' di un ruolo non superuser.
#
# Procedura (stessa verifica manuale fatta nel giro 3, qui come script
# riusabile/versionato, invocato anche da CI; giro 4: due passi in piu',
# [5] e [6], per G3-02 e G3-03):
#   1. database usa e getta, eliminato all'uscita (anche in caso di errore);
#   2. bootstrap UNA TANTUM, da superuser, dei due ruoli che richiedono
#      privilegi che un proprietario di migrazione non superuser non puo'
#      concedersi da solo (CREATEROLE non basta per BYPASSRLS):
#      `gravya_migrator` (NOLOGIN NOSUPERUSER CREATEROLE) e
#      `gravya_e1_so_owner` (NOLOGIN BYPASSRLS, proprietario della funzione
#      SECURITY DEFINER cross-tenant). Qui si concede anche, temporaneamente,
#      `CREATE` sullo schema `public` a `gravya_e1_so_owner`: **serve
#      davvero** (PostgreSQL lo richiede al nuovo proprietario per `ALTER
#      FUNCTION ... OWNER TO`, verificato con `psql` diretto, vedi report
#      "Giro 5" - il giro 4 diceva il contrario, corretto qui); revocato al
#      passo 5, insieme all'appartenenza.
#   3. `alembic upgrade head` con MIGRATION_ROLE=gravya_migrator: tutte le
#      istruzioni di migrazione girano con i privilegi di gravya_migrator,
#      non del superuser che si e' autenticato;
#   4. verifica funzionale vera (scripts/_verify_nonsuperuser.py): un ruolo
#      non superuser autenticato a password scrive con TracingHelper, poi si
#      controlla che il trigger anti-modifica e la funzione cross-tenant
#      funzionino sullo schema cosi' creato;
#   5. (giro 4, G3-02) la sessione superuser revoca subito l'appartenenza e i
#      privilegi temporanei concessi al passo 2 (la stessa sessione che li ha
#      concessi puo' sempre revocarli): dopo questo punto `gravya_migrator`
#      non puo' piu' fare `SET ROLE gravya_e1_so_owner`, verificato qui con
#      un ruolo di prova che NON e' superuser (una sessione superuser
#      potrebbe sempre fare `SET ROLE` verso qualunque ruolo, a prescindere
#      dall'appartenenza: non proverebbe nulla);
#   6. (giro 4, G3-03) un ruolo non superuser membro di `gravya_writer`
#      scrive un segnale con `PostgresSignalSink` (INSERT riuscito) e non
#      puo' leggerlo (SELECT negato).
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
    psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 -c "DROP OWNED BY gravya_e1_ci_nonsuper_writer;" >/dev/null 2>&1 || true
    psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP ROLE IF EXISTS gravya_e1_ci_nonsuper_writer;" >/dev/null 2>&1 || true
    psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${SCRATCH_DB};" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "== [1/6] database usa e getta: ${SCRATCH_DB} =="
psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS ${SCRATCH_DB};"
psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${SCRATCH_DB};"

echo "== [2/6] bootstrap una tantum (da superuser) di gravya_migrator/gravya_e1_so_owner =="
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

-- Concessione TEMPORANEA (revocata al passo 5, G3-02): serve solo perche'
-- la migrazione 0005 fa `ALTER FUNCTION ... OWNER TO gravya_e1_so_owner`
-- sotto il ruolo di migrazione, che deve esserne membro per la durata
-- dell'operazione. **Verificato**: PostgreSQL richiede che il NUOVO
-- proprietario di una funzione abbia CREATE sullo schema che la contiene
-- (`ALTER FUNCTION ... OWNER TO` fallisce con "permission denied for schema
-- public" altrimenti, provato direttamente con `psql`): la proposta del
-- compliance-auditor di toglierlo ("non serve alla funzione") non regge,
-- vedi report "Giro 4" per la prova. Resta quindi un privilegio di schema
-- per `gravya_e1_so_owner`, ma SOLO per la durata della migrazione: la
-- riga sotto lo revoca appena finita (passo 5), insieme all'appartenenza.
GRANT gravya_e1_so_owner TO gravya_migrator;
GRANT CREATE ON SCHEMA public TO gravya_migrator;
GRANT CREATE ON SCHEMA public TO gravya_e1_so_owner;

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

echo "== [3/6] alembic upgrade head con MIGRATION_ROLE=gravya_migrator (non superuser) =="
(
    cd "${ROOT_DIR}"
    DATABASE_URL="postgresql+psycopg://${PGUSER_}@${PGHOST_}:${PGPORT_}/${SCRATCH_DB}" \
    MIGRATION_ROLE=gravya_migrator \
        alembic upgrade head
)

echo "== [4/6] verifica funzionale con un ruolo non superuser autenticato a password =="
GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN="${SCRATCH_DSN}" \
GRAVYA_E1_CI_NONSUPER_HOST="${PGHOST_}" \
GRAVYA_E1_CI_NONSUPER_PORT="${PGPORT_}" \
GRAVYA_E1_CI_NONSUPER_DB="${SCRATCH_DB}" \
    python3 "${ROOT_DIR}/scripts/_verify_nonsuperuser.py"

echo "== [5/6] revoca l'appartenenza e i privilegi temporanei (G3-02) =="
psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 -c "REVOKE gravya_e1_so_owner FROM gravya_migrator;"
psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 -c "REVOKE CREATE ON SCHEMA public FROM gravya_migrator;"
psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 -c "REVOKE CREATE ON SCHEMA public FROM gravya_e1_so_owner;"

# Verifica vera: una sessione SUPERUSER puo' sempre fare SET ROLE verso
# qualunque ruolo, a prescindere dall'appartenenza (il controllo di
# PostgreSQL per SET ROLE guarda `session_user`, non `current_user`): con
# PGUSER superuser questo controllo passerebbe anche senza la revoca sopra,
# quindi non proverebbe nulla. Un ruolo di prova LOGIN non superuser, membro
# SOLO di `gravya_migrator` (come un vero account di deploy non superuser),
# autenticato a password: deve riuscire a `SET ROLE gravya_migrator` ma non
# a `SET ROLE gravya_e1_so_owner` da li'.
TESTER_ROLE="gravya_e1_ci_nonsuper_migrator_tester"
# Solo caratteri alfanumerici (esadecimale): una password con `/`, `+`, `@` o
# `:` romperebbe l'URL di connessione sotto (DSN `postgresql://utente:password@...`).
TESTER_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${TESTER_ROLE}') THEN
        CREATE ROLE ${TESTER_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
\$\$;
ALTER ROLE ${TESTER_ROLE} PASSWORD '${TESTER_PASSWORD}';
GRANT gravya_migrator TO ${TESTER_ROLE};
GRANT CONNECT ON DATABASE ${SCRATCH_DB} TO ${TESTER_ROLE};
SQL

TESTER_DSN="postgresql://${TESTER_ROLE}:${TESTER_PASSWORD}@${PGHOST_}:${PGPORT_}/${SCRATCH_DB}"
NOT_MEMBER="$(psql "${TESTER_DSN}" -At -c "SET ROLE gravya_migrator; SET ROLE gravya_e1_so_owner;" 2>&1 || true)"

psql "${SCRATCH_DSN}" -v ON_ERROR_STOP=1 -c "DROP OWNED BY ${TESTER_ROLE};" >/dev/null
psql "${SUPERUSER_ADMIN_DSN}" -v ON_ERROR_STOP=1 -c "DROP ROLE IF EXISTS ${TESTER_ROLE};" >/dev/null

if [[ "${NOT_MEMBER}" != *"permission denied"* ]] && [[ "${NOT_MEMBER}" != *"not a member"* ]]; then
    echo "ERRORE: un ruolo non superuser con sola appartenenza a gravya_migrator puo' ancora fare SET ROLE gravya_e1_so_owner dopo la revoca:" >&2
    echo "${NOT_MEMBER}" >&2
    exit 1
fi
echo "   OK: un ruolo non superuser con sola appartenenza a gravya_migrator non puo' fare SET ROLE gravya_e1_so_owner"

echo "== [6/6] segnali da ruolo non superuser (G3-03): INSERT riuscito, SELECT negato =="
GRAVYA_E1_CI_NONSUPER_SUPERUSER_DSN="${SCRATCH_DSN}" \
GRAVYA_E1_CI_NONSUPER_HOST="${PGHOST_}" \
GRAVYA_E1_CI_NONSUPER_PORT="${PGPORT_}" \
GRAVYA_E1_CI_NONSUPER_DB="${SCRATCH_DB}" \
    python3 "${ROOT_DIR}/scripts/_verify_signals_nonsuperuser.py"

echo "== OK: migrazioni e applicazione funzionano con proprietario di schema non superuser =="
