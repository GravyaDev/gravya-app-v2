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

Giro 4 (correzione richiesta dal coordinator). `tenant_context` assente e'
obbligatorio solo quando l'ambiente di produzione e' **reale**
(`is_production()`, `API_ENV=production`): in tal caso `__init__` emette il
segnale `trace.tenant_context_absent` e solleva `TenantContextRequiredError`,
l'helper non viene costruito. `production_override` da solo (produzione
"simulata" nei test, senza impersonare un ambiente reale) NON attiva questo
obbligo: e' una scelta esplicita del coordinator (vedi report), perche' i
pacchetti di prova fissi dei revisori costruiscono l'helper con
`production_override=True` e senza `tenant_context` in decine di casi.
Fuori da produzione reale, se `tenant_context` e' assente l'helper si avvia
comunque, ma emette lo stesso segnale in forma informativa (non bloccante).

Giro 4 (dopo il terzo RIPORTA di code-reviewer e compliance-auditor).
- **N2/N3.** Un guardiano per-job (`e1.write_tcp_user_timeout_ms`, usato sia
  come `tcp_user_timeout` di libpq sia come durata massima applicativa di un
  job) interrompe dall'esterno una scrittura o un'emissione di segnale ferme
  oltre il tempo configurato: chiude il socket della connessione bloccata
  (`shutdown()`, sicuro tra thread - non un `close()` concorrente, che su
  Linux non sblocca una `recv()` in corso in un altro thread). `close()` usa
  lo stesso meccanismo subito se `flush()` non si svuota entro il proprio
  `timeout`, invece di una `put()` bloccante del sentinella: non si appende
  mai oltre il `timeout` dato. I job rimasti in coda allo spegnimento sono
  contati (le scritture, in `loss_count`) e segnalati (log di ripiego: i
  thread di sfondo sono gia' fermi a quel punto).
- **G3-01.** I segnali passano da una coda e un thread di sfondo propri
  (separati da quelli delle scritture): nessuna emissione tocca mai il
  thread del chiamante. Coda piena: log di ripiego diretto (mai il
  database). Quando il sink dato (`signal_sink`) e' un `PostgresSignalSink`
  (riconosciuto per duck typing sull'attributo `_conn`, l'unico modo
  compatibile con la firma esistente `PostgresSignalSink(conn)` usata dai
  pacchetti di prova dei revisori), la sua connessione e' soggetta allo
  stesso guardiano per-job delle scritture: non e' una *nuova* connessione
  creata da `TracingHelper` (il sink resta quello costruito dal chiamante),
  ma la stessa interruzione e lo stesso timeout configurato.
- **N9.** Il contesto del tenant si confronta come UUID canonico (non come
  stringa): `tenant_context="...-ABC..."` (maiuscolo) e un modello con lo
  stesso tenant in minuscolo ora corrispondono.
- **N11.** `connect_timeout` non viene piu' arrotondato (`max(1, round(...))`
  trasformava 400 ms in 1 s e 2500 ms in 2 s): si passa `ms/1000` esatto.
- **G3-05.** Il nome di una chiave scartata in un segnale e' riportato per
  intero SOLO se e' una chiave nota della whitelist reale di E1; per
  qualunque altra chiave, solo la lunghezza (prima: anche un identificatore
  puntato generico a 4 segmenti passava per intero).

Vedi `docs/revisioni/impl-e1/report-implementer.md`, sezione "Giro 4", per
la nota sul punto NON implementato (G3-04, API_ENV a vocabolario chiuso:
contraddice un test bloccato del giro 1) e sulla scelta per N11.

Giro 5 (ultime correzioni dopo la verifica mirata del giro 4, e decisioni
dell'utente). Vedi report, sezione "Giro 5", per il collegamento
rilievo -> modifica -> test.
- **Decisione utente.** `API_ENV` fuori dall'insieme chiuso (`production`,
  `development`, `test`) ora **blocca l'avvio** (ribalta la scelta del giro
  4): emette `e5.environment_invalid` e solleva `EnvironmentInvalidError`.
  Assente resta "sviluppo" con `e5.environment_undeclared` (invariato).
  `code-reviewer/test_R15b` diventa fallito atteso per questa decisione.
- **Decisione utente.** `e1.write_connect_timeout_ms` rinominata
  `e1.write_connect_timeout_s` (intero, minimo tecnico effettivo 2 tramite
  `min` nell'istantanea): nessuna conversione nel codice, passata cosi'
  com'e' a `connect_timeout`.
- **W2a/W2b.** Il worker (scritture e segnali) non tenta piu' di
  riconnettersi dopo `close()`: `_get_own_connection`/
  `_get_own_signal_connection` sollevano subito se l'helper e' chiuso,
  invece di provare un `psycopg.connect()` (fino a `connect_timeout`) verso
  una rete che puo' essere ancora bloccata. Con 150 job in coda e la rete
  bloccata, questo fa drenare il resto della coda in pochi millisecondi
  invece che in `150 * connect_timeout`. `_invalidate_connection`/
  `_invalidate_signal_connection` accettano un `timeout` (lock con
  `acquire(timeout=...)`, mai un'attesa indefinita sul lock conteso da una
  riconnessione in corso). Il conteggio dei job rimasti (`_drain_remaining_as_lost`)
  gira solo se i due thread di sfondo sono gia' fermi (mai in concorrenza
  con un worker ancora vivo sulla stessa coda). Nota dichiarata: se la
  connessione e' sana e la coda e' solo profonda (non bloccata), il worker
  puo' continuare a scrivere oltre il momento in cui `close()` ha gia'
  deciso di arrendersi, finche' non gli serve una riconnessione: `flush()`
  mantiene il suo significato ("aspetta che si svuoti"), `close()` non
  aspetta oltre il proprio `timeout` ma non interrompe un lavoro sano in
  corso solo per principio.
- **S1/S2.** Il thread dei segnali usa una **connessione propria**
  (`_get_own_signal_connection`, stessi parametri/limiti della scrittura:
  `connect_timeout`, `statement_timeout`, `tcp_user_timeout`, keepalive,
  guardiano per-job), riconosciuta non piu' per duck typing su un attributo
  privato ma con `isinstance(self._signals, PostgresSignalSink)` (tipo
  pubblico): la connessione **data dal chiamante a `PostgresSignalSink` non
  viene piu' usata per scrivere**, solo per dire "voglio un sink Postgres".
  Dopo un errore: `rollback()` e riconnessione (connessione invalidata,
  una nuova alla prossima emissione), come per le scritture.
  **Questi limiti valgono solo per il sink PostgreSQL** (riconosciuto per
  tipo): un sink diverso (per esempio `InMemorySignalSink`, o un'altra
  implementazione di `SignalSink`) resta possibile tramite l'interfaccia,
  senza guardiano ne' connessione propria (non avrebbe senso: non c'e' una
  connessione psycopg da gestire).
- **S3.** Il campo `kind` di un segnale di scarto (`trace.segment_attribute_discarded`)
  e' ora validato contro il vocabolario dei `kind` noti
  (`wl.safe_signal_kind`): un `kind` arbitrario del chiamante (il parametro
  `kind` di `end_segment`, mai validato prima) diventa un segnaposto fisso,
  non il testo del chiamante.
- **V1.** `e1.write_tcp_user_timeout_ms` e' ora in `_EXPECTED_INT_VARIABLES`
  (tipo e minimo tecnico 1 applicati come per le altre). Nuova regola
  relazionale, verificata all'avvio: non puo' essere minore di
  `e1.write_statement_timeout_ms` (altrimenti blocca con segnale, lo stesso
  guardiano interromperebbe un job prima che il server abbia anche solo
  iniziato a contare il proprio timeout).

Giro 6 (ultimo giro, verifica mirata finale del code-reviewer).
- **X1.** `_get_own_connection`/`_get_own_signal_connection` ricontrollano
  `self._closed` anche DOPO che `psycopg.connect()` e' tornato con successo:
  una connessione completata mentre `close()` aveva gia' rinunciato ad
  aspettare (per esempio una rete bloccata che si sblocca proprio dopo)
  prima veniva comunque assegnata e usata per scrivere, un backend orfano
  mai chiuso. Ora si chiude subito e il job si conta come perso.
- **D1 (DX-22).** Tolte le due durate fisse nel codice: il `get()` con un
  intervallo di attesa di due decimi di secondo nei due worker torna un
  `get()` bloccante senza polling (il sentinella che li ferma e' consegnato
  da un thread di appoggio con una `put()` bloccante, cosi' arriva comunque
  anche con la coda piena, senza che `close()` stesso debba aspettarlo);
  `close()` perde il valore predefinito `timeout=5.0`,
  diventa un parametro **obbligatorio** del chiamante: scelta dichiarata
  (l'alternativa, una nuova variabile dell'istantanea, avrebbe richiesto
  aggiungerla a ogni istantanea/fixture esistente solo per questo; un
  parametro obbligatorio non tocca nessun altro file - solo i due posti in
  `tests/` che chiamavano `close()` senza argomenti, nessuno nei pacchetti
  di prova dei revisori, che lo passano gia' sempre esplicitamente).
- **Decisione dell'utente.** Il blocco per `API_ENV` fuori dall'insieme
  chiuso vale ora ANCHE con `production_override` impostato (anche `True`).
  Nuova decisione: `API_ENV` NON impostata ora blocca l'avvio con segnale
  (prima: trattata come sviluppo, con segnale informativo) - ma resta
  condizionata a `production_override is None` (chi sceglie esplicitamente
  un comportamento non deve impostare un `API_ENV` finto solo per poterlo
  fare).
- **V3.** Il minimo tecnico 2 di `e1.write_connect_timeout_s` e' ora imposto
  dal codice (`_HIGHER_TECHNICAL_MINIMUMS` in `config/variables.py`), non
  solo dal campo `min` facoltativo dell'istantanea.
"""
from __future__ import annotations

import json
import logging
import queue
import socket
import threading
import time
import uuid as _uuid
from dataclasses import dataclass, field
from typing import Any, Callable

import psycopg

from gravya_e1 import whitelist as wl
from gravya_e1.config.env import is_declared, is_declared_value_valid, is_production
from gravya_e1.config.variables import VariableRegistry, VariableUnavailableError
from gravya_e1.db import writer_transaction
from gravya_e1.hashing import HashUnavailableError, compute_args_hmac
from gravya_e1.keys import TenantKeyProvider
from gravya_e1.models import SegmentEnd, SegmentStart, TraceEnd, TraceStart
from gravya_e1.signals import PostgresSignalSink, SignalSink, log_fallback

logger = logging.getLogger("gravya_e1.tracing")

TRACE_REQUIRED_FIELDS = frozenset({"run_id"})

_SENTINEL = object()


class EnvironmentInvalidError(RuntimeError):
    """Sollevato da `__init__` quando `API_ENV` e' impostata a un valore fuori
    dall'insieme chiuso (`production`/`development`/`test`), giro 5,
    decisione dell'utente."""


class AttributeRejectedError(ValueError):
    """Sollevato fuori produzione quando un campo/attributo non e' conforme (§6)."""


def _canonical_tenant(value: Any) -> str:
    """UUID canonico se possibile (N9: confronto robusto al maiuscolo/minuscolo
    e ad altre forme equivalenti), altrimenti il valore testuale cosi' com'e'
    (difensivo: non deve mai sollevare)."""
    try:
        return str(_uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return str(value)


class TenantContextRequiredError(RuntimeError):
    """Sollevato da `__init__` quando l'ambiente e' di produzione reale (`API_ENV=production`)
    ma non e' stato dato un `tenant_context` (giro 4, correzione del coordinator)."""


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
        self._tenant_context = _canonical_tenant(tenant_context) if tenant_context is not None else None
        self._conninfo = conninfo

        # Avvio dell'helper (criterio 17): legge subito le variabili "da
        # definire" di E1; con la guardia di produzione attiva, un valore
        # mancante blocca l'avvio (solleva VariableUnavailableError).
        self._write_buffer_size = self._variables.get("e1.write_buffer_size").value
        self._max_value_bytes = self._variables.get("e1.attributes.max_value_bytes").value
        self._write_statement_timeout_ms = self._variables.get("e1.write_statement_timeout_ms").value
        # Giro 5 (decisione dell'utente): rinominata da _ms, nessuna
        # conversione nel codice (passata cosi' com'e' a `connect_timeout`).
        self._write_connect_timeout_s = self._variables.get("e1.write_connect_timeout_s").value
        self._keepalives_idle_s = self._variables.get("e1.write_tcp_keepalives_idle_s").value
        self._keepalives_interval_s = self._variables.get("e1.write_tcp_keepalives_interval_s").value
        self._keepalives_count = self._variables.get("e1.write_tcp_keepalives_count").value
        # Giro 4 (N2): usato sia come `tcp_user_timeout` di libpq sia come
        # durata massima applicativa di un job (guardiano per-job sotto).
        self._tcp_user_timeout_ms = self._variables.get("e1.write_tcp_user_timeout_ms").value
        self._job_timeout_s = self._tcp_user_timeout_ms / 1000

        self._loss_lock = threading.Lock()
        self.loss_count = 0
        self._pending_signal_loss = 0

        # Giro 5 (CR V1): regola relazionale, verificata subito (prima di
        # avviare i thread): un guardiano piu' corto dello statement_timeout
        # interromperebbe un job prima ancora che il server abbia iniziato a
        # contare il proprio timeout.
        if self._tcp_user_timeout_ms < self._write_statement_timeout_ms:
            self._emit_at_startup(
                "e5.variable_invalid",
                name="e1.write_tcp_user_timeout_ms",
                reason="minore di e1.write_statement_timeout_ms",
            )
            raise VariableUnavailableError(
                "e1.write_tcp_user_timeout_ms non puo' essere minore di e1.write_statement_timeout_ms "
                f"({self._tcp_user_timeout_ms} < {self._write_statement_timeout_ms})"
            )

        # Giro 6 (CA E2): un valore di API_ENV fuori dall'insieme chiuso
        # blocca l'avvio ANCHE con `production_override` impostato (anche
        # `True`): un valore dichiarato ma sbagliato e' un segnale di
        # configurazione errata che conta sempre, non solo quando nessuno ha
        # gia' scelto esplicitamente un comportamento per un test/una
        # simulazione. Emissione sincrona: non c'e' ancora un thread dei
        # segnali, e l'avvio e' gia' sincrono di suo.
        if not is_declared_value_valid():
            self._emit_at_startup(
                "e5.environment_invalid",
                reason="API_ENV fuori dall'insieme chiuso (production/development/test): avvio bloccato",
            )
            raise EnvironmentInvalidError(
                "API_ENV fuori dall'insieme chiuso (production/development/test)"
            )
        # Giro 6 (decisione dell'utente): API_ENV NON impostata ora blocca
        # l'avvio con segnale (prima: trattata come sviluppo, con segnale
        # informativo e avvio consentito). Resta gated da
        # `production_override is None`: chi sceglie esplicitamente un
        # comportamento (anche `production_override=False`, per simulare
        # "sviluppo" a prescindere dall'ambiente reale) non deve impostare
        # un API_ENV finto solo per poterlo fare.
        if self._production_override is None and not is_declared():
            self._emit_at_startup("e5.environment_undeclared", reason="API_ENV non impostata: avvio bloccato")
            raise EnvironmentInvalidError("API_ENV non impostata")

        # Giro 4: `tenant_context` e' obbligatorio solo sotto la guardia di
        # produzione REALE (`is_production()`, non `production_override`,
        # che resta una "produzione simulata" per i test - vedi report).
        if self._tenant_context is None:
            if is_production():
                self._emit_at_startup("trace.tenant_context_absent", reason="tenant_context_absent_bloccante")
                raise TenantContextRequiredError(
                    "tenant_context e' obbligatorio quando API_ENV=production"
                )
            self._emit_at_startup("trace.tenant_context_absent", reason="tenant_context_absent_informativo")

        self._conn_lock = threading.Lock()
        self._own_conn: psycopg.Connection | None = None
        # Giro 5 (S1/S2): connessione propria, separata, per i segnali.
        self._signal_conn_lock = threading.Lock()
        self._own_signal_conn: psycopg.Connection | None = None
        self._closed = False

        self._pending = 0
        self._pending_cv = threading.Condition()

        # Giro 4 (G3-01): coda e thread di sfondo propri per i segnali,
        # separati da quelli delle scritture (sotto): nessuna emissione tocca
        # mai il thread del chiamante.
        self._queue: "queue.Queue" = queue.Queue(maxsize=self._write_buffer_size)
        self._signal_queue: "queue.Queue" = queue.Queue(maxsize=self._write_buffer_size)

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._signal_worker_thread = threading.Thread(target=self._signal_worker_loop, daemon=True)
        self._signal_worker_thread.start()

    # -- ambiente -------------------------------------------------------
    def _is_production(self) -> bool:
        # G9: l'override puo' solo irrigidire la guardia, mai spegnerla.
        if self._production_override:
            return True
        return is_production()

    # -- segnali, mai propagati (B2) --------------------------------------
    def _emit_at_startup(self, event: str, **fields: Any) -> None:
        """Invio sincrono, solo per i controlli nel costruttore (giro 4): a
        quel punto il thread dei segnali non esiste ancora (o non serve: non
        c'e' un chiamante da proteggere dalla latenza durante l'avvio, gia'
        sincrono di suo). Stesso ripiego di `_safe_emit` in caso di eccezione
        del sink."""
        try:
            self._signals.emit(event, tenant_id=None, **fields)
        except Exception:  # noqa: BLE001 - il fail-open non dipende dal sink (B2/R-08)
            try:
                log_fallback(event, tenant_id=None, **fields)
            except Exception:  # noqa: BLE001 - ripiego di ultima istanza
                pass

    def _safe_emit(self, event: str, *, tenant_id: str | None = None, **fields: Any) -> None:
        """Accoda l'emissione (giro 4, G3-01): la esegue solo il thread di
        sfondo dei segnali, mai il thread del chiamante. Coda piena: log di
        ripiego diretto (mai il database)."""
        try:
            self._signal_queue.put_nowait((event, tenant_id, fields))
        except queue.Full:
            try:
                log_fallback(event, tenant_id=tenant_id, **fields)
            except Exception:  # noqa: BLE001
                pass
            return
        with self._pending_cv:
            self._pending += 1
            self._pending_cv.notify_all()

    def _signal_worker_loop(self) -> None:
        while True:
            item = self._signal_queue.get()
            if item is _SENTINEL:
                self._signal_queue.task_done()
                break
            event, tenant_id, fields = item
            # Giro 5 (CR S1): valutato a ogni emissione, non una volta sola
            # all'avvio del thread, cosi' resta corretto anche se il sink
            # cambia dopo la costruzione dell'helper.
            if isinstance(self._signals, PostgresSignalSink):
                self._emit_via_own_postgres_connection(event, tenant_id, fields)
            else:
                self._emit_via_generic_sink(event, tenant_id, fields)
            with self._pending_cv:
                self._pending -= 1
                self._pending_cv.notify_all()
            self._signal_queue.task_done()

    def _emit_via_generic_sink(self, event: str, tenant_id: str | None, fields: dict[str, Any]) -> None:
        """Sink diverso da PostgreSQL (giro 5, correzione 2): nessuna
        connessione propria ne' guardiano, solo l'interfaccia `SignalSink`,
        decoupled dal thread del chiamante (G3-01)."""
        try:
            self._signals.emit(event, tenant_id=tenant_id, **fields)
        except Exception:  # noqa: BLE001 - il fail-open non dipende dal sink (B2/R-08)
            with self._loss_lock:
                self._pending_signal_loss += 1
            try:
                log_fallback(event, tenant_id=tenant_id, **fields)
            except Exception:  # noqa: BLE001 - ripiego di ultima istanza
                pass
        else:
            self._flush_pending_loss(tenant_id)

    def _emit_via_own_postgres_connection(self, event: str, tenant_id: str | None, fields: dict[str, Any]) -> None:
        """Sink PostgreSQL (giro 5, correzione 2, S1/S2): connessione
        **propria** dell'helper (stessi parametri/limiti della scrittura),
        non quella data dal chiamante a `PostgresSignalSink` (riconosciuto
        per tipo, non per un attributo privato). Riconnessione dopo un
        errore, `rollback` dopo un INSERT fallito (in `PostgresSignalSink.emit`
        stesso, cosi' vale anche per chi la usa senza passare da qui)."""
        watchdog = None
        try:
            conn = self._get_own_signal_connection()
            watchdog = threading.Timer(self._job_timeout_s, self._force_disconnect, args=(conn,))
            watchdog.daemon = True
            watchdog.start()
            PostgresSignalSink(conn).emit(event, tenant_id=tenant_id, **fields)
        except Exception:  # noqa: BLE001 - il fail-open non dipende dal sink (B2/R-08)
            try:
                if self._own_signal_conn is not None:
                    self._own_signal_conn.rollback()
            except Exception:  # noqa: BLE001
                pass
            self._invalidate_signal_connection()
            with self._loss_lock:
                self._pending_signal_loss += 1
            try:
                log_fallback(event, tenant_id=tenant_id, **fields)
            except Exception:  # noqa: BLE001 - ripiego di ultima istanza
                pass
        else:
            self._flush_pending_loss(tenant_id)
        finally:
            if watchdog is not None:
                watchdog.cancel()

    def _force_disconnect(self, conn: psycopg.Connection | None) -> None:
        """Interrompe dall'esterno un'operazione bloccata su `conn` (N2/N3):
        `shutdown()` sul socket sottostante sblocca subito qualunque
        `recv`/`send` in corso nel thread che la sta eseguendo (a differenza
        di un `close()` concorrente, che su Linux non sblocca una syscall gia'
        bloccata in un altro thread). Chi stava usando `conn` la vede fallire
        con un errore, gestito dal chiamante (fail-open, B2)."""
        if conn is None:
            return
        try:
            fd = conn.pgconn.socket
        except Exception:  # noqa: BLE001 - connessione gia' chiusa o non disponibile
            return
        if fd is None or fd < 0:
            return
        try:
            raw = socket.socket(fileno=fd)
            try:
                raw.shutdown(socket.SHUT_RDWR)
            finally:
                raw.detach()  # non chiudere l'fd: resta della connessione originale
        except OSError:  # noqa: BLE001 - gia' chiuso o mai connesso del tutto
            pass

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
        # Giro 5 (CR S3): solo i valori del vocabolario dei `kind`, mai il
        # `kind` arbitrario del chiamante (il parametro di `end_segment`,
        # mai validato altrove).
        fields: dict[str, Any] = {
            "kind": wl.safe_signal_kind(discard.kind),
            "reason": discard.reason,
            "count": 1,
            "key_length": length,
        }
        if safe_key is not None:
            fields["key"] = safe_key
        self._safe_emit("trace.segment_attribute_discarded", tenant_id=tenant_id, **fields)

    def _record_loss(self, exc: Exception, table: str, tenant_id: str | None) -> None:
        with self._loss_lock:
            self.loss_count += 1
        self._safe_emit("trace.write_failed", tenant_id=tenant_id, table=table, reason=exc.__class__.__name__, count=1)

    # -- contesto del tenant (G16) ------------------------------------------
    def _resolve_tenant(self, model_tenant_id: Any) -> str | None:
        """Ritorna il tenant autoritativo, o None se e' in conflitto col contesto.

        Giro 4 (N9): confronto come UUID canonico, non come stringa (prima:
        lo stesso tenant in maiuscolo come contesto rifiutava ogni
        scrittura legittima)."""
        model_tenant = _canonical_tenant(model_tenant_id)
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
            # Giro 5 (W2a/W2b): non riconnettersi dopo close(). Senza questo
            # controllo, con la rete bloccata e una coda piena, ogni job
            # rimasto tenterebbe comunque una vera `psycopg.connect()` (fino
            # a `connect_timeout` ciascuno) prima di fallire: con 150 job
            # significa fino a 150 * connect_timeout prima che il thread
            # esca, anche se `close()` ha gia' rinunciato ad aspettare.
            if self._closed:
                raise RuntimeError("helper chiuso: nessuna riconnessione dopo close()")
            connect_timeout_s = self._write_connect_timeout_s
            kwargs = dict(
                connect_timeout=connect_timeout_s,
                keepalives=1,
                keepalives_idle=self._keepalives_idle_s,
                keepalives_interval=self._keepalives_interval_s,
                keepalives_count=self._keepalives_count,
                # Giro 4 (N2): timeout lato client sui dati gia' inviati e
                # non ancora confermati, in millisecondi (libpq >= 12).
                tcp_user_timeout=self._tcp_user_timeout_ms,
                options=f"-c statement_timeout={self._write_statement_timeout_ms}",
            )
            with self._conn_lock:
                if self._own_conn is None or self._own_conn.closed:
                    if self._closed:
                        # Giro 6 (X1): l'helper puo' essere stato chiuso
                        # mentre questo thread era in attesa del lock (per
                        # esempio una `close()` concorrente che ha appena
                        # finito di aspettare il proprio `timeout`): niente
                        # connessione nuova dopo questo punto.
                        raise RuntimeError("helper chiuso: nessuna riconnessione dopo close()")
                    if self._conninfo:
                        new_conn = psycopg.connect(self._conninfo, **kwargs)
                    else:
                        # Nessun parametro esplicito: le variabili d'ambiente
                        # standard di libpq (PGHOST, PGPORT, PGUSER, PGDATABASE,
                        # PGPASSWORD) forniscono la destinazione e la credenziale
                        # (mai una connessione del chiamante, G7/G14a).
                        new_conn = psycopg.connect(**kwargs)
                    if self._closed:
                        # Giro 6 (X1): `close()` puo' aver gia' rinunciato ad
                        # aspettare MENTRE questo `psycopg.connect()` era in
                        # corso (per esempio una rete bloccata che si sblocca
                        # proprio dopo che `close()` e' tornato): questa
                        # connessione non deve mai essere usata per scrivere
                        # ne' restare aperta come backend orfano.
                        try:
                            new_conn.close()
                        except Exception:  # noqa: BLE001
                            pass
                        raise RuntimeError("helper chiuso: connessione scartata dopo close()")
                    self._own_conn = new_conn
        return self._own_conn

    def _get_own_signal_connection(self) -> psycopg.Connection:
        """Come `_get_own_connection`, ma per il thread dei segnali (giro 5,
        correzione 2, S1/S2): connessione separata, stessi parametri/limiti.
        Chiamato solo dal thread di sfondo dei segnali."""
        if self._own_signal_conn is None or self._own_signal_conn.closed:
            if self._closed:
                raise RuntimeError("helper chiuso: nessuna riconnessione dopo close()")
            kwargs = dict(
                connect_timeout=self._write_connect_timeout_s,
                keepalives=1,
                keepalives_idle=self._keepalives_idle_s,
                keepalives_interval=self._keepalives_interval_s,
                keepalives_count=self._keepalives_count,
                tcp_user_timeout=self._tcp_user_timeout_ms,
                options=f"-c statement_timeout={self._write_statement_timeout_ms}",
            )
            with self._signal_conn_lock:
                if self._own_signal_conn is None or self._own_signal_conn.closed:
                    if self._closed:
                        raise RuntimeError("helper chiuso: nessuna riconnessione dopo close()")
                    if self._conninfo:
                        new_conn = psycopg.connect(self._conninfo, **kwargs)
                    else:
                        new_conn = psycopg.connect(**kwargs)
                    if self._closed:
                        # Giro 6 (X1), stessa correzione della connessione di scrittura.
                        try:
                            new_conn.close()
                        except Exception:  # noqa: BLE001
                            pass
                        raise RuntimeError("helper chiuso: connessione scartata dopo close()")
                    self._own_signal_conn = new_conn
        return self._own_signal_conn

    def _invalidate_connection(self, timeout: float | None = None) -> None:
        """Chiude e azzera la connessione propria delle scritture.

        Giro 5 (W2a): `timeout`, se dato, limita l'attesa sul lock (altrimenti
        bloccherebbe fino a quando una riconnessione in corso in un altro
        momento non lo rilascia). Se non si riesce ad acquisirlo in tempo, si
        rinuncia: la connessione (se mai creata) si chiudera' da sola alla
        prossima chiamata che trova `self._closed` vero (sopra)."""
        acquired = self._conn_lock.acquire(timeout=timeout if timeout is not None else -1)
        if not acquired:
            return
        try:
            if self._own_conn is not None:
                try:
                    self._own_conn.close()
                except Exception:  # noqa: BLE001
                    pass
                self._own_conn = None
        finally:
            self._conn_lock.release()

    def _invalidate_signal_connection(self, timeout: float | None = None) -> None:
        """Come `_invalidate_connection`, per la connessione propria dei segnali."""
        acquired = self._signal_conn_lock.acquire(timeout=timeout if timeout is not None else -1)
        if not acquired:
            return
        try:
            if self._own_signal_conn is not None:
                try:
                    self._own_signal_conn.close()
                except Exception:  # noqa: BLE001
                    pass
                self._own_signal_conn = None
        finally:
            self._signal_conn_lock.release()

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
            watchdog = None
            try:
                conn = self._get_own_connection()
                # Giro 4 (N2): un job fermo oltre `e1.write_tcp_user_timeout_ms`
                # (rete bloccata dopo la connessione: ne' `statement_timeout`
                # ne' `connect_timeout` ne' i keepalive la sbloccano, perche'
                # il peer e' comunque vivo a livello TCP) viene interrotto
                # dall'esterno invece di restare fermo finche' il kernel non
                # chiude la connessione da solo.
                watchdog = threading.Timer(self._job_timeout_s, self._force_disconnect, args=(conn,))
                watchdog.daemon = True
                watchdog.start()
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
                if watchdog is not None:
                    watchdog.cancel()
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

    def close(self, timeout: float) -> None:
        """Ferma i due thread di sfondo (scritture e segnali) e chiude le
        connessioni: non si appende mai oltre `timeout` in totale (N3).

        `timeout` e' obbligatorio (giro 6, DX-22: nessuna durata fissa nel
        codice; scelta dichiarata, l'alternativa era una variabile
        dell'istantanea, ma avrebbe richiesto una nuova voce in ogni
        istantanea/fixture esistente solo per questo - un parametro
        obbligatorio del chiamante non tocca nessun altro file). Se
        `flush()` non si svuota entro il timeout, il job fermo (scrittura o
        segnale) viene interrotto dall'esterno con lo stesso guardiano di N2,
        invece di affidarsi a una `put()` bloccante e basta (che con la coda
        piena e il thread fermo non sarebbe mai tornata). `self._closed`
        (impostato subito) fa si' che nessun job rimasto tenti una nuova
        riconnessione dopo questo punto (giro 5/6, W2a/W2b/X1): il resto
        della coda, se la rete e' bloccata, si svuota in pochi millisecondi
        invece di un multiplo di `connect_timeout`, e una connessione
        completata DOPO che `close()` ha gia' rinunciato ad aspettare si
        chiude subito invece di restare un backend orfano usato per scrivere
        (X1). Il sentinella che ferma ciascun thread e' consegnato da un
        thread di appoggio con una `put()` bloccante (giro 6, DX-22: nessun
        intervallo di polling): se la coda e' piena al momento di chiudere,
        la consegna arriva comunque appena il worker libera uno slot
        (drenando il resto in fretta, per il motivo sopra), senza che
        `close()` stesso debba aspettarla.
        """
        if self._closed:
            return
        self._closed = True
        deadline = time.monotonic() + timeout
        flushed = self.flush(max(0.0, deadline - time.monotonic()))
        if not flushed:
            self._force_disconnect(self._own_conn)
            self._force_disconnect(self._own_signal_conn)
        threading.Thread(target=self._queue.put, args=(_SENTINEL,), daemon=True).start()
        threading.Thread(target=self._signal_queue.put, args=(_SENTINEL,), daemon=True).start()
        self._worker_thread.join(max(0.0, deadline - time.monotonic()))
        self._signal_worker_thread.join(max(0.0, deadline - time.monotonic()))
        if not self._worker_thread.is_alive() and not self._signal_worker_thread.is_alive():
            self._drain_remaining_as_lost()
        remaining = max(0.0, deadline - time.monotonic())
        self._invalidate_connection(timeout=remaining)
        self._invalidate_signal_connection(timeout=remaining)

    def _drain_remaining_as_lost(self) -> None:
        """Rete di sicurezza difensiva (CA G3-11): con il disegno attuale
        (nessuna uscita anticipata del worker, il sentinella arriva sempre
        prima o poi) la coda e' normalmente gia' vuota quando questa funzione
        gira; resta solo per un'uscita imprevista del thread che lascerebbe
        job non contati. Job rimasti: contati (le scritture, in `loss_count`)
        e segnalati col ripiego di log diretto (i due thread di sfondo sono
        gia' fermi qui: nessuno consumerebbe un'emissione accodata ora)."""
        while True:
            try:
                job = self._queue.get_nowait()
            except queue.Empty:
                break
            if job is _SENTINEL:
                continue
            with self._pending_cv:
                self._pending -= 1
            with self._loss_lock:
                self.loss_count += 1
            try:
                log_fallback("trace.write_failed", tenant_id=job.tenant_id, table=job.table, reason="helper chiuso", count=1)
            except Exception:  # noqa: BLE001
                pass
        while True:
            try:
                item = self._signal_queue.get_nowait()
            except queue.Empty:
                break
            if item is _SENTINEL:
                continue
            event, tenant_id, fields = item
            with self._pending_cv:
                self._pending -= 1
            try:
                log_fallback(event, tenant_id=tenant_id, **fields)
            except Exception:  # noqa: BLE001
                pass

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
