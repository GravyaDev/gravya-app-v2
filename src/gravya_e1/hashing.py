"""HMAC-SHA-256 degli argomenti, con chiave per tenant (DA-E1-09, decisa).

Formato invariante (catalogo §18): HMAC-SHA-256, esadecimale (64 cifre). La
chiave viene dall'interfaccia `TenantKeyProvider` (keys.py). Senza chiave
valida l'helper non scrive l'attributo hash (criterio 15).
"""
from __future__ import annotations

import hashlib
import hmac

from gravya_e1.keys import KeyNotFoundError, TenantKeyProvider

HEX_SHA256_LEN = 64


class HashUnavailableError(RuntimeError):
    """Nessuna chiave valida per il tenant: l'attributo hash non viene scritto."""


def compute_args_hmac(provider: TenantKeyProvider, tenant_id: str, argument_bytes: bytes) -> tuple[str, str]:
    """Ritorna (hash_hex, key_ref) usando la chiave corrente del tenant.

    Solleva HashUnavailableError se il tenant non ha una chiave valida.
    """
    try:
        key_ref = provider.current_key_ref(tenant_id)
        key = provider.get_key(tenant_id, key_ref)
    except KeyNotFoundError as exc:
        raise HashUnavailableError(str(exc)) from exc
    digest = hmac.new(key, argument_bytes, hashlib.sha256).hexdigest()
    return digest, key_ref


def verify_args_hmac(
    provider: TenantKeyProvider, tenant_id: str, key_ref: str, argument_bytes: bytes, expected_hex: str
) -> bool:
    """Ricalcola l'HMAC con la chiave identificata da `key_ref` e lo confronta.

    Solleva HashUnavailableError se quella chiave non e' piu' disponibile
    (per esempio e' stata distrutta): l'hash non e' ricalcolabile (criterio 15).
    """
    try:
        key = provider.get_key(tenant_id, key_ref)
    except KeyNotFoundError as exc:
        raise HashUnavailableError(str(exc)) from exc
    digest = hmac.new(key, argument_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected_hex)


def is_well_formed_hex_sha256(value: str) -> bool:
    if len(value) != HEX_SHA256_LEN:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
