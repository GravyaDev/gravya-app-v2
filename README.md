# Gravya E1 — Tracing distribuito (ossatura)

Passi 0, 2 e 3 di E1 v1.6 (vedi `docs/`): schema PostgreSQL con RLS forzata
per `gravya_traces`/`gravya_trace_segments`, whitelist di attributi,
`TracingHelper` (scrittura asincrona, coda e connessione propria), registro
delle variabili E5 (istantanea versionata in `config/e5-snapshot.json`).

## Esecuzione locale

### Prerequisiti

- Python 3.11+
- PostgreSQL 16 in esecuzione (locale o raggiungibile via TCP)
- Un ruolo PostgreSQL con `CREATEDB` (per creare il database di test) e la
  possibilità di autenticarsi (peer, password o `trust`, a scelta
  dell'ambiente): **non deve essere superuser** per il flusso applicativo
  ordinario, ma la fixture `admin_conn` dei test (sotto) e il bootstrap
  una tantum dei ruoli `gravya_migrator`/`gravya_e1_so_owner` richiedono
  privilegi di superuser (vedi "Nota sul ruolo `root`" più sotto).

### Virtualenv e dipendenze

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements.lock.txt
pip install --no-build-isolation --no-deps -e .
```

### Variabili di connessione a PostgreSQL

I test e gli script non usano mai un socket Unix fisso o un nome di ruolo
scritto a lettere nel codice applicativo: leggono `GRAVYA_E1_TEST_DSN` (una
stringa di connessione libpq, senza `dbname`) oppure le variabili standard
`PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`. Esempio con un ruolo qualunque via
TCP:

```bash
export PGHOST=127.0.0.1
export PGPORT=5432
export PGUSER=<il_tuo_ruolo>
export GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5432 user=<il_tuo_ruolo>"
```

Se non si imposta nulla, i test di `tests/` usano `user=root` come
ripiego (vedi "Nota sul ruolo `root`" più sotto): non è un segreto, è solo
il nome del ruolo di sviluppo locale di questo progetto.

### Database di test e migrazioni

```bash
createdb -O "$PGUSER" gravya_e1_test   # o: psql -c "CREATE DATABASE gravya_e1_test OWNER <ruolo>;"
DATABASE_URL="postgresql+psycopg://${PGUSER}@${PGHOST:-}/gravya_e1_test" alembic upgrade head
```

`DATABASE_URL` è obbligatoria per `alembic upgrade head` (nessun database di
default, DX-22): senza, la migrazione si rifiuta di partire con un
messaggio esplicito.

### Eseguire i test

```bash
export GRAVYA_E1_TEST_DSN="host=${PGHOST:-} user=${PGUSER}"   # stessa dbname del passo precedente, aggiunta dai test
pytest -q
```

I test creano e distruggono le proprie partizioni/righe dentro
`gravya_e1_test` (fixture `ensure_partitions_now`, `make_helper`, ecc.): non
serve nessuna preparazione oltre alle migrazioni. Nessun file temporaneo
resta fuori da `tmp_path` (gestito da pytest).

### Script di verifica con un ruolo non superuser (criterio di fine 2)

`scripts/test-non-superuser.sh` dimostra che le migrazioni e l'applicazione
funzionano quando lo schema è di proprietà di un ruolo non superuser
(`gravya_migrator`), non di chi avvia la migrazione:

```bash
PGUSER=<un_ruolo_superuser> PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh
```

Usa un database "usa e getta" (`SCRATCH_DB`, default
`gravya_e1_ci_nonsuper`), eliminato alla fine anche in caso di errore. **Il
`PGUSER` di questo script deve essere un superuser**: il bootstrap una
tantum dei ruoli `gravya_migrator` (`CREATEROLE`) e soprattutto
`gravya_e1_so_owner` (`BYPASSRLS`, non ottenibile con `CREATEROLE`) richiede
privilegi che solo un superuser può concedere (vincolo di PostgreSQL, non
di questo progetto). Lo script poi *verifica* che un ruolo davvero non
superuser possa scrivere, leggere il trigger anti-modifica e la funzione
cross-tenant, e che non possa più assumere `gravya_e1_so_owner` dopo la
revoca: tutte le connessioni di verifica (non quelle di bootstrap) usano
ruoli non superuser creati al volo, con password generata a runtime (mai
salvata, mai nel codice).

### Prove dei revisori (`docs/revisioni/impl-e1/code-reviewer*/`)

Le suite di riproduzione dei revisori (`code-reviewer/`, `code-reviewer-giro2/`,
`code-reviewer-giro3/`) sono file di prova non modificabili. Ognuna crea e
cancella il proprio database (`gravya_e1_review`, `_review2`, `_review3`) con
una fixture di sessione autouse. Esecuzione tipica:

```bash
export PGDATABASE=gravya_e1_review        # _review2 / _review3 per le altre due
export GRAVYA_E1_TEST_DSN="dbname=gravya_e1_review user=<ruolo>"
export PYTHONPATH=docs/revisioni/impl-e1/code-reviewer
pytest -q docs/revisioni/impl-e1/code-reviewer/test_repro_rilievi.py
```

(`PYTHONPATH` punta alla cartella della suite che si vuole eseguire;
`PGDATABASE`/`GRAVYA_E1_TEST_DSN` al suo database, coerenti con il nome che
la fixture della suite usa internamente.)

## Nota sul ruolo `root` (dipendenza dichiarata, non eliminabile ovunque)

- `tests/` (la suite applicativa, non quella dei revisori): **non dipende**
  da un ruolo chiamato `root`. Il nome compare solo come valore di default
  di `PGUSER` quando non si imposta nessuna variabile d'ambiente
  (`tests/_pgconn.py`): con `PGUSER`/`GRAVYA_E1_TEST_DSN` impostati a un
  ruolo qualsiasi (con i privilegi giusti) la stessa suite gira identica.
- `docs/revisioni/impl-e1/code-reviewer/conftest.py`,
  `code-reviewer-giro2/conftest.py` e `code-reviewer-giro3/conftest.py`
  (le tre suite di riproduzione dei revisori, **non modificabili**)
  **scrivono `postgresql+psycopg://root@/...` e l'autenticazione peer
  implicita dell'utente del sistema operativo, letteralmente nel codice**:
  per eseguirle serve un ruolo PostgreSQL chiamato esattamente `root`,
  superuser, raggiungibile con autenticazione peer dall'utente del sistema
  operativo che lancia `pytest` (o da un utente di sistema chiamato `root`).
  Non c'è una variabile d'ambiente per cambiarlo in questi tre file: è un
  limite dei file stessi, dichiarato qui e nel report dell'implementer
  (`docs/revisioni/impl-e1/report-implementer.md`, sezione "Giro 4"), non
  qualcosa che questo README possa aggirare senza modificare file di prova
  dei revisori.
- `scripts/test-non-superuser.sh` e `scripts/_verify_nonsuperuser.py` /
  `scripts/_verify_signals_nonsuperuser.py` **non dipendono** da un ruolo
  chiamato `root`: `PGUSER` può essere qualunque ruolo superuser (vedi
  sopra), passato per variabile d'ambiente.
