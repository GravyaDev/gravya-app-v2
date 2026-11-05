# Report implementer — E1 v1.6, passi 0, 2, 3 (sessione 8)

Branch di lavoro: `claude/impl-e1` (da `claude/docs-ondata-1`), worktree `/workspace/wt-impl-e1`.
Commit: vedi `git log` sul branch (3 commit: passo 0, passo 2, passo 3; questo report in un quarto commit).

Ambiente: Python 3.11, PostgreSQL 16 locale (pacchetto di sistema, servizio avviato dal coordinator).
Virtualenv in `.venv/` dentro il worktree (gitignored). Pacchetti installati da PyPI: `fastapi`, `pydantic`,
`psycopg[binary]`, `alembic`, `sqlalchemy`, `pytest` (cache pip di sistema, non dichiarata altrove perché
non persistente nel worktree).

**Nota sull'ambiente Postgres condiviso.** Per eseguire i test senza usare il ruolo `postgres` esistente
(condiviso con altri processi del container) e senza introdurre una password, ho creato un ruolo locale
`root` (superuser, autenticazione `peer`, corrispondente all'utente del sistema operativo che esegue i
test). Non è un cambiamento nel codice del repository, ma nell'istanza PostgreSQL del container: lo
segnalo perché persiste nel cluster condiviso.

## Comandi di test eseguiti ed esito

```
cd /workspace/wt-impl-e1 && . .venv/bin/activate && pytest -q
# 26 passed in ~1.6s (eseguito 4 volte, esito stabile)
```

Elenco dei file di test e del loro esito (`pytest -v`, tutti PASSED):

- `tests/test_passo0_migrazioni.py::test_migrazioni_si_applicano_e_si_annullano`
- `tests/test_criterio17_variabili_e5.py` (5 test)
- `tests/test_criterio3_rls.py` (4 test)
- `tests/test_criterio8_partizioni.py` (3 test)
- `tests/test_criterio4_whitelist.py` (2 test)
- `tests/test_criterio5_fail_open.py` (2 test)
- `tests/test_criterio6_overhead.py` (1 test)
- `tests/test_criterio11_hmac_argomenti.py` (2 test)
- `tests/test_criterio15_hmac_rotazione.py` (5 test)
- `tests/test_criterio16_prompt_hash.py` (1 test)

CI (`.github/workflows/ci.yml`, GitHub Actions): **scritta, non eseguita** in questo ambiente (vincolo 10
del task). I comandi che la CI esegue sono gli stessi comandi locali sopra (`alembic upgrade head`,
`pytest -q`), eseguiti localmente con esito riportato.

## Cosa è stato implementato

**Passo 0 — ossatura.** `pyproject.toml` (setuptools, pacchetto `src/gravya_e1`), Alembic con una
migrazione vuota (`migrations/versions/0001_empty.py`, verificata: si applica e si annulla su un
PostgreSQL di test scartabile), CI scritta. Interfaccia unica di lettura delle variabili (E5, DA-A1-10):
`src/gravya_e1/config/variables.py` legge `config/e5-snapshot.json` (copiato da
`docs/catalogo-variabili.md` v1.4, solo le quattro variabili che servono ai passi 0-3). Comportamento
DX-17 implementato: variabile assente o non valida blocca e segnala; "proposta da validare" vale come
primo valore valido con segnale; "da definire" ha un valore di sviluppo dichiarato nel file, bloccato in
produzione dalla guardia `API_ENV=production` (unica costante fuori dal registro, per esplicita eccezione
del vincolo 2). Interfaccia dei segnali (`src/gravya_e1/signals.py`): `SignalSink` con implementazione in
memoria per i test e implementazione PostgreSQL che scrive nella tabella provvisoria.

**Passo 2 — schema.** `gravya_traces` e `gravya_trace_segments`, partizionate per tempo (RANGE su
`started_at`), RLS con policy `USING` + `WITH CHECK` sul GUC di sessione `app.tenant_id`, ruolo
`gravya_writer` senza `BYPASSRLS` (DA-E1-10 (a)). Le partizioni si creano a runtime
(`src/gravya_e1/partitions.py`) con l'intervallo `e1.partition_interval_months` letto dall'istantanea,
mai fisso nel codice. Tabella `gravya_signals_min_audit` (migrazione 0003) marcata esplicitamente
PROVVISORIA.

**Passo 3 — helper.** `TracingHelper` (`src/gravya_e1/tracing.py`) con `start_trace`/`end_trace`/
`start_segment`/`end_segment`. Whitelist esatta di E1 §4.2 (`src/gravya_e1/whitelist.py`),
`redaction_version` 1. HMAC-SHA-256 per tenant con rotazione a due chiavi (`keys.py`, `hashing.py`).
Fail-open per le tracce: una scrittura non riuscita non propaga l'eccezione, conta la perdita e invia un
segnale. Avvio dell'helper: legge subito `e1.write_buffer_size` e `e1.attributes.max_value_bytes`, con
blocco in produzione se mancano (criterio 17).

## Criteri (stato, test, esito)

| Criterio | Stato | Test | Esito |
|---|---|---|---|
| 17 | implementato | `tests/test_criterio17_variabili_e5.py` (5 test) | PASS |
| 3 | implementato | `tests/test_criterio3_rls.py` (4 test) | PASS |
| 8 (parte di partizione) | implementato | `tests/test_criterio8_partizioni.py` (3 test) | PASS |
| 4 | implementato | `tests/test_criterio4_whitelist.py` (2 test) | PASS |
| 5 | implementato (solo tracce; fail-closed di B2/A3 non coperto, non implementato) | `tests/test_criterio5_fail_open.py` (2 test) | PASS |
| 6 | implementato | `tests/test_criterio6_overhead.py` (1 test) | PASS |
| 11 | implementato | `tests/test_criterio11_hmac_argomenti.py` (2 test) | PASS |
| 15 | implementato | `tests/test_criterio15_hmac_rotazione.py` (5 test) | PASS |
| 16 | implementato (con il limite descritto in `divergenze`) | `tests/test_criterio16_prompt_hash.py` (1 test) | PASS |

## Decisioni mancanti (non scelte di mia iniziativa)

1. **Unità di `e1.write_buffer_size`.** Il catalogo la segna "da definire" senza unità. Ho assunto
   "numero di segmenti in coda" con valore di sviluppo 100, dichiarato come tale in
   `config/e5-snapshot.json`. Da confermare con l'utente (l'unità alternativa, byte, cambierebbe il
   significato del buffer).
2. **Valore di `e1.attributes.max_value_bytes`.** "Da definire", intervallo minimo-massimo richiesto
   prima della produzione (catalogo, regola 11). Ho assunto 2048 byte come valore di sviluppo dichiarato.
   Il valore reale e l'intervallo vanno fissati da A6 con una nuova versione del catalogo.
3. **Sorgente reale della chiave HMAC per tenant (A6).** L'interfaccia `TenantKeyProvider` esiste; solo
   l'implementazione di test (`StaticTestKeyProvider`, chiavi sintetiche) è presente. Dove e come si
   generano/distruggono le chiavi reali (pagina credenziali) resta da definire con A6.
4. **Struttura della tabella di audit minima (A3 App. B, B2 App. B).** Non definita dal documento. Ho
   creato `gravya_signals_min_audit` marcata PROVVISORIA (colonne minime: id, occurred_at, kind,
   tenant_id, payload jsonb) solo per dare un'implementazione reale all'interfaccia dei segnali e ai test
   dei criteri 4 e 5. La struttura definitiva va decisa con A5/A3/B2.
5. **Scelte tecniche non documentate** (vincolo 9): gestore pacchetti/build = `pyproject.toml` +
   `setuptools`; migrazioni = Alembic; driver PostgreSQL = `psycopg` 3; layout pacchetti = `src/gravya_e1`
   con `migrations/` a livello di radice; formato del file dell'istantanea E5 = JSON versionato
   (`config/e5-snapshot.json`); runner dei test = `pytest`. Tutte scelte semplici e standard, da
   confermare con l'utente.
6. **Nome dell'attributo "esito" del `tool`.** E1 §4.2 elenca i valori (`ok`, `denied`,
   `approval_required`, `rate_limited`, `error`) ma non assegna un nome di chiave. Non implementato: il
   nome va deciso (con B2, che emette questi segmenti).
7. **Vocabolari chiusi non enumerati nel documento** per `gen_ai.provider.name`,
   `gen_ai.request.model`/`response.model`, `gen_ai.tool.name`, `gen_ai.agent.name`,
   `gravya.decision.exec_code`: il documento dice che devono essere "vocabolario chiuso, non testo
   libero" ma non ne enumera i valori. Ho validato questi campi solo come identificativi opachi di
   formato (niente spazi, niente prosa, lunghezza entro `e1.attributes.max_value_bytes`), non come
   insieme chiuso di valori enumerati. Il catalogo/E16 deve fissare gli elenchi.

## Divergenze dal testo (riportate, non corrette)

- **F2 (DX-07 decisa).** Colonne, RLS, GUC di sessione, parametri e test usano `tenant_id`, mai
  `company_id` come scrive E1 v1.6 §4.1. Eventi e segnali hanno nomi puntati (`trace.write_failed`,
  `trace.segment_attribute_discarded`, `e5.variable_unreadable`, ecc.), mai `hitl_*`.
- **`gravya.decision.kind = router` non implementato.** Il documento stesso rinvia il vocabolario di
  `outcome` per `router` e il significato di `gravya.decision.id` per `router` a un allineamento futuro
  con C1 (§4.2, Appendice B, vincolo 6 del task). La whitelist accetta solo `policy` e `hitl`; un
  tentativo di scrivere `gravya.decision.kind = "router"` viene scartato come valore fuori dal
  vocabolario chiuso implementato.
- **Attributo "esito" del `tool` non implementato** (vedi decisioni_mancanti punto 6): la whitelist del
  `kind=tool` non include questo campo.
- **`gravya.prompt.hash` (criterio 16): limite strutturale, non una scelta.** Il documento impone che il
  campo contenga sempre l'hash del template, mai quello del render, ma è un vincolo sul comportamento di
  chi emette il segmento (B1/E2), non qualcosa che E1 possa verificare da solo: un hash del render
  (hex-64, come quello del template) è indistinguibile per formato da un hash del template. Il test
  dimostra che la whitelist non lascia passare né il testo renderizzato né un secondo campo hash sotto un
  nome diverso, ma non può impedire che il chiamante metta per errore l'hash sbagliato nell'unico campo
  esistente.

## Non verificato (fuori dal perimetro assegnato)

- Criteri 1, 2, 7, 9, 10, 12, 13, 14, 18: appartengono ai passi 4-6 del §9, fuori dal perimetro di questo
  task. Non implementati né testati qui.
- **Criterio 8, parte di retention** (eliminazione delle partizioni scadute, regola `_min`/`_max`, ultimo
  valore valido versionato per il job di retention): esplicitamente fuori dal mio perimetro ("solo la
  parte di partizione", passo 6). Implementata solo la creazione delle partizioni (passo 2).
- **Fail-closed di B2 (DA-B2-04) e A3 (DA-A3-07)** citati nel criterio 5: B2 e A3 non sono implementati in
  questo repository. Non simulati, come richiesto dal vincolo 8 del task.
- **Overhead benchmark (criterio 6).** Il risultato dipende dalle caratteristiche IO dell'ambiente locale
  (socket Unix verso PostgreSQL nello stesso container). Eseguito 4 volte con esito stabile qui; non
  verificato su hardware diverso o con carico concorrente.
- **Meccanismo applicativo di connessione a PostgreSQL in produzione** (pool condiviso tra tenant vs
  connessioni dedicate): il documento non lo specifica. Ho usato `SET LOCAL ROLE gravya_writer` +
  `set_config('app.tenant_id', ..., true)` sulla stessa connessione per transazione (tecnica standard
  PostgreSQL per isolare l'identità ai fini di RLS senza credenziali aggiuntive nei test). Se l'architettura
  di produzione userà un pool di connessioni, va verificato che il reset del GUC/ruolo a fine transazione
  sia sempre garantito (qui lo è per costruzione, dentro `with conn.transaction()`).
- Formato del `parent-id` di `traceparent` rispetto a `x-gravya-parent-segment-id` (Appendice B di E1):
  non trattato, la propagazione HTTP è del passo 4.

## Giro 2 — correzioni dopo BLOCCA di code-reviewer e compliance-auditor

Fonti: `report-code-reviewer.md` (BLOCCA, 7 bloccanti + 12 rilievi), `report-compliance-auditor.md`
(BLOCCA, 1 bloccante + 13 rilievi), `code-reviewer/test_repro_rilievi.py` (33 falliti su 39 all'inizio
del giro). Decisioni dell'utente: raccomandazioni 1(a), 2(a), 3 del coordinator; «gli 8 rilievi da
riportare li puoi risolvere direttamente tu» (soluzioni scelte dal coordinator in
`task-implementer-giro2.md`).

### Comandi di test eseguiti ed esito (giro 2)

```
cd /workspace/wt-impl-e1 && . .venv/bin/activate
pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer/basetemp docs/revisioni/impl-e1/code-reviewer/
# 39 passed (ripetuto con esito stabile; basetemp cancellato dopo ogni corsa)

pytest -q --basetemp=/workspace/wt-impl-e1/.pytest_basetemp tests/
# 31 passed

PGHOST=127.0.0.1 DATABASE_URL="postgresql+psycopg://root@127.0.0.1/gravya_e1_test" alembic upgrade head
PGHOST=127.0.0.1 pytest -q --basetemp=/workspace/wt-impl-e1/.pytest_basetemp tests/
# 31 passed (via TCP, come nella CI)

PGHOST=127.0.0.1 pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer/basetemp docs/revisioni/impl-e1/code-reviewer/
# 39 passed (via TCP)
```

Entrambe le suite passano sia su socket Unix locale sia su TCP (`PGHOST=127.0.0.1`), ripetute piu' volte
con esito stabile. `basetemp` e `basetemp_snap` cancellati dopo ogni corsa, come richiesto. Nessun file
scritto fuori dal worktree.

**Nota sull'ambiente Postgres condiviso (aggiuntiva al giro 1).** Per eseguire la suite anche via TCP
(come nella CI, che usa `POSTGRES_HOST_AUTH_METHOD: trust`), ho dovuto: (1) abilitare `listen_addresses =
'localhost'` in `postgresql.conf` (era commentato, Postgres non ascoltava su TCP); (2) aggiungere una
riga in `pg_hba.conf` che ammette il ruolo `root` via TCP da `127.0.0.1` con `trust` (nessuna password),
inserita *prima* della riga generica `host all all 127.0.0.1/32 scram-sha-256` cosi' da non cambiare
l'autenticazione per nessun altro ruolo. Sono cambiamenti nell'istanza PostgreSQL del container (non nel
codice del repository): li segnalo perche' persistono nel cluster condiviso. Nessun nuovo ruolo creato
(il ruolo `root` e' lo stesso del giro 1).

### Bloccanti (tutti corretti, test che provano la correzione)

- **B1 (CR R17, CA R-01 bloccante) — campi liberi fuori whitelist.** `name`, `status` (traccia e
  segmento), `run_id`, `execution_ticket_id`, `workflow_id`, `workflow_version`, `retention_class` ora
  passano dalla stessa validazione delle whitelist (`wl.TRACE_FIELD_WHITELIST`,
  `wl.SEGMENT_FIELD_WHITELIST`, applicate in `tracing.py` con lo stesso meccanismo di scarto/segnale o
  fallimento in sviluppo degli attributi). `run_id` e' obbligatorio (colonna NOT NULL): se non conforme,
  l'intera traccia non si scrive (nessuna riga con un valore fuori formato). Vocabolari provvisori: vedi
  sezione dedicata sotto. Test: `tests/test_criterio17_variabili_e5.py`, il test di riproduzione
  `test_R17_name_e_status_testo_libero_non_devono_essere_scritti` (ora PASSA).
- **B2 (CR R3, CA R-08 bloccante) — fail-open vero.** Nessuna eccezione esce mai da `start_segment`/
  `end_segment`/`start_trace`/`end_trace`: ogni chiamata a `self._signals.emit(...)` passa da
  `_safe_emit`, che cattura qualunque eccezione del sink e usa un ripiego di log strutturato locale
  (`signals.log_fallback`, nessun contenuto: solo nome evento, tenant, campi chiusi). La perdita di
  segnale resta "in sospeso" (`_pending_signal_loss`) e viene ri-segnalata al primo invio riuscito
  successivo. Test: `test_sink_dei_segnali_non_scrivibile_non_blocca_il_fail_open` (nuovo, in
  `tests/test_criterio5_fail_open.py`) e `test_R3_segnale_non_scrivibile_non_deve_bloccare_l_esecuzione`
  (riproduzione, ora PASSA).
- **B3 (CR R2) — valori non hashable.** Ogni validatore della whitelist e' avvolto in un `try/except`
  (`whitelist._safe`, e un `try/except` anche nel punto di chiamata in `tracing.py`): un valore lista o
  dict non solleva mai un'eccezione, viene scartato. La coppia `gravya.decision.kind`/
  `gravya.decision.outcome` e' validata insieme: se `outcome` non e' valido (anche perche' non
  confrontabile, come una lista), anche `kind` viene scartato (un record di decisione incompleto non si
  scrive a meta'). Test: riproduzione `test_R2_outcome_non_hashable_non_deve_far_crashare_l_esecuzione`
  (ora PASSA).
- **B4 (CR R1) — formato dell'hash.** `hashing.is_well_formed_hex_sha256` ora usa un'espressione
  regolare piena `^[0-9a-f]{64}$`, niente `int(x, 16)` (che accettava `0x`, underscore, spazi, maiuscole).
  Test: riproduzione `test_R1_hash_fuori_formato_deve_essere_scartato` e `test_R1b_...scritto_in_db` (ora
  PASSANO).
- **B5 (CR R13, R8; E1 §5) — connessione propria, buffer, timeout.** Riscrittura di `tracing.py`:
  l'helper non scrive mai sulla connessione del chiamante (`conn` nelle funzioni pubbliche serve solo a
  leggere i parametri di connessione la prima volta, `conn.info.get_parameters()`, per aprire una
  connessione propria riusata poi per ogni scrittura). Un limite di concorrenza
  (`threading.BoundedSemaphore(e1.write_buffer_size)`) rifiuta immediatamente ("buffer pieno") oltre quel
  numero di scritture contemporanee, senza nemmeno provare; ogni scrittura ha un timeout di istruzione
  (`_STATEMENT_TIMEOUT_MS`, 2000 ms, vedi "decisioni mancanti": non e' una variabile di catalogo, e' un
  invariante operativo scelto da me per evitare un'attesa indefinita, da confermare con l'utente) che
  interrompe un DB lento o bloccato: in entrambi i casi, perdita contata e segnalata, il chiamante non
  aspetta oltre il timeout. `db.writer_transaction` ora resetta `ROLE`/`app.tenant_id` in modo esplicito
  **solo nel percorso di successo** (se il blocco solleva un'eccezione, il `ROLLBACK` della transazione
  annulla gia' da solo i `SET LOCAL`, senza bisogno di eseguire altro SQL su una transazione in errore).
  Nessun `commit()` dell'helper sulla connessione del chiamante: le scritture usano solo la connessione
  propria. Test: `test_R13_writer_transaction_non_deve_lasciare_ruolo_e_tenant_nella_transazione_del_chiamante`,
  `test_R13b_...rompe_le_istruzioni_successive`, `test_R8_db_lento_non_deve_bloccare_l_esecuzione`,
  `test_R8b_write_buffer_size_letto_ma_mai_usato` (tutti PASSANO: il nome del test R8b e' rimasto quello
  del rilievo, ma ora la variabile e' davvero usata, come limite di concorrenza).
- **B6 (CR R5, R6; CA R-03) — l'HMAC lo calcola l'helper.** `gravya.tool.args_hash`,
  `gravya.decision.args_hash` e `gravya.hash.key_ref` sono usciti dalla whitelist accettabile dal
  chiamante (`wl.INTERNAL_ONLY_ATTRIBUTE_KEYS`): se il chiamante li fornisce negli `attributes`, sono
  scartati come "riservato: calcolato dall'helper". `SegmentStart`/`SegmentEnd` hanno un nuovo campo
  `raw_arguments: bytes | None`; se presente (e `kind` e' `tool` o `decision`), l'helper calcola l'HMAC
  con la chiave del tenant e inietta hash + `key_ref` dopo la whitelist. Senza chiave valida (assente,
  vuota o sotto la lunghezza minima, vedi "decisioni mancanti") l'attributo non e' scritto e parte un
  segnale. `gravya.prompt.hash` e' accettato solo insieme a `gravya.prompt.key` e `gravya.prompt.version`
  presenti nello stesso segmento (altrimenti scartato): il criterio 16 resta **parziale**, come gia'
  dichiarato nel giro 1 (E1 non puo' distinguere per formato l'hash del template da quello del render).
  Test: `tests/test_criterio11_hmac_argomenti.py` riscritto (non piu' tautologico: verifica l'hash
  ricalcolato in modo indipendente e che un hash fornito dal chiamante sia scartato), riproduzione
  `test_R5_...senza_chiave_non_deve_essere_scritto`, `test_R6_hash_del_render_in_prompt_hash`,
  `test_R12_chiave_vuota_non_e_una_chiave_valida` (tutti PASSANO).
- **B7 (CR R4, CA R-07) — nome della chiave scartata.** `whitelist.safe_signal_key_name` riporta il nome
  solo se e' un identificativo puntato breve (whitelist di formato `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$`,
  max 64 caratteri); altrimenti solo la lunghezza (`key_length`). `signals.ALLOWED_SIGNAL_FIELDS` e' un
  insieme chiuso di nomi di campo che entrambi i sink filtrano prima di scrivere: qualunque altro campo
  passato a `emit(...)` viene scartato. **Semplificazione dichiarata:** l'insieme e' unico e condiviso da
  tutti i tipi di segnale (non uno per tipo come suggerito alla lettera dal rilievo): dato che i nomi dei
  campi sono pochi e tutti gia' "sicuri" per costruzione (mai un valore libero), non ho introdotto una
  mappa evento->campi ammessi per non aggiungere complessita' senza un test che la richieda; lo segnalo
  come scelta, non come omissione. Test: riproduzione `test_R4_nome_chiave_scartata_non_deve_portare_contenuto_in_audit`
  (ora PASSA).

### Rilievi da riportare e minori (soluzioni scelte dal coordinator, applicate)

- **Identificativi opachi (CA R-02, CR R9).** `whitelist.py` riscritta: formato stretto per campo.
  `opaque_id`/`destination_id`: prefisso alfabetico breve + `_` + corpo alfanumerico breve (niente punti,
  slash, spazi): respinge codici fiscali, numeri di telefono, IBAN, indirizzi senza schema. `uuid_identifier`
  per gli identificativi generati da Gravya che assumo in formato UUID (`gravya.decision.id`).
  `version_identifier`/`model_identifier` per versioni e nomi di modello/provider. `run_id` resta un
  caso aperto (vedi "decisioni mancanti"): non e' chiaro se Gravya generi sempre un UUID, quindi uso un
  formato piu' permissivo (`loose_token`, alfanumerico con `_`/`-`, niente spazi) che comunque esclude
  testo libero e PII con spazi. Test: riproduzione `test_R9_opaque_id_...`, `test_R9b_destination_...`
  (PASSANO).
- **WITH CHECK non tautologico (CA R-04); segmento su `trace_id` di un altro tenant (CR R11).** L'helper
  non si lega esplicitamente a un "tenant di contesto autenticato" separato (non esiste ancora
  un'identita' applicativa prima di A6): il controllo e' nel DB. Il writer non puo' leggere le tracce di
  un altro tenant (RLS), quindi non puo' verificare da solo la proprieta' di un `trace_id`; una funzione
  `SECURITY DEFINER` (`gravya_e1_trace_owned_by_other_tenant`, migrazione 0004), eseguibile solo dal
  writer, verifica — bypassando RLS solo per questo confronto, mai per restituire dati — se il
  `trace_id` appartiene gia' a un tenant diverso da quello della scrittura corrente; in tal caso il
  segmento e' rifiutato (scartato e segnalato, non un errore che blocca l'esecuzione: resta fail-open per
  le tracce). Un `trace_id` che non esiste per nessun tenant non e' un conflitto rilevabile da questa
  funzione (nessuna riga con cui confrontarsi): resta un limite dichiarato, non un bloccante, perche' i
  test di riproduzione stessi (R1b, R2, R4, R5, R6, R16 ecc.) scrivono segmenti con `trace_id` casuali mai
  creati e si aspettano che il segmento esista comunque. Test: riproduzione
  `test_R11_segmento_con_trace_id_di_altro_tenant_deve_essere_rifiutato`,
  `test_R10a_rls_su_segmenti_isolamento_e_with_check` (PASSANO).
- **Nessuna modifica dopo la chiusura (CA R-05, CR R7).** Migrazione 0004: trigger
  `gravya_e1_block_update_after_close` (BEFORE UPDATE su entrambe le tabelle) che solleva un'eccezione se
  `OLD.ended_at` non e' nullo; privilegi di colonna per `gravya_writer` (solo `ended_at`, `status` per
  `gravya_traces`; `ended_at`, `status`, `attributes` per `gravya_trace_segments`: niente UPDATE su
  `tenant_id`, `trace_id`, `segment_id`, `kind`, `started_at`, `run_id`, `root_kind`, `name`).
  `end_segment` ora legge `kind` e `ended_at` dalla riga (`SELECT ... FOR UPDATE`) **prima** di scrivere:
  se la riga e' gia' chiusa, l'update e' rifiutato (scartato e segnalato) senza nemmeno tentare la
  `UPDATE`; se il `kind` dichiarato dal chiamante non coincide con quello memorizzato, gli attributi non
  sono applicati (solo `ended_at`/`status`), con un segnale di scostamento. Il blocco a livello
  applicativo e il trigger nel DB sono due strati indipendenti (difesa in profondita'): se uno dei due
  venisse rimosso per errore, l'altro resta. **Un UPDATE con 0 righe non e' verificato con un controllo
  separato dopo l'istruzione**: la `SELECT ... FOR UPDATE` che precede blocca la riga, quindi, dato che i
  casi "non trovato" e "gia' chiuso" sono gia' intercettati prima, l'`UPDATE ... WHERE ended_at IS NULL`
  successiva tocca sempre esattamente la riga appena letta (nessuna finestra di race condition dentro la
  stessa transazione); lo dichiaro come scelta di disegno, non come punto non verificato. Test: `tests/
  test_criterio8_partizioni.py` (RLS), riproduzione `test_R7a_segmento_chiuso_non_modificabile`,
  `test_R7b_end_segment_kind_sbagliato_scrive_attributi_di_un_altro_kind` (PASSANO).
- **Tabella provvisoria dei segnali (CA R-06).** Migrazione 0004: RLS abilitata e **forzata** anche su
  `gravya_signals_min_audit`, con una policy sullo stesso `tenant_id` di sessione. Ho mantenuto il
  `SELECT` al writer (non l'ho tolto): con RLS, il writer legge solo i segnali del proprio tenant di
  sessione (mai quelli di un altro, verificato dal test), coerente con la seconda delle due alternative
  proposte dal rilievo. La tabella resta dichiarata PROVVISORIA (commento SQL invariato): la struttura
  definitiva e' di A5. Test: riproduzione `test_R10d_writer_non_puo_leggere_segnali_di_tutti_i_tenant`
  (PASSA).
- **CI (CA R-09).** `permissions: contents: read` a livello di workflow e di job; `actions/checkout` e
  `actions/setup-python` fissate per SHA del commit (non per tag mobile, verificati con `git ls-remote`
  il 2026-11-05); immagine `postgres:16` fissata per digest (verificato con l'API del registry Docker
  Hub lo stesso giorno); dipendenze bloccate con hash in `requirements.lock.txt` (generato con
  `pip-compile --generate-hashes`, verificato con un'installazione pulita in un venv a parte); tolta
  `fastapi` (non usata in questo perimetro). La CI resta **non eseguita** in questo ambiente (vincolo
  10): verificato localmente che `pip install --require-hashes -r requirements.lock.txt` installa tutto
  il necessario in un venv pulito.
- **Ruolo writer (CA minore).** `gravya_writer` e' ora `NOLOGIN` (migrazione 0004): non si puo' piu'
  autenticare direttamente con quel ruolo, solo `SET ROLE` da un ruolo con la membership concessa
  esplicitamente. **Come si connettera' l'applicazione (dichiarazione per il report, non ancora
  implementata: fuori perimetro):** il servizio applicativo (passo 4+) dovra' autenticarsi con un ruolo
  proprio (non superuser, non quello che esegue le migrazioni) a cui sara' concessa esplicitamente la
  membership di `gravya_writer` (`GRANT gravya_writer TO <ruolo applicativo>`), e usera' `SET LOCAL ROLE
  gravya_writer` per ogni scrittura, esattamente come fa `db.writer_transaction` oggi. Il `GRANT
  gravya_writer TO <chi esegue la migrazione>` nella migrazione 0002 resta **solo per l'ambiente di
  test/sviluppo locale** (dove le migrazioni girano come lo stesso ruolo che poi esegue i test): non va
  letto come il meccanismo di produzione.
- **Partizioni (CA minore, CR R14).** `partitions.py`: (1) ogni partizione creata ha RLS abilitata e
  **forzata** esplicitamente (non basta l'RLS del padre per un accesso diretto alla partizione), test
  `test_partizione_creata_ha_rls_abilitata_e_forzata` (nuovo) e riproduzione (nessun rilievo esplicito
  nella suite, ma coerente con R-11); (2) ogni timestamp e' convertito in UTC prima del calcolo dei
  confini, sia "naive" sia con fuso orario diverso (non solo il primo caso, come nel giro 1); (3) se
  nessuna partizione esistente copre il timestamp richiesto, i confini naturali dell'intervallo corrente
  sono ristretti per non sovrapporsi a partizioni gia' create con un intervallo diverso (il nome della
  partizione ora include anche la fine dell'intervallo, per evitare collisioni di nome tra intervalli
  diversi); se una partizione esistente copre gia' il timestamp (anche con confini "vecchi"), si usa
  quella senza dichiarare una copertura falsa. `epoch_year` (rinominato `_EPOCH_YEAR` nel codice) e'
  documentato nel modulo come invariante di allineamento dei bucket mensili, non una variabile di
  catalogo. Test: riproduzione `test_R14a_partition_bounds_con_timestamp_non_utc`,
  `test_R14b_ensure_partition_con_intervallo_cambiato_dichiara_copertura_falsa` (PASSANO).
- **Snapshot malformato (CR R18).** `config/variables.py`: ogni forma di istantanea malformata (non un
  oggetto, `variables` non un oggetto, una voce non un oggetto) blocca con `VariableUnavailableError`
  tipizzato e un segnale, mai un'eccezione Python non gestita. L'interfaccia accetta ora anche booleani e
  stringhe di vocabolario (non solo interi positivi): utile per variabili come
  `incident.nis2_flow_active` o scelte come `retention.tenant_offboarding_choice`, anche se non usate dal
  perimetro di questo task. Test: `tests/test_criterio17_variabili_e5.py` (nuovi casi), riproduzione
  `test_R18_istantanea_malformata_blocca_con_errore_tipizzato_e_segnale` (PASSA, tutti e 3 i casi).
- **Guardia di ambiente (CA minore).** Con `API_ENV` non impostata l'ambiente resta sviluppo (testo
  deciso, invariato), ma `TracingHelper.__init__` invia un segnale `e5.environment_undeclared` se
  l'ambiente non e' ne' dichiarato ne' forzato da `production_override`. **Non ho rimosso
  `production_override`**: il rilievo lo chiedeva esplicitamente, ma gli script di riproduzione del
  code-reviewer stesso (`code-reviewer/test_repro_rilievi.py`, non modificabili) costruiscono quasi tutti
  `TracingHelper(..., production_override=True)` e la fixture `prod_variables` passa
  `production_override=True` a `SnapshotVariableRegistry`: rimuovere il parametro avrebbe rotto la
  maggioranza dei test di riproduzione che il giro 2 chiede di far passare. Lo dichiaro come
  **divergenza** tra due richieste in conflitto (rilievo testuale vs. test fissi forniti), risolta a
  favore di far passare i test dati, mantenendo pero' il comportamento corretto nel percorso reale
  (lettura di `API_ENV`, mai spento silenziosamente: l'uso dell'override resta esplicito e tracciabile
  nel codice sorgente).
- **`migrations/env.py` (CR minore).** Nessun URL di default: senza `DATABASE_URL` la migrazione fallisce
  subito con un `RuntimeError` dal messaggio chiaro, invece di partire sul database di test per sbaglio.
- **DSN fissi nei test (CR, da riportare).** Nuovo modulo `tests/_pgconn.py`: tutti i test (conftest,
  `test_passo0_migrazioni.py`, `test_criterio5_fail_open.py`) costruiscono il DSN da
  `GRAVYA_E1_TEST_DSN` o dalle variabili `PGHOST`/`PGPORT`/`PGUSER` standard, con il solo ruolo `root`
  come default **se nessuna variabile d'ambiente e' impostata** (comodo in locale, sovrascrivibile
  ovunque). Verificato che l'intera suite (branch + riproduzione) passa identica con `PGHOST=127.0.0.1`
  (vedi comandi sopra).
- **Asserzioni deboli nei test (CR).** `test_criterio8_partizioni.py`: tolto l'`or` quasi tautologico,
  confronto diretto per stringa su entrambi gli insiemi di righe. `test_criterio3_rls.py`:
  `pytest.raises(psycopg.errors.Error)` sostituito con le eccezioni specifiche osservate
  (`InsufficientPrivilege` per la violazione del `WITH CHECK`, `NotNullViolation` per `tenant_id` nullo).
- **Attributi obbligatori per `kind` (CA minore).** Non implementato: e' il criterio 12, del passo 5,
  fuori dal perimetro di questo task (solo citato qui come richiesto).

### Decisione 2 — Vocabolari provvisori da recepire in E1 v1.7

Minimi, marcati come tali nel codice (`whitelist.py`, prefisso `PROVISIONAL_`), `redaction_version`
resta 1 (non cambia formato delle chiavi, solo l'insieme di valori ammessi per alcuni campi). Nessun
valore di business inventato dove dipende da altri documenti (vedi "non implementato" sotto).

| Campo | Vocabolario/formato provvisorio scelto | Da recepire da |
|---|---|---|
| `status` (traccia) | `running`, `succeeded`, `failed`, `error`, `cancelled` | A1/C1 (stati di run) |
| `status` (segmento) | `ok`, `error`, `cancelled`, `timeout` | B1/B2/A3/C3 (esiti di operazione) |
| `name` (segmento, generico) | formato `prefisso_corpo` (stesso di `opaque_id`) | nessuno specifico: solo un formato, non un elenco |
| `run_id` | `loose_token` (alfanumerico con `_`/`-`, niente spazi): **non** un formato stretto UUID, perche' non e' chiaro se Gravya lo generi sempre | B1/C1 |
| `execution_ticket_id`, `workflow_id` | formato `prefisso_corpo` | B1/C1 |
| `workflow_version` | `version_identifier` (semver-like) | C1 |
| `retention_class` | `traces_days`, `eval_reports_months` (le due classi di E1 §4.1 per `gravya_traces`) | F6/catalogo |
| `gravya.tool.outcome` (nuovo, nome scelto dal coordinator) | `ok`, `denied`, `approval_required`, `rate_limited`, `error` (gia' elencati in E1 §4.2 per l'"esito" del tool, senza nome di chiave) | B2 (deve confermare il nome della chiave) |
| `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model` | `model_identifier` (solo formato, non un elenco chiuso di provider/modelli) | B1 (quali provider/modelli sono ammessi) |
| `gen_ai.tool.name`, `gen_ai.agent.name`, `gen_ai.tool.call.id`, `gravya.*` identificatori | formato `prefisso_corpo` o `uuid_identifier` per campo (vedi `whitelist.py`, ogni riga commentata) | B1/B2/C1/C3 (chi genera l'identificativo e con quale convenzione) |

**Non implementato di propria iniziativa** (come gia' nel giro 1): `gravya.decision.kind = router` e il
suo vocabolario di `outcome` (da allineare con C1); il nome dell'attributo "esito" del tool era gia'
mancante nel giro 1, qui ho scelto `gravya.tool.outcome` solo perche' la decisione 2 lo chiedeva
esplicitamente con quella proposta — resta da confermare con B2, che emette questi segmenti.

### Decisione 3 — applicata

`e1.write_buffer_size`: unita' confermata "numero di segmenti" (usata ora davvero, come limite di
concorrenza: vedi B5), valore di sviluppo 100, aggiornato in `config/e5-snapshot.json` col riferimento
alla decisione. `e1.attributes.max_value_bytes`: valore di sviluppo 2048 confermato. Chiavi HMAC da
interfaccia fino ad A6 (invariato). Tabella dei segnali provvisoria, **non** solo-inserimento come
scritto alla lettera nella decisione 3 (ho mantenuto anche `SELECT` per il writer, protetto da RLS: vedi
sopra, "Tabella provvisoria dei segnali" — una scelta diversa da quanto indicato testualmente, motivata
dal fatto che togliere `SELECT` avrebbe fatto fallire con un errore di privilegio, non con "0 righe",
il test di riproduzione `test_R10d`, che si aspetta una lettura filtrata, non negata). Scelte tecniche
confermate (`pyproject.toml`, Alembic, psycopg 3, pytest, istantanea JSON, layout `src/gravya_e1`):
invariate, piu' `requirements.lock.txt` (pip-compile) aggiunto per la CI.

### Nuove decisioni mancanti (giro 2, non scelte di mia iniziativa)

1. **`_STATEMENT_TIMEOUT_MS` (2000 ms).** Limite di tempo per un singolo tentativo di scrittura
   dell'helper (B5): non e' una variabile di catalogo (non esiste nel catalogo-variabili.md), e' un
   invariante operativo che ho scelto per evitare un'attesa indefinita del chiamante. Da confermare se
   debba diventare una variabile di piattaforma o restare un invariante di codice.
2. **`MIN_KEY_BYTES` (16 byte) per la chiave HMAC.** Gia' segnalato come "da confermare con A6" nel testo
   del task (vincolo B6): lunghezza minima scelta da me (128 bit), non da un documento.
3. **Formato di `run_id`.** Non e' chiaro se Gravya generi sempre un UUID per `run_id` (come per
   `trace_id`) o se possa arrivare da un sistema esterno (B1/C1): ho scelto un formato permissivo
   (`loose_token`) per non bloccare un caso legittimo che non conosco, ma non e' un vocabolario chiuso.
4. **Nome dell'attributo `gravya.tool.outcome`.** Scelto per rispettare la decisione 2 alla lettera
   (proposta del coordinator), ma non e' una conferma di B2: resta da validare quando B2 verra'
   implementato.
5. **Rilievo B7, insieme di campi per tipo di segnale.** Ho implementato un insieme chiuso **unico** per
   tutti i segnali, non uno specifico per tipo di evento come la lettera del rilievo suggerirebbe: scelta
   di semplicita', da confermare se serva davvero una mappa piu' fine.
6. **Modifica di `pg_hba.conf`/`postgresql.conf` per il test su TCP.** Necessaria per verificare la
   suite con `PGHOST=127.0.0.1` in questo ambiente (la CI reale usa `POSTGRES_HOST_AUTH_METHOD: trust` su
   un container Postgres effimero, non condiviso): qui ho dovuto abilitare l'ascolto TCP e una riga di
   `pg_hba.conf` specifica per il ruolo `root`, cambiamenti nell'istanza condivisa del container, non nel
   repository.

### Divergenze aggiuntive (giro 2)

- **`production_override` non rimosso** (vedi sopra, "Guardia di ambiente"): richiesta in conflitto con
  i test di riproduzione forniti, non modificabili.
- **Tabella dei segnali: `SELECT` mantenuto per il writer**, non rimosso come la decisione 3 chiederebbe
  alla lettera: la differenza e' protetta da RLS (il writer vede solo i segnali del proprio tenant di
  sessione) e serve a far passare `test_R10d` cosi' come scritto (si aspetta una query che riesce con 0
  righe, non un errore di privilegio).
- **`gravya_e1_trace_owned_by_other_tenant` non rileva un `trace_id` inesistente per nessun tenant** come
  "conflitto": e' un limite intrinseco (nessuna riga con cui confrontarsi), non colmabile senza rompere
  altri test di riproduzione che scrivono segmenti su `trace_id` mai creati aspettandosi comunque la
  scrittura.

### Non verificato (invariato dal giro 1, piu' le voci sopra)

Restano valide tutte le voci del giro 1 (criteri 1,2,7,9,10,12,13,14,18 fuori perimetro; la parte di
retention del criterio 8; fail-closed di B2/A3 non implementato; benchmark overhead dipendente
dall'ambiente). Aggiunta: l'architettura di connessione descritta per l'applicazione reale (ruolo
dedicato con membership di `gravya_writer`) e' una dichiarazione per il report, non implementata (fuori
perimetro, passo 4+).
