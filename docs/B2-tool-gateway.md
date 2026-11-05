# B2 — Tool gateway

## 1. Identità

| Campo | Valore |
|---|---|
| ID | B2 |
| Nome | Tool gateway |
| Componente padre | B — Runtime Agenti |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È l'unico punto da cui un agente in esecuzione (B1) può invocare un tool, anche dal ciclo di tool dei nodi agente. Per ogni chiamata: identifica agente e tenant dal `run_token`, chiede la decisione `allow/deny/require_approval` ad A3 (che valuta anche destinazione, opt-in, strumento di trasferimento, sub-responsabile e opposizione dell'agenzia), applica tre rate limit indipendenti, esegue o inoltra la chiamata e registra l'audit. Applica l'esito di A3 e non lo ricalcola. All'agente espone **solo** l'elenco dei tool autorizzati per lui (master plan, §6 B2).

**Cosa NON fa.**
- Non decide le autorizzazioni: la decisione è di A3, su policy compilate da A2 a partire da A1. Il gateway non contiene regole di permesso nel codice.
- Non implementa i connettori (D1–D4) né il protocollo MCP (D5, ondata 3); deve restare compatibile con un'esposizione MCP futura.
- Non gestisce l'approvazione umana: la richiede a C3 quando A3 risponde `require_approval`.
- Non è il registro permanente delle decisioni né notifica incidenti: emette eventi e segnali, A5 li conserva e decide (DX-10).
- Non verifica consensi di marketing né applica la marcatura art. 50: rifiuta le chiamate prive di `ai_generated` (§6) e dichiara i flag di catalogo; la precondizione di invio (base giuridica, mittente, opposizione) la verifica il connettore (D1–D4).

**Perché esiste.** Il master impone l'isolamento architetturale: l'agente non deve poter raggiungere un tool se non attraverso un confine che non controlla. Se i tool stanno nel processo dell'agente, l'isolamento dipende dalla disciplina del codice.

## 3. Contesto e dipendenze

**Dipende da:**
- **A3**: decisione sincrona. Il record di decisione e l'audit dell'esito stanno in un'unica transazione eseguita da B2 (DECISIONS §6). **A1** e **A2** indirettamente tramite A3 (A2 compila in policy opt-in, strumento, sub-responsabile e opposizioni).
- **B1**: emette il `run_token` (lo stesso oggetto del `tool_grant_ref` di B1, DA-CV-13); egress-proxy che applica lo stesso esito di A3 sulle destinazioni.
- **C3**: rilascia l'`approval_token`.
- **E1**: tracce DB-native, vocabolario `gravya.*` (niente OpenTelemetry, PV-02); regola dell'hash degli argomenti.
- **A5** (ondata 2): audit e segnali di incidente (DX-10). Nell'ondata 1 vanno in una tabella di audit minima nel database di Gravya, che A5 assorbe (DECISIONS §6).
- **A6** (ondata 2, DX-14): ruoli superadmin e admin agenzia, registro versionato delle variabili (`config_version`, `platform.config.changed`), configurazione per tenant (opt-in, opposizione), pagina credenziali, log degli accessi cross-tenant (DX-18).
- **F6** (ondata 2, DX-12): retention DX-09, classi senza durata, strumento di esportazione dei dati di un tenant (E15).
- DX-13, DX-17, DX-22.

**È richiesto da:** B1 (gli agenti chiamano i tool solo da qui), C1 (nodi tool e validatore: `audience` derivata dal catalogo B2), C3 (riprende la chiamata dopo l'approvazione), A3 (input della decisione fornito da B2), E3 (casi `act`/`refuse`), D1–D4 (si registrano come tool), D5 (ondata 3), E5 ed E6 (ondata 3), A5 (segnali).

**Assunzioni (non verificate):** il formato del `run_token` e i suoi campi sono di B1; il contratto di A3 (§4 di A3) è quello letto nella v1.5. Il gateway si costruisce da zero (DX-01, PV-03); gravya-app è solo riferimento (Appendice A).

## 4. Contratti

**Input (richiesta di invocazione):**

| Campo | Tipo | Note |
|---|---|---|
| `run_token` | stringa firmata | emesso da B1, durata `b1.run_token.ttl_s`; valido per tutto il run (non monouso); da qui `agent_id`, `agent_version`, `tenant_id`, `run_id` (mai dal corpo) |
| `tool_id` | stringa | id stabile nel catalogo |
| `args` | oggetto | validato contro lo schema del tool; per i tool con `audience` `person` o `third_party` porta `ai_generated` con `model` e `prompt_ref` |
| `idempotency_key` | stringa | obbligatoria per i tool di scrittura; la chiave effettiva è composta da tenant, tool e hash degli argomenti (§6) |
| `approval_token` | stringa, opzionale | monouso, emesso da C3, legato a tenant, tool e hash degli argomenti approvati; durata `hitl.approval_token.ttl_s` |
| `trace_context` | oggetto | `trace_id`, `run_id` del modello DB-native di E1; formato ispirato a `traceparent` (DA-E1-05), senza SDK né export OTel |

**Output:** `{status: ok|denied|approval_required|rate_limited|error, result?, reason?, decision_id}`; `rate_limited` porta `retry_after`. Un record di decisione non salvato è `denied` con `reason` `record_not_persisted` (un solo esito, come in A3); `error` resta per gli errori di esecuzione e di sistema. `result` è sempre marcato come dato e non come istruzione (idea ripresa da gravya-app, Appendice A).

**Catalogo tool (schema minimo).** Gestito dal superadmin, versionato e auditato. Campi: `tool_id`, versione, schema degli argomenti, classe di accesso (`read`/`write`/`money_write`), **classe di approvazione** `approval_class` (`ALWAYS_HITL`, `MONEY_WRITE` o nessuna; vocabolario chiuso e unico in tutti i documenti, senza `REQUIRES_HITL`), `domain`, `creates_new`, mappa argomenti→assi di scope, destinazione d'esecuzione, **destinazione dei dati** (obbligatoria, DA-B2-07: `destination_id`, giurisdizione, categorie di dati, sub-responsabile autorizzato con riferimento al DPA e data), `audience` (`internal` \| `person` \| `third_party`: chi riceve l'output; è la fonte unica, C1 la deriva da qui e rifiuta una dichiarazione meno restrittiva), flag `direct_interaction` (il tool conversa direttamente con una persona: informativa art. 50(1), la applica C1/D1–D4), flag `ai_generated_output`, limite del tool (`b2.rate_limit.tool_calls_per_minute`). Un tool con `audience` `person` o `third_party` senza `ai_generated_output` dichiarato non si registra.
- **Classe di approvazione (DA-CV-15, E4).** La assegna il superadmin nel catalogo. Si può solo **aggiungere**; toglierla richiede la conferma della seconda persona con accesso superadmin, con audit. Non è declassabile da altre UI. Un tool senza classe dichiarata va in `require_approval`. Le altre azioni seguono `hitl.approval_required_default`. L'`approval_class` è la sola fonte da cui si costruisce `tool_class` per A3.
- **Contenuti verso terzi:** non sono `ALWAYS_HITL` nell'ondata 1; l'approvazione la decide l'admin agenzia, con audit (DA-CV-18, da riesaminare con D1–D4). Nell'ondata 1 i tool di invio verso terzi sono negati nel bundle di A3 (DA-A3-09, E3).

**Fatti sulla destinazione, impostati dal superadmin con fonte e audit (DA-CV-19):** strumento di trasferimento (`tenant.extra_eu_optin.<destination_id>.transfer_instrument`), stato (`..._status`) con data e scadenza della verifica (`transfer.instrument_review_interval_days`), sub-responsabile (`destination.<destination_id>.subprocessor_authorization`). Dell'agenzia: opt-in (`tenant.extra_eu_optin.<destination_id>.enabled`, mai attivabile dal superadmin) e opposizione a un sub-responsabile (`tenant.destination.<destination_id>.objection_active`). Valori in A6; B2 non li scrive.

**Verso A3 (`DecisionRequest`, A3 §4):** `tenant_id`, `agent_id`, `agent_version`, `run_id`, `trace_id`, `action` (`tool.invoke`), `tool_id`, `tool_class` (da `approval_class`, `domain`, `money_write`, `creates_new`), `destination` (`destination_id`, giurisdizione, categorie), `resource` (da `args` tramite la mappa degli assi), `approval_token` se presente, `budget_state` se DA-A3-04 sceglie (a): la fonte non è definita in nessun documento dell'ondata 1.

**Eventi emessi** (trasporto: DA-A1-03): `tool.invoked`, `tool.denied`, `tool.rate_limited`, `tool.approval_requested`, `tool.completed`, `tool.failed`, `catalog.destination.changed` (destinazione o sub-responsabile aggiunti o cambiati). Campi comuni: tenant, agente, run, tool, `decision_id`, versione/hash della policy, `config_version`, identificativi e hash di prompt e modello come forniti dal run (DA-E1-12), durata, esito, anteprima redatta degli argomenti. **Hash:** HMAC-SHA-256 con chiave per tenant, nella pagina credenziali di piattaforma, con rotazione a due chiavi (E1, DA-CV-23); un SHA-256 semplice di un dato breve resterebbe dato personale (considerando 26); distruggere la chiave rende l'hash non riconducibile. **Segnali verso A5:** ogni evento rilevante per la sicurezza (§6), **senza soglia locale** (DA-CV-07).

**Eventi consumati:** invalidazione di catalogo o policy (A2/A3); `platform.config.changed` (A6).

**Esportabilità (E15).** I dati di un tenant che B2 conserva sono esportabili con lo strumento di F6: eventi di audit dei tool (identificativi, esito, anteprima redatta nella finestra), esiti memorizzati per idempotenza (stato e riferimento), registro dei token di approvazione consumati. Il formato è di F6. Contatori di rate limit e catalogo non sono dati del tenant.

## 5. Interfacce

- `GET /tools` — elenco dei tool autorizzati per il run, con gli schemi: è l'elenco filtrato da A3, non il catalogo intero. Si riallinea alle variazioni di policy entro `a3.policy.propagation_max_s`.
- `POST /tools/{tool_id}/invoke` — invocazione con il contratto §4.
- **Interfaccia amministrativa del catalogo** (superadmin, DX-13; pagina «Piattaforma → Tool gateway», provvisoria finché A6 non la fissa). Ogni modifica è versionata e auditata; se l'audit non si salva, la modifica non si applica. Una modifica di destinazione o sub-responsabile emette `catalog.destination.changed`: da lì parte l'informativa alle agenzie (E12, art. 28(2) GDPR).
- **Destinazioni dei dati:** l'admin agenzia attiva l'opt-in e può registrare l'opposizione a un sub-responsabile in «Agenzia → Impostazioni → Destinazioni dei dati» (MFA, DX-20); il superadmin aggiorna strumento, stato e sub-responsabile indicando la fonte.
- **Credenziali:** pagina dedicata di A6. Credenziali dei sistemi esterni: di agenzia (inserite dall'admin agenzia) o di piattaforma (solo per i tool di piattaforma, dal superadmin); il superadmin non inserisce mai credenziali per conto di un'agenzia (DX-22(b), DA-CV-16). Chiavi di firma del `run_token`, HMAC dei token monouso e HMAC degli hash per tenant: credenziali di piattaforma. Da UI solo inserimento o sostituzione, mai rilettura in chiaro. Archivio cifrato self-hosted nell'UE; cifratura e gestione delle chiavi sono di A6 (E11).
- **Variabili lette da B2** (catalogo §7, modificabili dal superadmin senza rilascio, versionate e auditate): `b2.rate_limit.agent_calls_per_minute`, `b2.rate_limit.tool_calls_per_minute`, `b2.rate_limit.tenant_calls_per_minute`, `b2.recovery_queue.retry_interval_s`, `b2.idempotency.window_hours` (massimo `b2.idempotency.window_hours_max`), `b1.run_token.ttl_s`, `hitl.approval_token.ttl_s`, `hitl.approval_required_default`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`, `a3.policy.propagation_max_s`, `b2.overhead_p95_ms`, le classi `retention.*` di §7.
- **Lettura delle variabili (DX-17, DA-CV-17, E5).** Tutte tramite una sola interfaccia. Prima di A6 è un'istantanea versionata nel repository, modificabile solo con una PR: ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste; i valori «proposta da validare» valgono come primo valore valido, con segnale; quelli «da definire» hanno un valore di sviluppo ammesso solo fuori produzione. Variabile non leggibile o non valida: le azioni si bloccano (`error`, nessuna esecuzione) con segnale ad A5; le cancellazioni programmate usano l'ultimo valore valido versionato. Senza alcun valore valido, il primo valore valido è il valore «deciso» del catalogo; segnali, audit e notifiche sono esclusi dal blocco; le classi di retention «da definire» non si scrivono in produzione finché A6 o F6 non fissano un valore. Le durate di retention sono di sola lettura finché l'intervallo del DPA non è definito (DA-CV-01).
- Trasporto: servizio HTTP separato in FastAPI (DA-B2-02 (a), E16). Origine dell'elenco autorizzato: DA-B2-05.

## 6. Comportamento

**Flusso principale:** verifica di `run_token` → voce di catalogo (destinazione dichiarata, validazione di `args`, presenza di `ai_generated` se richiesta) → decisione A3 → rate limit → **transazione unica** (record di decisione di A3 + audit dell'esito) → esecuzione con le credenziali del gateway → audit `completed`/`failed` → risposta.

**Transazione unica.** Copre ogni esito: `allow`, `deny`, `require_approval`, `rate_limited`. Se la transazione non si completa entro `a3.record.persist_timeout_ms` o fallisce, la risposta è `denied` con `record_not_persisted` e nulla si esegue. Un rifiuto prima di A3 (token non valido, tool assente dal catalogo, `args` non validi) produce solo l'evento di audit e il segnale.

**Destinazioni e trasferimenti (DA-B2-07, DA-CV-19, E2, E12).** Valuta A3 sulla policy compilata da A2; B2 applica l'esito (`destination_undeclared`, `extra_eu_no_optin`, `transfer_instrument_invalid`, `subprocessor_unauthorized`, più l'opposizione dell'agenzia) e l'egress-proxy di B1 applica lo stesso. B2 nega comunque un tool senza destinazione in catalogo.
- Anche per una destinazione UE serve il sub-responsabile autorizzato (art. 28(2) e (4) GDPR); non passa dall'opt-in.
- Extra-UE: opt-in dell'agenzia per quella destinazione **e** strumento con stato valido. Il Data Privacy Framework vale solo per le organizzazioni dell'elenco DPF (decisione 2023/1795, art. 1); per le altre serve uno strumento dell'art. 46.
- Se lo strumento cade o la sua verifica scade (`transfer.instrument_review_interval_days`, E15), lo stato diventa non valido, l'opt-in si disattiva, parte un segnale ad A5 e il tool è negato entro `a3.policy.propagation_max_s`: stesso criterio di ritardo di A3. La riattivazione richiede un nuovo opt-in dell'agenzia.
- Se una destinazione o un sub-responsabile cambia, parte l'informativa alle agenzie; un'agenzia che registra l'opposizione ha il tool negato per sé da quel momento.
- Stato non leggibile: `denied`.

**Casi limite:**
- A3 non raggiungibile o oltre `a3.eval.timeout_ms`: **deny**.
- Tool assente dal catalogo o dall'elenco del run: `denied`, senza rivelare se esiste.
- **Contenuti verso terzi:** per un tool con `audience` `person` o `third_party` (o `ai_generated_output`), una chiamata senza `ai_generated` con `model` e `prompt_ref` valorizzati in `args` è `denied` (`ai_generated_missing`), anche se arriva dal ciclo di tool di un nodo agente in B1; B2 non ne verifica la veridicità. Se A3 nega un invio, B2 risponde `denied` con il motivo di A3, con evento e segnale.
- `require_approval`: `approval_required` e richiesta a C3. Alla ripresa, A3 verifica firma e legame del token (tenant, tool, hash degli argomenti); B2 lo **consuma** nella transazione e lo registra come consumato; un token usato, scaduto o con argomenti diversi è `denied`. `ALWAYS_HITL` e `MONEY_WRITE` richiedono sempre l'approvazione.
- `money_write` con budget illeggibile: deny.
- **Audit non salvato prima dell'esecuzione:** l'azione si blocca (DA-B2-04). È «salvato» solo il commit in tabella o una coda locale **durevole su disco con fsync**; una coda in memoria non conta (DECISIONS §6). Con la coda, record di decisione e audit entrano come entrata unica e si riscrivono insieme al ripristino (assunzione, App. B).
- **Audit di esito fallito dopo l'esecuzione:** l'azione non si annulla; l'evento va nella coda di recupero durevole, ritentata ogni `b2.recovery_queue.retry_interval_s` fino a riuscirci, con segnale ad A5. La risposta riporta l'esito reale.
- **Rate limit:** tre limiti indipendenti (agente, tool, tenant), vince il più restrittivo; superamento → `rate_limited` con `retry_after`, nessuna esecuzione. Archivio dei contatori: DA-B2-03.
- **Idempotenza:** la chiave effettiva è composta da tenant, tool e hash degli argomenti; un retry entro `b2.idempotency.window_hours` (non oltre `b2.idempotency.window_hours_max`) restituisce il primo esito senza rieseguire; la stessa chiave con argomenti diversi è `error`. Si conservano solo stato e un riferimento redatto. Chiave scaduta per una scrittura: `error` (DA-B2-09 (b)).
- **Rotazione delle chiavi** (firma del `run_token`, HMAC del token monouso, HMAC degli hash per tenant; DA-CV-23): due chiavi valide in parallelo, ciascuna con data di attivazione e disattivazione; B2 accetta una chiave valida in quel momento e rifiuta una disattivata. Frequenza: `security.credential_rotation_interval_days`.
- **Segnali ad A5 senza soglia locale:** ogni `tool.denied`, token falsificato o scaduto, tentativo di bypass, destinazione negata, strumento caduto o scaduto, chiamata senza `ai_generated`, audit non salvato, variabile non leggibile. Sempre prodotti e conservati, anche con `incident.nis2_flow_active` falso (C2, DX-10).

## 7. Requisiti non funzionali

- **Esecuzione:** self-hosted su infrastruttura UE (DA-B1-06).
- **Sicurezza:** l'agente non ha credenziali dei sistemi esterni; restano al gateway, mai rilette in chiaro e fuori da log, audit e tracce. L'egress di B1 è consentito solo verso gateway e peer interni. Il token monouso (invariante) è l'`approval_token`; il `run_token` vale per tutto il run.
- **Isolamento tenant:** il tenant viene solo dal token; ogni accesso ai dati dei tool è in contesto RLS. Il superadmin vede di default solo dati aggregati senza identificativi (`access.aggregate_min_group_size_count`). Due vie di accesso ai dati di un tenant (DX-19, E8): (a) incidente dichiarato dal superadmin, che abilita la lettura con riferimento all'incidente; (b) richiesta di assistenza, in cui l'admin agenzia concede l'accesso. In entrambi i casi perimetro e durata `access.superadmin_trace_access_ttl_hours`, entro le istruzioni del titolare (art. 28), con log degli accessi (chi, quando, quale tenant, quale dato, motivo; proprietà di A6, DX-18, `retention.cross_tenant_access_log_months`).
- **Prestazioni:** overhead sotto `b2.overhead_p95_ms` (escluso il tool); i budget di A3 (`a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms`) servono per gli alert e non bloccano.
- **Osservabilità:** una traccia E1 DB-native per invocazione, collegata al run; nelle tracce gli argomenti compaiono solo come hash HMAC per tenant (DA-C3-06, E1); nessun contenuto di prompt o risposte. Anteprime e risultati redatti prima della persistenza.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Gravya è responsabile (art. 28, DX-11) per i dati delle agenzie; base giuridica del titolare, di Gravya per gli identificativi dei suoi utenti (DECISIONS §6). Minimizzazione: l'audit conserva identificativi, `config_version`, hash e anteprima redatta, non payload né risultato. Gli identificativi pseudonimi nelle tracce sono dati personali (considerando 26); le linee guida EDPB 01/2025 sono solo in consultazione. Diritti: identificativi e anteprime ricercabili per soggetto; assistenza alle agenzie ex art. 28(3)(e), senza termine di legge (`dsar.assist_max_days` è un obbligo del DPA, A5/F6). Violazione di dati: art. 33(2) senza ore; il termine verso le agenzie è un obbligo del DPA (DA-CV-08, A5). Trasferimenti (Cap. V) e sub-responsabili: §6; la decisione DPF è impugnata (C-703/25 P) e copre solo l'elenco; l'agenzia è informata dei cambiamenti e può opporsi (art. 28(2)).
  - **Retention (DX-09, F6; sola lettura finché manca l'intervallo del DPA, DA-CV-01).** Classi di B2: audit dei tool, `retention.audit_decisions_months`; anteprime redatte, `retention.sensitive_payload_days` (poi resta l'hash HMAC); tracce, `retention.traces_days`; log degli accessi cross-tenant, `retention.cross_tenant_access_log_months`; evidenze di incidente, `retention.incident_evidence_months` (sospensione non attivabile finché massimo, riesame e categorie mancano; vale solo per i dati di Gravya, per quelli delle agenzie servono istruzione nel DPA e parere legale prima di F6, DA-CV-21); segnali, `retention.incident_signals_months` (tetto provvisorio dell'utente prima della produzione, DA-CV-20); esiti di idempotenza, `b2.idempotency.window_hours`; accessi alle credenziali, `retention.credential_access_months`; catalogo e versioni: per tutta la durata del servizio; contatori di rate limit e token consumati: classe da assegnare in F6. Backup: scadono entro `retention.data_backup_days`; al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22). Fine contratto: la scelta restituzione o cancellazione (`retention.tenant_offboarding_choice`) è sempre dell'agenzia (art. 28(3)(g), DA-CV-12); senza scelta, export per tutto il periodo di uscita e poi cancellazione; periodo di recupero di almeno 30 giorni dopo il passaggio (Data Act art. 25(2)), `retention.tenant_offboarding_days` come minimo; qualificazione del SaaS da confermare con un legale.
  - *NIS2.* Gravya oggi non è soggetto NIS2; progettazione «NIS2 compliant ready by design» (DX-10). Log, protezione e backup dei log, accessi privilegiati: requisiti di progetto dal Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11. Il flusso di notifica è di A5, presente ma non attivo (`incident.nis2_flow_active`): preallarme 24 h, notifica 72 h, relazione finale entro un mese, CSIRT Italia, dalla conoscenza. B2 invia sempre segnali ed evidenze.
  - *AI Act.* Art. 50 dal 2.8.2026. B2 rifiuta le chiamate di invio senza `ai_generated` (§6) e porta `audience`, `direct_interaction`, `ai_generated_output`; etichetta «generato da AI» e informativa 50(1) sono invarianti, la marcatura leggibile da macchina anche del testo (50(2)) è dettagliata in C1 e D1–D4. Artt. 12, 14, 19, 26: solo buona pratica (DX-11), e comunque per l'alto rischio dal 2.12.2027.
  - *Marketing (PV-01 esteso).* Per i tool verso terzi: ePrivacy art. 13, Codice privacy artt. 122 e 130, d.lgs. 70/2003 artt. 8-9, linee guida del Garante sui pixel (registro, ◐). La precondizione di invio (base giuridica registrata, mittente identificato, meccanismo di opposizione) la verifica il connettore (D1–D4); consenso, opt-out e variabili sono di D1–D4, B2 non ne introduce (catalogo §1, regola 10).
  - *Osservabilità AI.* Quale agente, quale tool, quale run, decisione e versione della policy, esito, durata, approvazione umana, costo (per E5/E6).

## 8. Criteri di accettazione

Le dimensioni dei campioni (tentativi, chiamate, valore di N) sono parametri del test (DA-CV-04 (b)); le soglie leggono le variabili del catalogo.

1. **Esposizione filtrata:** due agenti con permessi diversi ottengono da `GET /tools` insiemi diversi, uguali a quelli attesi dalla policy; sono assenti i tool negati per destinazione (criterio 9).
2. **Nessun bypass:** un test da dentro B1 che importa o chiama direttamente un tool o un host esterno fallisce; il 100% delle chiamate nei test e2e ha un evento di audit con lo stesso `run_id`.
3. **Fail-closed:** con A3 spento o oltre `a3.eval.timeout_ms`, 0 chiamate eseguite; con la transazione non salvabile o oltre `a3.record.persist_timeout_ms`, 0 chiamate eseguite e risposta `denied` con `record_not_persisted`.
4. **Rate limit indipendenti:** con limiti di prova diversi per agente, tool e tenant, per ciascuno N+1 chiamate producono esattamente 1 `rate_limited` e vince il più restrittivo; una modifica di variabile si applica senza riavvio, con audit (versione precedente e nuova); con variabile illeggibile 0 chiamate eseguite.
5. **Approvazione monouso e legame:** due chiamate con lo stesso `approval_token` → la seconda `denied`; un token oltre `hitl.approval_token.ttl_s`, o con hash degli argomenti diverso, o di un altro tenant o tool → `denied`; il token consumato compare nel registro.
6. **Isolamento:** token del tenant A con un `record_id` del tenant B → `denied` o nessun risultato; la stessa `idempotency_key` usata da due tenant produce due esecuzioni e nessun esito di un tenant è restituito all'altro.
7. **Audit completo:** per ogni esito di §4 esiste 1 evento con i campi obbligatori, `config_version` compresa; la transazione contiene record di decisione e audit anche per `deny`, `require_approval` e `rate_limited`.
8. **Overhead:** benchmark su un campione di chiamate a un tool fittizio, p95 sotto `b2.overhead_p95_ms`.
9. **Destinazione e trasferimenti:** tabella di casi: nessuna destinazione → `denied`; UE senza sub-responsabile → `denied`; UE con sub-responsabile → consentito senza opt-in; extra-UE senza opt-in → `denied`; con opt-in, strumento valido e sub-responsabile → consentito; opposizione dell'agenzia → `denied` solo per quel tenant. Con lo strumento portato a non valido, o con la verifica scaduta, il tool è `denied` entro `a3.policy.propagation_max_s` (lo stesso valore del criterio di A3), con `enabled` falso e 1 segnale ad A5; tornato valido resta `denied` finché l'agenzia non rifà l'opt-in. Un aggiornamento dello stato senza fonte è rifiutato. Una modifica di destinazione in catalogo emette `catalog.destination.changed`.
10. **Transazione unica, coda e recupero:** con guasto iniettato tra record di decisione e audit esistono entrambi o nessuno; con tabella non disponibile e coda con fsync la chiamata è eseguita e le scritture compaiono al ripristino; con coda senza fsync 0 chiamate eseguite; con audit di esito impossibile dopo l'esecuzione l'evento entra nella coda di recupero, si scrive al ripristino e parte 1 segnale.
11. **Retention e accessi cross-tenant:** un job con orologio simulato elimina le anteprime oltre `retention.sensitive_payload_days` lasciando l'hash e l'audit oltre `retention.audit_decisions_months`; con variabile illeggibile usa l'ultimo valore valido e invia 1 segnale; l'accesso del superadmin a un altro tenant produce 1 riga nel log, solo se è dichiarato un incidente o l'admin agenzia ha concesso l'accesso, per non oltre `access.superadmin_trace_access_ttl_hours`; un admin di agenzia riceve un rifiuto.
12. **Credenziali:** nessuna risposta di API o UI e nessun log, audit o traccia contiene una credenziale di prova in chiaro (0 occorrenze); un tool con credenziale assente risponde `error`.
13. **Rotazione delle chiavi:** con chiamate continue durante il passaggio, token firmati con la chiave vecchia e con la nuova sono accettati finché entrambe sono valide e 0 chiamate falliscono; dopo la disattivazione il token della chiave vecchia è `denied`.
14. **Segnali:** ogni caso del §6 produce 1 segnale per evento, senza soglia locale, anche con `incident.nis2_flow_active` falso.
15. **Idempotenza:** due chiamate con la stessa chiave e gli stessi argomenti entro la finestra producono 1 esecuzione e lo stesso esito; stessa chiave con argomenti diversi → `error`; chiave scaduta su una scrittura → `error`; un valore di `b2.idempotency.window_hours` oltre il massimo è rifiutato.
16. **Contenuti verso terzi e catalogo:** una chiamata a un tool con `audience` `person` o `third_party` senza `ai_generated` valorizzato è `denied`, sia da una chiamata diretta sia dal ciclo di tool di un nodo agente; un tool con quell'`audience` senza `ai_generated_output` è rifiutato alla registrazione; un tool senza classe di approvazione dà `require_approval`; togliere una classe richiede la conferma della seconda persona; l'`audience` dichiarata da un workflow meno restrittiva di quella del catalogo è rifiutata da C1.
17. **Hash:** nelle tracce e nell'audit gli argomenti compaiono solo come HMAC per tenant; lo stesso argomento in due tenant dà hash diversi; dopo la distruzione della chiave di un tenant l'hash non è più verificabile.

## 9. Piano di implementazione

1. Catalogo dei tool e contratto §4, con un tool fittizio. Base già decisa: gateway nuovo (DX-01), servizio FastAPI (DA-B2-02 (a)).
2. Integrazione con A3: `DecisionRequest` completo, filtro di `GET /tools`, fail-closed, transazione unica.
3. Rate limit a tre livelli (DA-B2-03) e idempotenza con chiave composta.
4. Audit fail-closed, coda durevole, coda di recupero, eventi verso E1, segnali verso A5 (DX-10).
5. Campi di destinazione, `audience`, classe di approvazione e controllo di `ai_generated`; applicazione dell'esito di A3 su destinazioni, strumento e opposizioni; informativa alle agenzie.
6. Flusso `require_approval` con C3, legame del token, registro dei consumati; rotazione a due chiavi.
7. Primi tool di lettura, poi di scrittura, scritti sul contratto §4 (gravya-app come riferimento, non portando codice).

**Tecnologie:** Python/FastAPI per il servizio (E16: backend tutto in Python), PostgreSQL con RLS, Redis (DA-B2-03). Il master cita OPA/Rego per A3 (DA-A3-01) e MCP per D5. Niente SDK né export OpenTelemetry (PV-02). Self-hosted nell'UE (DA-B1-06); nessun servizio gestito che porti dati fuori dal perimetro senza decisione dell'utente.

**Rischi principali:** §11.

## 10. Test e valutazione

- **Unit:** schemi degli argomenti, mappatura degli esiti A3, contatori a tre livelli, token monouso e legame, chiave di idempotenza composta, HMAC degli hash, redazione.
- **Integration:** gateway + A3 + DB con due tenant; ripresa dopo C3; idempotenza; transazione unica con guasto iniettato per ogni esito.
- **Fail-closed:** audit non scrivibile; coda con fsync; audit di esito fallito dopo l'esecuzione; A3 non raggiungibile; variabile illeggibile.
- **Superadmin e retention:** modifica versionata e auditata delle variabili; stato dello strumento solo dal superadmin, con fonte; opt-in non attivabile dal superadmin; classe di approvazione solo in aggiunta; accesso cross-tenant solo per incidente o assistenza, con log; cancellazione per classe.
- **Security:** bypass da B1, token falsificato, tenant spoofing via `args`, prompt injection nel risultato, tool senza destinazione, extra-UE senza opt-in, invio senza `ai_generated` dal ciclo di tool, credenziali nei log, chiave disattivata.
- **Eval:** i golden set E3 che usano tool passano dal gateway.

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Logica di permesso nel codice dei tool (difetto di gravya-app) | Alto | Un solo punto di decisione: A3; test di bypass |
| Audit fail-closed riduce la disponibilità | Medio | Scelta accettata (DA-B2-04); coda con fsync; segnale ad A5; criteri 3 e 10 |
| Azione eseguita senza audit di esito | Alto | Coda di recupero e segnale; criterio 10 |
| Variabile errata (limite o retention) | Medio | Modifiche del superadmin, versionate e auditate; DX-17; criteri 4 e 11 |
| Abuso dell'accesso cross-tenant | Alto (GDPR art. 28) | Solo aggregati di default, accesso per incidente o assistenza con perimetro, durata e log; criterio 11 |
| Dati personali verso destinazioni non controllate, con strumento caduto o con sub-responsabile contestato | Alto (GDPR Cap. V, art. 28(2)) | Destinazione e sub-responsabile obbligatori, opt-in e opposizione per agenzia, stato dal superadmin, deny entro `a3.policy.propagation_max_s`; criterio 9 |
| Contenuto AI verso un terzo senza etichetta | Alto (AI Act art. 50) | Rifiuto di B2 senza `ai_generated`, `audience` dal catalogo; criterio 16 |
| Invio verso terzi senza base (marketing) | Alto (ePrivacy, Codice privacy) | Tool negati nel bundle nell'ondata 1; da D1–D4 precondizione verificata dal connettore |
| Hash riconducibile al dato dopo la cancellazione | Medio (GDPR considerando 26) | HMAC con chiave per tenant; criterio 17 |
| Sostituzione chiavi con interruzione | Medio | Due chiavi parallele; criterio 13 |
| Latenza del salto di rete | Medio | Servizio separato (DA-B2-02 (a)); criterio 8 |
| Cache dell'elenco tool non allineata | Alto | Invalidazione su evento; ritardo massimo `a3.policy.propagation_max_s`; in dubbio decide A3 a ogni invocazione |

## 12. Stima e priorità

- **Taglia:** M per lo skeleton (servizio, catalogo con destinazioni e classi, rate limit a tre livelli, idempotenza, audit fail-closed con transazione unica, HITL, chiavi parallele, HMAC per tenant, un tool di lettura e uno di scrittura). Verso L con il numero di tool reali (D1–D4). Stima non validata.
- **Dipendenze critiche:** A3, B1.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

Legenda: [L] = letto nel file indicato; [K] = da `docs/visione` di gravya-app-kloudify (fotografia del 16/10). Per DX-01/PV-03 nulla si porta in v2: sono idee e lezioni.

**Soluzioni da riprendere come idea:**
- [L] `services/agents/src/tools/_scope_enforcement.py`: enforce mode con `ScopeViolation`, assi di scope, `REQUIRES_HITL` con token monouso, `MONEY_WRITE` con tetto di spesa fail-closed, default-deny per i tool senza tassonomia, audit `tool.scope.denied`. I councils non passano da questo punto.
- [L] `services/agents/src/tools/_audit.py`: una riga per chiamata in `gravya_tool_invocations`, con redazione. È **best-effort**: se il pool DB non è disponibile l'audit è saltato e il tool eseguito lo stesso.
- [L] `services/agents/src/executors/generic_executor.py`: tool caricati con importlib (whitelist `src.tools.`), `_run_tool_loop` con massimo di chiamate per risposta, risultati troncati e delimitati come dati, `_park_write` per le scritture.
- [L] `services/agents/src/api/_shared.py`: slowapi con `RATE_LIMIT_RPM` per IP.
- Da ricognizione di terzi (non riletta): API Broker (cost ledger, circuit breaker, idempotenza), egress-proxy con allowlist e HMAC, firewall `OUTPUT DROP`.
Valori del sistema precedente (limiti di chiamate, caratteri, RPM) sono riferimenti, non default di v2 (catalogo §16).

**Difetti da non ripetere:**
1. Nessun gateway separato: import diretto, confine solo per convenzione.
2. Autorizzazione nel codice invece che come policy A3.
3. Rate limit per agente/tool assente (solo per IP).
4. Audit non garantito (best-effort).
5. MCP assente; [K] lo rinvia dopo la Beta, coerente con D5 (ondata 3).
6. [K] `architettura-agenti.md` r. 81-82 dice che i tool «non vengono mai eseguiti»: superato dal ciclo di tool del codice.
7. Nessun ADR né task aperto pertinente a B2.

## Appendice B — Non verificato

- I punti dell'Appendice A sono ripresi dalla v1.0 e non ricontrollati: se `_run_tool_loop` sia raggiunto in produzione; `api-broker.ts`, egress e firewall; il valore di `RATE_LIMIT_RPM`; se i councils invochino tool; lo stato delle issue #998 e #1801.
- Formato e campi del `run_token` di B1 (in particolare `agent_version`, identificativi e hash di prompt e modello per l'audit, DA-E1-12): non riletti in B1 per questa versione.
- Il nome `a3.policy.propagation_max_s` è proposto in questo documento: A3 lo chiama «ritardo massimo» (DA-A3-08) senza nome nel catalogo 1.3.
- Interazione tra coda locale con fsync e transazione unica: DECISIONS §6 decide entrambi, non il loro rapporto; l'entrata unica è un'assunzione da confermare con A3.
- Comportamento con archivio dei contatori non disponibile: fail-closed è una deduzione da DX-17.
- Confronto degli hash HMAC durante la rotazione a due chiavi (quale chiave per quale hash): dettaglio di E1.
- La chiave HMAC per tenant non è ancora nell'elenco delle credenziali del catalogo §15.
- Canale, contenuto e chi invia l'informativa alle agenzie su destinazioni e sub-responsabili (E12), e dove si registra l'opposizione (assunto: configurazione per tenant di A6): A6 non è documentato.
- Come B2 legge strumento, stato e scadenza (registro di A6): A6 non è documentato; granularità dell'audit degli accessi alle credenziali: di A6.
- Registro delle norme: ePrivacy art. 13, Codice privacy artt. 122 e 130, d.lgs. 70/2003 artt. 8-9, linee guida pixel e Codice di buone pratiche art. 50 (marcatura del testo) sono ◐ o non letti; elenco DPF non consultato; C-703/25 P ◐; qualificazione del SaaS per Data Act e NIS2 aperta.
- Durate di contatori di rate limit e token consumati (F6); tetti provvisori DA-CV-20; intervalli `_min`/`_max` delle durate (DPA, F6); formato dello strumento di esportazione di F6 (E15, proposta del coordinator in attesa di conferma).
- Valori «da definire» delle variabili B2 e soglie «proposta da validare».
- Struttura della tabella di audit minima e dei segnali dell'ondata 1.

## Appendice C — Decisioni (aperte e decise)

**Decise**
- **DA-B2-01 — Base di partenza.** Chiusa da DX-01: gateway nuovo.
- **DA-B2-02 — Forma del confine.** Decisa (E16, 2026-11-04): (a) servizio HTTP separato in FastAPI, backend tutto in Python.
- **DA-B2-04 — Audit fail-closed.** Decisa (2026-11-03): se l'audit non si salva l'azione si blocca; coda locale solo con fsync; audit di esito fallito: coda di recupero e segnale; tabella minima nell'ondata 1.
- **DA-B2-06 — Retention.** Assorbita da DX-09.
- **DA-B2-07 — Tool verso terzi o extra-UE.** Decisa (2026-11-03), precisata il 2026-11-04 (C9, D5, D7, DA-CV-19, E12, E15): destinazione e sub-responsabile obbligatori; opt-in per destinazione e opposizione per agenzia in A6; strumento, stato e sub-responsabile dal superadmin con fonte e audit; strumento caduto o scaduto → segnale e disattivazione; nuovo opt-in per riattivare.
- **DA-B2-08 — Chi valuta strumento e sub-responsabile.** Decisa (E2): A3 sulla policy di A2; B2 e l'egress-proxy applicano; ritardo massimo uguale in A3 e B2.
- **DA-B2-09 — Chiave di idempotenza oltre la finestra.** Decisa (E13): (b) errore per le scritture.
- **DA-B2-10 — Invii verso terzi senza base registrata.** Decisa (E3): nell'ondata 1 tool negati nel bundle; da D1–D4 precondizione verificata dal connettore; B2 rifiuta le chiamate senza `ai_generated`; `audience` dal catalogo.
- **DA-B2-11 — Chi assegna le classi di approvazione.** Decisa (E4): il superadmin nel catalogo, solo in aggiunta, rimozione con la seconda persona; senza classe → `require_approval`.
- **DX-14** (A6), **DA-CV-06, 07, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23**, **E1** (HMAC per tenant), **E7** (token di approvazione), **E8** (accessi del superadmin), **E15** (esportazione e verifica dello strumento): decise.

**Aperte**
- **DA-B2-03 — Archivio dei contatori.** (a) Redis; (b) PostgreSQL. Criterio: atomicità, latenza, isolamento tra tenant (Redis non ha RLS: la chiave composta è obbligatoria). Raccomandazione: (a).
- **DA-B2-05 — Origine dell'allowlist.** (a) edge `CAN_USE` in A1; (b) tabella dedicata; (c) solo policy A3. Criterio: una sola fonte di verità. Nessuna raccomandazione; da decidere con DA-A1-02.

---

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: catalogo tool esteso con `domain`, `creates_new` e mappa degli assi, richiesti dal `DecisionRequest` di A3; descritto come il gateway costruisce il `DecisionRequest` e segnalata la fonte mancante di `budget_state` (DA-A3-04); aggiunta DA-B2-05 (allowlist), rinviata qui da DA-A1-04 ma assente; rimando a DA-A1-03 per il trasporto eventi; aggiunto E3 in "È richiesto da". Motivo: interfacce non combacianti. |
| 1.2 | 2026-11-03 | Adeguamento a DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). DA-B2-01 chiusa da DX-01; rimossi assunzione e rischio sulla Beta; tecnologie, fasi e taglia §12 riformulate per costruzione da zero (resta M, senza migrazione di tool); Appendice A rinominata «Riferimenti dal sistema precedente» (idee da riprendere, difetti da non ripetere); span E1 sostituiti da tracce DB-native; aggiunta in §7 la voce «Sicurezza e conformità» (GDPR, NIS2, AI Act, osservabilità AI); DA-B2-04 raccomandazione rivista verso fail-closed e riportata all'utente; DA-B2-05 riformulata senza tabella esistente; nuove DA-B2-06 (retention audit) e DA-B2-07 (destinazioni dei tool fuori perimetro). |
| 1.3 | 2026-11-03 | Recepite le decisioni dell'utente del 2026-11-03. DA-B2-04 decisa (fail-closed): §6 scrive `tool.invoked` prima dell'esecuzione e blocca se fallisce, criterio 3 e test estesi, rischio §11 riformulato. DA-B2-07 decisa: destinazione/giurisdizione/categorie obbligatorie in catalogo, deny se mancano, opt-in extra-UE per tenant (§4-§6, §7, criterio 9, fase 5b, §11). DA-B2-06 assorbita da DX-09: rimossa la retention specifica, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica NIS2 ad A5, B2 invia segnali) e DX-11 (Gravya responsabile art. 28; artt. 12/14 AI Act come buona pratica). Recepite DA-B1-06 (self-hosted UE) e DA-E1-05 (vocabolario GenAI semconv e `traceparent` senza SDK/export OTel). Taglia §12 resta M con perimetro esteso. Motivo: decisioni dell'utente registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Recepite le decisioni dell'utente del 2026-11-03: default di retention DX-09 §5 in §7 (audit 12 mesi, anteprime 30 giorni poi hash, tracce 90 giorni, args solo hash nelle tracce) come variabili di piattaforma; DX-13: superadmin di istanza per catalogo e variabili (limiti di rate limit, retention), modifiche versionate, auditate e fail-closed, accesso cross-tenant solo da superadmin con log; DECISIONS §6: coda con fsync conta come salvato, coda di recupero e segnale A5 per l'audit di esito fallito, tabella di audit minima in ondata 1, egress-proxy B1 con la stessa regola DA-B2-07, base giuridica per gli utenti di Gravya. Nuovi criteri 10-11, test e rischi; DA-B2-04 completata; opt-in extra-UE e DX-14 (A6) restano aperti/da riportare. Motivo: decisioni registrate in DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo v1.2 e al registro v1.6. Valori fissi sostituiti da variabili (rate limit a tre livelli, finestra di idempotenza con massimo, token, coda di recupero, retention; §16 del catalogo). DA-B2-07 con C9, D5, D7 e DA-CV-19: opt-in per destinazione, strumento e sub-responsabile dal superadmin, controllo anche per l'UE, disattivazione e nuovo opt-in. Token unico B1→B2 (DA-CV-13), rotazione con due chiavi (DA-CV-23), credenziali mai rilette e non inserite dal superadmin per le agenzie, transazione unica con A3, segnali senza soglia locale, PV-01 esteso al marketing. Citazioni corrette: Reg. 2024/2690 per i log, evidenze di incidente al posto di «legal hold», flusso NIS2 non attivo, GDPR art. 33(2), DPF solo per l'elenco, AI Act art. 50 dal 2.8.2026. Nuovi criteri 12-16; DA-B2-08..11; DX-14 e opt-in chiusi. Motivo: un solo passaggio prima della revisione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 dell'utente (con le aggiunte E8 ed E15) e revisione unica della v1.5. Hash HMAC per tenant (E1); A3 valuta strumento, sub-responsabile e opposizione, B2 applica con ritardo `a3.policy.propagation_max_s` (E2, DA-B2-08 chiusa); rifiuto delle chiamate verso terzi senza `ai_generated` anche dal ciclo di tool, `audience` e `direct_interaction` nel catalogo, vocabolario unico con C1 (E3, DA-B2-10 chiusa); classe di approvazione assegnata dal superadmin, solo in aggiunta, senza classe → `require_approval`, `REQUIRES_HITL` eliminato (E4, DA-B2-11 chiusa); `approval_token` legato a tenant, tool e hash, consumato da B2, `run_token` non monouso (E7); accessi del superadmin per incidente o assistenza (E8); informativa alle agenzie e opposizione per agenzia (E12); chiave scaduta = errore (DA-B2-09 chiusa); FastAPI (E16, DA-B2-02 chiusa); verifica con scadenza dello strumento di trasferimento e esportabilità dei dati (E15); lettura delle variabili prima di A6 (E5). Transazione unica per ogni esito con `record_not_persisted` come `denied`, `DecisionRequest` completo, `a3.record.persist_timeout_ms` in §5; idempotenza con chiave composta tenant+tool+hash; `retention.tenant_offboarding_choice`; DA-CV-17 col testo deciso; tolte le note «non ancora in DECISIONS». Nuovi criteri 16-17. Motivo: un solo giro di revisione prima dell'approvazione. |
