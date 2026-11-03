# C1 — Grafo di workflow

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C1 |
| Nome | Grafo di workflow |
| Componente padre | C — Orchestrazione |
| Versione documento | 1.4 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Definisce in modo esplicito, versionato e validabile i workflow della piattaforma: **nodi** tipizzati (agente, tool, decisione, HITL) ed **edge condizionali**, con un **data contract** per ogni nodo (schema di input e di output). La stessa definizione viene eseguita da LangGraph, come raccomanda il master plan (durable execution, checkpoint, HITL nativo), usato come libreria open source self-hosted su infrastruttura UE, senza servizi gestiti (DA-C1-01, DA-C1-05, DA-B1-06, decise).

**Cosa NON fa.**
- Non classifica le richieste in ingresso: lo fa C2.
- Non definisce la politica di retry né la DLQ: lo fa C4. C1 si limita a dichiarare per nodo `retry_policy_ref`.
- Non gestisce timer e trigger (C5), non persiste i checkpoint (B5) e non fornisce la UI di approvazione (C3).
- Non decide le autorizzazioni. Ogni nodo tool passa da B2/A3.

**Perché esiste.** Senza un grafo esplicito il flusso degli agenti resta implicito nel codice, e non si possono fare eval gate, rollback per versione e audit del percorso. Il grafo versionato rende ogni run riproducibile, perché si sa da quale versione è partito.

## 3. Contesto e dipendenze

**Dipende da:** B1 (ambiente in cui girano i nodi agente), B2 (unico canale verso i tool), A3 (allow/deny prima di ogni nodo tool), C3 (semantica del nodo HITL), E1 (record di traccia DB-native per run, nodo ed edge), E2 (i nodi agente referenziano prompt versionati), E3 (eval gate prima di pubblicare una versione).
**Dipendenze di ondate successive:** B5 (checkpointer per i workflow lunghi; per lo skeleton serve un checkpointer Postgres con RLS costruito in v2, la collocazione dipende da DX-08; quello di gravya-app è solo riferimento, vedi Appendice A), C4 (retry e DLQ), C2 (instradamento verso il workflow), C5 (trigger), A1/A2 (indirettamente, tramite A3), G2 (Non verificato quale UI corrisponda a G2: la sezione G del master non è stata letta per intero), F6 (politica di retention DX-09, proposta, DX-12), A5 (audit e segnali di incidente, DX-10), A6 (identità, ruoli e registro delle variabili di piattaforma: **dipendenza proposta**, DX-14 ancora da riportare all'utente).
**È richiesto da:** C3 (il nodo HITL vive nel grafo), B1 (C1 è il chiamante dei job), E3 (workflow sotto test), C2, C4, C5, B5 e D1–D4 (che sono nodi tool).

**Assunzioni:**
- Il runtime di esecuzione è Python con LangGraph, come da master plan (DA-C1-01, decisa).
- Le definizioni e lo stato dei run stanno in PostgreSQL+RLS (DA-A1-01, decisa).
- Le definizioni vengono salvate in PostgreSQL v2 con RLS per tenant; gli snapshot immutabili `gravya_workflow_versions` di gravya-app sono il modello di riferimento, non una tabella da riusare.
- Il nome della colonna tenant (`company_id` qui) segue DX-07, ancora aperta.
- Le soglie e i limiti di C1 sono variabili di piattaforma gestite dal superadmin (DX-13): si modificano senza rilasci, ogni modifica è versionata e auditata, e se il valore non è leggibile o non è valido C1 non avvia il run (fail-closed). Il sottoprodotto che possiede il registro delle variabili non è deciso (DX-14, proposta A6).

## 4. Contratti

### 4.1 Definizione (`WorkflowDefinition`)
Il formato è progettato da zero in v2. Prende come idea la forma `{nodes:[{id,kind,config}], edges:[{from,to,condition}]}` dello schema zod di gravya-app (`server/src/services/workflow-graph.ts`), che ne è il riferimento. Il formato di serializzazione condiviso Node/Python (JSON Schema, Zod o Pydantic) dipende da DX-04.

| Campo | Obbligatorio | Note |
|---|---|---|
| `workflow_id`, `version` (intero, immutabile), `content_hash` | sì | snapshot fissato (idea ripresa da `gravya_workflow_versions` di gravya-app) |
| `nodes[].id`, `nodes[].kind` | sì | `kind` ∈ `agent` \| `tool` \| `decision` \| `hitl` \| `start` \| `end` (vocabolario chiuso proposto; in gravya-app `kind` era stringa libera validata contro il catalogo pieces, da non ripetere) |
| `nodes[].input_schema`, `nodes[].output_schema` | sì | JSON Schema: è il data contract; dichiara anche quali campi contengono dati personali (`x-gravya-personal-data`, *proposta*) per minimizzazione e per la politica di retention DX-09 |
| `nodes[].prompt_ref` | se `agent` | riferimento E2 nella forma `{prompt_key}@{version}` (chiave e versione intera di E2 §4.1) |
| `nodes[].tool_ref` | se `tool` | `tool_id` del catalogo B2 |
| `nodes[].retry_policy_ref` | no | risolto da C4 |
| `edges[].condition` | no | espressione su campi dello stato; il linguaggio è oggetto di DA-C1-03 |
| `max_steps`, `max_duration_ms` | sì | la definizione può solo restringere i tetti di piattaforma `c1.max_steps` e `c1.max_duration_ms` (variabili superadmin, DX-13); default di partenza ripresi da gravya-app: 500 step e 5 min (`workflow-executor.ts`), *proposta da validare* |
| `eval_suite_ref` | sì | suite di E3 richiesta per la pubblicazione |

### 4.2 Eventi emessi
`workflow.version.published`, `workflow.run.started`, `workflow.node.completed`, `workflow.node.failed`, `workflow.run.interrupted` (verso C3), `workflow.run.completed`, `workflow.version.rolled_back`. Il trasporto non è deciso: è la decisione trasversale DX-03 (= DA-A1-03). Il formato dei nomi (puntati o underscore) segue DX-07. Gli eventi non trasportano lo `state` del run, solo identificativi e esiti (minimizzazione).

### 4.3 Stato di run
Contiene `run_id`, `company_id`, `workflow_id@version`, `current_node`, `state` (validato contro gli schema dei nodi) e `step_count`. Il checkpoint è di competenza B5. Lo stato può contenere dati personali dei clienti delle agenzie: la sua retention segue la politica unica DX-09 (DA-C1-06 assorbita): default 30 giorni dopo la chiusura del run per stato e checkpoint (DECISIONS.md §5), variabile di piattaforma modificabile dal superadmin (DX-13).

## 5. Interfacce

- **Validazione statica** (funzione pura, nuova in v2; le regole di base riprendono quelle validate in gravya-app): rifiuta grafo vuoto, edge pendenti e id duplicati; segnala i cicli e i nodi irraggiungibili; verifica la compatibilità degli schema lungo ogni edge, l'esistenza dei ref (prompt in E2, tool in B2) e almeno un percorso `start→end`.
- **Compilatore** `WorkflowDefinition → StateGraph` LangGraph: `add_node` per nodo e `add_conditional_edges` per gli edge con condizione.
- **API** (proposta): `POST /workflows/{id}/versions` (crea una bozza), `POST .../versions/{v}/publish` (vincolata all'eval gate), `POST .../rollback` (ripunta alla versione precedente), `POST /workflows/{id}/runs`. Le API sono nuove; le route di gravya-app (`server/src/routes/workflows.ts`, contenuto Non verificato) non vincolano il disegno.

## 6. Comportamento

1. **Authoring → validazione → bozza.** Una definizione invalida viene rifiutata con l'elenco degli errori.
2. **Pubblicazione.** E3 esegue `eval_suite_ref` sulla bozza. Se c'è regressione, la pubblicazione viene bloccata. Se passa, la versione diventa `active` e la precedente resta disponibile per il rollback.
3. **Esecuzione.** Il run si lega alla versione attiva al momento dell'avvio e non cambia versione durante l'esecuzione. Ogni nodo `tool` invoca B2, che chiede la decisione ad A3 prima di eseguire (B2 §6, A3 §6). B2 e A3 sono fail-closed (DA-B2-04, DA-A3-07, decise): se il record di audit o di decisione non si salva, l'azione è bloccata e il nodo `tool` la tratta come esito negativo, senza proseguire sul ramo di successo. Conta come "salvato" solo un record nel DB o in una coda locale durevole su disco con fsync (DECISIONS.md §6, decisa). Nell'ondata 1 il salvataggio è confermato dalla tabella di audit minima che A5 poi assorbe (§6, decisa). Il nodo `hitl` chiama `interrupt()` e la ripresa avviene con il payload di C3. Il nodo `decision` valuta le condizioni degli edge.
4. **Rollback.** Il rollback cambia il puntatore della versione attiva. I run già in corso finiscono sulla loro versione.

**Casi limite:**
- Nessun edge soddisfatto da un nodo `decision`: il run fallisce in modo esplicito (`no_route`). Non c'è un default implicito.
- Più edge soddisfatti: la definizione deve dichiarare un ordine di priorità, altrimenti la validazione la rifiuta.
- Ciclo: è ammesso (scelta OPEN-3=B validata in gravya-app, ripresa come soluzione) ma viene interrotto dal cap `max_steps`.
- Output di un nodo non conforme a `output_schema`: il run fallisce sul nodo e la gestione passa a C4.
- Record di audit B2 o di decisione A3 non salvato: il tool non viene eseguito e il run non avanza oltre il nodo (fail-closed); la gestione dell'errore passa a C4.
- Audit dell'esito non salvato dopo che il tool è già stato eseguito (DECISIONS.md §6, decisa): l'azione non si annulla; B2 invia un segnale ad A5 e mette il record in una coda di recupero. C1 non ripete il nodo (nessuna doppia esecuzione) e marca il nodo `completed` con `audit_pending`; il run prosegue.
- Variabile di piattaforma (`c1.max_steps`, `c1.max_duration_ms`) non leggibile o non valida: il run non parte (fail-closed, DX-13).
- Checkpointer assente con un nodo `hitl`: il run deve fallire (fail-closed). In gravya-app `node_interrupt_check` documenta che senza checkpointer `interrupt()` non ha effetto: è il difetto da non ripetere.

## 7. Requisiti non funzionali

- **Sicurezza:** ogni run ha un actor-context e un `company_id` (RLS). Definizioni, run e checkpoint stanno in tabelle con FORCE RLS (soluzione validata in gravya-app, migrazione 0362, da riprogettare in v2). Nessun tool è invocabile fuori da B2.
- **Osservabilità:** un record di traccia E1 per run, per nodo e per edge valutato (segmento `kind=decision` con `gravya.decision.kind=router`), con gli attributi `gravya.workflow.id`, `gravya.workflow.version` e `gravya.workflow.node_id` (vocabolario di E1 §4.1). I record sono **DB-native** sul modello dati definito da E1 (PV-02): niente OpenTelemetry, OTLP né collector, e nessun export a piattaforme SaaS di tracing (incluso LangSmith: DA-C1-05, decisa). Per i nodi `agent` E1 può adottare come vocabolario i nomi delle GenAI semantic conventions e il formato traceparent, senza SDK né export OTel (DA-E1-05, decisa): C1 usa i nomi di attributo che E1 fissa.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Minimizzazione: le tracce E1 e gli eventi §4.2 registrano identificativi, versioni, esiti e durate, non lo `state` né input/output dei nodi; i campi personali sono marcati negli schema (§4.1). Ruolo: Gravya è responsabile del trattamento (art. 28 GDPR) per conto delle agenzie titolari (DX-11); la base giuridica del singolo workflow è dell'agenzia titolare. Non verificato come v2 la registri (dipende dai documenti A/E). Retention: si applica la politica unica DX-09 con i default approvati (DECISIONS.md §5), variabili di piattaforma modificabili dal superadmin (DX-13); l'applicazione è di F6 (proposto, DX-12). Classi di dati prodotte da C1 e default: definizioni e versioni dei workflow (artefatti di configurazione, per la durata del servizio, attore pseudonimo); stato dei run e checkpoint tramite B5 (30 giorni dopo la chiusura del run); eventi §4.2 (eventi di runtime, 90 giorni); record di traccia E1 di run/nodo/edge (tracce operative, 90 giorni); dati legati a un incidente aperto da A5 (durata del caso + 12 mesi, con sospensione delle altre scadenze). A fine contratto valgono restituzione o cancellazione entro 30 giorni. Diritti: cancellazione e accesso devono raggiungere stato di run e checkpoint per `company_id` e soggetto; il meccanismo (cancellazione o pseudonimizzazione dei checkpoint) è aperto (vedi Appendice B). Contenuti di prompt e risposte non vengono mai catturati nelle tracce di produzione (DA-E1-02, decisa). Accesso cross-tenant: nessun utente di agenzia vede definizioni, run o checkpoint di un altro tenant; l'unico accesso cross-tenant ammesso è del superadmin (DX-13), solo entro le istruzioni del titolare (art. 28) e con ogni accesso registrato in un log (12 mesi, DECISIONS.md §5; DA-E1-08). Base giuridica: per i dati delle agenzie è del titolare; per gli utenti Gravya (superadmin, operatori) è di Gravya (DECISIONS.md §6, decisa).
  - *NIS2 (art. 21).* Controllo accessi e isolamento per tenant (RLS), integrità delle versioni (`content_hash`, immutabilità), gestione delle modifiche (pubblicazione solo con eval gate, rollback), continuità (ripresa dai checkpoint), registrazione di ogni run nelle tracce E1. Un run cross-tenant o un tool eseguito senza decisione A3 è un incidente: C1 lo segnala ad A5, che possiede la notifica NIS2 (DX-10, ondata 2); C1 non notifica direttamente.
  - *AI Act.* I casi d'uso v2 non sono ad alto rischio (DX-11): sorveglianza umana e log (artt. 12, 14) non sono obblighi ma restano buona pratica di osservabilità. Il nodo `hitl` approva l'azione, non il testo, ed è fail-closed per scelta di sicurezza; ogni nodo `agent` registra `prompt_ref` e versione del workflow, così ogni output è riconducibile. Trasparenza art. 50 (applicabile): C1 non interagisce direttamente con persone; l'obbligo di informare che un contenuto è generato da AI va applicato dai nodi tool che inviano all'esterno (D1–D4) e da C3. Non verificato se serva un campo `ai_generated` nel contratto di output dei nodi `agent`: va coordinato con D1–D4 e C3.
  - *Osservabilità AI.* Percorso del run (nodi, edge scelti con motivo), versione del workflow e dei prompt, esiti di A3/B2/C3, eval gate di E3 per versione: tutto interrogabile dal DB.
- **Performance:** overhead del motore per nodo, esclusi LLM e tool, p95 < 50 ms (*proposta da validare*). È una soglia di test, non una variabile di piattaforma.
- **Limiti:** cap su step e durata obbligatori per ogni definizione, mai sopra i tetti di piattaforma `c1.max_steps` e `c1.max_duration_ms` gestiti dal superadmin (DX-13).

## 8. Criteri di accettazione

1. Il validatore rifiuta il 100% dei casi del set negativo: grafo vuoto, edge pendente, id duplicato, schema incompatibile, ref inesistente, `decision` senza priorità. Si verifica con un test unitario.
2. Un workflow di riferimento end-to-end (`start → agent → decision → tool → hitl → end`) viene compilato in LangGraph ed eseguito in un test di integrazione, con approvazione e con rifiuto.
3. Un run interrotto da `hitl` riprende dopo il riavvio del processo dallo stesso nodo, senza effetti collaterali duplicati (0 doppie invocazioni del tool nel log di B2).
4. Con il checkpointer disabilitato, un workflow con nodo `hitl` fallisce. Va verificato con un test che passi solo se il run non prosegue.
5. La pubblicazione con una suite E3 in regressione viene rifiutata (test CI). Il rollback riporta la versione attiva alla precedente e un nuovo run usa `version-1` (test di integrazione).
6. Il 100% dei nodi eseguiti ha un record di traccia E1 (DB-native) con `gravya.workflow.id`, `gravya.workflow.version` e `gravya.workflow.node_id` (query SQL sulle tracce del test 2). Nessun record contiene lo `state` del run (test di minimizzazione).
7. Un tool negato da A3 non viene eseguito: B2 risponde `denied`, 0 esecuzioni del tool (0 eventi `tool.completed`/`tool.failed` di B2), run in stato `denied`.
8. Fail-closed su audit/decisione: con la scrittura del record di audit B2 o del record di decisione A3 resa impossibile (guasto simulato), il tool non viene eseguito (0 esecuzioni) e il run non prosegue oltre il nodo (test di integrazione). Con una coda locale non durevole (senza fsync) l'esito è lo stesso; con la coda durevole il tool viene eseguito.
9. Audit dell'esito fallito dopo l'esecuzione (guasto simulato): 1 sola esecuzione del tool, 1 segnale ad A5, 1 record nella coda di recupero, nodo marcato `audit_pending` (test di integrazione).
10. Variabili di piattaforma: una definizione con `max_steps` oltre `c1.max_steps` viene rifiutata dal validatore; con la variabile non leggibile il run non parte; una modifica della variabile da parte del superadmin produce una nuova versione e un record di audit, e un utente admin di agenzia non può modificarla (test di integrazione).
11. Un admin di agenzia non legge run o checkpoint di un altro tenant (0 righe); una lettura cross-tenant del superadmin produce 1 record nel log degli accessi (test di integrazione).

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Fissare in configurazione le scelte decise: LangGraph solo libreria self-hosted UE (DA-C1-01, DA-C1-05, DA-B1-06), PostgreSQL+RLS (DA-A1-01); classificare i dati prodotti secondo DX-09.
2. Scrivere schema e validatore nuovi con data contract, tipi di nodo e priorità degli edge (riferimento: `workflow-graph.ts`).
3. Scrivere il compilatore verso LangGraph, con un checkpointer Postgres con RLS di v2 (B5 o skeleton secondo DX-08; riferimento: `kloud/checkpointer.py`).
4. Rendere fail-closed il nodo `hitl` senza checkpointer e allinearlo a C3 (si approva l'azione, non il testo).
5. Collegare i nodi `tool` ad A3 e B2 (con gestione fail-closed del mancato salvataggio dei record, coda durevole con fsync, stato `audit_pending` per l'audit dell'esito fallito) e leggere i tetti `c1.*` dal registro delle variabili di piattaforma (DX-13; nell'ondata 1 una tabella minima se DX-14 non è decisa), e la scrittura delle tracce DB-native di E1.
6. Implementare pubblicazione con eval gate (E3) e rollback.
7. Portare il workflow di riferimento end-to-end in CI.

**Tecnologie:** LangGraph open source self-hosted, senza LangSmith né LangGraph Platform (master plan; gravya-app usava `langgraph==1.2.11` e `langgraph-checkpoint-postgres==3.1.3`, versioni da riverificare), PostgreSQL+RLS su infrastruttura UE self-hosted, JSON Schema per i data contract (formato di scambio secondo DX-04).

**Rischi:** la dipendenza da B5 (ondata 2) va risolta con DX-08; il registro delle variabili di piattaforma dipende da DX-14 (proposta A6, da riportare).

## 10. Test e valutazione

- **Unit:** validatore (set positivo e negativo), valutazione delle condizioni, compilatore (topologia generata uguale alla definizione).
- **Integration:** workflow di riferimento, riavvio e ripresa, rollback, isolamento tra aziende (un run dell'azienda X non legge checkpoint dell'azienda Y).
- **Eval:** golden set di E3 per il workflow di riferimento.
- **Security:** tool non autorizzato, mancato salvataggio del record di audit B2 o di decisione A3 (il tool non deve partire, criterio 8), ref a una risorsa di un'altra azienda (fence `owning_company_id` già presente nel motore Node), payload HITL malformato (deve interrompere, come già fa `graph.py`), coda locale senza fsync non accettata come salvataggio, audit dell'esito fallito dopo l'esecuzione (criterio 9), modifica dei tetti `c1.*` da parte di un non superadmin, accesso cross-tenant senza log (criteri 10-11).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Ripetere in v2 i due motori paralleli di gravya-app | Un solo motore, LangGraph (DA-C1-01, decisa) e una sola `WorkflowDefinition`, anche per la pipeline agentica |
| Fail-open dell'HITL senza checkpointer | Criterio 4 come gate CI |
| Condizioni degli edge come codice arbitrario (iniezione) | Linguaggio dichiarativo limitato (DA-C1-03) |
| Dati personali trattenuti in checkpoint e stato oltre il necessario | Politica di retention unica DX-09; meccanismo di cancellazione da definire; tracce senza `state` (criterio 6) |
| Dati di run esportati verso SaaS di tracing (LangSmith) | Libreria senza export, verifica in CI della configurazione (DA-C1-05, decisa) |
| Audit o decisione non salvati ma azione eseguita | Fail-closed di B2/A3 (DA-B2-04, DA-A3-07), criterio 8 |
| Audit dell'esito perso dopo un tool già eseguito | Segnale ad A5 e coda di recupero, nessuna ripetizione del nodo (criterio 9) |
| Tetti di step e durata alzati senza controllo | Variabili superadmin versionate, auditate e fail-closed (DX-13), criterio 10 |
| Accesso improprio ai dati di run di altri tenant | Solo superadmin entro le istruzioni del titolare, con log degli accessi (criterio 11) |
| Versione cambiata durante un run lungo | Run legato alla versione dall'avvio alla fine |

## 12. Stima e priorità

- **Taglia:** L. Costruzione da zero di formato, validatore, compilatore, API di versioning con eval gate e rollback, HITL fail-closed e tracce DB-native; la taglia precedente dipendeva dalla convergenza dei motori esistenti, che con DX-01 non c'è più, ma il riuso che l'avrebbe ridotta a M non è più disponibile. Le decisioni del 2026-11-03 confermano la tecnologia e non cambiano la taglia.
- **Dipendenze critiche:** A3, B2, C3, E1, E3, B5 (DX-08); registro delle variabili di piattaforma (DX-14, proposta A6).
- **Thin-slice MVP:** sì (ondata 1).

---

## Appendice A — Riferimenti dal sistema precedente

Con DX-01 (PV-03) nulla di quanto segue entra in v2 come codice. È materiale di riferimento: idee da riprendere e difetti da non ripetere.

**Cosa insegna gravya-app (file letti):**
- `services/agents/src/kloud/graph.py`: è uno `StateGraph(KloudState)` LangGraph con 13 nodi (`resolve_context`, `route_memory`, `load_memory`, `founder_logic`, `run_supervisor`, `verify_output`, `interrupt_check`, `memory_writer`, `log_session`, `format_response` e altri) ed edge condizionali (`founder_next_step`, `verify_output_routing`, `interrupt_check_routing`). Viene compilato con `checkpointer`. Il grafo è **cablato nel codice**, non definito come dato.
- `services/agents/src/supervisors/generic_supervisor.py`: grafo LangGraph **lineare** (`load_sops → classify_task → retrieve → run_pipeline → collect_result`), compilato **senza** checkpointer.
- `services/agents/src/kloud/checkpointer.py`: checkpointer Postgres con cursore filtrato per azienda (FORCE RLS). Senza `DATABASE_URL`, async e HITL rispondono 503.
- `server/src/services/workflow-graph.ts`: schema zod `{nodes, edges, condition}` e validazione pura. I cicli sono ammessi (OPEN-3=B).
- `server/src/services/workflow-executor.ts`: motore DAG "β" in **Node**, eseguito dallo snapshot fissato `gravya_workflow_versions` con step idempotenti, cap di 500 step e 5 min e fence `owning_company_id`. Pieces registrati: `branch.if` e `email.send` (letti nel registro), più altri non verificati. Il file stesso dichiara retry e DLQ "being fleshed out".
- `services/agents/requirements.txt`: `langgraph==1.2.11`, `langgraph-checkpoint-postgres==3.1.3`.

**Da gravya-app-kloudify (file letto):** `docs/visione/architettura-agenti.md`: "un solo modello", cioè un'automazione è un workflow del motore Node β, che non ha mai avuto interfaccia. Per la Beta girano le automazioni Python. Dopo la Beta β diventa il motore unico (roadmap `workflow-beta-engine`) con la tela γ (`workflow-gamma-canvas`). L'override dei rifacimenti per passo è eliminato.

**Soluzioni da riprendere come idea:** definizione del workflow come dato con snapshot immutabile per versione; validatore puro; step idempotenti; cap su step e durata; fence `owning_company_id`; checkpointer con cursore filtrato per tenant e FORCE RLS; interruzione su payload HITL malformato.

**Difetti da non ripetere:**
1. Due motori (Node β e LangGraph) con due modelli di workflow: v2 ne ha uno solo.
2. Grafo agentico cablato nel codice e non ispezionabile: in v2 anche la pipeline agentica è una `WorkflowDefinition`.
3. HITL fail-open senza checkpointer, supervisore senza checkpointer, approvazione di un testo a fine catena invece dell'azione (ricognizione kloudify, `graph.py:863-867, 948-953`, non riletto da me).
4. Nessun eval gate né rollback per versione dei workflow nel codice letto.
5. `kind` dei nodi come stringa libera.

**Nota sul piano registrato.** La roadmap di gravya-app (β motore unico dopo la Beta) riguardava quel sistema e non vincola v2 (DX-01). La scelta DA-C1-01 è stata decisa a favore di LangGraph.

## Appendice B — Non verificato

- Il contenuto di `server/src/routes/workflows.ts`, `job_queue/workflow_schedule.py` e del catalogo pieces (migrazione 0262).
- L'elenco completo dei pieces oltre `branch.if` e `email.send`.
- L'esistenza di ADR specifici in `docs/decisions` di kloudify (nessun file corrispondente trovato con grep su workflow, graph, langgraph e orchestr).
- Le righe `graph.py:863-867, 948-953` (riportate dalla ricognizione).
- Quale bus eventi usare per gli eventi di §4.2 (DX-03).
- Come v2 registra la base giuridica per workflow (la notifica NIS2 è di A5, DX-10).
- Il meccanismo di cancellazione o pseudonimizzazione di stato e checkpoint per i diritti dell'interessato (DX-09 copre la retention, non questo meccanismo).
- Che la configurazione di LangGraph open source non invii dati a servizi esterni per default (da verificare sulla versione scelta).
- La corrispondenza di G2 con una UI di authoring.
- Tutte le soglie marcate *proposta da validare*.
- Il proprietario del registro delle variabili di piattaforma e dei ruoli (DX-14, proposta A6, da riportare) e i nomi `c1.max_steps`, `c1.max_duration_ms` (proposti).
- Se il grafo LangGraph gira tutto dentro il job B1 o solo i nodi agente (DECISIONS.md §6, aperta).
- Il campo `ai_generated` per l'etichetta art. 50 (DECISIONS.md §6, aperta, da coordinare nell'ondata 2).

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C1-01 | Motore di esecuzione dei workflow | — | — | **Decisa (2026-11-03, utente)**: LangGraph motore unico, come libreria self-hosted. Vedi DECISIONS.md |
| DA-C1-02 | ~~Grafo Kloud e supervisore: dato o codice~~ | — | — | **Chiusa da DX-01**: il grafo Kloud e il supervisore sono codice di gravya-app e non entrano in v2. In v2 la pipeline agentica si definisce come `WorkflowDefinition` (Appendice A, difetto 2) |
| DA-C1-03 | Linguaggio delle condizioni degli edge | (a) JSON dichiarativo (operatori limitati su campi dello stato); (b) funzioni Python registrate per nome | Sicurezza, auditabilità | (a), con (b) solo come registro chiuso |
| DA-C1-04 | ~~Tempistica rispetto alla Beta~~ | — | — | **Chiusa da DX-01**: la Beta di gravya-app non vincola v2; C1 resta in ondata 1 come da master |
| DA-C1-05 | LangGraph senza servizi gestiti | — | — | **Decisa (2026-11-03, utente)**: solo libreria open source, niente LangSmith né LangGraph Platform. Vedi DECISIONS.md |
| DA-C1-06 | ~~Retention e cancellazione di stato di run e checkpoint~~ | — | — | **Assorbita da DX-09** (politica di retention unica; default approvati: 30 giorni dopo la chiusura del run, modificabili dal superadmin, DX-13). Vedi DECISIONS.md. Il meccanismo di cancellazione per i diritti resta aperto (Appendice B) |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: flusso dei nodi tool allineato a B2/A3 (il nodo invoca B2, che consulta A3) e criterio 7 corretto di conseguenza (prima prevedeva "0 chiamate a B2", incompatibile con B2 come unico punto di decisione); `prompt_ref` allineato al formato chiave+versione di E2 e `tool_ref` al `tool_id` di B2; attributi degli span allineati a E1; aggiunti C3, B1, E3 in "È richiesto da"; trasporto eventi rimandato a DA-A1-03. Motivo: interfacce non combacianti. |
| 1.2 | 2026-11-03 | Applicate DX-01 (ripartenza da zero, PV-03) e DX-02 (niente OpenTelemetry, priorità alla conformità, PV-01/PV-02). Formato, validatore, API e checkpointer riformulati come costruzione nuova con gravya-app come riferimento; Appendice A rinominata "Riferimenti dal sistema precedente" (idee da riprendere, difetti da non ripetere); osservabilità su tracce DB-native di E1, senza OTel; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); minimizzazione su eventi e tracce. DA-C1-02 e DA-C1-04 chiuse da DX-01; DA-C1-01 riformulata; nuove DA-C1-05 (niente LangSmith/LangGraph Platform) e DA-C1-06 (retention dello stato); rischi e taglia §12 rivisti; rimandi a DX-03, DX-04, DX-07, DX-08. (rev. coerenza) §7 osservabilità: `tipo gravya.decision` → segmento `kind=decision` con `gravya.decision.kind=router` (E1 §4.2). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-C1-01, DA-C1-05 decise (Appendice C) e recepite con DA-A1-01, DA-B1-06 come scelte in §2-§3, §9, §11; DA-C1-06 assorbita da DX-09: niente retention propria, elenco delle classi di dati prodotte in §7. §7 allineata a DX-10 (incidenti segnalati ad A5) e DX-11 (Gravya responsabile art. 28; artt. 12/14 AI Act come buona pratica, art. 50 resta); DA-E1-02 (niente contenuti in produzione) e DA-E1-05 (vocabolario GenAI semconv tramite E1). Fail-closed di B2/A3 (DA-B2-04, DA-A3-07) in §6, nuovo criterio 8, test di sicurezza e rischio. Appendice B: tolta l'ipotesi sulla notifica NIS2, aggiunto il meccanismo di cancellazione aperto. Taglia invariata (L). Motivo: decisioni registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03: durate di default DX-09 (§4.3, §7: stato e checkpoint 30 giorni, eventi e tracce 90 giorni, configurazione per la durata del servizio, legal hold A5); DX-13 (tetti `c1.max_steps`/`c1.max_duration_ms` come variabili di piattaforma superadmin, versionate, auditate, fail-closed; accesso cross-tenant solo superadmin con log); righe decise di DECISIONS.md §6 che citano C1 (coda durevole con fsync come salvataggio, segnale ad A5 e coda di recupero per l'audit dell'esito fallito) e quelle correlate (tabella di audit minima in ondata 1, base giuridica). Nuovi casi limite, criteri 9-11, test, rischi; dipendenze F6, A5 e A6 (proposta, DX-14 da riportare). Righe aperte di §6 in Appendice B. Taglia invariata (L). Motivo: decisioni registrate in DECISIONS.md. |
