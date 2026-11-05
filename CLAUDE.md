# Gravya v2 — istruzioni per la sessione principale

Questo file lo legge Claude Code all'apertura del repository. Serve a continuare il lavoro in locale (abbonamento) esattamente come nelle sessioni sulla piattaforma.

1. **Ruolo.** In questa sessione sei il `coordinator`. Leggi per intero `.claude/agents/coordinator.md` (corpo del file, dopo l'intestazione) e seguilo come tue istruzioni: valgono tutte, comprese le sezioni «Avvio e chiusura di sessione» e «Ambiente: piattaforma o Claude Code locale».
2. **Avvio.** Leggi `stato/handoff-sessione.md`, poi `preferenze-e-lezioni.md`, `ambiente.md` e `azioni-utente.md` nella stessa cartella. Lavora sul branch indicato nel passaggio di consegne, allineato al remoto.
3. **Agenti.** Sono i file di `.claude/agents/` (catalogo e sequenze in `docs/agenti/README.md`). Si lanciano con lo strumento Task usando il nome del file come `subagent_type`. Il task si scrive prima in un file committato sotto `docs/revisioni/`, poi si passa all'agente con il suo template. Ogni lancio è autosufficiente: non esiste la prosecuzione di una conversazione con un agente.
4. **Fonti, in ordine di prevalenza:** `docs/PRINCIPI.md`, righe decise di `docs/DECISIONS.md`, documenti di dettaglio `docs/{ID}-{slug}.md` e `docs/index.md`, master plan e template in `docs/fonti/`.
5. **Registri.** `DECISIONS.md` e `index.md` li modifica solo l'agente `registrar`, con il testo dell'utente alla lettera.
6. **Chiusura di ogni turno che cambia lo stato:** commit, push, aggiornamento di `stato/handoff-sessione.md` (committato e pushato anch'esso).
7. **Lingua:** italiano. Nessuna stima temporale (solo taglie S/M/L). Nessun valore fisso nel codice (DX-22).
