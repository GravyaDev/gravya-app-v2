# E1 — Tracing distribuito

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E1 |
| Nome | Tracing distribuito |
| Componente padre | E — Osservabilità e Valutazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.2 |
| Data | 2026-11-03 |

## 2. Scopo

**Cosa fa.** Registra ogni esecuzione agente come una traccia **DB-native** (PV-02, DX-02): un `trace_id` generato da Gravya all'avvio del run e una serie di segmenti correlati per chiamata LLM, invocazione tool, retrieval e punto di decisione (policy/HITL/router). Le tracce stanno in tabelle PostgreSQL sotto il controllo diretto di Gravya, isolate per tenant, ed E3 le legge direttamente (o tramite un export interno) per agganciarvi i punteggi. Il vocabolario degli attributi è quello unificato `gravya.*` (§4.1). Non si usa OpenTelemetry (né SDK, né OTLP, né collector): il requisito del master plan "OpenTelemetry + GenAI semantic conventions" è sostituito da PV-02 per motivi di gestione dei dati, GDPR e NIS2.

**Cosa NON fa.** Non è l'eval harness (E3), non è il registry dei prompt (E2), non sostituisce l'audit legale (A5, `gravya_event_logs`), non è error tracking (resta GlitchTip). Non invia tracce a vendor o piattaforme SaaS di tracing/eval.

**Perché esiste.** PV-01 (l'osservabilità AI è priorità di progetto) e master plan, principio 1 e §"Errori da evitare": senza tracing non si fanno eval, senza eval non si concede autonomia. È il primo componente, non l'ultimo.

## 3. Contesto e dipendenze

**Dipende da:** nessun sottoprodotto per esistere; per popolare i segmenti di tipo specifico serve l'aggancio a B1 (runtime agente), B2 (tool gateway), C1 (grafo workflow), A3 (decisioni di enforcement), C3 (HITL).

**È richiesto da:** B1, B2, C1, A3, C3, A1 (dichiarano di emettere segmenti o eventi tracciati: vedi la tabella 4.1), E3 (eval offline, legge le tracce), E2 (riferimento prompt/versione nei segmenti LLM), E-successivi di guardrail telemetry e valutazione online (ID non assegnati nel master: Non verificato), A5 (audit trail, correlazione per `trace_id`).

**Assunzioni (non verificate):** v2 avrà un servizio Node e un servizio Python (come in gravya-app) che condividono PostgreSQL e una coda di job; entrambi possono propagare il `trace_id` su HTTP interno e nei job. La struttura dei servizi v2 è definita da altri documenti (DX-01: nulla è ereditato per default).

## 4. Contratti

### 4.1 Modello dati (DB-native)

Due tabelle, entrambe con `company_id` obbligatorio e Row-Level Security per tenant (nomi proposti, da validare con DX-07):

- **`gravya_traces`**: una riga per run. `trace_id` (UUID generato da Gravya all'avvio), `company_id`, `run_id`, `execution_ticket_id`, `root_kind` (agent/workflow/eval), `started_at`, `ended_at`, `status`, `workflow_id`/`workflow_version` se presenti, `retention_class` (DA-E1-06).
- **`gravya_trace_segments`**: una riga per operazione. `segment_id`, `trace_id`, `parent_segment_id`, `company_id`, `kind`, `name`, `started_at`, `ended_at`, `status`, `attributes` (JSONB con whitelist di chiavi per `kind`, validata in scrittura), `redaction_version`.

Tabelle **separate dall'audit legale** (A5, `gravya_event_logs`): hanno scopo, accesso e retention diversi; si correlano tramite `trace_id`, che A5 scrive nei propri eventi (DA-E1-07). Partizionamento per tempo (per mese) per rendere la retention una `DROP PARTITION` e non una cancellazione riga per riga: proposta da validare.

### 4.2 Tipi di segmento

| `kind` | Attributi minimi (in `attributes`) | Emesso da |
|---|---|---|
| `llm` | `gravya.llm.provider`, `gravya.llm.request_model`, `gravya.llm.response_model`, `gravya.llm.input_tokens`, `gravya.llm.output_tokens`, `gravya.prompt.key/version/hash` (E2) | B1 / dispatch LLM |
| `tool` | `gravya.tool.name`, `gravya.tool.call_id`, esito | B2 |
| `agent` | `gravya.agent.id`, `gravya.agent.name` | B1 |
| `retrieval` | sorgente, n. risultati (nessun contenuto) | pipeline memoria |
| `decision` | `gravya.decision.kind` (policy/hitl/router), `gravya.decision.outcome`; se `kind=policy` anche `gravya.policy.bundle_version`, `gravya.policy.bundle_hash` (A3); se `hitl` l'identificativo del revisore (pseudonimo, non nome) | A3, C3, C1 |
| `eval_case` | `gravya.eval.case_id`, `gravya.eval.pass` (E3) | E3 |

Sui segmenti di C1 anche `gravya.workflow.node_id`. I nomi `gravya.policy.*`, `gravya.eval.*`, `gravya.prompt.*` e `gravya.workflow.*` restano quelli unificati in v1.1. Gli attributi LLM prima espressi come `gen_ai.*` sono ora nel namespace `gravya.llm.*`: se mantenere un mapping 1:1 con i nomi delle GenAI semantic conventions (solo come vocabolario, senza SDK OTel) è DA-E1-05, **da riportare all'utente**.

### 4.3 Contenuti: cosa si cattura e cosa no

| Si cattura | Non si cattura (default) |
|---|---|
| metadati di esecuzione: tempi, esiti, modelli, token, costi, identificativi di prompt/policy/workflow, codici di errore | testo di prompt e risposte, argomenti e risultati dei tool, documenti recuperati, contenuto dei messaggi dei clienti |
| identificativi pseudonimi (agent, revisore, ticket) | nomi, email, numeri di telefono o altri dati personali in chiaro |

Il default è coerente con la decisione kloudify «non prompt e risultati». La cattura dei contenuti è DA-E1-02, **da riportare all'utente**.

## 5. Interfacce

- **Scrittura:** helper per linguaggio (`startSegment`/`endSegment`, Node e Python) che impone `company_id` e `trace_id`, valida gli attributi contro la whitelist del `kind` e applica la redazione. Scrittura asincrona e bufferizzata verso PostgreSQL (fail-open, §7).
- **Correlazione:** `trace_id` generato da Gravya, propagato in un header interno (es. `x-gravya-trace-id`, con `x-gravya-parent-segment-id`) sulle chiamate HTTP interne e in un campo dei job in coda. Il formato dell'header (proprio o compatibile con il formato W3C `traceparent` senza SDK OTel) ricade in DA-E1-05. Lo stesso `trace_id` è scritto negli eventi di audit di A5 (chiamate LLM, invocazioni tool).
- **Lettura applicativa:** API interna filtrata per tenant (RLS) per la vista Timeline/trace del tenant.
- **Esportazione verso E3:** E3 legge `gravya_traces`/`gravya_trace_segments` nello stesso perimetro (vista o export interno in formato JSONL versionato), con il filtro tenant applicato. Nessun export verso piattaforme di eval esterne: se E3 ne proponesse una, è un punto da riportare all'utente (PV-01).
- **Accesso operatore cross-tenant:** solo tramite route dedicata con ruolo di amministratore di istanza e log dell'accesso (DA-E1-08).

## 6. Comportamento

**Flusso principale** (aggiornato in v1.2 al modello DB-native):
1. All'avvio di un run il chiamante (B1, oppure C1 per un workflow, E3 per un caso di eval) genera il `trace_id` e scrive la riga in `gravya_traces` tramite l'helper, che impone `company_id`.
2. Le chiamate verso altri servizi propagano `trace_id` e segmento padre (header interno, campo nei job); i segmenti figli (LLM, tool, retrieval, decisione) si agganciano alla stessa traccia.
3. Ogni segmento è validato contro la whitelist, redatto e accodato nel buffer di scrittura, poi scritto in PostgreSQL.
4. A fine run la traccia viene chiusa con `ended_at` e `status`; A5 riporta il `trace_id` nei propri eventi.

**Casi limite:**
- Scrittura delle tracce non riuscita (DB lento, buffer pieno): l'esecuzione prosegue (fail-open, §7), la perdita viene contata in una metrica; la perdita di segmenti non blocca il run. Fanno eccezione gli eventi di audit di A5, che seguono le regole di A5.
- Contenuti di prompt/risposta: non registrati salvo DA-E1-02.
- Segmento senza `company_id` o con attributi fuori whitelist: l'helper lo rifiuta in sviluppo e test (errore) e in produzione lo scarta contando l'evento (proposta da validare).
- Richiesta di cancellazione di un interessato (GDPR art. 17): poiché i segmenti non contengono dati personali in chiaro, si agisce sugli identificativi pseudonimi; procedura da definire con A5 (Non verificato che basti).

## 7. Requisiti non funzionali

- **Multi-tenancy:** ogni traccia e segmento porta `company_id`; RLS in lettura e scrittura (motivo dello scarto di Phoenix, #266).
- **PII:** minimizzazione a monte (whitelist di attributi per `kind`) e redazione prima della scrittura; `redactAll` di gravya-app è solo key-based e non basta per testo libero, ma con la whitelist il testo libero non entra.
- **Overhead:** latenza aggiunta p95 < 5 ms per segmento sul percorso del run (scrittura asincrona; proposta da validare).
- **Fail-open:** la scrittura delle tracce non blocca le esecuzioni.
- **Retention:** per classe (DA-E1-06), applicata per partizione.
- **Sicurezza e conformità:**
  - *GDPR.* Minimizzazione: solo metadati (§4.3), identificativi pseudonimi, nessun contenuto. Base giuridica: per i metadati, interesse legittimo/esecuzione del contratto per sicurezza, qualità e fatturazione del servizio (ipotesi da validare con la DPIA e con l'analisi in `gravya-app/docs/compliance/gdpr`, non letta in questa revisione); per i contenuti nessuna base dichiarata, quindi non si catturano (DA-E1-02). Gravya agisce verosimilmente come responsabile per i dati dei clienti dell'agenzia (Non verificato). Retention: limitata e per classe (DA-E1-06). Diritti: accesso ed export per tenant tramite API filtrata; cancellazione via pseudonimi e drop di partizione (§6). Dati in UE, nello stesso PostgreSQL gestito da Gravya; nessun trasferimento a terzi.
  - *NIS2 (art. 21).* Controllo degli accessi (RLS, ruolo di istanza per il cross-tenant con log dell'accesso), cifratura a riposo e in transito ereditata dal DB, integrità (tracce non modificabili dopo la chiusura: append-only, proposta), backup secondo la policy generale. Le tracce sono anche una fonte per rilevare e ricostruire gli incidenti significativi da notificare (preallarme 24 h, notifica 72 h): la procedura di notifica non è di E1, che fornisce i dati.
  - *AI Act.* Art. 50 (trasparenza): E1 non interagisce con gli utenti, ma registra quale modello e quale prompt hanno prodotto un output, a supporto della marcatura e dell'informativa gestite altrove. Art. 12/14/19/26: solo se un uso ricade nell'Allegato III (selezione del personale, merito creditizio), con log conservati almeno 6 mesi e sorveglianza umana (`controlli-e-conformita.md`, riga 55, letta; obblighi spostati al 2027-12-02 secondo lo stesso documento). E1 rende possibile la conservazione con `retention_class` e registra le decisioni HITL (chi ha approvato, scavalcato o fermato).
  - *Osservabilità AI resa disponibile:* per ogni run modello richiesto e risposto, token, costo, latenza, versione di prompt, policy e workflow, esiti dei tool, decisioni di policy e HITL, punteggi di eval collegati: tutto interrogabile per tenant e leggibile da E3.

## 8. Criteri di accettazione

1. Un'esecuzione agente di test produce una riga in `gravya_traces` e ≥1 segmento per ciascun `kind` (llm, tool, retrieval, decision): test d'integrazione su PostgreSQL di test, 100% dei tipi presenti.
2. `trace_id` propagato tra servizio Node e servizio Python e nei job: test che verifica lo stesso `trace_id` su entrambi i lati.
3. 100% delle tracce e dei segmenti ha `company_id` non nullo e un tenant non legge le tracce di un altro (test RLS).
4. Nessun attributo fuori whitelist (in particolare contenuti di prompt, risposte, argomenti o risultati dei tool) viene scritto: test con payload contenenti testo e PII.
5. Scrittura delle tracce non riuscita → l'esecuzione termina con successo e la perdita è contata: test.
6. Overhead p95 < 5 ms/segmento su benchmark (proposta da validare).
7. `trace_id` presente negli eventi di audit di A5 per il 100% delle chiamate LLM e tool: test.
8. Una partizione oltre la retention della sua classe viene eliminata dal job di retention: test.

## 9. Piano di implementazione

1. Fase 0: decisioni dell'utente su DA-E1-02, DA-E1-05, DA-E1-06, DA-E1-08; chiudere DA-E1-03, DA-E1-04, DA-E1-07.
2. Fase 1: schema `gravya_traces`/`gravya_trace_segments` con RLS e partizioni; helper di scrittura Node e Python con whitelist, redazione, buffer e fail-open.
3. Fase 2: segmenti LLM nel dispatch LLM di v2 e `trace_id` negli eventi di audit di A5.
4. Fase 3: segmenti tool in B2; propagazione del `trace_id` su HTTP interno e nei job.
5. Fase 4: segmenti retrieval e decisione (A3, C1, C3).
6. Fase 5: API di lettura per tenant, export verso E3, route operatore con log degli accessi, job di retention, test §8.

**Tecnologie:** PostgreSQL (lo stesso del resto di v2, salvo DA-E1-03). Nessun SDK OpenTelemetry, nessun collector, nessun servizio di tracing esterno (PV-02).

## 10. Test e valutazione

Unit (helper, whitelist, redazione), integrazione su PostgreSQL di test (criteri 1-5, 7, 8), benchmark overhead (6), test di isolamento tenant (RLS) in lettura e scrittura.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Volume delle tracce che pesa sul PostgreSQL operativo | partizioni per mese, scrittura bufferizzata, DA-E1-03 |
| PII/contenuti dei clienti nelle tracce | whitelist per `kind`, default senza contenuti (§4.3); gravya-app#1925 |
| Doppia verità tracce vs audit | tabelle separate con scopi distinti, correlate da `trace_id` (DA-E1-07) |
| Nessun ecosistema di strumenti pronto (viste, flame graph) come con OTel | vista Timeline costruita in v2; costo accettato per PV-02 |
| Accesso cross-tenant degli operatori | ruolo di istanza, log degli accessi (DA-E1-08) |

## 12. Stima e priorità

- **Taglia:** M per una costruzione da zero (schema, due helper, propagazione, retention, API di lettura); non dipende più dal riuso della Timeline. Diventa L se DA-E1-03 sceglie uno storage separato.
- **Dipendenze critiche:** DA-E1-02 e DA-E1-06 (decisioni dell'utente), DX-07 (nomi tenant/eventi).
- **Thin-slice MVP:** sì, ondata 1.

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna `gravya-app` (riferimento, non codice da riusare: DX-01, PV-03). Letti in v1.0/1.1:
- `server/src/services/timeline-engine.ts`: Timeline DB-native su `gravya_event_logs`, intestazione «NO OpenTelemetry, NO new vendor (plan §F.1, 2026-06-15)». *Idea da riprendere:* tracing nel DB del prodotto, proiezione PII-safe con `summary` a whitelist. *Difetto da non ripetere:* nessun `trace_id`, correlazione euristica per company_id/created_at/agent/session/execution_ticket (#264); tracce e audit nella stessa tabella.
- `server/src/routes/superadmin-observability.ts`: route operatore cross-tenant con `assertInstanceAdmin` e bypass RLS. *Idea:* accesso cross-tenant separato e protetto da ruolo. *Da aggiungere:* log dell'accesso (non verificato se presente).
- `server/src/observability/error-tracking.ts`: Sentry→GlitchTip solo errori, `enableOpenTelemetrySetup: false`. *Lezione:* error tracking distinto dal tracing.
- `services/agents/src/councils/runtime.py`: hook OTel opzionale con fallback no-op, «TODO Phoenix span». *Difetto:* strumentazione opzionale e mai attivata; in v2 l'helper è obbligatorio.
- `server/src/routes/llm-dispatch.ts` (`llm.inference`) e `server/src/services/audit-event-kinds.ts`: *idea:* un unico punto di dispatch LLM come punto di aggancio.
- `services/agents/src/tools/_audit.py`: righe begin/end in `gravya_tool_invocations`. *Idea:* coppia begin/end per tool.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` (~r.178): Phoenix adottato 13/04, scartato 15/06 per multi-tenancy debole (#266); timeline senza prompt e risultati. *Lezione:* le piattaforme di tracing esterne falliscono sul requisito di isolamento per tenant.
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` riga 55 (letta in v1.2): log ≥6 mesi solo per usi Allegato III.

**Divergenze dal master plan (v1.2):** (1) niente OpenTelemetry né GenAI semantic conventions come standard, per PV-02; (2) multi-tenancy come requisito primario, che il master non cita; (3) contenuti di prompt non registrati per default, mentre l'eval GenAI tipicamente li richiede (DA-E1-02).

## Appendice B — Non verificato

- Piano `.claude/plans/2026-06-15-phoenix-wave-d-trace-timeline/README.md` e §F.1 citato: non letti.
- Stato di #264, #266, #1925: non verificato sul tracker.
- `docs/start/architecture.md`: non letto. `controlli-e-conformita.md`: letta solo la riga 55.
- Analisi in `gravya-app/docs/compliance/{gdpr,nis2,ai-act}`: non lette in questa revisione; le affermazioni di §7 su base giuridica e ruolo (titolare/responsabile) sono ipotesi.
- Volume atteso delle tracce e sostenibilità sul PostgreSQL operativo.
- Se la cancellazione via pseudonimi soddisfi l'art. 17 GDPR.
- ID dei sottoprodotti E di guardrail telemetry/eval online.
- Soglia overhead 5 ms: proposta da validare.

## Appendice C — Decisioni aperte

- **DA-E1-01 — OpenTelemetry vs Timeline DB-native.** **Chiusa da DX-02 (PV-02):** tracing DB-native, niente OTel. La raccomandazione B della v1.1 è superata.
- **DA-E1-02 — Cattura contenuti prompt/risultati.** **DA RIPORTARE ALL'UTENTE.** Opzioni: (A) mai, in nessun ambiente con dati reali; (B) opt-in per tenant, con redazione, retention breve e separata, base giuridica e DPIA documentate; (C) solo in ambienti non di produzione con dati sintetici. Criterio: GDPR (minimizzazione, base giuridica, ruolo di responsabile verso i clienti delle agenzie), #1925, fabbisogno di E3. Raccomandazione: A in produzione e C per lo sviluppo finché l'utente non decide; B richiede una valutazione legale che questo documento non può dare.
- **DA-E1-03 — Storage delle tracce** (riformulata: non più "backend OTLP"). Opzioni: (A) stesse istanze PostgreSQL di v2, schema dedicato e partizionato; (B) database separato self-hosted in UE (es. un'altra istanza PostgreSQL o un DB colonnare) sotto controllo di Gravya. Escluse: servizi di tracing o eval SaaS ed extra-UE (PV-01). Criterio: perimetro dati, volume, costo operativo. Raccomandazione: A per l'ondata 1, rivalutare con i volumi reali.
- **DA-E1-04 — Rappresentazione di retrieval e decisione.** (riformulata) Opzioni: (A) `kind` dedicati (`retrieval`, `decision`) in `gravya_trace_segments`; (B) attributi su segmenti esistenti. Criterio: interrogabilità in E3. Raccomandazione: A.
- **DA-E1-05 — Uso delle GenAI semantic conventions come solo vocabolario** (nuova). **DA RIPORTARE ALL'UTENTE.** Opzioni: (A) namespace solo `gravya.*`, nessun riferimento alle convenzioni OTel; (B) nomi degli attributi LLM/tool e formato dell'header di correlazione (`traceparent`) allineati alle convenzioni come vocabolario, senza SDK, collector né export; (C) A più un mapping documentato per un eventuale export futuro. Criterio: PV-02 (la decisione esclude OTel; non è esplicito se esclude anche il solo vocabolario), stabilità delle convenzioni (stato "Development"), interoperabilità. Nessuna raccomandazione: la v1.2 adotta provvisoriamente A.
- **DA-E1-06 — Retention per classe** (nuova). **DA RIPORTARE ALL'UTENTE.** Proposta di classi da validare: metadati operativi (es. 90 giorni); tracce collegate a casi di eval o incidenti (durata del caso/incidente); usi Allegato III AI Act (≥6 mesi, art. 19). Criterio: GDPR limitazione della conservazione, AI Act art. 19, esigenze NIS2 di ricostruzione degli incidenti. Le durate non sono verificate come lecite: servono conferma dell'utente e, se necessario, parere legale.
- **DA-E1-07 — Tracce e audit: tabelle separate o comuni** (nuova). Opzioni: (A) separate, correlate da `trace_id`; (B) estendere la tabella di audit di A5. Criterio: retention e accesso diversi, lezione della Timeline di gravya-app. Raccomandazione: A (da allineare con A5).
- **DA-E1-08 — Accesso cross-tenant degli operatori alle tracce** (nuova). **DA RIPORTARE ALL'UTENTE.** Opzioni: (A) nessun accesso cross-tenant, solo su richiesta del tenant; (B) ruolo di amministratore di istanza con log degli accessi; (C) B più accesso solo ad aggregati senza identificativi. Criterio: GDPR (responsabile del trattamento, istruzioni del titolare), NIS2 controllo accessi, necessità di supporto. Raccomandazione: C, ma il perimetro dipende dai contratti con i clienti, che non sono verificati.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: sezioni 6-12 riordinate secondo il template (aggiunta §6 Comportamento ricavata dal contenuto esistente; Decisioni aperte spostate dalla §9 all'Appendice C, eliminando il duplicato); aggiunti in §3 i sottoprodotti che dichiarano di emettere span; in §4.1 aggiunti gli attributi che A3, E2, E3 e C1 dichiarano di emettere (`gravya.policy.*`, `gravya.prompt.key/version/hash` al posto di `gravya.prompt.ref`, `gravya.eval.*`, `gravya.workflow.*`). Motivo: allineamento delle interfacce tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Riprogettazione per DX-02 / PV-01 / PV-02 (niente OpenTelemetry, conformità prevalente sul master plan) e DX-01 / PV-03 (ripartenza da zero). Rimossi OTel, OTLP, collector, `traceparent` come scelta e gli span OTel: §2, §4-6 e §9 ora descrivono un tracing DB-native (tabelle `gravya_traces`/`gravya_trace_segments`, `trace_id` generato da Gravya, RLS per tenant, partizioni per la retention, export interno verso E3); attributi `gen_ai.*` sostituiti da `gravya.llm.*`; aggiunta §4.3 su cosa si cattura e cosa no; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50 e 12/14/19, osservabilità AI); criteri §8, rischi §11 e taglia §12 ricalcolati per una costruzione da zero; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti, non riuso); Appendice C: DA-E1-01 chiusa da DX-02, DA-E1-02/03/04 riformulate, nuove DA-E1-05..08. |
