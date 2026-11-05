# Task per l'implementer, giro 5: ultime correzioni dopo la verifica mirata del giro 4

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisioni dell'utente: «ok» ai punti 1-5 del coordinator (DECISIONS §6, righe del 2026-11-05 registrate in parallelo dal registrar).

Branch `claude/impl-e1` (ora `5841994`), stesso perimetro (E1 §9 passi 0, 2, 3). Fonti: `docs/revisioni/impl-e1/report-code-reviewer-giro4.md` (prove in `code-reviewer-giro4/`: 8 falliti su 11), `docs/revisioni/e1-v1.8/report-compliance-auditor.md` (rilievo sul `connect_timeout`, sul branch `claude/docs-ondata-1`). Area di lavoro: worktree del branch (sulla piattaforma `/workspace/wt-impl-e1`; in locale la copia di lavoro del branch).

## Criterio di fine
1. Passano `tests/` (10 esecuzioni consecutive) e `code-reviewer-giro4/` salvo i falliti attesi sotto; le prove dei giri 1-3 con gli esiti di oggi, salvo quelli cambiati da queste decisioni (elencali).
2. Il README «Esecuzione locale» è eseguibile da un'altra persona su un altro computer: provalo da zero con un ruolo PostgreSQL diverso da `root`.
3. Nessun file in `/tmp`, nessun ruolo di prova lasciato nel cluster.
4. Report: sottosezione «Giro 5» in coda, rilievo per rilievo con il test che lo prova.

## Decisioni dell'utente da applicare
- **Tempo massimo di collegamento in secondi.** Rinomina `e1.write_connect_timeout_ms` in `e1.write_connect_timeout_s` (intero, minimo tecnico 2, perché libpq legge secondi interi e tratta i valori inferiori a 2 come 2, e 0 come attesa infinita); valore di sviluppo 2. Nessuna conversione nel codice.
- **`API_ENV` fuori dall'insieme chiuso** (`production`, `development`, `test`): l'avvio si **blocca** con segnale. Assente resta «sviluppo» con segnale (decisione precedente). `test_R15b` di `code-reviewer/` diventa fallito atteso per decisione dell'utente.
- **Chiave HMAC di almeno 32 byte:** invariante provvisoria fino ad A6 (nessuna variabile).

## Correzioni (code-reviewer giro 4)
1. **`close()` (W2a, W2b).** Mai oltre il timeout: nessun lock conteso con una riconnessione in corso; il worker controlla lo stato di chiusura e non si riconnette né scrive dopo `close()`; il conteggio dei job rimasti non gira in concorrenza con il worker.
2. **Sink dei segnali (S1, S2).** Il thread dei segnali usa una **propria** connessione (parametri passati all'helper come per la scrittura), con gli stessi limiti (statement, connect, tcp_user_timeout, keepalive, guardiano), riconnessione dopo un errore e `rollback` dopo un INSERT fallito; mai la connessione del chiamante, niente riconoscimento per attributi privati. Un sink diverso da PostgreSQL resta possibile tramite interfaccia, ma il testo del report deve dire che i limiti valgono solo per il sink PostgreSQL.
3. **`kind` nel segnale di scarto (S3).** Solo valori del vocabolario dei `kind`; altrimenti segnaposto.
4. **`e1.write_tcp_user_timeout_ms` (V1).** Nell'elenco dei tipi attesi (intero, minimo tecnico 1); regola relazionale: non inferiore a `e1.write_statement_timeout_ms` (valore non valido altrimenti, con segnale).
5. **README e test (R1, M2).** Il README dice il vero: il primo avvio delle migrazioni (creazione dei ruoli, tra cui quello con `BYPASSRLS`) richiede un superuser; poi `gravya_migrator`. Nessun test usa `user=root` o `127.0.0.1:5432` fissi: leggono le variabili PG*; un test saltato per mancanza di prerequisiti lo dice nel messaggio.
6. **Ruolo di prova (`gravya_e1_pwtest`).** Il test con password lo elimina alla fine (`DROP OWNED`, `DROP ROLE`).
7. **Migrazione 0006 e script.** Correggi il docstring di 0006 e l'intestazione dello script su `CREATE ON SCHEMA public` (serve durante la migrazione, va revocato dopo); nel README la revoca dell'appartenenza e del `CREATE` è un passo obbligatorio del superuser dopo le migrazioni (requisito di deploy).

## Falliti attesi ammessi
`code-reviewer-giro4/`: nessuno, salvo test che asseriscono un comportamento contrario alle decisioni sopra (elencali con il motivo). `code-reviewer/test_R15b` per la decisione su `API_ENV`. Se un test di prova contraddice il task o una decisione in altri punti, fermati e chiedi. File di prova dei revisori: solo l'aggiornamento delle fixture di istantanea per la variabile rinominata (commit separato).

## Regole
Commit piccoli, push, niente merge. Non modificare `docs/` salvo il report e le fixture come sopra. Percorsi relativi nel README e nel report.
