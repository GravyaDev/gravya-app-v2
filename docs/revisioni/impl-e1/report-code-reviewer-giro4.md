# Report code-reviewer, giro 4 — verifica mirata 3649b15..8dfb1de (PR claude/impl-e1)

Esito: **RIPORTA**. Nessun bloccante. Le correzioni 1-5 sono nel codice e i falliti attesi sono esattamente quelli indicati; restano difetti reali, quasi tutti nel sink dei segnali, in `close()` e nella variabile `e1.write_connect_timeout_ms`.
Prove: `docs/revisioni/impl-e1/code-reviewer-giro4/` (`conftest.py`, `test_giro4.py`, `runs.txt`), non committate. Comando: `PGDATABASE=gravya_e1_review4 pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro4/basetemp docs/revisioni/impl-e1/code-reviewer-giro4/test_giro4.py` → 8 failed, 3 passed (ogni test asserisce il comportamento corretto: FAIL = difetto dimostrato). `basetemp` cancellato, nessun file in `/tmp` (controllato prima e dopo: 0), DB scratch eliminati.

## 1. Correzioni 1-5 e minori

| Punto | Esito | Verifica |
|---|---|---|
| Guardiano per job, rete bloccata | risolto | W1 passa: rete bloccata dopo la connessione, il job è interrotto entro ~`tcp_user_timeout`, perdita contata, dopo lo sblocco le scritture riescono. `shutdown()` sul socket da un altro thread è la tecnica giusta. Rischio residuo: se il timer scatta quando il job sta finendo, interrompe una connessione sana (una perdita e riconnessione); un fd riusato tra la lettura di `pgconn.socket` e lo `shutdown` è una finestra molto stretta. |
| `close()` mai oltre il timeout | **non del tutto** | Vedi rilievi 1 e 2. |
| Segnali con coda e thread propri | risolto per il chiamante | Il test del branch e il mio W/S non mostrano blocchi del chiamante. Il sink però non è sotto gli stessi timeout (rilievo 3). |
| Migrazione 0006 | risolta come «best effort» | Sotto `gravya_migrator` la REVOKE fallisce (nessuna ADMIN OPTION) e resta un `RAISE WARNING`; la revoca reale la fa il passo 5 dello script (superuser). Verificato dopo lo script: `gravya_migrator` non è più membro di `gravya_e1_so_owner`. Senza quel passo manuale l'appartenenza BYPASSRLS resta: requisito di deploy da dichiarare, non una garanzia della migrazione. |
| Policy segnali con `WITH CHECK` | risolta | Script passo 6: INSERT da ruolo non superuser riesce, SELECT negato. `test_G15b` fallito atteso: regge, l'INSERT grezzo senza GUC è rifiutato per scelta; il sink imposta il GUC. |
| `MIGRATION_ROLE` quotato | risolto | M1 passa: un valore con virgolette/`;` è rifiutato. |
| Nome della chiave nei segnali | risolto per le chiavi | Solo le chiavi note. Resta il campo `kind` (rilievo 5). |
| `API_ENV` fuori insieme | accettabile | Segnale `e5.environment_invalid` senza blocco, coerente con `test_R15b`. Solo `production` esatto cambia il comportamento. |

## 2. Falliti attesi
`code-reviewer-giro2/`: 13 falliti = i 12 di prima (G3 ×5, G3b ×3, G7, G8b, G8c, G11) più `test_G15b`: esatto. `code-reviewer-giro3/`: solo `test_N4` e `test_N10`: esatto. `code-reviewer/`: 39 passati + 1 errore di teardown noto (invariato). `tests/`: 69 passati.

## 3. README «Esecuzione locale»
Il README non è eseguibile così com'è da un'altra persona, per tre motivi:
- «**Ruolo senza superuser** per il flusso ordinario» è inesatto per `alembic upgrade head` (e quindi per i test): la migrazione 0005 crea `gravya_e1_so_owner` con `BYPASSRLS` e la 0002 crea `gravya_writer`; un ruolo non superuser non può (M2: `CREATE ROLE ... BYPASSRLS` sotto `gravya_migrator` → `InsufficientPrivilege`). Il README stesso dice altrove che serve un superuser per il bootstrap, ma l'elenco dei passi lo omette.
- «`tests/` **non dipende** da un ruolo `root`» è inesatto: `tests/_freezable_proxy.py::tcp_ok()` e `tests/test_giro4_misc.py` usano `user=root` fisso e TCP su `127.0.0.1:5432` senza leggere `PGUSER`. Senza quel ruolo `tcp_ok()` è falso e i test con proxy (rete bloccata, sink bloccato) vengono **saltati senza avviso**; 4 file hanno `user=root` fisso (R1).
- Le suite dei revisori richiedono `root` con autenticazione peer: dichiarato correttamente, e motivato (file non modificabili).
La parte su `GRAVYA_E1_TEST_DSN`, `DATABASE_URL` obbligatoria e script non superuser è corretta e l'ho eseguita: `PGUSER=root PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh` → OK. Una persona su un altro computer deve anche avere il ruolo `gravya_e1_pwtest` come residuo: il test con password lascia il ruolo (LOGIN, senza password, membro di `gravya_writer`, con CONNECT) nel cluster a ogni corsa; con un'autenticazione `trust` sarebbe un accesso aperto.

## 4. DX-22
`e1.write_tcp_user_timeout_ms` (da definire, valore di sviluppo 5000, min 1) è usata sia come `tcp_user_timeout` di libpq sia come durata massima del job: nessun numero fisso nel guardiano (solo la conversione `/1000`). Difetti: la variabile non è in `_EXPECTED_INT_VARIABLES`, quindi un'istantanea senza `min` accetta `0` (il timer scatta subito e interrompe ogni job) e una stringa solleva `TypeError` non tipizzato (V1); e `e1.write_connect_timeout_ms` passa ms/1000 esatto a libpq, che lo legge come intero: 400 ms diventa «nessun timeout» (V2, rilievo 4).

## 5. Stabilità
10 esecuzioni consecutive (`runs.txt`): `tests/` 69 passed in tutte; `code-reviewer/` 39 passed + 1 errore noto; `code-reviewer-giro2/` 13 falliti attesi + 34 passati; `code-reviewer-giro3/` 2 falliti attesi + 11 passati; nessuna variazione. Nessun file in `/tmp`.
