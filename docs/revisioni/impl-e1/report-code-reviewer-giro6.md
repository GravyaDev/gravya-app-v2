# Report code-reviewer, giro 6 — verifica mirata (0865f6e..3797543, PR claude/impl-e1)

Esito: **BLOCCA**, per un solo punto: la decisione dell'utente su `API_ENV` non impostata non è applicata come scritta (punto 3). Gli altri cinque punti sono a posto o hanno solo difetti minori.
Prove: `docs/revisioni/impl-e1/code-reviewer-giro6/` (`runs.txt`; l'esperimento sulla copia patchata è descritto sotto, la copia è stata cancellata). Nessun file in `/tmp` (26 voci prima e dopo), `basetemp` cancellati, DB scratch eliminati, nessun ruolo di prova rimasto (restano `gravya_writer`, `gravya_migrator`, `gravya_e1_so_owner`).

## 1. X1 — risolto
`_get_own_connection` e `_get_own_signal_connection` ricontrollano `_closed` dopo il lock e dopo `psycopg.connect()`; se chiuso, la connessione appena aperta è chiusa e il job conta come perso. `test_X1` di `code-reviewer-giro5/` passa (12 passati su 12), con il job non scritto e nessun backend in più.

## 2. D1 — risolto
Nel sorgente non resta nessuna durata fissa: il `get(timeout=0.2)` dei due worker è tolto, il sentinella è consegnato da un thread di appoggio con `put()` bloccante (X2: `close(timeout=2)` con worker fermo e coda piena ritorna entro 2,5 s), `close(timeout)` è obbligatorio (`TypeError` senza argomento). Restano solo i tempi presi dall'istantanea (guardiano) e l'aritmetica di `deadline`. `test_D1` passa.
Nota minore: con coda profonda e rete sana il worker consuma i job rimasti anche dopo che `close()` ha rinunciato ad aspettare (il sentinella arriva dopo di loro): la scrittura in volo dopo `close()` resta possibile, e `_drain_remaining_as_lost` gira solo se i thread sono già fermi. Dichiarato dall'implementer.

## 3. `API_ENV` non impostata — NON conforme alla decisione
Testo deciso. DECISIONS §6 (2026-11-05): «`API_ENV` in un insieme chiuso (`production`, `development`, `test`): un valore fuori insieme, **o `API_ENV` non impostata, blocca l'avvio con segnale**». Catalogo v1.8 §18: «un valore fuori dall'insieme o la variabile non impostata bloccano l'avvio con segnale, **anche con `production_override`**». Nessuno dei due ammette un'eccezione per «non impostata».
Codice. Il valore fuori insieme blocca sempre (test E2 passa). «Non impostata» blocca solo se `production_override is None` (`if self._production_override is None and not is_declared()`): con `production_override=True` o `False` l'helper parte senza `API_ENV`, senza blocco né segnale. È un'eccezione non decisa dall'utente: contraddice il catalogo e il README la presenta come regola.
La giustificazione dell'implementer («un blocco incondizionato avrebbe rotto quasi tutte le prove bloccate») regge solo se `API_ENV` non è esportata. Verificato con una copia patchata del codice nella mia cartella (blocco incondizionato, copia cancellata a fine prova):
- senza `API_ENV`: 36 falliti su `tests/`, 4 su giro 5, 15 su giro 1, 23 su giro 2, 12 su giro 3, 7 su giro 4 (la giustificazione, in questo caso, è vera);
- con `API_ENV=development` esportata (come il README ora chiede): `tests/` 86 passati e 1 fallito (un test proprio dell'implementer che asserisce il comportamento condizionato), giro 5 12 su 12, giro 1 1 fallito (`test_R15b`) + 1 errore, giro 2 13 falliti, giro 3 3 falliti, giro 4 3 falliti: **esiti identici a oggi**.
Quindi la conformità si ottiene senza toccare i file bloccati dei revisori: togliere la condizione `self._production_override is None and`, impostare `API_ENV=development` nell'ambiente (o in una fixture autouse) e aggiornare il test proprio `test_api_env_assente_non_blocca_con_production_override_esplicito`. Se l'utente vuole invece l'eccezione per `production_override`, il testo del catalogo §18 e di DECISIONS §6 va corretto.
Il task diceva «se un test di prova contraddice una decisione, fermati e chiedi»: l'implementer ha deciso da solo.

## 4. V3 — risolto
`_HIGHER_TECHNICAL_MINIMUMS` impone 2 a `e1.write_connect_timeout_s` anche senza `min` nell'istantanea. `test_V3` passa; 1 è rifiutato con segnale, 2 è valido.

## 5. README
- `DATABASE_URL` con valori predefiniti (`${PGUSER:-root}@${PGHOST:-localhost}:${PGPORT:-5432}`): corretto e non presuppone variabili esportate. Minore: i predefiniti `localhost`/TCP differiscono da quelli di `tests/` (socket con peer quando `PGHOST` è vuoto).
- `API_ENV` documentata e impostata nell'esempio, ma presentata con l'eccezione `production_override` per l'assente (vedi punto 3).
- `PGDATABASE` per le suite dei revisori: verificato. Giro 3, 4, 5 danno lo stesso esito senza `PGDATABASE` (3 falliti, 3 falliti, 12 passati); giro 1 e 2 la richiedono (dichiarato). La riga su `PYTHONPATH` tolta è corretta.

## 6. Nessuna regressione
10 esecuzioni consecutive (`runs.txt`) di `tests/` e delle cinque suite dei revisori: `tests/` 87 passati ogni volta; giro 1: 1 fallito (`test_R15b`) + 1 errore di teardown; giro 2: 13 falliti attesi + 34 passati (in 3 corse su 10 anche 1 errore di teardown); giro 3: 3 falliti attesi (N4, N10, N11); giro 4: 3 falliti attesi (S1, V1, V2); giro 5: 12 passati. Stessi esiti del giro 5.
L'errore di teardown intermittente (`DROP DATABASE` con sessioni aperte) è davvero preesistente: eseguendo `code-reviewer-giro2/` 25 volte sul codice di `41607af` (copia ricavata con `git archive`, cancellata) è comparso 3 volte, sul codice attuale 4 volte su 25. Non è una regressione del giro 6.
