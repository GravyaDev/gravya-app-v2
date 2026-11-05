# Ambiente e accessi (keywords: repo, accesso, token, piattaforma, locale, claude code, strumenti)

Solo informazioni in vigore. Istruzioni su avvio, `stato/` e chiusura: `CLAUDE.md`.

## Repository (keywords: clone, token, branch)
- `gravya-app-v2` (privato, `https://github.com/GravyaDev/gravya-app-v2.git`): **un solo branch di lavoro, `main`** (unico branch del remoto dopo la PR #1; decisione dell'utente, 2026-11-05), con documenti e codice. Non si creano branch per l'implementer.
- Sulla piattaforma il token vale solo per `gravya-app-v2` e l'utente può ritirarlo: senza token niente push, si consegna l'elenco dei file modificati. `git push --dry-run` verso un branch nuovo è una prova innocua del permesso di scrittura.
- `gravya-app` e `gravya-app-kloudify`: solo riferimento (PV-03). Sulla piattaforma non leggibili senza credenziali. In locale i clone `~/Antigravity/gravya-app` e `~/Antigravity/gravya-app-kloudify` sono **lavoro in corso dell'utente: SOLA LETTURA, mai toccarli** (vincolo dell'utente, 2026-11-05). Blocco: hook `.claude/hooks/riferimenti-sola-lettura.py` (unico punto con i percorsi protetti) e regole `deny` in `.claude/settings.json`, valide per ogni sessione aperta in questo repository, agenti compresi (provato con un agente). Si leggono solo con Read, Grep e Glob (anche `git status` scrive in `.git/index`); al code-reader si passano con `--add-dir`. L'hook rifiuta ogni comando Bash che ne nomina il percorso, anche dentro un testo: i file che li citano si scrivono con Edit o Write. Non rimuovere strumenti che usano (es. Python 3.14 di uv per i loro worktree).
- Se il branch locale ha una storia non correlata al remoto (remoto riscritto), salvarlo con `git branch backup/<nome>` e riallinearlo con `git checkout -B <branch> origin/<branch>`; chiedere prima di cancellare il backup.

## Codice di E1, esecuzione (keywords: test, postgres, prerequisiti)
- Prerequisiti e comandi: `README.md` alla radice del repository (sezione «Esecuzione locale»). Versioni: DECISIONS §6 «Versioni di runtime» (README e CI ancora su Python 3.11 e PostgreSQL 16 fino all'aggiornamento); virtualenv `.venv/`; connessione dalle variabili libpq (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) e `GRAVYA_E1_TEST_DSN`. Il primo avvio delle migrazioni richiede un superuser.
- Le prove dei revisori in `docs/revisioni/impl-e1/code-reviewer*/` richiedono `PGDATABASE` del loro database di prova e un ruolo PostgreSQL chiamato `root` (dichiarato nel README).

## Claude Code locale (keywords: wsl, script agenti, python, postgres, docker)
- Macchina dell'utente: WSL2 (Linux), Claude Code 2.x, `gh` autenticato. Repository in `~/Antigravity/gravya-app-v2`.
- Agenti: `scripts/agenti.py` (uso in `CLAUDE.md`). `claude -p --agent <nome>` rispetta il `model:` del file (verificato 2026-11-05 con il registrar: Haiku). Il controllo dei file comparsi guarda repository, `/tmp` (escluse le cartelle `claude-*` di Claude Code) (non le cartelle `--add-dir`, in sola lettura). Con più lanci in parallelo l'elenco comprende i file degli altri agenti attivi e dei processi della macchina in `/tmp`: si legge confrontandolo con i perimetri.
- Python: 3.15 di uv (`uv python find 3.15`); `.venv/` creato con quello dal lockfile. `python3` di sistema è la 3.12.
- PostgreSQL 18 in Docker: container `gravya-v2-pg18`, volume `gravya-v2-pg18-data`, `127.0.0.1:5432`, superuser `root` senza password (trust, solo su localhost). Dopo un riavvio: `docker start gravya-v2-pg18`. Variabili per i test: `PGHOST=127.0.0.1 PGPORT=5432 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5432 user=root" API_ENV=development`; comando `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp`. `psql` e `createdb` con `docker exec gravya-v2-pg18 …` finché manca il client sull'host.
- Prove dei revisori (`docs/revisioni/impl-e1/code-reviewer*/`): hanno scritto nei file il percorso della piattaforma `/workspace/wt-impl-e1`; in locale girano solo con il collegamento simbolico di `azioni-utente.md`.

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
