"""Migrazione vuota (passo 0, verifica: si applica e si annulla su un PostgreSQL di test).

Revision ID: 0001
Revises:
Create Date: 2026-11-05
"""
from __future__ import annotations

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
