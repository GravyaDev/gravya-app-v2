# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 9, prima in Claude Code locale). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md`, `ambiente.md` (sezione «Claude Code locale»), `azioni-utente.md`.
2. **Branch:** `main` per documenti e codice; ogni implementer in un worktree `.worktrees/<nome>` sul branch `impl/<nome>`, cancellato dopo il merge (DECISIONS §6 «Branch di lavoro», comandi in `CLAUDE.md`). **Worktree aperti: nessuno.**
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md`.

## Stato (2026-11-05, sessione 9 in Claude Code locale)
- Ondata 1: E1 alla v1.10, gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- **E1 (passi 0, 2, 3) chiuso**: BLOCCA del giro 6 risolto dalla micro-correzione `API_ENV` (db41169, aa20e20). Residui in DECISIONS §4 «E1, residui del giro 6».
- **Versioni di runtime attuate**: Python 3.15 e PostgreSQL 18 con il merge 3bf8969 (worktree `e1-runtime`, chiuso); `code-reviewer` OK, `compliance-auditor` RIPORTA (punti in DECISIONS §4 «Catena di fornitura e aggiornamenti»); report in `docs/revisioni/e1-runtime/`. Verifica del coordinator su `main`: `tests/` 88 verdi 10 volte, `test-non-superuser.sh` riuscito, prove dei revisori con gli esiti del giro 6.
- Locale: `scripts/agenti.py` con task, lancio e worktree (immagine PostgreSQL dei worktree letta dalla CI); repository di riferimento bloccati in sola lettura (`ambiente.md`).

## Prossimi passi, in ordine
1. Decisioni dell'utente sui punti di §4 «Catena di fornitura e aggiornamenti» (sotto), poi implementer in un worktree, revisioni, merge.
2. Minori da applicare in E1 v1.11 e catalogo: rilievi minori dei report `docs/revisioni/e1-v1.9/` non ancora recepiti (precisazioni su `production_override`, guardiano che interrompe un job sano, protezione dei segnali per tenant contro l'inserimento diretto); rimandi nei documenti (A1 App. C e B1 §7 verso DECISIONS §6 e §5); residui di §4 «E1, residui del giro 6».
3. Poi: A1 (passi 3-4) sull'ossatura; allineamento degli altri documenti dell'ondata 1 (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Blocco di decisioni su DECISIONS §4 «Catena di fornitura e aggiornamenti» (a: scansione e aggiornamenti automatici; b: runner, client `psql`, action su Node 24; c: lockfile separati al deploy; d: limite superiore di `requires-python`), presentato a fine sessione 9 con raccomandazioni.
