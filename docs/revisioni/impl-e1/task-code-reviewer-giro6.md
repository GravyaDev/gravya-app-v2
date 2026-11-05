# Task per il code-reviewer: verifica del giro 6 (ultima)

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente: giro 6 definitivo, verifica del code-reviewer solo sui suoi punti; ciò che resta va tra i punti aperti di DECISIONS §4, senza altri giri.

Modifiche: `0865f6e..3797543` sul branch `claude/impl-e1`. Task del giro: `docs/revisioni/impl-e1/task-implementer-giro6.md`; report dell'implementer, sezione «Giro 6».

Verifica solo:
1. X1 (`close()` con riconnessione in corso: nessuna connessione orfana né scrittura dopo la chiusura).
2. D1 (nessuna durata fissa nel codice dei worker e di `close()`; `close(timeout)` ora è obbligatorio).
3. `API_ENV`: decisione dell'utente «`API_ENV` non impostata blocca l'avvio con segnale, come un valore fuori dall'insieme chiuso»; il catalogo v1.8 §18 dice «anche con `production_override`». L'implementer ha reso incondizionato il blocco del valore fuori insieme, ma ha lasciato il blocco per «non impostata» condizionato all'assenza di `production_override`, per non rompere le prove: valuta la conformità alla decisione.
4. V3 (minimo 2 di `e1.write_connect_timeout_s` imposto dal codice).
5. README (`DATABASE_URL`, `API_ENV`, `PGDATABASE` per le prove).
6. Nessuna regressione: suite completa 10 volte, prove dei giri precedenti con gli stessi esiti del giro 5; errore di teardown intermittente dichiarato preesistente.

Esecuzione come nei giri precedenti (`PGDATABASE` per le prove). Prove nuove solo in `docs/revisioni/impl-e1/code-reviewer-giro6/`; nessun file in `/tmp`; non modificare codice, test o file precedenti; niente commit.

Report: `docs/revisioni/impl-e1/report-code-reviewer-giro6.md`. Risposta: solo il JSON dello schema del code-reviewer.
