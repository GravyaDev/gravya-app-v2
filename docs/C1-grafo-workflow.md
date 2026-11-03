# C1 — Grafo di workflow

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C1 |
| Nome | Grafo di workflow |
| Componente padre | C — Orchestrazione |
| Versione documento | 1.1 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Definisce in modo esplicito, versionato e validabile i workflow della piattaforma: **nodi** tipizzati (agente, tool, decisione, HITL) ed **edge condizionali**, con un **data contract** per ogni nodo (schema di input e di output). La stessa definizione viene eseguita da LangGraph, come raccomanda il master plan (durable execution, checkpoint, HITL nativo).

**Cosa NON fa.**
- Non classifica le richieste in ingresso: lo fa C2.
- Non definisce la politica di retry né la DLQ: lo fa C4. C1 si limita a dichiarare per nodo `retry_policy_ref`.
- Non gestisce timer e trigger (C5), non persiste i checkpoint (B5) e non fornisce la UI di approvazione (C3).
- Non decide le autorizzazioni. Ogni nodo tool passa da B2/A3.

**Perché esiste.** Senza un grafo esplicito il flusso degli agenti resta implicito nel codice, e non si possono fare eval gate, rollback per versione e audit del percorso. Il grafo versionato rende ogni run riproducibile, perché si sa da quale versione è partito.

## 3. Contesto e dipendenze

**Dipende da:** B1 (ambiente in cui girano i nodi agente), B2 (unico canale verso i tool), A3 (allow/deny prima di ogni nodo tool), C3 (semantica del nodo HITL), E1 (span per nodo ed edge), E2 (i nodi agente referenziano prompt versionati), E3 (eval gate prima di pubblicare una versione).
**Dipendenze di ondate successive:** B5 (checkpointer per i workflow lunghi; nello skeleton si usa quello già presente, vedi Appendice A), C4 (retry e DLQ), C2 (instradamento verso il workflow), C5 (trigger), A1/A2 (indirettamente, tramite A3), G2 (Non verificato quale UI corrisponda a G2: la sezione G del master non è stata letta per intero).
**È richiesto da:** C3 (il nodo HITL vive nel grafo), B1 (C1 è il chiamante dei job), E3 (workflow sotto test), C2, C4, C5, B5 e D1–D4 (che sono nodi tool).

**Assunzioni:**
- Il runtime di esecuzione è Python con LangGraph. È ciò che il codice usa oggi, ma vedi DA-C1-01.
- Le definizioni vengono salvate in PostgreSQL con RLS per azienda, come gli snapshot `gravya_workflow_versions` già esistenti.

## 4. Contratti

### 4.1 Definizione (`WorkflowDefinition`)
Il formato riusa e completa lo schema zod esistente `{nodes:[{id,kind,config}], edges:[{from,to,condition}]}` (`server/src/services/workflow-graph.ts`).

| Campo | Obbligatorio | Note |
|---|---|---|
| `workflow_id`, `version` (intero, immutabile), `content_hash` | sì | snapshot fissato, come oggi in `gravya_workflow_versions` |
| `nodes[].id`, `nodes[].kind` | sì | `kind` ∈ `agent` \| `tool` \| `decision` \| `hitl` \| `start` \| `end` (vocabolario proposto; oggi `kind` è stringa libera validata contro il catalogo pieces) |
| `nodes[].input_schema`, `nodes[].output_schema` | sì (nuovo) | JSON Schema: è il data contract |
| `nodes[].prompt_ref` | se `agent` | riferimento E2 nella forma `{prompt_key}@{version}` (chiave e versione intera di E2 §4.1) |
| `nodes[].tool_ref` | se `tool` | `tool_id` del catalogo B2 |
| `nodes[].retry_policy_ref` | no | risolto da C4 |
| `edges[].condition` | no | espressione su campi dello stato; il linguaggio è oggetto di DA-C1-03 |
| `max_steps`, `max_duration_ms` | sì | oggi in Node: 500 step e 5 min (`workflow-executor.ts`) |
| `eval_suite_ref` | sì (nuovo) | suite di E3 richiesta per la pubblicazione |

### 4.2 Eventi emessi
`workflow.version.published`, `workflow.run.started`, `workflow.node.completed`, `workflow.node.failed`, `workflow.run.interrupted` (verso C3), `workflow.run.completed`, `workflow.version.rolled_back`. Il trasporto non è deciso: è la decisione trasversale DA-A1-03 (vedi `revisione-ondata-1.md`).

### 4.3 Stato di run
Contiene `run_id`, `company_id`, `workflow_id@version`, `current_node`, `state` (validato contro gli schema dei nodi) e `step_count`. Il checkpoint è di competenza B5.

## 5. Interfacce

- **Validazione statica** (funzione pura, già esistente in TS): rifiuta grafo vuoto, edge pendenti e id duplicati; segnala i cicli e i nodi irraggiungibili. Va estesa con la compatibilità degli schema lungo ogni edge, con i ref esistenti (prompt in E2, tool in B2) e con almeno un percorso `start→end`.
- **Compilatore** `WorkflowDefinition → StateGraph` LangGraph: `add_node` per nodo e `add_conditional_edges` per gli edge con condizione.
- **API** (proposta): `POST /workflows/{id}/versions` (crea una bozza), `POST .../versions/{v}/publish` (vincolata all'eval gate), `POST .../rollback` (ripunta alla versione precedente), `POST /workflows/{id}/runs`. Le route esistenti sono in `server/src/routes/workflows.ts`. Il contenuto attuale di quel file è Non verificato nel dettaglio.

## 6. Comportamento

1. **Authoring → validazione → bozza.** Una definizione invalida viene rifiutata con l'elenco degli errori.
2. **Pubblicazione.** E3 esegue `eval_suite_ref` sulla bozza. Se c'è regressione, la pubblicazione viene bloccata. Se passa, la versione diventa `active` e la precedente resta disponibile per il rollback.
3. **Esecuzione.** Il run si lega alla versione attiva al momento dell'avvio e non cambia versione durante l'esecuzione. Ogni nodo `tool` invoca B2, che chiede la decisione ad A3 prima di eseguire (B2 §6, A3 §6). Il nodo `hitl` chiama `interrupt()` e la ripresa avviene con il payload di C3. Il nodo `decision` valuta le condizioni degli edge.
4. **Rollback.** Il rollback cambia il puntatore della versione attiva. I run già in corso finiscono sulla loro versione.

**Casi limite:**
- Nessun edge soddisfatto da un nodo `decision`: il run fallisce in modo esplicito (`no_route`). Non c'è un default implicito.
- Più edge soddisfatti: la definizione deve dichiarare un ordine di priorità, altrimenti la validazione la rifiuta.
- Ciclo: è ammesso, come nella scelta OPEN-3=B già nel codice, ma viene interrotto dal cap `max_steps`.
- Output di un nodo non conforme a `output_schema`: il run fallisce sul nodo e la gestione passa a C4.
- Checkpointer assente con un nodo `hitl`: il run deve fallire. Oggi `node_interrupt_check` documenta che senza checkpointer `interrupt()` non ha effetto: è un fail-open da chiudere.

## 7. Requisiti non funzionali

- **Sicurezza:** ogni run ha un actor-context e un `company_id` (RLS). I checkpoint sono già protetti da FORCE RLS (migrazione 0362, citata in `kloud/checkpointer.py`). Nessun tool è invocabile fuori da B2.
- **Osservabilità:** uno span E1 per run, per nodo e per edge valutato (span `gravya.decision` con `kind=router`), con gli attributi `gravya.workflow.id`, `gravya.workflow.version` e `gravya.workflow.node_id` (nomi allineati a E1 §4.1).
- **Performance:** overhead del motore per nodo, esclusi LLM e tool, p95 < 50 ms (*proposta da validare*).
- **Limiti:** cap su step e durata obbligatori per ogni definizione.

## 8. Criteri di accettazione

1. Il validatore rifiuta il 100% dei casi del set negativo: grafo vuoto, edge pendente, id duplicato, schema incompatibile, ref inesistente, `decision` senza priorità. Si verifica con un test unitario.
2. Un workflow di riferimento end-to-end (`start → agent → decision → tool → hitl → end`) viene compilato in LangGraph ed eseguito in un test di integrazione, con approvazione e con rifiuto.
3. Un run interrotto da `hitl` riprende dopo il riavvio del processo dallo stesso nodo, senza effetti collaterali duplicati (0 doppie invocazioni del tool nel log di B2).
4. Con il checkpointer disabilitato, un workflow con nodo `hitl` fallisce. Va verificato con un test che passi solo se il run non prosegue.
5. La pubblicazione con una suite E3 in regressione viene rifiutata (test CI). Il rollback riporta la versione attiva alla precedente e un nuovo run usa `version-1` (test di integrazione).
6. Il 100% dei nodi eseguiti ha uno span E1 con `gravya.workflow.id`, `gravya.workflow.version` e `gravya.workflow.node_id` (query sulle trace del test 2).
7. Un tool negato da A3 non viene eseguito: B2 risponde `denied`, 0 esecuzioni del tool (0 eventi `tool.completed`/`tool.failed` di B2), run in stato `denied`.

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Chiudere DA-C1-01 (motore unico) e DA-C1-02 (rapporto con il grafo Kloud).
2. Estendere lo schema e il validatore esistenti con data contract, tipi di nodo e priorità degli edge.
3. Scrivere il compilatore verso LangGraph, riusando il checkpointer Postgres con RLS di `kloud/checkpointer.py`.
4. Rendere fail-closed il nodo `hitl` senza checkpointer e allinearlo a C3 (si approva l'azione, non il testo).
5. Collegare i nodi `tool` ad A3 e B2 e la strumentazione a E1.
6. Implementare pubblicazione con eval gate (E3) e rollback.
7. Portare il workflow di riferimento end-to-end in CI.

**Tecnologie:** LangGraph (master plan; nel codice `langgraph==1.2.11` e `langgraph-checkpoint-postgres==3.1.3`, `services/agents/requirements.txt`), PostgreSQL, zod e JSON Schema (zod è già nel codice).

**Rischi:** la scelta del motore tocca un piano già registrato dall'utente (Appendice A).

## 10. Test e valutazione

- **Unit:** validatore (set positivo e negativo), valutazione delle condizioni, compilatore (topologia generata uguale alla definizione).
- **Integration:** workflow di riferimento, riavvio e ripresa, rollback, isolamento tra aziende (un run dell'azienda X non legge checkpoint dell'azienda Y).
- **Eval:** golden set di E3 per il workflow di riferimento.
- **Security:** tool non autorizzato, ref a una risorsa di un'altra azienda (fence `owning_company_id` già presente nel motore Node), payload HITL malformato (deve interrompere, come già fa `graph.py`).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Due motori in parallelo (DAG Node e LangGraph) divergono | Decisione esplicita DA-C1-01 prima del codice |
| Fail-open dell'HITL senza checkpointer | Criterio 4 come gate CI |
| Condizioni degli edge come codice arbitrario (iniezione) | Linguaggio dichiarativo limitato (DA-C1-03) |
| Anticipare lavoro che il piano registrato colloca dopo la Beta | Far decidere a Daniele (DA-C1-04) |
| Versione cambiata durante un run lungo | Run legato alla versione dall'avvio alla fine |

## 12. Stima e priorità

- **Taglia:** L. Il motivo è la convergenza di due motori esistenti; con un solo motore e il riuso sarebbe M.
- **Dipendenze critiche:** A3, B2, C3, E1, E3.
- **Thin-slice MVP:** sì (ondata 1).

---

## Appendice A — Allineamento con lo stato attuale

**Cosa esiste in gravya-app (file letti):**
- `services/agents/src/kloud/graph.py`: è uno `StateGraph(KloudState)` LangGraph con 13 nodi (`resolve_context`, `route_memory`, `load_memory`, `founder_logic`, `run_supervisor`, `verify_output`, `interrupt_check`, `memory_writer`, `log_session`, `format_response` e altri) ed edge condizionali (`founder_next_step`, `verify_output_routing`, `interrupt_check_routing`). Viene compilato con `checkpointer`. Il grafo è **cablato nel codice**, non definito come dato.
- `services/agents/src/supervisors/generic_supervisor.py`: grafo LangGraph **lineare** (`load_sops → classify_task → retrieve → run_pipeline → collect_result`), compilato **senza** checkpointer.
- `services/agents/src/kloud/checkpointer.py`: checkpointer Postgres con cursore filtrato per azienda (FORCE RLS). Senza `DATABASE_URL`, async e HITL rispondono 503.
- `server/src/services/workflow-graph.ts`: schema zod `{nodes, edges, condition}` e validazione pura. I cicli sono ammessi (OPEN-3=B).
- `server/src/services/workflow-executor.ts`: motore DAG "β" in **Node**, eseguito dallo snapshot fissato `gravya_workflow_versions` con step idempotenti, cap di 500 step e 5 min e fence `owning_company_id`. Pieces registrati: `branch.if` e `email.send` (letti nel registro), più altri non verificati. Il file stesso dichiara retry e DLQ "being fleshed out".
- `services/agents/requirements.txt`: `langgraph==1.2.11`, `langgraph-checkpoint-postgres==3.1.3`.

**Da gravya-app-kloudify (file letto):** `docs/visione/architettura-agenti.md`: "un solo modello", cioè un'automazione è un workflow del motore Node β, che non ha mai avuto interfaccia. Per la Beta girano le automazioni Python. Dopo la Beta β diventa il motore unico (roadmap `workflow-beta-engine`) con la tela γ (`workflow-gamma-canvas`). L'override dei rifacimenti per passo è eliminato.

**Divergenze dal master plan:**
1. Il master raccomanda LangGraph come orchestrazione principale. Il piano registrato sceglie invece il **motore Node β** come motore unico dei workflow e lascia LangGraph al grafo agentico Kloud. Oggi i motori sono due.
2. Il master chiede nodi ed edge "espliciti": il grafo Kloud lo è solo nel codice, mentre solo β ha una definizione come dato.
3. Il master chiede un HITL nativo con checkpoint. Oggi il supervisore non ha checkpointer, e l'HITL di Kloud approva un testo a fine catena invece dell'azione (ricognizione kloudify, `graph.py:863-867, 948-953`, non riletto da me).
4. Nessun eval gate né rollback per versione dei workflow risulta nel codice letto.
5. Il piano registrato colloca il motore β dopo la Beta, mentre il master lo mette in ondata 1.

## Appendice B — Non verificato

- Il contenuto di `server/src/routes/workflows.ts`, `job_queue/workflow_schedule.py` e del catalogo pieces (migrazione 0262).
- L'elenco completo dei pieces oltre `branch.if` e `email.send`.
- L'esistenza di ADR specifici in `docs/decisions` di kloudify (nessun file corrispondente trovato con grep su workflow, graph, langgraph e orchestr).
- Le righe `graph.py:863-867, 948-953` (riportate dalla ricognizione).
- Quale bus eventi usare per gli eventi di §4.2.
- La corrispondenza di G2 con una UI di authoring.
- Tutte le soglie marcate *proposta da validare*.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C1-01 | Motore di esecuzione dei workflow | (a) LangGraph come unico motore, come da master; (b) Node β come unico motore, come da piano registrato, con LangGraph solo per Kloud; (c) definizione unica compilata verso entrambi | Durable execution e HITL nativo, costo di convergenza, coerenza con il piano registrato | (a) con riuso dello schema e del validatore di β. Serve una decisione dell'utente perché diverge dal piano registrato |
| DA-C1-02 | Grafo Kloud e supervisore: dato o codice | (a) restano codice e C1 li invoca come nodo `agent`; (b) migrano su `WorkflowDefinition` | Rischio di regressione, ispezionabilità | (a) per l'ondata 1 |
| DA-C1-03 | Linguaggio delle condizioni degli edge | (a) JSON dichiarativo (operatori limitati su campi dello stato); (b) funzioni Python registrate per nome | Sicurezza, auditabilità | (a), con (b) solo come registro chiuso |
| DA-C1-04 | Tempistica rispetto alla Beta | (a) anticipare C1 in v2; (b) seguire il piano registrato (dopo la Beta) | Regola del 02/11 sulle priorità della Beta | Decisione di Daniele |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: flusso dei nodi tool allineato a B2/A3 (il nodo invoca B2, che consulta A3) e criterio 7 corretto di conseguenza (prima prevedeva "0 chiamate a B2", incompatibile con B2 come unico punto di decisione); `prompt_ref` allineato al formato chiave+versione di E2 e `tool_ref` al `tool_id` di B2; attributi degli span allineati a E1; aggiunti C3, B1, E3 in "È richiesto da"; trasporto eventi rimandato a DA-A1-03. Motivo: interfacce non combacianti. |
