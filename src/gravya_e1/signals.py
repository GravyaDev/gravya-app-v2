"""Destinazione dei segnali verso A5 (interfaccia, vincolo 4 del task implementer E1).

La tabella di audit minima dell'ondata 1 (A3 Appendice B, B2 Appendice B) non e'
definita: i segnali passano da questa interfaccia, con un'implementazione in
memoria per i test e un'implementazione PostgreSQL che scrive in una tabella
marcata esplicitamente "provvisoria" nella migrazione
(migrations/versions/0003_signals_provisional.py). La struttura reale della
tabella di audit minima resta da definire con A5 (vedi report,
decisioni_mancanti).

Giro 2 (B7): il sink accetta solo un insieme chiuso di campi per il payload
(mai contenuto arbitrario del chiamante: solo quelli che il codice di E1
dichiara esplicitamente qui) ed espone un ripiego di log strutturato, senza
contenuti, da usare quando il sink stesso non e' scrivibile (B2/R-08: il
fail-open non deve mai dipendere dalla disponibilita' del sink).
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

# Insieme chiuso dei campi di payload che il codice di E1 puo' inviare in un
# segnale (B7): qualunque altra chiave fornita a `emit` viene scartata prima
# di raggiungere il sink. Nessuno di questi campi porta mai il valore di un
# attributo scartato (DA-E1-02).
ALLOWED_SIGNAL_FIELDS = frozenset(
    {
        "name",
        "reason",
        "table",
        "key",
        "key_length",
        "count",
        "kind",
        "path",
    }
)

_fallback_logger = logging.getLogger("gravya_e1.signals_fallback")


def log_fallback(event: str, *, tenant_id: str | None = None, **payload: Any) -> None:
    """Ripiego quando il sink dei segnali non e' scrivibile (B2/R-08).

    Giro 3 (G17/G17b): il nome dell'evento, il tenant e i campi chiusi sono
    nel **messaggio** del log (non solo in `extra`, che va perso con la
    formattazione di default), e nessun campo passa come `extra` (alcuni
    nomi di campo, come `name`, sono riservati da `logging.LogRecord` e
    farebbero fallire la chiamata con un `KeyError` inghiottito dal ripiego
    di ultima istanza: nessun log veniva scritto).
    """
    safe_payload = _filter_payload(payload)
    parts = [f"event={event}", f"tenant_id={tenant_id}"]
    parts.extend(f"{key}={value}" for key, value in safe_payload.items())
    _fallback_logger.warning("segnale_non_scrivibile " + " ".join(parts))


def _filter_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in ALLOWED_SIGNAL_FIELDS}


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
        self.signals.append(Signal(kind=event, payload=_filter_payload(payload), tenant_id=tenant_id))

    def kinds(self) -> list[str]:
        return [s.kind for s in self.signals]


class PostgresSignalSink:
    """Implementazione che scrive nella tabella provvisoria `gravya_signals_min_audit`.

    Tabella marcata "provvisoria" nella migrazione: non e' la tabella di audit
    minima definitiva di A3/B2 (non ancora definita). Non scrive mai il valore
    scartato (vincolo 4): solo `kind`, chiavi del payload dichiarate esplicite
    dal chiamante (mai il valore di un attributo scartato) e conteggi, filtrati
    dall'insieme chiuso `ALLOWED_SIGNAL_FIELDS` (B7).
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def emit(self, event: str, *, tenant_id: str | None = None, **payload: Any) -> None:
        safe_payload = _filter_payload(payload)
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gravya_signals_min_audit (id, kind, tenant_id, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), event, tenant_id, json.dumps(safe_payload)),
            )
        self._conn.commit()
