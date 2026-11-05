"""Giro 2: correzioni dopo BLOCCA di code-reviewer e compliance-auditor.

- B5/CA R-10 (ruolo writer): `gravya_writer` diventa `NOLOGIN`. Non si puo'
  piu' autenticare direttamente con quel ruolo (niente login/password): resta
  utilizzabile solo via `SET ROLE` da un ruolo con la membership concessa
  esplicitamente (in produzione sara' il ruolo applicativo; nei test/sviluppo
  locale e' il ruolo che esegue le migrazioni, vedi report).
- CA R-05/CR R7 (nessuna modifica dopo la chiusura): trigger che blocca un
  UPDATE quando la riga esistente ha gia' `ended_at` non nullo; privilegi di
  colonna per il writer (niente UPDATE su `tenant_id`, `trace_id`,
  `segment_id`, `kind`, `started_at`, `run_id`, `root_kind`).
- CA R-06 (tabella provvisoria dei segnali): RLS abilitata e forzata anche
  su `gravya_signals_min_audit` (il writer resta multi-tenant: con RLS vede
  solo i segnali del proprio tenant di sessione, mai quelli di un altro).
- CA R-04/CR R11 (WITH CHECK non tautologico, segmento su trace_id di un
  altro tenant): RLS impedisce al writer di leggere le tracce di un altro
  tenant, quindi non si puo' controllare la proprieta' di un `trace_id`
  dentro la sessione del tenant stesso. Una funzione `SECURITY DEFINER`
  (bypassa RLS solo per questo controllo, mai per leggere i dati) verifica
  se il `trace_id` e' gia' di un tenant diverso da quello della scrittura:
  in tal caso il segmento e' rifiutato. Se il `trace_id` non esiste affatto
  (per nessun tenant) non c'e' conflitto da segnalare qui: resta un caso di
  integrita' applicativa fuori da questo controllo (nessuna FK possibile
  tra tabelle partizionate su colonne diverse dalla chiave di partizione).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05
"""
from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER ROLE gravya_writer NOLOGIN;")

    # Privilegi di colonna: via il blanket UPDATE, solo le colonne che si
    # possono davvero modificare dopo l'inserimento (CA R-05).
    op.execute("REVOKE UPDATE ON gravya_traces FROM gravya_writer;")
    op.execute("GRANT UPDATE (ended_at, status) ON gravya_traces TO gravya_writer;")
    op.execute("REVOKE UPDATE ON gravya_trace_segments FROM gravya_writer;")
    op.execute("GRANT UPDATE (ended_at, status, attributes) ON gravya_trace_segments TO gravya_writer;")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION gravya_e1_block_update_after_close() RETURNS trigger AS $$
        BEGIN
            IF OLD.ended_at IS NOT NULL THEN
                RAISE EXCEPTION 'E1: riga gia'' chiusa (ended_at non nullo), modifica rifiutata'
                    USING ERRCODE = 'integrity_constraint_violation';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in ("gravya_traces", "gravya_trace_segments"):
        op.execute(f"DROP TRIGGER IF EXISTS no_update_after_close ON {table};")
        op.execute(
            f"""
            CREATE TRIGGER no_update_after_close
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION gravya_e1_block_update_after_close();
            """
        )

    op.execute("ALTER TABLE gravya_signals_min_audit ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE gravya_signals_min_audit FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON gravya_signals_min_audit
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION gravya_e1_trace_owned_by_other_tenant(p_trace_id uuid, p_tenant_id uuid)
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


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS gravya_e1_trace_owned_by_other_tenant(uuid, uuid);")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gravya_signals_min_audit;")
    op.execute("ALTER TABLE gravya_signals_min_audit NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE gravya_signals_min_audit DISABLE ROW LEVEL SECURITY;")

    for table in ("gravya_traces", "gravya_trace_segments"):
        op.execute(f"DROP TRIGGER IF EXISTS no_update_after_close ON {table};")
    op.execute("DROP FUNCTION IF EXISTS gravya_e1_block_update_after_close();")

    op.execute("REVOKE UPDATE (ended_at, status) ON gravya_traces FROM gravya_writer;")
    op.execute("GRANT UPDATE ON gravya_traces TO gravya_writer;")
    op.execute("REVOKE UPDATE (ended_at, status, attributes) ON gravya_trace_segments FROM gravya_writer;")
    op.execute("GRANT UPDATE ON gravya_trace_segments TO gravya_writer;")

    op.execute("ALTER ROLE gravya_writer LOGIN;")
