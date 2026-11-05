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
- E1 v1.8 **fatta** (doc-writer, Storico verificato intatto), commit su `claude/docs-ondata-1`.
- **Plan-auditor e compliance-auditor su E1 v1.8 e catalogo v1.6** — task `docs/revisioni/e1-v1.8/task-auditor.md`. Se interrotti: rilanciare da quel task (report attesi in `docs/revisioni/e1-v1.8/`). Plan-auditor concluso: RIPORTA (2 da riportare: E1 e catalogo §18 in contrasto sui formati/chiave minima come invarianti; API_ENV fuori insieme = scelta del coordinator senza riga decisa, da portare all'utente). Compliance-auditor concluso: RIPORTA (3 da riportare: connect_timeout non onorato sotto 2 s e troncato a secondi interi [verificato]; isolamento dipende da chi imposta app.tenant_id, ruolo di migrazione 'non deve essere usato a runtime'; §9 senza condizione che vieti dati reali prima di DA-E1-13, segnali durevoli A5, deploy approvato). Code-reviewer giro 4: RIPORTA (close() oltre timeout e worker che non si ferma; sink segnali senza timeout/riconnessione/rollback; connect_timeout <1 s = attesa infinita [verificato]; README non eseguibile altrove: migrazioni richiedono superuser, test con root fisso; minori: kind nel segnale, tipo di e1.write_tcp_user_timeout_ms, ruolo gravya_e1_pwtest lasciato). Report su impl. Presentate all'utente le decisioni M1-M5 (giro 5 + E1 v1.9 + catalogo v1.7; chiave 32 byte invariante provvisoria; API_ENV fuori insieme; connect timeout in secondi; condizione §9 prima dei dati reali): in attesa.
- Catalogo v1.6 fatto dal coordinator.

## Prossimi passi, in ordine
1. Esito del code-reviewer sul giro 4.
2. Esiti degli auditor su E1 v1.8, poi registrar. Contenuto chiesto alla v1.8: chiudere i rilievi della voce «Da riportare. Revisione di E1 v1.7 e catalogo v1.5» di DECISIONS §4 (report in `docs/revisioni/e1-v1.7/`), con DA-E1-13 in App. C, deroga C2, tenant di contesto, avvio bloccato, formati e chiave minima 32 byte nel catalogo §18, regola 11 per le variabili `e1.write_*`, valore di sviluppo di `e1.write_tcp_user_timeout_ms`. Poi plan-auditor e compliance-auditor, poi registrar.
3. Chiedere all'utente quando e dove unire `claude/impl-e1`.
4. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Nessuna decisione aperta.
