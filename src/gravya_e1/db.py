"""Connessioni: ruolo writer senza bypass di RLS, tenant impostato per transazione.

DA-E1-10 (a). `WRITER_ROLE` e il nome del GUC di sessione sono invarianti di
codice (come i nomi degli header di correlazione), non variabili di
piattaforma: non passano dall'istantanea E5.

Giro 2 (B5, CR R13). Se la connessione del chiamante ha gia' una transazione
aperta, `conn.transaction()` di psycopg crea un SAVEPOINT: `SET LOCAL ROLE`
e il GUC del tenant restano impostati fino al COMMIT della transazione
esterna, non alla chiusura del savepoint (il `SET LOCAL` e' legato alla
transazione di livello piu' alto, non al savepoint). Per questo, prima di
uscire dal context manager, si fa un `RESET ROLE` e un `set_config(...,
false)` espliciti (non `LOCAL`): agiscono subito, dentro la transazione
corrente, e non lasciano il ruolo/tenant del writer attivi per le istruzioni
successive del chiamante, qualunque sia l'annidamento.
"""
from __future__ import annotations

from contextlib import contextmanager

import psycopg

WRITER_ROLE = "gravya_writer"
TENANT_GUC = "app.tenant_id"


@contextmanager
def writer_transaction(conn: psycopg.Connection, tenant_id: str, *, statement_timeout_ms: int | None = None):
    """Apre una transazione come `gravya_writer` con il tenant impostato.

    `conn` deve essere una connessione con il permesso di `SET ROLE` a
    `gravya_writer` (grant di membership, vedi migrazione 0002). Al termine
    del blocco (anche in caso di eccezione), ruolo e tenant sono resettati
    esplicitamente sulla stessa connessione, cosi' non restano impostati
    nella transazione del chiamante (vincolo 7 del task implementer,
    correzione del giro 2 su B5/R13).

    `statement_timeout_ms`, se dato, limita la durata delle istruzioni nella
    transazione (DB lento o bloccato: l'istruzione viene annullata invece di
    restare in attesa indefinitamente, §5/§6 e giro 2 B5).
    """
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL ROLE {WRITER_ROLE}")
            cur.execute("SELECT set_config(%s, %s, true)", (TENANT_GUC, str(tenant_id)))
            if statement_timeout_ms is not None:
                cur.execute("SELECT set_config('statement_timeout', %s, true)", (str(statement_timeout_ms),))
        yield conn
        # Solo se il blocco e' terminato senza eccezioni: la transazione sta
        # per essere confermata (COMMIT) e i `SET LOCAL` non si annullano da
        # soli al commit (solo al rollback). Se il blocco solleva
        # un'eccezione, `yield` la rilancia subito: il ROLLBACK della
        # transazione esterna annulla gia' da solo ruolo e GUC, senza che
        # serva eseguire altro SQL su una transazione ormai in errore.
        with conn.cursor() as cur:
            cur.execute("RESET ROLE")
            cur.execute("SELECT set_config(%s, '', false)", (TENANT_GUC,))
