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
- Decisioni M1-M5 dell'utente («ok», 2026-11-05): ultimo giro unico. Catalogo v1.7 fatto dal coordinator.
- **Implementer, giro 5** — task `docs/revisioni/impl-e1/task-implementer-giro5.md` (branch `claude/impl-e1`, commit 09b7162). Se interrotto: controllare i commit dopo 09b7162 e la sezione «Giro 5» del report; altrimenti rilanciare da quel task.
- **Doc-writer, E1 v1.9** — task `docs/revisioni/e1-v1.9/task-doc-writer.md` (branch `claude/docs-ondata-1`). Se interrotto: rilanciare; poi controllare le righe 1.0-1.8 dello Storico di E1.
- **Registrar** — esiti della revisione di E1 v1.8 e del giro 4 e decisioni M1-M5 (testo nel messaggio; se interrotto, ricostruirlo da questo file: «ok» ai punti 1 ultimo giro unico, 2 e1.write_connect_timeout_s minimo 2, 3 API_ENV fuori insieme blocca l'avvio, 4 chiave 32 byte invariante provvisoria, 5 nessun dato reale prima di DA-E1-13, segnali durevoli di A5 e procedura di installazione approvata).

## Prossimi passi, in ordine
1. Verificare giro 5, E1 v1.9 e il diff del registrar; commit.
2. Verifica mirata finale: code-reviewer sulle modifiche del giro 5; plan-auditor e compliance-auditor su E1 v1.9 e catalogo v1.7. Poi registrar.
3. Chiedere all'utente quando e dove unire `claude/impl-e1`.
4. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Nessuna decisione aperta.
