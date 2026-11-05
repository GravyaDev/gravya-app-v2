# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 8). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md` (politica sui thread, file temporanei degli agenti, lezioni), `ambiente.md` (due ambienti), `azioni-utente.md`.
2. Branch dei documenti: `claude/docs-ondata-1`. Branch del codice di E1: `claude/impl-e1` (non unito; base `claude/docs-ondata-1`). Allineare entrambi al remoto prima di leggere.
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md` (v1.7).

## Stato
- Ondata 1: E1 alla v1.7 (2026-11-05), gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- Codice di E1, passi 0, 2, 3 del §9 su `claude/impl-e1`: tre giri di revisione; blocco tolto con il RIPORTA del terzo giro. Prove e report in `docs/revisioni/impl-e1/` (sul branch del codice).
- G2 (a) decisa: H2 e H3 da progettare in v2 da zero (dossier `docs/revisioni/dati-miglioramento/code-reader-meccanismo-v1.md`).
- Decisioni del 2026-11-05 su E1 v1.7 registrate (deroga C2 per l'ondata 1, DA-E1-13, tenant di contesto, avvio bloccato in produzione).

## In corso (agenti lanciati, non conclusi)
- Decisioni N1-N4 dell'utente («ok», 2026-11-05): API_ENV non impostata blocca; regola tcp ≥ statement confermata; giro 6 definitivo; dopo il giro 6 merge di `claude/impl-e1` in `claude/docs-ondata-1`. Catalogo v1.8 fatto dal coordinator.
- **Implementer, giro 6** — task `docs/revisioni/impl-e1/task-implementer-giro6.md` (branch `claude/impl-e1`, commit 0865f6e).
- **Doc-writer, E1 v1.10** — task `docs/revisioni/e1-v1.10/task-doc-writer.md`; controllare dopo le righe 1.0-1.9 dello Storico.
- **Registrar** (senza Bash) — task `docs/revisioni/e1-v1.10/task-registrar.md`.
Se interrotti: rilanciare dai task.

## Prossimi passi, in ordine
1. Verificare giro 6, E1 v1.10 e registrar; code-reviewer solo sui punti del giro 6 (task da scrivere); residui in DECISIONS §4.
2. Merge di `claude/impl-e1` in `claude/docs-ondata-1` (deciso).
3. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Ok dopo la ricopiatura dei prompt sulla piattaforma.
- Bash negato al registrar sulla piattaforma: voluto o da ripristinare?
