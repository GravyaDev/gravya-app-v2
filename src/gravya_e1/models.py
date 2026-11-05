"""Contratti condivisi come modelli Pydantic (E16)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

RootKind = Literal["agent", "workflow", "eval"]
SegmentKind = Literal["llm", "tool", "agent", "retrieval", "decision", "eval_case"]


class TraceStart(BaseModel):
    trace_id: UUID
    tenant_id: UUID
    run_id: str
    execution_ticket_id: str | None = None
    root_kind: RootKind
    started_at: datetime
    workflow_id: str | None = None
    workflow_version: str | None = None
    retention_class: str | None = None


class TraceEnd(BaseModel):
    trace_id: UUID
    tenant_id: UUID
    ended_at: datetime
    status: str


class SegmentStart(BaseModel):
    segment_id: UUID
    trace_id: UUID
    tenant_id: UUID
    kind: SegmentKind
    name: str | None = None
    parent_segment_id: UUID | None = None
    started_at: datetime
    attributes: dict[str, Any] = {}
    # Argomenti grezzi da cui l'helper calcola l'HMAC (giro 2, B6): mai un
    # hash gia' calcolato dal chiamante. Solo per kind 'tool'/'decision'.
    # repr=False (CA minore, giro 3): non deve comparire in repr/log del
    # modello; l'helper azzera il riferimento dopo il calcolo dell'HMAC.
    raw_arguments: bytes | None = Field(default=None, repr=False)


class SegmentEnd(BaseModel):
    segment_id: UUID
    tenant_id: UUID
    ended_at: datetime
    status: str
    attributes: dict[str, Any] = {}
    raw_arguments: bytes | None = Field(default=None, repr=False)
