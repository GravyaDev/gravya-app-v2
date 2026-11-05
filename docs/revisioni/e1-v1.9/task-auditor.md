# Task per plan-auditor e compliance-auditor: verifica finale di E1 v1.9 e catalogo v1.7

Preparato dal coordinator il 2026-11-05 (sessione 8). Ultima verifica del giro unico deciso dall'utente (DECISIONS §6, «E1: chiusura della v1.8»).

Oggetto: `docs/E1-tracing-distribuito.md` v1.9 e `docs/catalogo-variabili.md` v1.7 (branch `claude/docs-ondata-1`); differenze dalla versione revisionata: `git diff f11e560..HEAD -- docs/E1-tracing-distribuito.md docs/catalogo-variabili.md`. Codice di riferimento: branch `claude/impl-e1` a `41607af` (sola lettura; README e report dell'implementer, sezione «Giro 5»). Nota: `docs/DECISIONS.md` è stato ristrutturato il 2026-11-05 con sole decisioni correnti (stessi numeri di sezione; storia in `docs/decisioni-archivio.md`).

Cosa verificare:
1. Che i rilievi delle revisioni della v1.8 (`docs/revisioni/e1-v1.8/`) e della verifica del giro 4 (`docs/revisioni/impl-e1/report-code-reviewer-giro4.md` sul branch del codice) siano chiusi o dichiarati come limiti; elenca quelli aperti.
2. Coerenza di E1 v1.9 con le righe correnti di DECISIONS (§2 DA-E1-*, §6 righe di E1) e con il catalogo v1.7 (`e1.write_connect_timeout_s` in secondi con minimo 2, regola tra `e1.write_tcp_user_timeout_ms` e `e1.write_statement_timeout_ms`, guardia `API_ENV` a insieme chiuso, deroga C2, formati e chiave minima in §18).
3. Che E1 non dichiari come implementato ciò che il codice del giro 5 non fa (il doc-writer ha descritto il codice dal task del giro 5, prima che fosse scritto).
4. Storico di E1: righe 1.0-1.8 intatte, una sola riga nuova.

Regole: non modificare file salvo il proprio report; niente commit; nessun file fuori dalla cartella; nel JSON solo le chiavi dello schema.

Report: `docs/revisioni/e1-v1.9/report-plan-auditor.md` e `docs/revisioni/e1-v1.9/report-compliance-auditor.md`.
