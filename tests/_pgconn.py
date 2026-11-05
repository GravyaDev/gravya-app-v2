"""Costruzione delle stringhe di connessione per i test (CR, "DSN fissi nei test").

Tutti i test leggono `GRAVYA_E1_TEST_DSN` o le variabili PG* standard
(`PGHOST`, `PGPORT`, `PGUSER`), invece di un socket Unix fisso o un ruolo
`root` scritto come stringa letterale: cosi' la stessa suite gira anche con
`PGHOST=127.0.0.1` (TCP, come nella CI). Il ruolo di sviluppo locale
(superuser, autenticazione peer, creato una volta per il giro 1) resta il
valore di default di `PGUSER` solo se non e' impostata nessuna variabile
d'ambiente: non e' un segreto, e' un nome di ruolo locale non in produzione.
"""
from __future__ import annotations

import os


def pg_dsn(dbname: str) -> str:
    override = os.environ.get("GRAVYA_E1_TEST_DSN")
    if override:
        return f"{override} dbname={dbname}"
    parts = []
    host = os.environ.get("PGHOST")
    if host:
        parts.append(f"host={host}")
    port = os.environ.get("PGPORT")
    if port:
        parts.append(f"port={port}")
    parts.append(f"user={os.environ.get('PGUSER', 'root')}")
    parts.append(f"dbname={dbname}")
    return " ".join(parts)


def pg_dsn_no_db() -> str:
    override = os.environ.get("GRAVYA_E1_TEST_DSN")
    if override:
        return override
    parts = []
    host = os.environ.get("PGHOST")
    if host:
        parts.append(f"host={host}")
    port = os.environ.get("PGPORT")
    if port:
        parts.append(f"port={port}")
    parts.append(f"user={os.environ.get('PGUSER', 'root')}")
    return " ".join(parts)


def alembic_database_url(dbname: str) -> str:
    user = os.environ.get("PGUSER", "root")
    host = os.environ.get("PGHOST")
    port = os.environ.get("PGPORT")
    netloc = user
    if host:
        netloc += f"@{host}"
        if port:
            netloc += f":{port}"
    else:
        netloc += "@"
    override = os.environ.get("GRAVYA_E1_TEST_DSN")
    if override:
        # GRAVYA_E1_TEST_DSN e' nel formato chiave=valore di libpq: lo si
        # riusa solo per host/porta/utente, il resto (incluso il database)
        # resta esplicito qui.
        from psycopg.conninfo import conninfo_to_dict

        parsed = conninfo_to_dict(override)
        user = parsed.get("user", user)
        host = parsed.get("host", host)
        port = parsed.get("port", port)
        netloc = user
        if host:
            netloc += f"@{host}"
            if port:
                netloc += f":{port}"
        else:
            netloc += "@"
    return f"postgresql+psycopg://{netloc}/{dbname}"
