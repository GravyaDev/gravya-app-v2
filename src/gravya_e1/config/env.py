"""Guardia di ambiente (invariante di deploy, catalogo §18, D2 (b)).

`API_ENV=production` e' l'unica costante ammessa fuori dal registro delle
variabili (vincolo 2 del task implementer E1): non e' una variabile di
piattaforma, e' un'invariante di deploy.
"""
from __future__ import annotations

import os

# Giro 4 (CA G3-04, decisione del coordinator): insieme chiuso dei valori
# ammessi di `API_ENV`. Un valore impostato ma fuori da questo insieme (per
# esempio "Production", "prod") NON blocca l'avvio (bloccarlo contraddirebbe
# `test_R15b_informativo_guardia_solo_valore_esatto_production`, bloccato dal
# giro 1: un valore diverso da "production" esatto resta trattato come
# sviluppo, decisione gia' presa): emette un segnale distinto
# (`e5.environment_invalid`, vedi `tracing.py`), nient'altro.
VALID_API_ENV_VALUES = frozenset({"production", "development", "test"})


def is_production() -> bool:
    return os.environ.get("API_ENV") == "production"


def is_declared() -> bool:
    """Vero se `API_ENV` e' impostata (a qualunque valore).

    Non impostata: l'ambiente resta sviluppo (invariante decisa), ma
    l'helper deve avvisare con un segnale "ambiente non dichiarato"
    all'avvio (giro 2, rilievo minore del compliance-auditor).
    """
    return "API_ENV" in os.environ


def is_declared_value_valid() -> bool:
    """Vero se `API_ENV` non e' impostata, oppure e' impostata a un valore
    dell'insieme chiuso (giro 4, G3-04). Non influisce su `is_production()`:
    resta `API_ENV == "production"` esatto, invariato."""
    value = os.environ.get("API_ENV")
    return value is None or value in VALID_API_ENV_VALUES
