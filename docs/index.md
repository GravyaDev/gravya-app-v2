# Gravya v2: indice dei documenti di progetto

Fonti: "Piano generale" (master plan) e "Prompt e workflow" (template a 12 sezioni, ondate).
Stato del codice di riferimento: `gravya-app` al commit `349118b11` (2026-11-02) e `gravya-app-kloudify` al commit `e43f15e3` (2026-11-02).

## Documenti trasversali

| File | Contenuto |
|---|---|
| [DECISIONS.md](DECISIONS.md) | Registro delle decisioni: 22 trasversali (DX) e 119 DA (per documento e del catalogo), incluse le 23 del catalogo (DA-CV-01…23, §7). Ultimo aggiornamento 2026-11-05 (esito BLOCCA del giro 2 di E1 v1.6, head bc32c72, registrato come «Bloccante (giro 2)» in §4; terzo giro di correzioni e valori provvisori in §6; esito BLOCCA di E1 v1.6 sulla PR `claude/impl-e1`, registrato come «Bloccante» in §4; giro di correzioni e vocabolari provvisori in §6; G2 a: H2 e H3 da progettare in v2 da zero; dossier G1 (b) prodotto); 2026-11-04 (blocco E1-E16 approvato, con le aggiunte E8 ed E15) |
| [catalogo-variabili.md](catalogo-variabili.md) | Catalogo delle variabili di piattaforma, v1.4 (2026-11-04, registro delle norme v1.6). Decisioni DA-CV-01…23 decise il 2026-11-04 (DA-CV-18…23 con «Ok» dell'utente); valori aperti per DA-CV-01 (valori min/max della retention) e DA-CV-08 (termine verso le agenzie), e le righe «Da riportare» di DECISIONS §4. Le variabili nuove dei documenti v1.6 sono in attesa di unione nel catalogo |
| [agenti/README.md](agenti/README.md) | Agenti (coordinator, registrar, regulatory-researcher, plan-auditor, code-reviewer, compliance-auditor, doc-writer, code-reader, implementer): prompt e regole di attivazione |
| [revisione-ondata-1.md](revisione-ondata-1.md) | Revisione di coerenza dell'ondata 1: matrice delle dipendenze, correzioni fatte, problemi aperti |
| [stato/sviluppo.md](stato/sviluppo.md) | Ricognizione di `gravya-app`: stack, struttura, cosa esiste per ciascun tema |
| [stato/kloudify.md](stato/kloudify.md) | Ricognizione di `gravya-app-kloudify`: stato del progetto, regole Beta, priorità |
| [norme-di-riferimento.md](norme-di-riferimento.md) | Registro delle norme di riferimento (GDPR, Codice privacy, NIS2, AI Act con Omnibus, CRA, Data Act, DSA) e lacune rispetto ai documenti: §9 |

## Ondata 1: walking skeleton

Stato: **tutti i documenti alla v1.6 (2026-11-04, decisioni fino a F1-F4)**. **E1 e A1 approvati dall'utente come base dell'implementazione** (opzione (a): F2 e F3 applicati nel codice; v1.7 di allineamento dei testi da fare). **A3, B1, B2, C1, C3, E2, E3 in attesa di approvazione dell'utente.** Principi vincolanti: [PRINCIPI.md](PRINCIPI.md).

| ID | Documento | Componente | Taglia | Decisioni aperte |
|---|---|---|---|---|
| E1 | [Tracing distribuito](E1-tracing-distribuito.md) | E: Osservabilità e Valutazione | M (L) | nessuna (DA-E1-03, 04, 07: ipotesi di lavoro decise il 2026-11-04) |
| E2 | [Prompt registry](E2-prompt-registry.md) | E: Osservabilità e Valutazione | M | DA-E2-01…03; DA-E2-04 (parte residua: approvazione C3 per le versioni umane) |
| E3 | [Eval harness offline](E3-eval-harness-offline.md) | E: Osservabilità e Valutazione | L | DA-E3-01, DA-E3-03…05 |
| A1 | [Modello del grafo dei mandati](A1-grafo-mandati.md) | A: Control Plane | L (M) | DA-A1-03…04 |
| A3 | [Runtime di enforcement](A3-runtime-enforcement.md) | A: Control Plane | M (L) | DA-A3-01…04 |
| B1 | [Agent runtime isolato](B1-agent-runtime-isolato.md) | B: Runtime Agenti | L | DA-B1-01…03 |
| B2 | [Tool gateway](B2-tool-gateway.md) | B: Runtime Agenti | M (L) | DA-B2-03, DA-B2-05 |
| C1 | [Grafo di workflow](C1-grafo-workflow.md) | C: Orchestrazione | L | DA-C1-03 |
| C3 | [Punto HITL](C3-punto-hitl.md) | C: Orchestrazione | L | nessuna |

Tra parentesi la taglia alternativa, che dipende da una decisione aperta (vedi §12 di ciascun documento).

## Ondata 2: MVP completo (da redigere)

A2, A4, A5 (con la notifica incidenti NIS2, DX-10), B3, B4, B5, C2, C4, D1, G2, **F6 Politica di retention e cancellazione** (nuovo, DX-12), **A6 Identità, ruoli e configurazione di piattaforma** (nuovo, DX-14)

## Ondata 3: scala (da redigere)

C5, D2, D3, D4, D5, E4, E5, E6, F1, F2, F3, F4, F5, G1, G3, G4

## Convenzioni

- Nome dei file: `{ID}-{slug}.md`. Ogni documento ha le 12 sezioni del template, seguite dalle appendici A (allineamento con lo stato attuale), B (non verificato) e C (decisioni aperte) e dallo Storico modifiche.
- Nessuna stima temporale, solo la taglia S/M/L.
- Le soglie che non vengono dal master plan o dal codice sono marcate "proposta da validare".
- Se il master plan cambia, i documenti si aggiornano con una riga nello Storico modifiche, senza riscriverli da capo.
