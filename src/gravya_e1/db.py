"""Connessioni: ruolo writer senza bypass di RLS, tenant impostato per transazione.

DA-E1-10 (a). `WRITER_ROLE` e il nome del GUC di sessione sono invarianti di
codice (come i nomi degli header di correlazione), non variabili di
piattaforma: non passano dall'istantanea E5.
"""
from __future__ import annotations

from contextlib import contextmanager

import psycopg

WRITER_ROLE = "gravya_writer"
TENANT_GUC = "app.tenant_id"


@contextmanager
def writer_transaction(conn: psycopg.Connection, tenant_id: str):
    """Apre una transazione come `gravya_writer` con il tenant impostato.

    `conn` deve essere una connessione admin con il permesso di `SET ROLE` a
    `gravya_writer` (grant di membership, vedi migrazione 0002). Il
    cambio di ruolo e del GUC del tenant valgono solo per la transazione
    (`SET LOCAL`), cosi' RLS si applica con l'identita' del writer, non con
    quella del superuser/admin (vincolo 7 del task implementer).
    """
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL ROLE {WRITER_ROLE}")
            cur.execute("SELECT set_config(%s, %s, true)", (TENANT_GUC, str(tenant_id)))
        yield conn
