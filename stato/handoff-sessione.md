# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 9, prima in Claude Code locale). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md`, `ambiente.md` (sezione «Claude Code locale»), `azioni-utente.md`.
2. **Branch:** `main` per documenti e codice; ogni implementer in un worktree `.worktrees/<nome>` sul branch `impl/<nome>`, cancellato dopo il merge (DECISIONS §6 «Branch di lavoro», comandi in `CLAUDE.md`). **Worktree aperti: nessuno.**
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md`.

## Stato (2026-11-05, fine sessione 9 in Claude Code locale)
- Ondata 1: E1 alla v1.10, gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- **E1 (passi 0, 2, 3) chiuso** (micro-correzione `API_ENV`, db41169, aa20e20). Residui in DECISIONS §4 «E1, residui del giro 6».
- **Runtime**: Python 3.15 e PostgreSQL 18 (merge 3bf8969).
- **Catena di fornitura della CI** (merge 46659bd): controllo OSV a ogni push e ogni settimana (`scripts/osv-check.py`, workflow «Catena di fornitura»), controllo settimanale del digest di PostgreSQL, Dependabot per le action, runner `ubuntu-24.04`, action su Node 24 fissate per SHA, `psql` dall'immagine dei servizi. Code-reviewer BLOCCA ai giri 1 e 2 (test che non proteggevano il fail-closed), corretti, OK al giro 3; compliance-auditor RIPORTA. Punti aperti in DECISIONS §4 «Catena di fornitura e aggiornamenti». Ultimo commit di lavoro: 46659bd; `tests/` 123 verdi.
- Locale: `scripts/agenti.py` con task, lancio e worktree; repository di riferimento in sola lettura (`ambiente.md`).

## Prossimi passi, in ordine
1. Decisioni dell'utente su §4 «Catena di fornitura e aggiornamenti» (sotto); poi, se serve codice, implementer in un worktree.
2. **Nuova fase, sessione nuova:** A1 passi 3-4 sull'ossatura (implementer in worktree, poi code-reviewer e compliance-auditor).
3. Alla prossima revisione di A1: App. C r.251 cita «DECISIONS §4» per «Mutazioni del grafo», ora in §6 (plan-auditor E1 v1.9, F4). Gli altri minori di E1 indicati nella sessione 8 sono già nella v1.10.
4. Poi: allineamento degli altri documenti dell'ondata 1 (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6). Da guardare con il plan-auditor: `security.vulnerability_scan_interval_days` del catalogo (piattaforma, A5/A6) e la cadenza settimanale della CI.

## In attesa di risposta dall'utente
- Blocco di decisioni su §4 «Catena di fornitura e aggiornamenti» (a: aggiornamento dei pacchetti Python; b: destinatario degli avvisi e controllo obbligatorio; c: eccezioni; e: runner come rischio accettato; d, f: minori), presentato a fine sessione 9.
