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

Giro 3 (G13): le variabili elencate in `_EXPECTED_INT_VARIABLES` devono
essere intere (un valore di tipo sbagliato blocca con segnale, mai un
`TypeError`); `min`/`max` non numerici bloccano allo stesso modo (mai un
confronto che solleva un'eccezione); nessuna correzione silenziosa come
`max(1, valore)`.

Giro 3 (G9): `production_override` puo' solo irrigidire la guardia di
produzione (`is_production() or override`), mai spegnerla: con
`API_ENV=production` nell'ambiente, nessun valore di `production_override`
puo' far accettare una variabile "da definire".

Giro 5 (CR V1, decisione dell'utente). `e1.write_tcp_user_timeout_ms` e'
ora in `_EXPECTED_INT_VARIABLES` (prima mancava: un'istantanea senza `min`
accettava 0, e una stringa sollevava `TypeError` invece di un errore
tipizzato). `e1.write_connect_timeout_ms` e' rinominata
`e1.write_connect_timeout_s` (intero, minimo tecnico effettivo 2 tramite
`min` nell'istantanea: libpq legge secondi interi e tratta valori sotto 2
come 2, e 0 come attesa infinita); `TracingHelper` non la converte piu'.
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

# Variabili di E1 il cui tipo atteso e' un intero (giro 3, G13): un valore
# di un altro tipo (stringa, lista, ecc.) blocca con segnale invece di
# propagare un TypeError piu' avanti nel codice (per esempio in
# threading.BoundedSemaphore). Le variabili non elencate qui mantengono la
# tipizzazione dinamica (intero non negativo, booleano o stringa non vuota),
# usata per esempio da variabili non ancora consumate da E1 nei test.
_EXPECTED_INT_VARIABLES = frozenset(
    {
        "e1.partition_interval_months",
        "e1.overhead_p95_ms",
        "e1.write_buffer_size",
        "e1.attributes.max_value_bytes",
        "e1.write_statement_timeout_ms",
        "e1.write_connect_timeout_s",
        "e1.write_tcp_keepalives_idle_s",
        "e1.write_tcp_keepalives_interval_s",
        "e1.write_tcp_keepalives_count",
        "e1.write_tcp_user_timeout_ms",
    }
)


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
        # Giro 3 (G9): l'override puo' solo irrigidire la guardia, mai
        # spegnerla: is_production() or override (mai "override" da solo).
        if self._production_override:
            return True
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
            if minimum is not None:
                if not isinstance(minimum, int) or isinstance(minimum, bool):
                    self._signal_sink.emit("e5.variable_invalid", name=name, reason="minimo non numerico")
                    raise VariableUnavailableError(f"variabile '{name}' con minimo non numerico: {minimum!r}")
                if value < minimum:
                    self._signal_sink.emit("e5.variable_invalid", name=name, reason="valore sotto il minimo")
                    raise VariableUnavailableError(f"variabile '{name}' sotto il minimo ({value} < {minimum})")
            if maximum is not None:
                if not isinstance(maximum, int) or isinstance(maximum, bool):
                    self._signal_sink.emit("e5.variable_invalid", name=name, reason="massimo non numerico")
                    raise VariableUnavailableError(f"variabile '{name}' con massimo non numerico: {maximum!r}")
                if value > maximum:
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

        if name in _EXPECTED_INT_VARIABLES:
            if not isinstance(raw_value, int) or isinstance(raw_value, bool):
                self._signal_sink.emit(
                    "e5.variable_invalid", name=name, reason="tipo atteso intero"
                )
                raise VariableUnavailableError(f"variabile '{name}' deve essere un intero: {raw_value!r}")
            # Le variabili di E1 elencate qui sono tutte conteggi/durate: il
            # minimo tecnico e' 1 come invariante di codice (giro 3, G13;
            # catalogo: "validita' tecnica"), non dipende da un campo "min"
            # facoltativo nell'istantanea (che potrebbe mancare o essere
            # sbagliato in una voce specifica). Se l'istantanea dichiara un
            # proprio "min" esplicito, il controllo qui sotto E il controllo
            # su `entry.get("min")` in `get()` si applicano entrambi in
            # sequenza: vale il piu' restrittivo dei due (1, o il "min"
            # dichiarato se superiore a 1).
            if raw_value < 1:
                self._signal_sink.emit(
                    "e5.variable_invalid", name=name, reason="valore sotto il minimo tecnico (1)"
                )
                raise VariableUnavailableError(f"variabile '{name}' sotto il minimo tecnico: {raw_value!r}")
            return raw_value

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
