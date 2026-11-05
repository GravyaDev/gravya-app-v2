# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 8). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md` (politica sui thread, file temporanei degli agenti, lezioni), `ambiente.md` (due ambienti), `azioni-utente.md`.
2. Branch dei documenti: `claude/docs-ondata-1`. Branch del codice di E1: `claude/impl-e1` (non unito; base `claude/docs-ondata-1`). Allineare entrambi al remoto prima di leggere.
3. `docs/DECISIONS.md` §4 (voci «Da riportare» di E1 v1.6, giri 1-3, E1 v1.7) e §6 (righe del 2026-11-05), `docs/agenti/README.md`, `docs/catalogo-variabili.md` (v1.5).

## Stato
- Ondata 1: E1 alla v1.7 (2026-11-05), gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- Codice di E1, passi 0, 2, 3 del §9 su `claude/impl-e1`: tre giri di revisione; blocco tolto con il RIPORTA del terzo giro. Prove e report in `docs/revisioni/impl-e1/` (sul branch del codice).
- G2 (a) decisa: H2 e H3 da progettare in v2 da zero (dossier `docs/revisioni/dati-miglioramento/code-reader-meccanismo-v1.md`).
- Decisioni del 2026-11-05 su E1 v1.7 registrate (deroga C2 per l'ondata 1, DA-E1-13, tenant di contesto, avvio bloccato in produzione).

## In corso (agenti lanciati, non conclusi)
- Giro 4 dell'implementer **concluso**: `claude/impl-e1` a 8dfb1de (verificato: 69 test, prove giro 3 con N4/N10 attesi, script non superuser OK; README «Esecuzione locale» alla radice del branch).
- **Code-reviewer, verifica mirata del giro 4** — task `docs/revisioni/impl-e1/task-code-reviewer-giro4.md` (branch `claude/impl-e1`, commit 14a743e). Se interrotto: rilanciare da quel task (report atteso `report-code-reviewer-giro4.md`).
- **Doc-writer, E1 v1.8** — task `docs/revisioni/e1-v1.8/task-doc-writer.md` (branch `claude/docs-ondata-1`). Se interrotto: rilanciare da quel task; poi controllare che le righe 1.0-1.7 dello Storico di E1 siano intatte.
- Catalogo v1.6 fatto dal coordinator.

## Prossimi passi, in ordine
1. Esito del code-reviewer sul giro 4.
2. Verificare E1 v1.8 (doc-writer) con il catalogo v1.6 già fatto, poi plan-auditor e compliance-auditor, poi registrar. Contenuto richiesto: chiudere i rilievi della voce «Da riportare. Revisione di E1 v1.7 e catalogo v1.5» di DECISIONS §4 (report in `docs/revisioni/e1-v1.7/`), con DA-E1-13 in App. C, deroga C2, tenant di contesto, avvio bloccato, formati e chiave minima 32 byte nel catalogo §18, regola 11 per le variabili `e1.write_*`, valore di sviluppo di `e1.write_tcp_user_timeout_ms`. Poi plan-auditor e compliance-auditor, poi registrar.
4. Chiedere all'utente quando e dove unire `claude/impl-e1`.
5. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Nessuna decisione aperta.
