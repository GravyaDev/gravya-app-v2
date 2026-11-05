# Task per plan-auditor e compliance-auditor: revisione di E1 v1.8 e catalogo v1.6

Preparato dal coordinator il 2026-11-05 (sessione 8). Sequenza «modifica a un documento di dettaglio» (docs/agenti/README.md).

Oggetto: `docs/E1-tracing-distribuito.md` v1.8 e `docs/catalogo-variabili.md` v1.6, branch `claude/docs-ondata-1`. Differenze dalla versione già revisionata: `git diff 0cf35f6..HEAD -- docs/E1-tracing-distribuito.md docs/catalogo-variabili.md`.

Motivo: chiusura dei rilievi della revisione di E1 v1.7 e catalogo v1.5 (`docs/revisioni/e1-v1.7/`, voce «Da riportare. Revisione di E1 v1.7 e catalogo v1.5» di DECISIONS §4) e recepimento delle decisioni del 2026-11-05 (DECISIONS §2 DA-E1-13; §6 «Segnali e C2: deroga per l'ondata 1», «Tenant di contesto dell'helper di E1», «Variabile di E1 da definire mancante all'avvio in produzione») e del codice del giro 4 (branch `claude/impl-e1`, sola lettura; README e report dell'implementer, sezione «Giro 4»).

Cosa verificare:
1. Che ogni rilievo dei report `docs/revisioni/e1-v1.7/` sia chiuso o dichiarato come limite; elenca quelli ancora aperti.
2. Coerenza E1-catalogo (in particolare timeout lato server/client, regola 11, formati e chiave minima in §18, deroga C2).
3. Che E1 non presenti come garantito ciò che il codice fa solo in parte. Punto segnalato dal doc-writer: la revoca dell'appartenenza al proprietario BYPASSRLS nella migrazione 0006 è best-effort (avviso se non riesce) ed è reale solo nello script di deploy; il docstring della migrazione e il report dell'implementer non concordano sul `CREATE` su `public`.
4. Storico di E1: righe 1.0-1.7 intatte, una sola riga nuova.

Regole: non modificare file salvo il proprio report; niente commit; nessun file fuori dalla cartella; nel JSON solo le chiavi dello schema.

Report: `docs/revisioni/e1-v1.8/report-plan-auditor.md` e `docs/revisioni/e1-v1.8/report-compliance-auditor.md`.
