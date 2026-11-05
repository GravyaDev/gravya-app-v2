"""Interfaccia unica di lettura delle variabili di piattaforma (E5, DA-A1-10).

Finche' A6 non esiste, le variabili si leggono da un'istantanea versionata nel
repository (config/e5-snapshot.json), tramite questa sola interfaccia condivisa
(DX-13, DX-22). Nessun'altra parte del codice deve leggere il file
direttamente o duplicare un valore come costante (DX-22, vincolo 2 del task
implementer E1).

Comportamento (E1 §5, DX-17):
- variabile assente dalla istantanea, o valore non valido tecnicamente:
  azione bloccata (`VariableUnavailableError`) e segnale ad A5.
- stato "proposta_da_validare": il valore vale come primo valore valido,
  con un segnale.
- stato "da_definire": valore di sviluppo ammesso solo fuori produzione
  (`API_ENV=production`); con la guardia di produzione attiva, la lettura
  fallisce (blocca l'avvio dell'helper).

Giro 2 (CR R18, CA 12): l'istantanea puo' essere malformata in piu' punti
(non un oggetto, 'variables' non un oggetto, una voce non un oggetto): ogni
caso blocca con `VariableUnavailableError` tipizzato e un segnale, mai
un'eccezione non gestita (`AttributeError`/`TypeError`). L'interfaccia
accetta anche valori booleani e stringhe di vocabolario, non solo interi
positivi (CR 12).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Union

from gravya_e1.config.env import is_production
from gravya_e1.signals import SignalSink

DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "config" / "e5-snapshot.json"

_VALID_STATUSES = {"deciso", "proposta_da_validare", "da_definire"}

VariableScalar = Union[int, bool, str]


class VariableUnavailableError(RuntimeError):
    """Variabile non leggibile, non valida, o 'da definire' in produzione (DX-17)."""


@dataclass(frozen=True)
class VariableValue:
    name: str
    value: VariableScalar
    unit: str
    status: str
    dev_only: bool


class VariableRegistry(Protocol):
    def get(self, name: str) -> VariableValue:
        ...


class SnapshotVariableRegistry:
    """Implementazione di E5: legge `config/e5-snapshot.json`."""

    def __init__(
        self,
        signal_sink: SignalSink,
        snapshot_path: Path | None = None,
        *,
        production_override: bool | None = None,
    ) -> None:
        self._signal_sink = signal_sink
        self._path = snapshot_path or DEFAULT_SNAPSHOT_PATH
        self._production_override = production_override
        self._proposal_signalled: set[str] = set()
        self._raw = self._load()

    def _load(self) -> dict:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            self._signal_sink.emit(
                "e5.snapshot_unreadable",
                reason=str(exc),
                path=str(self._path),
            )
            raise VariableUnavailableError(f"istantanea E5 non leggibile: {exc}") from exc

        if not isinstance(data, dict):
            self._signal_sink.emit(
                "e5.snapshot_unreadable", reason="l'istantanea non e' un oggetto JSON", path=str(self._path)
            )
            raise VariableUnavailableError("istantanea E5 malformata: atteso un oggetto JSON")

        variables = data.get("variables", {})
        if not isinstance(variables, dict):
            self._signal_sink.emit(
                "e5.snapshot_unreadable", reason="'variables' non e' un oggetto", path=str(self._path)
            )
            raise VariableUnavailableError("istantanea E5 malformata: 'variables' deve essere un oggetto")
        return variables

    def _is_production(self) -> bool:
        if self._production_override is not None:
            return self._production_override
        return is_production()

    def get(self, name: str) -> VariableValue:
        entry = self._raw.get(name)
        if entry is None:
            self._signal_sink.emit("e5.variable_unreadable", name=name, reason="assente dall'istantanea")
            raise VariableUnavailableError(f"variabile '{name}' assente dall'istantanea E5")
        if not isinstance(entry, dict):
            self._signal_sink.emit("e5.variable_unreadable", name=name, reason="voce malformata nell'istantanea")
            raise VariableUnavailableError(f"variabile '{name}' malformata nell'istantanea E5")

        status = entry.get("status")
        if status not in _VALID_STATUSES:
            self._signal_sink.emit(
                "e5.variable_invalid", name=name, reason=f"stato non riconosciuto: {status!r}"
            )
            raise VariableUnavailableError(f"variabile '{name}' con stato non riconosciuto: {status!r}")

        if status == "da_definire" and self._is_production():
            self._signal_sink.emit(
                "e5.variable_unreadable",
                name=name,
                reason="variabile 'da definire' assente in produzione",
            )
            raise VariableUnavailableError(
                f"variabile '{name}' e' 'da definire': non ammessa in produzione (avvio bloccato)"
            )

        value = self._validate_scalar(name, entry)

        if isinstance(value, int) and not isinstance(value, bool):
            minimum = entry.get("min")
            maximum = entry.get("max")
            if minimum is not None and value < minimum:
                self._signal_sink.emit("e5.variable_invalid", name=name, reason="valore sotto il minimo")
                raise VariableUnavailableError(f"variabile '{name}' sotto il minimo ({value} < {minimum})")
            if maximum is not None and value > maximum:
                self._signal_sink.emit("e5.variable_invalid", name=name, reason="valore sopra il massimo")
                raise VariableUnavailableError(f"variabile '{name}' sopra il massimo ({value} > {maximum})")

        if status == "proposta_da_validare" and name not in self._proposal_signalled:
            self._proposal_signalled.add(name)
            self._signal_sink.emit(
                "e5.variable_proposed_value_in_use",
                name=name,
                reason="valore 'proposta da validare' usato come primo valore valido",
            )

        return VariableValue(
            name=name,
            value=value,
            unit=entry.get("unit", ""),
            status=status,
            dev_only=bool(entry.get("dev_only", False)),
        )

    def _validate_scalar(self, name: str, entry: dict) -> VariableScalar:
        raw_value = entry.get("value")
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, int):
            if raw_value < 0:
                self._signal_sink.emit(
                    "e5.variable_invalid", name=name, reason="valore negativo non valido tecnicamente"
                )
                raise VariableUnavailableError(f"variabile '{name}' con valore negativo: {raw_value!r}")
            return raw_value
        if isinstance(raw_value, str) and raw_value != "":
            return raw_value
        self._signal_sink.emit(
            "e5.variable_invalid",
            name=name,
            reason="valore non valido tecnicamente (intero non negativo, booleano o stringa non vuota attesi)",
        )
        raise VariableUnavailableError(f"variabile '{name}' con valore non valido: {raw_value!r}")
