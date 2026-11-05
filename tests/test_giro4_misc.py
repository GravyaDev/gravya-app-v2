"""Prove del giro 4: correzione richiesta dal coordinator su `tenant_context`.

`tenant_context` e' obbligatorio solo sotto la guardia di produzione REALE
(`API_ENV=production`, letta da `is_production()`): senza contesto in quel
caso `TracingHelper.__init__` deve fallire con un segnale.
`production_override=True` da solo (produzione "simulata" usata dai test di
riproduzione dei revisori) NON attiva questo obbligo: scelta esplicita del
coordinator, vedi report sezione "Giro 3" (nota in coda) perche' i pacchetti
fissi dei revisori costruiscono l'helper con `production_override=True` senza
`tenant_context` in oltre 25 casi che non si possono modificare.
"""
from __future__ import annotations

import json
import uuid

import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.tracing import TenantContextRequiredError, TracingHelper

from _e1vars import snapshot_with


def _prod_registry(tmp_path, signal_sink):
    """Istantanea con tutte le variabili 'deciso' (nessuna 'da definire'),
    cosi' il blocco di produzione osservato nei test e' quello del
    tenant_context, non quello (gia' provato altrove) delle variabili di
    scrittura non ancora decise."""
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with()))
    return SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)


def test_api_env_production_senza_tenant_context_blocca_l_avvio_con_segnale(monkeypatch, tmp_path, signal_sink, key_provider):
    """API_ENV=production reale, nessun tenant_context: __init__ deve sollevare
    e deve aver emesso il segnale trace.tenant_context_absent."""
    monkeypatch.setenv("API_ENV", "production")
    prod_vars = _prod_registry(tmp_path, signal_sink)
    with pytest.raises(TenantContextRequiredError):
        TracingHelper(prod_vars, signal_sink, key_provider)
    events = [e for e in signal_sink.signals if e.kind == "trace.tenant_context_absent"]
    assert len(events) == 1
    assert events[0].payload["reason"] == "tenant_context_absent_bloccante"


def test_api_env_production_con_tenant_context_si_avvia(monkeypatch, tmp_path, signal_sink, key_provider, make_helper):
    """API_ENV=production reale, tenant_context dato: l'avvio deve riuscire e
    non deve emettere il segnale di assenza del contesto."""
    monkeypatch.setenv("API_ENV", "production")
    prod_vars = _prod_registry(tmp_path, signal_sink)
    helper = make_helper(prod_vars, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
    assert helper is not None
    assert not [e for e in signal_sink.signals if e.kind == "trace.tenant_context_absent"]


def test_production_override_true_senza_tenant_context_non_blocca_ma_segnala(variables, signal_sink, key_provider, make_helper):
    """Fuori da API_ENV=production reale, production_override=True da solo
    (produzione "simulata") non attiva l'obbligo: l'avvio riesce, ma emette il
    segnale informativo (non bloccante)."""
    helper = make_helper(variables, signal_sink, key_provider, production_override=True)
    assert helper is not None
    events = [e for e in signal_sink.signals if e.kind == "trace.tenant_context_absent"]
    assert len(events) == 1
    assert events[0].payload["reason"] == "tenant_context_absent_informativo"


def test_fuori_produzione_senza_tenant_context_si_avvia_con_segnale_informativo(variables, signal_sink, key_provider, make_helper):
    """Sviluppo (nessun API_ENV, nessun override), nessun tenant_context:
    l'avvio riesce comunque (compatibilita' coi chiamanti multi-tenant), ma
    emette il segnale informativo."""
    helper = make_helper(variables, signal_sink, key_provider)
    assert helper is not None
    events = [e for e in signal_sink.signals if e.kind == "trace.tenant_context_absent"]
    assert len(events) == 1
    assert events[0].payload["reason"] == "tenant_context_absent_informativo"


def test_con_tenant_context_nessun_segnale_di_assenza_fuori_produzione(variables, signal_sink, key_provider, make_helper):
    """Con tenant_context dato, il segnale di assenza non deve comparire
    nemmeno fuori produzione."""
    helper = make_helper(variables, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
    assert helper is not None
    assert not [e for e in signal_sink.signals if e.kind == "trace.tenant_context_absent"]
