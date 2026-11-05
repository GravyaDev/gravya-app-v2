"""Proxy TCP congelabile per i test (giro 4): inoltra i byte verso PostgreSQL
finche' `frozen` e' falso, poi li trattiene (la connessione resta viva a
livello TCP, ma nessun dato arriva dal lato opposto). Copia minima e
indipendente della stessa tecnica usata da
`docs/revisioni/impl-e1/code-reviewer-giro3/test_giro3.py` (file di prova dei
revisori, non importabile/modificabile da qui)."""
from __future__ import annotations

import socket
import threading
import time


class FreezableProxy:
    def __init__(self, target: tuple[str, int] = ("127.0.0.1", 5432)) -> None:
        self.frozen = False
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(8)
        self.port = self.srv.getsockname()[1]
        self.target = target
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


def tcp_ok() -> bool:
    try:
        import psycopg

        psycopg.connect("host=127.0.0.1 user=root dbname=postgres").close()
        return True
    except Exception:  # noqa: BLE001
        return False
