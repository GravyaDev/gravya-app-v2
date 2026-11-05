"""Helper di scrittura `start_segment`/`end_segment` (E1 §5, passo 3 del §9).

- Whitelist di chiavi e valori per `kind` (criterio 4).
- Fail-open solo per le tracce: una scrittura non riuscita non interrompe
  l'esecuzione, la perdita e' contata e segnalata (criterio 5).
- HMAC degli argomenti con chiave per tenant; senza chiave valida l'attributo
  non e' scritto (criterio 15).
- `redaction_version` 1 (whitelist di E1 §4.2, vincolo 6).

Eventi e segnali con nomi puntati (F2/DX-07): `trace.*`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from gravya_e1 import whitelist as wl
from gravya_e1.config.env import is_production
from gravya_e1.config.variables import VariableRegistry
from gravya_e1.hashing import HashUnavailableError, compute_args_hmac
from gravya_e1.keys import TenantKeyProvider
from gravya_e1.models import SegmentEnd, SegmentStart, TraceEnd, TraceStart
from gravya_e1.signals import SignalSink


class AttributeRejectedError(ValueError):
    """Sollevato fuori produzione quando un attributo non e' conforme (§6)."""


class WriteFailedSilently(RuntimeError):
    """Interno: la scrittura e' fallita ma e' stata assorbita (fail-open)."""


@dataclass
class ValidationResult:
    clean: dict[str, Any]
    discarded: list[wl.DiscardReason]


def _validate_decision_outcome(attrs: dict[str, Any]) -> tuple[bool, str | None]:
    kind_value = attrs.get("gravya.decision.kind")
    outcome = attrs.get("gravya.decision.outcome")
    if kind_value == "policy":
        if outcome in wl.POLICY_OUTCOMES:
            return True, None
        return False, "valore fuori dal vocabolario di gravya.decision.outcome per policy"
    if kind_value == "hitl":
        if outcome in wl.HITL_OUTCOMES:
            return True, None
        return False, "valore fuori dal vocabolario di gravya.decision.outcome per hitl"
    return False, "gravya.decision.outcome richiede gravya.decision.kind valido (policy o hitl)"


def validate_attributes(kind: str, attributes: dict[str, Any], max_value_bytes: int) -> ValidationResult:
    if kind not in wl.ATTRIBUTE_WHITELIST:
        raise ValueError(f"kind non riconosciuto: {kind!r}")
    spec = wl.ATTRIBUTE_WHITELIST[kind]
    clean: dict[str, Any] = {}
    discarded: list[wl.DiscardReason] = []
    for key, value in attributes.items():
        if key not in spec:
            discarded.append(wl.DiscardReason(kind=kind, key=key, reason="attributo fuori whitelist"))
            continue
        if kind == "decision" and key == "gravya.decision.outcome":
            ok, reason = _validate_decision_outcome(attributes)
            if not ok:
                discarded.append(wl.DiscardReason(kind=kind, key=key, reason=reason or "non valido"))
                continue
            clean[key] = value
            continue
        validator = spec[key]
        if not validator(value, max_value_bytes):
            discarded.append(wl.DiscardReason(kind=kind, key=key, reason="valore fuori formato o vocabolario"))
            continue
        clean[key] = value
    return ValidationResult(clean=clean, discarded=discarded)


class TracingHelper:
    """`start_segment`/`end_segment`, fail-open solo per le tracce (§6)."""

    def __init__(
        self,
        variables: VariableRegistry,
        signal_sink: SignalSink,
        key_provider: TenantKeyProvider,
        *,
        production_override: bool | None = None,
    ) -> None:
        self._variables = variables
        self._signals = signal_sink
        self._keys = key_provider
        self._production_override = production_override
        # Avvio dell'helper (criterio 17): legge subito le variabili "da
        # definire" di E1; con la guardia di produzione attiva, un valore
        # mancante blocca l'avvio (solleva VariableUnavailableError).
        self._write_buffer_size = self._variables.get("e1.write_buffer_size").value
        self._max_value_bytes = self._variables.get("e1.attributes.max_value_bytes").value
        self.loss_count = 0

    def _is_production(self) -> bool:
        if self._production_override is not None:
            return self._production_override
        return is_production()

    # -- HMAC ---------------------------------------------------------
    def hash_tool_args(self, tenant_id: str, argument_bytes: bytes) -> tuple[str, str] | None:
        """HMAC-SHA-256 degli argomenti con la chiave del tenant.

        Ritorna None (e invia un segnale) se il tenant non ha una chiave
        valida: l'attributo hash non viene scritto (criterio 15).
        """
        try:
            digest, key_ref = compute_args_hmac(self._keys, tenant_id, argument_bytes)
            return digest, key_ref
        except HashUnavailableError:
            self._signals.emit(
                "trace.args_hash_unavailable",
                tenant_id=str(tenant_id),
                reason="nessuna chiave HMAC valida per il tenant",
            )
            return None

    # -- validazione + scrittura ---------------------------------------
    def _apply_whitelist(self, kind: str, attributes: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        result = validate_attributes(kind, attributes, self._max_value_bytes)
        if result.discarded:
            if not self._is_production():
                details = "; ".join(f"{d.key}: {d.reason}" for d in result.discarded)
                raise AttributeRejectedError(f"attributi non conformi per kind={kind}: {details}")
            for d in result.discarded:
                self._signals.emit(
                    "trace.segment_attribute_discarded",
                    kind=d.kind,
                    key=d.key,
                    reason=d.reason,
                    count=1,
                    tenant_id=str(tenant_id),
                )
        return result.clean

    def _fail_open(self, exc: Exception, table: str, tenant_id: str) -> None:
        """Scrittura non riuscita: conta la perdita e segnala, senza propagare (§6, criterio 5)."""
        self.loss_count += 1
        self._signals.emit(
            "trace.write_failed",
            table=table,
            reason=str(exc.__class__.__name__),
            count=1,
            tenant_id=tenant_id,
        )

    def _execute(self, conn, tenant_id: str, table: str, sql: str, params: tuple) -> None:
        from gravya_e1.db import writer_transaction

        try:
            with writer_transaction(conn, tenant_id) as tconn:
                with tconn.cursor() as cur:
                    cur.execute(sql, params)
        except Exception as exc:  # noqa: BLE001 - fail-open deliberato, solo per le tracce
            self._fail_open(exc, table, tenant_id)

    def start_trace(self, conn, trace: TraceStart) -> None:
        tenant_id = str(trace.tenant_id)
        self._execute(
            conn,
            tenant_id,
            "gravya_traces",
            """
            INSERT INTO gravya_traces
                (trace_id, tenant_id, run_id, execution_ticket_id, root_kind,
                 started_at, workflow_id, workflow_version, retention_class)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(trace.trace_id),
                tenant_id,
                trace.run_id,
                trace.execution_ticket_id,
                trace.root_kind,
                trace.started_at,
                trace.workflow_id,
                trace.workflow_version,
                trace.retention_class,
            ),
        )

    def end_trace(self, conn, trace_end: TraceEnd) -> None:
        tenant_id = str(trace_end.tenant_id)
        self._execute(
            conn,
            tenant_id,
            "gravya_traces",
            "UPDATE gravya_traces SET ended_at = %s, status = %s WHERE trace_id = %s",
            (trace_end.ended_at, trace_end.status, str(trace_end.trace_id)),
        )

    def start_segment(self, conn, segment: SegmentStart) -> None:
        tenant_id = str(segment.tenant_id)
        clean_attrs = self._apply_whitelist(segment.kind, segment.attributes, tenant_id)
        self._execute(
            conn,
            tenant_id,
            "gravya_trace_segments",
            """
            INSERT INTO gravya_trace_segments
                (segment_id, trace_id, parent_segment_id, tenant_id, kind, name,
                 started_at, attributes, redaction_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                str(segment.segment_id),
                str(segment.trace_id),
                str(segment.parent_segment_id) if segment.parent_segment_id else None,
                tenant_id,
                segment.kind,
                segment.name,
                segment.started_at,
                json.dumps(clean_attrs),
                wl.REDACTION_VERSION,
            ),
        )

    def end_segment(self, conn, segment_end: SegmentEnd, kind: str) -> None:
        tenant_id = str(segment_end.tenant_id)
        clean_attrs = self._apply_whitelist(kind, segment_end.attributes, tenant_id)
        self._execute(
            conn,
            tenant_id,
            "gravya_trace_segments",
            """
            UPDATE gravya_trace_segments
            SET ended_at = %s, status = %s,
                attributes = attributes || %s::jsonb
            WHERE segment_id = %s
            """,
            (
                segment_end.ended_at,
                segment_end.status,
                json.dumps(clean_attrs),
                str(segment_end.segment_id),
            ),
        )
