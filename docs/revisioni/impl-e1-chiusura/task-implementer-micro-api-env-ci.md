# Task per implementer: API_ENV nella CI (seguito della micro-correzione)

Agente: implementer
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Seguito di `docs/revisioni/impl-e1-chiusura/task-implementer-micro-api-env.md` (tuo commit db41169, risposta in `risposta-implementer-micro-api-env.json`). Nel tuo `non_verificato` hai segnalato che `scripts/_verify_nonsuperuser.py` ora richiede `API_ENV` e che `scripts/test-non-superuser.sh` non la esporta. Verifica del coordinator: neanche `.github/workflows/ci.yml` imposta `API_ENV`, in nessuno dei due job; il task originale chiedeva la variabile «esportata nel README e nella CI».

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10)
Perimetro: solo la micro-correzione API_ENV (DECISIONS §6 «E1: ambiente e avvio»): `API_ENV: development` nel blocco `env:` di entrambi i job di `.github/workflows/ci.yml`. Nient'altro nella CI: niente cambi di versioni di Python o PostgreSQL (lavoro a parte, già deciso). In `scripts/test-non-superuser.sh` non impostare un valore: se `API_ENV` non è impostata, lo script si ferma subito con un messaggio chiaro (coerente con il fail-closed: nessun valore implicito).
Repository: radice del repository; branch di lavoro: main
Push: no
Vincoli specifici: commit separato; aggiorna la sottosezione «Micro-correzione API_ENV» in coda a `docs/revisioni/impl-e1/report-implementer.md`. Ambiente locale come nel task precedente (`.venv/` con Python 3.15; PostgreSQL 18 su 127.0.0.1:5432, ruolo `root`). Lo script `.sh` non è eseguibile in locale (manca `psql`): verifica almeno `bash -n` e il ramo con `API_ENV` non impostata (deve fermarsi prima di usare `psql`).
Cartella report: docs/revisioni/impl-e1/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
