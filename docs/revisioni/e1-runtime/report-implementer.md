# Report implementer — runtime Python 3.15 e PostgreSQL 18

Documento: docs/E1-tracing-distribuito.md v1.10 (perimetro: solo versioni di runtime e dipendenze).

## Comando di rigenerazione
Dal `pyproject.toml` (nessun file d'ingresso esterno), con pip-tools nel `.venv` (non nel lockfile), partendo da un lockfile assente (altrimenti pip-compile riusa i pin esistenti):

    rm requirements.lock.txt
    pip-compile --all-build-deps --allow-unsafe --extra=dev --generate-hashes --output-file=requirements.lock.txt --strip-extras pyproject.toml

`--all-build-deps` include setuptools e wheel (`build-system.requires`), necessari a `pip install --no-build-isolation`.

## Pacchetti (OSV: nessuna vulnerabilità nota per tutte le versioni fissate; ultima versione su PyPI verificata)
| Pacchetto | Vecchia | Nuova | OSV |
|---|---|---|---|
| alembic | 1.20.1 | 1.20.1 | nessuna |
| annotated-types | 0.8.0 | 0.8.0 | nessuna |
| iniconfig | 2.3.1 | 2.3.1 | nessuna |
| mako | 1.4.3 | 1.4.3 | nessuna |
| markupsafe | 3.0.4 | 3.0.4 | nessuna |
| packaging | 26.3 | 26.3 | nessuna |
| pluggy | 1.7.0 | 1.7.0 | nessuna |
| psycopg | 3.3.8 | 3.3.8 | nessuna |
| psycopg-binary | 3.3.8 | 3.3.8 | nessuna |
| pydantic | 2.14.2 | 2.14.3 | nessuna |
| pydantic-core | 2.50.2 | 2.50.4 | nessuna |
| pygments | 2.21.0 | 2.21.0 | nessuna |
| pytest | 9.2.0 | 9.2.0 | nessuna |
| sqlalchemy | 2.1.8 | 2.1.8 | nessuna |
| typing-extensions | 4.16.0 | 4.16.0 | nessuna |
| typing-inspection | 0.4.5 | 0.4.5 | nessuna |
| wheel | 0.48.0 | 0.48.0 | nessuna |
| setuptools | 84.2.1 | 84.2.1 | nessuna |

Nota: con `--strip-extras` la riga `psycopg[binary]` diventa `psycopg` + `psycopg-binary` (stesso insieme di pacchetti).

## Altre modifiche
- `pyproject.toml`: `requires-python = ">=3.15"`; limiti inferiori delle dipendenze invariati.
- CI: `python-version: "3.15"` nei due job; `postgres:18@sha256:bd5dfa49…8583` nei due job.
- README: prerequisiti Python 3.15, PostgreSQL 18.

## Esiti
- `.venv` ricreato (Python 3.15.2) con `pip install --require-hashes -r requirements.lock.txt`; `pip check`: nessun errore.
- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` (PostgreSQL 18, porta 5433): 88 passed, 10 esecuzioni su 10.
- `bash scripts/test-non-superuser.sh`: riuscito.
- CI (GitHub, run 42084513531 sul commit 3834130): successo nei due job, `test` e `test-non-superuser`. Avvisi non bloccanti: Node.js 20 deprecato per le action fissate; `ubuntu-latest` migrerà a Ubuntu 26 dal 2026-10-19.
