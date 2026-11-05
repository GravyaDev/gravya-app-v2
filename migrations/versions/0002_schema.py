"""Schema E1: gravya_traces / gravya_trace_segments, RLS con WITH CHECK, ruolo writer senza bypass.

Passo 2 del §9 di docs/E1-tracing-distribuito.md (v1.6). Criteri 3 e 8
(parte di partizione). Nomi delle colonne secondo F2/DX-07 (`tenant_id`, non
`company_id`: vedi report, divergenze).

Le tabelle sono partizionate per tempo (RANGE su `started_at`); questa
migrazione crea solo le tabelle padre partizionate, i vincoli e le policy di
RLS. Le singole partizioni si creano a runtime con l'intervallo
`e1.partition_interval_months` letto dall'istantanea E5
(`src/gravya_e1/partitions.py`): l'intervallo non è un valore fisso di
migrazione (DX-22).

Il ruolo `gravya_writer` non ha `BYPASSRLS` (DA-E1-10 (a)): il tenant si
imposta per transazione con `SELECT set_config('app.tenant_id', ..., true)`
e la sessione passa a quel ruolo con `SET LOCAL ROLE gravya_writer`
(vincolo 7 del task implementer: nei test non si gira come superuser).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05
"""
from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gravya_writer') THEN
                CREATE ROLE gravya_writer NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS LOGIN;
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO gravya_writer;")
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT gravya_writer TO %I', current_user);
        END
        $$;
        """
    )

    op.execute(
        """
        CREATE TABLE gravya_traces (
            trace_id uuid NOT NULL,
            tenant_id uuid NOT NULL,
            run_id text NOT NULL,
            execution_ticket_id text,
            root_kind text NOT NULL CHECK (root_kind IN ('agent', 'workflow', 'eval')),
            started_at timestamptz NOT NULL,
            ended_at timestamptz,
            status text,
            workflow_id text,
            workflow_version text,
            retention_class text,
            PRIMARY KEY (trace_id, started_at)
        ) PARTITION BY RANGE (started_at);
        """
    )

    op.execute(
        """
        CREATE TABLE gravya_trace_segments (
            segment_id uuid NOT NULL,
            trace_id uuid NOT NULL,
            parent_segment_id uuid,
            tenant_id uuid NOT NULL,
            kind text NOT NULL CHECK (kind IN ('llm', 'tool', 'agent', 'retrieval', 'decision', 'eval_case')),
            name text,
            started_at timestamptz NOT NULL,
            ended_at timestamptz,
            status text,
            attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
            redaction_version integer NOT NULL,
            PRIMARY KEY (segment_id, started_at)
        ) PARTITION BY RANGE (started_at);
        """
    )

    op.execute("CREATE INDEX ix_gravya_traces_tenant ON gravya_traces (tenant_id);")
    op.execute("CREATE INDEX ix_gravya_trace_segments_tenant ON gravya_trace_segments (tenant_id);")
    op.execute("CREATE INDEX ix_gravya_trace_segments_trace ON gravya_trace_segments (trace_id);")

    for table in ("gravya_traces", "gravya_trace_segments"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            FOR ALL
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
            """
        )
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON {table} TO gravya_writer;")


def downgrade() -> None:
    # Nota: i ruoli PostgreSQL sono a livello di cluster, condivisi tra tutti
    # i database. Questa migrazione non elimina `gravya_writer` ne' revoca la
    # sua membership (concessa con GRANT ... TO <chi esegue la migrazione>):
    # farlo romperebbe altri database dello stesso cluster che usano lo
    # stesso ruolo (per esempio durante i test). Si annullano solo gli
    # oggetti di questo database: tabelle, policy (cadono con le tabelle) e
    # il privilegio sullo schema locale.
    op.execute("DROP TABLE IF EXISTS gravya_trace_segments;")
    op.execute("DROP TABLE IF EXISTS gravya_traces;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM gravya_writer;")
