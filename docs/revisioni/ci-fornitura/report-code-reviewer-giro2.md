# Report code-reviewer, giro 2: controllo OSV (`impl/ci-fornitura`)

Diff verificato: `git diff a0f238c..impl/ci-fornitura` (3 commit: e3759ef, c11fa33, 3f64f3d).
File toccati: `scripts/osv-check.py`, `tests/test_ci_osv_check.py`, `docs/revisioni/ci-fornitura/report-implementer.md`. Nessun cambiamento fuori perimetro.

**Esito: BLOCCA.** Il BLOCCA del giro 1 è risolto per il caso principale, cioè `invia_http` che ingoia l'errore. Resta però un controllo introdotto in questo giro, il rifiuto di uno stato HTTP diverso da 200, che nessun test protegge. Resta anche un test del timeout che non verifica il timeout.

## Punti richiesti

### 1. I test nuovi falliscono sui mutanti di `invia_http`?

Comandi, eseguiti dalla radice del worktree con `.venv` attiva e le variabili del task precedente.

- `bash ../../docs/revisioni/ci-fornitura/prove-code-reviewer/prova-mutante.sh`:
  - suite del branch sul mutante del giro 1: 8 falliti, 21 passati;
  - prove del giro 1 sul mutante: 3 falliti;
  - le stesse prove sul branch: 3 passati.
- `pytest tests/test_ci_osv_check.py` sul branch: 29 passati.
- Mutanti miei, uno per volta, contro la sola suite del branch:

| Mutante | Esito della suite |
|---|---|
| `invia_http` ingoia l'errore (restituisce risultati vuoti) | ucciso, 7 falliti (stato 500, 404, corpo non JSON, non UTF-8, troncata, porta chiusa, timeout) |
| `except` senza `http.client.HTTPException` | ucciso (`risposta_troncata`) |
| `except` senza `ValueError` | ucciso (corpo non JSON, non UTF-8) |
| `main` non cattura `ErroreLockfile` | ucciso (7 casi di lockfile) |
| controllo dello stato rimosso (`if False:`) | **sopravvive**, 29 passati |
| controllo dello stato ridotto a `>= 400` | **sopravvive** |
| nessun timeout (`timeout=None`) | **sopravvive**, 29 passati |

Nota sul lavoro: nella prima esecuzione i mutanti sembravano morire tutti per `test_lockfile_attuale_e_conforme`. Era un artefatto del mio ambiente, perché quel test legge `requirements.lock.txt` dalla cartella padre e nella cartella del mutante non c'era. Ho corretto copiando il lockfile e ho rieseguito. La tabella sopra riporta solo i risultati dopo la correzione.

**Perché il controllo dello stato non è protetto.**
- `urlopen` solleva `HTTPError` (un `OSError`) per ogni stato 4xx e 5xx. I test `stato_500` e `stato_404` quindi non esercitano la riga `risposta.status != HTTP_OK`.
- Il caso `stato_204` ha corpo vuoto. Senza il controllo, `json.loads("")` solleva `ValueError` e si arriva comunque al codice 2.
- L'unico input che distingue il controllo è un 2xx diverso da 200 con corpo JSON valido (201, 203, 206). Nessun test lo usa.
- Il report dell'implementer dice che il caso 204 «è coperto dal test sul codice corretto». Non lo è: il test passa con e senza il controllo.
- Senza il controllo, un proxy o un gateway che risponde 203 o 206 con un `{"results":[{}]}` valido dà «nessuna vulnerabilità» (codice 0).

**Timeout.**
- `test_invia_http_timeout_codice_2` fa rispondere il server dopo 2 secondi con `{}`.
- `{}` non ha `results`, quindi `interroga` solleva `ErroreOsv` e il codice è 2 anche senza alcun timeout.
- Il test non distingue «timeout scattato» da «risposta lenta e non valida».
- Senza timeout il rischio è una CI appesa, non un fail-open.

Prova: `docs/revisioni/ci-fornitura/prove-code-reviewer-giro2/prova-sopravvissuti.sh` con `test_stato_e_timeout.py`.
- Controllo dello stato rimosso: suite del branch 29 passati, prova 3 falliti su 4.
- Mutante senza timeout: suite del branch 29 passati, prova 1 fallito.
- Sul branch: 4 passati.

### 2. `IncompleteRead` e gli altri errori di `http.client`: codice 2 senza traceback

Verificato.
- `IncompleteRead` è coperto dal test `risposta_troncata`, che asserisce codice 2, `ERRORE:` su stderr e assenza di `Traceback`.
- Ho provato a mano con un socket grezzo:
  - riga di stato non valida → `BadStatusLine`;
  - connessione chiusa senza risposta → `RemoteDisconnected`;
  - chunk non valido → `IncompleteRead`.
- Tutti e tre diventano `ErroreOsv` (codice 2).
- Il mutante senza `HTTPException` fallisce in `risposta_troncata`.

### 3. Lettura del lockfile fail-closed

Verificato.
- Una riga a colonna 0 che non sia `nome==versione` solleva `ErroreLockfile`, che `main` converte in codice 2.
- I 7 casi parametrizzati (`nome[extra]==v`, `nome @ url`, `>=`, `===`, testo dopo la versione, `--index-url`, `-e .`) fanno fallire sia `leggi_lockfile` sia `main`.
- Il mutante che aggiunge `continue` prima del `raise` fallisce 1 test: il controllo dei conteggi lo ferma.
- Il controllo dei conteggi rimosso da solo non cambia nulla, perché il regex rigoroso già solleva. Il mutante con entrambe le difese tolte è ucciso da 7 test.
- Le due difese sono ridondanti, come l'implementer dichiara nel report. Non è un difetto.
- `python3 scripts/osv-check.py requirements.lock.txt` esce 0 su 18 pacchetti.

### 4. Cambiamenti fuori perimetro

Nessuno. Il diff tocca solo lo script, il suo test e la sezione «Giro 2» del report. Non ci sono workflow, Dependabot, README né funzionalità non documentate.

## Rilievi

1. **Bloccante, verificato.** Il rifiuto di uno stato HTTP diverso da 200 (`scripts/osv-check.py`, riga `if risposta.status != HTTP_OK`) non ha un test che lo distingua. Il task chiedeva test che falliscano su mutanti che ingoiano «stato HTTP diverso da 200». Il mutante senza controllo lascia la suite verde (29 passati). Serve un test con 2xx diverso da 200 e corpo valido, atteso codice 2.
2. **Da riportare, verificato.** Il test del timeout non verifica il timeout. Il server risponde con `{}`, che dà comunque codice 2. Con `timeout=None` la suite resta verde. Serve una risposta tardiva ma valida (`{"results":[{}]}`), attesa codice 2.
3. **Minore.** Il report dell'implementer afferma che il caso 204 è «coperto dal test sul codice corretto». L'affermazione è inesatta (vedi punto 1).

Gli altri rilievi del giro 1 (Dependabot per pip, costanti tautologiche, ancore YAML, esecuzioni doppie) restano come riportati e non sono stati riesaminati.

## Tentativi di rottura
- Mutante che ingoia l'errore di `invia_http`.
- Mutanti sullo stato HTTP, sul timeout, sulle eccezioni catturate, sulla gestione di `ErroreLockfile`, sul `continue` nel lockfile e sul controllo dei conteggi.
- Risposte HTTP malformate con un socket grezzo.
- 2xx diversi da 200 con corpo valido.
- Risposta tardiva ma valida.

## Prove nel repository principale
- `docs/revisioni/ci-fornitura/prove-code-reviewer-giro2/prova-sopravvissuti.sh`
- `docs/revisioni/ci-fornitura/prove-code-reviewer-giro2/test_stato_e_timeout.py`
- La cartella di lavoro `lavoro-mutanti/` è stata cancellata.
- Il worktree non è stato modificato.
