# A3 — Runtime di enforcement

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A3 |
| Nome | Runtime di enforcement |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Valuta `allow/deny/require_approval` **prima** di ogni azione di un agente (chiamata di tool, delega, scrittura) con policy già compilate e caricate in locale. Il master plan lo descrive come "Sidecar/OPA agent" (Piano generale §6, riga A3). Le policy sono compilate da A2. La valutazione avviene sul percorso caldo e **non interroga il grafo A1**.

**Cosa NON fa.**
- Non compila le policy (A2) e non legge il grafo A1 (PostgreSQL+RLS, DA-A1-01).
- Non verifica il drift tra policy e grafo (A4).
- Non conserva l'audit a lungo termine: emette la decisione; la persistenza la esegue B2 (§6), poi A5.
- Non consuma i token di approvazione (B2) e non assegna le classi di approvazione (catalogo dei tool di B2).
- Non sostituisce l'isolamento fra tenant: il confine dei dati resta RLS (B1/B2).
- Non gestisce l'interfaccia di approvazione (C3): restituisce `require_approval`.
- Non verifica consensi, opt-out, liste di soppressione né tracciamento: spettano al connettore da D1-D4 (§7).

**Perché esiste.** Un punto di decisione unico e precedente all'azione rende i controlli verificabili rispetto ai mandati, invece di lasciarli sparsi nel codice dei tool.

## 3. Contesto e dipendenze

**Dipende da:**
- **A2** Compilatore policy (ondata 2, non documentato): bundle con `bundle_version`, `content_hash` e firma. Assunzioni sotto.
- **A1** Grafo mandati: solo tramite gli identificativi (agente, mandato, dominio) nell'input.
- **A6** Identità, ruoli e configurazione di piattaforma (DX-14, decisa; ondata 2): registro versionato delle variabili (DX-13, DX-22), configurazione per tenant con l'opt-in extra-UE, pagina delle credenziali, identità dell'attore (DX-21), log degli accessi cross-tenant (DX-18), cifratura a riposo e in transito e gestione delle chiavi (E11), produttore di `platform.config.changed`.
- **E1** Tracing DB-native (PV-02): un record di traccia per decisione, vocabolario `gravya.*`; E1 può adottare nomi GenAI semconv e il formato `traceparent` (DA-E1-05), senza SDK né export OpenTelemetry.
- **B2** Tool gateway: chiamante e punto di intercettazione; esegue la transazione di §6, consuma i token di approvazione, dichiara destinazione, giurisdizione, categorie di dati e destinatario dei tool (DA-B2-07) e assegna la classe di approvazione nel catalogo (E4). **B1** Agent runtime: chiamante indiretto; l'egress-proxy applica lo stesso esito delle destinazioni.
- **C3** Punto HITL: riceve `require_approval` e rilascia il token.
- **A5** Audit trail (ondata 2): consuma le decisioni e riceve i segnali di incidente (DX-10). Nell'ondata 1 la conferma di salvataggio la dà la tabella di audit minima, che A5 poi assorbe (DECISIONS §6); la sua struttura non è ancora definita.
- **F6** Retention, cancellazione ed esportazione (DX-12, ondata 2).

**È richiesto da:** B2, B1 (valutazione all'avvio del job), C1, C3, E3 (casi di rifiuto), E2 (autorizzazione delle scritture sul registry: problema aperto in `revisione-ondata-1.md`, perché A3 è progettato per azioni di agenti). **A4** confronta l'hash del bundle caricato. **A5** riceve i segnali.

**Decisioni trasversali ancora aperte che toccano A3:** DX-03 (trasporto eventi), DX-04 (formato dei contratti; con E16 diventerebbe Pydantic), DX-05 (chi parcheggia la chiamata: B2), DX-06 (topologia, con DA-A3-02), DX-07 (nomi: qui in notazione puntata, `tenant_id` provvisorio).

**Cosa A3 assume da A2 (da confermare quando si scrive A2):**
1. Un bundle per tenant, oppure globale con dati per tenant (DA-A3-03), con versione, hash e **firma**.
2. Formato Rego/OPA se si conferma OPA (DA-A3-01).
3. Distribuzione pull o push. La firma è obbligatoria e A3 la verifica con la chiave di verifica, nella pagina credenziali di piattaforma (catalogo §15: voce da aggiungere); l'hash da solo non basta.
4. Bundle autosufficiente, senza chiamate al grafo.
5. Il bundle incorpora, per ogni tenant, lo stato **effettivo** di ogni destinazione: opt-in attivo, strumento di trasferimento e stato validi (con data di verifica), sub-responsabile autorizzato, eventuale opposizione dell'agenzia.
6. Scadenza e revoca di un mandato (A1) arrivano al bundle entro il ritardo massimo `a3.policy.propagation_max_s`, misurato.

**In ondata 1, senza A2 e senza A6:** bundle scritto a mano nel repo (fixture), stesso formato, firmato con una chiave di sviluppo che esiste solo fuori produzione. Le variabili vengono dall'istantanea versionata (§4). L'ondata 1 non va in produzione (DA-CV-20).

**Assunzione.** L'identità di agente e tenant arriva già autenticata da B1/B2; come la garantiscano non è definito in quei documenti (in gravya-app la domanda era rimasta aperta, gravya-app#998). Non verificato.

## 4. Contratti

**Input (`DecisionRequest`)**, interamente costruito da B2, che deve fornire **tutti** i campi seguenti:

| Campo | Tipo | Note |
|---|---|---|
| `tenant_id` | string | Nome definitivo secondo DX-07 |
| `agent_id`, `agent_version` | string | Da A1 |
| `run_id`, `trace_id` | string | Da B1/E1 |
| `action` | string | Es. `tool.invoke`, `delegate` |
| `tool_id` | string | |
| `tool_class` | oggetto | `approval_class` ∈ {`ALWAYS_HITL`, `MONEY_WRITE`, classe «ordinaria» dichiarata}, più `domain` e `creates_new`. Vocabolario chiuso. Assente = classe non dichiarata (§6). `REQUIRES_HITL` non esiste più (E4) |
| `destination` | oggetto | Nome proposto, da concordare con B2: `destination_id`, `jurisdiction`, `data_categories`, `audience` (destinatario: terzi o interno, con il flag di interazione diretta con persone), tutti dal catalogo dei tool, mai dichiarati dall'autore del workflow (E3) |
| `resource` | oggetto | Assi: `client_ids`, `record_ids`, `campaign_ids`, `object_slugs`. Solo identificativi, mai contenuti |
| `args_hash` | string | HMAC-SHA-256 degli argomenti con chiave per tenant (E1), calcolato da B2; A3 non vede gli argomenti |
| `approval_token` | string? | Legato a tenant, tool e `args_hash` approvati (E7) |
| `budget_state` | oggetto? | Spesa del run e del giorno (DA-A3-04) |

**Dati dei clienti delle agenzie.** `client_ids`, `record_ids` e gli identificativi negli assi sono dati personali pseudonimi (considerando 26): compaiono nel record di decisione (classe `retention.audit_decisions_months`) e possono comparire nel bundle (DA-A3-10). La cancellazione su richiesta del titolare e a fine contratto è eseguita da F6 con A5 (conflitto con l'audit append-only: A5).

**Output (`Decision`):** `result` ∈ {`allow`, `deny`, `require_approval`}, `reason`, `axis`, `bundle_version`, `bundle_hash`, `config_version`, `decision_id`, `latency_ms`. Codici `reason` proposti: `destination_undeclared`, `extra_eu_no_optin`, `transfer_instrument_invalid`, `subprocessor_unauthorized`, `subprocessor_objected`, `third_party_send_not_enabled`, `class_undeclared`, `record_not_persisted`, `config_unreadable`.

**Esportabilità (E15).** I dati di A3 di un tenant (record di decisione: tenant, agente, run, tool, assi come identificativi, esito, `reason`, versioni di bundle e configurazione, istante) sono esportabili con lo strumento di esportazione di F6, in un formato strutturato di uso comune; il formato non è fissato qui (proposta del coordinator, in attesa di conferma dell'utente).

**Eventi emessi** (nomi secondo DX-07): `policy.decision`, `policy.bundle.loaded`, `policy.bundle.rejected`. Nessuna compatibilità con `tool.scope.denied` (DX-01). **Segnali verso A5** (DA-CV-07): `deny`, `policy.bundle.rejected`, mancato salvataggio del record, variabile non leggibile o non valida, deny per destinazione. A3 li invia **senza soglia locale**; le soglie vivono in A5. Sono sempre prodotti e conservati, anche con `incident.nis2_flow_active` falso (C2); A3 non legge l'interruttore.

**Eventi consumati:** `policy.bundle.published` (A2) e `platform.config.changed` (A6, DX-21).

**Variabili usate da A3** (catalogo `catalogo-variabili.md`, unico punto di verità; qui solo i nomi):
- Soglie di sicurezza: `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` (letta da B2, che esegue la transazione). Senza intervallo min/max deciso (D4) non sono attivabili in produzione.
- Ritardo di propagazione: `a3.policy.propagation_max_s` (variabile proposta, da definire con A2 e A6). Un solo criterio per stato di destinazione e mandati, **uguale in A3 e B2** (E2).
- Budget di latenza: `a3.latency.eval_p99_ms`, `a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms`: servono agli **alert**, non bloccano (DECISIONS §6).
- Altre: `hitl.approval_token.ttl_s`, `hitl.approval_required_default`, `tenant.extra_eu_optin.<destination_id>.enabled` con `.transfer_instrument` e `.transfer_instrument_status`, `transfer.instrument_review_interval_days` (variabile proposta, E15), `destination.<destination_id>.subprocessor_authorization`, retention (§7).

**Lettura delle variabili (DX-17, DA-CV-17, E5).** Ogni `Decision` riporta la `config_version`. Prima di A6 tutte le variabili sono lette da **un'istantanea versionata nel repository**, modificabile solo con una PR, tramite una sola interfaccia: è un ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste. I valori «proposta da validare» valgono come primo valore valido, con segnale; i valori «da definire» hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione. In produzione, se una variabile non è leggibile, non è valida o è «da definire», la decisione che ne dipende è `deny` con segnale ad A5; non esiste un ripiego su «valori più restrittivi». **Eccezione:** per le variabili `incident.*` vale il limite di legge, e se `incident.nis2_flow_active` non è leggibile il flusso è trattato come attivo, mai `deny` (DX-10, D1). Produzione e conservazione di segnali e audit sono esclusi dal blocco.

## 5. Interfacce

- **Decisione:** chiamata locale verso il sidecar o libreria in-process (DA-A3-02). Con OPA, `POST /v1/data/gravya/authz/decision` (API dati standard; endpoint da confermare in fase 1).
- **Salute:** `GET /health` restituisce versione e hash del bundle attivo.
- **Bundle:** directory o URL configurabili. In ondata 1 un file nel repo (`policies/fixtures/`).
- **CLI di test:** `opa test policies/` con OPA; altrimenti la suite equivalente nel linguaggio scelto.

## 6. Comportamento

**Flusso.** B2 riceve la chiamata → costruisce `DecisionRequest` → A3 valuta → `allow`: B2 scrive la transazione e poi esegue · `deny`: errore tipizzato ed evento · `require_approval`: B2 sospende e passa a C3 → C3 rilascia il token → nuova richiesta con token → `allow`; B2 consuma il token nella transazione.

**Ordine dei controlli** (idea ripresa dal sistema precedente, App. A; qui riprogettata sul contratto):
1. contratto del run presente;
2. tassonomia: classe dichiarata, default-deny per `MONEY_WRITE` senza mappa degli assi, salvo `creates_new`;
3. destinazione e destinatario (sotto);
4. dominio;
5. assi;
6. tetto di spesa;
7. token HITL.

**Classi di approvazione (E4, DA-CV-15).** Vocabolario unico `ALWAYS_HITL` e `MONEY_WRITE`. Senza token valido mai `allow`: `require_approval`; con token non valido, scaduto o non legato alla chiamata `deny`. Né variabili né contenuto del bundle declassano le due classi; le altre azioni seguono `hitl.approval_required_default`. Un tool **senza classe dichiarata** va in `require_approval` (`class_undeclared`). L'unica fonte della classe è il catalogo dei tool di B2: la assegna il superadmin, versionata e auditata; si può solo aggiungere, toglierla richiede la conferma della seconda persona con accesso superadmin. La chiave di permesso di A1 non assegna classi.

**Token di approvazione (E7).** Legato a tenant, tool e `args_hash` approvati. **A3 verifica** firma (HMAC con chiave nella pagina credenziali; in sostituzione due chiavi valide in parallelo, con data di attivazione e disattivazione, DA-CV-23), scadenza (`hitl.approval_token.ttl_s`) e legame con tenant, tool e hash. **B2 verifica che non sia consumato e lo consuma** nella transazione (registro dei token consumati); A3 resta stateless. Il `run_token` non è monouso e A3 non lo usa.

**Invii verso terzi (E3, DA-CV-18).** I tool con `audience` verso terzi sono **negati nel bundle dell'ondata 1** (`third_party_send_not_enabled`); l'ondata 1 non va in produzione. Da D1-D4 la precondizione (base giuridica registrata, mittente identificato, meccanismo di opposizione) la verifica il connettore; A3 non verifica consensi né opt-out. B2 rifiuta un invio senza `ai_generated` con `model` e `prompt_ref` nei suoi argomenti. Dove l'invio è ammesso, i contenuti verso terzi non sono `ALWAYS_HITL`: decide l'admin agenzia, con audit.

**Destinazioni e extra-UE (E2, DA-B2-07, DA-CV-06, DA-CV-19; GDPR cap. V).** L'opt-in è registrato in A6 dall'admin agenzia per destinazione; A2 lo compila; **A3 valuta** opt-in, strumento di trasferimento e sub-responsabile; B2 e l'egress-proxy di B1 **applicano lo stesso esito**. A3 risponde `deny` se: la destinazione manca; è extra-UE senza opt-in; strumento o stato (aggiornati dal superadmin con fonte e audit, mai dall'agenzia) non sono validi o la loro verifica è oltre `transfer.instrument_review_interval_days` (alla scadenza lo stato diventa non valido, l'opt-in si disattiva e parte un segnale ad A5); manca il sub-responsabile autorizzato con riferimento al DPA, **anche per una destinazione UE**; l'agenzia ha registrato un'opposizione a quel sub-responsabile (E12: da quel momento il tool è negato per lei; l'informativa alle agenzie è di A6). La riattivazione dopo una disattivazione richiede un nuovo opt-in. Il deny arriva entro `a3.policy.propagation_max_s` dal cambio di stato, lo stesso criterio di B2.

**Transazione unica con B2 (DECISIONS §6; DA-A3-07; DA-B2-04).** Il record di decisione di A3 e l'audit di B2 vanno **in un'unica transazione eseguita da B2, per ogni esito**: `allow` (con `tool.invoked`), `deny`, `require_approval` e `rate_limited`, ciascuno con il proprio evento di audit. Un `allow` vale come autorizzazione effettiva solo dopo il commit. Se il commit fallisce o supera `a3.record.persist_timeout_ms`, l'esito è **uno solo**: `deny` con `record_not_persisted` (B2 non esegue e non usa un altro esito), con segnale ad A5. «Salvato» è la scrittura nella tabella di audit (ondata 1: tabella minima, poi A5) oppure in una coda locale **durevole su disco con fsync**; una coda in memoria non conta. Vale per ogni azione.

**Casi limite:**
- **Bundle assente, scaduto (`a3.bundle.max_age_s`), con firma o hash non validi:** `deny`, `policy.bundle.rejected`, segnale ad A5.
- **Timeout della valutazione (`a3.eval.timeout_ms`):** `deny`, mai `allow`.
- **Audit dell'esito fallito dopo l'esecuzione:** l'azione non si annulla; segnale ad A5 e coda di recupero di B2 (DECISIONS §6). A3 fornisce `decision_id`.
- **Cambio di bundle durante un run:** vale la versione caricata all'inizio della decisione.
- **Budget di latenza superato** (`a3.latency.*`): alert, nessun blocco.

## 7. Requisiti non funzionali

- **Latenza.** Tre budget separati (DECISIONS §6): valutazione `a3.latency.eval_p99_ms` (escluso il trasporto), salvataggio sincrono `a3.latency.persist_p99_ms`, totale `a3.latency.total_p99_ms`. Valori «proposta da validare con misura»; per alert, non per bloccare.
- **Sicurezza.** Default-deny e fail-closed (invarianti), bundle verificato per firma e hash prima del caricamento, nessun segreto nell'input. Cifratura a riposo e in transito e gestione delle chiavi: A6 (E11); backup: F6. L'audit append-only è protetto da permessi del database (ruolo solo-inserimento); una verifica di integrità dei record è aperta (DA-A3-11).
- **Scalabilità.** Valutazione stateless; lo stato (spesa) arriva nell'input o è risolto da B2 (DA-A3-04).
- **Osservabilità (DB-native, PV-02).** Un record di traccia per decisione nel modello E1: `gravya.decision.kind=policy`, `gravya.decision.outcome`, `gravya.policy.bundle_version`, `gravya.policy.bundle_hash`, colonna `company_id` del segmento (E1 §4.1), `config_version` nella whitelist del segmento decision (DX-21). Metriche `decisions_total{result}` e latenza dai dati del DB. Nessun SDK, collector o esportatore OpenTelemetry; con OPA i *decision logs* e la *status/discovery API* remoti restano disabilitati. Canale degli alert di latenza: non definito (Appendice B).
- **Sicurezza e conformità (PV-01).**
  - *GDPR.* Gravya è **responsabile del trattamento** (art. 28) per i dati delle agenzie (DX-11); il log di decisione è misura di sicurezza (art. 32). Minimizzazione (art. 5(1)(c)): niente contenuti CRM né prompt, solo identificativi e l'HMAC degli argomenti. Gli identificativi pseudonimi nei trace sono **dati personali** (considerando 26); le linee guida EDPB 01/2025 sono solo in consultazione e non si citano come requisito. Base giuridica (DA-A1-08): del titolare per i dati delle agenzie, di Gravya per i suoi utenti. Il termine verso le agenzie per una violazione è un obbligo del DPA (art. 33(2), senza ore; DA-CV-08, valore aperto). Trasferimenti (artt. 44-46): il DPF copre solo i provider nell'elenco DPF ed è impugnato (C-703/25 P); servono strumento di trasferimento e sub-responsabile autorizzato (art. 28(2) e (4)).
  - *Retention (DX-09).* Rimando a DX-09 e al catalogo (durate di sola lettura finché il DPA non fissa gli intervalli, DA-CV-01). Classi prodotte da A3: record di decisione (`retention.audit_decisions_months`); eventi `policy.bundle.*` (`retention.runtime_events_days`); record di traccia E1 (`retention.traces_days`); log degli accessi cross-tenant (`retention.cross_tenant_access_log_months`, di A6); segnali di incidente (`retention.incident_signals_months`) e audit delle modifiche alle variabili (`retention.config_audit_months`), «da definire» con tetto provvisorio dell'utente prima della produzione (DA-CV-20); coda locale durevole (classe da assegnare a F6, DX-21); backup (`retention.data_backup_days`, DA-CV-22: alla restore le cancellazioni già eseguite si riapplicano). Bundle: artefatti di configurazione per la durata del servizio, salvo se contengono identificativi di clienti (DA-A3-10). Evidenze di incidente: la sospensione non è attivabile finché massimo, riesame e categorie sono «da definire»; vale solo per i dati di Gravya, per quelli delle agenzie servono istruzione nel DPA e parere legale prima di F6 (DA-CV-21). Diritti degli interessati: record interrogabili per `tenant_id` e identificativo.
  - *Accesso ai dati di un tenant (DX-18, DX-19, E8).* Nessun utente di agenzia vede decisioni di altri tenant. Il superadmin vede di default solo dati aggregati senza identificativi (`access.aggregate_min_group_size_count`). Due vie per la singola decisione: (a) **incidente dichiarato dal superadmin**, che abilita la lettura direttamente, con riferimento all'incidente; (b) **richiesta di assistenza**, in cui l'admin agenzia concede l'accesso come parte della richiesta. In entrambi i casi perimetro e durata (`access.superadmin_trace_access_ttl_hours`, dedotto che valga anche per i record di decisione) e ogni accesso è nel log di A6.
  - *NIS2.* Gravya non è oggi soggetto NIS2; la progettazione è «NIS2 compliant ready by design» (DX-10). Per log, conservazione e integrità: Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11, non l'art. 21 della direttiva. Registrazione di ogni decisione, accessi privilegiati e integrità del bundle sono requisiti di progetto. A3 produce sempre i segnali; la notifica (preallarme 24 h, notifica 72 h, relazione finale entro un mese, CSIRT Italia, dalla conoscenza) è di A5, presente ma non attiva (`incident.nis2_flow_active`). Runtime self-hosted UE (DA-B1-06).
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica e comunque per l'alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 (dal 2.8.2026) non riguarda A3, che non genera contenuti né interagisce con persone: etichetta «generato da AI», informativa 50(1) e marcatura 50(2) sono invarianti di C1, C3, B2 e D1-D4.
  - *Marketing (PV-01 esteso).* Dove A3 valuta invii verso terzi (ePrivacy; Codice privacy artt. 122 e 130, registro N-PRIV-IT ◐) li nega nell'ondata 1 (§6); consenso, opt-out e soppressione sono del connettore, variabili rinviate a D1-D4.
  - *Osservabilità AI.* Per ogni azione: chi l'ha chiesta, su quali risorse, con quale versione di policy e configurazione, con quale esito e perché (`reason`, `axis`), se è passata da approvazione umana.

## 8. Criteri di accettazione

Soglie come variabili del catalogo; le dimensioni dei campioni sono parametri del test (DA-CV-04 (b)).
1. Con il bundle fixture, `opa test policies/` (o equivalente) passa al 100% su un campione che copre i sette controlli di §6.
2. Integration test con B2: un tool `MONEY_WRITE` senza token dà `require_approval`; token scaduto, già consumato o con `args_hash`, tool o tenant diversi: `deny`; nessun side effect. Con `hitl.approval_required_default` falso il risultato non cambia. Un tool senza classe dichiarata dà `require_approval`.
3. Un bundle corrotto, rimosso o con firma non valida porta il 100% delle richieste a `deny`.
4. Con il database del grafo A1 spento il test resta verde.
5. Benchmark: p99 della valutazione ≤ `a3.latency.eval_p99_ms`; totale per azione ≤ `a3.latency.total_p99_ms`.
6. Il 100% delle decisioni ha un record di traccia E1 con `gravya.policy.bundle_hash` e `config_version`.
7. Il token è accettato da A3 solo se firma, scadenza e legame sono validi; B2 lo consuma una volta e rifiuta il secondo uso. Con due chiavi HMAC valide in parallelo, un token firmato con la chiave in sostituzione è accettato prima della disattivazione e rifiutato dopo (DA-CV-23).
8. Con OPA: nessun *decision log* né status remoto e nessun traffico in uscita dal runtime.
9. Con il salvataggio reso impossibile, il 100% delle richieste che sarebbero `allow` risulta non eseguito, con **un solo esito** `deny` e `record_not_persisted` e segnale ad A5.
10. Coda locale senza fsync confermato: record non salvato. Con fsync: l'azione procede.
11. **Transazione unica.** Per ciascun esito (`allow`, `deny`, `require_approval`, `rate_limited`) esiste, dopo il commit, il record di A3 insieme all'evento di audit di B2; con un errore iniettato dopo il primo inserimento non ne resta nessuno e il tool non viene eseguito. Un salvataggio più lento di `a3.latency.persist_p99_ms` ma entro `a3.record.persist_timeout_ms` genera un alert e non un `deny`.
12. **Variabili.** Cambiando `a3.eval.timeout_ms` dall'istantanea, senza rilascio di codice, la nuova soglia vale dalla decisione successiva e il record riporta la nuova `config_version`. In produzione, con variabile non leggibile, non valida o «da definire», le decisioni dipendenti sono `deny` con segnale; con `incident.nis2_flow_active` non leggibile non si produce alcun `deny`. Prima della produzione le tre variabili `a3.*` di sicurezza hanno min/max deciso (D4), verificato dal catalogo.
13. **Destinazioni.** `deny` per: destinazione non dichiarata; extra-UE senza opt-in; stato dello strumento non valido o verifica scaduta; destinazione UE senza sub-responsabile autorizzato; opposizione dell'agenzia. Dopo il cambio di stato il deny arriva entro `a3.policy.propagation_max_s`, lo stesso valore usato dal test di B2.
14. **Mandati.** Dopo la revoca o la scadenza di un mandato in A1, A3 nega entro `a3.policy.propagation_max_s`.
15. **Segnali.** Un solo `deny`, un solo `policy.bundle.rejected` o un solo mancato salvataggio producono ciascuno un segnale ad A5 (tabella minima in ondata 1), senza soglia locale e con `incident.nis2_flow_active` falso.
16. **Accesso ai dati di un tenant.** Un admin di agenzia non legge decisioni di un altro tenant. Il superadmin, senza incidente dichiarato né accesso concesso dall'agenzia, riceve solo aggregati; con incidente dichiarato o accesso concesso legge una singola decisione entro `access.superadmin_trace_access_ttl_hours`, e ogni lettura produce una riga nel log di A6 con il riferimento.
17. **Invii verso terzi.** Nel bundle fixture dell'ondata 1 un tool con `audience` verso terzi è negato (`third_party_send_not_enabled`).
18. **Esportazione.** I record di decisione di un tenant sono estratti dallo strumento di F6 con i campi dichiarati in §4 (verificabile quando F6 esiste).

## 9. Piano di implementazione

**Fasi:**
- **F1 — Decisioni bloccanti:** DA-A3-01 (motore) e DA-A3-02 (topologia, con DX-06); DA-A3-10 prima di F2.
- **F2 — Contratti:** `DecisionRequest`/`Decision` (con `destination`, `args_hash`, `config_version`) concordati con B2, e bundle fixture scritto da zero; le regole del sistema precedente servono come requisiti e casi di test.
- **F3 — Runtime:** caricamento e verifica di firma e hash del bundle, endpoint di decisione, fail-closed.
- **F4 — Integrazione:** con B2 (chokepoint e transazione unica, token) e con C3.
- **F5 — Osservabilità:** traccia E1 DB-native, tabella di audit minima, segnali verso A5.
- **F5b — Variabili:** istantanea versionata nel repository con interfaccia unica (E5); da sostituire con il registro di A6.
- **F6 — Casi di riferimento:** i casi dell'enforcer di gravya-app diventano casi di test, senza shadow mode (DX-01).

**Tecnologie (master plan, Piano §2 e §6):** OPA/Rego, oppure valutatore proprio (DA-A3-01). OPA è eseguibile in locale: PV-02 non la esclude con le funzioni remote disabilitate. Il backend è in Python (E16, approvata): il valutatore proprio sarebbe in Python.

**Rischi:** §11.

## 10. Test e valutazione

- **Unit:** test di policy per ogni controllo, asse e codice `reason`.
- **Integration:** B2 → A3 → C3 su un tool reale di scrittura CRM.
- **Eval:** casi di E3 con azioni da rifiutare, falsi allow = 0 (gate senza eccezioni sui casi bloccanti).
- **Security:** manomissione o firma falsa del bundle; replay del token su altra chiamata, altro tenant, altri argomenti; `tenant_id` diverso dal contesto; fuzz di `resource` e `destination`; salvataggio fallito o lento; coda senza fsync; variabili manomesse, fuori intervallo o «da definire»; accesso cross-tenant senza incidente o concessione; opt-in attivato dal superadmin (rifiutato da A6, verificato lì).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Regole del sistema precedente perse | Casi di riferimento F6 |
| A2 assente: la fixture diventa «la policy» de facto | Fixture temporanea con chiave di sviluppo; A4 la confronta; ondata 1 non in produzione |
| Percorsi che bypassano B2 (councils di gravya-app) | Nessuna eccezione; test di copertura |
| Latenza in più per ogni tool | Scelta sidecar/libreria; CA5, CA11; budget con alert |
| Componente OPA in più; funzioni remote attivate per errore | DA-A3-01; configurazione bloccata; CA8 |
| Dati personali nei record e nel bundle conservati troppo | Minimizzazione; DX-09; DA-A3-10 |
| Soglia `a3.*` modificata male dal superadmin | Intervallo min/max obbligatorio prima della produzione (D4), versioning, audit, fail-closed; CA12 |
| Un guasto della persistenza blocca tutte le azioni | Scelta accettata (DA-A3-07, DA-B2-04); segnale ad A5; CA9 |
| Stato di una destinazione o un mandato non ancora propagato | `a3.policy.propagation_max_s`, uguale in A3 e B2; CA13, CA14 |
| Token di approvazione riusato su un'altra chiamata | Legame a tenant, tool e hash; consumo in B2; CA2, CA7 |
| Audit append-only modificabile da chi ha accesso al database | Ruolo solo-inserimento; verifica di integrità: DA-A3-11 |

## 12. Stima e priorità

- **Taglia:** M con valutatore proprio in libreria; M-L con OPA in sidecar. Stima non verificata.
- **Dipendenze critiche:** B2 (intercettazione, transazione, token), C3, formato e firma del bundle con A2, registro delle variabili e credenziali di A6.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (DX-01, PV-03): idee da riprendere e difetti da non ripetere; nulla viene esteso o portato. **Questi riferimenti sono ripresi dalla v1.4 e non sono stati riverificati sul codice nelle versioni 1.5 e 1.6.**

- `gravya-app/services/agents/src/tools/_scope_enforcement.py`: enforcer con `ScopeViolation` ed evento `tool.scope.denied` best-effort. Controlli: contratto, default-deny di tassonomia, dominio, assi `SCOPE_ARG_MAP`, spesa, token HITL monouso. Idee da riprendere: ordine dei controlli, default-deny di tassonomia, token monouso. Da non ripetere: copertura parziale (councils esclusi), regole fisse negli attributi di classe, evento best-effort, audit saltato.
- `run_scope_contract.py`: contratto di scope immutabile per run. `grant-evaluator.ts`: grant con condizioni DSL che falliscono chiuse (piccolo compilatore di policy lato server, non OPA).
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` §1-3: modello permessi «una chiave per azione» (gravya-app#998) e barriere «irraggiungibili finché gli agenti non eseguono i tool».

**Lezioni:** (1) OPA è assente nel sistema precedente (enforcer custom in-process); (2) le regole sono attributi di classe dei tool, non un bundle versionato con hash; (3) in v2 nessuna eccezione di copertura; (4) il modello permessi (Admin, Membro, Kloud, Supervisore, Agente) non coincide con i nodi A1: mappatura in A1/A2; (5) commenti incoerenti sullo stato di attivazione: in v2 lo stato è verificato da test.

## Appendice B — Non verificato

- Tutta l'Appendice A. In particolare l'**ordine dei controlli** di §6 poggia su `_scope_enforcement.py` (non ricontrollato); l'inserimento del controllo «destinazione» è una proposta di questo documento.
- Contratto con B2: nomi dei campi (`destination`, `audience`, `args_hash`, `approval_class`), come B2 esprime una classe «ordinaria» dichiarata, codici `reason`, copertura della transazione per `rate_limited`. Sono richieste di questo documento a B2; B2 non è stato riletto in questa versione.
- Struttura della tabella di audit minima di ondata 1 e come A5 la assorbe; schema di A6 (configurazione per tenant, log cross-tenant, credenziali); formato di firma dei bundle e chiave di verifica (voce da aggiungere al catalogo §15).
- Valori, intervalli min/max e nomi di `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`; valore e nome di `a3.policy.propagation_max_s` e `transfer.instrument_review_interval_days` (proposti qui, non ancora nel catalogo); valori dei budget `a3.latency.*` (proposta da validare con misura).
- Come arriva ad A3 `hitl.approval_required_default` per le azioni diverse da `ALWAYS_HITL` e `MONEY_WRITE` (A2, C3).
- Canale e destinatario degli alert di latenza; classe di retention della coda locale durevole (F6, DX-21).
- Applicazione di `access.superadmin_trace_access_ttl_hours` ai record di decisione: dedotta dal modello E1.
- Le decisioni E1-E16 del 2026-11-04 sono citate dal blocco di decisioni approvato dall'utente; la loro registrazione in DECISIONS.md non è stata verificata.
- Norme (registro v1.6): Codice privacy artt. 122 e 130 ed ePrivacy ◐ (solo estratti); DPF: elenco non consultato e impugnazione C-703/25 P ◐; Reg. 2024/2690 applicabile solo se Gravya è fornitore cloud in ambito NIS2 (ambito non accertato).
- Funzioni remote di OPA da disabilitare: elenco da verificare sulla documentazione della versione scelta.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-A3-01 | Motore di policy | (a) OPA/Rego locale; (b) valutatore proprio; (c) (b) in ondata 1, poi OPA | Conformità e perimetro, carico operativo, fedeltà al master | (c), con contratto indipendente dal motore |
| DA-A3-02 | Topologia | (a) sidecar; (b) libreria; (c) servizio centrale | Latenza, isolamento, coerenza con B1; da decidere con DX-06 | (a) con OPA, altrimenti (b) |
| DA-A3-03 | Granularità del bundle | (a) per tenant; (b) globale con dati per tenant | Isolamento contro numero di artefatti; con A2 | (a) |
| DA-A3-04 | Stato dinamico (spesa) | (a) nell'input da B2; (b) letto dal runtime | Valutazione stateless | (a) |
| DA-A3-10 | Identificativi di clienti nel bundle compilato | (a) il bundle contiene solo riferimenti a mandati e assi, e gli identificativi di clienti restano nell'input e nel record; (b) il bundle li contiene e segue una classe di retention propria | Minimizzazione (GDPR art. 5(1)(c) e (e)); DECISIONS §5 prevede «durata del servizio» per i bundle, che presuppone assenza di dati personali | (a); in caso di (b), classe assegnata da F6. **DA RIPORTARE ALL'UTENTE** (dati) |
| DA-A3-11 | Integrità dei record di decisione append-only | (a) ruolo di database solo-inserimento e controlli di accesso; (b) catena di hash dei record verificata periodicamente | Reg. 2024/2690 all. 3.2.5 (protezione dei log da modifiche; vale se Gravya è in ambito NIS2, design «ready»); costo | (a) in ondata 1, (b) da valutare in A5 |
| — | Intervalli min/max di `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`, `a3.policy.propagation_max_s` | — | — | **Aperti** (DECISIONS §4, D4): valori con A5 e A6 prima della produzione |

**Decise o chiuse (per riferimento):**
- DA-A3-05 (DX-01), DA-A3-06 (assorbita da DX-09), DA-A3-07 (fail-closed sul record, coda con fsync, tabella minima), DX-14 (A6), soglia di latenza complessiva (DECISIONS §6: budget separati, alert), opt-in extra-UE (DECISIONS §6: A6 → A2 → A3 → B2, per destinazione), DA-CV-07, DA-CV-15, DA-CV-18..23.
- **DA-A3-08** (propagazione e chi valuta strumento e sub-responsabile): chiusa da **E2**: valuta A3 sulla policy di A2, B2 e l'egress-proxy applicano lo stesso esito; un solo ritardo massimo misurato, `a3.policy.propagation_max_s`, uguale in A3 e B2 (valore da definire con A2 e A6).
- **DA-A3-09** (invii verso terzi nell'ondata 1): chiusa da **E3**: negati nel bundle; precondizione al connettore da D1-D4; B2 rifiuta senza `ai_generated`.
- Classi di approvazione (**E4**), token di approvazione (**E7**), variabili prima di A6 (**E5**), accesso ai dati dei tenant (**E8** con l'aggiunta), esportazione dei dati (**E15**, formato in attesa di conferma).

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span di decisione allineati ai nomi E1 (`gravya.decision.*`, `gravya.policy.*`, `gravya.company_id`) in §7 e CA6; aggiunti B1, E3, E2 in "È richiesto da" perché quei documenti dichiarano di dipendere da A3; rimando a B2 per `budget_state`. Motivo: interfacce non combacianti tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): eliminati riuso e parità shadow con `_scope_enforcement.py` (DA-A3-05 chiusa), compatibilità con `tool.scope.denied` rimossa, Appendice A rinominata "Riferimenti dal sistema precedente" come lezioni, rischi Beta rimossi, taglia ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: tracce di decisione DB-native nel modello E1 al posto degli span OTel (§3, §7, CA6, F5), OPA ammessa solo locale con funzioni remote disabilitate (CA8), nuova voce §7 "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI). DA-A3-01 riformulata; nuove DA-A3-06 (retention) e DA-A3-07 (allow senza record), da riportare all'utente. Riferimenti a Neo4j resi neutri rispetto al backend A1. (rev. coerenza) §7: `gravya.company_id` come attributo sostituito dalla colonna `company_id` del segmento (E1 §4.1). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-A3-07 decisa (fail-closed sul record di decisione, coerente con DA-B2-04): §6, nota di latenza §7, CA9, test di sicurezza, F3, nuovo rischio. DA-A3-06 assorbita da DX-09: retention rimandata alla politica unica, elencate le classi di dati prodotte. §7 allineata a DX-10 (segnali ad A5 per la notifica NIS2) e DX-11 (Gravya responsabile art. 28; artt. 12/14 AI Act ridotti a buona pratica); rimossa la relativa voce dall'Appendice B. Recepite DA-A1-01 (PostgreSQL+RLS), DA-B1-06 (self-hosted UE), DA-E1-05 (vocabolario GenAI semconv/traceparent ammesso in E1). CA riordinati (7, 8). Taglia invariata. Motivo: decisioni registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: default di retention di DECISIONS §5 (decisioni 12 mesi, eventi 90 giorni). DX-13: soglie di A3 e durate come variabili di piattaforma gestite dal superadmin (tabella §4, `config_version` nel record, fail-closed sulla configurazione), accesso cross-tenant solo da superadmin con log. DECISIONS §6 decise: coda durevole con fsync conta come salvato, segnale ad A5 e coda di recupero dopo l'esecuzione, tabella di audit minima in ondata 1, base giuridica DA-A1-08. Nuovi CA10-12, test, F5b, rischi; DX-14 citata come dipendenza proposta da riportare; latenza complessiva e opt-in extra-UE restano aperte. Motivo: decisioni registrate in DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo v1.2 e al registro v1.6. Latenza: tre budget come variabili `a3.latency.*` per alert, non per bloccare. Record di decisione e audit `tool.invoked` in un'unica transazione eseguita da B2. Variabili rinominate (`_s`, `_months`, `_days`) e valori fissi sostituiti dai nomi; tolto il ripiego «valore più restrittivo» a favore di DX-17/DA-CV-17; `a3.*` di sicurezza con intervallo min/max richiesto prima della produzione (D4). Nuovo controllo «destinazione» e opt-in extra-UE per destinazione (A6→A2→A3→B2, DA-CV-06, DA-CV-19). `ALWAYS_HITL`/`MONEY_WRITE` non declassabili da UI (DA-CV-15); senza token l'esito è `require_approval` (prima il CA2 diceva `deny`, incoerente con il flusso). Segnali ad A5 senza soglia locale (DA-CV-07). Accesso del superadmin allineato a DX-18/DX-19. Citazioni corrette: log e integrità → Reg. 2024/2690 all. 3.2 e 11 (non «NIS2 art. 21»); notifica 24 h/72 h/un mese, CSIRT Italia, flusso presente ma non attivo; GDPR art. 33(2); DPF; EDPB 01/2025; AI Act dal 2.8.2026 e Reg. 2026/1744; PV-01 esteso al marketing. Retention per classe con rimando a DX-09, DA-CV-20..22. Chiavi in parallelo (DA-CV-23). DX-14 e opt-in segnati come decisi. Nuove DA-A3-08 e DA-A3-09. Appendice A dichiarata non riverificata; testo tagliato dove superato. Motivo: un solo giro di revisione prima dell'approvazione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 del 2026-11-04 (con le aggiunte E8 ed E15) e rilievi della revisione unica della v1.5 (plan-auditor, compliance-auditor A1-A3-B1). E2: A3 valuta strumento e sub-responsabile, DA-A3-08 chiusa, un solo ritardo `a3.policy.propagation_max_s` con B2; scadenza della verifica dello strumento (E15) e opposizione delle agenzie (E12). E3: invii verso terzi negati nel bundle dell'ondata 1, DA-A3-09 chiusa, CA16 sostituito dal CA17 su regola decisa. E4: vocabolario `ALWAYS_HITL`/`MONEY_WRITE`, tool senza classe in `require_approval`, classe assegnata solo nel catalogo di B2. E7: token legato a tenant, tool e `args_hash`; A3 verifica, B2 consuma. E1: `args_hash` HMAC. E5: istantanea versionata nel repository, valori di sviluppo solo fuori produzione. E8: due vie di accesso del superadmin (incidente dichiarato, assistenza concessa dall'agenzia). E11: cifratura e chiavi ad A6. E15: esportabilità dei dati con lo strumento di F6. Transazione unica: per ogni esito, un solo esito `deny` con `record_not_persisted`, campi richiesti a B2. Firma del bundle verificata con chiave nella pagina credenziali; scadenza e revoca dei mandati entro il ritardo massimo. `incident.nis2_flow_active` illeggibile = flusso attivo, non `deny`; A3 non legge l'interruttore. Dati dei clienti dichiarati (DA-A3-10). Rimosse le note «non ancora in DECISIONS» su DA-CV-18..23. Nuove DA-A3-10 e DA-A3-11. Motivo: un solo giro di revisione, poi approvazione dell'utente. |
