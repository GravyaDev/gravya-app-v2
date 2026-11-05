# Task per code-reviewer: catena di fornitura della CI

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura (worktree `.worktrees/ci-fornitura`).

## Contesto
Decisione dell'utente in `docs/DECISIONS.md` §6, riga «Catena di fornitura» (punti 1 e 2), con il punto aperto in §4 «Catena di fornitura e aggiornamenti». Task dell'implementer: `docs/revisioni/ci-fornitura/task-implementer.md`; la sua risposta: `docs/revisioni/ci-fornitura/risposta-implementer.json` (con due divergenze dichiarate: Dependabot per pip non configurato perché la documentazione non garantisce la rigenerazione del lockfile con hash, e un file di test nuovo `tests/test_ci_osv_check.py`); il suo report è sul branch (`git show impl/ci-fornitura:docs/revisioni/ci-fornitura/report-implementer.md`).

## Task
PR: branch impl/ci-fornitura, base main, head impl/ci-fornitura (`git diff main...impl/ci-fornitura`)
Documento di dettaglio dichiarato: E1 (`docs/E1-tracing-distribuito.md` v1.10), per la sola parte di ambiente; criterio principale: la riga «Versioni di runtime» di DECISIONS §6 e i vincoli del task dell'implementer.
Cartella report: docs/revisioni/ci-fornitura/ (nel repository principale, non nel worktree)

Cosa verificare in particolare: `scripts/osv-check.py` fallisce davvero (fail-closed) con una versione vulnerabile, con OSV non raggiungibile o con risposta malformata, e i suoi test non passerebbero con lo script vuoto; il job settimanale del digest rileva davvero un digest diverso (provalo in locale con un `ci.yml` modificato in una cartella di lavoro dentro `docs/revisioni/ci-fornitura/`, poi cancellala); action fissate per SHA che corrispondono al tag dichiarato e girano su Node 24 (`gh api`); runner `ubuntu-24.04` in tutti i job; `psql` della CI preso dall'immagine dei servizi con lo stesso digest; `scripts/test-non-superuser.sh` invariato nel comportamento con il `psql` dell'host; l'immagine PostgreSQL resta una sola riga `image:` (la legge `scripts/agenti.py`); nessun cambiamento fuori perimetro. Per eseguire: `cd .worktrees/ci-fornitura && . .venv/bin/activate` con `PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development`; `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` e `bash scripts/test-non-superuser.sh`. Esito della CI sul branch: `gh run list --branch impl/ci-fornitura`. Non modificare nulla nel worktree e non fare commit; cancella `.pytest_basetemp` del worktree a fine esecuzione.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
