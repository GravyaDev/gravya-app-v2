# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 9, prima in Claude Code locale). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md`, `ambiente.md` (sezione «Claude Code locale»), `azioni-utente.md`.
2. **Un solo branch di lavoro: `main`** (documenti e codice; `claude/docs-ondata-1` unito con la PR #1). Non creare altri branch: anche l'implementer lavora qui.
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md`.

## Stato (2026-11-05, sessione 9 in Claude Code locale)
- Ondata 1: E1 alla v1.10, gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- Codice di E1 (passi 0, 2, 3) su `main`. **Micro-correzione `API_ENV` fatta** (decisione dell'utente «(a, micro-correzione)»): commit db41169 (codice, test, README) e aa20e20 (`API_ENV` nella CI, arresto di `scripts/test-non-superuser.sh` se manca); task e risposte in `docs/revisioni/impl-e1-chiusura/`. Verifica del coordinator: `tests/` 88 verdi 10 volte su Python 3.15 e PostgreSQL 18; prove dei revisori e `test-non-superuser.sh` **non ancora rieseguiti** in locale (mancano il collegamento `/workspace/wt-impl-e1` e `psql`: `azioni-utente.md`).
- Versioni di runtime decise (DECISIONS §6): Python 3.15 e PostgreSQL 18. L'ambiente locale è già su queste; lockfile, CI e README ancora su Python 3.11 e PostgreSQL 16.
- Locale: script `scripts/agenti.py` (uso in `CLAUDE.md`); repository di riferimento bloccati in sola lettura (`ambiente.md`).

## Prossimi passi, in ordine
1. Quando l'utente ha fatto le azioni di `azioni-utente.md`: prove dei revisori (comandi nel `README.md`, sezione «Prove dei revisori», con le variabili di `ambiente.md`) con gli stessi esiti del giro 6 (`docs/revisioni/impl-e1/code-reviewer-giro6/runs.txt`), più `scripts/test-non-superuser.sh`.
2. Registrar: §4 di DECISIONS, il punto «E1, chiusura definitiva (giro 6)» si chiude con il BLOCCA del giro 6 risolto dalla micro-correzione (report `docs/revisioni/impl-e1/report-code-reviewer-giro6.md`; commit db41169, aa20e20); minori residui del giro 6 (scrittura in volo dopo `close()` con coda profonda; default di `DATABASE_URL` nel README diversi da quelli dei test) come punti aperti in §4.
3. Implementer: aggiornamento a Python 3.15 e PostgreSQL 18 (lockfile con hash rigenerato, CI con immagine fissata per digest, README), poi `code-reviewer` e `compliance-auditor` (DECISIONS §6 «Versioni di runtime»).
4. Minori da applicare in E1 v1.11 e catalogo: rilievi minori dei report `docs/revisioni/e1-v1.9/` non ancora recepiti (precisazioni su `production_override`, guardiano che interrompe un job sano, protezione dei segnali per tenant contro l'inserimento diretto); rimandi nei documenti (A1 App. C e B1 §7 verso DECISIONS §6 e §5).
5. Poi: A1 (passi 3-4) sull'ossatura; allineamento degli altri documenti dell'ondata 1 (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Branch e worktree per l'implementer: proposta del coordinator (worktree in `.worktrees/<task>` su branch `impl/<task>`, `.venv` e PostgreSQL in Docker propri su porta diversa, comando di chiusura che cancella worktree, branch locale e remoto e container solo dopo il merge, elenco di quelli aperti nell'handoff). Se approvata: registrar (cambia DECISIONS §6 «Branch di lavoro») e script.
