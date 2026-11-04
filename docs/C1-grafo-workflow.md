# C1 — Grafo di workflow

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C1 |
| Nome | Grafo di workflow |
| Componente padre | C — Orchestrazione |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Definisce in modo esplicito, versionato e validabile i workflow della piattaforma: **nodi** tipizzati (agente, tool, decisione, HITL) ed **edge condizionali**, con un **data contract** per ogni nodo (schema di input e di output). La stessa definizione viene eseguita da LangGraph (master plan, componente C: durable execution, checkpoint, HITL nativo), usato come libreria open source self-hosted su infrastruttura UE, senza servizi gestiti (DA-C1-01, DA-C1-05, DA-B1-06, decise). Il grafo gira nel **servizio di orchestrazione** con il checkpointer B5; in B1 girano solo i nodi `agent`, con il loro ciclo di tool, un job effimero per nodo (DECISIONS §6, decisa).

**Cosa NON fa.**
- Non classifica le richieste in ingresso (C2) e non definisce retry e DLQ (C4): dichiara solo `retry_policy_ref` per nodo.
- Non gestisce timer e trigger (C5), non persiste i checkpoint (B5), non fornisce la UI di approvazione (C3).
- Non decide le autorizzazioni (ogni nodo `tool` passa da B2 e A3), non invia nulla a terzi (i connettori D1–D4), non applica la marcatura sul canale (D1–D4).

**Perché esiste.** Senza un grafo esplicito il flusso degli agenti resta implicito nel codice: non si possono fare eval gate, rollback per versione e audit del percorso. Il grafo versionato rende ogni run riproducibile.

## 3. Contesto e dipendenze

**Dipende da:** B1 (ambiente dei nodi agente), B2 (unico canale verso i tool), A3 (allow/deny prima di ogni nodo tool), C3 (semantica del nodo HITL), E1 (tracce DB-native per run, nodo ed edge), E2 (prompt versionati), E3 (eval gate), B5 (checkpointer, ondata 2: per lo skeleton la copertura dipende da DX-08, aperta), A6 (registro delle variabili e ruoli, ondata 2; DX-14 decisa), A5 (segnali di incidente, ondata 2; fino ad allora tabella di audit minima, DECISIONS §6).
**Dipendenze di ondate successive e ricorrenze:** C4 (retry e DLQ), C2 (instradamento), C5 (trigger), F6 (applicazione della retention, DX-12), A1/A2 (indirettamente, tramite A3), G2 (corrispondenza con una UI non verificata, Appendice B).
**È richiesto da:** C3 (il nodo HITL vive nel grafo), B1 (C1 è il chiamante dei job), E3 (workflow sotto test), C2, C4, C5, B5, D1–D4 (nodi tool).

**Assunzioni:**
- Runtime Python con LangGraph (DA-C1-01); definizioni e stato dei run in PostgreSQL+RLS (DA-A1-01). Gli snapshot `gravya_workflow_versions` di gravya-app sono un modello di riferimento, non una tabella da riusare.
- Nome della colonna tenant (`company_id` qui) e formato dei nomi di evento: DX-07, aperta. Formato dei contratti condivisi Node/Python: DX-04, aperta. Trasporto degli eventi: DX-03, aperta.
- Ogni limite di C1 è una variabile del catalogo (DX-22): se non è leggibile o valida il run non parte (fail-closed, DX-17).

## 4. Contratti

### 4.1 Definizione (`WorkflowDefinition`)
Formato progettato da zero in v2; idea ripresa dalla forma `{nodes, edges, condition}` di gravya-app (`server/src/services/workflow-graph.ts`, riferimento).

| Campo | Obbligatorio | Note |
|---|---|---|
| `workflow_id`, `version` (intero, immutabile), `content_hash` | sì | snapshot fissato |
| `nodes[].id`, `nodes[].kind` | sì | `kind` ∈ `agent` \| `tool` \| `decision` \| `hitl` \| `start` \| `end` (vocabolario chiuso) |
| `nodes[].input_schema`, `nodes[].output_schema` | sì | JSON Schema (data contract); marca i campi con dati personali (`x-gravya-personal-data`, *proposta*) per minimizzazione e retention |
| `nodes[].prompt_ref` | se `agent` | `{prompt_key}@{version}` (E2); C1 lo risolve da E2 all'avvio del nodo (§6) |
| `nodes[].tool_ref` | se `tool` | `tool_id` del catalogo B2 |
| destinatario del contenuto (`audience`) | **non è un campo della definizione** | l'autore del workflow non lo dichiara: il validatore e il runtime lo derivano dai flag del tool nel catalogo B2 (`outbound_to_third_parties`, `ai_generated_output` e il flag di interazione diretta con persone, art. 50(1)), un solo vocabolario in B2 e C1 (E3). Il nome del flag di interazione diretta è *proposta*, da fissare in B2 |
| `nodes[].retry_policy_ref` | no | risolto da C4 |
| `edges[].condition` | no | linguaggio: DA-C1-03 |
| `max_steps`, `max_duration_ms` | sì | la definizione può solo restringere i tetti `c1.max_steps` e `c1.max_duration_ms` |
| `eval_suite_ref` | sì | suite E3 richiesta per la pubblicazione |

### 4.2 Eventi emessi
`workflow.version.published`, `workflow.run.started`, `workflow.node.completed`, `workflow.node.failed`, `workflow.run.interrupted` (verso C3), `workflow.run.completed`, `workflow.version.rolled_back`. Trasporto e formato dei nomi: DX-03, DX-07. Gli eventi non trasportano lo `state`, solo identificativi ed esiti. Classe di retention: `retention.runtime_events_days`.

### 4.3 Stato di run
`run_id`, `company_id`, `workflow_id@version`, `current_node`, `state` (validato contro gli schema dei nodi), `step_count`. Il checkpoint è di B5. Lo stato può contenere dati personali dei clienti delle agenzie: classe `retention.run_state_days`.

### 4.4 Output dei nodi `agent` e contenuti generati da AI (art. 50)
L'`output_schema` di ogni nodo `agent` contiene l'oggetto obbligatorio `ai_generated` con `model` (modello e provider usati, come destinazione dichiarata in B2) e `prompt_ref` (DECISIONS §6, decisa). Regole di validazione e di esecuzione:
1. Un nodo `agent` senza `ai_generated` obbligatorio nello schema è rifiutato dal validatore; un output senza `ai_generated` o non conforme fa fallire il nodo.
2. `ai_generated` segue il contenuto lungo gli edge: se il contenuto di un nodo `agent` raggiunge un nodo `tool` il cui tool, nel catalogo B2, è `outbound_to_third_parties`, `ai_generated_output` o di interazione diretta con persone, anche l'`input_schema` di quel nodo richiede `ai_generated`; un nodo intermedio che trasforma il testo non può eliminarlo. Il destinatario non lo dichiara l'autore del workflow (§4.1): un tenant non può togliere le regole dichiarando un nodo «interno». L'etichetta è un'invariante, non disattivabile dal tenant (catalogo §18).
3. **Marcatura leggibile da macchina (art. 50(2)).** È un'invariante anche per il testo, nei limiti tecnici del canale (D7). C1 garantisce il livello di dati: `ai_generated` accompagna sempre il testo nello stato del run e nell'output del nodo agente (come viaggi da B1 a C1 nel `JobResult`: Appendice B). Quanti livelli di marcatura servano per il testo, quali tecniche e quale soglia non sono verificati (registro N-AIACT-COM, riquadro: il testo del Codice non è stato letto): C1 non fissa numeri di strati. **Decisa (E13, DA-C1-07 (c))**: la scelta è rinviata alla lettura del Codice di buone pratiche, con scadenza **prima del primo rilascio in produzione** (l'art. 50 si applica dal 2.8.2026; per un sistema nuovo il 2.12.2026 non è una proroga, registro, interpretazione da confermare). **Dove si applica la marcatura** e l'hash: la marcatura che il canale consente fa parte degli argomenti della chiamata e quindi di quelli approvati da C3 (C3 AC-5: argomenti eseguiti = approvati, byte per byte); l'hash registrato è l'HMAC del contenuto marcato (E1: HMAC-SHA-256 con chiave per tenant, non SHA-256 semplice). Chi produce il contenuto marcato prima dell'approvazione (C1, B2 o il connettore) è aperto: DA-C1-10.
4. **Informativa art. 50(1)** (D6, invariante): un nodo `tool` il cui tool ha il flag di interazione diretta con persone richiede nel suo `input_schema` il campo di informativa «sei con un'IA», da inviare al più tardi alla prima interazione; l'invio è di D1–D4 e C3.
5. **Contenuti verso terzi** (email, post, messaggi per conto delle agenzie): non sono una classe ALWAYS_HITL nell'ondata 1; l'approvazione la decide l'admin agenzia, con audit, da riesaminare con D1–D4 (DA-CV-18). Nell'ondata 1 i tool di invio verso terzi sono negati nel bundle (E3: l'ondata 1 non va in produzione); da D1–D4 la precondizione (base giuridica registrata, mittente identificato, meccanismo di opposizione) è verificata dal connettore. Classi di approvazione: vocabolario unico `ALWAYS_HITL` e `MONEY_WRITE`, assegnato dal superadmin nel catalogo B2, aggiungibile e non declassabile da UI (togliere la classe richiede la conferma della seconda persona con accesso superadmin); un tool senza classe dichiarata va in `require_approval` (E4, DA-CV-15). Per i tool delle classi `ALWAYS_HITL` e `MONEY_WRITE` il validatore rifiuta una definizione in cui il nodo `tool` non sia preceduto da un nodo `hitl` su ogni percorso. Dove l'approvazione sia imposta oltre il validatore dipende da DX-05, aperta.
6. **Ciclo di tool dei nodi `agent`.** Le chiamate che un agente fa nel suo ciclo in B1 non passano da un nodo `tool` di C1, ma da B2. Le regole dei punti 2, 4 e 5 valgono anche per esse e le impone B2 a runtime: B2 rifiuta (`denied`) una chiamata a un tool `outbound_to_third_parties`, `ai_generated_output` o di interazione diretta con persone se gli argomenti non portano `ai_generated` con `model` e `prompt_ref` (E3, c); per `ALWAYS_HITL` e `MONEY_WRITE` valgono approvazione e token di A3/B2. C1 non ha controlli propri su quel ciclo oltre ai tetti del nodo.

## 5. Interfacce

- **Validazione statica** (funzione pura): rifiuta grafo vuoto, edge pendenti, id duplicati; segnala cicli e nodi irraggiungibili; verifica compatibilità degli schema lungo gli edge, esistenza dei ref (prompt in E2, tool in B2), almeno un percorso `start→end` e le regole di §4.4.
- **Compilatore** `WorkflowDefinition → StateGraph` LangGraph (`add_node`, `add_conditional_edges`).
- **API** (proposta): `POST /workflows/{id}/versions` (bozza), `POST .../versions/{v}/publish` (vincolata all'eval gate), `POST .../rollback`, `POST /workflows/{id}/runs`. Le route di gravya-app non vincolano il disegno.

## 6. Comportamento

1. **Authoring → validazione → bozza.** Una definizione invalida è rifiutata con l'elenco degli errori.
2. **Pubblicazione.** E3 gira in CI e non è richiamato a runtime: per ogni bozza produce un esito registrato (versione, hash, esito, data) e C1 lo verifica alla pubblicazione, come E2 fa per i prompt (E6; l'estensione ai workflow è una deduzione, Appendice B). Con un esito mancante o con un fallimento bloccante la pubblicazione è bloccata (invariante: zero fallimenti bloccanti). Se passa, la versione diventa `active` e la precedente resta per il rollback.
3. **Esecuzione.** Il run si lega alla versione attiva all'avvio. All'avvio di ogni nodo `agent` C1 risolve il prompt da E2 e passa al job di B1 il testo renderizzato e l'input tramite `input_ref`; il job non accede al DB (E6, DA-B1-04). `input_ref` segue la classe dei payload sensibili temporanei (`retention.sensitive_payload_days`). Ogni nodo `tool` invoca B2, che chiede la decisione ad A3 prima di eseguire. B2 e A3 sono fail-closed (DA-B2-04, DA-A3-07): se il record di audit o di decisione non si salva, l'azione è bloccata e il nodo ha esito negativo. Conta come «salvato» solo un record nel DB o in una coda locale durevole su disco con fsync; nell'ondata 1 il salvataggio è confermato dalla tabella di audit minima che A5 assorbirà (DECISIONS §6). Il nodo `hitl` chiama `interrupt()` e riprende con il payload di C3; il nodo `decision` valuta gli edge.
4. **Rollback.** Cambia il puntatore della versione attiva; i run in corso finiscono sulla loro versione.
5. **Segnali di incidente.** C1 produce un segnale per ogni evento rilevante, senza soglia locale (DA-CV-07), e lo invia ad A5 (nell'ondata 1, alla tabella di audit minima). I segnali si producono e si conservano sempre, anche con `incident.nis2_flow_active` falso (DX-10, C2, D6). Eventi che producono un segnale: run con accesso cross-tenant; tool eseguito senza decisione A3; nodo `audit_pending`; variabile non leggibile o non valida; checkpointer assente con nodo `hitl`; raggiungimento di un tetto di step o durata (elenco *proposta*, da confermare con A5).

**Casi limite:**
- Nessun edge soddisfatto da un nodo `decision`: il run fallisce (`no_route`), nessun default implicito. Più edge soddisfatti: serve un ordine di priorità dichiarato, altrimenti la validazione rifiuta.
- Ciclo ammesso, interrotto dal tetto `max_steps`; superamento di `max_duration_ms`: il run termina con esito `limit_exceeded`. La durata misura solo il tempo di esecuzione, escluse le attese HITL, già limitate dal TTL di C3 (E13, DA-C1-09 (a)).
- Output non conforme a `output_schema`: il run fallisce sul nodo e la gestione passa a C4.
- Record di audit B2 o di decisione A3 non salvato: il tool non parte e il run non avanza (fail-closed); gestione a C4.
- Audit dell'esito non salvato dopo l'esecuzione del tool: l'azione non si annulla; B2 invia un segnale ad A5 e mette il record in una coda di recupero; C1 non ripete il nodo, lo marca `completed` con `audit_pending` e il run prosegue (DECISIONS §6).
- Variabile `c1.*` non leggibile o non valida: il run non parte, con segnale (DX-17).
- Checkpointer assente con nodo `hitl`: il run fallisce (fail-closed). In gravya-app senza checkpointer `interrupt()` non ha effetto: difetto da non ripetere.
- Chiusura per TTL di una richiesta HITL: scadenza programmata che porta solo alla non esecuzione, con ultimo valore valido versionato e segnale ad A5 (DA-C3-08, decisa).

## 7. Requisiti non funzionali

- **Sicurezza:** ogni run ha actor-context e `company_id` (RLS). Definizioni, run e checkpoint in tabelle con FORCE RLS (riferimento: migrazione 0362 di gravya-app, da riprogettare). Nessun tool è invocabile fuori da B2.
- **Osservabilità:** un record di traccia E1 per run, nodo ed edge valutato (segmento `kind=decision` con `gravya.decision.kind=router`), con `gravya.workflow.id`, `gravya.workflow.version`, `gravya.workflow.node_id` (E1 §4.1). Record DB-native (PV-02): niente OpenTelemetry, OTLP, collector, né export a SaaS di tracing (LangSmith incluso, DA-C1-05). Per i nodi `agent` E1 può usare come vocabolario i nomi GenAI semantic conventions e il formato traceparent, senza SDK né export (DA-E1-05); C1 usa i nomi che E1 fissa.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per i dati delle agenzie titolari, che hanno la base giuridica del workflow; per gli utenti Gravya (superadmin, operatori) la base è di Gravya (DECISIONS §6). Minimizzazione: tracce ed eventi registrano identificativi, versioni, esiti e durate, non `state` né input/output dei nodi; contenuti di prompt e risposte mai nelle tracce di produzione (DA-E1-02); argomenti dei tool solo come hash (DA-C3-06; l'hash è un HMAC con chiave per tenant, E1, perché uno SHA-256 semplice di un dato breve resta un dato personale). Gli identificativi pseudonimi nelle tracce restano dati personali (considerando 26; le linee guida EDPB 01/2025 sono solo in consultazione e non sono un requisito). Violazione di dati personali: l'art. 33(2) non fissa ore per il responsabile; il termine verso le agenzie è un obbligo del DPA, valore aperto (DA-CV-08); i segnali di C1 alimentano A5. Trasferimenti: C1 non invia dati fuori dal perimetro; le chiamate ai modelli e ai tool passano da B2, che nega le destinazioni senza strumento di trasferimento valido e sub-responsabile autorizzato, anche in UE (DA-B2-07; il Data Privacy Framework copre solo le organizzazioni USA dell'elenco ed è impugnato, C-703/25 P). Accesso cross-tenant: nessun utente di agenzia vede dati di altri tenant; il superadmin vede di default solo dati aggregati e ogni accesso ha un log, di proprietà di A6 (DX-18, DX-19). Due vie di accesso a run o checkpoint di un tenant (E8): (a) incidente dichiarato dal superadmin, con riferimento all'incidente; (b) richiesta di assistenza, in cui l'admin agenzia concede l'accesso. In entrambi i casi perimetro e durata sono limitati (`access.superadmin_trace_access_ttl_hours`) e ogni accesso è registrato.
  - *Retention (DX-09, F6).* Le durate sono variabili di sola lettura finché l'intervallo del contratto/DPA non è definito (DA-CV-01); le cancellazioni programmate usano l'ultimo valore valido (DX-17). Classi prodotte da C1: definizioni e versioni dei workflow (artefatti di configurazione, per la durata del servizio, attore pseudonimo); stato e checkpoint (`retention.run_state_days`); eventi §4.2 (`retention.runtime_events_days`); tracce E1 (`retention.traces_days`); audit dei tool e delle decisioni collegati ai nodi (`retention.audit_decisions_months`); log degli accessi cross-tenant (`retention.cross_tenant_access_log_months`); segnali di incidente (`retention.incident_signals_months`, durata provvisoria fissata dall'utente prima della produzione, DA-CV-20); dati legati a un incidente aperto da A5 (evidenze di incidente, `retention.incident_evidence_months`; la sospensione delle scadenze vale solo per i dati di Gravya e non è attivabile finché limiti e categorie di F6 non sono definiti; per i dati delle agenzie servono istruzione nel DPA e parere legale, DA-CV-21). Backup: scadono entro `retention.data_backup_days` e al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22, procedura di F6). Fine contratto: periodo di recupero dei dati di almeno 30 giorni dalla fine del passaggio, poi cancellazione (Data Act art. 25(2)); `retention.tenant_offboarding_days` è un minimo e la qualificazione del SaaS come servizio di trattamento dei dati è da confermare con un legale; la scelta dell'agenzia tra restituzione e cancellazione (`retention.tenant_offboarding_choice`) è sempre disponibile, e se non sceglie l'esportazione resta disponibile per tutto il periodo di uscita, poi cancellazione (DA-CV-12). `input_ref`: `retention.sensitive_payload_days`. Cancellazione per i diritti dell'interessato: **decisa (E13, DA-C1-08 (a))**, cancellazione delle righe di stato e checkpoint riferite all'interessato nei run chiusi, via campi marcati `x-gravya-personal-data`.
  - *Esportazione (E15).* I dati di un tenant conservati da C1 sono esportabili con lo strumento di F6 (ondata 2, formato non fissato qui: proposta del coordinator in attesa di conferma dell'utente): definizioni e versioni dei workflow, stato dei run entro `retention.run_state_days`, checkpoint (tramite B5), eventi §4.2 entro `retention.runtime_events_days`.
  - *NIS2.* Gravya oggi non è soggetto NIS2; per scelta «NIS2 compliant ready by design» (DX-10) valgono come requisiti di progetto le misure del Reg. di esecuzione (UE) 2024/2690 (allegati 3.2 e 11: registrazione delle attività, protezione dei log, accessi privilegiati), non l'art. 21 della direttiva per i log. In C1: isolamento per tenant (RLS), integrità delle versioni (`content_hash`, immutabilità), pubblicazione solo con eval gate, ripresa dai checkpoint. Un run cross-tenant o un tool eseguito senza decisione A3 è un incidente: C1 emette il segnale ad A5 (§6, punto 5), che prepara il flusso di notifica (preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, decorrenza dalla conoscenza) presente ma non attivo (`incident.nis2_flow_active`). C1 non notifica.
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica, e comunque per l'alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 si applica dal 2.8.2026: etichetta «generato da AI» (§4.4 punti 1-2), informativa art. 50(1) (punto 4) e marcatura leggibile da macchina anche del testo (punto 3, art. 50(2)) sono invarianti; per un sistema nuovo il termine del 2.12.2026 non è una proroga (registro, interpretazione da confermare). Marketing (PV-01, ePrivacy, Codice privacy artt. 122 e 130): C1 non invia né traccia; consensi, opt-out e tracciamento sono di D1–D4.
  - *Osservabilità AI.* Percorso del run (nodi, edge scelti con motivo), versione del workflow, `prompt_ref` e `model` di ogni output, esiti di A3/B2/C3, eval gate di E3: tutto interrogabile dal DB.
- **Performance:** overhead per nodo (esclusi LLM e tool) entro `c1.node_overhead_p95_ms`.
- **Limiti:** tetti `c1.max_steps` e `c1.max_duration_ms` (superadmin); la definizione può solo restringerli.

## 8. Criteri di accettazione

1. Il validatore rifiuta il 100% del set negativo: grafo vuoto, edge pendente, id duplicato, schema incompatibile, ref inesistente, `decision` senza priorità, nodo `agent` senza `ai_generated`, contenuto `agent` verso un nodo il cui tool (catalogo B2) è `outbound_to_third_parties`, `ai_generated_output` o di interazione diretta con persone, senza propagazione di `ai_generated`; tool `ALWAYS_HITL`/`MONEY_WRITE` senza `hitl` a monte; definizione che dichiara un destinatario meno restrittivo di quello del catalogo B2 (il campo non esiste: la dichiarazione è rifiutata) (test unitario).
2. Un workflow di riferimento (`start → agent → decision → tool → hitl → end`) è compilato ed eseguito in un test di integrazione, con approvazione e con rifiuto.
3. Un run interrotto da `hitl` riprende dopo il riavvio dallo stesso nodo, con 0 doppie invocazioni del tool nel log di B2.
4. Con il checkpointer disabilitato un workflow con `hitl` fallisce (il test passa solo se il run non prosegue), con 1 segnale prodotto.
5. La pubblicazione senza esito E3 registrato per l'hash della bozza, o con un fallimento bloccante registrato, è rifiutata (test CI); il rollback riporta la versione attiva alla precedente e un nuovo run usa `version-1`.
6. Il 100% dei nodi eseguiti ha un record E1 con `gravya.workflow.id`, `gravya.workflow.version`, `gravya.workflow.node_id` (query SQL sulle tracce del test 2); nessun record contiene `state`, prompt o risposte (test di minimizzazione).
7. Un tool negato da A3 non è eseguito: B2 risponde `denied`, 0 eventi `tool.completed`/`tool.failed`, run `denied`.
8. Fail-closed: con la scrittura dell'audit B2 o del record A3 resa impossibile, 0 esecuzioni del tool e run fermo al nodo; con coda senza fsync stesso esito; con coda durevole il tool è eseguito.
9. Audit dell'esito fallito dopo l'esecuzione: 1 sola esecuzione, 1 segnale ad A5, 1 record nella coda di recupero, nodo `audit_pending`.
10. Tetti: una definizione con `max_steps` o `max_duration_ms` oltre i tetti è rifiutata; con una variabile `c1.*` non leggibile il run non parte e produce 1 segnale; la modifica da parte del superadmin crea una nuova versione e 1 record di audit; un admin agenzia non può modificarla; un ciclo infinito termina a `c1.max_steps` con `limit_exceeded`.
11. Isolamento: un admin agenzia non legge run o checkpoint di un altro tenant (0 righe); una lettura cross-tenant del superadmin produce 1 record nel log degli accessi.
12. Etichetta: in un test con un tool `outbound_to_third_parties`, il 100% degli output `agent` consegnati al nodo ha `ai_generated` con `model` e `prompt_ref` valorizzati; nessuna configurazione da UI lo disattiva. Per il ciclo di tool di un nodo `agent`: una chiamata dell'agente a un tool verso terzi senza `ai_generated` negli argomenti è rifiutata da B2 (`denied`, 0 esecuzioni) (test di integrazione con B2 e test di sicurezza).
13. Segnali: per ciascun evento elencato in §6 punto 5, con `incident.nis2_flow_active` falso, 1 segnale prodotto e conservato (test di integrazione, uno per evento).
14. Overhead per nodo p95 ≤ `c1.node_overhead_p95_ms` nel test di integrazione (soglia di test; il numero di esecuzioni è un parametro del test).
15. Prompt e input: per un nodo `agent` il job di B1 riceve testo renderizzato e `input_ref` e non apre connessioni al DB (test di integrazione con rete del job chiusa); l'oggetto di `input_ref` è cancellato alla scadenza di `retention.sensitive_payload_days` (test con orologio simulato).
16. Durata: un run in attesa HITL oltre `c1.max_duration_ms` non termina con `limit_exceeded`; un run in esecuzione oltre il tetto sì (test di integrazione).
17. Cancellazione per l'interessato: dopo la richiesta, 0 righe di stato e checkpoint dei run chiusi riferite al soggetto; i run aperti non sono toccati (test di integrazione).

## 9. Piano di implementazione

**Fasi:**
1. Fissare in configurazione le scelte decise (LangGraph solo libreria UE, DA-C1-01, DA-C1-05, DA-B1-06; PostgreSQL+RLS, DA-A1-01) e classificare i dati prodotti secondo §7.
2. Schema e validatore con data contract, tipi di nodo, priorità degli edge, regole di §4.4.
3. Compilatore verso LangGraph con checkpointer Postgres RLS di v2 (B5 o skeleton secondo DX-08).
4. Nodo `hitl` fail-closed senza checkpointer, allineato a C3 (si approva l'azione, non il testo).
5. Nodi `tool` con A3 e B2 (fail-closed, coda durevole con fsync, `audit_pending`); lettura dei tetti `c1.*` tramite l'interfaccia unica alle variabili (E5: nell'ondata 1 un'istantanea versionata nel repository, modificabile solo con una PR, ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste; i valori «proposta da validare» valgono come primo valore valido, con segnale); risoluzione del prompt da E2 e `input_ref` per i nodi `agent`; produzione dei segnali; scrittura delle tracce E1.
6. Pubblicazione con verifica dell'esito E3 registrato e rollback.
7. Workflow di riferimento end-to-end in CI.

**Tecnologie:** LangGraph open source self-hosted, senza LangSmith né LangGraph Platform; PostgreSQL+RLS su infrastruttura UE; JSON Schema per i data contract (formato di scambio: DX-04). Versioni da riverificare (gravya-app usava `langgraph==1.2.11`, `langgraph-checkpoint-postgres==3.1.3`).

**Rischi:** dipendenza da B5 (DX-08); registro delle variabili (A6, ondata 2); marcatura del testo non verificata (DA-C1-07 (c): da sciogliere prima del primo rilascio in produzione).

## 10. Test e valutazione

- **Unit:** validatore (set positivo e negativo, regole §4.4), valutazione delle condizioni, compilatore.
- **Integration:** workflow di riferimento, riavvio e ripresa, rollback, isolamento tra aziende, produzione dei segnali.
- **Eval:** golden set di E3 su dati sintetici (DA-E3-08).
- **Security:** tool non autorizzato; mancato salvataggio di audit o decisione (criterio 8); audit dell'esito fallito (9); ref a risorsa di un'altra azienda; payload HITL malformato (deve interrompere); coda senza fsync non accettata; modifica dei tetti da un non superadmin; accesso cross-tenant senza log (10-11); tentativo di consegnare contenuto verso terzi senza `ai_generated` (12).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Due motori paralleli come in gravya-app | Un solo motore e una sola `WorkflowDefinition` (DA-C1-01), anche per la pipeline agentica |
| Fail-open dell'HITL senza checkpointer | Criterio 4 come gate CI |
| Condizioni degli edge come codice arbitrario | Linguaggio dichiarativo limitato (DA-C1-03) |
| Dati personali oltre il necessario in checkpoint e stato | Retention `retention.run_state_days`; cancellazione per interessato (DA-C1-08 (a), criterio 17); tracce senza `state` (criterio 6) |
| Dati di run esportati a SaaS di tracing | Libreria senza export; verifica in CI (DA-C1-05) |
| Audit o decisione non salvati ma azione eseguita | Fail-closed B2/A3, criterio 8 |
| Audit dell'esito perso dopo l'esecuzione | Segnale ad A5 e coda di recupero (criterio 9) |
| Contenuto AI inviato a terzi senza etichetta o marcatura | Regole di §4.4 nel validatore, criteri 1 e 12; marcatura del testo: DA-C1-07 |
| Segnali di incidente persi a flusso spento | Produzione e conservazione sempre attive, criterio 13 |
| Tetti alzati senza controllo | Variabili superadmin versionate e auditate, criterio 10 |
| Run lunghi interrotti dal tetto di durata durante l'attesa HITL | La durata esclude le attese HITL (DA-C1-09 (a), criterio 16) |
| Contenuto AI verso terzi dal ciclo di tool di un agente, fuori dai nodi `tool` | B2 rifiuta a runtime senza `ai_generated` (§4.4 punto 6, criterio 12) |
| Autore del workflow che dichiara un nodo «interno» per eludere le regole | Destinatario derivato dal catalogo B2, non dichiarato (§4.1) |
| Versione cambiata durante un run | Run legato alla versione dall'avvio |

## 12. Stima e priorità

- **Taglia:** L. Costruzione da zero di formato, validatore, compilatore, versioning con eval gate e rollback, HITL fail-closed, contratto `ai_generated` e tracce DB-native; il riuso che avrebbe ridotto la taglia a M non c'è più (DX-01).
- **Dipendenze critiche:** A3, B2, C3, E1, E3, B5 (DX-08), A6.
- **Thin-slice MVP:** sì (ondata 1).

---

## Appendice A — Riferimenti dal sistema precedente

Con DX-01 (PV-03) nulla di quanto segue entra in v2 come codice: sono idee da riprendere e difetti da non ripetere. Il contenuto di questa appendice viene dalla v1.4; per la v1.5 non è stato riletto il codice.

**Cosa insegna gravya-app:**
- `services/agents/src/kloud/graph.py`: `StateGraph` LangGraph con 13 nodi ed edge condizionali, compilato con checkpointer; grafo **cablato nel codice**, non dato.
- `services/agents/src/supervisors/generic_supervisor.py`: grafo lineare compilato **senza** checkpointer.
- `services/agents/src/kloud/checkpointer.py`: checkpointer Postgres con cursore filtrato per azienda (FORCE RLS); senza `DATABASE_URL`, async e HITL rispondono 503.
- `server/src/services/workflow-graph.ts`: schema zod `{nodes, edges, condition}`, validazione pura, cicli ammessi (OPEN-3=B).
- `server/src/services/workflow-executor.ts`: motore DAG in Node con snapshot `gravya_workflow_versions`, step idempotenti, cap di 500 step e 5 min (valori di riferimento, non default di v2), fence `owning_company_id`; pieces letti: `branch.if`, `email.send`.
- `services/agents/requirements.txt`: `langgraph==1.2.11`, `langgraph-checkpoint-postgres==3.1.3`.

**Da gravya-app-kloudify:** `docs/visione/architettura-agenti.md`: «un solo modello»; il motore Node β non ha mai avuto interfaccia.

**Idee da riprendere:** definizione come dato con snapshot immutabile; validatore puro; step idempotenti; cap su step e durata; fence per tenant; checkpointer filtrato per tenant con FORCE RLS; interruzione su payload HITL malformato.

**Difetti da non ripetere:** (1) due motori con due modelli di workflow; (2) grafo agentico cablato nel codice; (3) HITL fail-open senza checkpointer, supervisore senza checkpointer, approvazione di un testo a fine catena invece dell'azione; (4) nessun eval gate né rollback per versione; (5) `kind` come stringa libera.

## Appendice B — Non verificato

- Contenuto di `server/src/routes/workflows.ts`, `job_queue/workflow_schedule.py`, catalogo pieces (migrazione 0262) e pieces oltre `branch.if` e `email.send`; ADR di kloudify; righe `graph.py:863-867, 948-953` (dalla ricognizione, non riletto da me).
- Marcatura leggibile da macchina del **testo** (art. 50(2)): numero di strati, ruolo dei metadati nel testo libero, soglia di lunghezza, tecniche; il testo del Codice sulla trasparenza non è stato letto (registro N-AIACT-COM, PDF non apribile; segno non_verificata). L'eccezione per la funzione assistiva di editing non è valutata. Applicabilità del termine 2.12.2026: interpretazione del registro.
- Nome del flag di interazione diretta con persone nel catalogo B2 (proposta, da allineare in B2); campi del catalogo B2 `outbound_to_third_parties` e `ai_generated_output` presi da una ricerca nel testo di B2, non da una lettura per intero. Dove l'approvazione sia imposta oltre il validatore: DX-05, aperta.
- Elenco degli eventi che producono un segnale (§6, punto 5): proposta, da confermare con A5.
- Come `ai_generated` viaggia da B1 a C1 (`JobResult`, `outputs_ref`): B1 non ha un campo dedicato, da concordare con B1. Formato e collocazione di `input_ref`: DA-B1-10, concordare con B1.
- Estensione ai workflow dell'esito E3 registrato (E6 riguarda le versioni di prompt): deduzione, da confermare con E2 ed E3.
- Chi produce il contenuto marcato prima dell'approvazione (DA-C1-10) e la sua coerenza con C3 AC-5: C3 non letto in questo task oltre una ricerca per la parola «marcatura».
- Strumento di esportazione dei dati di tenant (F6, ondata 2): formato non fissato, proposta del coordinator in attesa di conferma dell'utente.
- Qualificazione di Gravya come fornitore NIS2 e criterio dimensionale (DX-10; registro N-NIS2, N-PMI); qualificazione del SaaS come «servizio di trattamento dei dati» (Data Act); base giuridica delle evidenze di incidente (parere legale).
- Marketing: consensi, opt-out, tracciamento e artt. 122 e 130 del Codice privacy sono di D1–D4 e non sono stati letti per questo documento.
- Che la configurazione di LangGraph open source non invii dati a servizi esterni per default (da verificare sulla versione scelta); versioni dei pacchetti.
- Corrispondenza di G2 con una UI di authoring; bus eventi (DX-03); formato dei contratti (DX-04); nomi (DX-07); copertura di B5 nello skeleton (DX-08).
- La procedura di propagazione delle cancellazioni ai backup (F6) e come la cancellazione per interessato raggiunga i checkpoint di B5.
- Le soglie e i valori marcati «proposta da validare» o «da definire» nel catalogo (`c1.max_steps`, `c1.max_duration_ms`, `c1.node_overhead_p95_ms`, `retention.incident_signals_months`).
- Il proprietario del registro delle variabili è A6 (DX-14, decisa), non ancora documentato.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C1-01 | Motore di esecuzione | — | — | **Decisa (2026-11-03, utente)**: LangGraph motore unico, libreria self-hosted |
| DA-C1-02 | ~~Grafo Kloud e supervisore~~ | — | — | **Chiusa da DX-01** |
| DA-C1-03 | Linguaggio delle condizioni degli edge | (a) JSON dichiarativo con operatori limitati; (b) funzioni Python registrate per nome | Sicurezza, auditabilità | (a), con (b) solo come registro chiuso |
| DA-C1-04 | ~~Tempistica rispetto alla Beta~~ | — | — | **Chiusa da DX-01** |
| DA-C1-05 | LangGraph senza servizi gestiti | — | — | **Decisa (2026-11-03, utente)**: niente LangSmith né LangGraph Platform |
| DA-C1-06 | ~~Retention di stato e checkpoint~~ | — | — | **Assorbita da DX-09** |
| DA-C1-07 | Marcatura leggibile da macchina del testo generato (art. 50(2)) | (a) solo `ai_generated` più disclosure per canale; (b) (a) più marcatura incorporata nel testo dove il canale lo consente; (c) rinviare alla lettura del Codice, poi (b) o (a) | Efficacia, interoperabilità, robustezza «per quanto tecnicamente fattibile»; limiti dei canali | **Decisa (c) (2026-11-04, utente, E13)**, con scadenza prima del primo rilascio in produzione; i livelli e le tecniche restano da scegliere dopo la lettura del Codice |
| DA-C1-08 | Cancellazione di stato e checkpoint per i diritti dell'interessato | (a) cancellare le righe riferite al soggetto nei run chiusi; (b) pseudonimizzare; (c) attendere la scadenza | Effettività del diritto, riproducibilità, art. 28(3)(e) | **Decisa (a) (2026-11-04, utente, E13)** |
| DA-C1-09 | Cosa misura `max_duration_ms` rispetto alle attese HITL | (a) solo l'esecuzione, escluse le attese; (b) tempo totale; (c) due variabili | Compatibilità con workflow di giorni | **Decisa (a) (2026-11-04, utente, E13)** |
| DA-C1-10 | Chi produce il contenuto marcato prima dell'approvazione, così che l'approvatore e l'hash (HMAC) coprano il contenuto marcato (C3 AC-5). **DA RIPORTARE ALL'UTENTE** (conformità) | (a) un passo di marcatura dichiarato dal connettore (D1–D4) e invocato da B2 prima del parcheggio; (b) un nodo di C1 prima del nodo `hitl`; (c) il connettore dopo l'approvazione, con l'hash che copre il contenuto non marcato e un record separato della marcatura | Conformità art. 50(2); l'approvatore vede quanto verrà inviato; il canale è noto solo al connettore | (a), da concordare con B2, C3 e D1–D4; dipende da DA-C1-07 |
| DX-08 (trasversale) | Copertura di B5 nello skeleton | Vedi DECISIONS §1 | — | Aperta: C1 la richiama, non la decide |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: flusso dei nodi tool allineato a B2/A3, `prompt_ref` e `tool_ref` allineati a E2 e B2, attributi E1. Motivo: interfacce non combacianti. |
| 1.2 | 2026-11-03 | DX-01 e DX-02: costruzione da zero, tracce DB-native senza OpenTelemetry, voce «Sicurezza e conformità», DA-C1-05 e DA-C1-06. |
| 1.3 | 2026-11-03 | Decisioni del 2026-11-03: DA-C1-01 e DA-C1-05 decise, DA-C1-06 assorbita da DX-09, fail-closed B2/A3, criterio 8. |
| 1.4 | 2026-11-03 | Durate DX-09, DX-13, coda durevole e audit dell'esito fallito, criteri 9-11, dipendenze F6, A5, A6. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo v1.2 e al registro v1.6. Aggiunti: contratto `ai_generated` (model, prompt_ref) con regole di propagazione, informativa art. 50(1) e marcatura del testo art. 50(2) (§4.4, DA-C1-07); esecuzione del grafo nel servizio di orchestrazione con checkpointer B5, in B1 solo i nodi agente (DECISIONS §6); segnali di incidente sempre prodotti e senza soglia locale (DA-CV-07, DX-10); approvazione dei contenuti verso terzi (DA-CV-18) e ALWAYS_HITL/MONEY_WRITE (DA-CV-15); criteri 12-14. Corretti: «NIS2 (art. 21)» per i log sostituito dal Reg. 2024/2690 allegati 3.2 e 11 (DX-10); «legal hold» sostituito da evidenze di incidente (DA-CV-21); flusso di notifica NIS2 non attivo; GDPR art. 28 e 33(2); trasferimenti e DPF; EDPB 01/2025; calendario AI Act dopo il Reg. 2026/1744; fine contratto (Data Act art. 25(2)); marketing rinviato a D1–D4. Valori fissi sostituiti da nomi di variabili (`c1.node_overhead_p95_ms`, retention). Nuove DA-C1-08 (cancellazione dati di run, ex punto aperto) e DA-C1-09 (durata e attese HITL). Motivo: unico giro di revisione prima dell'approvazione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 (2026-11-04) e revisione unica della v1.5. Il destinatario del contenuto non è più dichiarato nella definizione ma derivato dal catalogo B2, con vocabolario unico e flag di interazione diretta (E3); le regole di §4.4 valgono anche per il ciclo di tool dei nodi agente, imposte da B2 (E3, rilievo compliance R1); classi `ALWAYS_HITL`/`MONEY_WRITE` assegnate dal superadmin, tool senza classe in `require_approval` (E4); C1 risolve il prompt da E2 e passa testo e `input_ref` al job, esito E3 registrato verificato alla pubblicazione (E6); hash come HMAC per tenant (E1); due vie di accesso del superadmin ai dati di tenant (E8); DA-C1-07 (c) con scadenza prima del primo rilascio in produzione, DA-C1-08 (a), DA-C1-09 (a) decise (E13); istantanea delle variabili prima di A6 (E5); `retention.tenant_offboarding_choice` e dichiarazione dei dati esportabili con lo strumento di F6 (E15); nuovi criteri 15-17; nuova DA-C1-10 sul punto di applicazione della marcatura (rilievo compliance R8); tolte le note «non ancora in DECISIONS». Motivo: chiudere la v1.5 prima dell'approvazione dell'utente. |
