# E1 — Tracing distribuito

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E1 |
| Nome | Tracing distribuito |
| Componente padre | E — Osservabilità e Valutazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.5 |
| Data | 2026-11-04 |

## 2. Scopo

**Cosa fa.** Registra ogni esecuzione agente come una traccia **DB-native** (PV-02, DX-02): un `trace_id` generato da Gravya all'avvio del run e una serie di segmenti correlati per chiamata LLM, invocazione tool, retrieval e punto di decisione (policy, HITL, router). Le tracce stanno in tabelle PostgreSQL self-hosted in UE sotto il controllo diretto di Gravya, isolate per tenant. Il vocabolario degli attributi usa i nomi delle GenAI semantic conventions (`gen_ai.*`) per LLM, tool e agenti e il namespace `gravya.*` per il resto (§4.2); la correlazione usa il formato W3C `traceparent` (DA-E1-05, decisa). Non si usa OpenTelemetry come software (né SDK, né OTLP, né collector, né export): del master plan resta solo il vocabolario.

**Cosa NON fa.** Non è l'eval harness (E3), non è il registry dei prompt (E2), non sostituisce l'audit (A5; nell'ondata 1 la tabella di audit minima, DECISIONS §6), non è error tracking (resta GlitchTip). Non invia tracce a vendor o piattaforme SaaS di tracing o eval. Non possiede il log degli accessi cross-tenant (è di A6, DX-18) né la mappa degli pseudonimi. Non notifica incidenti: invia segnali ad A5. Non è la prova della marcatura «generato da AI» né il registro delle decisioni di enforcement: sono audit fail-closed di altri sottoprodotti (§7).

**Perché esiste.** PV-01 (l'osservabilità AI è priorità di progetto) e master plan, principio 1: senza tracing non si fanno eval, senza eval non si concede autonomia.

## 3. Contesto e dipendenze

**Dipende da:**
- **F6** (politica di retention e cancellazione, DX-12, ondata 2): job di retention, intervalli `_min`/`_max` del DPA, classi di backup, sospensione per evidenze di incidente. Finché F6 non esiste valgono i default del catalogo, di sola lettura (DX-09, DA-CV-01).
- **A6** (identità, ruoli e configurazione, DX-14, ondata 2): registro versionato delle variabili (DX-13), ruoli superadmin e admin agenzia con MFA (DX-20), log degli accessi cross-tenant (DX-18), identità pseudonima dell'attore (DX-21), `config_version`. Finché A6 non esiste: l'istantanea delle variabili è un file versionato nel repository (ripiego dell'ondata 1, catalogo §17.1 punto 9) e la route cross-tenant non è esposta (§5).
- **A5** (audit trail e notifiche NIS2, DX-10, ondata 2): riceve i segnali; nell'ondata 1 i segnali vanno nella tabella di audit minima.
- DX-07 (nomi di tenant ed eventi) e DX-03/DX-04 per il trasporto e i contratti condivisi Node-Python: aperte.
- Per popolare i segmenti: B1, B2, C1, A3, C3, E2, E3 (tabella 4.2).

**È richiesto da:** B1, B2, C1, A3, C3 (emettono segmenti), E2 (riferimento prompt nei segmenti LLM), E3 (legge le tracce `root_kind=eval`), A1 (scrive il `trace_id` nell'audit delle mutazioni dentro un run: non emette segmenti, DECISIONS §4), A5 (correlazione per `trace_id`), A6 (consuma la classe e usa le viste aggregate), E4, E5, E6 (ondata 3).

**Assunzioni (non verificate):** v2 avrà un servizio Node e un servizio Python che condividono PostgreSQL e una coda di job, e che propagano il `trace_id` su HTTP interno e nei job.

## 4. Contratti

### 4.1 Modello dati (DB-native)

Due tabelle, entrambe con `company_id` obbligatorio e Row-Level Security per tenant (nomi proposti, da validare con DX-07):

- **`gravya_traces`**: una riga per run. `trace_id` (UUID generato da Gravya), `company_id`, `run_id`, `execution_ticket_id`, `root_kind` (agent/workflow/eval), `started_at`, `ended_at`, `status`, `workflow_id`/`workflow_version` se presenti, `retention_class` (aggancio per l'override per classe, non attivo: `retention.class_override_enabled`).
- **`gravya_trace_segments`**: una riga per operazione. `segment_id`, `trace_id`, `parent_segment_id`, `company_id`, `kind`, `name`, `started_at`, `ended_at`, `status`, `attributes` (JSONB, whitelist di chiavi **e di valori** per `kind`, §4.2), `redaction_version`.

Tabelle **separate dall'audit** (A5): scopo, accesso e retention diversi; si correlano per `trace_id` (DA-E1-07, aperta: ipotesi di lavoro). Partizionamento per tempo con intervallo `e1.partition_interval_months`; la retention per partizione elimina una partizione solo quando l'intero intervallo è più vecchio di `retention.traces_days`, quindi una riga vive al più `retention.traces_days` più un intervallo di partizione, e questa somma non supera `retention.traces_days_max` (D5; catalogo §1 regole 8c e 8d). Dove una durata non coincide con la partizione (valore per agenzia `retention.traces_days.tenant_value` con override attivo, fine contratto, cancellazione per interessato) la cancellazione è **per riga**; con l'override attivo la partizione si elimina solo se tutte le righe sono scadute per i rispettivi tenant (dedotto; F6 conferma). Storage: lo stesso PostgreSQL self-hosted in UE del resto di v2 (DA-A1-01, DA-B1-06); DA-E1-03 resta aperta solo sull'eventuale separazione per volume.

**Classi di dati prodotte da E1** (DX-09; i valori stanno nel catalogo, le durate sono di sola lettura finché non esiste l'intervallo del DPA, DA-CV-01):

| Classe | Variabile di retention |
|---|---|
| Righe di traccia e segmenti con metadati, compresi i segmenti `decision` con lo pseudonimo del revisore HITL (dato personale, §4.3) | `retention.traces_days` |
| Segmenti `eval_case`, tracce `root_kind=eval` e file di export verso E3 (dati sintetici) | `retention.eval_reports_months` |
| Contatori di perdita e di scarto dei segmenti | `retention.traces_days` (assegnazione proposta da validare, catalogo §2) |
| Segnali verso A5 prodotti da E1 | `retention.incident_signals_months` (da definire, F6 o A6; sempre conservati, C2) |
| Copie di backup | `retention.data_backup_days`; per i registri `retention.log_backup_months` (da definire, F6/A5) |
| Mappa pseudonimo-persona | non in E1: `retention.pseudonym_map_months` (da definire, F6) |

Non sono classi di E1: il log degli accessi cross-tenant (A6, `retention.cross_tenant_access_log_months`) e l'audit delle variabili (A6, `retention.config_audit_months`).

**Evidenze di incidente** (`retention.incident_evidence_months`). La sospensione delle scadenze **non è attivabile** finché massimo, riesame e categorie non sono definiti (D5, catalogo §1 regola 12); per i dati delle agenzie servono l'istruzione del titolare nel DPA e un parere legale prima di F6 (DA-CV-21). Come una traccia sospesa esce dal drop di partizione è di F6 e A5: non deciso.

**Fine contratto.** Le tracce di un'agenzia seguono `retention.tenant_offboarding_days` (periodo minimo, Data Act art. 25(2)(g)-(h), ✔ registro v1.6, se il SaaS è un «servizio di trattamento dei dati»: da confermare con un legale) e la scelta `retention.tenant_offboarding_choice` dell'agenzia (restituzione o cancellazione, GDPR art. 28(3)(g)). E1 fornisce l'export per tenant e la cancellazione per riga; l'ordine esportazione poi cancellazione è di F6.

### 4.2 Tipi di segmento

I nomi `gravya.*` sono proposti (DX-07 aperta); `config_version` è il nome unico di DX-21. I nomi `gen_ai.*` si fissano sulla versione delle convenzioni in vigore all'implementazione (stato «Development», possono cambiare): solo vocabolario, nessun SDK né export OTel.

| `kind` | Attributi ammessi (whitelist) | Emesso da |
|---|---|---|
| `llm` | `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gravya.prompt.key/version/hash` (E2), `gravya.llm.destination` (destinazione dichiarata con giurisdizione, DA-B2-07) | B1 / dispatch LLM |
| `tool` | `gen_ai.tool.name`, `gen_ai.tool.call.id` (identificativo opaco), esito (`ok`, `denied`, `approval_required`, `rate_limited`, `error`), `gravya.tool.destination` (DA-B2-07), `gravya.tool.args_hash` (solo hash degli argomenti, DA-C3-06 (a)), `gravya.decision.id` (identificativo del record di decisione di A3) | B2 |
| `agent` | `gen_ai.agent.id`, `gen_ai.agent.name` (riferimento al catalogo degli agenti) | B1 |
| `retrieval` | `gravya.retrieval.source` (identificativo di sorgente), `gravya.retrieval.results_count` (nessun contenuto) | pipeline memoria |
| `decision` | `gravya.decision.kind` (`policy`, `hitl`, `router`), `gravya.decision.outcome` (vocabolario chiuso per `kind`), `gravya.decision.id`, `config_version` (DX-21); se `policy`: `gravya.policy.bundle_version`, `gravya.policy.bundle_hash`; se `hitl`: `gravya.decision.reviewer_ref` (pseudonimo fornito da A6) e `gravya.decision.args_hash`; se emesso da C1: `gravya.workflow.id`, `gravya.workflow.version`, `gravya.workflow.node_id` | A3, C3, C1 |
| `eval_case` | `gravya.eval.case_id`, `gravya.eval.pass` | E3 |

**Vocabolari di `gravya.decision.outcome`.** `policy`: `allow`, `deny`, `require_approval` (A3 §4). `hitl`: `requested`, `approved`, `denied`, `input_provided`, `expired`, `outcome`, una per transizione di C3 (nomi come C3 §4.4, da allineare a DX-07). `router`: valori definiti da C1 (da allineare).

**Validazione di chiavi e valori (whitelist versionata, `redaction_version`).** Ogni chiave ha tipo, insieme chiuso o formato: gli identificativi sono opachi; gli hash hanno il formato fissato; `name`, sorgenti, esiti e codici di errore sono valori di un vocabolario chiuso, non testo libero; la lunghezza massima di un valore è `e1.attributes.max_value_bytes`. Un attributo fuori whitelist o un valore non conforme viene scartato (§6). Formato dell'hash, whitelist, nomi degli header e formato `traceparent` sono invarianti (catalogo §18, DA-CV-05 (a)).

### 4.3 Contenuti: cosa si cattura e cosa no

| Si cattura | Non si cattura |
|---|---|
| metadati di esecuzione: tempi, esiti, modelli, token, identificativi di prompt/policy/workflow, `config_version`, codici di errore da vocabolario | testo di prompt e risposte, argomenti e risultati dei tool, documenti recuperati, contenuto dei messaggi dei clienti, nomi, email, telefoni o altri dati personali in chiaro |
| identificativi pseudonimi (agente, revisore, ticket), hash degli argomenti | destinatari finali di messaggi e dati di tracciamento (aperture, clic): materia di D1-D4 |

Decisione DA-E1-02: i contenuti **non si catturano mai in produzione** (invariante, catalogo §18); gli argomenti dei tool nelle tracce compaiono solo come hash (DA-C3-06 (a)), anche per la chiamata parcheggiata da HITL; un eventuale opt-in futuro richiede DPIA e parere legale e oggi non ha variabile. Negli ambienti di sviluppo e di eval solo dati sintetici (DA-E3-08).

**Gli identificativi pseudonimi sono dati personali.** Per il considerando 26 GDPR (✔ registro) un identificativo attribuibile a una persona con informazioni aggiuntive, in mano a Gravya, all'agenzia o a un terzo, resta dato personale; la pseudonimizzazione è una misura (artt. 25 e 32), non un'esenzione. Le linee guida EDPB 01/2025 sono solo una bozza in consultazione e non si citano come requisito. Quindi i segmenti `decision` e le tracce hanno retention limitata, accesso ristretto (§5) e cancellazione per interessato (§6). Anche `args_hash` di argomenti a bassa entropia può essere riconducibile all'argomento: DA-E1-09.

## 5. Interfacce

- **Scrittura:** helper per linguaggio (`startSegment`/`endSegment`, Node e Python) che impone `company_id` e `trace_id`, valida chiavi e valori contro la whitelist del `kind` e scrive in modo asincrono e bufferizzato (`e1.write_buffer_size`). Fail-open per le tracce (§7); i record di audit e di decisione sono fail-closed e non passano da questo buffer. Il writer scrive per più tenant: ruolo senza bypass di RLS, tenant impostato per ogni transazione e `WITH CHECK` sulle policy (DA-E1-10).
- **Correlazione:** `trace_id` generato da Gravya, propagato sulle chiamate HTTP interne negli header `x-gravya-trace-id` e `x-gravya-parent-segment-id` e in un campo dei job. Il valore del `trace_id` è l'UUID reso come 32 cifre esadecimali, nel formato W3C `traceparent`, senza SDK OTel (DA-E1-05). Nomi e formato sono invarianti (catalogo §18). Lo stesso `trace_id` è scritto negli eventi di audit di A5 (chiamate LLM, invocazioni tool) e nell'audit delle mutazioni di A1 dentro un run.
- **Lettura applicativa:** API interna filtrata per tenant (RLS) per la vista Timeline del tenant; gli admin delle agenzie leggono solo il proprio tenant.
- **Export verso E3:** E3 legge le sole tracce `root_kind=eval` (dati sintetici, DA-E3-08) con vista o export JSONL versionato; le tracce di produzione non escono. Nessun export verso piattaforme di eval o servizi gestiti (DA-E3-09, DA-C1-05).
- **Accesso del superadmin (DX-13, DX-18, DX-19, DX-20).** (1) **Di default solo dati aggregati senza identificativi**, con dimensione minima di gruppo `access.aggregate_min_group_size_count`; è imposto dal database (viste aggregate e ruolo dedicato senza accesso alle tabelle base) e non da un filtro applicativo (DA-E1-11). (2) **Singola traccia** solo su richiesta dell'agenzia o per un incidente, con riferimento alla richiesta o al caso, per la durata `access.superadmin_trace_access_ttl_hours`; la lettura delle singole tracce è di tracce che contengono pseudonimi, quindi dati personali, e resta entro le istruzioni del titolare (art. 28). (3) MFA obbligatoria (DX-20). (4) Ogni accesso è registrato **nel log di A6** (chi, quando, tenant, traccia o filtro, motivo): E1 lo usa e non lo possiede. Se il log non si salva l'accesso è negato (fail-closed; da confermare con A6). Finché A6 non esiste la route non è esposta.
- **Variabili (DX-13, DX-22).** Durate, soglie e parametri si leggono dal registro delle variabili e si citano per nome: `retention.*` (§4.1), `e1.partition_interval_months`, `e1.write_buffer_size`, `e1.overhead_p95_ms`, `e1.attributes.max_value_bytes`, `access.*`. **Valore non leggibile o non valido (DX-17):** le azioni si bloccano; il job di retention usa l'**ultimo valore valido versionato** (i dati non restano oltre la scadenza nota) e parte un segnale ad A5. Una combinazione che viola la regola `retention.traces_days` + partizione ≤ massimo è non valida. Primo avvio senza valore valido: per le classi con valore «deciso» vale il default del catalogo; una classe «da definire» non si scrive in produzione (DA-CV-17).
- **Segnali ad A5 (DA-CV-07 (b)).** E1 non ha soglie locali: invia ogni evento rilevante, sempre prodotto e conservato anche con `incident.nis2_flow_active` falso (C2): perdita di segmenti, scarto di attributi fuori whitelist in produzione, valore di variabile non leggibile, scrittura delle tracce non disponibile. Nell'ondata 1 la destinazione è la tabella di audit minima.

## 6. Comportamento

**Flusso principale:**
1. All'avvio di un run il chiamante (B1; C1 per un workflow eseguito con LangGraph come libreria self-hosted, DA-C1-01; E3 per un caso di eval) genera il `trace_id` e scrive la riga in `gravya_traces` tramite l'helper.
2. Le chiamate verso altri servizi propagano `trace_id` e segmento padre; i segmenti figli si agganciano alla stessa traccia.
3. Ogni segmento è validato, accodato nel buffer e scritto in PostgreSQL.
4. A fine run la traccia si chiude con `ended_at` e `status`; A5 riporta il `trace_id` nei propri eventi.

**Casi limite:**
- **Scrittura non riuscita** (DB lento, buffer pieno): l'esecuzione prosegue (fail-open), la perdita è contata e segnalata ad A5. Non vale per l'audit dei tool (DA-B2-04) né per il record di decisione di A3 (DA-A3-07): fail-closed, fuori da E1. Il segmento `decision` è un riflesso osservabile: la sua perdita non sblocca né blocca nulla. Per questo l'attribuzione di prompt, modello e `config_version` a un'azione irreversibile non può poggiare solo sulla traccia: DA-E1-12.
- **Contenuti o valori non conformi:** un payload con contenuti di prompt o risposta, o con un valore fuori formato, in sviluppo e test fa fallire la scrittura; in produzione l'attributo è scartato, contato e segnalato ad A5.
- **Segmento senza `company_id`** o con `company_id` diverso da quello del contesto: rifiutato dal `WITH CHECK` e dall'helper.
- **Richiesta di cancellazione di un interessato** (GDPR art. 17) o fine contratto: cancellazione per riga dei segmenti e delle tracce collegati; per gli pseudonimi si agisce sulla mappa (A6/F6, `retention.pseudonym_map_months`). Non è verificato che basti a rendere i segmenti non più riconducibili: procedura da definire con A5, A6 e F6 (App. B). Le tracce non sono modificabili dopo la chiusura salvo cancellazione per retention, per diritto o per fine contratto.

## 7. Requisiti non funzionali

- **Multi-tenancy:** `company_id` su ogni traccia e segmento; RLS in lettura e scrittura (motivo dello scarto di Phoenix, #266).
- **PII:** minimizzazione a monte (whitelist di chiavi e valori); `redactAll` di gravya-app è solo key-based e non basta per il testo libero, ma con la whitelist il testo libero non entra.
- **Overhead:** latenza aggiunta p95 non superiore a `e1.overhead_p95_ms` per segmento (scrittura asincrona).
- **Fail-open (solo tracce)**, come in §6.
- **Retention:** DX-09, classi e variabili in §4.1; applicazione di F6.
- **Sicurezza e conformità:**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28, DX-11). Solo metadati e pseudonimi (§4.3); contenuti mai in produzione. Finalità e istruzioni sono quelle del titolare nel DPA: l'uso dei metadati per scopi propri di Gravya (qualità del prodotto, addestramento) non è coperto senza istruzione e rischierebbe la riqualificazione come titolare (art. 28(10), registro); che il DPA copra sicurezza, qualità e fatturazione non è verificato. Il termine verso le agenzie per una violazione (per esempio accesso non autorizzato alle tracce) è un obbligo del DPA, senza ore nell'art. 33(2) (`incident.gdpr.processor_notice_hours`, valore aperto: DA-CV-08). Diritti: export per tenant e cancellazione per riga, a supporto del titolare. Dati in UE nello stesso PostgreSQL self-hosted (DA-B1-06); nessun trasferimento a terzi o a servizi di tracing o eval. I segmenti `llm` e `tool` riportano la destinazione dichiarata, così un trasferimento extra-UE è verificabile (DA-B2-07, D5, D7). Cifratura e backup: nessuna policy di v2 è definita (App. B).
  - *Sicurezza dei sistemi (progettazione «NIS2 compliant ready by design», DX-10).* Gravya oggi non è soggetto NIS2; le misure sotto sono requisiti di progetto del Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11 (✔ registro), valide solo se Gravya fosse fornitore cloud in ambito. Registrazione delle attività (3.2.1) con tempi da origini sincronizzate (3.2.6, `security.clock_skew_max_ms`, A5); protezione dei registri da accessi e modifiche non autorizzati (3.2.5): RLS, writer senza bypass, nessuna modifica dopo la chiusura; copie di backup per un periodo predefinito (`retention.log_backup_months`); accessi privilegiati registrati e MFA (11.3, DX-20, A6). Se le tracce siano «registri» ai sensi di 3.2.5 è interpretazione. E1 non notifica: invia segnali ad A5 (§5), che gestisce preallarme 24 h, notifica 72 h, relazione finale entro un mese e destinatario CSIRT Italia, con decorrenza dalla conoscenza; flusso non attivo finché `incident.nis2_flow_active` è falso, segnali sempre prodotti. L'art. 21 della direttiva non nomina i log: non si cita per i log.
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11). L'art. 50 si applica dal 2.8.2026 (✔ registro): E1 non interagisce con gli utenti e registra quale modello e quale prompt hanno prodotto un output, ma la traccia, fail-open e a retention limitata, **non è la prova** dell'etichetta «generato da AI» né della marcatura leggibile da macchina (art. 50(2), anche per il testo: dettaglio in C1 e D1-D4). Gli artt. 12, 14, 19, 26 non sono obbligatori e per l'alto rischio varrebbero dal 2.12.2027 (Reg. 2026/1744); la registrazione delle decisioni HITL resta buona pratica, senza durate minime imposte (non si usa il riferimento di 6 mesi dell'art. 19).
  - *Osservabilità AI:* per ogni run modello richiesto e risposto, token, latenza, versioni di prompt, policy e workflow, `config_version`, esiti dei tool, decisioni di policy e HITL, punteggi di eval, interrogabili per tenant. Il costo non ha un attributo (App. B).

## 8. Criteri di accettazione

1. Un'esecuzione agente di test produce una riga in `gravya_traces` e almeno un segmento per ciascun `kind` (llm, tool, retrieval, decision): test d'integrazione su PostgreSQL di test, tutti i tipi presenti.
2. `trace_id` propagato tra servizio Node e servizio Python e nei job: stesso valore su entrambi i lati.
3. Ogni traccia e segmento ha `company_id` non nullo; un tenant non legge le tracce di un altro; una scrittura con `company_id` diverso dal contesto è rifiutata (`WITH CHECK`): test RLS in lettura e scrittura.
4. Nessun attributo fuori whitelist e nessun valore fuori formato viene scritto, in particolare contenuti di prompt, risposte, argomenti o risultati dei tool: test con payload contenenti testo e PII. In produzione l'attributo è scartato e un segnale arriva ad A5.
5. Scrittura delle tracce non riuscita: l'esecuzione termina con successo, la perdita è contata e segnalata ad A5; nello stesso scenario un mancato salvataggio dell'audit dei tool o del record di decisione blocca l'azione (DA-B2-04, DA-A3-07). Il buffer di E1 non è usato per quei record.
6. Overhead p95 per segmento non superiore a `e1.overhead_p95_ms` su benchmark.
7. `trace_id` presente negli eventi di audit di A5 (nell'ondata 1, nella tabella di audit minima) per tutte le chiamate LLM e tool: test.
8. **Retention.** Con i valori del catalogo letti dal registro, una partizione il cui intervallo è più vecchio di `retention.traces_days` è eliminata e una più recente no; `retention.eval_reports_months` vale per le tracce `root_kind=eval`: test con orologio simulato. Con valori di prova che violano `retention.traces_days` più `e1.partition_interval_months` ≤ `retention.traces_days_max`, o fuori da `_min`/`_max`, il valore è non valido. Con un valore non leggibile o non valido il job usa l'ultimo valore valido versionato e un segnale arriva ad A5; con nessun valore valido vale il default del catalogo per le classi «deciso». Una modifica di variabile (come superadmin, quando consentita) è applicata senza rilascio e risulta versionata e auditata.
9. L'header di correlazione ha il formato `traceparent` e i nomi concordati; gli attributi LLM, tool e agente usano i nomi `gen_ai.*` della whitelist: test.
10. Un admin di agenzia non può usare la route cross-tenant (403). Il superadmin vede per default solo aggregati: un gruppo sotto `access.aggregate_min_group_size_count` non è restituito e il ruolo non legge le tabelle base (test sul ruolo DB). La singola traccia richiede il riferimento alla richiesta o al caso, scade dopo `access.superadmin_trace_access_ttl_hours` e produce una riga nel log di A6; se il log non si salva l'accesso è negato: test.
11. Nei segmenti `tool` e `decision` gli argomenti compaiono solo come hash, mai in chiaro: test con argomenti contenenti PII.
12. I segmenti `decision` di policy e HITL portano `config_version`, `gravya.decision.kind`, `gravya.decision.outcome` dal vocabolario e `gravya.decision.id`: test su 100% dei segmenti di prova.
13. E3 legge solo tracce `root_kind=eval`; la richiesta di una traccia di produzione è rifiutata: test.
14. Cancellazione per tenant e per interessato: dopo la cancellazione per riga nessun segmento del tenant o dello pseudonimo resta; con `retention.tenant_offboarding_days` come minimo, la cancellazione non precede il periodo di recupero: test con dati sintetici.

## 9. Piano di implementazione

1. Fase 0: chiudere DA-E1-09..12; DA-E1-03, DA-E1-04, DA-E1-07 (con A5); concordare con F6 e A6 i punti dell'ondata 2 (§3); allineare `gravya.decision.outcome` con A3, C1, C3 e gli attributi con B1, B2, E2.
2. Fase 1: schema, RLS con `WITH CHECK`, partizioni con `e1.partition_interval_months`; helper Node e Python con whitelist di chiavi e valori, buffer e fail-open.
3. Fase 2: segmenti LLM nel dispatch di v2 e `trace_id` negli eventi di audit.
4. Fase 3: segmenti tool in B2; propagazione su HTTP interno e nei job.
5. Fase 4: segmenti retrieval e decisione (A3, C1, C3) con `config_version`.
6. Fase 5: API di lettura per tenant, export `root_kind=eval` per E3, job di retention per partizione e per riga con regola DX-17, viste aggregate; route superadmin quando A6 è disponibile; test §8.

**Tecnologie:** PostgreSQL+RLS self-hosted in UE (DA-A1-01, DA-B1-06). Vocabolario GenAI semantic conventions e formato `traceparent` (DA-E1-05). Nessun SDK OpenTelemetry, collector, servizio di tracing o eval esterno, niente LangSmith (PV-02, DA-E3-09, DA-C1-05).

## 10. Test e valutazione

Unit (helper, whitelist di chiavi e valori, formato `traceparent`, regola delle durate), integrazione su PostgreSQL di test con soli dati sintetici (criteri 1-5, 7-14), benchmark overhead (6), test di isolamento tenant e del ruolo aggregato. I campioni dei test sono parametri dei test e citano il catalogo (DA-CV-04 (b)).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Volume delle tracce sul PostgreSQL operativo | partizioni, scrittura bufferizzata, DA-E1-03 |
| PII o contenuti nelle tracce, pseudonimi riconducibili | whitelist di chiavi e valori, contenuti mai in produzione, retention limitata, DA-E1-09 |
| Cancellazione per riga costosa o retention per partizione disallineata dai valori per agenzia | regola `retention.traces_days` più partizione ≤ massimo; cancellazione per riga dove serve; criterio 8 e 14 |
| Instabilità dei nomi GenAI semconv | nomi fissati in whitelist versionata |
| Confusione tra fail-open delle tracce e fail-closed di audit e decisioni | record fail-closed fuori dal buffer; criterio 5; DA-E1-12 |
| Doppia verità tracce e audit | tabelle separate, correlate da `trace_id` (DA-E1-07) |
| Nessun ecosistema di strumenti pronto come con OTel | vista Timeline costruita in v2; costo accettato per PV-02 |
| Accesso del superadmin oltre le istruzioni del titolare | aggregati di default imposti dal DB, singola traccia su richiesta o incidente, log di A6 fail-closed, MFA; criterio 10 |
| Modifica errata di una durata | durate di sola lettura finché manca l'intervallo del DPA; poi solo entro `_min`/`_max`; versionate e auditate |
| Dipendenze dell'ondata 2 (A5, A6, F6) non pronte | ripieghi dichiarati: istantanea delle variabili, tabella di audit minima, route cross-tenant non esposta |

## 12. Stima e priorità

- **Taglia:** M (schema, due helper, propagazione, job di retention per partizione e per riga, viste aggregate, API di lettura). Diventa L solo se DA-E1-03 sceglie uno storage separato.
- **Dipendenze critiche:** DX-07; A6 (variabili, ruoli, log, pseudonimi); F6 (retention); A5 (segnali).
- **Thin-slice MVP:** sì, ondata 1.

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna `gravya-app` (riferimento, non codice da riusare: DX-01, PV-03). Ripresi dalla v1.4, non riletti nel codice per la v1.5.
- `server/src/services/timeline-engine.ts`: Timeline DB-native su `gravya_event_logs`, «NO OpenTelemetry, NO new vendor». *Da riprendere:* tracing nel DB del prodotto, proiezione PII-safe con whitelist. *Da non ripetere:* nessun `trace_id`, correlazione euristica (#264), tracce e audit nella stessa tabella.
- `server/src/routes/superadmin-observability.ts`: route cross-tenant con `assertInstanceAdmin` e bypass RLS. *Da riprendere:* accesso separato protetto da ruolo. *Da non ripetere:* bypass di RLS applicativo; in v2 viste aggregate e log di A6.
- `server/src/observability/error-tracking.ts`: Sentry→GlitchTip solo errori. *Lezione:* error tracking distinto dal tracing.
- `services/agents/src/councils/runtime.py`: hook OTel opzionale mai attivato. *Da non ripetere:* in v2 l'helper è obbligatorio.
- `server/src/routes/llm-dispatch.ts` e `server/src/services/audit-event-kinds.ts`: un unico punto di dispatch LLM come aggancio.
- `services/agents/src/tools/_audit.py`: coppia begin/end per tool.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` (~r.178): Phoenix adottato 13/04, scartato 15/06 per multi-tenancy debole (#266). *Lezione:* le piattaforme di tracing esterne falliscono sull'isolamento per tenant.

**Divergenze dal master plan:** (1) niente OpenTelemetry come software, solo il vocabolario (PV-02, DA-E1-05); (2) multi-tenancy come requisito primario; (3) contenuti di prompt mai registrati in produzione (DA-E1-02; E3 usa dati sintetici, DA-E3-08).

## Appendice B — Non verificato

- File di gravya-app e kloudify dell'Appendice A, #264, #266, #1925: non riletti per la v1.5.
- Se la cancellazione per riga e la cancellazione della mappa rendano i segmenti non più riconducibili a una persona (art. 17); la valutazione di anonimato dei trace con il DPO (linee guida EDPB 02/2026 non lette nel registro).
- Se le tracce siano «registri» ai sensi del Reg. 2024/2690 allegato 3.2.5, e se rientrino tra i «dati esportabili» del Data Act (art. 2(38)); se il SaaS sia un «servizio di trattamento dei dati» e il divieto di costi di passaggio dal 12.1.2027 (art. 29).
- Se il DPA con le agenzie copra le finalità dei metadati; se l'infrastruttura self-hosted poggi su un provider terzo, da censire come sub-responsabile (D7).
- Policy di cifratura e di backup di v2: non definita in alcun documento; backup e propagazione delle cancellazioni: DA-CV-22, F6.
- Il fail-closed del log degli accessi cross-tenant (A6) e la route non esposta in ondata 1: proposte, da confermare con A6. Meccanismo con cui F6 e A5 sottraggono una traccia sospesa al drop di partizione: non deciso.
- `gravya.llm.destination`, `gravya.retrieval.*`, `gravya.decision.id`, `gravya.decision.reviewer_ref`, `gravya.decision.args_hash`: nomi proposti da E1; i vocabolari di `outcome` per `router` (C1) e `hitl` (C3, nomi `hitl_*`) vanno allineati. Formato del `parent-id` di `traceparent` (16 cifre) rispetto a `x-gravya-parent-segment-id`: non definito.
- Costo per run: non ha un attributo (calcolo a valle da token e modello, con E6, ondata 3).
- Unità di `e1.write_buffer_size` (segmenti o byte); valori di `e1.attributes.max_value_bytes`, `e1.overhead_p95_ms`, `e1.partition_interval_months`: proposte da validare nel catalogo; `retention.traces_days_max` non è definito, quindi la regola «durata più partizione ≤ massimo» non è valutabile con i valori reali.
- Volume atteso delle tracce e sostenibilità sul PostgreSQL operativo.
- I vocabolari e i nomi di attributi di A3, C1 e C3 citati in §4.2 sono ripresi dai documenti v1.4 di quei sottoprodotti, che si aggiornano in parallelo.

## Appendice C — Decisioni aperte

- **DA-E1-01 — OpenTelemetry vs Timeline DB-native.** **Decisa** (DX-02, PV-02): tracing DB-native, niente OTel.
- **DA-E1-02 — Cattura contenuti prompt/risultati.** **Decisa** (2026-11-03, utente): mai in produzione; invariante.
- **DA-E1-03 — Storage delle tracce.** Aperta. Opzioni: (A) stesse istanze PostgreSQL di v2, schema dedicato e partizionato; (B) database separato self-hosted in UE. Escluse: SaaS ed extra-UE (DA-B1-06, DA-E3-09). Criterio: volume, costo operativo. Raccomandazione: A per l'ondata 1.
- **DA-E1-04 — Rappresentazione di retrieval e decisione.** Aperta in DECISIONS; usata come ipotesi di lavoro. Opzioni: (A) `kind` dedicati; (B) attributi su segmenti esistenti. Raccomandazione: A.
- **DA-E1-05 — GenAI semantic conventions come vocabolario.** **Decisa** (2026-11-03, utente): nomi GenAI semconv e formato `traceparent`, senza SDK né export OTel.
- **DA-E1-06 — Retention per classe.** **Assorbita da DX-09.**
- **DA-E1-07 — Tracce e audit: tabelle separate o comuni.** Aperta in DECISIONS; usata come ipotesi di lavoro. Opzioni: (A) separate, correlate da `trace_id`; (B) estendere la tabella di audit di A5. Raccomandazione: A (da allineare con A5).
- **DA-E1-08 — Accesso cross-tenant del superadmin.** **Decisa** (DX-13, DX-19, 2026-11-03): aggregati senza identificativi di default, singola traccia solo su richiesta o per incidente, log di A6 (DX-18).
- **DA-E1-09 — Hash degli argomenti.** Aperta. Opzioni: (a) hash semplice (formato invariante del catalogo §18); (b) HMAC con chiave per tenant, la cui distruzione rende l'hash non più riconducibile; (c) solo identificativo del record. Criterio: GDPR art. 4(5), considerando 26, art. 5(1)(e), art. 25; il confronto di uguaglianza (C3) resta possibile con (a) e (b). Raccomandazione: (b), con chiave nella pagina credenziali e sostituzione senza interruzione (DA-CV-23); richiede di modificare l'invariante sul formato. **DA RIPORTARE ALL'UTENTE.**
- **DA-E1-10 — Scrittura per più tenant e RLS.** Aperta. Opzioni: (a) writer senza bypass, tenant impostato per transazione, `WITH CHECK`; (b) ruolo con bypass e controllo applicativo; (c) un writer per tenant. Criterio: isolamento dichiarato da E1 §7. Raccomandazione: (a).
- **DA-E1-11 — Come si impongono gli aggregati al superadmin.** Aperta. Opzioni: (a) viste aggregate e ruolo DB senza accesso alle tabelle base; (b) filtro applicativo; (c) tabelle di aggregati precalcolate. Criterio: DX-19 (invariante), GDPR art. 25(2). Raccomandazione: (a).
- **DA-E1-12 — Attribuzione di prompt, modello e `config_version` a un'azione irreversibile.** Aperta. Opzioni: (a) l'audit fail-closed di B2 e A5 porta solo identificativi e hash (chiave, versione e hash del prompt, modello, `config_version`), E1 resta fail-open; (b) i segmenti `decision` e `hitl` sono fail-closed. Criterio: osservabilità AI (PV-01); DA-B2-04 e DA-A3-07 non devono allargarsi senza decisione. Raccomandazione: (a), da concordare con B2 e A5. **DA RIPORTARE ALL'UTENTE** (tocca il perimetro del fail-closed).

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: sezioni 6-12 riordinate secondo il template (aggiunta §6 Comportamento ricavata dal contenuto esistente; Decisioni aperte spostate dalla §9 all'Appendice C, eliminando il duplicato); aggiunti in §3 i sottoprodotti che dichiarano di emettere span; in §4.1 aggiunti gli attributi che A3, E2, E3 e C1 dichiarano di emettere (`gravya.policy.*`, `gravya.prompt.key/version/hash` al posto di `gravya.prompt.ref`, `gravya.eval.*`, `gravya.workflow.*`). Motivo: allineamento delle interfacce tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Riprogettazione per DX-02 / PV-01 / PV-02 (niente OpenTelemetry, conformità prevalente sul master plan) e DX-01 / PV-03 (ripartenza da zero). Rimossi OTel, OTLP, collector, `traceparent` come scelta e gli span OTel: §2, §4-6 e §9 ora descrivono un tracing DB-native (tabelle `gravya_traces`/`gravya_trace_segments`, `trace_id` generato da Gravya, RLS per tenant, partizioni per la retention, export interno verso E3); attributi `gen_ai.*` sostituiti da `gravya.llm.*`; aggiunta §4.3 su cosa si cattura e cosa no; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50 e 12/14/19, osservabilità AI); criteri §8, rischi §11 e taglia §12 ricalcolati per una costruzione da zero; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti, non riuso); Appendice C: DA-E1-01 chiusa da DX-02, DA-E1-02/03/04 riformulate, nuove DA-E1-05..08. |
| 1.3 | 2026-11-03 | Allineamento alle decisioni dell'utente del 2026-11-03. DA-E1-02 (contenuti mai in produzione) e DA-E1-05 (vocabolario GenAI semconv e formato `traceparent`, senza SDK OTel) diventano scelte: attributi LLM/tool/agente rinominati da `gravya.llm/tool/agent.*` a `gen_ai.*`, header di correlazione in formato `traceparent`. Recepite DA-A1-01 e DA-B1-06 (PostgreSQL self-hosted UE), DA-C1-01/05, DA-E3-08/09, DA-B2-07 (`gravya.tool.destination`). DA-E1-06 assorbita da DX-09: rimosse le durate proposte, elencate in §4.1 le classi di dati prodotte. §7 allineata a DX-10 (notifica NIS2 di A5, E1 invia segnali) e DX-11 (Gravya responsabile art. 28; artt. 12/14/19/26 AI Act solo buona pratica, art. 50 resta); tolte le ipotesi relative dall'Appendice B. Fail-open limitato alle tracce, con distinzione esplicita dal fail-closed di DA-B2-04/DA-A3-07 in §5-§8 e §10. Criteri 5, 8 e nuovo 9 aggiornati; taglia M confermata. |
| 1.4 | 2026-11-03 | Recepite le decisioni dell'utente del 2026-11-03: durate di default DX-09 (DECISIONS.md §5) in §4.1 e §7 (90 giorni tracce/segmenti, 12 mesi log accessi ed eval); DX-13: ruolo superadmin per l'accesso cross-tenant con log (DA-E1-08 decisa nell'impianto, residuo sugli aggregati da riportare) e soglie/durate come variabili di piattaforma versionate, auditate e fail-closed (§5); riga decisa di DECISIONS.md §6: argomenti dei tool solo come hash (`gravya.tool.args_hash`); base giuridica distinta per superadmin e dati delle agenzie. Dipendenze da F6 e da DX-14 (proposta A6, da riportare). Criterio 8 riscritto, nuovi criteri 10-11, rischi, Fase 0, §12 e Appendici B/C aggiornati. |
| 1.5 | 2026-11-04 | Allineamento a decisioni del 2026-11-04, catalogo v1.2 e registro norme v1.6. Valori sostituiti dai nomi del catalogo; regola durata più partizione ≤ massimo (D5) e cancellazione per riga. DX-17 (ultimo valore valido, segnale ad A5; primo avvio), DX-18 (log cross-tenant di A6), DX-19 e DX-20 (aggregati, singola traccia, MFA), DX-21 (`config_version`). Pseudonimi come dati personali; whitelist anche sui valori; attributi allineati a A3, B2, C1, C3; segnali ad A5 senza soglia locale; export a E3 solo `root_kind=eval`. «Evidenze di incidente» al posto di «legal hold»; Reg. 2024/2690 al posto di «NIS2 (art. 21)» per i log; fine contratto secondo Data Act art. 25; AI Act dopo l'Omnibus; dipendenze A5, A6, F6 con ripieghi. Criteri 1-14 riordinati; DA-E1-08 decisa; nuove DA-E1-09..12. Perché: un solo passaggio di allineamento prima della revisione della v1.5. |
