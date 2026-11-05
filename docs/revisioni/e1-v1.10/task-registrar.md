# Task per il registrar: decisioni dell'utente sulla chiusura di E1

Preparato dal coordinator il 2026-11-05 (sessione 8). Sulla piattaforma il registrar non ha Bash: usa solo Read, Edit, Write.

Evento: decisione utente ed esiti di revisione. Cartella: `docs/` (branch `claude/docs-ondata-1`). File: `docs/DECISIONS.md`, `docs/decisioni-archivio.md` (solo in coda), `docs/index.md` solo se serve.

## Esiti da registrare in §4 (sostituiscono il punto «E1, chiusura della v1.8»)
Verifica finale del giro unico, tutti RIPORTA: compliance-auditor e plan-auditor su E1 v1.9 e catalogo v1.7 (`docs/revisioni/e1-v1.9/`), code-reviewer sul giro 5 (`docs/revisioni/impl-e1/report-code-reviewer-giro5.md`, branch `claude/impl-e1`, commit 13c59ad). Il punto «E1, chiusura della v1.8» di §4 diventa «E1, chiusura definitiva (giro 6)»: si chiude con il giro 6 del codice, E1 v1.10, catalogo v1.8 e la verifica del code-reviewer sui soli punti del giro 6; ciò che resta dopo va in §4 come punto aperto. La versione precedente del punto va in coda all'archivio.

## Decisioni (testo dell'utente alla lettera: «ok», 2026-11-05, alle quattro raccomandazioni del coordinator)
1. `API_ENV` non impostata: opzione (b), blocca l'avvio con un segnale, come un valore fuori dall'insieme chiuso. Motivo: PV-01, una configurazione mancante in produzione non spegne le protezioni. Effetto: in §6 la riga «E1: ambiente e avvio» si aggiorna; il punto di §4 «`API_ENV` assente» si chiude (va in archivio).
2. Regola «`e1.write_tcp_user_timeout_ms` non inferiore a `e1.write_statement_timeout_ms`; altrimenti valore non valido e avvio bloccato con segnale»: confermata. Motivo: applicazione di DX-17. Effetto: in §6 la riga «E1: robustezza della scrittura e ruoli del database» si aggiorna.
3. Chiusura di E1: opzione (a), giro 6 piccolo e definitivo (task `docs/revisioni/impl-e1/task-implementer-giro6.md` sul branch `claude/impl-e1`), E1 v1.10 (task `docs/revisioni/e1-v1.10/task-doc-writer.md`), catalogo v1.8 dal coordinator, verifica del code-reviewer solo sui punti del giro 6; ciò che resta va in §4 senza altri giri. Effetto: in §6 la riga «E1: chiusura della v1.8» diventa «E1: chiusura definitiva» con questo contenuto.
4. Dopo il giro 6, `claude/impl-e1` si unisce in `claude/docs-ondata-1` (codice e documenti in un solo branch). Effetto: riga nuova in §6 «Branch di lavoro».

Per ogni riga di §6 aggiornata, la versione precedente va in coda all'archivio nella sezione «2026-11-05 — righe superate», con la data. Aggiorna «Ultimo aggiornamento» (una riga).

## Vincoli
Stati solo quelli della legenda; «ok» = Decisa. Nessun file fuori dai tre indicati; niente commit. Risposta: solo il JSON dello schema del registrar.
