"""Criterio 17: variabili prima di A6 (E5).

Con l'ambiente di sviluppo l'helper parte con i valori di sviluppo
dell'istantanea per le variabili "da definire"; con la guardia di produzione
attiva l'avvio fallisce se una variabile "da definire" manca.
"""
from __future__ import annotations

import json

import pytest

from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
from gravya_e1.keys import StaticTestKeyProvider
from gravya_e1.signals import InMemorySignalSink
from gravya_e1.tracing import TracingHelper

from _e1vars import snapshot_with


def test_variabile_assente_blocca_e_segnala(tmp_path, signal_sink):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"variables": {}}))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    with pytest.raises(VariableUnavailableError):
        reg.get("e1.partition_interval_months")
    assert "e5.variable_unreadable" in signal_sink.kinds()


def test_valore_negativo_e_bloccato_e_segnalato(tmp_path, signal_sink):
    # Giro 2 (CR 12): l'interfaccia accetta anche stringhe di vocabolario e
    # booleani, non solo interi positivi; resta non valido un intero
    # negativo (B3/CR 12: 0 e' tecnicamente valido, un negativo no).
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"variables": {"x.y": {"value": -5, "unit": "ms", "status": "deciso"}}}))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    with pytest.raises(VariableUnavailableError):
        reg.get("x.y")
    assert "e5.variable_invalid" in signal_sink.kinds()


def test_valore_di_tipo_non_supportato_e_bloccato_e_segnalato(tmp_path, signal_sink):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"variables": {"x.y": {"value": [1, 2], "unit": "ms", "status": "deciso"}}}))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    with pytest.raises(VariableUnavailableError):
        reg.get("x.y")
    assert "e5.variable_invalid" in signal_sink.kinds()


def test_valore_booleano_e_stringa_di_vocabolario_sono_validi(tmp_path, signal_sink):
    # Giro 2 (CR 12): l'interfaccia non gestiva booleani ne' vocabolari di
    # stringa; ora li accetta.
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            {
                "variables": {
                    "incident.nis2_flow_active": {"value": False, "unit": "", "status": "deciso"},
                    "retention.tenant_offboarding_choice": {"value": "export", "unit": "", "status": "deciso"},
                }
            }
        )
    )
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    assert reg.get("incident.nis2_flow_active").value is False
    assert reg.get("retention.tenant_offboarding_choice").value == "export"


def test_proposta_da_validare_vale_come_primo_valore_con_segnale(variables, signal_sink):
    value = variables.get("e1.partition_interval_months")
    assert value.value == 1
    assert "e5.variable_proposed_value_in_use" in signal_sink.kinds()


def test_helper_parte_in_sviluppo_con_valori_di_sviluppo(variables, signal_sink):
    helper = TracingHelper(
        variables=variables,
        signal_sink=signal_sink,
        key_provider=StaticTestKeyProvider(),
        production_override=False,
    )
    try:
        assert helper._write_buffer_size == 100  # valore di sviluppo dichiarato nell'istantanea
        assert helper._max_value_bytes == 2048
        assert helper._write_statement_timeout_ms == 2000  # giro 3: e1.write_statement_timeout_ms
        assert helper._write_connect_timeout_s == 2
        assert helper._keepalives_idle_s == 10
        assert helper._keepalives_interval_s == 5
        assert helper._keepalives_count == 3
    finally:
        helper.close()


def test_helper_non_parte_in_produzione_senza_variabile_da_definire(signal_sink):
    prod_vars = SnapshotVariableRegistry(signal_sink=signal_sink, production_override=True)
    with pytest.raises(VariableUnavailableError):
        TracingHelper(
            variables=prod_vars,
            signal_sink=signal_sink,
            key_provider=StaticTestKeyProvider(),
            production_override=True,
        )
    assert "e5.variable_unreadable" in signal_sink.kinds()


def test_helper_non_parte_in_produzione_senza_write_statement_timeout_ms(tmp_path, signal_sink):
    # Giro 3: e1.write_statement_timeout_ms ha lo stesso trattamento di
    # e1.write_buffer_size/e1.attributes.max_value_bytes (DX-22): qui le
    # altre variabili sono "deciso" (valide) apposta, cosi' il blocco in
    # produzione si osserva proprio sulla nuova variabile "da definire".
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            snapshot_with(
                {
                    "e1.write_statement_timeout_ms": {
                        "value": 2000,
                        "unit": "ms",
                        "status": "da_definire",
                        "dev_only": True,
                    }
                }
            )
        )
    )
    prod_vars = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=True)
    with pytest.raises(VariableUnavailableError):
        TracingHelper(
            variables=prod_vars,
            signal_sink=signal_sink,
            key_provider=StaticTestKeyProvider(),
            production_override=True,
        )
    assert "e5.variable_unreadable" in signal_sink.kinds()

    # fuori produzione, la stessa istantanea parte con il valore di sviluppo.
    dev_vars = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=False)
    helper = TracingHelper(
        variables=dev_vars,
        signal_sink=signal_sink,
        key_provider=StaticTestKeyProvider(),
        production_override=False,
    )
    try:
        assert helper._write_statement_timeout_ms == 2000
    finally:
        helper.close()
