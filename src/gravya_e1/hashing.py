"""HMAC-SHA-256 degli argomenti, con chiave per tenant (DA-E1-09, decisa).

Formato invariante (catalogo §18): HMAC-SHA-256, esadecimale minuscolo, 64
cifre `[0-9a-f]`, espressione regolare piena (giro 2, B4: niente `int(x, 16)`,
che accetta `0x`, underscore e spazi). La chiave viene dall'interfaccia
`TenantKeyProvider` (keys.py). Senza chiave valida l'helper non scrive
l'attributo hash (criterio 15).

Lunghezza minima della chiave (giro 2, B6): 16 byte (128 bit), invariante di
formato non ancora confermata da A6 (da riportare nel report).
"""
from __future__ import annotations

import hashlib
import hmac
import re

from gravya_e1.keys import KeyNotFoundError, TenantKeyProvider

HEX_SHA256_LEN = 64
_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Invariante di formato (non una variabile di piattaforma): lunghezza minima
# della chiave HMAC. Da confermare con A6 quando la pagina credenziali
# esistera' (vedi report, decisioni_mancanti).
MIN_KEY_BYTES = 16


class HashUnavailableError(RuntimeError):
    """Nessuna chiave valida per il tenant: l'attributo hash non viene scritto."""


def _require_valid_key(key: bytes) -> None:
    if not isinstance(key, (bytes, bytearray)) or len(key) < MIN_KEY_BYTES:
        raise HashUnavailableError(
            f"chiave non valida: lunghezza {len(key) if isinstance(key, (bytes, bytearray)) else 'n/d'} "
            f"byte, minimo richiesto {MIN_KEY_BYTES}"
        )


def compute_args_hmac(provider: TenantKeyProvider, tenant_id: str, argument_bytes: bytes) -> tuple[str, str]:
    """Ritorna (hash_hex, key_ref) usando la chiave corrente del tenant.

    Solleva HashUnavailableError se il tenant non ha una chiave valida (assente,
    vuota o sotto la lunghezza minima).
    """
    try:
        key_ref = provider.current_key_ref(tenant_id)
        key = provider.get_key(tenant_id, key_ref)
    except KeyNotFoundError as exc:
        raise HashUnavailableError(str(exc)) from exc
    _require_valid_key(key)
    digest = hmac.new(key, argument_bytes, hashlib.sha256).hexdigest()
    return digest, key_ref


def verify_args_hmac(
    provider: TenantKeyProvider, tenant_id: str, key_ref: str, argument_bytes: bytes, expected_hex: str
) -> bool:
    """Ricalcola l'HMAC con la chiave identificata da `key_ref` e lo confronta.

    Solleva HashUnavailableError se quella chiave non e' piu' disponibile
    (per esempio e' stata distrutta) o non e' valida: l'hash non e'
    ricalcolabile (criterio 15).
    """
    try:
        key = provider.get_key(tenant_id, key_ref)
    except KeyNotFoundError as exc:
        raise HashUnavailableError(str(exc)) from exc
    _require_valid_key(key)
    digest = hmac.new(key, argument_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected_hex)


def is_well_formed_hex_sha256(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_HEX_SHA256_RE.match(value))
