# Task per il doc-writer: E1 v1.8

Preparato dal coordinator il 2026-11-05 (sessione 8).

Sottoprodotto: E1 — Tracing distribuito (componente E). Ondata 1; altri documenti (A1, A3, B1, B2, C1, C3, E2, E3) da non toccare.
Operazione: aggiornamento per: chiudere i rilievi della revisione di E1 v1.7 e recepire le decisioni dell'utente del 2026-11-05 e il codice del giro 4 (v1.7 -> v1.8).
Dossier del code-reader: nessuno.
File: `docs/E1-tracing-distribuito.md` (repository gravya-app-v2, branch `claude/docs-ondata-1`).

## Fonti da leggere per intero
- `docs/revisioni/e1-v1.7/report-plan-auditor.md` e `docs/revisioni/e1-v1.7/report-compliance-auditor.md` (rilievi da chiudere).
- `docs/DECISIONS.md`: §2 riga DA-E1-13; §4 voce «Da riportare. Revisione di E1 v1.7 e catalogo v1.5»; §6 righe del 2026-11-05 «Segnali e C2: deroga per l'ondata 1», «Tenant di contesto dell'helper di E1», «Variabile di E1 da definire mancante all'avvio in produzione».
- `docs/E1-tracing-distribuito.md` v1.7.
- Codice del branch `claude/impl-e1` dopo il giro 4 (sola lettura): worktree o `git show origin/claude/impl-e1:<percorso>`; in particolare la sezione «Giro 4» di `docs/revisioni/impl-e1/report-implementer.md`, `src/gravya_e1/tracing.py`, `src/gravya_e1/signals.py`, `migrations/versions/0006_giro4_fixes.py`, `config/e5-snapshot.json`.

## Cosa cambiare
1. Appendice C: aggiungere DA-E1-13 (decisa: (a) e (b) insieme; (c) solo ondata 1 con dati sintetici).
2. §5 segnali: segnali sempre prodotti, coda e thread propri, mai bloccanti per il chiamante; conservati nella tabella solo se scrivibile, altrimenti nel log locale di ripiego: **deroga a C2 solo per l'ondata 1**, la conservazione garantita è requisito di A5 (ondata 2). Togliere la contraddizione «sempre conservati».
3. §5 tenant e ruoli: tenant di contesto obbligatorio con `API_ENV=production` reale (decisione), facoltativo altrove con segnale; valore di `API_ENV` fuori dall'insieme chiuso: segnale `e5.environment_invalid` senza blocco; ruolo di migrazione distinto, appartenenza al proprietario BYPASSRLS revocata dopo la migrazione (migrazione 0006), `CREATE` su `public` concesso solo durante la migrazione; policy dei segnali con `WITH CHECK` sul tenant, lettura negata al writer, isolamento in lettura da definire con A5.
4. §5 e §6 avvio: variabile «da definire» mancante in produzione = il servizio non si avvia e parte un segnale; il fail-open vale solo per i guasti a runtime.
5. Timeout: `e1.write_statement_timeout_ms` è **lato server**; lato client `e1.write_connect_timeout_ms`, `e1.write_tcp_user_timeout_ms`, keepalive e guardiano per job. Correggere §5 e §11.
6. §4.2, §4.3, §7: dove oggi il testo dice «vocabolario chiuso» per campi che hanno solo un formato, scrivere lo stato attuale (formato) e il rimando a DA-E1-13.
7. Criterio 4: aggiungere che per gli identificativi generici si verifica il formato (fino all'attuazione di DA-E1-13). Criterio 5: estendere ai segnali con connessione bloccata. Criterio 9: renderlo verificabile (nomi degli header e formato del `trace_id` in forma `traceparent`), dichiarando non definito il `parent-id`.
8. Appendice B: togliere i limiti chiusi dal giro 4 (segnali sincroni, `close()` appeso, thread fermo con rete bloccata, appartenenza al ruolo BYPASSRLS); aggiungere i limiti residui: segmenti in coda persi all'uscita del processo (contati e segnalati se `close()` è chiamato), contatori in memoria, oracolo di esistenza del `trace_id` tramite il GUC, whitelist applicata dall'helper e non dal database, nome della chiave scartata solo se nota.
9. Testi superati: «l'invariante SHA-256 del catalogo §18 va aggiornata» e «la voce chiave HMAC non è nel catalogo §15» (già fatti); DX-07 non è più aperta; togliere «(in corso)» e riferimenti ai «giri» come fonte di contratto (restano solo nei rimandi alle prove).
10. Variabili: elencare nel campo `variabili` della risposta tutte le `e1.*` con il valore di sviluppo dell'istantanea dopo il giro 4 (compreso `e1.write_tcp_user_timeout_ms`). **Non** scrivere in `docs/catalogo-variabili.md`.

## Vincoli
Template a 12 sezioni invariato; versione 1.8 e data 2026-11-05; **una sola riga nuova** nello Storico modifiche; le righe precedenti dello Storico non si toccano né si riassumono (controllo riga per riga). Non scrivere «verificato sul codice» per ciò che non hai letto nel codice. Nessun file fuori da `docs/E1-tracing-distribuito.md`, niente file temporanei, niente commit. Risposta: solo il JSON dello schema del doc-writer.
