# Gravya E1 — Tracing distribuito (ossatura)

Passi 0, 2 e 3 di E1 v1.6 (vedi `docs/`): schema PostgreSQL con RLS forzata
per `gravya_traces`/`gravya_trace_segments`, whitelist di attributi,
`TracingHelper` (scrittura asincrona, coda e connessione propria), registro
delle variabili E5 (istantanea versionata in `config/e5-snapshot.json`).

## Esecuzione locale

### Prerequisiti

- Python 3.15
- PostgreSQL 18 in esecuzione (locale o raggiungibile via TCP)
- **Un ruolo PostgreSQL superuser per il primissimo `alembic upgrade head`**
  (giro 5, correzione del README): la migrazione `0002` crea il ruolo
  `gravya_writer` e la migrazione `0005` crea `gravya_e1_so_owner` con
  `BYPASSRLS` — creare un ruolo con `BYPASSRLS` **richiede un superuser**,
  vincolo di PostgreSQL che nessun privilegio come `CREATEROLE` aggira (vedi
  "Nota sul ruolo di sviluppo" più sotto per la verifica diretta di questo
  limite). Una volta che i ruoli esistono nel cluster, le migrazioni
  *possono* girare con un proprietario non superuser (`gravya_migrator`):
  vedi "Script di verifica con un ruolo non superuser" sotto, che lo
  dimostra su un database usa e getta.

### Virtualenv e dipendenze

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements.lock.txt
pip install --no-build-isolation --no-deps -e .
```

### Variabili di connessione a PostgreSQL

I test e gli script non usano mai un socket Unix fisso o un nome di ruolo
scritto a lettere nel codice applicativo (giro 5, CR R1: verificato che
nessun file di `tests/*.py`, salvo `_pgconn.py`, contiene `user=root`):
leggono `GRAVYA_E1_TEST_DSN` (una stringa di connessione libpq, senza
`dbname`) oppure le variabili standard `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`.
Esempio con un ruolo qualunque via TCP:

```bash
export PGHOST=127.0.0.1
export PGPORT=5432
export PGUSER=<il_tuo_ruolo>
export PGPASSWORD=<se_serve>
export GRAVYA_E1_TEST_DSN="host=${PGHOST} port=${PGPORT} user=${PGUSER}"
export API_ENV=development
```

Se non si imposta nulla, `tests/` usa `root` come ripiego locale di questo
progetto (`tests/_pgconn.py`, l'unico file dove il nome compare: non è un
segreto). Con le variabili sopra impostate a un ruolo qualsiasi (con i
privilegi del caso), la stessa suite gira identica: provato in questo giro
creando un ruolo apposta (vedi "Nota sul ruolo di sviluppo").

**`API_ENV` va impostata esplicitamente (giro 6, decisione dell'utente)**: a
un valore dell'insieme chiuso (`production`, `development`, `test`). Non
impostarla affatto **blocca l'avvio** dell'helper con un segnale (prima:
trattata come sviluppo, con un segnale solo informativo); lo stesso vale per
un valore fuori da quell'insieme (per esempio `Production`, maiuscolo). Non
ci sono eccezioni: il blocco vale anche con `production_override` esplicito.
`API_ENV` va quindi impostata sempre, anche per eseguire le prove dei
revisori e gli script in `scripts/` (per esempio `API_ENV=development`).

### Database di test e migrazioni

Il ruolo che fa il **primo** `alembic upgrade head` su un cluster nuovo deve
essere un superuser (vedi "Prerequisiti" sopra). `DATABASE_URL` qui sotto usa
solo valori espliciti o default documentati (`root`/`localhost`/`5432`, gli
stessi ripieghi di `tests/`): non presuppone che le variabili sopra siano
già state esportate in questa shell.

```bash
createdb -O "${PGUSER:-root}" gravya_e1_test   # o: psql -c "CREATE DATABASE gravya_e1_test OWNER <ruolo>;"
DATABASE_URL="postgresql+psycopg://${PGUSER:-root}@${PGHOST:-localhost}:${PGPORT:-5432}/gravya_e1_test" alembic upgrade head
```

`DATABASE_URL` è obbligatoria per `alembic upgrade head` (nessun database di
default, DX-22): senza, la migrazione si rifiuta di partire con un messaggio
esplicito.

**Requisito di deploy (giro 5, correzione 7, non ancora automatizzato da
nessuno script):** se in futuro una migrazione deve ricreare la funzione
`gravya_e1_trace_owned_by_other_tenant` sotto un proprietario di migrazione
non superuser, la concessione temporanea di `CREATE` sullo schema `public` e
dell'appartenenza a `gravya_e1_so_owner` **deve** essere seguita da una
revoca, fatta dal superuser, subito dopo le migrazioni (esattamente come fa
`scripts/test-non-superuser.sh`, passo 5): senza quella revoca, chi ha
eseguito la migrazione resta permanentemente in grado di leggere le tracce
di ogni tenant con `SET ROLE gravya_e1_so_owner`.

### Eseguire i test

```bash
pytest -q
```

(`GRAVYA_E1_TEST_DSN`/`PGUSER` impostati come sopra; stessa `dbname` del
passo precedente, aggiunta internamente dai test.) `tests/` imposta da sé
`API_ENV=development` (fixture autouse in `tests/conftest.py`); fuori da
`tests/` va impostata sempre (vedi sopra). I test
creano e distruggono le proprie partizioni/righe dentro `gravya_e1_test`
(fixture `ensure_partitions_now`, `make_helper`, ecc.): non serve nessuna
preparazione oltre alle migrazioni. Nessun file temporaneo resta fuori da
`tmp_path` (gestito da pytest).

I test che usano un proxy TCP congelabile (rete bloccata dopo la
connessione: guardiano per-job, sink dei segnali) hanno bisogno di
raggiungere il server PostgreSQL via TCP con lo stesso ruolo di `PGUSER`: se
non riescono, lo **dicono nel messaggio di skip** (per esempio "TCP non
disponibile verso 127.0.0.1:5432 con l'utente ... : impostare
PGHOST/PGPORT/PGUSER"), non saltano in silenzio (giro 5, CR R1).

### Script di verifica con un ruolo non superuser (criterio di fine 2)

`scripts/test-non-superuser.sh` dimostra che le migrazioni e l'applicazione
funzionano quando lo schema è di proprietà di un ruolo non superuser
(`gravya_migrator`), non di chi avvia la migrazione:

```bash
PGUSER=<un_ruolo_superuser> PGHOST=127.0.0.1 PGPORT=5432 bash scripts/test-non-superuser.sh
```

Variabile opzionale `GRAVYA_PSQL`: comando con cui lo script lancia `psql`
(default `psql` dell'host, diviso in parole). In CI vale `docker run --rm -i
--network host <immagine-dei-servizi> psql`, così `psql` viene dalla stessa
immagine (stesso digest) del servizio PostgreSQL e non da apt. In locale, per
provare come in CI:

```bash
GRAVYA_PSQL="docker run --rm -i --network host postgres:18@sha256:<digest-di-ci.yml> psql" \
  PGUSER=root PGHOST=127.0.0.1 PGPORT=5433 bash scripts/test-non-superuser.sh
```

Usa un database "usa e getta" (`SCRATCH_DB`, default
`gravya_e1_ci_nonsuper`), eliminato alla fine anche in caso di errore. **Il
`PGUSER` di questo script deve essere un superuser**: il bootstrap una
tantum dei ruoli `gravya_migrator` (`CREATEROLE`) e soprattutto
`gravya_e1_so_owner` (`BYPASSRLS`, non ottenibile con `CREATEROLE`) richiede
privilegi che solo un superuser può concedere (vincolo di PostgreSQL, non di
questo progetto). Lo script poi:
1. concede temporaneamente `CREATE` sullo schema `public` e l'appartenenza a
   `gravya_e1_so_owner` a `gravya_migrator` (serve davvero per `ALTER
   FUNCTION ... OWNER TO`, non è un residuo da togliere: verificato con
   `psql` diretto, vedi report "Giro 5");
2. esegue le migrazioni con `MIGRATION_ROLE=gravya_migrator`;
3. *verifica* che un ruolo davvero non superuser possa scrivere, che il
   trigger anti-modifica e la funzione cross-tenant funzionino;
4. **revoca** la concessione temporanea del passo 1 (requisito di deploy) e
   verifica, con un ruolo di prova che NON è superuser, che `gravya_migrator`
   non possa più fare `SET ROLE gravya_e1_so_owner` dopo la revoca;
5. verifica che un ruolo non superuser possa scrivere un segnale
   (`PostgresSignalSink`, INSERT riuscito) ma non leggerlo (SELECT negato).

Tutte le connessioni di verifica (non quelle di bootstrap/revoca, che
restano del superuser) usano ruoli non superuser creati al volo, con
password generata a runtime (mai salvata, mai nel codice), eliminati
(`DROP OWNED` + `DROP ROLE`) alla fine.

### Prove dei revisori (`docs/revisioni/impl-e1/code-reviewer*/`)

Le suite di riproduzione dei revisori (`code-reviewer/`, `code-reviewer-giro2/`,
`code-reviewer-giro3/`, `code-reviewer-giro4/`, `code-reviewer-giro5/`) sono
file di prova non modificabili. Ognuna crea e cancella il proprio database
(`gravya_e1_review`, `_review2`, `_review3`, `_review4`, `_review5`) con una
fixture di sessione autouse. `pytest` trova da solo il `conftest.py` della
cartella del file indicato: **nessuna di queste suite ha bisogno di
`PYTHONPATH`** (verificato in questo giro eseguendo ciascuna sia con sia senza
`PYTHONPATH` impostata: stesso esito identico; la riga che lo richiedeva in
una versione precedente di questo README era inesatta).

`code-reviewer/` (giro 1) e `code-reviewer-giro2/` (giro 2) **hanno bisogno**
di `PGDATABASE`/`GRAVYA_E1_TEST_DSN`: alcune delle loro prove costruiscono
`TracingHelper` senza passare `conninfo` esplicito, affidandosi al ripiego
nudo di psycopg sulle variabili d'ambiente standard, che deve puntare al
database giusto:

```bash
export PGDATABASE=gravya_e1_review        # gravya_e1_review2 per il giro 2
export GRAVYA_E1_TEST_DSN="dbname=gravya_e1_review user=<ruolo>"
pytest -q docs/revisioni/impl-e1/code-reviewer/test_repro_rilievi.py
```

`code-reviewer-giro3/`, `code-reviewer-giro4/` e `code-reviewer-giro5/` **non
hanno bisogno** di `PGDATABASE` ne' di `GRAVYA_E1_TEST_DSN` (verificato in
questo giro eseguendole con e senza queste variabili: stesso esito identico):
i loro `conftest.py` passano sempre `conninfo`/`DATABASE_URL` espliciti con
`dbname=gravya_e1_review3` / `_review4` / `_review5` e autenticazione peer:

```bash
pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer-giro5/basetemp docs/revisioni/impl-e1/code-reviewer-giro5/test_giro5.py
```

## Nota sul ruolo di sviluppo (dipendenza dichiarata, non eliminabile ovunque)

- `tests/` (la suite applicativa, non quella dei revisori): **non dipende**
  da un ruolo chiamato `root`. Il nome compare solo come valore di default
  quando non si imposta nessuna variabile d'ambiente (`tests/_pgconn.py`,
  `tests/_freezable_proxy.py`): con `PGUSER`/`GRAVYA_E1_TEST_DSN` impostati a
  un ruolo qualsiasi (con i privilegi giusti) la stessa suite gira identica.
  **Verificato in questo giro**: creato un ruolo superuser diverso (nome a
  caso, eliminato subito dopo), database `gravya_e1_test` di sua proprietà,
  `tests/` eseguita per intero con `PGUSER`/`PGPASSWORD`/`PGHOST` impostati a
  quel ruolo via TCP (niente peer, niente `root`): stesso esito, nessuna
  differenza.
- `docs/revisioni/impl-e1/code-reviewer/conftest.py`,
  `code-reviewer-giro2/conftest.py`, `code-reviewer-giro3/conftest.py`,
  `code-reviewer-giro4/conftest.py` e `code-reviewer-giro5/conftest.py` (le
  cinque suite di riproduzione dei revisori, **non modificabili**) **scrivono
  `postgresql+psycopg://root@/...` e l'autenticazione peer implicita
  dell'utente del sistema operativo, letteralmente nel codice**: per
  eseguirle serve un ruolo PostgreSQL chiamato esattamente `root`, superuser,
  raggiungibile con autenticazione peer dall'utente del sistema operativo che
  lancia `pytest` (o da un utente di sistema chiamato `root`). Non c'è una
  variabile d'ambiente per cambiarlo in questi cinque file: è un limite dei
  file stessi, dichiarato qui e nel report dell'implementer
  (`docs/revisioni/impl-e1/report-implementer.md`, sezioni "Giro 4", "Giro 5"
  e "Giro 6"), non qualcosa che questo README possa aggirare senza modificare
  file di prova dei revisori.
- `scripts/test-non-superuser.sh` e `scripts/_verify_nonsuperuser.py` /
  `scripts/_verify_signals_nonsuperuser.py` **non dipendono** da un ruolo
  chiamato `root`: `PGUSER` può essere qualunque ruolo superuser (vedi
  sopra), passato per variabile d'ambiente. **Verificato in questo giro**
  con lo stesso ruolo creato per `tests/` sopra.

### Catena di fornitura (CI e controlli in locale)

Le Actions di GitHub hanno un tetto mensile di minuti (sforarlo ha già bloccato
tutto): su GitHub gira solo ciò che serve davvero, il resto gira su questa
macchina (DECISIONS §6 «Catena di fornitura» e «Minuti di GitHub Actions»).

**Su GitHub**
- `.github/workflows/ci.yml`: runner `ubuntu-24.04`, action fissate per SHA
  (checkout v7.0.1, setup-python v7.1.0, entrambe su Node 24); servizi PostgreSQL
  definiti una volta sola (ancora YAML), con il digest dell'immagine in un solo
  punto. Parte solo con `push` di branch (non di tag; non con `pull_request`: i
  merge in `main` si fanno in locale) o a mano (`workflow_dispatch`), e **non parte** se il push
  tocca solo `docs/**`, `stato/**`, `**/*.md`, `.claude/**` (`paths-ignore`:
  basta un file diverso perché parta). Un nuovo push sullo stesso branch annulla
  l'esecuzione in corso (`concurrency`).
- `.github/workflows/fornitura.yml`: il solo controllo OSV
  (`scripts/osv-check.py`), solo se il push cambia `requirements.lock.txt`,
  `scripts/osv-check.py` o il workflow stesso, o a mano. Niente `schedule`.
- `.github/dependabot.yml`: aggiornamenti settimanali delle action. I pacchetti
  Python non sono coperti da Dependabot: li copre il job locale qui sotto.

**In locale** (`scripts/fornitura-locale.py`, solo libreria standard più `git`,
`gh`, `docker`):
1. controllo OSV di `requirements.lock.txt` e di `requirements-strumenti.lock.txt`;
2. digest di PostgreSQL fissato in `ci.yml` contro quello attuale del tag;
3. rigenerazione del lockfile alle ultime versioni (comando dell'intestazione del
   lockfile con `--upgrade`, dopo un `git fetch`, su `origin/main`, nella cartella
   `.fornitura-lavoro/` ignorata da git); se cambia: branch `impl/lockfile-AAAA-MM-GG`,
   push e PR con le differenze (non ne apre un'altra se una PR di lockfile è ancora
   aperta). Se `main` locale ha commit non pubblicati su `pyproject.toml` o sui
   lockfile, non apre nessuna PR: esito «errore» con una issue che lo spiega (prima
   si fa il push di `main`).

Ogni controllo è isolato: un'eccezione inattesa in uno diventa il suo esito
«errore» (con la sua issue) e non fa perdere le issue degli altri. Un
controllo fallito apre una issue assegnata a `GravyaDev` con titolo fisso per tipo.
Se ce n'è già una aperta con lo stesso titolo: se il contenuto è cambiato aggiunge
un commento con il nuovo contenuto, se è invariato non fa nulla (le issue non si
chiudono da sole). `gh` parte sempre con `-R <proprietario>/<repository>` ricavato
dal remoto `origin`, mai dalla cartella di lancio; prima di scrivere in una issue,
in un commento o in una PR si tolgono i pattern di credenziali (`ghp_…`,
`github_pat_…`, `gho_…`, URL `https://…@`). Codici di uscita (somma bit a bit): 0
tutto a posto; 1 vulnerabilità; 2 digest cambiato; 4 controllo non riuscito; 8
aggiornamento del lockfile non riuscito (anche: git, gh, pip-tools, venv, timeout);
16 PR aperta (esito normale); 32 issue non aperta; con `--stato`, 64 = ultima
esecuzione riuscita troppo vecchia o assente.

**Traccia delle esecuzioni e `--stato`.** A ogni esecuzione (anche fallita o di
`--prova`) si aggiunge una riga JSON (data, esito per controllo, versioni) a
`~/.local/state/gravya-fornitura/esiti.jsonl`, fuori dal repository. Il controllo
periodico dipende da una macchina che può essere spenta (WSL2), quindi va
controllato che giri davvero:

```bash
python3 scripts/fornitura-locale.py --stato    # ultima esecuzione riuscita; errore (64) se più vecchia di 9 giorni o assente
```

Il `coordinator` lo esegue a ogni avvio di sessione. «Riuscita» = esecuzione vera
(non `--prova`) di tutti e tre i controlli senza nessun errore (trovare
vulnerabilità non è un fallimento del controllo). La soglia
(`SOGLIA_ESECUZIONE_GIORNI`, in testa a `scripts/fornitura-locale.py`) è il
periodo del timer più un margine di 2 giorni. Se manca la rete o il token di `gh`
è scaduto, la issue non si apre (codice 32 nel journal): in quel caso il segnale
è proprio `--stato`, che non dipende da GitHub.

**Strumenti fissati.** `pip-tools` e le sue dipendenze stanno, con versioni e hash,
in `requirements-strumenti.lock.txt` (comando di rigenerazione nell'intestazione,
partendo da `requirements-strumenti.in`) e si installano con `--require-hashes`;
il job settimanale controlla con OSV anche quel file. **Limite dichiarato:** la
rigenerazione (`pip-compile --all-build-deps`) risolve e costruisce le dipendenze di
build, che possono eseguire codice di terze parti nella stessa sessione utente in cui
`gh` e `git` hanno le credenziali: non è isolata in un contenitore. Mitigazioni: il
risultato passa da OSV, dalla CI e dalla revisione prima del merge; il token di `gh`
resta una scelta dell'utente (consigliato un token limitato al solo repository).

```bash
python3 scripts/fornitura-locale.py --prova                     # niente issue, branch, push o PR: riferisce soltanto
python3 scripts/fornitura-locale.py --solo digest               # un solo controllo (osv,digest,lockfile)
python3 scripts/fornitura-locale.py --solo digest --prova --digest-attuale sha256:<64 cifre>   # prova del ramo «digest cambiato» (solo con --prova)
python3 scripts/fornitura-locale.py                             # esecuzione vera
```

**Timer settimanale** (systemd utente; WSL2 con systemd e «linger» attivo). Le
unità stanno in `systemd/`; lo script le copia in `~/.config/systemd/user/` con
il percorso del repository e abilita il timer. Va lanciato dal repository
principale (non da un worktree) e si può rieseguire senza danni:

```bash
bash scripts/installa-timer-fornitura.sh
systemctl --user list-timers gravya-fornitura.timer      # prossima esecuzione
journalctl --user -u gravya-fornitura.service -n 50      # esito e messaggi
systemctl --user start gravya-fornitura.service          # esecuzione a mano ora
python3 scripts/fornitura-locale.py --stato              # l'ultimo controllo riuscito è recente?
systemctl --user disable --now gravya-fornitura.timer    # disinstallare
```

Il timer è settimanale con `Persistent=true`: se il computer era spento all'ora
prevista, l'esecuzione parte all'accensione successiva. Lo script esegue
`daemon-reload` dopo la copia e, se il timer era già attivo, anche `restart`
(altrimenti una modifica di `OnCalendar` non avrebbe effetto).

**Prima del merge in `main`** (in locale, `scripts/agenti.py`):

```bash
python3 scripts/agenti.py worktree-unisci <nome> -m "messaggio del merge"
```

Rifiuta (e `main` non cambia) se: l'HEAD del worktree non coincide con la punta di
`impl/<nome>`; `main` non è antenato del branch (`main` è andato avanti: prima si
aggiorna il branch con un merge di `main` e si rilanciano i controlli); l'ultima
esecuzione riuscita del job settimanale è più vecchia di `SOGLIA_ESECUZIONE_GIORNI`
(oppure si forza con `--forza-fornitura`, e il messaggio di merge lo riporta);
oppure un controllo fallisce. Nel worktree, con le variabili di
`.worktrees/<nome>.env`, esegue `scripts/osv-check.py` sui due lockfile, `pytest
tests/` e `scripts/test-non-superuser.sh`; solo se tutti riescono fa `git merge
--no-ff impl/<nome>` in `main` dal repository principale. Non fa push. L'obbligo
resta una convenzione del coordinator: un `git merge` a mano lo aggira.
