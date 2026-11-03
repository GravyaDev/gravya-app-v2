Per progettare da zero una piattaforma di gestione per un'agenzia di marketing basata sull'AI, la scelta architetturale fondamentale non è "quale LLM usare", ma **come governare l'autonomia degli agenti**. La letteratura 2026 è concorde: il collo di bottiglia non è più la capacità del modello, ma l'affidabilità sotto composizione e la governance sotto autonomia. La piattaforma deve quindi nascere come un **sistema di orchestrazione e verifica**, non come un'applicazione con l'AI "aggiunta".

Ecco un piano completo, dall'architettura all'esploso dettagliato.

---

## 1. Principi guida: cosa distingue una piattaforma AI-native

Prima degli strumenti, i principi. Una piattaforma per agenti si progetta intorno a tre assi che un SaaS tradizionale non ha:

1. **L'osservabilità è la fondamenta, non un extra.** Senza tracing di ogni chiamata LLM, tool e punto di decisione, non puoi costruire valutazioni, esperimenti o guardrail. "Non puoi correggere ciò che non puoi vedere".
2. **La valutazione è parte del ciclo di sviluppo, non un test finale.** Un sistema agentico si sviluppa con *evaluation-driven development*: specifiche, harness di valutazione, osservabilità in produzione e metriche di costo-per-risultato.
3. **La governance è un layer architetturale, non una policy.** Autorizzazioni, mandati e tracciabilità devono vivere in un substrato esplicito (un grafo di coordinamento), non essere impliciti nel codice degli agenti.

---

## 2. Architettura di riferimento

Il pattern più solido emerso nel 2026 per ecosistemi multi-agente è il **Backbone Pattern**. L'idea centrale è separare tre cose che spesso vengono confuse:

- **Un grafo-substrato come "mappa canonica"**: un graph database che contiene *chi* è un agente, *quali mandati* ha, *come* è collegato agli altri, e *quali artefatti* produce. Non contiene i payload grandi (quelli stanno in object storage), ma solo i nodi-àncora che li referenziano.
- **Policy compilate all'edge**: le regole di autorizzazione vengono compilate dal grafo in piccoli ruleset veloci (es. OPA/Rego) e applicate *prima* che l'agente agisca, sul percorso caldo. Il grafo non viene interrogato a ogni richiesta.
- **Validazione a round-trip**: un processo continuo verifica che le regole compilate corrispondano ancora al grafo, perché la topologia degli agenti cambia.

Sopra questo substrato, l'architettura applicativa segue un modello **hub-and-spoke** per il multi-tenancy: un hub centrale (routing, autenticazione, controllo) e spoke isolati per ogni tenant/agenzia-cliente. L'isolamento non è basato su filtri `WHERE company_id = ?`, ma su **partizioni dati e compute separate per design**.

### Componenti macro dell'architettura

| Layer | Responsabilità | Tecnologia indicativa |
|---|---|---|
| **Control Plane** | Grafo di mandati, policy compilation, audit trail | Neo4j/Amazon Neptune + OPA |
| **Runtime Agenti** | Esecuzione di job agente in workspace effimeri | Container/VM isolati per tenant |
| **Orchestrazione** | Grafi di stato, checkpoint, HITL | LangGraph (durable execution) |
| **Tool Layer** | Accesso a CRM, ads, email, ecc. | MCP server + API gateway |
| **Memoria** | Breve termine (thread), lungo termine (vettoriale), episodica | Redis + pgvector/Qdrant |
| **Osservabilità** | Tracing, valutazione, guardrail telemetry | OpenTelemetry + piattaforma eval |
| **Dati applicativi** | Record CRM, campagne, report | PostgreSQL multi-tenant |

---

## 3. Stack tecnologico consigliato (2026)

### Framework di orchestrazione

La scelta del framework determina il modello mentale con cui pensi agli agenti.

- **LangGraph** è la scelta per agenti **stateful e durevoli**: grafo esplicito, checkpointing, time-travel debugging, human-in-the-loop nativo. È il più adatto se prevedi workflow lunghi (campagne che durano giorni) e devi poter riprendere dopo un'interruzione.
- **CrewAI** è più adatto a **pipeline role-based sequenziali** (ricercatore → copywriter → revisore), con minor complessità di sviluppo per team non esperti di graph modeling.
- **Microsoft Agent Framework** è il successore raccomandato di AutoGen e Semantic Kernel, con workflow tipizzati e forte integrazione Azure. AutoGen è in maintenance mode: da evitare per nuovi progetti.

**Raccomandazione:** LangGraph come orchestrazione principale, con la possibilità di invocare sub-workflow CrewAI per pipeline creative semplici. Non scegliere un framework per gli "stars" su GitHub, ma per la **debug story**: il tempo per riprodurre e correggere un fallimento in produzione è il vero costo.

### Osservabilità e valutazione

Non costruire su un solo vendor. Cerca framework compatibili con **OpenTelemetry GenAI semantic conventions**, così i punteggi di valutazione possono essere attaccati agli span e le decisioni di runtime non ti bloccano su un fornitore di eval.

Lo stack minimo:
- **Tracing**: ogni chiamata LLM (prompt, completion, token, costo), ogni tool invocation, ogni retrieval, ogni decision point.
- **Prompt management**: prompt esterni al codice, versionati, con templating e rollback.
- **Valutazioni continue**: eval non supervisionate sul traffico di produzione, binarie e specifiche (non "la risposta era buona?", ma "l'agente ha citato informazioni non nei documenti recuperati?").
- **Guardrail**: pre-LLM (input) e post-LLM (output), trattati come logica di esecuzione di prima classe, non come un afterthought.

### Dati e infrastruttura

- **PostgreSQL** per i dati applicativi (CRM, campagne, report), con RLS (Row-Level Security) *in aggiunta* all'isolamento architetturale, non al suo posto.
- **pgvector** per la memoria semantica a breve termine; **Qdrant** se la scala delle collezioni per-tenant lo richiede.
- **Redis** per stato di sessione e rate limiting.
- **Object storage** (S3/Garage) per gli artefatti grandi (brief, creatività, PDF), referenziati da nodi-àncora nel grafo.

---

## 4. Piano di implementazione a fasi

Il piano segue la logica del **thin-slice MVP**: non partire da una piattaforma completa, ma da **un singolo workflow ad alto volume e basso rischio** (es. triage di richieste interne, bozze di risposta email, summarization di thread), con data contract, eval gate e rollback definiti *prima* di scrivere codice.

### Fase 0 — Fondamenta (2–4 settimane)

L'obiettivo non è "fare AI", ma costruire il sistema nervoso che rende l'AI governabile.

**Componenti e sottoprodotti:**

- **0.1 Data contracts**
  - 0.1.1 Definizione input/output in linguaggio chiaro + esempi per il workflow scelto.
  - 0.1.2 Schema di validazione (Zod/Pydantic) enforced nel codice.
  - 0.1.3 Versione del contratto e politica di breaking change.

- **0.2 Osservabilità minima**
  - 0.2.1 Struttura di logging: `who/what/when` + input/output per ogni chiamata AI.
  - 0.2.2 Tracing distribuito (OpenTelemetry) con span per LLM call, tool, retrieval, decisione.
  - 0.2.3 Dashboard di costo per tenant e per workflow.

- **0.3 Eval harness**
  - 0.3.1 Golden dataset iniziale (10–30 casi) per il workflow.
  - 0.3.2 Eval binarie e specifiche (pass/fail), non su scala.
  - 0.3.3 Eval gate in CI: il deploy si blocca se la qualità scende sotto soglia.

- **0.4 Rollback e feature flag**
  - 0.4.1 "AI off switch" a livello di workflow, non di applicazione.
  - 0.4.2 Trigger di auto-disable pre-decisi (picco di errori, eval cattive, lamentele).

### Fase 1 — Thin-slice MVP (1–2 settimane)

Un solo workflow, end-to-end, in produzione limitata.

**Componenti e sottoprodotti:**

- **1.1 Agente singolo** (o crew minimale)
  - 1.1.1 Prompt esternalizzato e versionato.
  - 1.1.2 Tool access (es. lettura CRM, invio email) con autorizzazione a livello di policy.
  - 1.1.3 Memoria di thread (Redis) e checkpoint (LangGraph).

- **1.2 Human-in-the-loop**
  - 1.2.1 Punto di approvazione umana per azioni irreversibili (invio, modifica record).
  - 1.2.2 UI di revisione con contesto (input, output proposto, motivazione).

- **1.3 Metriche di successo**
  - 1.3.1 % di suggerimenti accettati.
  - 1.3.2 Tempo di completamento vs baseline.
  - 1.3.3 Tasso di escalation/override.

### Fase 2 — Hardening (2–4 settimane)

Si passa da "funziona" a "funziona in modo affidabile e ripetibile".

**Componenti e sottoprodotti:**

- **2.1 Valutazione su traffico live**
  - 2.1.1 Shadow mode: l'agente propone, l'umano decide, le differenze sono valutate.
  - 2.1.2 Rollout parziale (per tenant, per regione) con eval gate attive.
  - 2.1.3 Rituale di revisione giornaliera dei fallimenti (log review).

- **2.2 Guardrail di sicurezza**
  - 2.2.1 Pre-LLM: rilevamento PII, prompt injection, input non conformi.
  - 2.2.2 Post-LLM: verifica output (allucinazioni, tono, conformità al brand).
  - 2.2.3 Telemetria dei guardrail: ogni trigger, ogni blocco, ogni falso positivo.

- **2.3 Multi-tenancy**
  - 2.3.1 Partizione dati per tenant (schema separato o database separato a seconda della sensibilità).
  - 2.3.2 Isolamento compute: workspace effimeri per job agente.
  - 2.3.3 Key management per-tenant (BYOK opzionale).

### Fase 3 — Scala e governance (continuo)

**Componenti e sottoprodotti:**

- **3.1 Grafo dei mandati (Backbone)**
  - 3.1.1 Modello dati: agenti, mandati, domini, artefatti, deleghe.
  - 3.1.2 Compilazione policy → OPA/Rego.
  - 3.1.3 Validazione round-trip grafo ↔ policy compilate.

- **3.2 Catalogo agenti e tool**
  - 3.2.1 Registry di agenti con versione, prompt, tool abilitati.
  - 3.2.2 MCP server per l'accesso controllato a CRM, ads, email.
  - 3.2.3 Allowlist di tool per agente, con scope di autorizzazione.

- **3.3 Valutazione continua e regressioni**
  - 3.3.1 Suite di eval estesa a tutti i workflow critici.
  - 3.3.2 Regression test su prompt, RAG e cambi di modello.
  - 3.3.3 Metriche di costo-per-risultato per workflow e per tenant.

---

## 5. Verifica: come si misura che la piattaforma funziona

La verifica non è un test finale, ma un **ciclo continuo** con quattro livelli.

### Livello 1 — Eval offline (in CI)

- **Cosa**: golden dataset, eval binarie, regression suite.
- **Quando**: a ogni PR che cambia prompt, modello, tool o logica di orchestrazione.
- **Criterio**: il deploy si blocca se il pass rate scende sotto la soglia definita.

### Livello 2 — Eval online (in produzione)

- **Cosa**: eval non supervisionate sui trace di produzione, che valutano il comportamento usando il contesto dell'agente stesso (senza risposta "corretta" nota).
- **Quando**: continuamente, con alert su drift.
- **Criterio**: un calo statisticamente significativo attiva un rollback o un'indagine.

### Livello 3 — Revisione umana strutturata

- **Cosa**: campionamento dei trace per revisione umana, con rubric esplicite.
- **Quando**: rituale giornaliero o settimanale, a seconda del volume.
- **Criterio**: i fallimenti trovati diventano nuovi casi nel golden dataset (il dataset cresce dai fallimenti reali, non da esempi inventati).

### Livello 4 — Metriche di business e di costo

- **Cosa**: tempo risparmiato, conversione, CSAT, costo per output, costo per tenant.
- **Quando**: review settimanale.
- **Criterio**: la piattaforma è giustificata solo se il costo-per-risultato è inferiore al baseline umano per lo stesso workflow.

---

## 6. Esploso dettagliato (Work Breakdown Structure)

L'esploso seguente è organizzato per **componenti** e, per ciascuna, in **sottoprodotti** fino a unità di lavoro stimabili.

### Componente A — Control Plane (governance)

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| A1 | **Modello del grafo dei mandati** | Schema Neo4j: nodi `Agent`, `Mandate`, `Domain`, `Artifact`, `Delegation`; edge tipizzati |
| A2 | **Compilatore policy** | Servizio che traduce il grafo in bundle Rego/OPA, con versione e hash |
| A3 | **Runtime di enforcement** | Sidecar/OPA agent che valuta `allow/deny` prima di ogni azione dell'agente |
| A4 | **Validatore round-trip** | Job periodico che confronta policy compilate vs grafo, alert su drift |
| A5 | **Audit trail dei mandati** | Log append-only di ogni decisione di autorizzazione (chi, cosa, quando, perché) |

### Componente B — Runtime Agenti

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| B1 | **Agent runtime isolato** | Container/VM effimero per job, con filesystem temporaneo e rete limitata |
| B2 | **Tool gateway** | API gateway che espone solo i tool autorizzati per quell'agente, con rate limit e audit |
| B3 | **Memoria di thread** | Store Redis per stato conversazionale, con TTL e partizione per tenant |
| B4 | **Memoria a lungo termine** | Collezione vettoriale per tenant (pgvector/Qdrant), con politiche di retention |
| B5 | **Checkpoint e ripresa** | Persistenza dello stato del grafo (LangGraph checkpointer) per workflow lunghi |

### Componente C — Orchestrazione

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| C1 | **Grafo di workflow** | Definizione esplicita di nodi (agenti, tool, decisioni) ed edge condizionali |
| C2 | **Router di intent** | Nodo che classifica la richiesta e instrada al workflow corretto |
| C3 | **Punto HITL** | Nodo di approvazione umana con UI di revisione e payload di contesto |
| C4 | **Gestione errori e retry** | Politica di retry con backoff, dead-letter queue per fallimenti persistenti |
| C5 | **Timer e trigger** | Scheduler per workflow time-based (follow-up, report settimanali) |

### Componente D — Tool Layer (integrazioni marketing)

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| D1 | **CRM connector** | Tool per lettura/scrittura record (contatti, aziende, deal), con scope di autorizzazione |
| D2 | **Ads connector** | Tool per lettura metriche e scrittura campagne (Meta, Google), con HITL per scritture |
| D3 | **Email/messaging connector** | Tool per invio e lettura (SendGrid, Brevo, ecc.), con template e tracking |
| D4 | **Analytics connector** | Tool per query su dati di performance (GA4, piattaforme ads) |
| D5 | **MCP server unificato** | Esposizione dei tool via Model Context Protocol per compatibilità con l'ecosistema agenti |

### Componente E — Osservabilità e Valutazione

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| E1 | **Tracing distribuito** | Strumentazione OpenTelemetry con span per LLM, tool, retrieval, decisione |
| E2 | **Prompt registry** | Store versionato di prompt con templating, diff e rollback |
| E3 | **Eval harness offline** | Runner CI che esegue golden dataset e blocca il deploy su regressione |
| E4 | **Eval online** | Job che valuta trace di produzione con metriche binarie e alert su drift |
| E5 | **Guardrail telemetry** | Log di ogni trigger/blocco, con dashboard per falso positivo |
| E6 | **Dashboard costi** | Costo per tenant, per workflow, per modello, con breakdown token |

### Componente F — Dati e Multi-tenancy

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| F1 | **Schema applicativo** | Tabelle PostgreSQL per CRM, campagne, report, con `tenant_id` e RLS |
| F2 | **Partizione per tenant** | Politica di isolamento (schema separato o database separato) per tenant sensibili |
| F3 | **Key management** | Vault per chiavi di cifratura per-tenant, rotazione automatica |
| F4 | **Backup e restore** | Procedura di backup per tenant, con test di restore periodico |
| F5 | **Data residency** | Configurazione per mantenere i dati in regioni specifiche (EU/US) |

### Componente G — Interfaccia utente

| ID | Sottoprodotto | Output concreto |
|---|---|---|
| G1 | **Dashboard agenzia** | Vista aggregata per brand/cliente: stato campagne, metriche, alert |
| G2 | **Coda di revisione HITL** | Lista di task in attesa di approvazione, con contesto e azioni rapide |
| G3 | **Editor di workflow** | UI per comporre/modificare grafi di workflow (anche in fase avanzata) |
| G4 | **Registro agenti** | Catalogo di agenti disponibili, con stato, versione e tool abilitati |

---

## 7. Cosa evitare (lezioni dal campo)

- **Non costruire il grafo dei mandati come "database di tutto".** Il Backbone Pattern è esplicito: il grafo è la mappa, non il magazzino. I payload grandi vanno in object storage, referenziati da nodi-àncora.
- **Non rimandare l'osservabilità a "dopo la Beta".** Senza tracing non puoi fare eval, e senza eval non puoi concedere autonomia in modo sicuro. È il primo componente, non l'ultimo.
- **Non usare l'isolamento basato solo su filtri applicativi.** Per dati sensibili (GDPR, contratti, PII), l'isolamento deve essere architetturale: partizioni dati e compute separate per design.
- **Non pianificare per conteggio di feature.** Pianifica per **workflow end-to-end**, ciascuno con i suoi data contract, eval gate e rollback. Un workflow che funziona in produzione vale più di dieci prototipi.
- **Non scegliere il framework per popolarità.** LangGraph per stato durevole, CrewAI per pipeline role-based, Microsoft Agent Framework per l'ecosistema Azure. AutoGen è in maintenance: evitarlo per nuovi progetti.

---

## Sintesi

Una piattaforma di gestione per un'agenzia di marketing AI-native si costruisce come un **sistema di orchestrazione governata**, non come un'app con l'AI. L'ordine è: fondamenta di osservabilità e valutazione → thin-slice MVP su un workflow a basso rischio → hardening con guardrail e multi-tenancy → scala con grafo dei mandati e catalogo di agenti. Ogni fase produce sottoprodotti verificabili, e la verifica è continua (eval offline, eval online, revisione umana, metriche di business). Il costo maggiore non è il modello: è il sistema di governance e misurazione che rende il modello affidabile.