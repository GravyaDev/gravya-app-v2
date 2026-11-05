# Report implementer — catena di fornitura della CI

Branch `impl/ci-fornitura`. Perimetro: punti 1 e 2 della decisione (DECISIONS §4 «Catena di fornitura e aggiornamenti»).

## Cosa è cambiato
- `scripts/osv-check.py` (solo libreria standard): legge `nome==versione` da `requirements.lock.txt`, interroga OSV `querybatch` (PyPI, con paginazione e blocchi da 1000), esce 1 se ci sono vulnerabilità (elenco su stderr), 2 se OSV non risponde / risposta non valida / lockfile vuoto o illeggibile (fail-closed). Costanti (URL, ecosistema, blocco, timeout) in testa con il motivo.
- `.github/workflows/fornitura.yml`: job `osv` a ogni push, pull request, `schedule` settimanale (lunedì 05:17 UTC) e `workflow_dispatch`; job `digest-postgres` solo su `schedule`/`workflow_dispatch`: legge l'immagine `postgres:<tag>@sha256:…` da `ci.yml` (deve essere una sola), ottiene il digest attuale con `docker buildx imagetools inspect` e fallisce con messaggio chiaro se cambiato.
- `.github/workflows/ci.yml`: `runs-on: ubuntu-24.04` in tutti i job; action aggiornate e fissate per SHA; servizi PostgreSQL definiti **una volta sola** con ancora YAML (`services: &servizi` nel job `test`, `services: *servizi` in `test-non-superuser`): il digest sta in un solo punto e la riga `image: postgres:18@sha256:…` è invariata (`scripts/agenti.py` → `IMMAGINE_PG` verificato, una sola immagine). Nel job `test-non-superuser` tolto `apt-get install postgresql-client`: `psql` da `docker run --rm -i --network host <immagine del servizio> psql`, con l'immagine letta da `docker inspect` del container del servizio (stesso digest, nessuna duplicazione) e controllata con `case`.
- `scripts/test-non-superuser.sh`: variabile `GRAVYA_PSQL` (default `psql`), dichiarata in testa e nel README.
- `.github/dependabot.yml`: solo `github-actions`, settimanale. Il `pip` NON è configurato (vedi divergenze).
- `tests/test_ci_osv_check.py` (file nuovo, offline, 11 test: parsing, vulnerabile/pulito, paginazione, blocchi, risposte non valide, esiti di `main` incluso rete assente e lockfile vuoto). Il task diceva «nessun cambiamento ai test»: non ho modificato test esistenti, ho aggiunto solo questo.
- README: `GRAVYA_PSQL` e sezione «Catena di fornitura (CI)».

## Action (verificate con `gh api`)
| Action | Release latest | SHA del commit | `runs.using` |
|---|---|---|---|
| actions/checkout | v7.0.1 | 3d3c42e5aac5ba805825da76410c181273ba90b1 | node24 |
| actions/setup-python | v7.1.0 | 6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 | node24 |

(SHA risolti dal tag con `git/ref/tags/<tag>`, tipo `commit`; `action.yml` letto a quel SHA.)

## Esiti
- OSV in locale: `python3 scripts/osv-check.py` → «OK: nessuna vulnerabilità nota in 18 pacchetti», exit 0. Prova di rilevamento: un lockfile temporaneo con `jinja2==2.4.1` → exit 1 con elenco di 18 ID (file poi cancellato).
- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp`: 99 passed.
- `bash scripts/test-non-superuser.sh` con `psql` dell'host: riuscito (exit 0). Con `GRAVYA_PSQL="docker run --rm -i --network host postgres:18@sha256:bd5d… psql"`: riuscito (exit 0).
- CI sul branch (run 42087878924): `test` e `test-non-superuser` success; run `Catena di fornitura` del push (42087878876): `osv` success.
- Job settimanale provato con `workflow_dispatch` (run 42088064447): `osv` e `digest-postgres` success (digest fissato = digest attuale di `postgres:18`). Il ramo «digest cambiato → fallisce» non è stato provato con un digest diverso.

## Divergenze e punti aperti
- **Dependabot per pip**: la documentazione ufficiale (docs.github.com, «Supported ecosystems and repositories», sezione «pip and pip-compile») dice solo che Dependabot supporta «any `.txt` file» e `pyproject.toml` PEP 621; non dice che rigeneri un lockfile `pip-compile` con `--generate-hashes --all-build-deps --extra=dev` da `pyproject.toml`. Come da task, mi fermo: nessuna voce `pip` in `dependabot.yml`. Serve una decisione (provare con una PR reale di Dependabot, o altra via).
- Il commit `d3d1fb0` («scripts/osv-check.py…») contiene per errore tutto il lavoro (un primo tentativo di commit separati era fallito per identità git mancante, ma i file erano già in staging): non è un commit per argomento come richiesto. Già pushato, non riscrivo la storia.
- Il commento del passo «Crea il database di test» in `ci.yml` cita ancora che `test-non-superuser` usa `psql`: resta vero (ora dall'immagine), non modificato.
- Ancora YAML nei workflow: funzionano su GitHub Actions (verificato dalla CI verde); `scripts/agenti.py` legge la riga `image:` con la regex invariata.

## Giro 2

Correzione del BLOCCA del `code-reviewer` e del minore del `compliance-auditor`.
Perimetro: `scripts/osv-check.py`, `tests/test_ci_osv_check.py`.

**Punti 1-2 (commit e3759ef).** `invia_http` ora:
- rifiuta ogni stato HTTP diverso da 200 (`http.HTTPStatus.OK`; prima un 204 vuoto passava solo per il fallimento del parse JSON);
- cattura anche `http.client.HTTPException` (`IncompleteRead` e simili): errore OSV con codice 2 e messaggio, senza traceback (prima traceback e codice 1).

Test reali (server HTTP locale su `127.0.0.1` avviato nel test, nessuna rete esterna), tutti via `main` con `invia_http` vera e codice atteso 2: stato 500/404/204, corpo non JSON, corpo non UTF-8, risposta troncata, porta chiusa, timeout (server lento e `TIMEOUT_SECONDI` ridotto dal test). Controprova: risposta valida con vulnerabilità → 1, pulita → 0.

**Punto 3 (commit c11fa33).** `leggi_lockfile` è fail-closed: ogni riga a colonna 0 non vuota e non commento è un blocco e deve essere `nome==versione` (a fine riga solo marcatore `;` e backslash), altrimenti `ErroreLockfile` → codice 2. Il numero di pacchetti letti deve coincidere con i blocchi. Test: `nome[extra]==v`, `nome @ url`, `>=`, `===`, testo dopo la versione, `--index-url`, `-e .`; conteggio pacchetti = blocchi; lockfile attuale conforme.

**Nota onesta.** Il controllo dei conteggi è difensivo: con la lettura rigorosa riga per riga non è raggiungibile da input reali (una riga non letta solleva prima). Il test verifica l'uguaglianza; non esiste un mutante che solo quel controllo distingua.

**Verifiche.**
- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` (ambiente come da task): 117 passed.
- `python3 scripts/osv-check.py requirements.lock.txt`: esito 0 (18 pacchetti).
- `prova-mutante.sh`: la riga mutata (`raise ErroreOsv(f"richiesta a {url} fallita: {e}") from e`) è rimasta identica, quindi il mutante è quello del reviewer. Suite del branch sul mutante: 8 failed (prima 11 passed); le tre prove del reviewer falliscono sul mutante e passano sul codice del branch (3 passed).
- Correzione (giro 3): l'affermazione precedente sul caso 204 era inesatta. Il test sul 204 passa con e senza il controllo dello stato (un corpo vuoto fallisce comunque il parse JSON), quindi non lo protegge. Il rifiuto degli stati diversi da 200 è protetto solo dai test del giro 3 (2xx con corpo valido).

README: il comportamento documentato (errore se OSV non risponde) non cambia; non toccato.

## Giro 3

Correzione del secondo BLOCCA del `code-reviewer`. Perimetro: solo `tests/test_ci_osv_check.py`; `scripts/osv-check.py` non modificato (nessun difetto rivelato).

**Test aggiunti/modificati.**
- `test_invia_http_stato_2xx_diverso_da_200_con_corpo_valido_codice_2`: stato 201, 203, 206, ciascuno con corpo pulito (`{"results": [{}]}`) e con corpo vulnerabile; atteso codice 2 e messaggio «stato HTTP <n>», senza traceback.
- `test_invia_http_timeout_codice_2`: la risposta tardiva (1 s) è ora **valida** e pulita; `TIMEOUT_SECONDI` ridotto a 0,2 s dal test con `monkeypatch` (default dello script invariato). Atteso codice 2 e «timed out» nel messaggio. Dura circa 1 s.

**Mutanti** (copie dello script in `docs/revisioni/ci-fornitura/lavoro-mutanti/`, cancellata a fine prova), eseguiti con la suite di `tests/test_ci_osv_check.py`:

| Mutante | Modifica | Esito |
|---|---|---|
| m1 | `if risposta.status != HTTP_OK:` → `if False:` | 6 failed, 29 passed (tutti i casi 201/203/206) |
| m2 | `if risposta.status != HTTP_OK:` → `if risposta.status >= 400:` | 6 failed, 29 passed (tutti i casi 201/203/206) |
| m3 | `timeout=TIMEOUT_SECONDI` → `timeout=None` | 1 failed (`test_invia_http_timeout_codice_2`), 34 passed |

**Prove del code-reviewer** (`prove-code-reviewer-giro2/prova-sopravvissuti.sh`, non modificate): sul codice del branch 4 passed; la suite del branch ora fallisce su s1 (6 failed) e s2 (1 failed), come le prove (s1: 3 failed, s2: 1 failed). s3 (lockfile) resta rilevato dalla suite (7 failed).

**Verifiche.** `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` con le variabili del worktree (`../ci-fornitura.env`, PostgreSQL su 5433): 123 passed. CI sul branch: da verificare dopo il push.
