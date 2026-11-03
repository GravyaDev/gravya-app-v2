# Collaudo degli agenti di governance — 2026-11-03

Risultati del collaudo eseguito in sandbox nella sessione 3. Gli agenti hanno lavorato su copie di `docs/` alla v1.4 dell'ondata 1. Nessun file del repository è stato modificato da questi test. L'esito del collaudo e le correzioni ai prompt che ne sono derivate sono in `docs/agenti/README.md`, Storico, righe 1.8 e 1.9.

| File | Agente | Cosa contiene | Come usarlo |
|---|---|---|---|
| `plan-auditor-C1-C3.md` | plan-auditor | Verifica di coerenza di C1 e C3 v1.4. Esito BLOCCA. | I rilievi sono reali: input per la v1.5 dell'ondata 1. |
| `compliance-auditor-C3-E1-v1.4.md` | compliance-auditor | Revisione di conformità di C3 ed E1 v1.4. Esito BLOCCA. | I rilievi sono reali: input per la v1.5 dell'ondata 1. |
| `review-C3-sweeper.md` | code-reviewer | Revisione di una PR finta: sweeper HITL con TTL scritto nel codice. Esito BLOCCA. | Esempio di revisione. Il codice esaminato non esiste nel repository. |
| `doc-writer-C3-v1.5.diff` | doc-writer | Bozza di aggiornamento di C3 per DA-C3-04 e DX-22, scritta in sandbox. | **Non applicata.** Contiene difetti noti: AC-12 in contrasto con DX-17, la ripartizione dei ruoli sul TTL scritta come decisa, metadati del collaudo dentro l'Appendice B. Usarla solo come confronto. |
| `registrar.diff` | registrar | Registrazione in sandbox di una decisione **di prova** su DA-E3-05. | **La decisione è fittizia: non applicarla.** Serve solo a mostrare il formato "Decisa con riserva" e la riga "Da riportare". |

Le sezioni "Collaudo" dentro i report contengono le autodichiarazioni degli agenti su modello e strumenti. Non sono verificate.
