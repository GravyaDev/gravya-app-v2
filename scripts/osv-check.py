#!/usr/bin/env python3
"""Controllo OSV del lockfile (strumento di CI, non codice applicativo).

Legge le versioni fissate in `requirements.lock.txt`, le interroga su OSV
(`querybatch`, ecosistema PyPI) ed esce con errore se una versione ha
vulnerabilita' note, elencandole. Solo libreria standard.

Fail-closed: se OSV non risponde o la risposta non e' valida, esce con
errore (non "nessuna vulnerabilita'"). Se il lockfile non contiene nessun
pacchetto fissato, esce con errore (un lockfile vuoto non e' un esito pulito).

Uso: python3 scripts/osv-check.py [percorso-lockfile]
"""
from __future__ import annotations

import http
import http.client
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Callable

# --- Costanti dello strumento di CI (DX-22: non sono valori applicativi) ---
# Endpoint ufficiale di OSV per interrogazioni in blocco.
OSV_URL = "https://api.osv.dev/v1/querybatch"
# Ecosistema OSV dei pacchetti del lockfile (generato da pip-compile).
ECOSISTEMA = "PyPI"
# Lockfile di default (percorso relativo alla radice del repository).
LOCKFILE_DEFAULT = "requirements.lock.txt"
# Limite di OSV: al massimo 1000 interrogazioni per richiesta querybatch.
DIMENSIONE_BLOCCO = 1000
# Tempo massimo di una richiesta: oltre, errore (la CI non deve restare appesa).
TIMEOUT_SECONDI = 30
# Unico stato HTTP accettato da OSV per una risposta valida.
HTTP_OK = http.HTTPStatus.OK
# Riga di un pacchetto fissato nel lockfile: `nome==versione \` (i marcatori
# di ambiente dopo `;` e il backslash finale non fanno parte della versione).
RE_PACCHETTO = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;\\]+)")


class ErroreOsv(Exception):
    """Risposta di OSV assente o non valida (fail-closed)."""


def leggi_lockfile(testo: str) -> list[tuple[str, str]]:
    trovati: list[tuple[str, str]] = []
    for riga in testo.splitlines():
        m = RE_PACCHETTO.match(riga)
        if m:
            trovati.append((m.group(1), m.group(2)))
    return trovati


def invia_http(url: str, corpo: dict) -> dict:
    richiesta = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=TIMEOUT_SECONDI) as risposta:
            if risposta.status != HTTP_OK:
                raise ErroreOsv(f"stato HTTP {risposta.status} da {url} (atteso {HTTP_OK})")
            return json.loads(risposta.read().decode("utf-8"))
    # OSError: rete, timeout, HTTPError; ValueError: corpo non JSON/UTF-8;
    # HTTPException: risposta troncata (IncompleteRead) o malformata.
    except (OSError, ValueError, http.client.HTTPException) as e:
        raise ErroreOsv(f"richiesta a {url} fallita: {e}") from e


def interroga(
    pacchetti: list[tuple[str, str]],
    invia: Callable[[str, dict], dict] = invia_http,
) -> dict[tuple[str, str], list[str]]:
    """Ritorna {(nome, versione): [id vulnerabilita']} solo per i vulnerabili."""
    vulnerabili: dict[tuple[str, str], list[str]] = {}
    for inizio in range(0, len(pacchetti), DIMENSIONE_BLOCCO):
        blocco = pacchetti[inizio : inizio + DIMENSIONE_BLOCCO]
        # Per ogni voce del blocco, il token di pagina (None = prima pagina).
        in_corso = {i: None for i in range(len(blocco))}
        while in_corso:
            indici = list(in_corso)
            queries = []
            for i in indici:
                q = {"package": {"name": blocco[i][0], "ecosystem": ECOSISTEMA}, "version": blocco[i][1]}
                if in_corso[i]:
                    q["page_token"] = in_corso[i]
                queries.append(q)
            risposta = invia(OSV_URL, {"queries": queries})
            risultati = risposta.get("results") if isinstance(risposta, dict) else None
            if not isinstance(risultati, list) or len(risultati) != len(queries):
                raise ErroreOsv("risposta OSV non valida: 'results' mancante o di lunghezza diversa dalle query")
            prossimi: dict[int, str] = {}
            for i, ris in zip(indici, risultati):
                if not isinstance(ris, dict):
                    raise ErroreOsv("risposta OSV non valida: voce di 'results' non e' un oggetto")
                for v in ris.get("vulns", []) or []:
                    vid = v.get("id") if isinstance(v, dict) else None
                    if not vid:
                        raise ErroreOsv("risposta OSV non valida: vulnerabilita' senza 'id'")
                    vulnerabili.setdefault(blocco[i], []).append(vid)
                if ris.get("next_page_token"):
                    prossimi[i] = ris["next_page_token"]
            in_corso = prossimi
    return vulnerabili


def main(argv: list[str]) -> int:
    percorso = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent / LOCKFILE_DEFAULT
    try:
        testo = percorso.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERRORE: lockfile non leggibile ({percorso}): {e}", file=sys.stderr)
        return 2
    pacchetti = leggi_lockfile(testo)
    if not pacchetti:
        print(f"ERRORE: nessun pacchetto fissato (nome==versione) in {percorso}", file=sys.stderr)
        return 2
    try:
        vulnerabili = interroga(pacchetti)
    except ErroreOsv as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        return 2
    if vulnerabili:
        print(f"VULNERABILITA' NOTE in {len(vulnerabili)} pacchetti su {len(pacchetti)}:", file=sys.stderr)
        for (nome, versione), ids in sorted(vulnerabili.items()):
            print(f"  {nome}=={versione}: {', '.join(sorted(set(ids)))}", file=sys.stderr)
        return 1
    print(f"OK: nessuna vulnerabilita' nota in {len(pacchetti)} pacchetti ({percorso})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
