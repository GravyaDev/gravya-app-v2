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
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry
from gravya_e1.models import SegmentEnd
from gravya_e1.signals import PostgresSignalSink
from gravya_e1.tracing import TenantContextRequiredError, TracingHelper

from _e1vars import snapshot_with
from _freezable_proxy import FreezableProxy, tcp_ok

TEST_DB = "gravya_e1_test"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


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


# --- G3-04 (decisione del coordinator): API_ENV fuori insieme chiuso -------
# Non blocca l'avvio (contraddirebbe test_R15b, bloccato dal giro 1: solo
# "production" esatto conta), ma emette un segnale distinto.


def test_api_env_fuori_insieme_chiuso_non_blocca_ma_segnala(monkeypatch, variables, signal_sink, key_provider, make_helper):
    monkeypatch.setenv("API_ENV", "Production")  # fuori insieme chiuso (non e' "production" esatto)
    helper = make_helper(variables, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
    assert helper is not None
    assert "e5.environment_invalid" in signal_sink.kinds()


def test_api_env_valore_noto_non_segnala_invalido(monkeypatch, variables, signal_sink, key_provider, make_helper):
    monkeypatch.setenv("API_ENV", "development")
    helper = make_helper(variables, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
    assert helper is not None
    assert "e5.environment_invalid" not in signal_sink.kinds()


def test_api_env_assente_non_segnala_invalido_solo_non_dichiarato(signal_sink, key_provider, make_helper, variables):
    helper = make_helper(variables, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
    assert helper is not None
    assert "e5.environment_invalid" not in signal_sink.kinds()
    assert "e5.environment_undeclared" in signal_sink.kinds()


# --- G3-01: i segnali passano da una coda/thread propri, il chiamante non aspetta ---


def test_segnale_con_sink_bloccato_il_chiamante_non_aspetta(variables, key_provider, make_helper, admin_conn, ensure_partitions_now):
    """Giro 4 (CA G3-01): un `PostgresSignalSink` la cui connessione si blocca
    dopo essere stata stabilita (stessa tecnica di
    code-reviewer-giro3/test_giro3.py::test_N1/N2, qui sul sink dei segnali,
    non sulla scrittura) non deve far aspettare il chiamante: i segnali
    passano da una coda e un thread di sfondo propri (separati dalle
    scritture)."""
    if not tcp_ok():
        pytest.skip("TCP non disponibile")
    proxy = FreezableProxy()
    sink_conn = psycopg.connect(f"host=127.0.0.1 port={proxy.port} user=root dbname={TEST_DB}")
    sink = PostgresSignalSink(sink_conn)
    helper = make_helper(variables, sink, key_provider, production_override=True)
    try:
        proxy.frozen = True
        t0 = time.perf_counter()
        for _ in range(30):
            helper.end_segment(
                None,
                SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"),
                "kind_sconosciuto_bogus",
            )  # kind sconosciuto in produzione: scarto con segnale (trace.segment_attribute_discarded)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"il chiamante ha aspettato {elapsed:.2f}s con il sink dei segnali bloccato"
    finally:
        proxy.frozen = False
        sink_conn.close()
