"""Tabella PROVVISORIA per i segnali verso A5 (vincolo 4 del task implementer E1).

La struttura della tabella di audit minima dell'ondata 1 non e' definita
(A3 Appendice B, B2 Appendice B). Questa tabella non e' quella definitiva:
serve solo a dare un'implementazione reale a `PostgresSignalSink`
(src/gravya_e1/signals.py) e ai test dei criteri 4 e 5, che richiedono di
cercare un valore scartato nella "tabella di audit" e non trovarlo. La
struttura reale va definita con A5 (vedi report, decisioni_mancanti).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-05
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- TABELLA PROVVISORIA: non e' la tabella di audit minima definitiva di A3/B2.
        CREATE TABLE gravya_signals_min_audit (
            id uuid PRIMARY KEY,
            occurred_at timestamptz NOT NULL DEFAULT now(),
            kind text NOT NULL,
            tenant_id uuid,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb
        );
        """
    )
    op.execute("COMMENT ON TABLE gravya_signals_min_audit IS 'PROVVISORIA: in attesa della tabella di audit minima definita da A5/A3/B2';")
    op.execute("GRANT SELECT, INSERT ON gravya_signals_min_audit TO gravya_writer;")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gravya_signals_min_audit;")
