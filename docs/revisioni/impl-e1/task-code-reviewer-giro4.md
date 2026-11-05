# Task per il code-reviewer: verifica mirata del giro 4 di E1

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente: «ok» al giro 4 piccolo e mirato con verifica del code-reviewer **solo sulle modifiche** (DECISIONS §6, riga «Quarto giro di correzioni a E1 v1.6»).

PR: branch `claude/impl-e1`, base `claude/docs-ondata-1`; modifiche da verificare: `3649b15..8dfb1de` (giro 4). Documento: E1 (passi 0, 2, 3). Task del giro: `docs/revisioni/impl-e1/task-implementer-giro4.md`; report dell'implementer, sezione «Giro 4»; README alla radice (sezione «Esecuzione locale»).

Scelte del coordinator durante il giro (da valutare, non da contestare come difetti dell'implementer):
- `test_G15b` di `code-reviewer-giro2/` classificato «fallito atteso»: inserisce senza impostare il GUC del tenant e il rifiuto è il comportamento voluto (policy con `WITH CHECK` sul tenant).
- `API_ENV` fuori dall'insieme chiuso (`production`, `development`, `test`): segnale `e5.environment_invalid` senza blocco, per coerenza con `test_R15b`.
- `GRANT CREATE ON SCHEMA public` al proprietario della funzione solo durante la migrazione, revocato subito dopo.

Cosa verificare:
1. Che le correzioni 1-5 e i minori del task siano risolti nel codice (non solo che i test passino): guardiano per job con rete bloccata (`shutdown()` del socket da un altro thread: rischi di concorrenza), `close()` mai oltre il timeout, coda e thread dei segnali con la connessione del sink sotto gli stessi timeout (il riconoscimento del sink per «duck typing» su `_conn` è fragile?), migrazione 0006 (revoca dell'appartenenza, `RAISE WARNING`), policy dei segnali con `WITH CHECK`, `MIGRATION_ROLE` quotato, nome della chiave nei segnali solo se nota.
2. Che i falliti attesi siano esattamente: `code-reviewer-giro2/` 12 di prima più `test_G15b`; `code-reviewer-giro3/` solo `test_N4` e `test_N10`.
3. README «Esecuzione locale»: eseguibile da una persona su un altro computer? Dipendenze residue dal ruolo `root` dichiarate e motivate?
4. DX-22 sulla nuova variabile `e1.write_tcp_user_timeout_ms` e sul guardiano (nessun numero fisso).
5. Stabilità: suite completa 10 volte.

Esecuzione: `tests/` con il virtualenv `.venv`; prove dei revisori con `PGDATABASE` del loro database (`gravya_e1_review`, `gravya_e1_review2`, `gravya_e1_review3`); script: `PGUSER=<superuser> PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh`.

Prove nuove solo in `docs/revisioni/impl-e1/code-reviewer-giro4/`; `--basetemp` lì dentro, cancellato alla fine; nessun file in `/tmp` (né `--basetemp` in `/tmp`). Non modificare codice, test o file precedenti; niente commit.

Report: `docs/revisioni/impl-e1/report-code-reviewer-giro4.md`. Risposta: solo il JSON dello schema del code-reviewer.
