# Gravya v2 — istruzioni di sessione

Questo file è l'unica fonte delle istruzioni su avvio, cartella `stato/` e chiusura dei turni. Lo legge Claude Code all'apertura del repository; sulla piattaforma il prompt del `coordinator` rimanda qui. Vale identico in locale (abbonamento) e sulla piattaforma (API).

## Ruolo
In Claude Code locale la sessione principale è il `coordinator`: leggi per intero `.claude/agents/coordinator.md` (corpo del file, dopo l'intestazione) e seguilo come tue istruzioni. Sulla piattaforma lo stesso testo è già il prompt della sessione.

## Avvio
1. `git fetch` e porta allineato al remoto il branch indicato in `stato/handoff-sessione.md` (oggi `claude/docs-ondata-1`; se il file non c'è, chiedi all'utente quale branch).
2. Leggi `stato/handoff-sessione.md`, poi `stato/preferenze-e-lezioni.md`, `stato/ambiente.md` e `stato/azioni-utente.md`. Se mancano, dillo all'utente.
3. Ricorda all'utente le voci aperte di `stato/azioni-utente.md`; nel dubbio su una voce, chiedi se è ancora aperta invece di ripresentarla come da fare.
4. Riprendi dagli agenti «in corso» del passaggio di consegne: controlla sui branch se il loro lavoro è arrivato; se no, rilanciali dal file del task indicato.

## Agenti
Sono i file di `.claude/agents/` (catalogo e sequenze in `docs/agenti/README.md`).
- **Locale:** strumento Task con `subagent_type` = nome del file. Ogni lancio è autosufficiente: un seguito è un nuovo lancio che cita il task precedente e i file prodotti. I subagenti non lanciano altri agenti.
- **Piattaforma:** `create_agent` e `send_to_agent` (riusare i thread inattivi dello stesso tipo; limite di thread in `stato/ambiente.md`).
- **In entrambi:** il task si scrive prima in un file committato sotto `docs/revisioni/`, poi si passa all'agente con il template della sua descrizione. Percorsi relativi alla radice del repository.

## Cartella `stato/` (stato di lavoro e memoria tra sessioni)
Sta nel repository ed è committata e pushata insieme al lavoro: è l'unica memoria tra sessioni e tra ambienti. Contiene solo ciò che i documenti di progetto non contengono. Quattro file, nient'altro:
- `handoff-sessione.md`: stato del lavoro, agenti lanciati e non conclusi con il file del task da cui rilanciarli, decisioni in attesa (solo ID e domanda), prossimi passi. Si **riscrive**, non si accoda.
- `preferenze-e-lezioni.md`: vincoli e preferenze dell'utente sul modo di lavorare, errori da non ripetere, risultati negativi.
- `ambiente.md`: accesso ai repository, comportamenti degli ambienti e degli strumenti, posizione delle cose.
- `azioni-utente.md`: cose che solo l'utente può fare. Appena l'utente dice che un'azione è fatta, si aggiorna nello stesso turno.

Regole:
- Mai copiare decisioni o contenuti dei documenti: si scrive il rimando (`DECISIONS.md` DX-22, `docs/C3-punto-hitl.md` §12).
- Niente percorsi effimeri (`/tmp`, identificativi di thread o di esecuzioni) senza la marcatura «effimero»: in un altro ambiente non esistono.
- Una nota superata si corregge o si toglie subito; a fine sessione si rileggono i file e si toglie ciò che non vale più.
- Formato: sezioni `## Argomento (keywords: …)`. Mai segreti o credenziali.
- Solo il `coordinator` scrive in `stato/`.

## Chiusura di ogni turno che cambia lo stato
Commit e push del lavoro; aggiornamento di `stato/handoff-sessione.md` (stato, ultimo commit di lavoro pushato, agenti in corso con il loro task, decisioni in attesa, prossimi passi), committato e pushato subito. La sessione può interrompersi in qualunque momento: ciò che non è nel repository pushato è perso. A un cambio di fase si propone all'utente una sessione nuova.

## Promemoria
Fonti in ordine di prevalenza: `docs/PRINCIPI.md`, righe decise di `docs/DECISIONS.md`, documenti di dettaglio e `docs/index.md`, `docs/fonti/`. `DECISIONS.md` e `index.md` li modifica solo il `registrar`, con il testo dell'utente alla lettera. Italiano; nessuna stima temporale (taglie S/M/L); nessun valore fisso nel codice (DX-22).
