# Report compliance-auditor, giro 2 — PR claude/impl-e1 (head bc32c72)

Diff a tre punti `origin/claude/docs-ondata-1...HEAD`, modifiche 8d56cf0..bc32c72. Sola lettura, nessun test eseguito. Norme dal registro v1.7 (GDPR 5, 25, 32 ✔; NIS2 art. 21 ✔; Reg. 2024/2690 ✔). Nessuna norma da aggiungere al registro.

**Esito: RIPORTA.** Il bloccante del giro 1 (campi liberi) è risolto. Degli 8 rilievi da riportare, 5 sono risolti, 2 sono risolti solo in parte (R-04, R-05/R-06 con rischio residuo) e 1 (R-08) è risolto con un residuo minore. Nessun nuovo bloccante. 4 nuovi rilievi da riportare, 7 minori.

## Esito per rilievo del giro 1

| Rilievo | Esito | Dove |
|---|---|---|
| R-01 bloccante, campi liberi | RISOLTO | `whitelist.py` 267-285 (`TRACE_FIELD_WHITELIST`, `SEGMENT_FIELD_WHITELIST`), `tracing.py` 536-598: `name`, `status`, `run_id`, `execution_ticket_id`, `workflow_id`, `workflow_version`, `retention_class` validati; in produzione scarto e segnale, fuori produzione errore; `run_id` non conforme = traccia non scritta. |
| R-02 identificativi opachi | PARZIALE, vedi G2-05 | Formati stretti, ma `mario_rossi` passa ancora. |
| R-03 `args_hash` | RISOLTO | `whitelist.py` 263-265 (`INTERNAL_ONLY_ATTRIBUTE_KEYS`), `tracing.py` 334-344: l'helper calcola l'HMAC da `raw_arguments`, imposta `key_ref`; un hash del chiamante è scartato; chiave assente, vuota o sotto 16 byte = non scritto con segnale (`hashing.py` 532-553). `prompt.hash` richiede `key` e `version`; criterio 16 dichiarato parziale (accettabile finché E2 non esiste). Hash: regex `^[0-9a-f]{64}$`. |
| R-04 tenant di contesto | NON RISOLTO, vedi G2-02 | Solo il controllo cross-tenant sul `trace_id`. |
| R-05 immutabilità | RISOLTO | `0004_giro2_fixes.py` 45-72: trigger `BEFORE UPDATE` che rifiuta se `OLD.ended_at IS NOT NULL` (vale anche per il proprietario), privilegi di colonna (`ended_at, status` / `ended_at, status, attributes`), `end_segment` rilegge `kind` e `ended_at` con `FOR UPDATE` (`tracing.py` 490-533), 0 righe segnalate. Residuo minore G2-09. |
| R-06 segnali, SELECT al writer | ACCETTATO con rischio nuovo, vedi G2-03 | RLS `ENABLE`+`FORCE` (0004 74-83). Il SELECT mantenuto è accettabile: il writer vede solo i segnali del proprio tenant, e il payload è limitato a campi chiusi. |
| R-07 nome della chiave e sink | RISOLTO | `whitelist.safe_signal_key_name` (nome solo se identificativo puntato ≤64 caratteri, altrimenti `key_length`); `signals.ALLOWED_SIGNAL_FIELDS` filtra i campi in entrambi i sink e nel log di ripiego. Insieme unico per tutti i segnali: accettabile (filtra i nomi dei campi, non i valori, ma i chiamanti sono solo il codice di E1). |
| R-08 fail-open | RISOLTO con residuo | `tracing.py` 276-306 (`_safe_emit`), `signals.log_fallback` (solo evento, tenant e campi chiusi); la perdita in sospeso è ri-segnalata. Residui: G2-07 e G2-11. |
| R-09 CI | RISOLTO | `ci.yml`: `permissions: contents: read`, action fissate per SHA (verificato con `git ls-remote` che l'SHA di `checkout` è quello del tag v4), immagine con digest (digest non verificato), `requirements.lock.txt` con hash, `fastapi` rimossa, nessun segreto. Residuo minore G2-10. |
| R-10 writer LOGIN | RISOLTO | `ALTER ROLE gravya_writer NOLOGIN`; l'uso in produzione è dichiarato nel report (ruolo applicativo con membership, `SET LOCAL ROLE`). Il grant al ruolo di migrazione resta dichiarato solo per i test. |
| R-11 RLS sulle partizioni | RISOLTO | `partitions.py`: `ENABLE`+`FORCE` su ogni partizione, senza policy, quindi default-deny per un accesso diretto di un ruolo non bypass. |
| R-12 partizioni e 0 righe | RISOLTO per il perimetro | Conversione in UTC, errore se i confini si sovrappongono; 0 righe segnalate. Il job di creazione anticipata resta del passo 6. |
| R-13 guardia di ambiente | PARZIALE, vedi G2-04 | Segnale `e5.environment_undeclared` aggiunto; `production_override` mantenuto. |
| R-14 attributi obbligatori e chiave | RISOLTO per il perimetro | Lunghezza minima della chiave (16 byte, invariante da confermare con A6); `end_segment` valida contro il `kind` salvato; attributi obbligatori rinviati al passo 5. |

## Giudizio sulle quattro divergenze dal task

1. **`production_override` mantenuto.** Non accettato così com'è: G2-04. Si risolve senza toccare i test del code-reviewer.
2. **SELECT del writer sulla tabella dei segnali con RLS forzata.** Accettabile per l'isolamento tra tenant, ma la RLS forzata crea un problema operativo per chi scrive i segnali (G2-03).
3. **`trace_id` mai esistito non rifiutato.** Accettabile. Un segmento che punta a un `trace_id` non ancora scritto non espone dati altrui (la lettura è per tenant) e sotto fail-open la traccia può mancare per perdita; è solo inquinamento di integrità del proprio tenant.
4. **Funzione `SECURITY DEFINER` per il controllo cross-tenant.** L'idea è corretta e `search_path` è fissato, ma come scritta può non funzionare in produzione (G2-01). Restituisce anche un booleano di esistenza di un `trace_id` altrui: rischio trascurabile con UUID.

## Rilievi nuovi

### G2-01 DA RIPORTARE — Il controllo cross-tenant può essere inefficace se il proprietario non è superuser (isolamento tra tenant, DA-E1-10) — dedotto
- `0004_giro2_fixes.py` 85-101: `gravya_e1_trace_owned_by_other_tenant` è `SECURITY DEFINER` e legge `gravya_traces`, che ha `FORCE ROW LEVEL SECURITY` (0002, righe 99-100). Con FORCE la RLS vale anche per il proprietario; solo un superuser o un ruolo `BYPASSRLS` la salta.
- Nei test e in CI il proprietario è un superuser (`root`, `ci_writer` = `POSTGRES_USER`), quindi la funzione vede tutte le righe e il test passa. In produzione, con un proprietario normale, la funzione vedrebbe solo le righe del tenant corrente e il controllo darebbe sempre «falso»: falso positivo di test.
- Proposta: affidare la funzione a un ruolo dedicato `NOLOGIN BYPASSRLS` (con `ALTER FUNCTION … OWNER TO`) e aggiungere un test in cui le migrazioni girano con un proprietario non superuser.

### G2-02 DA RIPORTARE — Il tenant di contesto non esiste ancora: R-04 non risolto (isolamento tra tenant; E1 §6) — verificato
- `tracing.py` 536-598: `tenant_id` viene sempre dal modello e va sia nella riga sia nel GUC (`db.py` 479); nessun parametro di contesto (grep: nessun `context_tenant`). Il task chiedeva un helper legato a un tenant di contesto con rifiuto dei modelli discordi e test sull'helper.
- L'implementer lo giustifica con l'assenza di un'identità applicativa prima di A6. Non regge del tutto: il contesto può essere un parametro del costruttore o della chiamata fornito dal chiamante (B1/B2 conoscono il tenant dell'esecuzione). Il controllo sul `trace_id` copre solo uno dei due casi.
- Proposta: `TracingHelper(..., tenant_context=...)` o parametro per chiamata; rifiuto con segnale se il modello ha un tenant diverso; test sull'helper.

### G2-03 DA RIPORTARE — Con la RLS forzata il sink dei segnali può non riuscire a scrivere i segnali per tenant (C2 «sempre prodotti», DX-10) — dedotto
- `0004_giro2_fixes.py` 74-83: policy `WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid)`. `PostgresSignalSink.emit` (`signals.py` 407-417) inserisce con `tenant_id` valorizzato su una connessione che non imposta `app.tenant_id`.
- Se il ruolo del sink non è superuser, l'INSERT di un segnale con tenant viene rifiutato; `_safe_emit` finisce nel log di ripiego e il segnale non arriva ad A5. In test passa perché i test girano da superuser.
- Proposta: il sink scrive nella stessa transazione del writer (con il GUC del tenant) oppure usa un ruolo dedicato di sola scrittura per i segnali con una policy `INSERT` esplicita; test con ruolo non superuser.

### G2-04 DA RIPORTARE — `production_override` può declassare la produzione (DX-22, DA-A1-10) — verificato
- `tracing.py` 270-273 e `variables.py`: se `production_override` è impostato, `API_ENV=production` viene ignorata. Passando `False` in produzione una variabile «da definire» con valore di sviluppo viene accettata e gli attributi non conformi fanno errore invece di essere scartati (nessuna perdita di contenuto, ma il blocco di avvio è disattivato).
- La motivazione (i test del code-reviewer lo usano con `True`) non impedisce una versione sicura.
- Proposta: l'override può solo irrigidire (`is_production() or override`); i test con `True` restano validi, e nei test con `False` si usa l'ambiente.

### G2-05 MINORE — I formati stretti non escludono nomi e dati con prefisso (GDPR 5(1)(c), 25) — verificato
- `whitelist.py` 56 e 74: `^[a-z]{2,16}_[A-Za-z0-9]{1,40}$` accetta `mario_rossi`, `tel_3331234567`, `cf_RSSMRA80A01H501U`. `reviewer_ref` (pseudonimo) usa ancora `opaque_id`. `loose_token` (`run_id`) accetta fino a 64 caratteri `[A-Za-z0-9_-]`, quindi anche testo codificato.
- La riduzione rispetto al giro 1 è reale (niente frasi, URL, email, punti), ma la minimizzazione resta sintattica.
- Proposta: `reviewer_ref` con prefisso fisso più esadecimale o UUID forniti da A6; `run_id` come UUID se generato da Gravya; elenchi chiusi per nomi di agenti e tool quando i cataloghi esistono.

### G2-06 MINORE — Gli argomenti in chiaro stanno nel modello (GDPR 5(1)(f), 32) — verificato
- `models.py`: `raw_arguments: bytes | None = None` è un campo normale di Pydantic: compare in `repr`, nei messaggi di errore e nei log accidentali del modello.
- Proposta: `Field(default=None, repr=False)` e azzerare il riferimento dopo il calcolo dell'HMAC.

### G2-07 MINORE — La scrittura non è asincrona e la connessione non ha timeout (E1 §5, continuità) — verificato
- `tracing.py` 378-407: la scrittura avviene nel thread del chiamante, serializzata da `_conn_lock`; il semaforo è un limite di concorrenza, non un buffer. `psycopg.connect(**params)` (riga 375) non ha `connect_timeout`, quindi un host irraggiungibile blocca il chiamante oltre `e1.write_statement_timeout_ms`. E1 §5 prevede scrittura «asincrona e bufferizzata».
- Proposta: `connect_timeout` da variabile (DX-22) e, se si mantiene la scrittura sincrona, dichiararlo nel documento (E1 v1.7) come scelta.

### G2-08 MINORE — Tipo e intervallo delle variabili non controllati per variabile (DX-17, DX-22) — verificato
- `variables.py` `_validate_scalar`: accetta booleano, stringa o intero per qualunque variabile; un `min` o `max` non numerico dà `TypeError` non tipizzato in `get`. La nuova `e1.write_statement_timeout_ms` (snapshot) è corretta come DX-22: «da definire», valore di sviluppo dichiarato, `min` 1, bloccata in produzione, ma non è ancora nel catalogo (dichiarato, lo aggiunge il coordinator) e non ha `max`.
- Proposta: tipo atteso per variabile e `VariableUnavailableError` con segnale per `min`/`max` malformati.

### G2-09 MINORE — Fail-open incompleto su `kind` non valido e whitelist solo applicativa (DA-E1-02; E1 §6) — verificato
- `tracing.py` 134-136: `validate_attributes` solleva `ValueError` per un `kind` sconosciuto, e `end_segment(kind: str)` non lo cattura: in produzione l'eccezione arriva al chiamante.
- Il writer può ancora scrivere `attributes` arbitrari con SQL diretto sulle righe aperte (nessun CHECK sulle chiavi): la whitelist resta applicativa, mitigata da privilegi di colonna e immutabilità.
- Proposta: catturare l'errore in produzione e segnalarlo; valutare un CHECK sulle chiavi ammesse per `kind`.

### G2-10 MINORE — CI: residui di supply chain e ruolo superuser (NIS2 art. 21(2)(d)) — dedotto
- `ci.yml`: `pip install --no-deps -e .` costruisce con `setuptools>=68` e `wheel` non fissati (isolamento di build), `apt-get install postgresql-client` non fissato; il database della CI gira con `ci_writer` superuser, il che maschera G2-01 e G2-03.
- Proposta: build dipendente dal lockfile o `--no-build-isolation`; ruolo di test non superuser per le migrazioni.

### G2-11 MINORE — Il contatore delle perdite non sopravvive al riavvio (E1 §4.1 classe «contatori di perdita») — verificato
- `tracing.py` 250-253: `loss_count` e `_pending_signal_loss` sono in memoria; il segnale che li riporta è l'unica traccia persistente, e se il sink non è mai disponibile prima del riavvio la perdita resta solo nel log di ripiego.
- Proposta: accettabile finché A5 non definisce la tabella; da dichiarare in E1 v1.7.

## Controllato e senza rilievi
- Contenuti: nessun testo libero nei campi di base; `name`/`status` validati; segnale senza valore (campi chiusi e `safe_signal_key_name`).
- HMAC: calcolato dall'helper, `key_ref` formato `^v[0-9]{1,8}$`, chiave ≥16 byte, hash fornito dal chiamante scartato, `compare_digest`.
- Immutabilità dopo la chiusura: trigger nel DB e controllo applicativo; privilegi di colonna senza `tenant_id`, `trace_id`, `kind`, `started_at`.
- PV-02: nessun SDK OpenTelemetry (`grep` sul diff); solo vocabolario `gen_ai.*`.
- Nessun segreto nel repository o nella CI; dati dei test sintetici; `migrations/env.py` senza URL di default.
- DX-22: nessun valore numerico di configurazione fisso nel codice dopo il giro 3 (il timeout viene dall'istantanea); le costanti rimaste sono formati e invarianti dichiarati (`MIN_KEY_BYTES`, regex, `_EPOCH_YEAR`).
- Vocabolari provvisori dichiarati in `whitelist.py` con prefisso `PROVISIONAL_` e nella sezione del report «Vocabolari provvisori da recepire in E1 v1.7»; `router` non accettato; criterio 16 parziale dichiarato.
- Retention, export e cancellazione dei passi 4-6 non pregiudicati (nessun DELETE concesso, `tenant_id` indicizzato).

## Letture
Tutti i sorgenti modificati letti per intero: `tracing.py` 1-598, `whitelist.py` 1-308, `signals.py` 1-417, `db.py` 1-99, `hashing.py` 1-78, `config/env.py` 1-23, `config/variables.py` (diff), `models.py` (diff), `partitions.py` (diff e righe 112-175), `0004_giro2_fixes.py` 1-120, `ci.yml`, `e5-snapshot.json`, `migrations/env.py`, `pyproject.toml`, `requirements.lock.txt` (solo prime righe), report implementer (giro 2 e vocabolari provvisori), `task-implementer-giro2.md`. Test: solo grep.
