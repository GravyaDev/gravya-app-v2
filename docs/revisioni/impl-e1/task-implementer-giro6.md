# Task per l'implementer, giro 6 (definitivo)

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisioni dell'utente («ok», 2026-11-05): `API_ENV` non impostata blocca l'avvio con segnale; la regola «`e1.write_tcp_user_timeout_ms` non inferiore a `e1.write_statement_timeout_ms`» è confermata (valore non valido = avvio bloccato con segnale, DX-17); giro 6 piccolo e definitivo, poi verifica del code-reviewer solo su questi punti; ciò che resta va tra i punti aperti, senza altri giri.

Branch `claude/impl-e1` (ora `13c59ad`). Fonte: `docs/revisioni/impl-e1/report-code-reviewer-giro5.md` (prove in `code-reviewer-giro5/`, con il `conftest.py` corretto dal code-reviewer: 4 falliti su 12).

## Correzioni (solo queste)
1. **X1, `close()` con riconnessione in corso.** Dopo `close()` nessuna connessione orfana e nessuna scrittura: il controllo dello stato di chiusura va fatto anche dopo una `psycopg.connect()` completata (se l'helper è chiuso, la connessione appena aperta si chiude subito e il job è contato come perso). Test `test_X1` deve passare.
2. **DX-22, durate fisse.** Togli dal codice l'attesa di 0,2 s dei due worker e il tempo predefinito di 5,0 s di `close()`. L'attesa dei worker non deve essere un numero: usa un meccanismo che non richiede un intervallo di polling (per esempio un valore sentinella o un evento di chiusura che sveglia la coda); il timeout di `close()` è un parametro obbligatorio del chiamante oppure una variabile dell'istantanea «da definire» con valore di sviluppo (scegli e dichiara). Test `test_D1` deve passare.
3. **`API_ENV`.** Il blocco per valore fuori dall'insieme chiuso vale anche con `production_override` impostato (test `test_E2`). Nuova decisione: `API_ENV` **non impostata** blocca l'avvio con segnale (non più «sviluppo con segnale»); i test e il README impostano `API_ENV` esplicitamente.
4. **Minimo di `e1.write_connect_timeout_s`.** Il minimo tecnico 2 è imposto dal codice, non solo dal campo `min` dell'istantanea (test `test_V3`).
5. **README.** `DATABASE_URL` costruito senza variabili non impostate (valori espliciti o default documentati); spiegare `PGDATABASE` per le suite dei revisori; `API_ENV` da impostare.

## Criterio di fine
`tests/` 10 volte verde; `code-reviewer-giro5/` tutto verde (con `PGDATABASE=gravya_e1_review5`); prove dei giri precedenti con gli esiti di oggi salvo quelli cambiati dalla decisione su `API_ENV` (elencali); script non superuser OK; nessun file in `/tmp`; nessun ruolo lasciato. Report: sottosezione «Giro 6» in coda.

## Regole
Nessuna modifica fuori da questi punti. Se un test di prova contraddice il task o una decisione, fermati e chiedi. File di prova dei revisori: solo l'aggiornamento delle fixture per `API_ENV` se indispensabile, in un commit separato citato nel report. Commit piccoli, push, niente merge.
