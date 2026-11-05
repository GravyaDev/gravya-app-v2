"""Destinazione dei segnali verso A5 (interfaccia, vincolo 4 del task implementer E1).

La tabella di audit minima dell'ondata 1 (A3 Appendice B, B2 Appendice B) non e'
definita: i segnali passano da questa interfaccia, con un'implementazione in
memoria per i test e un'implementazione PostgreSQL che scrive in una tabella
marcata esplicitamente "provvisoria" nella migrazione
(migrations/versions/0003_signals_provisional.py). La struttura reale della
tabella di audit minima resta da definire con A5 (vedi report,
decisioni_mancanti).
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(frozen=True)
class Signal:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SignalSink(Protocol):
    def emit(self, event: str, *, tenant_id: str | None = None, **payload: Any) -> None:
        ...


class InMemorySignalSink:
    """Implementazione di test: tiene i segnali in una lista in memoria."""

    def __init__(self) -> None:
        self.signals: list[Signal] = []

    def emit(self, event: str, *, tenant_id: str | None = None, **payload: Any) -> None:
        self.signals.append(Signal(kind=event, payload=dict(payload), tenant_id=tenant_id))

    def kinds(self) -> list[str]:
        return [s.kind for s in self.signals]


class PostgresSignalSink:
    """Implementazione che scrive nella tabella provvisoria `gravya_signals_min_audit`.

    Tabella marcata "provvisoria" nella migrazione: non e' la tabella di audit
    minima definitiva di A3/B2 (non ancora definita). Non scrive mai il valore
    scartato (vincolo 4): solo `kind`, chiavi del payload dichiarate esplicite
    dal chiamante (mai il valore di un attributo scartato) e conteggi.
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def emit(self, event: str, *, tenant_id: str | None = None, **payload: Any) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gravya_signals_min_audit (id, kind, tenant_id, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), event, tenant_id, json.dumps(payload)),
            )
        self._conn.commit()
