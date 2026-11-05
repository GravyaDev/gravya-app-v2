"""Whitelist di chiavi e valori per `kind` (E1 §4.2), `redaction_version` 1.

Implementa esattamente la tabella di E1 §4.2 (vincolo 6 del task implementer):
un attributo fuori whitelist o un valore non conforme al formato viene
scartato (§6, criterio 4). Whitelist, nomi degli header e formato
`traceparent` sono invarianti (catalogo §18): non sono variabili di
piattaforma e non passano dall'istantanea E5.

Punti non completati di propria iniziativa (riportati in `divergenze` /
`non_verificato` nel report, come richiesto dal vincolo 6):
- l'attributo per l'«esito» del `tool` (`ok`, `denied`, `approval_required`,
  `rate_limited`, `error`) non ha un nome di chiave definito in E1 §4.2: non
  implementato.
- `gravya.decision.kind = router` e il vocabolario di `gravya.decision.outcome`
  per `router` non sono definiti (da allineare con C1): `router` non e'
  accettato da questo modulo.
- i "vocabolari chiusi" di `gen_ai.provider.name`, `gen_ai.*.model`,
  `gen_ai.tool.name`, `gen_ai.agent.name` e `gravya.decision.exec_code` non
  sono enumerati nel documento: validati solo come identificativi opachi di
  formato (non testo libero), non come insieme chiuso di valori.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

REDACTION_VERSION = 1

_OPAQUE_RE = re.compile(r"^[A-Za-z0-9_\-:./]{1,}$")


def _is_opaque_token(value: object, max_bytes: int) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if len(value.encode("utf-8")) > max_bytes:
        return False
    if not _OPAQUE_RE.match(value):
        return False
    # Rifiuta spazi e segni di punteggiatura da prosa: deve restare un
    # identificativo opaco, mai testo libero (§4.2).
    if " " in value or "\n" in value or "\t" in value:
        return False
    return True


def opaque_id(value: object, max_bytes: int) -> bool:
    return _is_opaque_token(value, max_bytes)


def destination_id(value: object, max_bytes: int) -> bool:
    """Identificativo di destinazione dichiarata: non un URL (DA-B2-07)."""
    if not _is_opaque_token(value, max_bytes):
        return False
    lowered = value.lower()
    if "://" in lowered or lowered.startswith("http"):
        return False
    return True


def hash_hex(value: object, max_bytes: int) -> bool:
    from gravya_e1.hashing import is_well_formed_hex_sha256

    if not isinstance(value, str):
        return False
    if len(value.encode("utf-8")) > max_bytes:
        return False
    return is_well_formed_hex_sha256(value)


def nonneg_int(value: object, max_bytes: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def bool_value(value: object, max_bytes: int) -> bool:
    return isinstance(value, bool)


def closed_vocab(allowed: frozenset[str]) -> Callable[[object, int], bool]:
    def _validator(value: object, max_bytes: int) -> bool:
        return isinstance(value, str) and value in allowed

    return _validator


POLICY_OUTCOMES = frozenset({"allow", "deny", "require_approval"})
HITL_OUTCOMES = frozenset(
    {"requested", "approved", "rejected", "input_provided", "expired", "cancelled", "executed"}
)
EXEC_RESULTS = frozenset({"ok", "refused", "error"})
DECISION_KINDS = frozenset({"policy", "hitl"})  # "router": non implementato, vedi docstring

SEGMENT_KINDS = frozenset({"llm", "tool", "agent", "retrieval", "decision", "eval_case"})

# kind -> { attribute_name: validator(value, max_bytes) -> bool }
ATTRIBUTE_WHITELIST: dict[str, dict[str, Callable[[object, int], bool]]] = {
    "llm": {
        "gen_ai.provider.name": opaque_id,
        "gen_ai.request.model": opaque_id,
        "gen_ai.response.model": opaque_id,
        "gen_ai.usage.input_tokens": nonneg_int,
        "gen_ai.usage.output_tokens": nonneg_int,
        "gravya.prompt.key": opaque_id,
        "gravya.prompt.version": opaque_id,
        "gravya.prompt.hash": hash_hex,
        "gravya.llm.destination": destination_id,
    },
    "tool": {
        "gen_ai.tool.name": opaque_id,
        "gen_ai.tool.call.id": opaque_id,
        "gravya.tool.destination": destination_id,
        "gravya.tool.args_hash": hash_hex,
        "gravya.hash.key_ref": opaque_id,
        "gravya.decision.id": opaque_id,
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
        "gravya.decision.id": opaque_id,
        "config_version": opaque_id,
        "gravya.policy.bundle_version": opaque_id,
        "gravya.policy.bundle_hash": hash_hex,
        "gravya.decision.reviewer_ref": opaque_id,
        "gravya.decision.args_hash": hash_hex,
        "gravya.hash.key_ref": opaque_id,
        "gravya.decision.exec_result": closed_vocab(EXEC_RESULTS),
        "gravya.decision.exec_code": opaque_id,
        "gravya.workflow.id": opaque_id,
        "gravya.workflow.version": opaque_id,
        "gravya.workflow.node_id": opaque_id,
    },
    "eval_case": {
        "gravya.eval.case_id": opaque_id,
        "gravya.eval.pass": bool_value,
    },
}


@dataclass(frozen=True)
class DiscardReason:
    kind: str
    key: str
    reason: str
