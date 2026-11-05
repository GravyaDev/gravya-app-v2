# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 9, prima in Claude Code locale). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md`, `ambiente.md` (sezione «Claude Code locale»), `azioni-utente.md`.
2. **Un solo branch di lavoro: `main`** (documenti e codice; `claude/docs-ondata-1` unito con la PR #1). Non creare altri branch: anche l'implementer lavora qui.
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md`.

## Stato (2026-11-05, sessione 9 in Claude Code locale)
- Ondata 1: E1 alla v1.10, gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- Codice di E1 (passi 0, 2, 3) nel branch unico (merge 9311762 di `claude/impl-e1`): 87 test verdi. Ultima verifica del code-reviewer (giro 6) **BLOCCA** su un solo punto: `API_ENV` non impostata non blocca se c'è `production_override` (`src/gravya_e1/tracing.py` riga 496).
- **Decisione dell'utente (2026-11-05, testo alla lettera): «(a, micro-correzione)».** Correzione dimostrata dal code-reviewer: togliere la condizione, impostare `API_ENV=development` nei test, aggiornare un test proprio. Nessun altro giro di revisione: verifica del coordinator rieseguendo le suite.
- DECISIONS.md ristrutturato (solo decisioni correnti, storia in `docs/decisioni-archivio.md`); catalogo v1.8.
- Sessione 9: passaggio a Claude Code locale. Script `scripts/agenti.py` (task dal template e lancio degli agenti, uso in `CLAUDE.md`); README degli agenti v1.23; `implementer` senza branch dedicato. Dipendenze Python: tutte all'ultima versione su PyPI salvo `pydantic` 2.14.2→2.14.3 e `pydantic-core` 2.50.2→2.50.4 (usciti il 2026-11-05), nessuna vulnerabilità nota su OSV (verifica del 2026-11-05).

## Prossimi passi, in ordine
0. Ambiente locale: server PostgreSQL per i test (versione da decidere, sotto) e `.venv/`.
1. Lanciare l'implementer con `python3 scripts/agenti.py lancia docs/revisioni/impl-e1-chiusura/task-implementer-micro-api-env.md`, su `main`.
2. Verificare: `tests/` 10 volte verde e prove dei revisori con gli stessi esiti del giro 6 (comandi nel `README.md` della radice; `PGDATABASE` per le prove dei giri 1-2; `API_ENV=development`).
3. Registrar (testo alla lettera sopra): §4 di DECISIONS, il punto «E1, chiusura definitiva (giro 6)» si chiude con il BLOCCA del giro 6 risolto dalla micro-correzione (report `docs/revisioni/impl-e1/report-code-reviewer-giro6.md`); minori residui del giro 6 (scrittura in volo dopo `close()` con coda profonda; default di `DATABASE_URL` nel README diversi da quelli dei test) come punti aperti in §4.
4. Minori da applicare in E1 v1.11 e catalogo: rilievi minori dei report `docs/revisioni/e1-v1.9/` non ancora recepiti (precisazioni su `production_override`, guardiano che interrompe un job sano, protezione dei segnali per tenant contro l'inserimento diretto); rimandi nei documenti (A1 App. C e B1 §7 verso DECISIONS §6 e §5).
5. Poi: A1 (passi 3-4) sull'ossatura; allineamento degli altri documenti dell'ondata 1 (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Versioni di runtime: Python 3.11 e PostgreSQL 16 venivano dal container della piattaforma, non da una decisione. Proposta: PostgreSQL 18 (in Docker) e Python 3.14, con aggiornamento di CI, README e lockfile tramite l'implementer.
- Ok dopo la ricopiatura dei prompt sulla piattaforma (se si torna sulla piattaforma).
