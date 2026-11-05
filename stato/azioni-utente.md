# Azioni dell'utente (keywords: piattaforma, configurazione, client, budget, da fare utente)

Cose che il coordinator non può fare. Origine: revisione della sessione 3 (2026-11-03). Il coordinator le ricorda all'avvio e toglie le voci fatte.

## Configurazione degli agenti sulla piattaforma (keywords: ricopiatura, drift, versioni)
- [X] Ricopiare i 9 agenti dai file `.claude/agents/*.md` del repo (commit `ff16450` o successivo): descrizione, prompt, modello, impegno, strumenti. Il pacchetto `/mnt/session/outputs/agenti/` della sessione 3 era effimero: se manca, il coordinator lo rigenera dai file del repo.
- [X] Togliere tutti gli strumenti custom `risposta_*`, compreso `risposta_coordinator`.
- [X] Strumenti per agente come da intestazione dei file. Da notare: `Write` ora anche per plan-auditor, compliance-auditor, code-reviewer e code-reader (scrivono il report); niente `Bash` per plan-auditor; `Edit`/`Write` per il Registrar (prima mancavano).
- [X] (2026-11-04, sessione 6) Ricopiare sulla piattaforma il solo prompt di doc-writer, plan-auditor e compliance-auditor (commit bdbcc43). Fatto: confermato dall'utente all'avvio della sessione 7.
- [ ] Valutare di gestire gli agenti da file con `ant beta:agents update` invece di incollarli a mano, per evitare copie disallineate (la revisione segnala il Coordinator alla versione 16 sulla piattaforma). Da verificare se il formato dei file `.claude/agents/` è accettato così com'è. Rinviata dall'utente (2026-11-04): è una chiamata API e oggi non usa le API; resta aperta, la riesaminerà più avanti. Non riproporla finché non lo chiede.

## Client e sessione (keywords: custom tool, watchdog, interrupt, budget, cache)
- Impegno del coordinator e cache persa nella sessione 3: FATTI dall'utente (già comunicato in una sessione precedente, non segnato per errore; tolti nella sessione 7). Non riproporli.
- [X] Non dare ai subagenti strumenti custom di risposta, a meno di avere un client che li gestisce: uno strumento custom lo esegue il client, che deve rispondere con `user.custom_tool_result` indicando `session_thread_id`. Senza client il thread resta in `requires_action` e blocca il turno (è la causa probabile del blocco della sessione 3, secondo la revisione).

## Ricopiature in sospeso (keywords: doc-writer, bash, strumenti)
- [X] (2026-11-04, sessione 7) doc-writer: togliere lo strumento Bash sulla piattaforma. FATTO: confermato dall'utente il 2026-11-05 (sessione 8). Non riproporre.

## Ricopiature in sospeso, sessione 8 (keywords: prompt, ricopiatura, piattaforma, memoria)
- [ ] (2026-11-05) Ricopiare sulla piattaforma il **prompt** di tutti e 9 gli agenti da `.claude/agents/*.md` (ultimo commit del branch `claude/docs-ondata-1`, README agenti 1.21): istruzioni su avvio e `stato/` solo in `CLAUDE.md`, il coordinator vi rimanda; nessun riferimento a `/mnt/memory/`. Descrizioni, modelli e strumenti invariati. Poi l'utente dà l'ok ed elimina la memoria della piattaforma (`/mnt/memory/gravya/`, che oggi contiene solo rimandi).
