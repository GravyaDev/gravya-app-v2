# Task per il doc-writer: E1 v1.9

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisioni dell'utente: «ok» ai punti 1-5 del coordinator (DECISIONS §6, righe del 2026-11-05).

Sottoprodotto: E1 — Tracing distribuito. Operazione: aggiornamento (v1.8 -> v1.9) per chiudere i rilievi della revisione della v1.8 e recepire le decisioni. File: `docs/E1-tracing-distribuito.md` (branch `claude/docs-ondata-1`). Altri documenti dell'ondata da non toccare. Non scrivere nel catalogo (lo aggiorna il coordinator alla v1.7).

## Fonti da leggere per intero
`docs/revisioni/e1-v1.8/report-plan-auditor.md`, `docs/revisioni/e1-v1.8/report-compliance-auditor.md`, `docs/E1-tracing-distribuito.md` v1.8; dal branch `claude/impl-e1` (sola lettura) `docs/revisioni/impl-e1/report-code-reviewer-giro4.md`, `docs/revisioni/impl-e1/task-implementer-giro5.md`.

## Cosa cambiare
1. **Decisioni:** `e1.write_connect_timeout_ms` diventa `e1.write_connect_timeout_s` (secondi interi, minimo 2, motivo libpq); `API_ENV` fuori dall'insieme chiuso blocca l'avvio con segnale; chiave HMAC minima 32 byte invariante provvisoria fino ad A6, presente nel catalogo §18 (togliere «non è nel catalogo»); formati della whitelist nel catalogo §18 come invarianti provvisorie, fino all'attuazione di DA-E1-13.
2. **§9, condizione prima dei dati reali (decisione):** nessun dato reale di un'agenzia prima dell'attuazione di DA-E1-13, dei segnali durevoli di A5 e di una procedura di installazione approvata (ruoli, revoche dopo le migrazioni). Scriverla come condizione dei passi 4-6 e dell'attivazione per un'agenzia; in App. C indicare chi redige gli elenchi di DA-E1-13 (B1, B2, E16) e in §3 e §12 la dipendenza.
3. **Isolamento (compliance V-02):** l'isolamento presuppone che solo l'helper imposti `app.tenant_id` e che i ruoli con privilegi sulle tabelle (proprietario, ruolo di migrazione, writer) non siano usati da altro codice; «il ruolo di migrazione non deve essere usato a runtime» come requisito di installazione, al posto di «non ha accesso».
4. **Segnali:** «di norma» dove oggi dice «mai» (all'avvio alcuni segnali sono sincroni); i limiti di tempo valgono per il sink PostgreSQL con connessione propria (giro 5); la segnalazione dei job rimasti in coda alla chiusura va nel log locale; un solo nome per la destinazione dei segnali (tabella provvisoria dei segnali, che nell'ondata 1 fa da tabella di audit minima per E1): dirlo in §2 e §5.
5. **Regola tra variabili:** `e1.write_tcp_user_timeout_ms` non inferiore a `e1.write_statement_timeout_ms`; spiegare il doppio uso (tcp_user_timeout e durata massima di un job).
6. **Requisito di installazione:** la migrazione 0006 tenta solo la revoca dell'appartenenza (avviso se non riesce); la revoca reale dell'appartenenza e del `CREATE` su `public` è un passo obbligatorio del superuser dopo le migrazioni.
7. **Residui** segnalati dai report della v1.8 non coperti sopra.

## Vincoli
Template a 12 sezioni; versione 1.9 e data 2026-11-05; **una sola riga nuova** nello Storico, righe 1.0-1.8 intatte. Elenca nel campo `variabili` della risposta le `e1.*` aggiornate. Nessun file fuori da E1, niente file temporanei, niente commit. Risposta: solo il JSON dello schema del doc-writer.
