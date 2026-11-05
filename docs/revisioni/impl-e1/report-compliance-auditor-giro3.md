# Report compliance-auditor, giro 3 — PR claude/impl-e1 (head d3cb476)

Diff a tre punti `origin/claude/docs-ondata-1...HEAD`, modifiche bc32c72..d3cb476. Sola lettura, nessun test eseguito (niente script, niente database). Norme dal registro v1.7 (GDPR 5, 25, 32 ✔; NIS2 art. 21 ✔; Reg. 2024/2690 ✔). Nessuna norma da aggiungere al registro.

**Esito: RIPORTA.** Nessun bloccante. I 4 rilievi del giro 2 sono risolti nel codice, con un residuo ciascuno; 3 rilievi da riportare nuovi e 8 minori.

## Verifica dei rilievi del giro 2

| Rilievo | Esito | Dove |
|---|---|---|
| G2-01 funzione `SECURITY DEFINER` e `FORCE` RLS | RISOLTO nel codice, residuo G3-02 | `0005_giro3_fixes.py` 93-115: un solo parametro, tenant dal GUC, proprietario `gravya_e1_so_owner` `NOLOGIN BYPASSRLS`, `search_path = pg_catalog, public, pg_temp`, `REVOKE ALL FROM PUBLIC`, `EXECUTE` solo al writer, `SELECT` solo su `gravya_traces`. `start_trace` ora fa lo stesso controllo (`tracing.py` handler di inserimento). Test `test_funzione_security_definer_bypassa_rls_sotto_ruolo_non_superuser`. |
| G2-02 tenant di contesto | RISOLTO secondo la scelta del coordinator, residuo minore | `tracing.py` 195-215 (`_resolve_tenant`, `_enforce_tenant_context`): con contesto il GUC viene dal contesto, un modello con tenant diverso è scartato con segnale in produzione, errore altrove. Con `API_ENV=production` reale il contesto è obbligatorio (`TenantContextRequiredError` e segnale). |
| G2-03 segnali da ruolo non superuser | RISOLTO nel disegno, NON PROVATO, vedi G3-03 | `0005` 117-127: il writer perde `SELECT`, policy `USING (true) WITH CHECK (true)`. |
| G2-04 `production_override` | RISOLTO | `tracing.py _is_production` e `variables.py`: `if override: True` altrimenti `is_production()`. Test `test_production_override_false_non_spegne_la_guardia`. |

## Verifica dei minori del giro 2

- G2-05 formati: UUID canonico (`str(UUID(x)) == x`), `fullmatch` ovunque, `run_id` UUID, `reviewer_ref` = `reviewer_` + UUID canonico, hash `[0-9a-f]{64}` con `fullmatch`. Resta `opaque_id` (vedi G3-08), ora dichiarato nel docstring e nel report.
- G2-06 `raw_arguments`: `Field(repr=False)` e azzeramento dopo il calcolo dell'HMAC (`_inject_args_hash`, anche in caso di errore). Risolto.
- G2-07 scrittura asincrona: coda limitata `e1.write_buffer_size`, thread con connessione propria da `conninfo` (mai dal chiamante), `connect_timeout`, keepalive e `statement_timeout` da variabili. Risolto per le tracce; per i segnali vedi G3-01.
- G2-08 variabili: tipo intero atteso per le variabili di E1, `min`/`max` non numerici bloccano con segnale, minimo tecnico 1. Risolto.
- G2-09 `kind` sconosciuto: scarto con segnale in produzione. Risolto. Il CHECK sulle chiavi nel DB non è stato aggiunto (la whitelist resta applicativa, mitigata da privilegi di colonna e trigger): residuo minore già noto.
- G2-10 CI: aggiunto il job `test-non-superuser` (`permissions: contents: read`, action e immagine fissate). Resta `pip install --no-deps -e .` con isolamento di build e `apt-get` (G3-09).
- G2-11 contatori in memoria: dichiarato come limite, accettato finché A5 non definisce la tabella.

## Valutazione del ruolo con `BYPASSRLS` (richiesta del coordinator)

Il disegno è accettabile. Il ruolo `gravya_e1_so_owner` è `NOLOGIN`, non superuser, ha solo `SELECT` su `gravya_traces` (non sui segmenti, nessun `INSERT`/`UPDATE`), possiede solo la funzione; l'attributo `BYPASSRLS` non si eredita per appartenenza al ruolo (serve `SET ROLE`); il corpo della funzione restituisce un booleano e il `search_path` è sicuro. Il rischio residuo è operativo e riguarda chi può fare `SET ROLE` a quel ruolo (G3-02). L'oracolo di esistenza di un `trace_id` altrui resta trascurabile con UUID e con il solo writer come chiamante.

## Rilievi nuovi

### G3-01 DA RIPORTARE — I segnali sono scritti in modo sincrono e senza timeout: il fail-open non è garantito con il DB bloccato (E1 §5 e §6; DX-10 C2; NIS2 art. 21(2)(c) come progetto) — dedotto
- `tracing.py` `_safe_emit` (righe 276-306 del giro 2, invariate) viene chiamata sul thread del chiamante per scarti, mismatch di tenant e coda piena, e dal thread di scrittura per le perdite. `PostgresSignalSink.emit` (`signals.py`) fa un INSERT e un `commit()` sulla connessione che gli ha dato l'applicazione, senza `connect_timeout`, keepalive o `statement_timeout` (quei parametri valgono solo per la connessione del thread di scrittura).
- Con un DB che non risponde, un'emissione si blocca; se la connessione è condivisa (psycopg serializza con un lock) si bloccano anche le altre emissioni, comprese quelle del chiamante: la promessa «il chiamante non aspetta» vale per le scritture ma non per i segnali. I test di fail-open usano un sink su connessione chiusa (errore immediato) o in memoria, non una connessione appesa.
- Proposta: passare anche i segnali da una coda con thread e timeout propri (o imporre al sink una connessione con gli stessi timeout) e aggiungere un test con connessione bloccata.

### G3-02 DA RIPORTARE — Appartenenza permanente al ruolo `BYPASSRLS` e errori inghiottiti nelle migrazioni (isolamento tra tenant, DX-18/DX-19, NIS2 art. 21(2)(i) come progetto) — verificato
- `0005_giro3_fixes.py` 56-66 e 81-91: `GRANT gravya_migrator TO current_user` e `GRANT gravya_e1_so_owner TO current_user` dentro `EXCEPTION WHEN OTHERS THEN NULL`; `scripts/test-non-superuser.sh` concede `gravya_e1_so_owner` a `gravya_migrator` e `USAGE, CREATE ON SCHEMA public` al proprietario della funzione. Dopo la migrazione chi usa il ruolo di migrazione può fare `SET ROLE gravya_e1_so_owner` e leggere `gravya_traces` di tutti i tenant senza alcun log, fuori dal regime di accesso del superadmin (aggregati di default, log degli accessi). Il `CREATE` sullo schema `public` per il proprietario non serve alla funzione. Gli errori dei `GRANT` sono ignorati, quindi un grant fallito non si vede.
- Proposta: dopo `ALTER FUNCTION … OWNER TO` revocare l'appartenenza (`REVOKE gravya_e1_so_owner FROM gravya_migrator`) e togliere `CREATE` su `public`; non inghiottire gli errori (almeno un `RAISE WARNING`); dichiarare nel documento di deploy che il ruolo di migrazione non è mai il ruolo applicativo e non ha accesso ai dati a runtime.

### G3-03 DA RIPORTARE — Il sink dei segnali e la lettura dei segnali non sono provati con un ruolo non superuser (DX-10 C2; criterio di fine 2) — verificato
- `scripts/_verify_nonsuperuser.py` usa `InMemorySignalSink`; i test che usano `PostgresSignalSink` (criteri 4, 16, 5) la costruiscono su `admin_conn` (superuser). Nessun test dimostra che `INSERT` di un segnale con tenant riesce con un ruolo membro di `gravya_writer` (che ha il solo `INSERT`) e che un `SELECT` della tabella da quel ruolo è negato.
- La policy `USING (true) WITH CHECK (true)` con RLS forzata non isola nulla: la riservatezza dipende solo dai privilegi. Accettabile per la decisione dell'utente («solo inserimento»), ma quando A5 concederà un `SELECT` bisognerà aggiungere l'isolamento o le viste aggregate (DX-19).
- Proposta: aggiungere allo script o ai test una scrittura con `PostgresSignalSink` da ruolo non superuser e una lettura negata; annotare per A5 che la policy `true` non va riusata per la lettura.

## Minori

### G3-04 MINORE — La guardia di produzione dipende da un confronto esatto con `production` (DX-22) — verificato
`config/env.py`: `os.environ.get("API_ENV") == "production"`. Un valore impostato ma scritto diversamente («prod», «Production») non produce alcun segnale e spegne tutte le garanzie che dipendono dalla produzione (contesto del tenant obbligatorio, scarto con segnale, variabili «da definire»). Il segnale esiste solo per l'ambiente non impostato. Proposta: segnale (o rifiuto) per un valore non appartenente a un insieme chiuso.

### G3-05 MINORE — Il nome della chiave nei segnali può portare fino a 64 caratteri di testo minuscolo (GDPR 5(1)(c)) — verificato
`whitelist.py` `safe_signal_key_name`: oltre alle chiavi note passa qualunque identificatore minuscolo a 1-4 segmenti da 20 caratteri (`ciao.mario.rossi`). È una chiave, non un valore, e rispetta la decisione sul formato, ma resta un canale di testo. Proposta: riportare solo le chiavi note e, per le altre, la sola lunghezza.

### G3-06 MINORE — Arrotondamento silenzioso del timeout di connessione (DX-22, G13) — verificato
`tracing.py` `_get_own_connection`: `connect_timeout_s = max(1, round(ms/1000))`: 500 ms diventa 1 s, 2500 ms diventa 2 s. È la «correzione silenziosa» che G13 chiedeva di evitare. Proposta: validare che il valore sia un multiplo di 1000 oppure dichiarare l'arrotondamento e il minimo (secondi interi) nel catalogo.

### G3-07 MINORE — Variabili nuove non ancora nel catalogo (DX-22) — verificato
`config/e5-snapshot.json`: `e1.write_statement_timeout_ms`, `e1.write_connect_timeout_ms`, `e1.write_tcp_keepalives_{idle_s,interval_s,count}` hanno stato «da definire», valore di sviluppo dichiarato, `min` 1, `catalog_ref: non ancora nel catalogo`, `max` null. Conforme a DX-22 e DA-A1-10 (bloccate in produzione), ma da aggiungere al catalogo con intervallo prima della produzione. Il coda queue con `e1.write_buffer_size` senza `max` può occupare memoria senza limite fino alla definizione dell'intervallo.

### G3-08 MINORE — Formati ancora sintattici (GDPR 5(1)(c)) — verificato
`opaque_id` accetta ancora `mario_rossi` e `tel_3331234567` (dichiarato in `whitelist.py` e nel report); `model_identifier` accetta fino a 128 caratteri con `.`, `_`, `:`, `-` (per esempio `mario.rossi`); `exec_code`, `node_id`, `config_version` usano ancora `opaque_id`. `reviewer_ref` e `run_id` sono ora stretti, quindi il rischio principale è chiuso. Proposta: elenchi chiusi per modelli, provider, agenti e tool quando i cataloghi esistono.

### G3-09 MINORE — CI e script (NIS2 art. 21(2)(d)) — dedotto
`ci.yml`: `pip install --no-deps -e .` costruisce con isolamento di build (setuptools e wheel non fissati) e `apt-get install postgresql-client` non fissato, in entrambi i job. Il job `test` usa ancora `ci_writer` superuser per i test pytest: solo lo script del secondo job prova lo schema con un proprietario non superuser. `scripts/test-non-superuser.sh` lascia nel cluster il ruolo `gravya_e1_ci_nonsuper_writer` (LOGIN, password azzerata): con `trust` (come nella CI o in un cluster locale) un ruolo `LOGIN` senza password è utilizzabile da chiunque si connetta e ha `INSERT` sulle tracce. Proposta: `DROP OWNED BY` e `DROP ROLE` nel `cleanup`, build dal lockfile.

### G3-10 MINORE — `SET ROLE` costruito per interpolazione (migrations/env.py) — verificato
`migrations/env.py`: `text(f"SET ROLE {migration_role}")` con `MIGRATION_ROLE` dall'ambiente. Il valore è di deploy e non arriva da un utente, ma non è quotato come identificatore. Proposta: `psycopg.sql.Identifier` o validazione con una regex.

### G3-11 MINORE — Chiusura e perdita al riavvio (E1 §6) — verificato
`tracing.py` `close()`: il thread è `daemon`; con `flush` scaduto i job in coda non ancora scritti non sono contati né segnalati e all'uscita del processo si perdono. Il limite sui contatori in memoria è già dichiarato. Proposta: contare e segnalare i job rimasti in `close()`.

## File temporanei in /tmp (domanda del coordinator)

**Non è un rilievo di conformità, solo igiene.** I file JSON creati con `tempfile.mkstemp` (`tests/test_giro3_misc.py` righe 251-257; `scripts/_verify_nonsuperuser.py` righe 64-70) contengono solo valori di variabili sintetici (numeri e stati di variabili E1): nessun dato personale, nessun segreto, nessuna credenziale (la password del ruolo di prova è generata con `secrets` e resta in memoria). `mkstemp` crea il file con permessi 0600. Difetti: nei test `mkstemp(...)[1]` lascia aperto il descrittore; né i test né lo script cancellano il file. Proposta: `tmp_path` nei test e `TemporaryDirectory` o `unlink` nello script.

## Controllato e senza rilievi
- HMAC: chiave ≥32 byte (`hashing.MIN_KEY_BYTES = 32`, `_require_valid_key` su calcolo e verifica), calcolato dall'helper, `key_ref` `v[0-9]{1,8}` con `fullmatch`, `compare_digest`; hash del chiamante scartato.
- `raw_arguments`: `repr=False`, azzerato anche in caso di errore.
- Immutabilità: trigger e privilegi di colonna del giro 2 intatti; `0005` non concede nuovi `UPDATE`.
- Minimizzazione: `run_id` UUID canonico, `reviewer_ref` `reviewer_` + UUID canonico, UUID solo in forma canonica; log di ripiego con evento, tenant e campi chiusi nel messaggio, nessun valore.
- PV-02: nessun SDK OpenTelemetry; nessun segreto nel repository, nella CI o nello script; dati sintetici.
- DX-22: nessun valore numerico di configurazione fisso nel codice, le costanti sono invarianti dichiarati.
- Partizioni: confini letti in UTC con `SET LOCAL TimeZone = 'UTC'`, RLS forzata su ogni partizione.
- Retention, export e cancellazione dei passi 4-6 non pregiudicati.

## Letture
`tracing.py` 1-599 (intero, riletto), `0005_giro3_fixes.py` 1-163, `scripts/test-non-superuser.sh` 1-100, `scripts/_verify_nonsuperuser.py` 1-165, `migrations/env.py`, `.github/workflows/ci.yml` (diff), `config/e5-snapshot.json` (diff), diff bc32c72..HEAD di `whitelist.py`, `signals.py`, `hashing.py`, `models.py`, `config/variables.py`, `partitions.py`, `db.py`. Test: solo grep e lettura parziale di `tests/test_giro3_misc.py` e `tests/conftest.py`; `tests/test_giro4_misc.py` solo grep.
