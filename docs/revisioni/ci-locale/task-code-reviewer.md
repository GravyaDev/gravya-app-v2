# Task per code-reviewer: job della catena di fornitura in locale e CI ridotta

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-locale (worktree `.worktrees/ci-locale`).

## Contesto
Decisione dell'utente del 2026-11-05 (testo alla lettera in `docs/revisioni/ci-locale/task-implementer.md`): job della catena di fornitura in locale, CI di GitHub ridotta per i minuti (DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura»). Task dell'implementer: `docs/revisioni/ci-locale/task-implementer.md`; risposta `docs/revisioni/ci-locale/risposta-implementer.json` (con divergenze e decisioni mancanti dichiarate); report sul branch (`git show impl/ci-locale:docs/revisioni/ci-locale/report-implementer.md`).

## Task
PR: branch impl/ci-locale, base main, head impl/ci-locale (`git diff main...impl/ci-locale`)
Documento di dettaglio dichiarato: E1 (v1.10), parte di CI; DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura».
Cartella report: docs/revisioni/ci-locale/ (nel repository principale)

Cosa verificare in particolare: i filtri dei workflow non lasciano partire nulla per commit di soli `docs/**`, `stato/**`, `**/*.md`, `.claude/**` e non saltano commit che toccano codice, test, migrazioni, lockfile, script o workflow; `scripts/fornitura-locale.py` è fail-closed (un errore di rete, di `docker`, di `gh` o di `pip-compile` non diventa «tutto a posto»), non duplica le issue, apre la PR solo se il lockfile cambia, non tocca `main`; i suoi test fallirebbero con mutanti che ingoiano gli errori; `worktree-unisci` non unisce se OSV o la suite falliscono e non fa push; unità systemd e installazione idempotenti e corrette; nessun cambiamento fuori perimetro. **Non eseguire il job senza `--prova`**: niente issue, PR o push reali; niente installazione del timer. Per eseguire: `cd .worktrees/ci-locale && . .venv/bin/activate` e `set -a; . ../ci-locale.env; set +a`; `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp`. Non modificare nulla nel worktree e non fare commit; cartelle di lavoro solo dentro `docs/revisioni/ci-locale/`, cancellate a fine verifica; cancella `.pytest_basetemp` del worktree.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
