# Report code-reviewer, giro 3 — PR claude/impl-e1, head d3cb476 (E1 v1.6, passi 0, 2, 3)

Esito: **RIPORTA**. Nessun bloccante rimasto: i 5 bloccanti del giro 2 sono risolti. Restano limiti da riportare (stallo di rete sul thread di sfondo, `close()` che può appendersi) e minori. Nessun test del branch fallisce.
Prove: `docs/revisioni/impl-e1/code-reviewer-giro3/` (`conftest.py`, `test_giro3.py`, `runs.txt`). Non committate. Esecuzione: `pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro3/basetemp docs/revisioni/impl-e1/code-reviewer-giro3/test_giro3.py` → 7 failed, 6 passed (ogni test asserisce il comportamento corretto: FAIL = difetto dimostrato). DB scratch `gravya_e1_review3`, eliminato. `basetemp`, `snap_tmp`, `basetemp_sub` cancellati; cancellati anche i file `/tmp/tmp*.json` lasciati dai test del branch durante le mie corse (53).

## 1. Diff dei miei file di prova
`git diff 7dfc08d..HEAD -- code-reviewer/ code-reviewer-giro2/`: solo le modifiche autorizzate. 13 righe `assert h.flush(timeout=5)` (7 in `test_repro_rilievi.py`, 6 in `test_giro2.py`, nei test indicati), la correzione di `test_R10d` (accetta `InsufficientPrivilege` o 0 righe) e le variabili nuove nei due `conftest.py` (`e1.write_connect_timeout_ms` e tre keepalive). Nient'altro. OK.

## 2. I 5 bloccanti del giro 2

| Bloccante | Esito | Come verificato |
|---|---|---|
| Scrittura asincrona, chiamante mai bloccato | risolto per `start_*`/`end_*` | `test_G4a/G4b/G5` passano. N1: con rete bloccata dopo la connessione 150 `start_segment` tornano in <1 s, le eccedenze sono perdite contate (≥49). Limiti sotto (N2, N3). |
| Formati `fullmatch`, UUID canonici | risolto | `test_G1/G1b/G2/G2b` passano. |
| Tenant di contesto | risolto con riserva | Con `API_ENV=production` reale il contesto è obbligatorio (segnale e `TenantContextRequiredError`); N8: un modello di altro tenant è scartato con segnale e non scritto. Riserve: N9 (UUID in maiuscolo nel contesto rifiuta tutto), N10 (con `production_override` senza contesto nessun controllo: scelta del coordinator, accettabile solo perché un ambiente senza `API_ENV` è «sviluppo» per decisione, con il segnale `e5.environment_undeclared`). |
| Segnali solo INSERT, funzionanti da non superuser | risolto | `test_G15/G15b` passano; `PGUSER=root PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh` → OK (migrazioni con `gravya_migrator`, scrittura del helper con un ruolo a password, trigger e funzione). La policy RLS dei segnali ora è `USING (true) WITH CHECK (true)`: la riservatezza dipende solo dal privilegio. Il writer può inserire segnali con qualunque `tenant_id` (minore). |
| Funzione SECURITY DEFINER | risolto | N5: owner dedicato `NOLOGIN`, `BYPASSRLS`, non superuser; `search_path = pg_catalog, public, pg_temp`; `EXECUTE` non concesso a PUBLIC; chiamata come writer sotto RLS vede la traccia dell'altro tenant. N6: `start_trace` con il `trace_id` di un altro tenant è scartato e non blocca i segmenti legittimi. |

## 3. Falliti attesi dichiarati: i motivi reggono?
- **G3/G3b (`mario_rossi`, `api.openai.com`)**: reggono come decisione (nessun vocabolario chiuso deciso), ma il rischio resta e va in E1 v1.7: una PII con prefisso e underscore passa per i campi generici (`opaque_id`, `model_identifier`: fino a 40 e 128 caratteri liberi).
- **G7**: regge. Era una proprietà di psycopg; il test sostitutivo `tests/test_giro3_misc.py::test_helper_scrive_con_connessione_propria_a_password_via_tcp` usa un ruolo diverso da `root` con `scram-sha-256` (verificato nella regola `pg_hba` generica), quindi la password è davvero usata.
- **G8b**: **non regge del tutto.** Il report dice che il parametro tenant rimosso «chiude l'oracolo», ma il tenant ora sta nel GUC `app.tenant_id`, che il writer imposta liberamente. N4 dimostra lo stesso oracolo con una firma a un parametro: `true` per un `trace_id` esistente presso un altro tenant, `false` per uno inesistente. È un limite intrinseco di un controllo di unicità: da dichiarare, non da dire «chiuso» (minore).
- **G8c**: regge. N5 prova l'efficacia reale della funzione con owner `BYPASSRLS` (il test originale eseguiva il SELECT come writer, non la funzione).
- **G11**: regge. Usa `run_id="run-1"`, ora non valido, quindi la traccia non si scrive. N7 ripete lo stesso scenario con un `run_id` UUID: trigger e privilegi di colonna funzionano.

## 4. Stallo di rete dopo la connessione (non verificato dall'implementer)
- N1 (passa): il chiamante non si blocca; la coda si riempie e le perdite sono contate.
- **N2 (fallisce):** dopo 12 s di rete bloccata il thread di sfondo è ancora fermo, con `statement_timeout`, `connect_timeout` e keepalive a 2/2/10 s. Non c'è un timeout lato client sul socket (né `tcp_user_timeout`). Il tracing è fermo finché il kernel non chiude la connessione. Fail-open tiene, ma la disponibilità no.
- **N3 (fallisce):** `close()` esegue `self._queue.put(_SENTINEL)` bloccante e senza timeout: con il worker fermo e la coda piena `close(timeout=2)` non ritorna entro 8 s. Lo spegnimento si appende.

## 5. DX-22
Nuove variabili (`e1.write_connect_timeout_ms`, keepalive idle/interval/count) nell'istantanea come «da definire» con valore di sviluppo e minimo tecnico 1: ok. Costanti rimaste: `keepalives=1` (flag, ok), formati e lunghezze della whitelist (invarianti per decisione), `_EPOCH_YEAR`, `MIN_KEY_BYTES=32` (provvisoria, ok). **`max(1, round(ms/1000))`** in `_get_own_connection`: `connect_timeout` è in secondi interi, quindi 400 ms diventa 1 s e 2500 ms diventa 2 s (arrotondamento al pari): correzione silenziosa del valore dell'istantanea, esattamente ciò che il task vietava (N11, minore). Nessun URL né segreto nel codice.

## 6. File temporanei
`tests/test_criterio5_fail_open.py`, `tests/test_giro3_misc.py` e `scripts/_verify_nonsuperuser.py` usano `tempfile.mkstemp(...)` senza cancellare il file (nei test con `[1]`, quindi anche con il descrittore aperto). Ogni corsa di `tests/` lascia 4-5 file `/tmp/tmp*.json` (53 accumulati nelle mie corse). Contenuto: copia di un'istantanea, non segreta; permessi 0600. Violano la regola comune 6 (niente file temporanei in /tmp) e lasciano descrittori aperti. N13. Rilievo minore, correzione banale (`tmp_path`).

## 7. Stabilità
10 esecuzioni consecutive (`runs.txt`): `tests/` 65 passed in tutte; `code-reviewer/` 39 passed + 1 error (errore di teardown della mia fixture `DROP DATABASE` con sessioni dell'helper ancora aperte: i test fissi non chiamano `close()`; non è un test fallito, ma `pytest` esce con codice ≠ 0); `code-reviewer-giro2/` 35 passed + 12 falliti attesi, identici. Con `PGHOST=127.0.0.1`: `tests/` 65 passed. Criterio 6: ora misura il costo di accodamento, 0 falliti su 10 con 4 processi che occupano la CPU. Nessun test instabile osservato. Race `_pending` (incremento dopo `put_nowait`): contatore mai negativo in N12 (nessun difetto osservato).

## 8. Altro
Nessun file del repository contiene istruzioni rivolte a un agente.
