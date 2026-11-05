# Task per implementer: aggiornamento a Python 3.15 e PostgreSQL 18

Agente: implementer
Worktree: e1-runtime
Preparato dal coordinator il 2026-11-05. Branch: impl/e1-runtime.

## Contesto
Decisione dell'utente in `docs/DECISIONS.md` §6, riga «Versioni di runtime»: Python 3.15 e PostgreSQL 18 al posto di Python 3.11 e PostgreSQL 16 (ereditate dal container della piattaforma); aggiornamento di lockfile (con hash), CI e README come lavoro a parte, seguito da `code-reviewer` e `compliance-auditor`. L'utente aveva chiesto di portare tutti i pacchetti all'ultima versione, senza vulnerabilità note e senza incompatibilità tra loro, con un lock di versione. Verifica del coordinator del 2026-11-05: tutti i pacchetti del lockfile attuale sono installabili su Python 3.15 e `tests/` è verde su Python 3.15 e PostgreSQL 18 con il lockfile attuale; su PyPI erano più recenti solo `pydantic` (2.14.3) e `pydantic-core` (2.50.4).

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10)
Perimetro: solo le versioni di runtime e delle dipendenze; nessun cambiamento al codice applicativo, ai test, alle migrazioni, salvo che un test fallisca per la sola nuova versione (in quel caso fermati e riporta il punto in `divergenze`, senza correggere).
Repository: .worktrees/e1-runtime; branch di lavoro: impl/e1-runtime
Push: sì (solo il branch `impl/e1-runtime`, serve a far girare la CI di GitHub)
Vincoli specifici:
1. `requirements.lock.txt`: rigeneralo per Python 3.15, con hash (`pip install --require-hashes` deve funzionare), ogni pacchetto all'ultima versione compatibile pubblicata su PyPI. L'intestazione del file deve riportare il comando esatto per rigenerarlo, senza percorsi in `/tmp` o fuori dal repository (oggi cita `/tmp/reqs.in`): se serve un file d'ingresso, mettilo nel repository e dichiaralo; preferibile partire da `pyproject.toml`. Strumenti disponibili: `uv` (0.13), o `pip-tools` installato nel `.venv` del worktree (non nel lockfile).
2. Per ogni pacchetto del nuovo lockfile, interroga OSV (`https://api.osv.dev/v1/querybatch`, ecosistema PyPI) sulla versione fissata; se una versione ha vulnerabilità note, fermati e riportalo. Dopo l'installazione, `pip check` senza errori.
3. `pyproject.toml`: `requires-python` coerente con la decisione (Python 3.15); i limiti inferiori delle dipendenze restano o si alzano solo se servono.
4. `.github/workflows/ci.yml`: `python-version: "3.15"` nei due job; immagine dei servizi `postgres:18@sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583` (digest verificato dal coordinator il 2026-11-05), sempre fissata per digest. Non cambiare le action (fissate per SHA) né altro.
5. `README.md`: prerequisiti (Python 3.15, PostgreSQL 18) e ogni altro punto che cita le versioni vecchie.
6. Ricrea il `.venv` del worktree dal nuovo lockfile. Ambiente: `. .venv/bin/activate` nel worktree e variabili `PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development` (PostgreSQL 18 in Docker dedicato al worktree, database `gravya_e1_test` già migrato). Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde 10 volte; `bash scripts/test-non-superuser.sh` riuscito con le stesse variabili; dopo il push, esito della CI sul branch (`gh run list --branch impl/e1-runtime`, `gh run watch`) nei due job. Le prove dei revisori in `docs/revisioni/impl-e1/code-reviewer*/` non si eseguono nel worktree (hanno il percorso del repository principale scritto nei file): le esegue il coordinator dopo il merge.
7. Commit piccoli, uno per argomento (lockfile e pyproject; CI; README). Aggiungi in `docs/revisioni/e1-runtime/report-implementer.md` il report: comando di rigenerazione, tabella pacchetto, versione vecchia e nuova, esito OSV; esiti dei test e della CI.
Cartella report: docs/revisioni/e1-runtime/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
