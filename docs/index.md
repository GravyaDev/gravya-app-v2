# Gravya v2: indice dei documenti di progetto

Fonti: "Piano generale" (master plan) e "Prompt e workflow" (template a 12 sezioni, ondate).
Stato del codice di riferimento: `gravya-app` al commit `349118b11` (2026-11-02) e `gravya-app-kloudify` al commit `e43f15e3` (2026-11-02).

## Documenti trasversali

| File | Contenuto |
|---|---|
| [DECISIONS.md](DECISIONS.md) | Registro delle decisioni aperte: 8 trasversali (DX) e 45 per documento (DA) |
| [revisione-ondata-1.md](revisione-ondata-1.md) | Revisione di coerenza dell'ondata 1: matrice delle dipendenze, correzioni fatte, problemi aperti |
| [stato/sviluppo.md](stato/sviluppo.md) | Ricognizione di `gravya-app`: stack, struttura, cosa esiste per ciascun tema |
| [stato/kloudify.md](stato/kloudify.md) | Ricognizione di `gravya-app-kloudify`: stato del progetto, regole Beta, priorità |

## Ondata 1: walking skeleton

Stato: **v1.1, in attesa di verifica dell'utente**.

| ID | Documento | Componente | Taglia | Decisioni aperte |
|---|---|---|---|---|
| E1 | [Tracing distribuito](E1-tracing-distribuito.md) | E: Osservabilità e Valutazione | M (L) | DA-E1-01…04 |
| E2 | [Prompt registry](E2-prompt-registry.md) | E: Osservabilità e Valutazione | M | DA-E2-01…05 |
| E3 | [Eval harness offline](E3-eval-harness-offline.md) | E: Osservabilità e Valutazione | M | DA-E3-01…07 |
| A1 | [Modello del grafo dei mandati](A1-grafo-mandati.md) | A: Control Plane | L (M) | DA-A1-01…06 |
| A3 | [Runtime di enforcement](A3-runtime-enforcement.md) | A: Control Plane | M (L) | DA-A3-01…05 |
| B1 | [Agent runtime isolato](B1-agent-runtime-isolato.md) | B: Runtime Agenti | L | DA-B1-01…05 |
| B2 | [Tool gateway](B2-tool-gateway.md) | B: Runtime Agenti | M (L) | DA-B2-01…05 |
| C1 | [Grafo di workflow](C1-grafo-workflow.md) | C: Orchestrazione | L | DA-C1-01…04 |
| C3 | [Punto HITL](C3-punto-hitl.md) | C: Orchestrazione | M | DA-C3-01…04 |

Tra parentesi la taglia alternativa, che dipende da una decisione aperta (vedi §12 di ciascun documento).

## Ondata 2: MVP completo (da redigere)

A2, A4, A5, B3, B4, B5, C2, C4, D1, G2

## Ondata 3: scala (da redigere)

C5, D2, D3, D4, D5, E4, E5, E6, F1, F2, F3, F4, F5, G1, G3, G4

## Convenzioni

- Nome dei file: `{ID}-{slug}.md`. Ogni documento ha le 12 sezioni del template, seguite dalle appendici A (allineamento con lo stato attuale), B (non verificato) e C (decisioni aperte) e dallo Storico modifiche.
- Nessuna stima temporale, solo la taglia S/M/L.
- Le soglie che non vengono dal master plan o dal codice sono marcate "proposta da validare".
- Se il master plan cambia, i documenti si aggiornano con una riga nello Storico modifiche, senza riscriverli da capo.
