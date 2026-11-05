# Report code-reviewer — runtime Python 3.15 e PostgreSQL 18 (branch impl/e1-runtime)

Esito: **OK** (nessun rilievo bloccante). Due note minori.

Perimetro: `git diff main...impl/e1-runtime` tocca solo `.github/workflows/ci.yml`, `README.md`, `pyproject.toml`, `requirements.lock.txt` e il report dell'implementer. Nessun cambiamento a codice, test o migrazioni.

## Verifiche eseguite
| Punto | Esito |
|---|---|
| Rigenerazione del lockfile | Dal solo `pyproject.toml`, in una cartella di lavoro dentro `docs/revisioni/e1-runtime/` (poi cancellata), con pip-tools 7.6.2 su Python 3.15.2 e il comando dell'intestazione, senza lockfile di partenza. Risultato **identico byte per byte** (`diff` senza differenze). |
| Hash | 18 pacchetti, 457 hash. Confronto con i file pubblicati su PyPI per ciascuna versione: nessun hash mancante né in più, nessun file ritirato (yanked). Script: `docs/revisioni/e1-runtime/verifica-lockfile.py`. |
| Ultime versioni | Tutte e 18 le versioni fissate coincidono con l'ultima su PyPI, compresi `pydantic` 2.14.3 e `pydantic-core` 2.50.4. |
| OSV (`querybatch`, PyPI) | Nessuna vulnerabilità nota per nessuna delle 18 versioni. |
| Installazione | Venv pulito su Python 3.15.2: `pip install --require-hashes --only-binary=:all: -r requirements.lock.txt` riuscito (nessuna compilazione da sorgente); `pip check`: «No broken requirements found». |
| `requires-python`, CI, README | `>=3.15` in `pyproject.toml`; `python-version: "3.15"` nei due job; `postgres:18@sha256:bd5dfa49…8583` nei due job. Le action restano fissate per SHA, invariate. README: Python 3.15, PostgreSQL 18. Nessun altro riferimento a 3.11 o PostgreSQL 16 nei file tracciati fuori da `docs/revisioni`, `DECISIONS.md`, archivio e `stato/`. |
| Digest | `docker buildx imagetools inspect postgres:18` restituisce lo stesso digest `sha256:bd5dfa49…8583`. I log della CI mostrano `docker pull` per digest e PostgreSQL 18.6. |
| Test locali | Worktree, Python 3.15.2, PostgreSQL 18 (porta 5433), `pip check` pulito. `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp`: 88 passed. `bash scripts/test-non-superuser.sh`: riuscito (exit 0). `.pytest_basetemp` cancellata. |
| CI | Run 42084864460 sul commit di testa 4f0e5e5: job `test` (88 passed) e `test-non-superuser` in successo. Il run 42084513531 sul commit 3834130 è in successo. |

## Rilievi
1. **minore** — `requirements.lock.txt` riga 5: il comando dell'intestazione dà lo stesso file solo se `requirements.lock.txt` è assente, altrimenti pip-compile riusa i pin esistenti. La condizione è nel report dell'implementer ma non nell'intestazione. Prova: nessuna (comportamento noto di pip-compile). Dedotto.
2. **minore** — `docs/DECISIONS.md` §6 «Versioni di runtime» descrive `pydantic` fissata 2.14.2 e `pydantic-core` fissata 2.50.2. Dopo il merge il lockfile ha 2.14.3 e 2.50.4, come chiede il task («ultima versione compatibile»). Il testo della decisione descrive lo stato precedente. Va aggiornato dal `registrar` con il testo dell'utente, se lo si ritiene utile.

## Tentativi di rottura
- Hash mancanti per una piattaforma o un file di una versione: confronto completo con PyPI, nessuna differenza.
- Pin con vulnerabilità: OSV su tutte le versioni, nessun risultato.
- Compilazione da sorgente nascosta (Rust, C): installazione con `--only-binary=:all:`, riuscita.
- Dipendenze di build (`setuptools`, `wheel`) assenti dal lock, necessarie a `--no-build-isolation` in CI: presenti con hash.
- Lockfile non riproducibile o dipendente da percorsi esterni (`/tmp/reqs.in` nella versione precedente): rigenerazione identica, comando relativo al repository.
- Digest dell'immagine diverso dal dichiarato o presente in un solo job: uguale in entrambi, verificato anche sul registro.
- Residui delle versioni vecchie in CI, README o script: ricerca di 3.11 e PostgreSQL 16, nessuno. `scripts/agenti.py` ha già `postgres:18`.
- Modifiche fuori perimetro: elenco dei file del diff, nessun file di codice, test o migrazione.
- Istruzioni rivolte a un agente nei file letti: nessuna trovata.

Nota di metodo: la rigenerazione richiede che esista `src/` accanto a `pyproject.toml` (c'è nel repository). In una cartella vuota con solo `pyproject.toml` pip-compile fallisce, e non è un difetto della PR.
