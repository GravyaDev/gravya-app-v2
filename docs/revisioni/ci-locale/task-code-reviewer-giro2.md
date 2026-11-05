# Task per code-reviewer: verifica del giro 2 (BLOCCA sul job locale)

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-locale (worktree `.worktrees/ci-locale`).

## Contesto
Il tuo BLOCCA sulla prima versione (`docs/revisioni/ci-locale/report-code-reviewer.md`, `risposta-code-reviewer.json`, prove in `prove-code-reviewer/`): errori ingoiati in `esegui` e `compila_con_pip_tools` (11 mutanti sopravvissuti su 15), issue perse per un'eccezione non gestita; più i tuoi rilievi da riportare e minori. Il giro 2 dell'implementer (task `task-implementer-giro2.md`, risposta `risposta-implementer-giro2.json`) li corregge insieme ai rilievi tecnici del compliance-auditor (`report-compliance-auditor.md`); le divergenze dichiarate sono nella risposta. CI e «Catena di fornitura» verdi su 19683a9 secondo l'implementer.

## Task
PR: branch impl/ci-locale, base main, head impl/ci-locale (giro 2: `git diff 65c4b12..impl/ci-locale`; esito sull'insieme `main...impl/ci-locale`)
Documento di dettaglio dichiarato: E1 (v1.10), parte di CI; DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura».
Cartella report: docs/revisioni/ci-locale/ (nel repository principale; report `report-code-reviewer-giro2.md`)

Verifica che i due bloccanti siano risolti (riesegui le tue prove e i tuoi mutanti), che i tuoi rilievi 3-9 siano corretti, che il nuovo codice del giro 2 (traccia delle esecuzioni e `--stato`, commenti alle issue, rimozione delle credenziali, `requirements-strumenti.lock.txt`, controlli nuovi di `worktree-unisci`) sia fail-closed e coperto da test che fallirebbero con mutanti, e che non ci siano cambiamenti fuori perimetro. I punti che richiedono una decisione dell'utente (eccezione a DX-22 per gli strumenti locali, credenziale `gh`, minuti del Graph Update) non sono rilievi bloccanti. **Non eseguire il job senza `--prova`** e non installare il timer. Per eseguire: `cd .worktrees/ci-locale && . .venv/bin/activate` e `set -a; . ../ci-locale.env; set +a`. Non modificare nulla nel worktree e non fare commit; cartelle di lavoro solo dentro `docs/revisioni/ci-locale/`, cancellate a fine verifica; cancella `.pytest_basetemp` del worktree.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
