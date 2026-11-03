# E1 — Tracing distribuito

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E1 |
| Nome | Tracing distribuito |
| Componente padre | E — Osservabilità e Valutazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.4 |
| Data | 2026-11-03 |

## 2. Scopo

**Cosa fa.** Registra ogni esecuzione agente come una traccia **DB-native** (PV-02, DX-02): un `trace_id` generato da Gravya all'avvio del run e una serie di segmenti correlati per chiamata LLM, invocazione tool, retrieval e punto di decisione (policy/HITL/router). Le tracce stanno in tabelle PostgreSQL sotto il controllo diretto di Gravya, isolate per tenant, ed E3 le legge direttamente (o tramite un export interno) per agganciarvi i punteggi. Il vocabolario degli attributi usa i nomi delle GenAI semantic conventions (`gen_ai.*`) per LLM, tool e agenti e il namespace `gravya.*` per il resto (§4.2); la correlazione usa il formato W3C `traceparent` (DA-E1-05, decisa). Non si usa OpenTelemetry come software (né SDK, né OTLP, né collector, né export): del master plan "OpenTelemetry + GenAI semantic conventions" resta solo il vocabolario, per PV-02 (gestione dei dati, GDPR e NIS2).

**Cosa NON fa.** Non è l'eval harness (E3), non è il registry dei prompt (E2), non sostituisce l'audit legale (A5, `gravya_event_logs`), non è error tracking (resta GlitchTip). Non invia tracce a vendor o piattaforme SaaS di tracing/eval.

**Perché esiste.** PV-01 (l'osservabilità AI è priorità di progetto) e master plan, principio 1 e §"Errori da evitare": senza tracing non si fanno eval, senza eval non si concede autonomia. È il primo componente, non l'ultimo.

## 3. Contesto e dipendenze

**Dipende da:** nessun sottoprodotto per esistere; F6 (politica di retention, DX-12, ID proposto) per il job di retention; il registro delle variabili di piattaforma e il ruolo superadmin (DX-13), il cui sottoprodotto responsabile è ancora da decidere (DX-14, proposta A6 — Identità, ruoli e configurazione di piattaforma, **DA RIPORTARE**); per popolare i segmenti di tipo specifico serve l'aggancio a B1 (runtime agente), B2 (tool gateway), C1 (grafo workflow), A3 (decisioni di enforcement), C3 (HITL).

**È richiesto da:** B1, B2, C1, A3, C3, A1 (dichiarano di emettere segmenti o eventi tracciati: vedi la tabella 4.1), E3 (eval offline, legge le tracce), E2 (riferimento prompt/versione nei segmenti LLM), E-successivi di guardrail telemetry e valutazione online (ID non assegnati nel master: Non verificato), A5 (audit trail, correlazione per `trace_id`).

**Assunzioni (non verificate):** v2 avrà un servizio Node e un servizio Python (come in gravya-app) che condividono PostgreSQL e una coda di job; entrambi possono propagare il `trace_id` su HTTP interno e nei job. La struttura dei servizi v2 è definita da altri documenti (DX-01: nulla è ereditato per default).

## 4. Contratti

### 4.1 Modello dati (DB-native)

Due tabelle, entrambe con `company_id` obbligatorio e Row-Level Security per tenant (nomi proposti, da validare con DX-07):

- **`gravya_traces`**: una riga per run. `trace_id` (UUID generato da Gravya all'avvio), `company_id`, `run_id`, `execution_ticket_id`, `root_kind` (agent/workflow/eval), `started_at`, `ended_at`, `status`, `workflow_id`/`workflow_version` se presenti, `retention_class` (aggancio per l'override per classe/tenant previsto da DX-09, non attivo: oggi vale la politica unica di default).
- **`gravya_trace_segments`**: una riga per operazione. `segment_id`, `trace_id`, `parent_segment_id`, `company_id`, `kind`, `name`, `started_at`, `ended_at`, `status`, `attributes` (JSONB con whitelist di chiavi per `kind`, validata in scrittura), `redaction_version`.

Tabelle **separate dall'audit legale** (A5, `gravya_event_logs`): hanno scopo, accesso e retention diversi; si correlano tramite `trace_id`, che A5 scrive nei propri eventi (DA-E1-07). Partizionamento per tempo (per mese) per applicare la politica di retention DX-09 con una `DROP PARTITION` e non una cancellazione riga per riga: proposta da validare. Storage: lo stesso PostgreSQL self-hosted in UE del resto di v2 (DA-A1-01, DA-B1-06); DA-E1-03 resta formalmente aperta solo sull'eventuale separazione futura per volume.

**Classi di dati prodotte da E1** (politica di retention unica DX-09; durate di default di DECISIONS.md §5, variabili di piattaforma modificabili dal superadmin, DX-13): (1) righe di traccia (`gravya_traces`): tracce operative, 90 giorni; (2) segmenti di esecuzione con metadati (`gravya_trace_segments`, inclusi i segmenti `decision` con pseudonimo del revisore HITL): 90 giorni; i segmenti `eval_case` e le tracce con `root_kind=eval` (dati sintetici) seguono la classe report di eval, 12 mesi; (3) log degli accessi cross-tenant del superadmin (§5): 12 mesi; (4) contatori di perdita/scarto dei segmenti (metriche): classe tracce operative, 90 giorni (assegnazione proposta da validare). Dati collegati a un incidente aperto da A5: durata del caso + 12 mesi, con sospensione delle altre scadenze (legal hold, meccanismo di F6 e A5). A fine contratto dell'agenzia: restituzione o cancellazione entro 30 giorni.

### 4.2 Tipi di segmento

| `kind` | Attributi minimi (in `attributes`) | Emesso da |
|---|---|---|
| `llm` | `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gravya.prompt.key/version/hash` (E2) | B1 / dispatch LLM |
| `tool` | `gen_ai.tool.name`, `gen_ai.tool.call.id`, esito; `gravya.tool.destination` (destinazione dichiarata, DA-B2-07); `gravya.tool.args_hash` (solo hash degli argomenti, mai il valore) | B2 |
| `agent` | `gen_ai.agent.id`, `gen_ai.agent.name` | B1 |
| `retrieval` | sorgente, n. risultati (nessun contenuto) | pipeline memoria |
| `decision` | `gravya.decision.kind` (policy/hitl/router), `gravya.decision.outcome`; se `kind=policy` anche `gravya.policy.bundle_version`, `gravya.policy.bundle_hash` (A3); se `hitl` l'identificativo del revisore (pseudonimo, non nome) | A3, C3, C1 |
| `eval_case` | `gravya.eval.case_id`, `gravya.eval.pass` (E3) | E3 |

Sui segmenti di C1 anche `gravya.workflow.node_id`. I nomi `gravya.policy.*`, `gravya.eval.*`, `gravya.prompt.*` e `gravya.workflow.*` restano quelli unificati in v1.1. Per LLM, tool e agenti si adottano i nomi delle GenAI semantic conventions (DA-E1-05, decisa): solo vocabolario, nessun SDK né export OTel. I nomi esatti vanno fissati sulla versione delle convenzioni in vigore all'implementazione (stato "Development", possono cambiare); `gravya.tool.destination` è un nome proposto.

### 4.3 Contenuti: cosa si cattura e cosa no

| Si cattura | Non si cattura (default) |
|---|---|
| metadati di esecuzione: tempi, esiti, modelli, token, costi, identificativi di prompt/policy/workflow, codici di errore | testo di prompt e risposte, argomenti e risultati dei tool, documenti recuperati, contenuto dei messaggi dei clienti |
| identificativi pseudonimi (agent, revisore, ticket) | nomi, email, numeri di telefono o altri dati personali in chiaro |

Decisione DA-E1-02: i contenuti **non si catturano mai in produzione**; gli argomenti dei tool rientrano nei contenuti esclusi e nelle tracce compaiono solo come hash (decisione di DECISIONS.md §6, DA-C3-06 (a)); vale anche per la chiamata parcheggiata da HITL; un eventuale opt-in futuro richiede DPIA e parere legale. Negli ambienti di sviluppo e di eval si usano solo dati sintetici (DA-E3-08).

## 5. Interfacce

- **Scrittura:** helper per linguaggio (`startSegment`/`endSegment`, Node e Python) che impone `company_id` e `trace_id`, valida gli attributi contro la whitelist del `kind` e applica la redazione. Scrittura asincrona e bufferizzata verso PostgreSQL (fail-open per le tracce, §7; i record di audit e di decisione sono fail-closed e non passano da questo buffer).
- **Correlazione:** `trace_id` generato da Gravya, propagato in un header interno (es. `x-gravya-trace-id`, con `x-gravya-parent-segment-id`) sulle chiamate HTTP interne e in un campo dei job in coda. Formato: W3C `traceparent` (il `trace_id` UUID reso come 32 cifre esadecimali), senza SDK OTel (DA-E1-05, decisa); nome dell'header da fissare. Lo stesso `trace_id` è scritto negli eventi di audit di A5 (chiamate LLM, invocazioni tool).
- **Lettura applicativa:** API interna filtrata per tenant (RLS) per la vista Timeline/trace del tenant.
- **Esportazione verso E3:** E3 legge `gravya_traces`/`gravya_trace_segments` nello stesso perimetro (vista o export interno in formato JSONL versionato), con il filtro tenant applicato. Nessun export verso piattaforme di eval esterne (DA-E3-09, decisa) né verso LangSmith o altri servizi gestiti (DA-C1-05, decisa).
- **Accesso cross-tenant:** solo il superadmin di istanza (DX-13), distinto dagli admin delle agenzie, tramite route dedicata; l'accesso è consentito solo entro le istruzioni del titolare (art. 28) e ogni accesso è registrato (chi, quando, tenant, traccia o filtro, motivo) nel log degli accessi, retention 12 mesi. Se il log dell'accesso non si salva, l'accesso è negato (fail-closed, proposta coerente con DX-13). Gli admin delle agenzie leggono solo il proprio tenant (RLS).
- **Variabili di piattaforma (DX-13):** le soglie e le durate di E1 si leggono dal registro delle variabili di piattaforma, modificabili solo dal superadmin senza rilasci; ogni modifica è versionata e auditata, e se il valore non è leggibile o non è valido si applica fail-closed (si mantiene l'ultimo valore valido versionato; il job di retention non cancella nulla su un valore non valido; proposta da validare). Variabili di E1: durate di retention per classe (§4.1), soglia di overhead p95 (default 5 ms, proposta da validare), dimensione del buffer di scrittura e soglia di perdita anomala di segmenti che genera il segnale verso A5 (valori proposti da validare, non fissati).

## 6. Comportamento

**Flusso principale** (aggiornato in v1.2 al modello DB-native):
1. All'avvio di un run il chiamante (B1, oppure C1 per un workflow eseguito con LangGraph come libreria self-hosted, DA-C1-01, E3 per un caso di eval) genera il `trace_id` e scrive la riga in `gravya_traces` tramite l'helper, che impone `company_id`.
2. Le chiamate verso altri servizi propagano `trace_id` e segmento padre (header interno, campo nei job); i segmenti figli (LLM, tool, retrieval, decisione) si agganciano alla stessa traccia.
3. Ogni segmento è validato contro la whitelist, redatto e accodato nel buffer di scrittura, poi scritto in PostgreSQL.
4. A fine run la traccia viene chiusa con `ended_at` e `status`; A5 riporta il `trace_id` nei propri eventi.

**Casi limite:**
- Scrittura delle tracce non riuscita (DB lento, buffer pieno, dimensione variabile di piattaforma): l'esecuzione prosegue (fail-open, §7), la perdita viene contata in una metrica; la perdita di segmenti non blocca il run. Non vale per l'audit dei tool (DA-B2-04) né per il record di decisione di A3 (DA-A3-07): sono **fail-closed**, se il record non si salva l'azione si blocca. Questi record sono di B2/A3/A5, non di E1; il segmento `decision` di E1 è un riflesso osservabile e la sua perdita non sblocca né blocca nulla.
- Contenuti di prompt/risposta: mai registrati in produzione (DA-E1-02); un payload che li contiene viene scartato dalla whitelist.
- Segmento senza `company_id` o con attributi fuori whitelist: l'helper lo rifiuta in sviluppo e test (errore) e in produzione lo scarta contando l'evento (proposta da validare).
- Richiesta di cancellazione di un interessato (GDPR art. 17): poiché i segmenti non contengono dati personali in chiaro, si agisce sugli identificativi pseudonimi; procedura da definire con A5 (Non verificato che basti).

## 7. Requisiti non funzionali

- **Multi-tenancy:** ogni traccia e segmento porta `company_id`; RLS in lettura e scrittura (motivo dello scarto di Phoenix, #266).
- **PII:** minimizzazione a monte (whitelist di attributi per `kind`) e redazione prima della scrittura; `redactAll` di gravya-app è solo key-based e non basta per testo libero, ma con la whitelist il testo libero non entra.
- **Overhead:** latenza aggiunta p95 < 5 ms per segmento sul percorso del run (scrittura asincrona; default proposto da validare, variabile di piattaforma DX-13).
- **Fail-open (solo tracce):** la scrittura delle tracce non blocca le esecuzioni; audit dei tool e record di decisione sono fail-closed (DA-B2-04, DA-A3-07) e fuori da E1.
- **Retention:** politica unica di default DX-09 con le durate approvate (DECISIONS.md §5: 90 giorni tracce e segmenti, 12 mesi log degli accessi e report di eval), applicata per partizione; le durate sono variabili di piattaforma del superadmin (DX-13); override per classe/tenant previsti ma non attivi. Classi prodotte: §4.1.
- **Sicurezza e conformità:**
  - *GDPR.* Gravya tratta i dati per conto delle agenzie come responsabile del trattamento (art. 28, DX-11). Minimizzazione: solo metadati (§4.3), identificativi pseudonimi, contenuti mai in produzione (DA-E1-02). Base giuridica e istruzioni: quelle del titolare (agenzia) nel contratto art. 28; la finalità dei metadati (sicurezza, qualità, fatturazione) va riportata nel contratto (Non verificato). Retention: politica unica DX-09, durate di default di §4.1. Accesso cross-tenant solo del superadmin entro le istruzioni del titolare e con log (DX-13); per gli utenti di Gravya (superadmin) la base giuridica del log è di Gravya, per i dati delle agenzie è del titolare (DECISIONS.md §6). Diritti: accesso ed export per tenant tramite API filtrata, a supporto del titolare; cancellazione via pseudonimi e drop di partizione (§6). Dati in UE, nello stesso PostgreSQL self-hosted (DA-B1-06); nessun trasferimento a terzi né a servizi di tracing/eval (DA-E3-09, DA-C1-05).
  - *NIS2 (art. 21).* Controllo degli accessi (RLS, superadmin per il cross-tenant con log dell'accesso, DX-13; modifiche alle variabili di piattaforma versionate e auditate), cifratura a riposo e in transito ereditata dal DB, integrità (tracce non modificabili dopo la chiusura: append-only, proposta), backup secondo la policy generale. Notifica degli incidenti (24 h/72 h): responsabilità di A5 (DX-10). E1 non notifica: invia ad A5 segnali (es. perdita anomala di segmenti, accessi cross-tenant) e fornisce le tracce per ricostruire l'incidente; il formato del segnale va concordato con A5.
  - *AI Act.* I casi d'uso v2 non sono ad alto rischio (DX-11). Art. 50 (trasparenza), applicabile: E1 non interagisce con gli utenti, ma registra quale modello e quale prompt hanno prodotto un output, a supporto della marcatura e dell'informativa gestite altrove. Artt. 12/14/19/26: non obbligatori; la registrazione delle esecuzioni e delle decisioni HITL (chi ha approvato, scavalcato o fermato) resta come buona pratica di osservabilità, senza durate minime imposte.
  - *Osservabilità AI resa disponibile:* per ogni run modello richiesto e risposto, token, costo, latenza, versione di prompt, policy e workflow, esiti dei tool, decisioni di policy e HITL, punteggi di eval collegati: tutto interrogabile per tenant e leggibile da E3.

## 8. Criteri di accettazione

1. Un'esecuzione agente di test produce una riga in `gravya_traces` e ≥1 segmento per ciascun `kind` (llm, tool, retrieval, decision): test d'integrazione su PostgreSQL di test, 100% dei tipi presenti.
2. `trace_id` propagato tra servizio Node e servizio Python e nei job: test che verifica lo stesso `trace_id` su entrambi i lati.
3. 100% delle tracce e dei segmenti ha `company_id` non nullo e un tenant non legge le tracce di un altro (test RLS).
4. Nessun attributo fuori whitelist (in particolare contenuti di prompt, risposte, argomenti o risultati dei tool) viene scritto: test con payload contenenti testo e PII.
5. Scrittura delle tracce non riuscita → l'esecuzione termina con successo e la perdita è contata; nello stesso scenario un mancato salvataggio dell'audit dei tool o del record di decisione blocca l'azione (fail-closed, DA-B2-04/DA-A3-07): test di non regressione, cioè il buffer fail-open di E1 non è usato per quei record.
6. Overhead p95 < 5 ms/segmento su benchmark (proposta da validare).
7. `trace_id` presente negli eventi di audit di A5 per il 100% delle chiamate LLM e tool: test.
8. Con i default di DECISIONS.md §5, una partizione di tracce oltre 90 giorni viene eliminata dal job di retention e una più recente no; i log degli accessi restano 12 mesi: test con orologio simulato. Cambiando la durata nel registro delle variabili di piattaforma (come superadmin) il job applica il nuovo valore senza rilascio e la modifica risulta versionata e auditata; con un valore non valido il job non cancella nulla (fail-closed): test.
10. Un admin di agenzia non può usare la route cross-tenant (403); un accesso del superadmin produce una riga nel log degli accessi; se il log non si salva l'accesso è negato: test.
11. Nei segmenti `tool` gli argomenti compaiono solo come `gravya.tool.args_hash`, mai in chiaro: test con argomenti contenenti PII.
9. L'header di correlazione rispetta il formato `traceparent` e gli attributi LLM/tool/agente usano i nomi `gen_ai.*` della whitelist: test.

## 9. Piano di implementazione

1. Fase 0: chiudere DA-E1-03, DA-E1-04, DA-E1-07 (con A5); limitazione agli aggregati nell'accesso cross-tenant (residuo di DA-E1-08); responsabile di ruoli e variabili di piattaforma (DX-14, da riportare).
2. Fase 1: schema `gravya_traces`/`gravya_trace_segments` con RLS e partizioni; helper di scrittura Node e Python con whitelist, redazione, buffer e fail-open.
3. Fase 2: segmenti LLM nel dispatch LLM di v2 e `trace_id` negli eventi di audit di A5.
4. Fase 3: segmenti tool in B2; propagazione del `trace_id` su HTTP interno e nei job.
5. Fase 4: segmenti retrieval e decisione (A3, C1, C3).
6. Fase 5: API di lettura per tenant, export verso E3, route superadmin con log degli accessi, job di retention che legge le durate dal registro delle variabili di piattaforma, test §8.

**Tecnologie:** PostgreSQL+RLS self-hosted in UE (lo stesso del resto di v2: DA-A1-01, DA-B1-06). Vocabolario GenAI semantic conventions e formato `traceparent` (DA-E1-05). Nessun SDK OpenTelemetry, nessun collector, nessun servizio di tracing o eval esterno, niente LangSmith (PV-02, DA-E3-09, DA-C1-05).

## 10. Test e valutazione

Unit (helper, whitelist, redazione, formato `traceparent`), integrazione su PostgreSQL di test con soli dati sintetici (criteri 1-5, 7-11; il 5 include il caso fail-closed, l'8 la modifica delle variabili di piattaforma, il 10 il log degli accessi), benchmark overhead (6), test di isolamento tenant (RLS) in lettura e scrittura.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Volume delle tracce che pesa sul PostgreSQL operativo | partizioni per mese, scrittura bufferizzata, DA-E1-03 |
| PII/contenuti dei clienti nelle tracce | whitelist per `kind`, contenuti mai in produzione (DA-E1-02); gravya-app#1925 |
| Instabilità dei nomi GenAI semconv (stato "Development") | nomi fissati in whitelist versionata; aggiornamento esplicito |
| Confusione tra fail-open delle tracce e fail-closed di audit/decisioni | record fail-closed fuori dal buffer di E1; criterio 5 |
| Doppia verità tracce vs audit | tabelle separate con scopi distinti, correlate da `trace_id` (DA-E1-07) |
| Nessun ecosistema di strumenti pronto (viste, flame graph) come con OTel | vista Timeline costruita in v2; costo accettato per PV-02 |
| Accesso cross-tenant fuori dalle istruzioni del titolare | solo superadmin, log degli accessi fail-closed, retention 12 mesi (DX-13); criterio 10 |
| Modifica errata di una durata di retention (cancellazione prematura) | variabili versionate e auditate, solo superadmin, fail-closed su valore non valido (DX-13); criterio 8 |
| Responsabile del registro delle variabili e dei ruoli non assegnato | dipendenza DX-14 (proposta A6) da riportare all'utente |

## 12. Stima e priorità

- **Taglia:** M per una costruzione da zero (schema, due helper, propagazione, job di retention parametrico, API di lettura); invariata dalle decisioni del 2026-11-03 (PostgreSQL self-hosted conferma lo scenario M). Diventa L solo se DA-E1-03 in futuro sceglie uno storage separato.
- **Dipendenze critiche:** DX-07 (nomi tenant/eventi); DX-14 (proposta A6, da riportare) per ruolo superadmin e registro delle variabili; F6 per il job di retention.
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
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` riga 55 (letta in v1.2): log ≥6 mesi solo per usi Allegato III; non applicabile a v2 (DX-11).

**Divergenze dal master plan (v1.3):** (1) niente OpenTelemetry come software, per PV-02; delle GenAI semantic conventions resta il vocabolario (DA-E1-05); (2) multi-tenancy come requisito primario, che il master non cita; (3) contenuti di prompt mai registrati in produzione, mentre l'eval GenAI tipicamente li richiede (DA-E1-02; E3 usa dati sintetici, DA-E3-08).

## Appendice B — Non verificato

- Piano `.claude/plans/2026-06-15-phoenix-wave-d-trace-timeline/README.md` e §F.1 citato: non letti.
- Stato di #264, #266, #1925: non verificato sul tracker.
- `docs/start/architecture.md`: non letto. `controlli-e-conformita.md`: letta solo la riga 55.
- Analisi in `gravya-app/docs/compliance/{gdpr,nis2,ai-act}`: non lette. Ruolo GDPR e classe AI Act ora decisi (DX-11); resta da verificare che le finalità dei metadati siano coperte dal contratto art. 28.
- Volume atteso delle tracce e sostenibilità sul PostgreSQL operativo.
- Se la cancellazione via pseudonimi soddisfi l'art. 17 GDPR.
- ID dei sottoprodotti E di guardrail telemetry/eval online.
- Soglia overhead 5 ms, dimensione del buffer e soglia di perdita anomala: proposte da validare.
- Chi realizza il registro delle variabili di piattaforma e il ruolo superadmin (DX-14 non decisa).
- Comportamento fail-closed del registro su valore non leggibile (ultimo valore valido): proposta, non verificata con F6/A6.

## Appendice C — Decisioni aperte

- **DA-E1-01 — OpenTelemetry vs Timeline DB-native.** **Decisa** (DX-02, PV-02, vedi [DECISIONS.md](DECISIONS.md)): tracing DB-native, niente OTel.
- **DA-E1-02 — Cattura contenuti prompt/risultati.** **Decisa** (2026-11-03, utente, vedi [DECISIONS.md](DECISIONS.md)): mai in produzione; un eventuale opt-in richiede DPIA e parere legale.
- **DA-E1-03 — Storage delle tracce.** Aperta. Opzioni: (A) stesse istanze PostgreSQL di v2, schema dedicato e partizionato; (B) database separato self-hosted in UE. Escluse da DA-B1-06/DA-E3-09: servizi SaaS ed extra-UE. Criterio: volume, costo operativo. Raccomandazione: A per l'ondata 1, rivalutare con i volumi reali.
- **DA-E1-04 — Rappresentazione di retrieval e decisione.** Aperta. Opzioni: (A) `kind` dedicati; (B) attributi su segmenti esistenti. Raccomandazione: A.
- **DA-E1-05 — GenAI semantic conventions come vocabolario.** **Decisa** (2026-11-03, utente, vedi [DECISIONS.md](DECISIONS.md)): ammessi i nomi GenAI semconv e il formato `traceparent`, senza SDK né export OTel. Adottata in §4.2 e §5.
- **DA-E1-06 — Retention per classe.** **Assorbita da DX-09** (vedi [DECISIONS.md](DECISIONS.md)): politica unica di default con durate approvate (DECISIONS.md §5, 2026-11-03), modificabili dal superadmin (DX-13), override per classe/tenant previsti ma non attivi. Le classi proposte nella v1.2 (90 giorni, ≥6 mesi Allegato III) sono ritirate.
- **DA-E1-07 — Tracce e audit: tabelle separate o comuni.** Aperta. Opzioni: (A) separate, correlate da `trace_id`; (B) estendere la tabella di audit di A5. Raccomandazione: A (da allineare con A5).
- **DA-E1-08 — Accesso cross-tenant degli operatori alle tracce.** **Decisa nell'impianto da DX-13** (2026-11-03, utente): accesso solo del superadmin di istanza, entro le istruzioni del titolare (art. 28), con log degli accessi (12 mesi). Resta aperto il solo residuo dell'opzione C, cioè se limitare il superadmin ai dati aggregati senza identificativi salvo richiesta del tenant: **DA RIPORTARE ALL'UTENTE**. Raccomandazione: sì, aggregati di default, accesso alle singole tracce solo su richiesta o istruzione del tenant.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: sezioni 6-12 riordinate secondo il template (aggiunta §6 Comportamento ricavata dal contenuto esistente; Decisioni aperte spostate dalla §9 all'Appendice C, eliminando il duplicato); aggiunti in §3 i sottoprodotti che dichiarano di emettere span; in §4.1 aggiunti gli attributi che A3, E2, E3 e C1 dichiarano di emettere (`gravya.policy.*`, `gravya.prompt.key/version/hash` al posto di `gravya.prompt.ref`, `gravya.eval.*`, `gravya.workflow.*`). Motivo: allineamento delle interfacce tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Riprogettazione per DX-02 / PV-01 / PV-02 (niente OpenTelemetry, conformità prevalente sul master plan) e DX-01 / PV-03 (ripartenza da zero). Rimossi OTel, OTLP, collector, `traceparent` come scelta e gli span OTel: §2, §4-6 e §9 ora descrivono un tracing DB-native (tabelle `gravya_traces`/`gravya_trace_segments`, `trace_id` generato da Gravya, RLS per tenant, partizioni per la retention, export interno verso E3); attributi `gen_ai.*` sostituiti da `gravya.llm.*`; aggiunta §4.3 su cosa si cattura e cosa no; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50 e 12/14/19, osservabilità AI); criteri §8, rischi §11 e taglia §12 ricalcolati per una costruzione da zero; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti, non riuso); Appendice C: DA-E1-01 chiusa da DX-02, DA-E1-02/03/04 riformulate, nuove DA-E1-05..08. |
| 1.3 | 2026-11-03 | Allineamento alle decisioni dell'utente del 2026-11-03. DA-E1-02 (contenuti mai in produzione) e DA-E1-05 (vocabolario GenAI semconv e formato `traceparent`, senza SDK OTel) diventano scelte: attributi LLM/tool/agente rinominati da `gravya.llm/tool/agent.*` a `gen_ai.*`, header di correlazione in formato `traceparent`. Recepite DA-A1-01 e DA-B1-06 (PostgreSQL self-hosted UE), DA-C1-01/05, DA-E3-08/09, DA-B2-07 (`gravya.tool.destination`). DA-E1-06 assorbita da DX-09: rimosse le durate proposte, elencate in §4.1 le classi di dati prodotte. §7 allineata a DX-10 (notifica NIS2 di A5, E1 invia segnali) e DX-11 (Gravya responsabile art. 28; artt. 12/14/19/26 AI Act solo buona pratica, art. 50 resta); tolte le ipotesi relative dall'Appendice B. Fail-open limitato alle tracce, con distinzione esplicita dal fail-closed di DA-B2-04/DA-A3-07 in §5-§8 e §10. Criteri 5, 8 e nuovo 9 aggiornati; taglia M confermata. |
| 1.4 | 2026-11-03 | Recepite le decisioni dell'utente del 2026-11-03: durate di default DX-09 (DECISIONS.md §5) in §4.1 e §7 (90 giorni tracce/segmenti, 12 mesi log accessi ed eval); DX-13: ruolo superadmin per l'accesso cross-tenant con log (DA-E1-08 decisa nell'impianto, residuo sugli aggregati da riportare) e soglie/durate come variabili di piattaforma versionate, auditate e fail-closed (§5); riga decisa di DECISIONS.md §6: argomenti dei tool solo come hash (`gravya.tool.args_hash`); base giuridica distinta per superadmin e dati delle agenzie. Dipendenze da F6 e da DX-14 (proposta A6, da riportare). Criterio 8 riscritto, nuovi criteri 10-11, rischi, Fase 0, §12 e Appendici B/C aggiornati. |
