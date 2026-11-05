# Report code-reviewer, giro 5 — verifica mirata finale 5841994..41607af (PR claude/impl-e1)

Esito: **RIPORTA**. Nessun bloccante. Le correzioni 1-7 e le decisioni dell'utente sono applicate; restano un difetto reale in `close()` (connessione orfana e scrittura dopo la chiusura) e alcuni minori.
Prove: `docs/revisioni/impl-e1/code-reviewer-giro5/` (`conftest.py` con il refuso corretto, `test_giro5.py`, `runs.txt`), non committate. Comando: `PGDATABASE=gravya_e1_review5 pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro5/basetemp docs/revisioni/impl-e1/code-reviewer-giro5/test_giro5.py` → 4 failed, 8 passed (ogni test asserisce il comportamento corretto: FAIL = difetto dimostrato). `basetemp` e `snap_tmp` cancellati; `ls /tmp` invariato (26 voci prima e dopo, nessuna creata da test o script); DB scratch eliminati; nessun ruolo `gravya_e1_*` di prova rimasto (restano `gravya_writer`, `gravya_migrator`, `gravya_e1_so_owner`).

## Refuso nel mio `conftest.py` (giro 4, riga 74)
Confermato: `_registry(sink, extra)` passava `signal_sink=signal_sink`, cioè la funzione-fixture del modulo, invece del parametro `sink`. La registry non usa il sink finché una variabile non è non valida: per questo il difetto restava silenzioso e `test_V1` (che costruisce variabili non valide) falliva con `AttributeError` invece di `VariableUnavailableError`. Lo stesso refuso è nel mio `code-reviewer-giro3/conftest.py` (riga 73), dove non ha effetto perché nessun test di quel pacchetto emette dalla registry. È un errore mio, non dell'implementer. Con la riga corretta (`signal_sink=sink`) nella nuova cartella, V1 per i valori `0` e `"abc"` passa: il rilievo V1 è risolto (`test_V1`, `test_V1b` per la regola relazionale).

## 1. Correzioni 1-7

| Correzione | Esito | Verifica |
|---|---|---|
| 1. `close()` entro il timeout, worker fermo dopo la chiusura | risolta in parte | `test_W2a`/`test_W2b` del giro 4 passano; X2: `close(timeout=2)` con worker fermo e coda piena ritorna entro 2,5 s. Difetto residuo: X1. |
| 2. Connessione propria per i segnali, riconnessione, rollback | risolta | S1b: dopo un blocco di rete sulla connessione propria i segnali successivi arrivano; S2b: il sink da solo resta utilizzabile dopo un errore (`rollback` in `emit`). Limiti dichiarati solo per il sink PostgreSQL (riconosciuto per tipo con `isinstance`: un sottoclasse o un wrapper resta senza guardiano). |
| 3. `kind` del segnale | risolta | S3b: il `kind` arbitrario diventa il segnaposto `kind_non_valido`. |
| 4. Tipo e regola relazionale di `e1.write_tcp_user_timeout_ms` | risolta | V1, V1b. |
| 5. README e test senza `root`/`127.0.0.1:5432` fissi | in gran parte risolta | Vedi sezione 3. |
| 6. Ruolo di prova eliminato | risolta | `pg_roles` dopo le mie 10 corse: nessun `gravya_e1_pwtest`. |
| 7. Testo di 0006 e dello script | risolta | Verificato nel diff: docstring e intestazione dicono ora ciò che fanno le righe; revoca come requisito di deploy nel README. |

Decisioni dell'utente: `e1.write_connect_timeout_s` (intero) applicata, nessuna conversione nel codice; `API_ENV` fuori insieme blocca l'avvio con segnale (E1 passa); chiave HMAC 32 byte invariante. Riserve: il minimo tecnico 2 di `connect_timeout` sta nel campo `min` dell'istantanea, non nel codice (V3: un'istantanea senza `min` accetta 1, che libpq alza a 2); il blocco su `API_ENV` è dentro `if production_override is None`, quindi chi passa `production_override` (anche `True`) non è bloccato né segnalato (E2). Entrambi minori.

## 2. Falliti attesi dichiarati: i motivi reggono?
- `test_S1` (giro 4): regge. Il test sostituisce `h._signals` dopo la costruzione con un sink sulla connessione di un proxy: ora la connessione del chiamante non conta più per scrivere. L'intento (riprendere dopo un blocco di rete) è coperto da S1b, che passa.
- `test_V1` (giro 4): regge, è un refuso mio; V1 rieseguito con la fixture corretta passa.
- `test_V2` (giro 4): regge. Chiama `psycopg.connect(connect_timeout=0.4)` direttamente (fatto di libpq); il codice nuovo non può produrre un valore sotto 2 se l'istantanea ha `min: 2` (V3 per il caso senza `min`).
- `test_N11` (giro 3): regge, usa il nome vecchio `e1.write_connect_timeout_ms`.
- `test_G15b` e `test_R15b`: reggono per decisione (policy `WITH CHECK` sul GUC; `API_ENV` bloccante).
Esiti completi: `tests/` 80 passati; `code-reviewer/` 38 passati + `test_R15b` + errore di teardown noto; `code-reviewer-giro2/` 13 falliti attesi (12 + `test_G15b`); `code-reviewer-giro3/` 3 falliti (N4, N10, N11); `code-reviewer-giro4/` 3 falliti (S1, V1, V2). Nessun fallito inatteso.

## 3. README
Letto e confrontato con il codice. Non ho rieseguito da zero con un altro ruolo (non creo ruoli nel cluster): l'esecuzione con `root` è invariata (`tests/` 80 passati, script non superuser OK nei giri precedenti). Dal testo:
- Il requisito di superuser per il primo `alembic upgrade head` ora c'è ed è motivato (BYPASSRLS), con la revoca come requisito di deploy.
- `tests/` non contiene `user=root` fisso (salvo `_pgconn.py`); `tests/_freezable_proxy.py` e `tests/conftest.py` hanno un ripiego `127.0.0.1`/`5432`/`root` solo se le variabili `PG*` non sono impostate, e i test con proxy dicono il motivo dello skip. Dichiarato nel README.
- Le suite dei revisori richiedono `root` e peer: dichiarato e motivato. Il passo per `code-reviewer-giro4/` nel README non usa `PGDATABASE`, ma l'helper si connette con le variabili libpq: nel mio pacchetto passo `conninfo` esplicito; chi esegue i test dei revisori senza `PGDATABASE` si ritrova sul database predefinito (non è un difetto dell'helper).
- Piccola inesattezza: `DATABASE_URL="postgresql+psycopg://${PGUSER}@${PGHOST}:${PGPORT}/..."` presuppone `PGHOST`/`PGPORT` impostati (con la variabile vuota l'URL è malformato).

## 4. DX-22
Nessun numero di configurazione fisso nuovo nella connessione, nel guardiano o nella regola relazionale (`e1.write_connect_timeout_s`, `e1.write_tcp_user_timeout_ms` e `e1.write_statement_timeout_ms` vengono dall'istantanea; `options=-c statement_timeout=` usa la variabile). Restano due durate fisse: `get(timeout=0.2)` nei due worker (intervallo di controllo di `_closed`) e `close(timeout=5.0)` come valore predefinito (D1, minore).

## 5. Stabilità
10 esecuzioni consecutive (`runs.txt`) di `tests/` e delle quattro suite dei revisori: esiti identici ogni volta, nessun test instabile. `ls /tmp` invariato.
