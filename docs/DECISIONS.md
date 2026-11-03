# Registro delle decisioni aperte

Ultimo aggiornamento: 2026-11-03, ondata 1.

Ogni decisione aperta nasce in un documento di dettaglio, nell'Appendice C, ed è numerata `DA-{ID}-NN`. Qui sono raccolte in un unico punto. Quando una decisione viene presa, si compilano le colonne **Scelta**, **Motivo** e **Data**, e si aggiorna il documento di origine con una nuova riga nello Storico modifiche.

Stati possibili:
- **Aperta**: manca la scelta.
- **Escalation**: senza una decisione di business (Daniele) non si procede.
- **Decisa**: la scelta è stata fatta.

---

## 1. Decisioni trasversali, da prendere per prime

Queste decisioni non sono in nessun singolo documento. Ricorrono in più documenti, e a volte i documenti si contraddicono tra loro. La revisione di coerenza le ha raccolte (`revisione-ondata-1.md`). Sono numerate `DX-NN`. Finché non sono prese, molte DA dei singoli documenti restano bloccate.

| ID | Questione | Documenti coinvolti | Stato | Scelta | Motivo | Data |
|---|---|---|---|---|---|---|
| DX-01 | **Rapporto tra gravya-app-v2, gravya-app e la Beta del 30/11/2026.** Bisogna capire se v2 è una riscrittura indipendente, un'evoluzione di gravya-app o un lavoro da fare dopo la Beta. Kloudify non menziona mai v2. B2 raccomanda un gateway nuovo (DA-B2-01), C3 raccomanda di portare i moduli esistenti (DA-C3-01). | A1, B2, C1, C3, E2, E3 (DA-A1-05, DA-B2-01, DA-C1-04, DA-C3-01, DA-E2-05, DA-E3-06) | Escalation | | | |
| DX-02 | **Aderenza al master plan o al codice esistente.** Il master prevede OTel, un graph DB, OPA, LangGraph come motore unico e runtime effimeri. Il codice ha la Timeline DB-native ("NO OpenTelemetry", scelta confermata da Daniele), tabelle PostgreSQL con RLS, un enforcer Python e due motori (Node β e LangGraph). | E1, A1, A3, C1, B1 | Escalation | | | |
| DX-03 | **Trasporto eventi** (Redis Stream, Redis pub/sub o pg NOTIFY). Coincide con DA-A1-03. | A1, B1, B2, C1, C3, E2 | Aperta | | | |
| DX-04 | **Formato dei contratti condivisi tra Node e Python** (JSON Schema, Zod o Pydantic). Coincide con DA-C3-03. | C3, B2, A3, C1 | Aperta | | | |
| DX-05 | **Chi parcheggia la chiamata da approvare e chi chiama `interrupt()`.** Per A3 e B2 è B2, con l'esito `require_approval` della policy. Per C3 e per il codice attuale è il run/esecutore. C1 modella l'HITL come nodo esplicito. | A3, B2, C1, C3 | Aperta | | | |
| DX-06 | **Topologia dell'enforcement**: sidecar, libreria o servizio. DA-A3-02 e DA-B2-02 vanno decise insieme. | A3, B2, B1 | Aperta | | | |
| DX-07 | **Convenzione dei nomi** per eventi e tenant. Gli eventi usano nomi puntati (`tool.*`) o underscore (`hitl_*`); il tenant si chiama `tenant_id` o `company_id`. | Tutti | Aperta | | | |
| DX-08 | **Dipendenze critiche che stanno nell'ondata 2**. B5 (checkpointer) serve a C1, C3 e B1; A2 (compilatore) serve ad A3. Le alternative sono anticiparli all'ondata 1 o accettare per lo skeleton il checkpointer esistente e un bundle fixture. | B1, C1, C3, A3 | Aperta | | | |

---

## 2. Decisioni per documento

| ID | Titolo | Raccomandazione del documento | Stato |
|---|---|---|---|
| DA-E1-01 | OpenTelemetry o Timeline DB-native | B: OTel per il tracing, Timeline come audit, correlati da `trace_id` | Aperta (vedi DX-02) |
| DA-E1-02 | Cattura dei contenuti di prompt e risposte | Solo fuori dalla produzione finché l'issue #1925 non è chiusa | Aperta |
| DA-E1-03 | Backend delle tracce | Scegliere dopo DA-E1-01 | Aperta |
| DA-E1-04 | Come rappresentare retrieval e decisioni | Span custom `gravya.*` | Aperta |
| DA-E2-01 | Modello dati del registry | Nuove tabelle `prompts`/`prompt_versions`, con migrazione dello storico della 0322 | Aperta |
| DA-E2-02 | Motore di template | Sostituzione `{{var}}` senza logica, in TS e Python | Aperta |
| DA-E2-03 | Quali prompt migrare | Supervisori, esecutori e Kloud; preambolo P11 escluso | Aperta |
| DA-E2-04 | Condizione per promuovere una versione | E3 più approvazione umana tramite C3 | Aperta |
| DA-E2-05 | Anticipare il versioning rispetto alla Beta | Nessuna: decide l'utente | Escalation (DX-01) |
| DA-E3-01 | Primo bersaglio del dataset | Prima gli scenari Kloud esistenti, poi il workflow C1 | Aperta |
| DA-E3-02 | Linguaggio e posizione del runner | TS in `server/scripts` | Aperta |
| DA-E3-03 | Controlli soggettivi in CI | Nel gate solo controlli deterministici; giudice LLM come segnale non bloccante | Aperta |
| DA-E3-04 | Date relative (R1) | Nuovo seed a ogni run | Aperta |
| DA-E3-05 | Non determinismo del modello | 1 run per iniziare | Aperta |
| DA-E3-06 | Collocazione rispetto alla Beta | Escalation | Escalation (DX-01) |
| DA-E3-07 | Soglia del gate | 100% sui casi bloccanti, solo report sugli altri | Aperta |
| DA-A1-01 | Backend del grafo | PostgreSQL+RLS per l'ondata 1, con schema migrabile a Neo4j (diverge dal master) | Aperta (vedi DX-02) |
| DA-A1-02 | Fonte di verità dei mandati | Proiezione se v2 riusa gravya-app, altrimenti solo v2 | Aperta (vedi DX-01) |
| DA-A1-03 | Trasporto eventi | Redis Stream | Aperta (= DX-03) |
| DA-A1-04 | Allowlist dei tool nel grafo | Rinviata a B2 (vedi DA-B2-05) | Aperta |
| DA-A1-05 | Rapporto con gravya-app e con la Beta | Decide l'utente | Escalation (= DX-01) |
| DA-A1-06 | Isolamento | Istanza condivisa, con l'istanza dedicata come opzione | Aperta |
| DA-A3-01 | Motore di policy | Enforcer Python esteso in ondata 1, poi OPA | Aperta (vedi DX-02) |
| DA-A3-02 | Topologia | Sidecar se si sceglie OPA, altrimenti libreria | Aperta (vedi DX-06) |
| DA-A3-03 | Granularità del bundle | Un bundle per tenant | Aperta |
| DA-A3-04 | Stato dinamico (spesa, token) | Passato da B2 nell'input | Aperta |
| DA-A3-05 | Destino di `_scope_enforcement.py` | Diventa un adattatore verso A3, con test di parità | Aperta |
| DA-B1-01 | Unità di isolamento | Un ambiente per job | Aperta |
| DA-B1-02 | Container o VM | Container con l'hardening attuale per lo skeleton | Aperta |
| DA-B1-03 | Launcher e trasporto | Launcher dedicato chiamato da arq | Aperta |
| DA-B1-04 | Rete laterale e DNS | Uscita solo verso B2 ed egress-proxy, niente accesso diretto al db | Aperta |
| DA-B1-05 | Telemetria del job | Segue E1 | Aperta (dipende da DA-E1-01) |
| DA-B2-01 | Base di partenza del gateway | Gateway nuovo in v2, con il codice esistente come riferimento | Aperta (vedi DX-01) |
| DA-B2-02 | Forma del confine | Servizio HTTP separato | Aperta (vedi DX-06) |
| DA-B2-03 | Archivio dei contatori di rate limit | Redis | Aperta |
| DA-B2-04 | Audit fail-open o fail-closed | Fail-closed solo per scritture e `money_write` finché A5 non esiste | Aperta |
| DA-B2-05 | Origine dell'allowlist dei tool | Nessuna; da decidere con DA-A1-02 | Aperta |
| DA-C1-01 | Quale motore esegue i workflow | LangGraph riusando lo schema di β (va contro il piano registrato) | Escalation (vedi DX-02) |
| DA-C1-02 | Grafo Kloud e supervisore: dato o codice | Restano nel codice in ondata 1 | Aperta |
| DA-C1-03 | Linguaggio delle condizioni sugli edge | JSON dichiarativo | Aperta |
| DA-C1-04 | Quando farlo rispetto alla Beta | Decide Daniele | Escalation (DX-01) |
| DA-C3-01 | Riuso dei moduli HITL in v2 | Portare i moduli esistenti (in contrasto con DA-B2-01) | Aperta (vedi DX-01) |
| DA-C3-02 | Dove vive il nodo HITL | Solo LangGraph in ondata 1 | Aperta (dipende da DA-C1-01) |
| DA-C3-03 | Fonte del contratto condiviso | JSON Schema neutro | Aperta (= DX-04) |
| DA-C3-04 | TTL delle richieste HITL | 24 h fisse in ondata 1 | Aperta |
