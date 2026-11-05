# Task per il doc-writer: E1 v1.10

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisioni dell'utente («ok», 2026-11-05): `API_ENV` non impostata blocca l'avvio con segnale; regola «`e1.write_tcp_user_timeout_ms` non inferiore a `e1.write_statement_timeout_ms`» confermata (valore non valido = avvio bloccato con segnale, DX-17); giro 6 definitivo del codice (task `docs/revisioni/impl-e1/task-implementer-giro6.md` sul branch `claude/impl-e1`).

Sottoprodotto: E1. Operazione: aggiornamento v1.9 -> v1.10. File: `docs/E1-tracing-distribuito.md` (branch `claude/docs-ondata-1`). Non toccare altri documenti né il catalogo.

## Fonti da leggere per intero
`docs/revisioni/e1-v1.9/report-plan-auditor.md`, `docs/revisioni/e1-v1.9/report-compliance-auditor.md`, E1 v1.9; dal branch `claude/impl-e1` (sola lettura) `docs/revisioni/impl-e1/report-code-reviewer-giro5.md` e `task-implementer-giro6.md`; `docs/DECISIONS.md` §2 (DA-E1-13), §4 e §6 (righe di E1, «Mutazioni del grafo A1»).

## Cosa cambiare
1. Decisioni: `API_ENV` non impostata blocca l'avvio con segnale (togliere «trattata come sviluppo»); `API_ENV` fuori insieme blocca anche con `production_override`; regola tcp ≥ statement come decisione del 2026-11-05 (regola relazionale del catalogo, 8(e)).
2. DA-E1-13: la ripartizione dei compiti tra B1, B2, E16 e C1 è una **proposta** da confermare nelle revisioni di B1, B2 ed E16; la decisione cita solo i cataloghi di B1 e B2 e gli UUID.
3. Rimandi a DECISIONS dopo la ristrutturazione: mutazioni del grafo A1 in §6 («Mutazioni del grafo A1»); valori provvisori in §4 («E1, valori provvisori»); punti aperti in §4.
4. Appendice B: il comportamento del giro 5 è stato controllato dai revisori leggendo il codice a `41607af`; restano non verificati solo i punti del giro 6 (descritti dal task, non ancora nel codice). Aggiungere i limiti: guardiano che può interrompere un job sano vicino alla fine (perdita contata e riconnessione); protezione dei segnali per tenant contro l'inserimento diretto, non contro un errore del chiamante; limiti di tempo dei segnali solo per il sink PostgreSQL; regola tcp ≥ statement controllata all'avvio, da validare anche alla modifica quando A6 la consentirà.
5. Criterio 17: per i tre casi di avvio bloccato (variabile mancante, `API_ENV` assente o fuori insieme, regola tcp ≥ statement) indicare il segnale e che l'avvio fallisce.
6. Il minimo 2 di `e1.write_connect_timeout_s` è imposto dal codice (giro 6).

## Vincoli
Template a 12 sezioni; versione 1.10 e data 2026-11-05; **una sola riga nuova** nello Storico, righe 1.0-1.9 intatte. Variabili `e1.*` nel campo `variabili` della risposta, senza scrivere nel catalogo. Nessun file fuori da E1, niente file temporanei, niente commit. Risposta: solo il JSON dello schema del doc-writer.
