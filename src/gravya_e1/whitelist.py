"""Whitelist di chiavi e valori per `kind` (E1 §4.2), `redaction_version` 1.

Implementa esattamente la tabella di E1 §4.2 (vincolo 6 del task implementer):
un attributo fuori whitelist o un valore non conforme al formato viene
scartato (§6, criterio 4). Whitelist, nomi degli header e formato
`traceparent` sono invarianti (catalogo §18): non sono variabili di
piattaforma e non passano dall'istantanea E5.

Giro 3 (dopo il secondo BLOCCA):
- **G1/G2.** Tutte le espressioni regolari usano `fullmatch` (mai `match`
  con un `$` finale, che in Python accetta anche un `\\n` finale). Gli UUID
  sono accettati solo nella forma canonica minuscola con trattini (36
  caratteri): si confronta `str(uuid.UUID(x)) == x`, cosi' forme come
  `urn:uuid:...`, `{...}`, senza trattini o con prefisso `0x` sono scartate.
- **G3 (decisione dell'utente, provvisorio fino ad A6).** `run_id` e'
  ora un UUID canonico (si assume generato da Gravya, come `trace_id`), non
  piu' un identificativo libero. `gravya.decision.reviewer_ref` e' un
  prefisso fisso (`reviewer_`) piu' un UUID canonico.
- Il formato "prefisso_corpo" (`opaque_id`, `destination_id`) resta un
  formato, non un vocabolario: una PII con un prefisso e un underscore
  (`mario_rossi`, `tel_3331234567`) passa ancora. E' un limite dichiarato,
  non un vocabolario chiuso: vedi report, sezione sui formati provvisori.

Giro 2 (dopo il primo BLOCCA), invariato:
- `gravya.tool.args_hash` e `gravya.decision.args_hash` NON sono accettati
  come attributi forniti dal chiamante (B6): l'helper li calcola lui stesso
  da argomenti grezzi (`tracing.py`) e li inietta dopo la whitelist.
- `gravya.prompt.hash` accettato solo insieme a `gravya.prompt.key` e
  `gravya.prompt.version` (B6); il criterio 16 resta parziale.
- Campi di base di traccia/segmento passano dalla stessa validazione
  (B1/R-01/R17): vocabolari **provvisori**, da recepire in E1 v1.7.
- `gravya.tool.outcome` (decisione 2 del coordinator, confermata nel giro 3):
  nome scelto per l'esito del tool di E1 §4.2 (non definito dal testo).
- Ogni validatore e' difensivo (B3): un valore di tipo inatteso (lista,
  dict, non hashable) non deve mai sollevare un'eccezione, solo restituire
  False (scartato).

Punti non completati di propria iniziativa (riportati in `divergenze` /
`non_verificato` nel report, come richiesto dal vincolo 6):
- `gravya.decision.kind = router` e il vocabolario di `gravya.decision.outcome`
  per `router` non sono definiti (da allineare con C1): `router` non e'
  accettato da questo modulo.
"""
from __future__ import annotations

import re
import uuid as _uuid
from dataclasses import dataclass
from typing import Callable

REDACTION_VERSION = 1

# --- formati stretti (invarianti di formato, catalogo §18) -----------------

# Identificativo "prefisso_corpo": prefisso alfabetico breve (il tipo di
# oggetto), underscore, corpo alfanumerico breve. Rifiuta codici fiscali,
# numeri di telefono, IBAN, indirizzi email e testo libero senza prefisso
# (ma non una PII con prefisso+underscore: formato, non vocabolario, vedi
# report).
_PREFIXED_ID_RE = re.compile(r"[a-z]{2,16}_[A-Za-z0-9]{1,40}")
_PREFIXED_ID_MAX_LEN = 48

# Identificativo di versione: alfanumerico con punti/trattini (semver-like).
_VERSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]{0,31}")

# Nome di modello/provider: alfanumerico con punti/trattini/underscore/due punti.
_MODEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:\-]{0,127}")

# Riferimento di versione della chiave HMAC (gravya.hash.key_ref): "v" + cifre.
_KEY_REF_RE = re.compile(r"v[0-9]{1,8}")

# Identificativo "libero" ma senza spazi ne' punteggiatura da prosa: usato
# dove il formato preciso non e' ancora deciso dal documento, per non
# bloccare un identificativo legittimo ma comunque non testo libero.
_LOOSE_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]{1,64}")

# Prefisso fisso per lo pseudonimo del revisore HITL (provvisorio, fino ad
# A6): "reviewer_" + UUID canonico.
_REVIEWER_REF_PREFIX = "reviewer_"

# Nome di chiave riportabile in un segnale (B7/G18): identificatore puntato,
# minuscolo, al piu' 4 segmenti (invariante strutturale, non una variabile),
# ciascuno di lunghezza breve.
_SIGNAL_KEY_SEGMENT = r"[a-z][a-z0-9_]{0,19}"
_SIGNAL_KEY_NAME_RE = re.compile(rf"{_SIGNAL_KEY_SEGMENT}(\.{_SIGNAL_KEY_SEGMENT}){{0,3}}")
_SIGNAL_KEY_NAME_MAX_LEN = 64


def _safe(fn: Callable[[object, int], bool]) -> Callable[[object, int], bool]:
    """Avvolge un validatore: nessuna eccezione deve mai uscire (B3)."""

    def _wrapped(value: object, max_bytes: int) -> bool:
        try:
            return bool(fn(value, max_bytes))
        except Exception:  # noqa: BLE001 - difensivo per costruzione (B3)
            return False

    return _wrapped


@_safe
def opaque_id(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) > _PREFIXED_ID_MAX_LEN or len(value.encode("utf-8")) > max_bytes:
        return False
    return bool(_PREFIXED_ID_RE.fullmatch(value))


def _is_canonical_uuid(value: str) -> bool:
    try:
        parsed = _uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return str(parsed) == value


@_safe
def uuid_identifier(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    return _is_canonical_uuid(value)


@_safe
def reviewer_ref_format(value: object, max_bytes: int) -> bool:
    """Pseudonimo del revisore HITL, provvisorio fino ad A6: `reviewer_` + UUID canonico."""
    if not isinstance(value, str):
        return False
    if not value.startswith(_REVIEWER_REF_PREFIX):
        return False
    return _is_canonical_uuid(value[len(_REVIEWER_REF_PREFIX):])


@_safe
def version_identifier(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_VERSION_RE.fullmatch(value))


@_safe
def model_identifier(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    if len(value.encode("utf-8")) > max_bytes:
        return False
    return bool(_MODEL_RE.fullmatch(value))


@_safe
def key_ref_format(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_KEY_REF_RE.fullmatch(value))


@_safe
def loose_token(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str):
        return False
    if len(value.encode("utf-8")) > max_bytes:
        return False
    return bool(_LOOSE_TOKEN_RE.fullmatch(value))


@_safe
def destination_id(value: object, max_bytes: int) -> bool:
    """Identificativo di destinazione dichiarata: non un URL/dominio (DA-B2-07).

    Stesso formato stretto "prefisso_corpo" degli identificativi opachi:
    niente punti ne' `/`, quindi nessun indirizzo di dominio o percorso puo'
    passare per costruzione.
    """
    if not isinstance(value, str):
        return False
    if len(value) > _PREFIXED_ID_MAX_LEN or len(value.encode("utf-8")) > max_bytes:
        return False
    return bool(_PREFIXED_ID_RE.fullmatch(value))


@_safe
def hash_hex(value: object, max_bytes: int) -> bool:
    from gravya_e1.hashing import is_well_formed_hex_sha256

    if not isinstance(value, str):
        return False
    if len(value.encode("utf-8")) > max_bytes:
        return False
    return is_well_formed_hex_sha256(value)


@_safe
def nonneg_int(value: object, max_bytes: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@_safe
def bool_value(value: object, max_bytes: int) -> bool:
    return isinstance(value, bool)


def closed_vocab(allowed: frozenset[str]) -> Callable[[object, int], bool]:
    @_safe
    def _validator(value: object, max_bytes: int) -> bool:
        return isinstance(value, str) and value in allowed

    return _validator


POLICY_OUTCOMES = frozenset({"allow", "deny", "require_approval"})
HITL_OUTCOMES = frozenset(
    {"requested", "approved", "rejected", "input_provided", "expired", "cancelled", "executed"}
)
EXEC_RESULTS = frozenset({"ok", "refused", "error"})
DECISION_KINDS = frozenset({"policy", "hitl"})  # "router": non implementato, vedi docstring

# --- Vocabolari PROVVISORI (decisione 2/3 del coordinator) -----------------
# Non sono nel testo di E1 v1.6: minimi, scelti per non lasciare passare
# testo libero, da recepire/confermare in E1 v1.7 con i documenti che li
# producono davvero (A3/B1/C1/C3). Vedi report, sezione "Vocabolari
# provvisori da recepire in E1 v1.7".
PROVISIONAL_TRACE_STATUSES = frozenset({"running", "succeeded", "failed", "error", "cancelled"})
PROVISIONAL_SEGMENT_STATUSES = frozenset({"ok", "error", "cancelled", "timeout"})
PROVISIONAL_ROOT_KINDS = frozenset({"agent", "workflow", "eval"})
PROVISIONAL_RETENTION_CLASSES = frozenset({"traces_days", "eval_reports_months"})
PROVISIONAL_TOOL_OUTCOMES = frozenset({"ok", "denied", "approval_required", "rate_limited", "error"})

SEGMENT_KINDS = frozenset({"llm", "tool", "agent", "retrieval", "decision", "eval_case"})

# kind -> { attribute_name: validator(value, max_bytes) -> bool }
# `gravya.tool.args_hash`, `gravya.decision.args_hash` e `gravya.hash.key_ref`
# non sono qui per tool/decision: li inietta l'helper dopo il calcolo
# dell'HMAC (B6), non sono accettati dal chiamante via `attributes`.
ATTRIBUTE_WHITELIST: dict[str, dict[str, Callable[[object, int], bool]]] = {
    "llm": {
        "gen_ai.provider.name": model_identifier,
        "gen_ai.request.model": model_identifier,
        "gen_ai.response.model": model_identifier,
        "gen_ai.usage.input_tokens": nonneg_int,
        "gen_ai.usage.output_tokens": nonneg_int,
        "gravya.prompt.key": opaque_id,
        "gravya.prompt.version": version_identifier,
        "gravya.prompt.hash": hash_hex,  # contestuale: richiede key+version, vedi validate_attributes
        "gravya.llm.destination": destination_id,
    },
    "tool": {
        "gen_ai.tool.name": opaque_id,
        "gen_ai.tool.call.id": opaque_id,
        "gravya.tool.destination": destination_id,
        "gravya.tool.outcome": closed_vocab(PROVISIONAL_TOOL_OUTCOMES),  # provvisorio, decisione 2
        "gravya.decision.id": uuid_identifier,
    },
    "agent": {
        "gen_ai.agent.id": opaque_id,
        "gen_ai.agent.name": opaque_id,
    },
    "retrieval": {
        "gravya.retrieval.source": opaque_id,
        "gravya.retrieval.results_count": nonneg_int,
    },
    "decision": {
        "gravya.decision.kind": closed_vocab(DECISION_KINDS),
        "gravya.decision.outcome": lambda v, m: isinstance(v, str),  # validato nel contesto (dipende da kind)
        "gravya.decision.id": uuid_identifier,
        "config_version": opaque_id,
        "gravya.policy.bundle_version": version_identifier,
        "gravya.policy.bundle_hash": hash_hex,
        "gravya.decision.reviewer_ref": reviewer_ref_format,  # giro 3: prefisso fisso + UUID canonico
        "gravya.decision.exec_result": closed_vocab(EXEC_RESULTS),
        "gravya.decision.exec_code": opaque_id,
        "gravya.workflow.id": opaque_id,
        "gravya.workflow.version": version_identifier,
        "gravya.workflow.node_id": opaque_id,
    },
    "eval_case": {
        "gravya.eval.case_id": opaque_id,
        "gravya.eval.pass": bool_value,
    },
}

# Chiavi che l'helper inietta lui stesso dopo il calcolo dell'HMAC (B6): mai
# accettate nel dizionario `attributes` fornito dal chiamante.
INTERNAL_ONLY_ATTRIBUTE_KEYS = frozenset(
    {"gravya.tool.args_hash", "gravya.decision.args_hash", "gravya.hash.key_ref"}
)

# Campi di base di traccia/segmento, fuori da `attributes` (B1/R-01/R17).
# Vocabolari/formati PROVVISORI: vedi report. `run_id` e' un UUID canonico
# (decisione dell'utente, giro 3: si assume generato da Gravya).
TRACE_FIELD_WHITELIST: dict[str, Callable[[object, int], bool]] = {
    "run_id": uuid_identifier,
    "execution_ticket_id": opaque_id,
    "root_kind": closed_vocab(PROVISIONAL_ROOT_KINDS),
    "workflow_id": opaque_id,
    "workflow_version": version_identifier,
    "retention_class": closed_vocab(PROVISIONAL_RETENTION_CLASSES),
    "status": closed_vocab(PROVISIONAL_TRACE_STATUSES),
}

SEGMENT_FIELD_WHITELIST: dict[str, Callable[[object, int], bool]] = {
    "name": opaque_id,
    "status": closed_vocab(PROVISIONAL_SEGMENT_STATUSES),
}


@dataclass(frozen=True)
class DiscardReason:
    kind: str
    key: str
    reason: str


# Nomi di chiave "conosciuti" (whitelist reale di E1): un segnale puo'
# sempre riportarli per intero (G18). Qualunque altra chiave passa solo dal
# formato strutturale limitato sotto.
_KNOWN_SIGNAL_KEYS = (
    frozenset(key for spec in ATTRIBUTE_WHITELIST.values() for key in spec)
    | frozenset(TRACE_FIELD_WHITELIST)
    | frozenset(SEGMENT_FIELD_WHITELIST)
    | INTERNAL_ONLY_ATTRIBUTE_KEYS
)


def safe_signal_key_name(key: str) -> tuple[str | None, int]:
    """Nome di chiave da riportare in un segnale (vincolo B7, G18).

    Ritorna (nome, lunghezza): il nome compare per intero solo se e' una
    chiave della whitelist reale di E1, oppure un identificativo puntato
    minuscolo con al piu' 4 segmenti brevi (invariante strutturale);
    altrimenti None e solo la lunghezza originale (mai il contenuto).
    """
    length = len(key) if isinstance(key, str) else -1
    if not isinstance(key, str) or len(key) > _SIGNAL_KEY_NAME_MAX_LEN:
        return None, length
    if key in _KNOWN_SIGNAL_KEYS:
        return key, length
    if _SIGNAL_KEY_NAME_RE.fullmatch(key):
        return key, length
    return None, length
