"""Giro 3: controllo cross-tenant senza parametro tenant, proprietario dedicato, segnali solo INSERT.

- **G8a/b/c.** La funzione `gravya_e1_trace_owned_by_other_tenant` non
  accetta piu' un tenant arbitrario (oracolo cross-tenant, G8b): legge il
  tenant dal GUC di sessione corrente (`app.tenant_id`), impostato da
  `writer_transaction`. Il proprietario non e' piu' chi esegue la
  migrazione (che in produzione sara' un ruolo non superuser, G8c): un
  ruolo dedicato `gravya_e1_so_owner`, `NOLOGIN BYPASSRLS`, creato da questa
  migrazione. **Creare un ruolo con `BYPASSRLS` richiede un superuser**
  (vincolo di PostgreSQL, non aggirabile da `CREATEROLE`): su un database
  nuovo, prima di eseguire le migrazioni con un proprietario non superuser
  (`gravya_migrator`), un superuser deve pre-creare `gravya_e1_so_owner` e
  concedergli la membership a `gravya_migrator` (vedi report, sezione "Giro
  3", requisito di deploy). Le istruzioni qui sono idempotenti (`IF NOT
  EXISTS`) apposta per funzionare sia alla prima esecuzione (da superuser)
  sia alla verifica con un proprietario non superuser (quando i ruoli
  esistono gia').
- `start_trace` controlla anche lui il `trace_id` (G8a): prima mancava.
- **G15/G15b.** Il writer perde `SELECT` sulla tabella provvisoria dei
  segnali (decisione dell'utente: "solo inserimento"). La policy di RLS
  per l'INSERT diventa permissiva (`WITH CHECK (true)`): la riservatezza
  ora si ottiene con il privilegio (nessun `SELECT`), non con il confronto
  del tenant in scrittura, che obbligherebbe chi scrive un segnale a usare
  sempre lo stesso contesto di tenant della sessione corrente (non vero in
  generale: un segnale puo' riguardare un tenant diverso da quello appena
  in corso).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05
"""
from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ruolo dedicato alle migrazioni, non superuser (criterio di fine 2):
    # idempotente, con CREATEROLE per poter creare `gravya_writer` da solo.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_migrator') THEN
                CREATE ROLE gravya_migrator NOLOGIN NOSUPERUSER NOBYPASSRLS CREATEROLE;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT gravya_migrator TO %I', current_user);
        EXCEPTION WHEN OTHERS THEN
            -- Giro 4 (G3-02): visibile, non inghiottito. Fallisce qui quando
            -- current_user e' gia' superuser (non puo' concedersi un ruolo a
            -- se stesso in questo modo) o quando manca l'ADMIN OPTION: in
            -- entrambi i casi non e' un errore fatale per questa migrazione.
            RAISE WARNING 'impossibile concedere gravya_migrator al chiamante qui (%)', SQLERRM;
        END
        $$;
        """
    )

    # Proprietario dedicato della funzione SECURITY DEFINER: NOLOGIN,
    # BYPASSRLS (richiede un superuser per essere creato, vedi docstring).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_e1_so_owner') THEN
                CREATE ROLE gravya_e1_so_owner NOLOGIN BYPASSRLS;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT gravya_e1_so_owner TO %I', current_user);
        EXCEPTION WHEN OTHERS THEN
            -- Giro 4 (G3-02): visibile, non inghiottito (stesso motivo sopra).
            -- La migrazione 0006 revoca questa appartenenza temporanea dopo
            -- l'ALTER OWNER sotto; se la concessione qui e' fallita perche'
            -- current_user e' gia' il proprietario finale o gia' superuser,
            -- non c'e' nulla da revocare e va bene cosi'.
            RAISE WARNING 'impossibile concedere gravya_e1_so_owner al chiamante qui (%)', SQLERRM;
        END
        $$;
        """
    )

    op.execute("DROP FUNCTION IF EXISTS gravya_e1_trace_owned_by_other_tenant(uuid, uuid);")
    op.execute(
        """
        CREATE FUNCTION gravya_e1_trace_owned_by_other_tenant(p_trace_id uuid)
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = pg_catalog, public, pg_temp
        AS $$
            SELECT EXISTS (
                SELECT 1 FROM gravya_traces
                WHERE trace_id = p_trace_id
                  AND tenant_id <> current_setting('app.tenant_id', true)::uuid
            );
        $$;
        """
    )
    op.execute("ALTER FUNCTION gravya_e1_trace_owned_by_other_tenant(uuid) OWNER TO gravya_e1_so_owner;")
    # BYPASSRLS salta solo la RLS: resta comunque necessario il privilegio
    # di base sulla tabella per il proprietario della funzione.
    op.execute("GRANT SELECT ON gravya_traces TO gravya_e1_so_owner;")
    op.execute("REVOKE ALL ON FUNCTION gravya_e1_trace_owned_by_other_tenant(uuid) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION gravya_e1_trace_owned_by_other_tenant(uuid) TO gravya_writer;")

    # G15/G15b: il writer perde SELECT sulla tabella provvisoria dei segnali.
    op.execute("REVOKE SELECT ON gravya_signals_min_audit FROM gravya_writer;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gravya_signals_min_audit;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON gravya_signals_min_audit
        FOR ALL
        USING (true)
        WITH CHECK (true);
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gravya_signals_min_audit;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON gravya_signals_min_audit
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )
    op.execute("GRANT SELECT ON gravya_signals_min_audit TO gravya_writer;")

    op.execute("DROP FUNCTION IF EXISTS gravya_e1_trace_owned_by_other_tenant(uuid);")
    op.execute(
        """
        CREATE FUNCTION gravya_e1_trace_owned_by_other_tenant(p_trace_id uuid, p_tenant_id uuid)
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT EXISTS (
                SELECT 1 FROM gravya_traces
                WHERE trace_id = p_trace_id AND tenant_id <> p_tenant_id
            );
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION gravya_e1_trace_owned_by_other_tenant(uuid, uuid) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION gravya_e1_trace_owned_by_other_tenant(uuid, uuid) TO gravya_writer;")
    op.execute("REVOKE SELECT ON gravya_traces FROM gravya_e1_so_owner;")
    # Nota: `gravya_migrator` e `gravya_e1_so_owner` non vengono eliminati
    # (ruoli a livello di cluster, condivisi: stessa motivazione di
    # `gravya_writer` nella migrazione 0002).
