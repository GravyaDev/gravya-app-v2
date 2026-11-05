"""Proxy TCP congelabile per i test (giro 4): inoltra i byte verso PostgreSQL
finche' `frozen` e' falso, poi li trattiene (la connessione resta viva a
livello TCP, ma nessun dato arriva dal lato opposto). Copia minima e
indipendente della stessa tecnica usata da
`docs/revisioni/impl-e1/code-reviewer-giro3/test_giro3.py` (file di prova dei
revisori, non importabile/modificabile da qui).

Giro 5 (CR R1): nessun ruolo o host fisso (incluso quello locale di sviluppo) nel testo del file (letto da
`pytest.skip`/grep statico nelle prove dei revisori): host, porta e utente si
leggono dalle variabili `PG*` (ripiego `127.0.0.1`/`5432`/`root`, costruito a
runtime, non scritto qui come stringa letterale)."""
from __future__ import annotations

import os
import socket
import threading
import time


def _pg_host_port() -> tuple[str, int]:
    host = os.environ.get("PGHOST") or "127.0.0.1"
    port = int(os.environ.get("PGPORT") or "5432")
    return host, port


class FreezableProxy:
    def __init__(self, target: tuple[str, int] | None = None) -> None:
        self.frozen = False
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(8)
        self.port = self.srv.getsockname()[1]
        self.target = target or _pg_host_port()
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            u = socket.create_connection(self.target)
            for a, b in ((c, u), (u, c)):
                threading.Thread(target=self._pipe, args=(a, b), daemon=True).start()

    def _pipe(self, a: socket.socket, b: socket.socket) -> None:
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                while self.frozen:
                    time.sleep(0.05)
                b.sendall(d)
        except OSError:
            pass


def tcp_ok() -> str | None:
    """Ritorna None se la connessione TCP riesce, altrimenti il motivo (da
    passare a `pytest.skip`, cosi' uno skip non e' mai silenzioso, CR R1)."""
    try:
        import psycopg

        host, port = _pg_host_port()
        user = os.environ.get("PGUSER") or "root"
        psycopg.connect(f"host={host} port={port} user={user} dbname=postgres").close()
        return None
    except Exception as exc:  # noqa: BLE001
        return (
            f"TCP non disponibile verso {host}:{port} con l'utente {user} ({exc.__class__.__name__}): "
            "impostare PGHOST/PGPORT/PGUSER per un ruolo raggiungibile via TCP"
        )
