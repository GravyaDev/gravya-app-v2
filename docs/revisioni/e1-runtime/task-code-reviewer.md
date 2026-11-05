# Task per code-reviewer: aggiornamento a Python 3.15 e PostgreSQL 18

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/e1-runtime (worktree `.worktrees/e1-runtime`).

## Contesto
Decisione dell'utente in `docs/DECISIONS.md` §6, riga «Versioni di runtime»: Python 3.15 e PostgreSQL 18; aggiornamento di lockfile (con hash, ultime versioni, nessuna vulnerabilità nota, nessuna incompatibilità), CI e README, poi `code-reviewer` e `compliance-auditor`. Task dell'implementer: `docs/revisioni/e1-runtime/task-implementer.md`; la sua risposta: `docs/revisioni/e1-runtime/risposta-implementer.json`; il suo report è sul branch (`git show impl/e1-runtime:docs/revisioni/e1-runtime/report-implementer.md`).

## Task
PR: branch impl/e1-runtime, base main, head impl/e1-runtime (`git diff main...impl/e1-runtime`)
Documento di dettaglio dichiarato: E1 (`docs/E1-tracing-distribuito.md` v1.10), per la sola parte di ambiente; criterio principale: la riga «Versioni di runtime» di DECISIONS §6 e i vincoli del task dell'implementer.
Cartella report: docs/revisioni/e1-runtime/ (nel repository principale, non nel worktree)

Cosa verificare in particolare: il lockfile è riproducibile con il comando dichiarato nella sua intestazione (rigeneralo in una cartella di lavoro dentro `docs/revisioni/e1-runtime/` e confronta; poi cancellala), contiene hash per tutte le distribuzioni, fissa le ultime versioni compatibili, non ha versioni con vulnerabilità note (OSV) e `pip check` passa; `requires-python`, CI (Python 3.15, `postgres:18` fissata per digest in entrambi i job, action invariate) e README coerenti tra loro; nessun cambiamento fuori perimetro (codice, test, migrazioni). Per eseguire: `cd .worktrees/e1-runtime && . .venv/bin/activate` con `PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development`; `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` e `bash scripts/test-non-superuser.sh`. Esito della CI sul branch: `gh run list --branch impl/e1-runtime`. Non modificare nulla nel worktree e non fare commit; cancella `.pytest_basetemp` del worktree a fine esecuzione.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
