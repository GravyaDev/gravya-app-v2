# Ricognizione repo di sviluppo `gravya-app` (sola lettura)

Data: 2026-11-03. Ho fatto la ricognizione con ls, grep e la lettura delle intestazioni di alcuni file (le prime 10-40 righe). Non ho letto i file per intero.
Legenda: **[L]** = l'ho letto in un file (indico il percorso). **[D]** = è una mia deduzione oppure una lettura parziale, da verificare. Tutti i percorsi sono relativi a `/workspace/gravya-app`.

## 1. Stack reale

| Area | Cosa ho trovato | Fonte |
|---|---|---|
| Linguaggi | TypeScript (monorepo pnpm: `server`, `ui`, `packages/*`) e Python (`services/agents`, `services/pii-redactor`, `infra/agent-search`) | [L] `package.json`, `pnpm-workspace.yaml`, `services/agents/requirements.txt` |
| Backend app | Node con Express 5, zod 4, ajv, helmet, express-rate-limit, ws (realtime), pino (log), multer, nodemailer, web-push | [L] `server/package.json` |
| UI | Vite e React [D: React dedotto da `App.tsx`/`.tsx`], Lingui per l'i18n, shadcn [D da `components.json`], Playwright per gli e2e | [L] `ui/`, `package.json` scripts |
| ORM e DB | Drizzle ORM 0.45 con `postgres` (driver), `embedded-postgres` per sviluppo e test. In produzione gira l'immagine `pgvector/pgvector:pg17`. Le migrazioni SQL in `packages/db/src/migrations` sono 421 file | [L] `packages/db/package.json`, `docker/docker-compose.prod.yml` |
| Multi-tenancy | PostgreSQL RLS **già in uso e diffusa**: 603 occorrenze di "ROW LEVEL SECURITY" nelle migrazioni, uso di ENABLE + FORCE, GUC `gravya.actor_type`, `gravya.bypass_rls`, con company_id come chiave di tenant. Helper: `reserveScopedDb`, `withActorContext`, `withReadContext`, `withSystemContext({bypassRls, reason})`. Ci sono script CI di guardia (`check:rls-nullif`, `check:no-naked-bypass-rls`). C'è anche un resolver che privilegia le righe del tenant rispetto ai default globali (`company_id IS NULL`) | [L] `packages/db/src/migrations/0078_gravya_hsar_infrastructure.sql`, `server/src/services/approvals.ts`, `server/src/services/multitenant-resolver.ts`, `package.json` |
| "HSAR" | Infrastruttura di audit per grant e violazioni (`gravya_hsar_grant_uses`, `gravya_hsar_violations`). Alcune tabelle sono scrivibili solo da un actor `human` | [L] header di `grant-evaluator.ts`, `kloud-approval.ts` |
| Auth | better-auth 1.7.7, jose (JWT), otplib (2FA, con suite e2e dedicata). Lato Python: PyJWT, `utils/auth.py`, `utils/run_token.py` | [L] `server/package.json`, `requirements.txt`, ls `services/agents/src/utils` |
| Code / job | Redis 7 (in compose). Lato Node: ioredis (api-broker, pub/sub della cache LLM). Lato Python: **arq** (code async su Redis DB 1), con DLQ persistita in `gravya_job_dead_letters`. In più ci sono un `AutomationWorker` con poll scheduler basato su croniter e un `pg_listener` | [L] `requirements.txt`, `server/src/lib/redis.ts`, ls `services/agents/src/automation`, `job_queue` |
| Provider LLM | **LiteLLM 1.104.3** come gateway unico verso Anthropic, OpenAI, Gemini, Mistral e OpenRouter. Le integrazioni LangChain servono solo per i tipi dei messaggi. Le policy di modello per ruolo sono risolte lato server (`llm-role-policy-resolver.ts`, `llm-resolver-cache.ts`) e invalidate via Redis pub/sub. Per gli embedding si usa Jina via HTTP (`vector(1024)`). OCR e trascrizione passano da Mistral (Voxtral) | [L] `requirements.txt`, `packages/db/src/schema/gravya_memory_topic_tree.ts`, ls `server/src/services` |
| Agent / orchestrazione | **LangGraph 1.2.11** con `langgraph-checkpoint-postgres` e langchain 1.4. La gerarchia è "Kloud / Supervisor / Executor / Tool". Ci sono anche i "councils" (forme multi-persona) | [L] `requirements.txt`, `services/agents/src/kloud/graph.py`, `multitenant-resolver.ts` |
| API agenti | FastAPI con uvicorn e slowapi. I container sono `agents` (tool-runner) e `agents-worker` (arq) | [L] `requirements.txt`, `firewall-entrypoint.sh` |
| Vettori | **pgvector** dentro Postgres. Qdrant non è presente | [L] compose, grep `qdrant` (0 risultati) |
| Object storage | `@aws-sdk/client-s3` con provider `s3-provider.ts` e `local-disk-provider.ts`. La colonna `storage_tier` ammette `general`/`protected` e un commento cita la migrazione a **Garage** (#1218) | [L] `server/src/storage/`, `packages/db/src/schema/gravya_files.ts` |
| Osservabilità | Sentry SDK puntato a GlitchTip self-hosted, **solo per gli errori** (`enableOpenTelemetrySetup: false`). Log con pino. È presente una "Timeline Engine" DB-native su `gravya_event_logs`, con la dicitura esplicita "NO OpenTelemetry" (decisione attribuita a Daniele, 2026-06-15) | [L] `server/src/observability/error-tracking.ts`, `server/src/services/timeline-engine.ts` |
| Sicurezza egress | Un container `egress-proxy` fa da allowlist default-deny con firma HMAC. Il firewall iptables nei container agents imposta `OUTPUT DROP` e lascia passare solo i peer interni. Il redattore PII è un servizio separato (`services/pii-redactor`) | [L] `services/agents/firewall-entrypoint.sh`, `docker/`, `server/src/services/egress-*.ts` |
| Ricerca web | `infra/agent-search` (servizio vendorizzato) e SearXNG in compose | [L] ls `infra/agent-search`, compose |
| Deploy | Docker Compose (`docker/docker-compose.yml`, `docker-compose.prod.yml`) con i servizi redis, db, server, egress-proxy, agents, agents-worker, searxng, agent-search, pii-redactor. C'è un `Dockerfile` in root. La CI usa runner self-hosted (`infra/ci-runner-local`) e gli script di release sono in `scripts/` | [L] compose, ls. Kubernetes e cloud provider: **non trovati** |

## 2. Struttura del monorepo

- `server/` [L]: è il backend Express. In `server/src/services` ci sono più di 200 servizi: CRM, fatturazione (SDI/FatturaPA), booking, contratti, memoria, workflow, approvals, api-broker, egress e altri. `routes/` contiene 105 file. Le altre cartelle sono `auth/`, `middleware/`, `realtime/`, `storage/`, `observability/`, `secrets/` e `security/`.
- `ui/` [L]: è il frontend. Contiene pagine, componenti e `lib/hitl.ts` (lo schema Zod del contratto HITL; l'ho trovato citato, non letto).
- `packages/db` [L]: schema Drizzle, migrazioni, backup, `reserve-scoped-db`, `system-db`.
- `packages/shared` [L]: tipi e validatori condivisi tra server e ui, organizzati per dominio (crm, booking, ecc.).
- `services/agents` [L]: è il runtime AI in Python. Le sue sottocartelle:
  - `kloud/`: grafo LangGraph, router, checkpointer, HITL, fencing della memoria.
  - `supervisors/` ed `executors/`: classi base e generiche.
  - `councils/`.
  - `tools/`: crm, google, meta, web, documents, office, transcription, translator, plutio e altri, più i file `_audit.py` e `_scope_enforcement.py`.
  - `automation/`: 40 handler `c2_*`.
  - `job_queue/` (arq), `pipelines/` (memoria, entity extraction, text-to-SQL), `compliance/`, `egress/`, `benchmarks/`, `fatturapa/`, `pdf/`.
  - `api/`: router FastAPI, tra cui `runtime.py`, `internal.py`, `council.py`.
- `services/pii-redactor` [L ls]: servizio di redazione PII.
- `infra/agent-search` e `infra/ci-runner-local` [L ls].
- `doc/`, `docs/` (Mintlify), `report/`, `releases/`, `tests/` (e2e, ui-layout), `tools/eslint` [L ls; non ho letto il contenuto].

## 3. I 9 temi dell'ondata 1: cosa esiste già

### E1 Tracing distribuito
- Esiste [L] la Timeline Engine DB-native (`server/src/services/timeline-engine.ts`). Ricostruisce la sequenza degli eventi da `gravya_event_logs`, correlandoli per company_id, created_at, agent_id/session_id ed execution_ticket_id/run_id. Il commento dice che **non c'è un trace_id** su `llm.inference` (#264 "not landed"). La route di consultazione è `server/src/routes/superadmin-observability.ts` (citata, non letta).
- In `services/agents/src/councils/runtime.py` c'è un hook OpenTelemetry/Phoenix opzionale, rimasto TODO [L].
- `traceparent` e Langfuse: **non trovati**. Per LangSmith esiste solo la dipendenza transitiva [L]; [D] non risulta che sia usato.
- **Divergenza:** il codice ha scelto in modo esplicito di non usare OpenTelemetry.

### E2 Prompt registry
- Non ho trovato un registry dedicato (grep `prompt_registry`/`prompt_versions`: 0 risultati).
- Esiste [L] `gravya_supervisors.system_prompt`, una tabella in raw SQL senza Drizzle. Le sue revisioni stanno in `packages/db/src/schema/gravya_supervisor_prompt_revisions.ts` (RLS FORCE, migrazione 0322). Ci sono poi un loop di auto-miglioramento con approvazione umana (`services/agents/src/job_queue/prompt_improvement_job.py`, `server/src/services/learning-proposal-apply.ts`, `learning_proposals`) e `server/src/services/llm/prompt-hash.ts` (SHA-256 troncato a 16 caratteri).
- [D] Ci sono probabilmente altri prompt hard-coded nel codice Python. Non l'ho verificato.

### E3 Eval harness offline
- C'è solo un benchmark sulla memoria [L]: `services/agents/src/benchmarks/` (`golden_set.json`, `memory_recall.py` con Recall@k/Precision@k, `rerank_ab.py`) e l'handler `automation/handlers/c2_memory_benchmark.py`.
- C'è un "REPLAY" nel prompt_improvement_job [L], che ricalcola la classificazione con il prompt attuale e con quello candidato.
- Un harness generale di eval sugli agenti **non l'ho trovato**.

### A1 Grafo mandati
- Non ho trovato un database a grafo (grep neo4j: 0 risultati).
- Esistono [L] i capability grant in `principal_permission_grants` con `server/src/services/grant-evaluator.ts`. Il ciclo di vita copre revoca, valid_from/until e max_uses. Ci sono anche le condizioni DSL compilate (`server/src/services/grant-condition/{parse,compile,evaluate}.ts`), che falliscono chiuse se non valide.
- Altri file correlati, dove ho letto solo il nome: `collaborator-grants.ts`, `access.ts`, `board-auth.ts`, `tier-policy.ts`.
- [D] La delega è modellata in relazionale con RLS, non come grafo.

### A3 Runtime enforcement
- Esistono [L]:
  - `services/agents/src/tools/_scope_enforcement.py`: un enforcement in modalità enforce che solleva `ScopeViolation` e scrive l'audit `tool.scope.denied`. Il file dichiara che i councils **non** passano da questo punto di controllo.
  - `utils/capability_check.py`, `run_scope_contract.py`, `injection_detector.py`, `llm_guard.py` (ho letto solo i nomi).
  - `compliance/{engine,policy,validators}.py` (letto solo il nome).
  - Lato server: budget (`budgets.ts`), rate-limit (`llm/rate-limit.ts`), RLS e `rls-role-guard.ts`.
- OPA/Rego: **non trovato**. Le occorrenze di "opa" che il grep ha restituito sono falsi positivi [D].

### B1 Agent runtime isolato
- Esiste [L] l'isolamento a livello di container: `agents` e `agents-worker` girano dietro il firewall iptables con default-deny, e l'egress passa da `egress-proxy` con HMAC (`services/agents/firewall-entrypoint.sh`, `services/agents/src/egress/`, `docker/egress-proxy`).
- Il contesto di tenant per i job è in `job_queue/tenant_context.py` e `utils/actor_context.py` (letti solo i nomi).
- Sandbox per singola esecuzione (gVisor, Firecracker o simili): **non trovata**.

### B2 Tool gateway
- MCP: **non trovato**. L'unico riferimento è in un documento.
- Esistono [L]:
  - l'API Broker (`server/src/services/api-broker.ts`, `api-broker-adapter.ts`), con cost ledger, circuit breaker, log delle chiamate in uscita e idempotenza; il commento OQ-1 dice "emit-only — no cap enforcement";
  - l'allowlist egress (`egress-allowlist-match.ts`, `egress-hmac-signer.ts`, `egress-proxy-dispatcher.ts`) e `ssrf-http-client`;
  - l'audit dei tool in `services/agents/src/tools/_audit.py`.
- [D] I tool sono classi LangChain (`AuditedBaseTool`) caricate in-process e non passano da un gateway separato.

### C1 Grafo workflow
- Esistono [L]:
  - `server/src/services/workflow-graph.ts`: validazione di un DAG `{nodes, edges}` in jsonb; i cicli sono permessi e limitati a runtime;
  - `server/src/services/workflow-executor.ts`: esegue il grafo dallo snapshot fissato in `gravya_workflow_versions`, con step idempotenti (`gravya_workflow_run_steps`), cap su step e durata, actor-context RLS e fence `owning_company_id`. Il file dice che pieces, retry e DLQ sono "in corso";
  - `server/src/routes/workflows.ts`, il catalogo "pieces" (migrazione 0262), `job_queue/workflow_schedule.py`.
- **Ci sono due motori distinti** [D]: il DAG dei workflow gira in **Node**, mentre il grafo agentico Kloud gira in **Python/LangGraph**. Il workflow-executor invoca gli agenti con `invokeAgentRun`.

### C3 Punto HITL
- Esistono [L]:
  - `services/agents/src/kloud/graph.py` (`node_interrupt_check`, `interrupt()` di LangGraph, che richiede il checkpointer Postgres);
  - `kloud/hitl_types.py` (payload `approval_required` / `input_required`);
  - `kloud/checkpointer.py`;
  - lato server, `kloud-approval.ts` (risoluzione della policy di approvazione task → cliente → azienda → default `true`, migrazione 0393), `kloud-resume.ts`, `kloud-hitl-expiry-sweeper.ts`, `approvals.ts` (FORCE RLS);
  - l'handler `c2_hitl_timeout.py`;
  - `ui/src/lib/hitl.ts` (citato, non letto).

## 4. Divergenze rispetto al master plan

| Master plan | Stato attuale | Divergenza |
|---|---|---|
| Neo4j/Neptune per i mandati | Grant relazionali in Postgres con DSL di condizioni | **Sì**: nessun DB a grafo |
| OPA | Enforcement custom in Python (scope contract) e TS (grant-evaluator), più RLS | **Sì**: OPA assente |
| LangGraph | LangGraph 1.2.11 con checkpointer Postgres | Allineato. Nota: il DAG dei workflow è un motore Node separato |
| MCP | Non trovato. Tool LangChain in-process, API Broker ed egress-proxy | **Sì** |
| Redis | Redis 7 (arq, api-broker, pub/sub) | Allineato |
| pgvector/Qdrant | pgvector (`vector(1024)`) | Allineato su pgvector, Qdrant assente |
| OpenTelemetry | Esclusa di proposito: Timeline DB-native e GlitchTip solo per gli errori | **Sì, per decisione esplicita**: va segnalata, non va risolta in silenzio |
| PostgreSQL con RLS | PG17 con RLS FORCE diffusa e GUC di actor | Allineato e già maturo |
| S3/Garage | Client S3 con tier `general`/`protected`, Garage citato come destinazione (#1218) | Allineato in parte. [D] Non ho verificato quale backend sia oggi in produzione |
| (non nel piano) | LiteLLM come gateway LLM, arq, FastAPI, better-auth, GlitchTip | Da considerare nei documenti |

## 5. Non verificato / limiti
- Non ho letto per intero nessun file. Le funzionalità le ho dedotte da header e commenti, che possono non corrispondere al codice.
- Non so quali di queste parti siano davvero attive in produzione e quali siano dietro flag.
- Per lo stato di avanzamento (Task Board) va consultato il repo `gravya-app-kloudify`, che qui non ho esaminato.
