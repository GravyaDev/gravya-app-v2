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


def test_variabile_assente_blocca_e_segnala(tmp_path, signal_sink):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"variables": {}}))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    with pytest.raises(VariableUnavailableError):
        reg.get("e1.partition_interval_months")
    assert "e5.variable_unreadable" in signal_sink.kinds()


def test_valore_non_intero_e_bloccato_e_segnalato(tmp_path, signal_sink):
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps({"variables": {"x.y": {"value": "non-numerico", "unit": "ms", "status": "deciso"}}})
    )
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path)
    with pytest.raises(VariableUnavailableError):
        reg.get("x.y")
    assert "e5.variable_invalid" in signal_sink.kinds()


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
    assert helper._write_buffer_size == 100  # valore di sviluppo dichiarato nell'istantanea
    assert helper._max_value_bytes == 2048


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
