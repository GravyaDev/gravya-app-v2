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
- Ristrutturazione di DECISIONS.md **conclusa**: registro solo corrente, storia in `docs/decisioni-archivio.md`. Da fare nelle revisioni dei documenti: rimandi a vecchi titoli di §4 (E1 §3 e A1 App. C sulle mutazioni del grafo, ora §6; B1 sulla base giuridica delle evidenze, ora §5).
- Decisioni M1-M5 dell'utente («ok», 2026-11-05): ultimo giro unico. Catalogo v1.7 fatto dal coordinator.
- Giro 5 dell'implementer **concluso**: `claude/impl-e1` a 41607af (verificato: 80 test; falliti attesi dichiarati, refuso confermato nel conftest del code-reviewer giro 4 r.74).
- **Verifica finale** in corso: code-reviewer (task `docs/revisioni/impl-e1/task-code-reviewer-giro5.md` sul branch del codice), plan-auditor e compliance-auditor su E1 v1.9 e catalogo v1.7 (task `docs/revisioni/e1-v1.9/task-auditor.md`). Se interrotti: rilanciare dai task. Compliance-auditor concluso: RIPORTA, solo 5 minori (report in `docs/revisioni/e1-v1.9/`, da committare).
- E1 v1.9 fatta (doc-writer, Storico verificato intatto) e committata.
- Registrar concluso: decisioni M1-M5 ed esiti registrati, commit 1ecfe11.

## Prossimi passi, in ordine
1. Esiti della verifica finale, poi registrar.
2. Chiedere all'utente quando e dove unire `claude/impl-e1`.
3. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## In attesa di risposta dall'utente
- Ok dopo la ricopiatura dei prompt sulla piattaforma.
- Bash negato al registrar sulla piattaforma: voluto o da ripristinare?
