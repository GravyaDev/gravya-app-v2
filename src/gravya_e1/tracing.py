"""Helper di scrittura `start_segment`/`end_segment` (E1 §5, passo 3 del §9).

Giro 2 (dopo BLOCCA di code-reviewer e compliance-auditor): riscrittura per i
bloccanti B1-B7. Vedi `docs/revisioni/impl-e1/report-implementer.md`,
sezione "Giro 2", per il collegamento rilievo -> modifica -> test.

Architettura (B5). L'helper scrive sempre con una connessione propria, mai
quella del chiamante: la connessione passata alle funzioni pubbliche serve
solo a leggere i parametri di connessione (host/porta/utente/database) per
aprire, la prima volta, la connessione dedicata dell'helper (riusata poi per
tutte le scritture successive, protetta da un lock perche' psycopg non e'
pensato per l'uso concorrente della stessa connessione).

Ogni scrittura e' soggetta a: (1) un limite di concorrenza
(`e1.write_buffer_size` tentativi in corso contemporaneamente: oltre, e'
"buffer pieno", perdita immediata senza nemmeno provare la scrittura); (2)
un timeout di istruzione (`e1.write_statement_timeout_ms`, letto
dall'istantanea E5 come `e1.write_buffer_size`: DX-22, giro 3, nessun valore
fisso nel codice) che assicura che un DB lento o bloccato non faccia
attendere il chiamante indefinitamente. In entrambi i casi: perdita contata
e segnalata, il chiamante non aspetta oltre il timeout e non vede mai
l'eccezione (criterio 5/6, E1 §5/§6).

Fail-open vero (B2). Nessuna eccezione, ne' della scrittura ne' dell'invio
di un segnale, esce mai da queste funzioni pubbliche verso il chiamante.
Se il sink dei segnali stesso fallisce, c'e' un ripiego di log strutturato
locale (`signals.log_fallback`), senza contenuti, e la perdita resta in
sospeso per essere ri-segnalata alla prima occasione successiva in cui il
sink torna disponibile.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

import psycopg

from gravya_e1 import whitelist as wl
from gravya_e1.config.env import is_declared, is_production
from gravya_e1.config.variables import VariableRegistry
from gravya_e1.db import writer_transaction
from gravya_e1.hashing import HashUnavailableError, compute_args_hmac
from gravya_e1.keys import TenantKeyProvider
from gravya_e1.models import SegmentEnd, SegmentStart, TraceEnd, TraceStart
from gravya_e1.signals import SignalSink, log_fallback

logger = logging.getLogger("gravya_e1.tracing")

TRACE_REQUIRED_FIELDS = frozenset({"run_id"})


class AttributeRejectedError(ValueError):
    """Sollevato fuori produzione quando un campo/attributo non e' conforme (§6)."""


@dataclass
class _ValidationResult:
    clean: dict[str, Any]
    discarded: list[wl.DiscardReason]


# --- parametri delle scritture -----------------------------------------


@dataclass
class _InsertTraceJob:
    tenant_id: str
    trace_id: str
    run_id: str
    execution_ticket_id: str | None
    root_kind: str
    started_at: Any
    workflow_id: str | None
    workflow_version: str | None
    retention_class: str | None


@dataclass
class _UpdateTraceJob:
    tenant_id: str
    trace_id: str
    ended_at: Any
    status: str | None


@dataclass
class _InsertSegmentJob:
    tenant_id: str
    segment_id: str
    trace_id: str
    parent_segment_id: str | None
    kind: str
    name: str | None
    started_at: Any
    attributes: dict = field(default_factory=dict)


@dataclass
class _UpdateSegmentJob:
    tenant_id: str
    segment_id: str
    ended_at: Any
    status: str | None
    attributes: dict
    expected_kind: str


def _validate_decision_outcome(attrs: dict[str, Any]) -> tuple[bool, str | None]:
    kind_value = attrs.get("gravya.decision.kind")
    outcome = attrs.get("gravya.decision.outcome")
    try:
        if kind_value == "policy":
            if outcome in wl.POLICY_OUTCOMES:
                return True, None
            return False, "valore fuori dal vocabolario di gravya.decision.outcome per policy"
        if kind_value == "hitl":
            if outcome in wl.HITL_OUTCOMES:
                return True, None
            return False, "valore fuori dal vocabolario di gravya.decision.outcome per hitl"
    except TypeError:
        return False, "valore non confrontabile per gravya.decision.outcome"
    return False, "gravya.decision.outcome richiede gravya.decision.kind valido (policy o hitl)"


def _validate_prompt_hash_context(attrs: dict[str, Any]) -> tuple[bool, str | None]:
    if "gravya.prompt.key" in attrs and "gravya.prompt.version" in attrs:
        return True, None
    return False, "gravya.prompt.hash richiede gravya.prompt.key e gravya.prompt.version (B6)"


def validate_attributes(kind: str, attributes: dict[str, Any], max_value_bytes: int) -> _ValidationResult:
    if kind not in wl.ATTRIBUTE_WHITELIST:
        raise ValueError(f"kind non riconosciuto: {kind!r}")
    if not isinstance(attributes, dict):
        return _ValidationResult(clean={}, discarded=[wl.DiscardReason(kind=kind, key="attributes", reason="non e' un oggetto")])
    spec = wl.ATTRIBUTE_WHITELIST[kind]
    clean: dict[str, Any] = {}
    discarded: list[wl.DiscardReason] = []

    # Coppia legata (decision): se gravya.decision.outcome e' presente e non
    # valido per il gravya.decision.kind dichiarato, scarta anche
    # gravya.decision.kind (un kind senza un esito valido e coerente non e'
    # un record di decisione completo e affidabile, giro 2).
    skip_keys: set[str] = set()
    if kind == "decision" and "gravya.decision.outcome" in attributes:
        try:
            outcome_ok, outcome_reason = _validate_decision_outcome(attributes)
        except Exception:  # noqa: BLE001 - difensivo (B3)
            outcome_ok, outcome_reason = False, "errore nella validazione del contesto"
        if not outcome_ok:
            discarded.append(
                wl.DiscardReason(kind=kind, key="gravya.decision.outcome", reason=outcome_reason or "non valido")
            )
            skip_keys.add("gravya.decision.outcome")
            if "gravya.decision.kind" in attributes:
                discarded.append(
                    wl.DiscardReason(
                        kind=kind,
                        key="gravya.decision.kind",
                        reason="scartato insieme a gravya.decision.outcome non valido",
                    )
                )
                skip_keys.add("gravya.decision.kind")

    for key, value in attributes.items():
        if key in skip_keys:
            continue
        if not isinstance(key, str):
            discarded.append(wl.DiscardReason(kind=kind, key="", reason="chiave non testuale"))
            continue
        if key in wl.INTERNAL_ONLY_ATTRIBUTE_KEYS:
            discarded.append(
                wl.DiscardReason(kind=kind, key=key, reason="riservato: calcolato dall'helper (B6)")
            )
            continue
        if key not in spec:
            discarded.append(wl.DiscardReason(kind=kind, key=key, reason="attributo fuori whitelist"))
            continue
        if kind == "decision" and key == "gravya.decision.outcome":
            # gia' validato sopra (coppia legata): qui arriva solo se valido.
            clean[key] = value
            continue
        if kind == "llm" and key == "gravya.prompt.hash":
            try:
                ok, reason = _validate_prompt_hash_context(attributes)
            except Exception:  # noqa: BLE001
                ok, reason = False, "errore nella validazione del contesto"
            if not ok:
                discarded.append(wl.DiscardReason(kind=kind, key=key, reason=reason))
                continue
        validator = spec[key]
        try:
            is_valid = validator(value, max_value_bytes)
        except Exception:  # noqa: BLE001 - difensivo (B3): mai un'eccezione dal validatore
            is_valid = False
        if not is_valid:
            discarded.append(wl.DiscardReason(kind=kind, key=key, reason="valore fuori formato o vocabolario"))
            continue
        clean[key] = value
    return _ValidationResult(clean=clean, discarded=discarded)


def validate_fields(spec: dict[str, Any], fields_values: dict[str, Any], max_value_bytes: int) -> _ValidationResult:
    clean: dict[str, Any] = {}
    discarded: list[wl.DiscardReason] = []
    for key, value in fields_values.items():
        if value is None:
            continue
        validator = spec.get(key)
        if validator is None:
            discarded.append(wl.DiscardReason(kind="_field", key=key, reason="campo fuori whitelist"))
            continue
        try:
            ok = validator(value, max_value_bytes)
        except Exception:  # noqa: BLE001 - difensivo (B3)
            ok = False
        if not ok:
            discarded.append(wl.DiscardReason(kind="_field", key=key, reason="valore fuori formato o vocabolario"))
            continue
        clean[key] = value
    return _ValidationResult(clean=clean, discarded=discarded)


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
        self._write_statement_timeout_ms = self._variables.get("e1.write_statement_timeout_ms").value

        self._loss_lock = threading.Lock()
        self.loss_count = 0
        self._pending_signal_loss = 0

        # "Buffer" come limite di concorrenza (B5): oltre questo numero di
        # scritture gia' in corso, una nuova richiesta e' "buffer pieno" e
        # non prova nemmeno a scrivere (perdita immediata).
        self._capacity = threading.BoundedSemaphore(max(1, self._write_buffer_size))

        self._conn_lock = threading.Lock()
        self._own_conn: psycopg.Connection | None = None
        self._conn_params: dict | None = None

        if self._production_override is None and not is_declared():
            self._safe_emit(
                "e5.environment_undeclared",
                reason="API_ENV non impostata: ambiente trattato come sviluppo",
            )

    # -- ambiente -------------------------------------------------------
    def _is_production(self) -> bool:
        if self._production_override is not None:
            return self._production_override
        return is_production()

    # -- segnali, mai propagati (B2) --------------------------------------
    def _safe_emit(self, event: str, *, tenant_id: str | None = None, **fields: Any) -> None:
        try:
            self._signals.emit(event, tenant_id=tenant_id, **fields)
        except Exception:  # noqa: BLE001 - il fail-open non dipende dal sink (B2/R-08)
            with self._loss_lock:
                self._pending_signal_loss += 1
            try:
                log_fallback(event, tenant_id=tenant_id, **fields)
            except Exception:  # noqa: BLE001 - ripiego di ultima istanza
                pass
            return
        self._flush_pending_loss(tenant_id)

    def _flush_pending_loss(self, tenant_id: str | None) -> None:
        with self._loss_lock:
            pending = self._pending_signal_loss
            self._pending_signal_loss = 0
        if not pending:
            return
        try:
            self._signals.emit("trace.pending_loss_flushed", tenant_id=tenant_id, count=pending)
        except Exception:  # noqa: BLE001
            with self._loss_lock:
                self._pending_signal_loss += pending

    def _signal_discard(self, discard: wl.DiscardReason, tenant_id: str) -> None:
        safe_key, length = wl.safe_signal_key_name(discard.key)
        fields: dict[str, Any] = {"kind": discard.kind, "reason": discard.reason, "count": 1, "key_length": length}
        if safe_key is not None:
            fields["key"] = safe_key
        self._safe_emit("trace.segment_attribute_discarded", tenant_id=tenant_id, **fields)

    def _record_loss(self, exc: Exception, table: str, tenant_id: str | None) -> None:
        with self._loss_lock:
            self.loss_count += 1
        self._safe_emit("trace.write_failed", tenant_id=tenant_id, table=table, reason=exc.__class__.__name__, count=1)

    # -- HMAC -------------------------------------------------------------
    def hash_tool_args(self, tenant_id: str, argument_bytes: bytes) -> tuple[str, str] | None:
        """HMAC-SHA-256 degli argomenti con la chiave del tenant (criterio 15).

        Ritorna None (e invia un segnale) se il tenant non ha una chiave
        valida: l'attributo hash non viene scritto.
        """
        try:
            digest, key_ref = compute_args_hmac(self._keys, tenant_id, argument_bytes)
        except HashUnavailableError:
            self._safe_emit(
                "trace.args_hash_unavailable", tenant_id=str(tenant_id), reason="nessuna chiave HMAC valida per il tenant"
            )
            return None
        if not wl.key_ref_format(key_ref, self._max_value_bytes):
            self._safe_emit(
                "trace.args_hash_unavailable", tenant_id=str(tenant_id), reason="key_ref di formato non valido"
            )
            return None
        return digest, key_ref

    def _inject_args_hash(self, kind: str, tenant_id: str, raw_arguments: bytes | None, clean_attrs: dict[str, Any]) -> None:
        """Calcola e inietta l'HMAC degli argomenti (B6): mai accettato dal chiamante."""
        if raw_arguments is None or kind not in ("tool", "decision"):
            return
        result = self.hash_tool_args(tenant_id, raw_arguments)
        if result is None:
            return
        digest, key_ref = result
        field_name = "gravya.tool.args_hash" if kind == "tool" else "gravya.decision.args_hash"
        clean_attrs[field_name] = digest
        clean_attrs["gravya.hash.key_ref"] = key_ref

    # -- validazione campi/attributi ---------------------------------------
    def _apply_whitelist(self, kind: str, attributes: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        result = validate_attributes(kind, attributes, self._max_value_bytes)
        self._enforce_or_signal(result, tenant_id, "attributi")
        return result.clean

    def _apply_field_whitelist(self, spec: dict[str, Any], values: dict[str, Any], tenant_id: str) -> _ValidationResult:
        result = validate_fields(spec, values, self._max_value_bytes)
        self._enforce_or_signal(result, tenant_id, "campi")
        return result

    def _enforce_or_signal(self, result: _ValidationResult, tenant_id: str, what: str) -> None:
        if not result.discarded:
            return
        if not self._is_production():
            details = "; ".join(f"{d.key}: {d.reason}" for d in result.discarded)
            raise AttributeRejectedError(f"{what} non conformi: {details}")
        for d in result.discarded:
            self._signal_discard(d, tenant_id)

    # -- connessione propria (B5) -------------------------------------------
    def _set_conn_template(self, conn: psycopg.Connection) -> None:
        if self._conn_params is None:
            with self._conn_lock:
                if self._conn_params is None:
                    self._conn_params = conn.info.get_parameters()

    def _get_own_connection(self) -> psycopg.Connection:
        if self._own_conn is None or self._own_conn.closed:
            self._own_conn = psycopg.connect(**self._conn_params)
        return self._own_conn

    def _attempt_write(self, conn_template: psycopg.Connection, table: str, tenant_id: str, fn: Callable[[psycopg.Connection], None]) -> None:
        """Esegue `fn` sulla connessione propria dell'helper, mai quella del chiamante.

        Limite di concorrenza (`e1.write_buffer_size`) e timeout di
        istruzione (`e1.write_statement_timeout_ms`): un buffer pieno o un
        DB lento sono una perdita contata e segnalata, mai un'attesa
        indefinita per il chiamante (B5, criterio 5/6).
        """
        try:
            self._set_conn_template(conn_template)
        except Exception as exc:  # noqa: BLE001 - connessione del chiamante gia' rotta: fail-open comunque
            self._record_loss(exc, table, tenant_id)
            return
        if not self._capacity.acquire(blocking=False):
            self._record_loss(RuntimeError("buffer pieno (e1.write_buffer_size)"), table, tenant_id)
            return
        try:
            with self._conn_lock:
                try:
                    own_conn = self._get_own_connection()
                    fn(own_conn)
                except Exception as exc:  # noqa: BLE001 - fail-open deliberato (B2/B5)
                    try:
                        if self._own_conn is not None:
                            self._own_conn.rollback()
                    except Exception:  # noqa: BLE001
                        pass
                    self._record_loss(exc, table, tenant_id)
        finally:
            self._capacity.release()

    # -- scritture effettive (sulla connessione propria) ----------------
    def _write_insert_trace(self, conn: psycopg.Connection, job: _InsertTraceJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gravya_traces
                    (trace_id, tenant_id, run_id, execution_ticket_id, root_kind,
                     started_at, workflow_id, workflow_version, retention_class)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job.trace_id,
                    job.tenant_id,
                    job.run_id,
                    job.execution_ticket_id,
                    job.root_kind,
                    job.started_at,
                    job.workflow_id,
                    job.workflow_version,
                    job.retention_class,
                ),
            )

    def _write_update_trace(self, conn: psycopg.Connection, job: _UpdateTraceJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            cur.execute("SELECT ended_at FROM gravya_traces WHERE trace_id = %s FOR UPDATE", (job.trace_id,))
            row = cur.fetchone()
            if row is None:
                self._safe_emit(
                    "trace.update_target_not_found", tenant_id=job.tenant_id, table="gravya_traces", reason="non trovata", count=1
                )
                return
            if row[0] is not None:
                self._safe_emit(
                    "trace.trace_already_closed", tenant_id=job.tenant_id, table="gravya_traces", reason="gia' chiusa", count=1
                )
                return
            cur.execute(
                "UPDATE gravya_traces SET ended_at = %s, status = COALESCE(%s, status) WHERE trace_id = %s AND ended_at IS NULL",
                (job.ended_at, job.status, job.trace_id),
            )

    def _write_insert_segment(self, conn: psycopg.Connection, job: _InsertSegmentJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            # Il writer non puo' leggere le tracce di un altro tenant (RLS):
            # una funzione SECURITY DEFINER verifica, senza esporre i dati
            # altrui, se il trace_id e' gia' di un tenant diverso (CA R-04,
            # CR R11). Un trace_id che non esiste affatto per nessuno non e'
            # un conflitto rilevabile qui (nessuna riga da confrontare).
            cur.execute(
                "SELECT gravya_e1_trace_owned_by_other_tenant(%s, %s)", (job.trace_id, job.tenant_id)
            )
            if cur.fetchone()[0]:
                self._safe_emit(
                    "trace.segment_trace_tenant_mismatch",
                    tenant_id=job.tenant_id,
                    table="gravya_trace_segments",
                    reason="trace_id appartiene a un altro tenant",
                    count=1,
                )
                return
            cur.execute(
                """
                INSERT INTO gravya_trace_segments
                    (segment_id, trace_id, parent_segment_id, tenant_id, kind, name,
                     started_at, attributes, redaction_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    job.segment_id,
                    job.trace_id,
                    job.parent_segment_id,
                    job.tenant_id,
                    job.kind,
                    job.name,
                    job.started_at,
                    json.dumps(job.attributes),
                    wl.REDACTION_VERSION,
                ),
            )

    def _write_update_segment(self, conn: psycopg.Connection, job: _UpdateSegmentJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            cur.execute(
                "SELECT kind, ended_at FROM gravya_trace_segments WHERE segment_id = %s FOR UPDATE", (job.segment_id,)
            )
            row = cur.fetchone()
            if row is None:
                self._safe_emit(
                    "trace.update_target_not_found",
                    tenant_id=job.tenant_id,
                    table="gravya_trace_segments",
                    reason="non trovato",
                    count=1,
                )
                return
            actual_kind, ended_at = row
            if ended_at is not None:
                self._safe_emit(
                    "trace.segment_already_closed",
                    tenant_id=job.tenant_id,
                    table="gravya_trace_segments",
                    reason="gia' chiuso",
                    count=1,
                )
                return
            attrs = job.attributes
            if actual_kind != job.expected_kind:
                self._safe_emit(
                    "trace.segment_kind_mismatch",
                    tenant_id=job.tenant_id,
                    table="gravya_trace_segments",
                    reason="kind dichiarato diverso da quello memorizzato",
                    count=1,
                )
                attrs = {}
            cur.execute(
                """
                UPDATE gravya_trace_segments
                SET ended_at = %s, status = COALESCE(%s, status),
                    attributes = attributes || %s::jsonb
                WHERE segment_id = %s AND ended_at IS NULL
                """,
                (job.ended_at, job.status, json.dumps(attrs), job.segment_id),
            )

    # -- API pubblica ---------------------------------------------------
    def start_trace(self, conn: psycopg.Connection, trace: TraceStart) -> None:
        tenant_id = str(trace.tenant_id)
        field_values = {
            "run_id": trace.run_id,
            "execution_ticket_id": trace.execution_ticket_id,
            "workflow_id": trace.workflow_id,
            "workflow_version": trace.workflow_version,
            "retention_class": trace.retention_class,
        }
        result = self._apply_field_whitelist(wl.TRACE_FIELD_WHITELIST, field_values, tenant_id)
        if any(d.key in TRACE_REQUIRED_FIELDS for d in result.discarded):
            # run_id e' obbligatorio (NOT NULL): senza un valore conforme la
            # traccia non si scrive (nessun valore fuori formato nella riga).
            return
        clean = result.clean
        job = _InsertTraceJob(
            tenant_id=tenant_id,
            trace_id=str(trace.trace_id),
            run_id=clean.get("run_id"),
            execution_ticket_id=clean.get("execution_ticket_id"),
            root_kind=trace.root_kind,  # Literal tipizzato da Pydantic, gia' vincolato
            started_at=trace.started_at,
            workflow_id=clean.get("workflow_id"),
            workflow_version=clean.get("workflow_version"),
            retention_class=clean.get("retention_class"),
        )
        self._attempt_write(conn, "gravya_traces", tenant_id, lambda c: self._write_insert_trace(c, job))

    def end_trace(self, conn: psycopg.Connection, trace_end: TraceEnd) -> None:
        tenant_id = str(trace_end.tenant_id)
        result = self._apply_field_whitelist(wl.TRACE_FIELD_WHITELIST, {"status": trace_end.status}, tenant_id)
        job = _UpdateTraceJob(
            tenant_id=tenant_id,
            trace_id=str(trace_end.trace_id),
            ended_at=trace_end.ended_at,
            status=result.clean.get("status"),
        )
        self._attempt_write(conn, "gravya_traces", tenant_id, lambda c: self._write_update_trace(c, job))

    def start_segment(self, conn: psycopg.Connection, segment: SegmentStart) -> None:
        tenant_id = str(segment.tenant_id)
        clean_attrs = self._apply_whitelist(segment.kind, segment.attributes, tenant_id)
        field_result = self._apply_field_whitelist(wl.SEGMENT_FIELD_WHITELIST, {"name": segment.name}, tenant_id)
        self._inject_args_hash(segment.kind, tenant_id, segment.raw_arguments, clean_attrs)
        job = _InsertSegmentJob(
            tenant_id=tenant_id,
            segment_id=str(segment.segment_id),
            trace_id=str(segment.trace_id),
            parent_segment_id=str(segment.parent_segment_id) if segment.parent_segment_id else None,
            kind=segment.kind,
            name=field_result.clean.get("name"),
            started_at=segment.started_at,
            attributes=clean_attrs,
        )
        self._attempt_write(conn, "gravya_trace_segments", tenant_id, lambda c: self._write_insert_segment(c, job))

    def end_segment(self, conn: psycopg.Connection, segment_end: SegmentEnd, kind: str) -> None:
        tenant_id = str(segment_end.tenant_id)
        clean_attrs = self._apply_whitelist(kind, segment_end.attributes, tenant_id)
        field_result = self._apply_field_whitelist(wl.SEGMENT_FIELD_WHITELIST, {"status": segment_end.status}, tenant_id)
        self._inject_args_hash(kind, tenant_id, segment_end.raw_arguments, clean_attrs)
        job = _UpdateSegmentJob(
            tenant_id=tenant_id,
            segment_id=str(segment_end.segment_id),
            ended_at=segment_end.ended_at,
            status=field_result.clean.get("status"),
            attributes=clean_attrs,
            expected_kind=kind,
        )
        self._attempt_write(conn, "gravya_trace_segments", tenant_id, lambda c: self._write_update_segment(c, job))
