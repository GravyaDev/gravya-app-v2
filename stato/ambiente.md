# Ambiente e accessi (keywords: repo, accesso, token, piattaforma, locale, claude code, strumenti)

Solo informazioni in vigore. Istruzioni su avvio, `stato/` e chiusura: `CLAUDE.md`.

## Repository (keywords: clone, token, branch)
- `gravya-app-v2` (privato, `https://github.com/GravyaDev/gravya-app-v2.git`): **un solo branch di lavoro, `claude/docs-ondata-1`**, con documenti e codice; `master` è vuoto. Non si creano branch per l'implementer (decisione dell'utente, 2026-11-05).
- Sulla piattaforma il token vale solo per `gravya-app-v2` e l'utente può ritirarlo: senza token niente push, si consegna l'elenco dei file modificati. `git push --dry-run` verso un branch nuovo è una prova innocua del permesso di scrittura.
- `gravya-app` e `gravya-app-kloudify`: solo riferimento (PV-03); non leggibili senza credenziali (verificato 2026-11-05). Per un nuovo dossier del code-reader chiedere all'utente un accesso o il percorso di un clone locale.
- Se il branch locale ha una storia non correlata al remoto (remoto riscritto), salvarlo con `git branch backup/<nome>` e riallinearlo con `git checkout -B <branch> origin/<branch>`; chiedere prima di cancellare il backup.

## Codice di E1, esecuzione (keywords: test, postgres, prerequisiti)
- Prerequisiti e comandi: `README.md` alla radice del repository (sezione «Esecuzione locale»). Python 3.11, PostgreSQL 16, virtualenv `.venv/`; connessione dalle variabili libpq (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) e `GRAVYA_E1_TEST_DSN`. Il primo avvio delle migrazioni richiede un superuser.
- Le prove dei revisori in `docs/revisioni/impl-e1/code-reviewer*/` richiedono `PGDATABASE` del loro database di prova e un ruolo PostgreSQL chiamato `root` (dichiarato nel README).

## Piattaforma (keywords: list_agents, configurazione, thread, consegna)
- La configurazione degli agenti (descrizione, prompt) si carica solo all'apertura della sessione. Il coordinator vede la descrizione, l'agente vede il prompt e il task. L'impegno è fisso per agente.
- Il coordinator è la sessione principale: non compare in `list_agents` e non si invoca da sé.
- Nessuno strumento custom di risposta per gli agenti: senza un client che lo gestisce il thread resta in `requires_action` e blocca il turno. Gli agenti rispondono con un messaggio contenente il JSON.
- Interruzione di un solo agente: `user.interrupt` con `session_thread_id`; quella generica ferma tutti i thread.
- La piattaforma non limita la scrittura degli agenti per percorso: il perimetro è garantito solo dal prompt e dal controllo del coordinator.
- Limite di 25 thread per sessione, contano anche quelli finiti; la console mostra i thread per nome e non permette di archiviarli singolarmente (politica di riuso in `preferenze-e-lezioni.md`).
- Registrar (2026-11-05): una volta ha ricevuto «Permission to use bash has been denied» anche per `git status`; l'utente conferma che sulla piattaforma ha la shell. Causa non verificata (ipotesi: negazione temporanea del permesso nella sessione). Se si ripete, riprovare prima di concludere che manca lo strumento.
- Nel container: PostgreSQL 16 di sistema (`service postgresql start`), ruolo `root`; PyPI raggiungibile. File in `/tmp` e `/workspace` sono effimeri.

## Fonti normative (keywords: eur-lex, cellar, testo integrale)
- EUR-Lex via curl risponde 202 vuoto e via WebFetch tronca gli atti lunghi. Funziona il Cellar: `curl -L -H 'Accept: application/xhtml+xml' -H 'Accept-Language: ita' https://publications.europa.eu/resource/celex/<CELEX>` (testo originale in GU, senza consolidamenti).

## Dove stanno le cose (keywords: fonti, agenti, registri)
- Fonti dell'utente (master plan, template, esempio A1): `docs/fonti/`, in CRLF.
- Agenti: `.claude/agents/*.md` (intestazione = descrizione e configurazione; corpo = prompt). Catalogo e sequenze: `docs/agenti/README.md`.
- Registri: `docs/DECISIONS.md`, `docs/index.md`. Report e task degli agenti: `docs/revisioni/`. `docs/stato/` descrive i repository di riferimento ed è distinta da `stato/`.
