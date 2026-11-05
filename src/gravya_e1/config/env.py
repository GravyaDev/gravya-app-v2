"""Guardia di ambiente (invariante di deploy, catalogo §18, D2 (b)).

`API_ENV=production` e' l'unica costante ammessa fuori dal registro delle
variabili (vincolo 2 del task implementer E1): non e' una variabile di
piattaforma, e' un'invariante di deploy.
"""
from __future__ import annotations

import os


def is_production() -> bool:
    return os.environ.get("API_ENV") == "production"
