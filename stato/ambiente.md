# Ambiente e accessi (keywords: repo, accesso, token, piattaforma, agenti, strumenti, locale, claude code)

## Due ambienti (keywords: piattaforma, locale, abbonamento, claude code)
- Dal 2026-11-05 (sessione 8, richiesta dell'utente) il lavoro deve poter continuare anche in Claude Code locale con l'abbonamento, se finisce il credito API. Stato di lavoro e task stanno nel repository. Istruzioni su avvio, `stato/` e chiusura: solo in `CLAUDE.md` (decisione dell'utente, 2026-11-05); il prompt del coordinator vi rimanda e descrive le differenze tra ambienti («Ambiente: piattaforma o Claude Code locale»).
- Le sezioni sotto marcate «piattaforma» valgono solo nel container della piattaforma (percorsi `/workspace/...`, `/mnt/...`, PostgreSQL di sistema con ruolo `root`).

## Ambiente locale (keywords: claude code, prerequisiti, test, postgres)
- Prerequisiti del codice di E1 (branch `claude/impl-e1`): Python 3.11, PostgreSQL 16 raggiungibile, virtualenv `.venv/` nella radice del repository. I test leggono la connessione dalle variabili libpq (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) e da `GRAVYA_E1_TEST_DSN`; le prove dei revisori richiedono `PGDATABASE` del loro database di prova (vedi `docs/revisioni/impl-e1/report-implementer.md`, giro 3). Lo script `scripts/test-non-superuser.sh` richiede un superuser per il bootstrap dei ruoli.
- Le istruzioni di esecuzione locale complete (README del codice) non esistono ancora: da chiedere all'implementer dopo il giro 4.
- Clone di riferimento (`gravya-app`, `gravya-app-kloudify`): percorso locale da chiedere all'utente se servono.


## Repository, piattaforma (keywords: clone, token, branch)
- gravya-app-v2 (privato): `git clone https://github.com/GravyaDev/gravya-app-v2.git`, branch di lavoro `claude/docs-ondata-1`; master è vuoto.
- Il token di sessione vale solo per gravya-app-v2 e può essere ritirato dall'utente: in quel caso niente push, si consegna l'elenco dei file modificati.
- gravya-app e gravya-app-kloudify: verificato il 2026-11-05 (sessione 8) che **non** sono più leggibili senza credenziali (`git ls-remote` senza helper chiede l'utente); la nota precedente «pubblici» è superata. Sono solo riferimenti (PV-03). Nella sessione 8 erano già clonati in `/workspace/` (effimero). L'utente può ritirare il token per questi repository: per un nuovo dossier del code-reader (per esempio l'Appendice A dei documenti dell'ondata 2) va chiesto un accesso o un clone locale.

- Clone locale all'avvio (sessione 6): HEAD staccato, con il branch locale `claude/docs-ondata-1` indietro di 31 commit rispetto a origin. Prima di leggere: `git fetch origin claude/docs-ondata-1 && git checkout claude/docs-ondata-1 && git merge --ff-only origin/claude/docs-ondata-1`.

- Sessione 8: il `merge --ff-only` è fallito con "refusing to merge unrelated histories" (il clone locale aveva una storia vecchia, il remoto era stato riscritto). Soluzione usata: `git branch backup/<nome> claude/docs-ondata-1` e poi `git checkout -B claude/docs-ondata-1 origin/claude/docs-ondata-1`.
- Sessione 8: `git push --dry-run` verso un branch nuovo funziona come prova innocua del permesso di scrittura. Per far lavorare l'implementer in parallelo al coordinator si usa un worktree separato (`git worktree add /workspace/wt-<nome> -b <branch> origin/<base>`).
- Blocco del Registrar nella sessione 5 (keywords: registrar, blocco, consegna): la causa, accertata dall'utente sugli eventi della console, era la vecchia versione dell'agente, che aveva ancora lo strumento custom di risposta. Chiuso.
- La piattaforma non permette di limitare la scrittura degli agenti per percorso (utente, 2026-11-04): il perimetro di scrittura è garantito solo dal prompt (regola comune 6) e dal controllo del coordinator dopo ogni invocazione.

## Dove stanno le cose (keywords: fonti, agenti, registri)
- Fonti dell'utente (master plan, template, esempio A1): `docs/fonti/`, in CRLF. Originali nel commit 7dcf7b0.
- Agenti: `.claude/agents/*.md` (intestazione = Descrizione della piattaforma; corpo = Prompt; model/effort/tools). Catalogo e sequenze: `docs/agenti/README.md`.
- Registri: `docs/DECISIONS.md`, `docs/index.md`. Report degli agenti: `docs/revisioni/`.

## Comportamenti della piattaforma (keywords: list_agents, configurazione, sessione)
- La configurazione degli agenti (descrizione, prompt) si carica solo all'apertura della sessione: modifiche fatte a sessione aperta non si vedono.
- Il coordinator vede solo la Descrizione degli agenti, non il loro Prompt; l'agente vede solo il Prompt e il task.
- L'impegno (effort) è fisso per agente, non per singola chiamata.
- Una sessione su Opus non può creare agenti al volo su un altro modello: si usano gli agenti predefiniti.
- Nomi sulla piattaforma: "Registrar", "Coordinator", ecc. (vedi list_agents).
- Il coordinator è la sessione principale: non può invocare se stesso e non compare in list_agents. Potrà invocarlo solo un futuro supervisor; per ora nessun test "come agente" (indicazione dell'utente, sessione 3).
- Consegna delle risposte degli agenti (keywords: risposta_*, send_to_parent, blocco, custom tool): lo schema di output sta solo nel prompt. Uno strumento custom lo esegue il client (`user.custom_tool_result`); senza client il subagente resta in `requires_action` e il turno del coordinator si blocca finché l'utente non interrompe (sessione 3, spiegazione della revisione richiesta dall'utente). Consegna: messaggio con `send_to_parent` contenente il JSON. Azioni lato utente: `azioni-utente.md`.
- Interruzione di un solo agente (keywords: interrupt, thread): `user.interrupt` con `session_thread_id`; l'interruzione generica ferma tutti i thread, compreso il principale. L'utente ne ha preso atto (2026-11-04) e la usa quando serve.
- Watchdog su `requires_action` (keywords: watchdog, blocco): servirebbe un client esterno che legge gli eventi della sessione via API; dalla UI non risulta configurabile (non verificato). Non serve finché nessun agente ha strumenti custom: senza strumenti custom il thread non va in `requires_action`. Voce tolta da azioni-utente il 2026-11-04.

## Testi ufficiali UE senza EUR-Lex (keywords: eur-lex, cellar, curl, 202, regulatory-researcher, testo integrale)
- Sessione 7: EUR-Lex via curl risponde 202 con corpo vuoto (challenge anti-bot) e via WebFetch tronca gli atti lunghi (GDPR fino al considerando 87). Funziona il Cellar dell'Ufficio pubblicazioni: `curl -L -H 'Accept: application/xhtml+xml' -H 'Accept-Language: ita' https://publications.europa.eu/resource/celex/<CELEX>` restituisce la GU ufficiale (XHTML); poi conversione in testo e lettura con Read/Grep. Testato su 32016R0679, 32022L2555, 32023D1795. È il testo originale in GU, senza rettifiche né consolidamenti.
- I file scaricati in /tmp/s7/fonti/ sono effimeri: rigenerarli col comando sopra.

## Limite di thread degli agenti (keywords: 25 thread, archive, create_agent, cannot spawn)
- Sessione 7: create_agent fallisce con "25 of 25 child threads are live" anche se quasi tutti sono IDLE (finiti): i thread finiti contano finché l'utente non li archivia (POST /v1/sessions/{id}/threads/{thread_id}/archive). Il coordinator non può archiviarli. Sessione 7: la console dell'utente mostra i thread con nomi leggibili (es. "Regulatory researcher", ripetuti), non con gli ID sthr_… di list_agents; sesn_… è l'ID della sessione intera. L'utente quindi non può archiviare un thread specifico dalla console. Soluzione pratica: aprire una sessione nuova (riparte da zero thread) e, nella sessione, riusare i thread IDLE invece di crearne di nuovi; tenere i lanci entro 25. Contromisura: riusare con send_to_agent i thread IDLE dello stesso tipo, dicendo esplicitamente che è un NUOVO INCARICO e quale file non toccare più; pianificare i lanci paralleli tenendo conto del limite.
