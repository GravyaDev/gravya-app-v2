"""Criterio 15: HMAC per tenant, rotazione a due chiavi, distruzione, chiave assente."""
from __future__ import annotations

from gravya_e1.hashing import HashUnavailableError, compute_args_hmac, verify_args_hmac
from gravya_e1.keys import KeyNotFoundError, StaticTestKeyProvider
from gravya_e1.tracing import TracingHelper

ARGS = b"argomento-di-prova"


def test_stesso_argomento_stesso_tenant_stesso_hmac():
    provider = StaticTestKeyProvider()
    provider.set_key("tenant-a", "v1", b"chiave-sintetica-a")
    h1, ref1 = compute_args_hmac(provider, "tenant-a", ARGS)
    h2, ref2 = compute_args_hmac(provider, "tenant-a", ARGS)
    assert h1 == h2
    assert ref1 == ref2 == "v1"


def test_stesso_argomento_tenant_diversi_hmac_diversi():
    provider = StaticTestKeyProvider()
    provider.set_key("tenant-a", "v1", b"chiave-sintetica-a")
    provider.set_key("tenant-b", "v1", b"chiave-sintetica-b")
    h_a, _ = compute_args_hmac(provider, "tenant-a", ARGS)
    h_b, _ = compute_args_hmac(provider, "tenant-b", ARGS)
    assert h_a != h_b


def test_rotazione_due_chiavi_in_parallelo_vecchia_verificabile():
    provider = StaticTestKeyProvider()
    provider.set_key("tenant-a", "v1", b"chiave-sintetica-vecchia")
    old_hash, old_ref = compute_args_hmac(provider, "tenant-a", ARGS)
    assert old_ref == "v1"

    # sostituzione: v2 diventa corrente, v1 resta valida in parallelo (DA-CV-23)
    provider.set_key("tenant-a", "v2", b"chiave-sintetica-nuova", make_current=True)
    new_hash, new_ref = compute_args_hmac(provider, "tenant-a", ARGS)
    assert new_ref == "v2"
    assert new_hash != old_hash

    # l'hash prodotto con la chiave precedente resta verificabile finche' v1 esiste
    assert verify_args_hmac(provider, "tenant-a", "v1", ARGS, old_hash) is True


def test_dopo_distruzione_chiave_hash_non_ricalcolabile():
    provider = StaticTestKeyProvider()
    provider.set_key("tenant-a", "v1", b"chiave-sintetica-da-distruggere")
    old_hash, old_ref = compute_args_hmac(provider, "tenant-a", ARGS)

    provider.destroy_key("tenant-a", "v1")

    try:
        verify_args_hmac(provider, "tenant-a", old_ref, ARGS, old_hash)
        raised = False
    except HashUnavailableError:
        raised = True
    assert raised


def test_senza_chiave_valida_attributo_non_scritto_e_segnale(signal_sink, variables):
    provider = StaticTestKeyProvider()  # nessuna chiave per questo tenant
    helper = TracingHelper(variables, signal_sink, provider, production_override=False)
    result = helper.hash_tool_args("tenant-senza-chiave", ARGS)
    assert result is None
    assert "trace.args_hash_unavailable" in signal_sink.kinds()
