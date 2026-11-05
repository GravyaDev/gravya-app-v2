# Task per implementer: catena di fornitura della CI (scansione, aggiornamenti, componenti fissati)

Agente: implementer
Worktree: ci-fornitura
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura.

## Contesto
Rilievi RIPORTA del compliance-auditor in `docs/DECISIONS.md` §4 «Catena di fornitura e aggiornamenti» (report `docs/revisioni/e1-runtime/report-compliance-auditor.md`). Decisione dell'utente del 2026-11-05 («ok» alle raccomandazioni del coordinator):
1. controllo OSV del lockfile nella CI, a ogni push e ogni settimana; Dependabot settimanale per i pacchetti Python e per le action; il digest di PostgreSQL lo controlla lo stesso job settimanale;
2. runner fissato a `ubuntu-24.04`, `psql` dalla stessa immagine `postgres:18` della CI invece che da apt, action aggiornate a versioni su Node 24, sempre fissate per SHA;
3. lockfile separati per esecuzione e sviluppo rimandati al primo deploy (fuori da questo task);
4. nessun limite superiore in `requires-python` (fuori da questo task).

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10), parte di ambiente e CI; criterio principale: la decisione sopra.
Perimetro: solo i punti 1 e 2. Nessun cambiamento al codice applicativo, ai test, alle migrazioni, al lockfile.
Repository: .worktrees/ci-fornitura; branch di lavoro: impl/ci-fornitura
Push: sì (solo il branch `impl/ci-fornitura`, per far girare la CI)
Vincoli specifici:
1. **Controllo OSV.** Uno script nel repository (per esempio `scripts/osv-check.py`, solo libreria standard) che legge le versioni fissate in `requirements.lock.txt`, interroga `https://api.osv.dev/v1/querybatch` (ecosistema PyPI) ed esce con errore se una versione ha vulnerabilità note, elencandole. Un job della CI lo esegue a ogni push e pull request e una volta a settimana (`schedule`). Nessun valore di soglia o URL nascosto nel codice: costanti dichiarate in testa allo script con il loro motivo (strumento di CI, non codice applicativo).
2. **Digest di PostgreSQL.** Nello stesso job settimanale, un passo confronta il digest fissato in `.github/workflows/ci.yml` con quello attuale del tag `postgres:18` (per esempio `docker buildx imagetools inspect`) e fallisce con un messaggio chiaro se è cambiato (segnale per aggiornare il digest). Il digest fissato deve stare in un solo punto del workflow, se GitHub Actions lo permette per i `services`; se non lo permette, lascialo nei due job e dichiaralo nel report. Non deve cambiare la riga `image: postgres:18@sha256:...` dei servizi, che `scripts/agenti.py` legge per i worktree (deve restare una sola immagine distinta).
3. **Dependabot.** `.github/dependabot.yml` con aggiornamenti settimanali per `pip` e `github-actions`. Prima verifica nella documentazione ufficiale di GitHub se Dependabot sa aggiornare un lockfile `pip-compile` generato da `pyproject.toml` con hash: se non lo sa fare, fermati su quel punto e riportalo in `divergenze` con la fonte, senza inventare soluzioni.
4. **Runner e action.** `runs-on: ubuntu-24.04` in tutti i job. `actions/checkout` e `actions/setup-python` all'ultima release (oggi v7.0.1 e v7.1.0 secondo il coordinator: verificalo con `gh api repos/<action>/releases/latest`), fissate per SHA del commit con il tag nel commento; verifica che girino su Node 24 (`action.yml`, campo `runs.using`).
5. **psql.** Nel job `test-non-superuser` niente `apt-get install postgresql-client`: `psql` viene dalla stessa immagine dei servizi (per esempio un comando di passo che esegue `docker run --rm -i --network host ... psql`), con lo stesso digest. `scripts/test-non-superuser.sh` deve continuare a funzionare in locale con il `psql` dell'host: se serve un modo per scegliere il comando, una variabile d'ambiente con default `psql`, dichiarata in testa allo script e nel README.
6. Ambiente locale del worktree: `. .venv/bin/activate` e variabili `PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development` (PostgreSQL 18 in Docker dedicato). Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde; `bash scripts/test-non-superuser.sh` riuscito sia con il `psql` dell'host sia con il `psql` dell'immagine (come in CI); lo script OSV eseguito in locale con esito; dopo il push, CI verde in tutti i job sul branch (`gh run list --branch impl/ci-fornitura`, `gh run watch`). Il job settimanale si prova con `workflow_dispatch` se lo aggiungi, altrimenti dichiara che non è stato eseguito.
7. Commit piccoli, uno per argomento. README aggiornato dove cita CI, `psql` o controlli. Report in `docs/revisioni/ci-fornitura/report-implementer.md`: cosa è cambiato, SHA e versioni delle action con la verifica di Node 24, esito dello script OSV, esiti locali e della CI.
Cartella report: docs/revisioni/ci-fornitura/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
