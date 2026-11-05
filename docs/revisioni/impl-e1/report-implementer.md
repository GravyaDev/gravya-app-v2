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
