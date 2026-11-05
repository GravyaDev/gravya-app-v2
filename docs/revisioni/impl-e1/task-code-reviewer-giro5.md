# Task per il code-reviewer: verifica mirata finale del giro 5 di E1

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente: ultimo giro unico, poi una sola verifica mirata (DECISIONS §6, «E1: chiusura della v1.8»).

PR: branch `claude/impl-e1`, base `claude/docs-ondata-1`; modifiche da verificare: `5841994..41607af` (task del giro 5 e giro 5). Task del giro: `docs/revisioni/impl-e1/task-implementer-giro5.md`; report dell'implementer, sezione «Giro 5»; README «Esecuzione locale».

Decisioni dell'utente applicate (non contestarle, verifica che siano applicate): `e1.write_connect_timeout_s` in secondi interi, minimo 2; `API_ENV` fuori dall'insieme chiuso blocca l'avvio con segnale (`test_R15b` di `code-reviewer/` fallito atteso); chiave HMAC minima 32 byte invariante provvisoria.

Cosa verificare:
1. Che le correzioni 1-7 del task siano risolte nel codice: `close()` entro il timeout e worker fermo dopo la chiusura; connessione propria del thread dei segnali con gli stessi limiti, riconnessione e rollback; `kind` del segnale limitato al vocabolario; tipo e regola relazionale di `e1.write_tcp_user_timeout_ms`; README eseguibile altrove (superuser per il primo avvio delle migrazioni, nessun test con `root` o `127.0.0.1:5432` fissi); ruolo di prova eliminato; testo di 0006 e dello script.
2. Falliti attesi dichiarati dall'implementer, da giudicare: in `code-reviewer-giro4/` `test_S1` (assunto superato dalla connessione propria), `test_V1` (refuso nel tuo `conftest.py`, riga 74: `signal_sink=signal_sink` invece di `sink`; verificato dal coordinator), `test_V2` (proprietà di libpq); in `code-reviewer-giro3/` `test_N11` (nome vecchio della variabile); `test_G15b` e `test_R15b` per decisione. Puoi correggere il refuso del tuo `conftest.py` nella tua cartella di prove nuova, non nel file esistente.
3. DX-22: nessun numero di configurazione fisso nel codice nuovo.
4. Stabilità: suite completa 10 volte.

Esecuzione: `tests/` con `.venv`; prove con `PGDATABASE` del loro database (`gravya_e1_review`, `gravya_e1_review2`, `gravya_e1_review3`, `gravya_e1_review4`); script: `PGUSER=<superuser> PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh`.

Prove nuove solo in `docs/revisioni/impl-e1/code-reviewer-giro5/`; `--basetemp` lì dentro, cancellato alla fine; nessun file in `/tmp`. Non modificare codice, test o file precedenti; niente commit.

Report: `docs/revisioni/impl-e1/report-code-reviewer-giro5.md`. Risposta: solo il JSON dello schema del code-reviewer.
