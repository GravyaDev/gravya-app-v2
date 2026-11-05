# Report code-reviewer, giro 2 — PR claude/impl-e1, head bc32c72 (E1 v1.6, passi 0, 2, 3)

Esito: **BLOCCA**. Diff: `git diff origin/claude/docs-ondata-1...HEAD`; modifiche dopo il primo giro: 8d56cf0..bc32c72.
Prove: `docs/revisioni/impl-e1/code-reviewer-giro2/` (`conftest.py`, `test_giro2.py`, `measure_overhead.py`, `runs.txt`). Non committate.
Esecuzione: `pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro2/basetemp docs/revisioni/impl-e1/code-reviewer-giro2/test_giro2.py` → 43 failed, 4 passed. Ogni test asserisce il comportamento corretto: FAIL = difetto dimostrato, PASS = tentativo di rottura fallito. DB scratch `gravya_e1_review2`, eliminato a fine corsa. `basetemp` e `snap_tmp` cancellati.

## 1. I miei rilievi del giro 1: risolti davvero?

| Rilievo | Stato | Note |
|---|---|---|
| 1 colonne di testo libero | risolto | `name`, `status`, `run_id` e gli altri campi passano da whitelist (R17 passa). I formati sono deboli: vedi rilievi 6 e 7. |
| 2 fail-open se il sink fallisce | risolto | `_safe_emit` con ripiego. Il ripiego però non dice nulla (rilievo 12). |
| 3 TypeError su valore non hashable | risolto | validatori avvolti in `_safe`. Resta `end_segment(kind=...)` sconosciuto (rilievo 5). |
| 4 hash fuori formato | **non risolto** | `re.match(r"^[0-9a-f]{64}$")` accetta 64 cifre + `\n` (65 caratteri). Stesso difetto in tutti gli identificativi (rilievo 1). |
| 5 `writer_transaction` | risolto | Connessione propria, ripristino di ruolo/tenant/timeout del chiamante, rollback sul savepoint (G10 passa). Nuovi problemi di connessione: rilievi 3, 4. |
| 6 HMAC non imposto | risolto per i criteri 11 e 15 | L'helper lo calcola, un hash del chiamante è scartato, chiave vuota/corta non valida. Criterio 16 resta parziale come deciso. |
| 7 nome della chiave nell'audit | risolto in parte | Il formato puntato minuscolo ≤64 lascia passare frasi (G18, minore). |
| 8 buffer asincrono | **non risolto** | Rilievo 2. |
| 9 modifica dopo la chiusura | risolto | Trigger, privilegi di colonna, controllo del `kind` (G11 passa). |
| 10 identificativi opachi | risolto in parte | Rilievo 6. |
| 11 CI/DSN | risolto | `PGHOST=127.0.0.1 pytest tests/` → 33 passed. Azioni e immagine fissate per SHA/digest, lockfile con hash, `fastapi` tolto. CI non eseguita. |
| 12 snapshot malformato | risolto | Resta l'assenza di un tipo atteso per variabile (rilievo 9). |
| 14 partizioni | risolto in parte | Conversione in UTC ok; `ensure_partition` fallisce con un TimeZone di sessione non UTC (rilievo 8). |
| R10d tabella segnali | non conforme alla decisione | Rilievo 10. |
| R11 trace_id altrui | risolto in parte | Rilievo 11. |

### Le tre «correzioni adattate ai miei test»
1. **`production_override` mantenuto: non accettabile.** Nessun test fisso richiede `production_override=False` con `API_ENV=production`: basterebbe che l'override possa solo attivare la guardia, mai spegnerla. Prova G9: con `API_ENV=production` e `production_override=False` le variabili «da definire» sono accettate e l'avvio non blocca (DA-CV-11: la guardia non deve poterla spegnere il codice applicativo).
2. **`SELECT` sulla tabella dei segnali mantenuto: non accettabile come scritto.** La decisione dell'utente (DECISIONS §6, 2026-11-05) dice «tabella dei segnali provvisoria, solo inserimento». Il test R10d chiede «0 righe» e non «errore», ma è il test a doversi adeguare alla decisione, non viceversa. RLS impedisce la lettura cross-tenant (verificato: R10d passa), quindi l'isolamento regge; resta la violazione della decisione presa. Prova G15. Inoltre il sink PostgreSQL non imposta `app.tenant_id`: con RLS forzata funziona solo da superuser (G15b).
3. **`trace_id` mai esistito non rifiutato: accettabile**, con riserva. Rifiutarlo farebbe perdere i segmenti quando la scrittura della traccia fallisce (fail-open) o arriva dopo. Il controllo copre solo il caso in cui esista già una traccia di un altro tenant, e ha tre problemi: G8a, G8b, G8c (rilievi 11, 13).

## 2. conftest.py (commit 309785e)
`git diff 8d56cf0..bc32c72 -- docs/revisioni/impl-e1/code-reviewer/` mostra **una sola riga aggiunta** (`e1.write_statement_timeout_ms` in `prod_variables`). `test_repro_rilievi.py` è invariato. OK.

## 3. Codice nuovo

- **Connessione propria e scrittura:** non è una scrittura asincrona in background né un buffer. È una scrittura **sincrona** nel thread del chiamante, con un semaforo non bloccante sul numero di tentativi e un lock bloccante sulla connessione unica. Vedi rilievi 2, 3, 4.
- **`writer_transaction`:** il ripristino è corretto anche dopo un'eccezione dentro la transazione del chiamante (G10).
- **SECURITY DEFINER (`gravya_e1_trace_owned_by_other_tenant`):** nessuna escalation trovata (restituisce solo un booleano, `EXECUTE` solo al writer, `search_path` fissato; manca `pg_temp` ma l'effetto resta sul risultato della propria chiamata). Trovati: oracolo di esistenza (G8b, minore), dipendenza dal fatto che l'owner sia superuser (G8c) e uso come arma contro un altro tenant (G8a).
- **Trigger e privilegi di colonna:** funzionano e non sono aggirabili dal writer (G11 passa: UPDATE su riga chiusa rifiutato, UPDATE di `tenant_id` negato, trigger presente sulle partizioni).
- **Formati della whitelist:** `$` senza `fullmatch` (rilievo 1); `uuid.UUID()` accetta forme non canoniche (rilievo 1); il formato `prefisso_corpo` non è un vocabolario (rilievo 6).
- **HMAC dall'helper:** verificato (test 11/15 riscritti e la mia R5/R12).

## 4. DX-22
Nessun valore di configurazione fisso nel codice di `src/`, salvo: `_EPOCH_YEAR = 2000` (invariante di allineamento, accettabile: non è una durata né una soglia), `MIN_KEY_BYTES = 16` (soglia di sicurezza dichiarata come invariante da confermare con A6: accettabile solo come provvisoria), e i formati della whitelist (invarianti per decisione). Il floor `max(1, write_buffer_size)` e le lunghezze nei formati sono valori fissi minori. `e1.write_statement_timeout_ms` è ora una variabile (ok). Nessun URL, nessun modello, nessun segreto nel codice.

## 5. Stabilità
- 12 esecuzioni consecutive di `tests/` + `code-reviewer/` (72 test): 12 su 12 verdi (`runs.txt`).
- Il test instabile è, con ogni probabilità, `tests/test_criterio6_overhead.py`. Con `e1.overhead_p95_ms` = 5 ms, su 40 ripetizioni del benchmark senza carico il p95 è tra 1,9 e 4,1 ms; in un'altra serie da 20 il massimo è stato 4,996 ms. Con 4 processi che occupano la CPU (la macchina ha 4 core) il p95 supera la soglia in 17 ripetizioni su 20 (`measure_overhead.py`). Il fallimento visto dal coordinator coincide con un carico concorrente (per esempio un altro revisore in esecuzione). Non ho potuto riprodurre il fallimento nella suite completa. Margine insufficiente, e la misura include 6 istruzioni sincrone per segmento.
- Secondo candidato: `test_R8` (soglia di attesa 3 s con timeout 2 s): margine di 1 s, non osservato fallire.

## 6. Altri punti
- Gli elementi aggiunti dall'implementer fuori dal task (segnali `trace.update_target_not_found`, `trace.trace_already_closed`, ecc.) sono coerenti con «UPDATE con 0 righe contato e segnalato».
- Nessun file del repository contiene istruzioni rivolte a un agente.
