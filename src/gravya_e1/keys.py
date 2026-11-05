"""Chiave HMAC per tenant (vincolo 5 del task implementer E1, DA-E1-09, DA-CV-23).

La pagina credenziali (A6) non esiste ancora: l'helper legge la chiave da
questa interfaccia. Nei test si usano chiavi di prova sintetiche
(`StaticTestKeyProvider`). La sorgente reale delle chiavi (pagina credenziali,
A6) resta da definire: vedi report, decisioni_mancanti.

Rotazione a due chiavi (DA-CV-23): un tenant puo' avere piu' chiavi valide in
parallelo durante una sostituzione, identificate da `gravya.hash.key_ref`. La
distruzione di una chiave la rende definitivamente non recuperabile da questa
interfaccia: gli hash gia' scritti con quella chiave restano nel DB ma non
sono piu' ricalcolabili (DA-E1-09).
"""
from __future__ import annotations

from typing import Protocol


class KeyNotFoundError(RuntimeError):
    """Nessuna chiave valida per il tenant, o chiave distrutta (criterio 15)."""


class TenantKeyProvider(Protocol):
    def current_key_ref(self, tenant_id: str) -> str:
        """Ref della chiave corrente del tenant. Solleva KeyNotFoundError se assente."""

    def get_key(self, tenant_id: str, key_ref: str) -> bytes:
        """Byte della chiave identificata da `key_ref` per il tenant.

        Solleva KeyNotFoundError se la chiave non esiste o e' stata distrutta.
        """


class StaticTestKeyProvider:
    """Implementazione di test con chiavi sintetiche (mai segreti reali)."""

    def __init__(self) -> None:
        # tenant_id -> {key_ref: key_bytes}
        self._keys: dict[str, dict[str, bytes]] = {}
        # tenant_id -> key_ref corrente
        self._current: dict[str, str] = {}

    def set_key(self, tenant_id: str, key_ref: str, key_bytes: bytes, *, make_current: bool = True) -> None:
        self._keys.setdefault(tenant_id, {})[key_ref] = key_bytes
        if make_current:
            self._current[tenant_id] = key_ref

    def destroy_key(self, tenant_id: str, key_ref: str) -> None:
        keys = self._keys.get(tenant_id, {})
        keys.pop(key_ref, None)
        if self._current.get(tenant_id) == key_ref:
            del self._current[tenant_id]

    def current_key_ref(self, tenant_id: str) -> str:
        ref = self._current.get(tenant_id)
        if ref is None:
            raise KeyNotFoundError(f"nessuna chiave corrente per il tenant '{tenant_id}'")
        return ref

    def get_key(self, tenant_id: str, key_ref: str) -> bytes:
        key = self._keys.get(tenant_id, {}).get(key_ref)
        if key is None:
            raise KeyNotFoundError(f"chiave '{key_ref}' non trovata per il tenant '{tenant_id}' (distrutta o mai creata)")
        return key
