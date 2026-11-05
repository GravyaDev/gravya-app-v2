"""Prove del giro 5 (ultime correzioni dopo la verifica mirata del giro 4).

Ogni funzione qui prova un rilievo del task che non e' gia' coperto (o non e'
piu' coperto correttamente, per un bug nel file di prova bloccato) da
`docs/revisioni/impl-e1/code-reviewer-giro4/test_giro4.py`. Vedi report,
sezione "Giro 5", per il collegamento rilievo -> modifica -> test.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from _e1vars import snapshot_with
from gravya_e1 import whitelist as wl
from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
from gravya_e1.models import SegmentEnd
from gravya_e1.signals import InMemorySignalSink
from gravya_e1.tracing import TracingHelper

TEST_DB = "gravya_e1_test"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def _registry_with(tmp_path, overrides: dict) -> SnapshotVariableRegistry:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with(overrides)))
    return SnapshotVariableRegistry(signal_sink=InMemorySignalSink(), snapshot_path=path, production_override=True)


# --- V1: e1.write_tcp_user_timeout_ms tipizzata, minimo tecnico 1 ----------
# (code-reviewer-giro4/test_giro4.py::test_V1 ha un bug nel proprio fixture
# `_registry`: `SnapshotVariableRegistry(signal_sink=signal_sink, ...)` leggo
# la funzione di fixture del modulo (`FixtureFunctionDefinition`), non il
# parametro locale `sink` della funzione `_registry(sink, extra=None)` -> un
# refuso del file di prova, non del nostro codice: qualunque valore non
# valido che arrivi a `self._signal_sink.emit(...)` solleva `AttributeError`
# invece del comportamento che il test vuole verificare. Non e' un file
# modificabile oltre alla rinomina della variabile: riprovato qui.)


def test_tcp_user_timeout_valore_stringa_blocca_con_segnale_tipizzato(tmp_path):
    from gravya_e1.keys import StaticTestKeyProvider

    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_tcp_user_timeout_ms": {"value": "abc", "unit": "ms", "status": "deciso"}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, StaticTestKeyProvider(), production_override=True, conninfo=f"dbname={TEST_DB}")
    assert "e5.variable_invalid" in signal_sink.kinds()


def test_tcp_user_timeout_zero_blocca_con_segnale_invece_di_un_timer_immediato(tmp_path):
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_tcp_user_timeout_ms": {"value": 0, "unit": "ms", "status": "deciso"}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    from gravya_e1.keys import StaticTestKeyProvider

    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, StaticTestKeyProvider(), production_override=True, conninfo=f"dbname={TEST_DB}")
    assert "e5.variable_invalid" in signal_sink.kinds()


# --- V1 (regola relazionale, task correzione 4): tcp_user_timeout_ms >= statement_timeout_ms ---


def test_tcp_user_timeout_minore_dello_statement_timeout_blocca_con_segnale(tmp_path):
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({
        "e1.write_statement_timeout_ms": {"value": 5000, "unit": "ms", "status": "deciso"},
        "e1.write_tcp_user_timeout_ms": {"value": 1000, "unit": "ms", "status": "deciso"},
    })))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    from gravya_e1.keys import StaticTestKeyProvider

    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, StaticTestKeyProvider(), production_override=True, conninfo=f"dbname={TEST_DB}")
    assert "e5.variable_invalid" in signal_sink.kinds()


def test_tcp_user_timeout_uguale_allo_statement_timeout_e_valido(tmp_path, key_provider):
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({
        "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
        "e1.write_tcp_user_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
    })))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    helper = TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={TEST_DB}")
    try:
        assert "e5.variable_invalid" not in signal_sink.kinds()
    finally:
        helper.close(timeout=5)


# --- N11 (ora con la variabile rinominata): connect_timeout esatto, nessuna conversione ---
# (code-reviewer-giro3/test_giro3.py::test_N11 usa il vecchio nome
# `e1.write_connect_timeout_ms`, non piu' letto da nessuna parte dopo la
# rinomina di questo giro: diventa un fallito atteso, elencato nel report.
# Qui la stessa cosa con il nome nuovo.)


def test_connect_timeout_passato_esatto_senza_conversione(monkeypatch, tmp_path, key_provider):
    signal_sink = InMemorySignalSink()
    captured = {}

    def fake_connect(*a, **kw):
        captured.update(kw)
        raise psycopg.OperationalError("x")

    monkeypatch.setattr(psycopg, "connect", fake_connect)
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_connect_timeout_s": {"value": 7, "unit": "s", "status": "deciso", "min": 2}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    helper = TracingHelper(reg, signal_sink, key_provider, production_override=True, conninfo=f"dbname={TEST_DB}")
    from gravya_e1.models import SegmentStart

    helper.start_segment(
        None,
        SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), kind="agent",
                     started_at=NOW(), attributes={"gen_ai.agent.id": "agent_a"}),
    )
    helper.flush(3)
    helper.close(1)
    assert captured["connect_timeout"] == 7, captured["connect_timeout"]
    assert isinstance(captured["connect_timeout"], int), type(captured["connect_timeout"])


def test_connect_timeout_sotto_il_minimo_2_blocca_con_segnale(tmp_path):
    signal_sink = InMemorySignalSink()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_connect_timeout_s": {"value": 1, "unit": "s", "status": "deciso", "min": 2}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    with pytest.raises(VariableUnavailableError):
        reg.get("e1.write_connect_timeout_s")
    assert "e5.variable_invalid" in signal_sink.kinds()


# --- V2 (fatto di libpq/psycopg, non del nostro codice): il nostro codice non può più produrre un valore sotto 2s ---


def test_il_nostro_codice_non_passa_mai_meno_di_2_secondi_a_connect_timeout(tmp_path, key_provider):
    """V2 di code-reviewer-giro4/test_giro4.py dimostra un fatto di libpq
    (connect_timeout sotto 1s non onorato), chiamando `psycopg.connect`
    direttamente, non il nostro codice. Dopo la rinomina (minimo tecnico 2,
    intero, nessuna conversione) il NOSTRO codice non può più produrre un
    valore sotto 2: lo proviamo leggendo l'istantanea reale di sviluppo
    (`config/e5-snapshot.json`, non un'istantanea ad-hoc) e verificando che
    il minimo dichiarato sia effettivamente 2."""
    from gravya_e1.config.variables import SnapshotVariableRegistry as Reg

    signal_sink = InMemorySignalSink()
    reg = Reg(signal_sink=signal_sink)  # istantanea reale di sviluppo
    value = reg.get("e1.write_connect_timeout_s")
    assert value.value >= 2, "il valore di sviluppo di e1.write_connect_timeout_s e' sotto il minimo tecnico effettivo (2)"
    with pytest.raises(VariableUnavailableError):
        _registry_with(tmp_path, {"e1.write_connect_timeout_s": {"value": 1, "unit": "s", "status": "deciso", "min": 2}}).get(
            "e1.write_connect_timeout_s"
        )


# --- S3: il campo `kind` di un segnale di scarto non è più testo libero del chiamante ---


def test_kind_arbitrario_diventa_un_segnaposto_nel_segnale(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    helper = make_helper(variables, signal_sink, key_provider, production_override=True)
    sentinel = "Il cliente Mario Rossi chiede il rimborso SENTINELLA-GIRO5"
    helper.end_segment(None, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"), sentinel)
    assert helper.flush(timeout=5)
    kinds_reported = [s.payload.get("kind") for s in signal_sink.signals if s.kind == "trace.segment_attribute_discarded"]
    assert kinds_reported, "nessun segnale di scarto osservato"
    assert all(sentinel not in str(k) for k in kinds_reported), kinds_reported
    assert all(k == wl.safe_signal_kind(sentinel) for k in kinds_reported)


def test_kind_noto_resta_riportato_per_intero(wl=wl):
    assert wl.safe_signal_kind("agent") == "agent"
    assert wl.safe_signal_kind("_field") == "_field"
    assert wl.safe_signal_kind("testo libero arbitrario") != "testo libero arbitrario"


# --- Decisione dell'utente: API_ENV fuori insieme chiuso blocca l'avvio ----
# (gia' provato in tests/test_giro4_misc.py::test_api_env_fuori_insieme_chiuso_blocca_l_avvio_con_segnale,
# aggiornato in questo giro per la nuova decisione)
