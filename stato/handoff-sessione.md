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
- **Ristrutturazione di DECISIONS.md** (utente: «Ok per le decisioni»: archivio separato, la fa il coordinator su copia con verifica del plan-auditor, subito). Candidato e archivio in `docs/revisioni/decisions-ristrutturazione/`; primo controllo del plan-auditor: BLOCCA (2 decisioni omesse: mutazioni del grafo A1, G1 (a)); candidato corretto (commit 3ab3998), seconda verifica in corso (report atteso `report-plan-auditor-2.md`). Dopo lo scambio: aggiornare nei documenti i rimandi a vecchi titoli di §4 (E1 §3 e A1 App. C sulle mutazioni del grafo, ora §6; B1 sulla base giuridica). Dopo: registrar sostituisce `docs/DECISIONS.md` e crea `docs/decisioni-archivio.md`, registra la decisione e la frase dell'utente sulla memoria; aggiornare il prompt del registrar con la regola «solo correnti, superate in archivio».
- Decisioni M1-M5 dell'utente («ok», 2026-11-05): ultimo giro unico. Catalogo v1.7 fatto dal coordinator.
- **Implementer, giro 5** — task `docs/revisioni/impl-e1/task-implementer-giro5.md` (branch `claude/impl-e1`, commit 09b7162). Se interrotto: controllare i commit dopo 09b7162 e la sezione «Giro 5» del report; altrimenti rilanciare da quel task.
- E1 v1.9 fatta (doc-writer, Storico verificato intatto) e committata.
- Registrar concluso: decisioni M1-M5 ed esiti registrati, commit 1ecfe11.

## Prossimi passi, in ordine
1. Verificare il giro 5; commit.
2. Verifica mirata finale: code-reviewer sulle modifiche del giro 5; plan-auditor e compliance-auditor su E1 v1.9 e catalogo v1.7. Poi registrar.
3. Chiedere all'utente quando e dove unire `claude/impl-e1`.
4. Poi: A1 (passi 3-4) sull'ossatura; v1.7 di allineamento degli altri documenti (F2, `run_id` UUID, `gravya.tool.outcome` in B2, C3 con F4); approvazione dei sette documenti; ondata 2 (A5, A6, F6).

## Da passare al registrar alla prossima invocazione
- Testo dell'utente alla lettera (2026-11-05): «Dopo aver ricopiato ti do ok ed elimino la memoria. Istruzioni solo in Claude.md, nessun'altra sessione avrà istruzioni sull'uso della memoria» (regola di processo, DECISIONS §6; applicata nel commit ef40b12).

## In attesa di risposta dall'utente
- Ok dopo la ricopiatura dei prompt sulla piattaforma.
