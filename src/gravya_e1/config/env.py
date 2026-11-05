"""Guardia di ambiente (invariante di deploy, catalogo §18, D2 (b)).

`API_ENV=production` e' l'unica costante ammessa fuori dal registro delle
variabili (vincolo 2 del task implementer E1): non e' una variabile di
piattaforma, e' un'invariante di deploy.
"""
from __future__ import annotations

import os


def is_production() -> bool:
    return os.environ.get("API_ENV") == "production"


def is_declared() -> bool:
    """Vero se `API_ENV` e' impostata (a qualunque valore).

    Non impostata: l'ambiente resta sviluppo (invariante decisa), ma
    l'helper deve avvisare con un segnale "ambiente non dichiarato"
    all'avvio (giro 2, rilievo minore del compliance-auditor).
    """
    return "API_ENV" in os.environ
