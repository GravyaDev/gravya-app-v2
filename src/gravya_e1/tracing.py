"""Helper di scrittura `start_segment`/`end_segment` (E1 §5, passo 3 del §9).

Giro 3 (dopo il secondo BLOCCA di code-reviewer e compliance-auditor):
riscrittura della scrittura come coda asincrona vera, con un thread di
sfondo e una connessione propria dell'helper creata alla costruzione (mai
derivata dalla connessione del chiamante). Vedi
`docs/revisioni/impl-e1/report-implementer.md`, sezione "Giro 3", per il
collegamento rilievo -> modifica -> test.

Architettura (G4a/b, G5, G7, G14a, G19).
- `start_trace`/`end_trace`/`start_segment`/`end_segment` validano i campi
  e gli attributi **sincronamente** (cosi' in sviluppo un valore non
  conforme fa fallire subito la chiamata, come richiesto da §6), poi mettono
  in coda un "job" con un inserimento **non bloccante**
  (`queue.Queue(maxsize=e1.write_buffer_size)`, numero di segmenti) e
  tornano subito: la riga non e' necessariamente gia' scritta quando la
  chiamata ritorna (si usa `flush()` per aspettare che lo sia). Coda piena:
  perdita contata e segnalata, nessuna attesa.
- Il parametro `conn` delle funzioni pubbliche non e' piu' usato per nulla
  (ne' per scrivere ne' per leggere parametri di connessione): resta nella
  firma solo per compatibilita' con i chiamanti esistenti. I parametri di
  connessione dell'helper (DSN/parametri espliciti, o le variabili
  d'ambiente standard di libpq quando non specificati) si ricevono **alla
  creazione** (`conninfo`), mai da una connessione del chiamante: una
  connessione del chiamante gia' chiusa non ha piu' alcun effetto (G14a).
- Un thread di sfondo (avviato alla creazione) consuma la coda con una
  connessione propria, riconnettendosi dopo un errore. Ogni connessione ha
  un `connect_timeout` (`e1.write_connect_timeout_ms`) e keepalive TCP
  (`e1.write_tcp_keepalives_*`); ogni scrittura ha uno `statement_timeout`
  (`e1.write_statement_timeout_ms`). `flush(timeout)` aspetta che la coda si
  svuoti; `close()` ferma il thread e chiude la connessione.

Fail-open vero (B2, giro 2). Nessuna eccezione, ne' della scrittura ne'
dell'invio di un segnale, esce mai da queste funzioni pubbliche verso il
chiamante. Se il sink dei segnali stesso fallisce, c'e' un ripiego di log
strutturato locale (`signals.log_fallback`), senza contenuti.

Contesto del tenant (G16, CA R-04). `TracingHelper` puo' ricevere un
`tenant_context` alla creazione: se dato, ogni modello con `tenant_id`
diverso e' rifiutato (scartato con segnale in produzione, errore fuori
produzione) e il GUC si imposta dal contesto, non dal modello. Se NON dato
(default, `None`), per compatibilita' con i chiamanti che gestiscono piu'
tenant con lo stesso helper (passo 4+, dove non esiste ancora un'identita'
applicativa prima di A6) il tenant resta quello del modello, comportamento
preesistente: dichiarato qui, non nascosto (vedi report, sezione "Giro 3").
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
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

_SENTINEL = object()


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
    table: str = "gravya_traces"


@dataclass
class _UpdateTraceJob:
    tenant_id: str
    trace_id: str
    ended_at: Any
    status: str | None
    table: str = "gravya_traces"


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
    table: str = "gravya_trace_segments"


@dataclass
class _UpdateSegmentJob:
    tenant_id: str
    segment_id: str
    ended_at: Any
    status: str | None
    attributes: dict
    expected_kind: str
    table: str = "gravya_trace_segments"


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
    if not isinstance(attributes, dict):
        attributes = {}

    if kind not in wl.ATTRIBUTE_WHITELIST:
        # G6: un kind sconosciuto non deve sollevare un'eccezione non gestita
        # (prima: ValueError propagato fino al chiamante anche in
        # produzione). Si scartano tutti gli attributi con lo stesso motivo,
        # passando dallo stesso percorso di scarto/segnale o errore in
        # sviluppo degli altri casi.
        discarded = [wl.DiscardReason(kind=kind, key=key, reason="kind sconosciuto") for key in attributes]
        if not discarded:
            discarded = [wl.DiscardReason(kind=kind, key="", reason="kind sconosciuto")]
        return _ValidationResult(clean={}, discarded=discarded)

    spec = wl.ATTRIBUTE_WHITELIST[kind]
    clean: dict[str, Any] = {}
    discarded: list[wl.DiscardReason] = []

    # Coppia legata (decision, giro 2): se gravya.decision.outcome e'
    # presente e non valido per il gravya.decision.kind dichiarato, scarta
    # anche gravya.decision.kind (un kind senza un esito valido e coerente
    # non e' un record di decisione completo e affidabile).
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
        tenant_context: str | None = None,
        conninfo: str | None = None,
    ) -> None:
        self._variables = variables
        self._signals = signal_sink
        self._keys = key_provider
        self._production_override = production_override
        self._tenant_context = str(tenant_context) if tenant_context is not None else None
        self._conninfo = conninfo

        # Avvio dell'helper (criterio 17): legge subito le variabili "da
        # definire" di E1; con la guardia di produzione attiva, un valore
        # mancante blocca l'avvio (solleva VariableUnavailableError).
        self._write_buffer_size = self._variables.get("e1.write_buffer_size").value
        self._max_value_bytes = self._variables.get("e1.attributes.max_value_bytes").value
        self._write_statement_timeout_ms = self._variables.get("e1.write_statement_timeout_ms").value
        self._write_connect_timeout_ms = self._variables.get("e1.write_connect_timeout_ms").value
        self._keepalives_idle_s = self._variables.get("e1.write_tcp_keepalives_idle_s").value
        self._keepalives_interval_s = self._variables.get("e1.write_tcp_keepalives_interval_s").value
        self._keepalives_count = self._variables.get("e1.write_tcp_keepalives_count").value

        self._loss_lock = threading.Lock()
        self.loss_count = 0
        self._pending_signal_loss = 0

        self._queue: "queue.Queue" = queue.Queue(maxsize=self._write_buffer_size)
        self._pending = 0
        self._pending_cv = threading.Condition()

        self._conn_lock = threading.Lock()
        self._own_conn: psycopg.Connection | None = None
        self._closed = False

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        if self._production_override is None and not is_declared():
            self._safe_emit(
                "e5.environment_undeclared",
                reason="API_ENV non impostata: ambiente trattato come sviluppo",
            )

    # -- ambiente -------------------------------------------------------
    def _is_production(self) -> bool:
        # G9: l'override puo' solo irrigidire la guardia, mai spegnerla.
        if self._production_override:
            return True
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

    # -- contesto del tenant (G16) ------------------------------------------
    def _resolve_tenant(self, model_tenant_id: Any) -> str | None:
        """Ritorna il tenant autoritativo, o None se e' in conflitto col contesto."""
        model_tenant = str(model_tenant_id)
        if self._tenant_context is None:
            return model_tenant
        if model_tenant != self._tenant_context:
            return None
        return self._tenant_context

    def _enforce_tenant_context(self, model_tenant_id: Any) -> str | None:
        """Come `_resolve_tenant`, ma gestisce scarto/segnale o errore in sviluppo.

        Ritorna il tenant da usare, o None se la scrittura va abbandonata
        (gia' scartata e segnalata in produzione).
        """
        tenant_id = self._resolve_tenant(model_tenant_id)
        if tenant_id is not None:
            return tenant_id
        if not self._is_production():
            raise AttributeRejectedError(
                f"tenant_id del modello ({model_tenant_id}) diverso dal contesto ({self._tenant_context})"
            )
        self._safe_emit(
            "trace.tenant_context_mismatch",
            tenant_id=self._tenant_context,
            reason="tenant_id del modello diverso dal contesto",
            count=1,
        )
        return None

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

    def _inject_args_hash(self, kind: str, tenant_id: str, segment: Any, clean_attrs: dict[str, Any]) -> None:
        """Calcola e inietta l'HMAC degli argomenti (B6): mai accettato dal chiamante.

        Azzera `segment.raw_arguments` dopo l'uso (CA minore, giro 3): il
        riferimento ai byte in chiaro non deve sopravvivere oltre il calcolo.
        """
        raw_arguments = getattr(segment, "raw_arguments", None)
        if raw_arguments is None or kind not in ("tool", "decision"):
            return
        try:
            result = self.hash_tool_args(tenant_id, raw_arguments)
            if result is None:
                return
            digest, key_ref = result
            field_name = "gravya.tool.args_hash" if kind == "tool" else "gravya.decision.args_hash"
            clean_attrs[field_name] = digest
            clean_attrs["gravya.hash.key_ref"] = key_ref
        finally:
            try:
                segment.raw_arguments = None
            except Exception:  # noqa: BLE001 - modello non mutabile: non e' critico
                pass

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

    # -- connessione propria, coda e thread di sfondo (G4/G5/G7/G14a/G19) ---
    def _get_own_connection(self) -> psycopg.Connection:
        """Chiamato solo dal thread di sfondo (consumatore unico della coda)."""
        if self._own_conn is None or self._own_conn.closed:
            connect_timeout_s = max(1, round(self._write_connect_timeout_ms / 1000))
            kwargs = dict(
                connect_timeout=connect_timeout_s,
                keepalives=1,
                keepalives_idle=self._keepalives_idle_s,
                keepalives_interval=self._keepalives_interval_s,
                keepalives_count=self._keepalives_count,
            )
            with self._conn_lock:
                if self._conninfo:
                    self._own_conn = psycopg.connect(self._conninfo, **kwargs)
                else:
                    # Nessun parametro esplicito: le variabili d'ambiente
                    # standard di libpq (PGHOST, PGPORT, PGUSER, PGDATABASE,
                    # PGPASSWORD) forniscono la destinazione e la credenziale
                    # (mai una connessione del chiamante, G7/G14a).
                    self._own_conn = psycopg.connect(**kwargs)
        return self._own_conn

    def _invalidate_connection(self) -> None:
        with self._conn_lock:
            if self._own_conn is not None:
                try:
                    self._own_conn.close()
                except Exception:  # noqa: BLE001
                    pass
                self._own_conn = None

    def _worker_loop(self) -> None:
        handlers = {
            _InsertTraceJob: self._handle_insert_trace,
            _UpdateTraceJob: self._handle_update_trace,
            _InsertSegmentJob: self._handle_insert_segment,
            _UpdateSegmentJob: self._handle_update_segment,
        }
        while True:
            job = self._queue.get()
            if job is _SENTINEL:
                self._queue.task_done()
                break
            try:
                conn = self._get_own_connection()
                handlers[type(job)](conn, job)
                self._flush_pending_loss(job.tenant_id)
            except Exception as exc:  # noqa: BLE001 - fail-open deliberato (B2), solo per le tracce
                try:
                    if self._own_conn is not None:
                        self._own_conn.rollback()
                except Exception:  # noqa: BLE001
                    pass
                self._invalidate_connection()
                self._record_loss(exc, job.table, job.tenant_id)
            finally:
                with self._pending_cv:
                    self._pending -= 1
                    self._pending_cv.notify_all()
                self._queue.task_done()

    def _enqueue(self, job: Any) -> None:
        if self._closed:
            self._record_loss(RuntimeError("helper chiuso"), job.table, job.tenant_id)
            return
        try:
            self._queue.put_nowait(job)
        except queue.Full:
            self._record_loss(RuntimeError("buffer pieno (e1.write_buffer_size)"), job.table, job.tenant_id)
            return
        with self._pending_cv:
            self._pending += 1

    def flush(self, timeout: float | None = None) -> bool:
        """Aspetta che la coda si svuoti (tutte le scritture accodate finora completate).

        Ritorna False se il timeout scade prima che la coda sia vuota.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._pending_cv:
            while self._pending > 0:
                if deadline is None:
                    self._pending_cv.wait()
                    continue
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._pending_cv.wait(remaining)
        return True

    def close(self, timeout: float = 5.0) -> None:
        """Ferma il thread di sfondo e chiude la connessione propria (test e spegnimento)."""
        if self._closed:
            return
        self._closed = True
        self.flush(timeout)
        self._queue.put(_SENTINEL)
        self._worker_thread.join(timeout)
        self._invalidate_connection()

    # -- handler delle scritture (sulla connessione propria dell'helper) ----
    def _handle_insert_trace(self, conn: psycopg.Connection, job: _InsertTraceJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            # G8a: start_trace controlla anche lui che il trace_id non sia
            # gia' di un altro tenant (stesso controllo di start_segment).
            cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (job.trace_id,))
            if cur.fetchone()[0]:
                self._safe_emit(
                    "trace.trace_tenant_mismatch",
                    tenant_id=job.tenant_id,
                    table="gravya_traces",
                    reason="trace_id appartiene a un altro tenant",
                    count=1,
                )
                return
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

    def _handle_update_trace(self, conn: psycopg.Connection, job: _UpdateTraceJob) -> None:
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

    def _handle_insert_segment(self, conn: psycopg.Connection, job: _InsertSegmentJob) -> None:
        with writer_transaction(conn, job.tenant_id, statement_timeout_ms=self._write_statement_timeout_ms) as c, c.cursor() as cur:
            cur.execute(
                "SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (job.trace_id,)
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

    def _handle_update_segment(self, conn: psycopg.Connection, job: _UpdateSegmentJob) -> None:
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
        tenant_id = self._enforce_tenant_context(trace.tenant_id)
        if tenant_id is None:
            return
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
        self._enqueue(job)

    def end_trace(self, conn: psycopg.Connection, trace_end: TraceEnd) -> None:
        tenant_id = self._enforce_tenant_context(trace_end.tenant_id)
        if tenant_id is None:
            return
        result = self._apply_field_whitelist(wl.TRACE_FIELD_WHITELIST, {"status": trace_end.status}, tenant_id)
        job = _UpdateTraceJob(
            tenant_id=tenant_id,
            trace_id=str(trace_end.trace_id),
            ended_at=trace_end.ended_at,
            status=result.clean.get("status"),
        )
        self._enqueue(job)

    def start_segment(self, conn: psycopg.Connection, segment: SegmentStart) -> None:
        tenant_id = self._enforce_tenant_context(segment.tenant_id)
        if tenant_id is None:
            return
        clean_attrs = self._apply_whitelist(segment.kind, segment.attributes, tenant_id)
        field_result = self._apply_field_whitelist(wl.SEGMENT_FIELD_WHITELIST, {"name": segment.name}, tenant_id)
        self._inject_args_hash(segment.kind, tenant_id, segment, clean_attrs)
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
        self._enqueue(job)

    def end_segment(self, conn: psycopg.Connection, segment_end: SegmentEnd, kind: str) -> None:
        tenant_id = self._enforce_tenant_context(segment_end.tenant_id)
        if tenant_id is None:
            return
        clean_attrs = self._apply_whitelist(kind, segment_end.attributes, tenant_id)
        field_result = self._apply_field_whitelist(wl.SEGMENT_FIELD_WHITELIST, {"status": segment_end.status}, tenant_id)
        self._inject_args_hash(kind, tenant_id, segment_end, clean_attrs)
        job = _UpdateSegmentJob(
            tenant_id=tenant_id,
            segment_id=str(segment_end.segment_id),
            ended_at=segment_end.ended_at,
            status=field_result.clean.get("status"),
            attributes=clean_attrs,
            expected_kind=kind,
        )
        self._enqueue(job)
