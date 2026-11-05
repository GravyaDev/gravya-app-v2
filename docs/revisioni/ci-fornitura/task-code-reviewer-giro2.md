# Task per code-reviewer: verifica del giro 2 (BLOCCA sul controllo OSV)

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura (worktree `.worktrees/ci-fornitura`).

## Contesto
Il tuo BLOCCA sulla prima versione (`docs/revisioni/ci-fornitura/report-code-reviewer.md`, risposta `risposta-code-reviewer.json`): fail-closed di `invia_http` non protetto da test; inoltre (da riportare) `IncompleteRead` con codice 1 invece di 2. Il compliance-auditor ha riportato come minore la lettura del lockfile fail-open (`report-compliance-auditor.md`). Correzione dell'implementer (task `task-implementer-giro2.md`, risposta `risposta-implementer-giro2.json`, commit e3759ef, c11fa33, 3f64f3d). Verifica del coordinator: `prova-mutante.sh` dà 8 falliti sul mutante (prima 11 passati), la tua prova 3 falliti sul mutante e 3 passati sul branch, `osv-check.py` esce 0 sul lockfile, CI e «Catena di fornitura» verdi su 3f64f3d.

## Task
PR: branch impl/ci-fornitura, base main, head impl/ci-fornitura (solo i commit del giro 2: `git diff a0f238c..impl/ci-fornitura`)
Documento di dettaglio dichiarato: E1 (v1.10), parte di CI; DECISIONS §6 «Catena di fornitura» punto 1.
Cartella report: docs/revisioni/ci-fornitura/ (nel repository principale; report `report-code-reviewer-giro2.md`)

Verifica solo: che il BLOCCA sia risolto (i test nuovi falliscono su mutanti di `invia_http` che ingoiano errori di rete, timeout, stato HTTP diverso da 200, corpo non JSON, risposta troncata); che `IncompleteRead` e gli altri errori di `http.client` diano il codice 2 senza traceback; che la lettura del lockfile sia fail-closed; che non ci siano cambiamenti fuori perimetro nel giro 2. Le prove si eseguono dalla radice del worktree con `. .venv/bin/activate` (variabili come nel task precedente). Non modificare nulla nel worktree e non fare commit; cartelle di lavoro solo dentro `docs/revisioni/ci-fornitura/`, cancellate a fine verifica. Gli altri rilievi del tuo primo report (Dependabot per pip, costanti tautologiche, ancore YAML, esecuzioni doppie) restano come riportati: non riesaminarli.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
