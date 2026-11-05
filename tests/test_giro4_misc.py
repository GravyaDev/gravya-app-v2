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


# --- G3-04 / giro 5 (decisione dell'utente): API_ENV fuori insieme chiuso --
# Giro 5: l'avvio SI BLOCCA (decisione dell'utente, ribalta la scelta del
# giro 4): test_R15b di code-reviewer/ diventa fallito atteso per questa
# stessa decisione (vedi report, sezione "Giro 5").


def test_api_env_fuori_insieme_chiuso_blocca_l_avvio_con_segnale(monkeypatch, variables, signal_sink, key_provider):
    from gravya_e1.tracing import EnvironmentInvalidError

    monkeypatch.setenv("API_ENV", "Production")  # fuori insieme chiuso (non e' "production" esatto)
    with pytest.raises(EnvironmentInvalidError):
        TracingHelper(variables, signal_sink, key_provider, tenant_context=str(uuid.uuid4()))
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


def test_segnale_con_connessione_propria_bloccata_il_chiamante_non_aspetta(variables, key_provider, admin_conn, ensure_partitions_now):
    """Giro 5 (correzione 2, S1): il thread dei segnali usa una connessione
    PROPRIA (stesso `conninfo` della scrittura, non quella data dal
    chiamante a `PostgresSignalSink`, giro 5): se quella connessione si
    blocca dopo essere stata stabilita, il chiamante non deve aspettare."""
    import os

    reason = tcp_ok()
    if reason:
        pytest.skip(reason)
    proxy = FreezableProxy()
    user = os.environ.get("PGUSER") or "root"
    sink = PostgresSignalSink(admin_conn)  # "marcatore di tipo": non e' piu' la connessione usata per scrivere
    helper = TracingHelper(
        variables, sink, key_provider, production_override=True,
        conninfo=f"host=127.0.0.1 port={proxy.port} user={user} dbname={TEST_DB}",
    )
    try:
        # prima emissione: stabilisce la connessione propria (rete non ancora bloccata)
        helper.end_segment(
            None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"),
            "kind_sconosciuto_bogus",
        )
        assert helper.flush(timeout=5)
        proxy.frozen = True
        t0 = time.perf_counter()
        for _ in range(30):
            helper.end_segment(
                None,
                SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"),
                "kind_sconosciuto_bogus",
            )  # kind sconosciuto in produzione: scarto con segnale (trace.segment_attribute_discarded)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"il chiamante ha aspettato {elapsed:.2f}s con la connessione dei segnali bloccata"
    finally:
        proxy.frozen = False
        helper.close(timeout=10)


def test_segnale_scritto_con_connessione_propria_non_con_quella_del_chiamante(admin_conn, variables, key_provider, ensure_partitions_now, make_helper):
    """Giro 5 (correzione 2, S1): la connessione data a `PostgresSignalSink`
    non e' piu' usata per scrivere (solo un marcatore "voglio un sink
    Postgres", riconosciuto per tipo): anche se e' gia' chiusa, il segnale
    arriva comunque, scritto con la connessione propria dell'helper
    (`conninfo`, come per le scritture)."""
    from _pgconn import pg_dsn

    broken = psycopg.connect(pg_dsn(TEST_DB))
    broken.close()
    sink = PostgresSignalSink(broken)
    tenant_id = uuid.uuid4()
    helper = make_helper(variables, sink, key_provider, production_override=True)
    helper.end_segment(
        None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=tenant_id, ended_at=NOW(), status="ok"),
        "kind_sconosciuto_bogus",
    )
    assert helper.flush(timeout=5)
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_signals_min_audit WHERE tenant_id=%s", (str(tenant_id),))
        assert cur.fetchone() is not None, "il segnale non e' stato scritto: la connessione propria dell'helper non e' stata usata"


def test_segnale_si_riconnette_dopo_un_errore(admin_conn, variables, key_provider, ensure_partitions_now, make_helper):
    """Giro 5 (correzione 2, S2): dopo un errore sulla connessione propria dei
    segnali (qui simulato chiudendola a mano), l'emissione successiva
    riesce lo stesso (riconnessione), non resta bloccata in una transazione
    fallita."""
    sink = PostgresSignalSink(admin_conn)  # mai usata per scrivere (vedi sopra)
    helper = make_helper(variables, sink, key_provider, production_override=True)
    tenant_id = uuid.uuid4()
    helper.end_segment(
        None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=tenant_id, ended_at=NOW(), status="ok"),
        "kind_sconosciuto_bogus",
    )
    assert helper.flush(timeout=5)
    # chiude a mano la connessione propria dei segnali: la prossima emissione deve riconnettersi da sola
    helper._force_disconnect(helper._own_signal_conn)
    tenant_id2 = uuid.uuid4()
    helper.end_segment(
        None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=tenant_id2, ended_at=NOW(), status="ok"),
        "kind_sconosciuto_bogus",
    )
    assert helper.flush(timeout=10)
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_signals_min_audit WHERE tenant_id=%s", (str(tenant_id2),))
        assert cur.fetchone() is not None, "il segnale dopo la riconnessione non e' stato scritto"
