# A3 — Runtime di enforcement

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A3 |
| Nome | Runtime di enforcement |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.5 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Valuta `allow/deny/require_approval` **prima** di ogni azione di un agente (chiamata di tool, delega, scrittura) con policy già compilate e caricate in locale. Il master plan lo descrive come "Sidecar/OPA agent" (Piano generale §6, riga A3). Le policy sono compilate da A2. La valutazione avviene sul percorso caldo e **non interroga il grafo A1**.

**Cosa NON fa.**
- Non compila le policy (A2) e non legge il grafo A1 (PostgreSQL+RLS, DA-A1-01).
- Non verifica il drift tra policy e grafo (A4).
- Non conserva l'audit a lungo termine: emette la decisione; la persistenza la esegue B2 (§6), poi A5.
- Non sostituisce l'isolamento fra tenant: il confine dei dati resta RLS (B1/B2).
- Non gestisce l'interfaccia di approvazione (C3): restituisce `require_approval`.
- Non verifica consensi, opt-out, liste di soppressione né tracciamento (§7, DA-A3-09).

**Perché esiste.** Un punto di decisione unico e precedente all'azione rende i controlli verificabili rispetto ai mandati, invece di lasciarli sparsi nel codice dei tool.

## 3. Contesto e dipendenze

**Dipende da:**
- **A2** Compilatore policy (ondata 2, non documentato): bundle con `bundle_version` e `content_hash`. Assunzioni sotto.
- **A1** Grafo mandati: solo tramite gli identificativi (agente, mandato, dominio) nell'input.
- **A6** Identità, ruoli e configurazione di piattaforma (DX-14, decisa; ondata 2): registro versionato delle variabili (DX-13, DX-22), configurazione per tenant che contiene l'opt-in extra-UE, identità dell'attore (DX-21), log degli accessi cross-tenant (DX-18), produttore di `platform.config.changed`.
- **E1** Tracing DB-native (PV-02): un record di traccia per decisione, vocabolario `gravya.*`; E1 può adottare nomi GenAI semconv e il formato `traceparent` (DA-E1-05), senza SDK né export OpenTelemetry.
- **B2** Tool gateway: chiamante e punto di intercettazione; scrive il record di decisione (§6) e dichiara destinazione, giurisdizione e categorie di dati dei tool (DA-B2-07). **B1** Agent runtime: chiamante indiretto.
- **C3** Punto HITL: riceve `require_approval` e rilascia il token monouso.
- **A5** Audit trail (ondata 2): consuma le decisioni e riceve i segnali di incidente (DX-10). Nell'ondata 1 la conferma di salvataggio la dà la tabella di audit minima, che A5 poi assorbe (DECISIONS §6); la sua struttura non è ancora definita.
- **F6** Retention e cancellazione (DX-12, ondata 2): applica le scadenze.

**È richiesto da:** B2, B1 (valutazione all'avvio del job), C1, C3, E3 (casi di rifiuto), E2 (autorizzazione delle scritture sul registry: problema aperto in `revisione-ondata-1.md`, perché A3 è progettato per azioni di agenti). **A4** confronta l'hash del bundle caricato. **A5** riceve i segnali.

**Decisioni trasversali ancora aperte che toccano A3:** DX-03 (trasporto eventi), DX-04 (formato dei contratti), DX-05 (chi parcheggia la chiamata: B2), DX-06 (topologia, con DA-A3-02), DX-07 (nomi: qui in notazione puntata, `tenant_id` provvisorio).

**Cosa A3 assume da A2 (da confermare quando si scrive A2):**
1. Un bundle per tenant, oppure globale con dati per tenant (DA-A3-03), con versione e hash.
2. Formato Rego/OPA se si conferma OPA (DA-A3-01).
3. Distribuzione pull o push, con hash verificabile ed eventuale firma.
4. Bundle autosufficiente, senza chiamate al grafo.
5. Il bundle incorpora, per ogni tenant, lo stato **effettivo** di ogni destinazione: opt-in attivo, strumento di trasferimento e stato validi, sub-responsabile autorizzato (§6).

**In ondata 1, senza A2:** bundle scritto a mano e versionato nel repo (fixture), stesso formato. L'ondata 1 non va in produzione (DA-CV-20).

**Assunzione.** L'identità di agente e tenant arriva già autenticata da B1/B2; come la garantiscano non è definito in quei documenti (in gravya-app la domanda era rimasta aperta, gravya-app#998). Non verificato.

## 4. Contratti

**Input (`DecisionRequest`):**

| Campo | Tipo | Note |
|---|---|---|
| `tenant_id` | string | Nome definitivo secondo DX-07 |
| `agent_id`, `agent_version` | string | Da A1 |
| `run_id`, `trace_id` | string | Da B1/E1 |
| `action` | string | Es. `tool.invoke`, `delegate` |
| `tool_id` | string | |
| `tool_class` | oggetto | `domain`, `money_write`, `requires_hitl`, `creates_new`. Vocabolario chiuso, assegnato dal catalogo dei tool (B2), non da UI |
| `destination` | oggetto | Nome proposto, da concordare con B2: `destination_id`, `jurisdiction`, `data_categories`, come dichiarati dal tool (DA-B2-07) |
| `resource` | oggetto | Assi: `client_ids`, `record_ids`, `campaign_ids`, `object_slugs`. Solo identificativi, mai contenuti |
| `approval_token` | string? | Monouso |
| `budget_state` | oggetto? | Spesa del run e del giorno (DA-A3-04) |

**Output (`Decision`):** `result` ∈ {`allow`, `deny`, `require_approval`}, `reason`, `axis`, `bundle_version`, `bundle_hash`, `config_version`, `decision_id`, `latency_ms`. Codici `reason` proposti per i casi di §6: `destination_undeclared`, `extra_eu_no_optin`, `transfer_instrument_invalid`, `subprocessor_unauthorized`, `record_not_persisted`, `config_unreadable`.

**Eventi emessi** (i nomi seguono DX-07): `policy.decision`, `policy.bundle.loaded`, `policy.bundle.rejected`. Non c'è compatibilità con `tool.scope.denied` di gravya-app (DX-01). **Segnali verso A5** (§6, DA-CV-07): `policy.decision` con `deny`, `policy.bundle.rejected`, mancato salvataggio del record, configurazione non leggibile o non valida, deny per destinazione. A3 li invia **senza soglia locale**; le soglie vivono in A5.

**Eventi consumati:** `policy.bundle.published` (A2) e `platform.config.changed` (A6, DX-21).

**Variabili usate da A3** (catalogo `catalogo-variabili.md`, unico punto di verità per default, intervalli e pagina; qui solo i nomi):
- Soglie di sicurezza: `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` (quest'ultima è letta da B2, che esegue la transazione). Sono «da definire» e senza intervallo min/max deciso (D4): **non attivabili in produzione**. Fino ad allora in ondata 1 valgono valori di prova nel file fixture, con lo stesso schema del registro, esplicitamente non conformi a DX-22.
- Budget di latenza: `a3.latency.eval_p99_ms`, `a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms`. Servono agli **alert**, non bloccano (DECISIONS §6). Il blocco per tempo è dato solo dai timeout sopra.
- Altre: `hitl.approval_token.ttl_s`, `hitl.approval_required_default`, `tenant.extra_eu_optin.<destination_id>.enabled` con `.transfer_instrument` e `.transfer_instrument_status`, `destination.<destination_id>.subprocessor_authorization`, `incident.nis2_flow_active`, retention (§7).

**Regole di lettura (DX-17, DA-CV-17).** Ogni `Decision` riporta la `config_version` in vigore (DX-21). Se una variabile non è leggibile o non è valida, o è «da definire», la decisione che ne dipende è `deny`, con segnale ad A5; non esiste un ripiego su «valori più restrittivi». Produzione e conservazione dei segnali e dell'audit sono esclusi dal blocco.

## 5. Interfacce

- **Decisione:** chiamata locale verso il sidecar o libreria in-process (DA-A3-02). Con OPA, `POST /v1/data/gravya/authz/decision` (API dati standard; endpoint da confermare in fase 1).
- **Salute:** `GET /health` restituisce versione e hash del bundle attivo.
- **Bundle:** directory o URL configurabili. In ondata 1 un file nel repo (`policies/fixtures/`).
- **CLI di test:** `opa test policies/` con OPA; altrimenti la suite equivalente nel linguaggio scelto.

## 6. Comportamento

**Flusso.** B2 riceve la chiamata → costruisce `DecisionRequest` → A3 valuta → `allow`: B2 salva e poi esegue · `deny`: errore tipizzato ed evento · `require_approval`: B2 sospende e passa a C3 → C3 rilascia il token monouso → nuova richiesta con token → `allow`, token consumato.

**Ordine dei controlli** (idea ripresa dal sistema precedente, App. A; qui riprogettata sul contratto):
1. contratto del run presente;
2. tassonomia completa: default-deny per `MONEY_WRITE`/`REQUIRES_HITL` senza mappa degli assi, salvo `CREATES_NEW`;
3. destinazione (nuovo, sotto);
4. dominio;
5. assi;
6. tetto di spesa;
7. token HITL.

**Classi `ALWAYS_HITL` e `MONEY_WRITE`.** Senza token valido non c'è mai `allow`: l'esito è `require_approval`; con token non valido o già usato è `deny`. Questo non dipende da alcuna variabile né dal contenuto del bundle: `hitl.approval_required_default` governa solo le altre classi e la classificazione non è declassabile da UI (DA-CV-15, §18 del catalogo). I contenuti verso terzi (email, post, messaggi) **non** sono una classe `ALWAYS_HITL` nell'ondata 1: decide l'admin agenzia, con audit; da riesaminare con D1-D4 (DA-CV-18).

**Destinazioni e extra-UE (DA-B2-07, DA-CV-06, DA-CV-19; GDPR cap. V).** L'opt-in è registrato in A6 dall'admin agenzia, per destinazione dichiarata; A2 lo compila nel bundle; A3 lo valuta; B2 lo applica. Il superadmin non può attivarlo. A3 risponde `deny` se: la destinazione manca (`destination_undeclared`); la destinazione è extra-UE e l'opt-in non è attivo; lo strumento di trasferimento o il suo stato (aggiornati dal superadmin con fonte e audit, mai dall'agenzia) non sono validi; manca il sub-responsabile autorizzato con riferimento al DPA, **anche per una destinazione UE**. Se lo strumento cade, A6 disattiva l'opt-in e invia il segnale ad A5; la riattivazione richiede un nuovo opt-in dell'agenzia (DECISIONS §6). Il bundle è compilato, quindi A3 vede lo stato dopo il ricaricamento: il ritardo massimo di propagazione è aperto (DA-A3-08).

**Persistenza del record e audit di B2 in un'unica transazione (DECISIONS §6).** Il record di decisione di A3 e l'audit `tool.invoked` di B2 vanno **in un'unica transazione eseguita da B2**, per evitare la doppia scrittura. Di conseguenza `allow` di A3 vale come autorizzazione effettiva solo dopo il commit: se il commit fallisce o supera `a3.record.persist_timeout_ms`, B2 non esegue e registra l'esito come `deny` con `record_not_persisted` (DA-A3-07, fail-closed, coerente con DA-B2-04). «Salvato» significa scritto nella tabella di audit (ondata 1: tabella minima, poi A5) oppure in una coda locale **durevole su disco con fsync** confermato; una coda in memoria non conta. Vale per ogni azione, non solo per le scritture.

**Casi limite:**
- **Bundle assente, scaduto (`a3.bundle.max_age_s`) o con hash non valido:** `deny`, evento `policy.bundle.rejected`, segnale ad A5.
- **Timeout della valutazione (`a3.eval.timeout_ms`):** `deny`, mai `allow`.
- **Audit dell'esito fallito dopo l'esecuzione:** l'azione non si annulla; segnale ad A5 e coda di recupero di B2 che ritenta (DECISIONS §6). A3 fornisce `decision_id`.
- **Cambio di bundle durante un run:** vale la versione caricata all'inizio della decisione.
- **Chiavi HMAC del token monouso:** durante una sostituzione due chiavi sono valide in parallelo, con data di attivazione e disattivazione (DA-CV-23); un token firmato con la chiave in scadenza è accettato fino alla disattivazione. Se il bundle è firmato da A2, la chiave di verifica segue la stessa regola.
- **Budget di latenza superato** (`a3.latency.*`): alert, nessun blocco.

## 7. Requisiti non funzionali

- **Latenza.** Tre budget separati (DECISIONS §6, decisa): valutazione `a3.latency.eval_p99_ms` (escluso il trasporto), salvataggio sincrono `a3.latency.persist_p99_ms`, totale per azione `a3.latency.total_p99_ms`. I valori sono «proposta da validare con misura» (catalogo §4). Sono variabili per alert, non per bloccare.
- **Sicurezza.** Default-deny e fail-closed (invarianti, DX-17, DA-A3-07), hash verificato prima del caricamento, nessun segreto nell'input.
- **Scalabilità.** Valutazione stateless; lo stato (token, spesa) arriva nell'input o è risolto da B2 (DA-A3-04).
- **Osservabilità (DB-native, PV-02).** Un record di traccia per decisione nel modello E1: `gravya.decision.kind=policy`, `gravya.decision.outcome`, `gravya.policy.bundle_version`, `gravya.policy.bundle_hash`, colonna `company_id` del segmento (E1 §4.1; nome secondo DX-07), `config_version` nella whitelist del segmento decision (DX-21). Metriche `decisions_total{result}` e latenza calcolate dai dati del DB di Gravya. Nessun SDK, collector o esportatore OpenTelemetry. Con OPA, *decision logs* e *status/discovery API* remoti restano disabilitati. Il canale degli alert di latenza non è definito (Appendice B).
- **Sicurezza e conformità (PV-01).**
  - *GDPR.* Gravya è **responsabile del trattamento** (art. 28) per i dati delle agenzie (DX-11); il log di decisione è misura di sicurezza (art. 32). Minimizzazione (art. 5(1)(c)): input e record contengono solo identificativi, mai contenuti CRM né prompt. Gli identificativi pseudonimi nei trace sono **dati personali** (considerando 26): vanno trattati con conservazione limitata (art. 5(1)(e)) e cancellazione coerente; le linee guida EDPB 01/2025 sono solo in consultazione e non sono citate come requisito. Base giuridica (DA-A1-08): per i dati delle agenzie del titolare; per gli utenti Gravya di Gravya. Il termine verso le agenzie per una violazione è un obbligo del DPA (art. 33(2), senza ore; DA-CV-08, valore aperto). Trasferimenti: opt-in e controlli di §6; per un provider USA il DPF vale solo se è nell'elenco DPF ed è impugnato (C-703/25 P); servono strumento e sub-responsabile validi (art. 28(2) e (4); artt. 44-46). La verifica operativa dello stato è del superadmin (DA-CV-19).
  - *Retention (DX-09).* Rimando a DX-09 e DECISIONS §5; le durate sono nel catalogo e di sola lettura finché il DPA non fissa gli intervalli (DA-CV-01). Classi prodotte da A3: record di decisione (`retention.audit_decisions_months`); eventi `policy.bundle.*` (`retention.runtime_events_days`); record di traccia E1 (`retention.traces_days`); log degli accessi cross-tenant (`retention.cross_tenant_access_log_months`, proprietà di A6); segnali di incidente (`retention.incident_signals_months`, durata «da definire», tetto provvisorio dell'utente prima della produzione: DA-CV-20); audit delle modifiche alle variabili (`retention.config_audit_months`, idem); coda locale durevole (classe non assegnata, la assegna F6, DX-21); backup (`retention.data_backup_days`, DA-CV-22). Bundle: artefatti di configurazione per la durata del servizio. «Evidenze di incidente»: la sospensione delle scadenze non è attivabile finché massimo, riesame e categorie sono «da definire» e, per i dati delle agenzie, serve istruzione nel DPA e parere legale prima di F6 (DA-CV-21). Diritti degli interessati: record interrogabili per `tenant_id` e identificativo; il conflitto cancellazione/audit append-only è di A5.
  - *Accesso cross-tenant.* Nessun utente di agenzia vede decisioni di altri tenant. Il superadmin vede di default solo dati aggregati senza identificativi (`access.aggregate_min_group_size_count`); la singola decisione solo su richiesta dell'agenzia o per un incidente, entro l'istruzione del titolare (art. 28(3)(a)), con log degli accessi di A6 (DX-18, DX-19).
  - *NIS2.* Gravya non è oggi soggetto NIS2; la progettazione è «NIS2 compliant ready by design» (DX-10). Per log, conservazione e integrità si cita il Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11, non l'art. 21 della direttiva. Le misure (registrazione di ogni decisione, accessi privilegiati, integrità del bundle) sono requisiti di progetto. A3 produce sempre i segnali verso A5, anche con `incident.nis2_flow_active` falso; la notifica (preallarme 24 h, notifica 72 h, relazione finale entro un mese, CSIRT Italia, dalla conoscenza) è di A5 e il flusso è presente ma non attivo. Il runtime è self-hosted UE (DA-B1-06).
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica e comunque per l'alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 (applicabile dal 2.8.2026) non riguarda A3, che non genera contenuti né interagisce con persone: etichetta «generato da AI», informativa 50(1) e marcatura 50(2) sono invarianti di C1, C3 e D1-D4.
  - *Marketing (PV-01 esteso).* Dove A3 valuta azioni di invio verso terzi, non verifica consenso, opt-out, liste di soppressione né tracciamento (ePrivacy; Codice privacy artt. 122 e 130; registro N-PRIV-IT ◐): le variabili sono rinviate a D1-D4. Rischio e scelta provvisoria in DA-A3-09.
  - *Osservabilità AI.* Per ogni azione: chi l'ha chiesta, su quali risorse, con quale versione di policy e configurazione, con quale esito e perché (`reason`, `axis`), se è passata da approvazione umana.

## 8. Criteri di accettazione

Le soglie citano le variabili del catalogo. Le dimensioni dei campioni sono parametri del test (DA-CV-04 (b)).
1. Con il bundle fixture, `opa test policies/` (o equivalente) passa al 100% su un campione che copre i sette controlli di §6.
2. Integration test con B2: un tool `MONEY_WRITE` senza token produce `require_approval`, con token già usato `deny`; in entrambi i casi nessun side effect. Con `hitl.approval_required_default` falso per l'agenzia il risultato non cambia (DA-CV-15).
3. Un bundle corrotto o rimosso porta il 100% delle richieste a `deny`.
4. Con il database del grafo A1 spento il test resta verde.
5. Benchmark: p99 della valutazione ≤ `a3.latency.eval_p99_ms`; totale per azione ≤ `a3.latency.total_p99_ms`.
6. Il 100% delle decisioni ha un record di traccia E1 con `gravya.policy.bundle_hash` e `config_version`.
7. Il token monouso è accettato una volta e rifiutato la seconda. Con due chiavi HMAC valide in parallelo, un token firmato con la chiave in sostituzione è accettato prima della data di disattivazione e rifiutato dopo (DA-CV-23).
8. Con OPA: configurazione senza *decision logs* né status remoti e nessun traffico in uscita dal runtime, verificato da test.
9. Con il salvataggio reso impossibile, il 100% delle richieste che sarebbero `allow` risulta non eseguito, con `record_not_persisted` e segnale ad A5.
10. Coda locale senza fsync confermato: record non salvato. Con fsync: l'azione procede.
11. **Transazione unica.** Con un errore iniettato dopo l'inserimento del record di decisione, né il record né `tool.invoked` risultano persistiti e il tool non viene eseguito. Un salvataggio più lento di `a3.latency.persist_p99_ms` ma entro `a3.record.persist_timeout_ms` genera un alert e non un `deny`.
12. **Variabili.** Cambiando `a3.eval.timeout_ms` dal registro senza rilascio, la nuova soglia vale dalla decisione successiva e il record riporta la nuova `config_version`. Con registro non leggibile, valore non valido (tipo, positivo, min ≤ max) o «da definire», le decisioni dipendenti sono `deny` con segnale ad A5. Prima della produzione: le tre variabili `a3.*` di sicurezza hanno min/max deciso (D4), verificato dal catalogo.
13. **Destinazioni.** `deny` per: destinazione non dichiarata; extra-UE senza opt-in; opt-in attivo ma stato dello strumento non valido; destinazione UE senza sub-responsabile autorizzato. Dopo la disattivazione dell'opt-in e il ricaricamento del bundle la destinazione è negata (ritardo massimo: DA-A3-08).
14. **Segnali.** Un solo `deny`, un solo `policy.bundle.rejected` o un solo mancato salvataggio producono ciascuno un segnale ad A5 (nella tabella minima in ondata 1), senza soglia locale (DA-CV-07).
15. **Accesso cross-tenant.** La lettura di decisioni di un altro tenant fallisce per un admin di agenzia; per il superadmin, senza richiesta dell'agenzia o incidente, restituisce solo aggregati; con richiesta o incidente produce una riga nel log di A6.
16. **Marketing.** Nel bundle fixture dell'ondata 1 un tool di invio verso terzi è negato secondo DA-A3-09, finché D1-D4 non forniscono il controllo di consenso.

## 9. Piano di implementazione

**Fasi:**
- **F1 — Decisioni bloccanti:** DA-A3-01 (motore) e DA-A3-02 (topologia, con DX-06); DA-A3-08 e DA-A3-09 prima della fase 4.
- **F2 — Contratti:** `DecisionRequest`/`Decision` (con `destination` e `config_version`) e bundle fixture scritto da zero; le regole del sistema precedente servono come requisiti e casi di test, non come codice.
- **F3 — Runtime:** caricamento e verifica del bundle, endpoint di decisione, fail-closed.
- **F4 — Integrazione:** con B2 (chokepoint e transazione unica) e con C3 (token).
- **F5 — Osservabilità:** traccia E1 DB-native, tabella di audit minima, segnali verso A5.
- **F5b — Variabili:** lettura dal registro A6; in ondata 1 file fixture con lo stesso schema, non conforme a DX-22 e non utilizzabile in produzione.
- **F6 — Casi di riferimento:** i casi dell'enforcer di gravya-app diventano casi di test, senza shadow mode (DX-01).

**Tecnologie (master plan, Piano §2 e §6):** OPA/Rego, oppure valutatore proprio nel linguaggio del runtime (DA-A3-01). OPA è eseguibile in locale: PV-02 non la esclude se le funzioni remote sono disabilitate.

**Rischi:** §11.

## 10. Test e valutazione

- **Unit:** test di policy per ogni controllo, asse e codice `reason`.
- **Integration:** B2 → A3 → C3 su un tool reale di scrittura CRM.
- **Eval:** casi di E3 con azioni da rifiutare, falsi allow = 0 (gate senza eccezioni sui casi bloccanti).
- **Security:** manomissione del bundle; replay del token; `tenant_id` diverso dal contesto; fuzz di `resource` e `destination`; salvataggio fallito o lento; coda senza fsync; variabili manomesse, fuori intervallo o «da definire»; accesso cross-tenant senza ruolo; opt-in attivato dal superadmin (deve essere rifiutato da A6, verificato lì).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Regole del sistema precedente perse | Casi di riferimento F6 |
| A2 assente: la fixture diventa «la policy» de facto | Fixture temporanea; A4 la confronta; ondata 1 non in produzione |
| Percorsi che bypassano B2 (councils di gravya-app) | Nessuna eccezione; test di copertura |
| Latenza in più per ogni tool | Scelta sidecar/libreria; CA5, CA11; budget `a3.latency.*` con alert |
| Componente OPA in più | Valutare in DA-A3-01 |
| Funzioni remote di OPA attivate per errore | Configurazione bloccata; CA8 |
| Log di decisione con dati personali conservati troppo | Minimizzazione; DX-09 |
| Soglia `a3.*` modificata male dal superadmin | Intervallo min/max obbligatorio prima della produzione (D4), versioning, audit, fail-closed; CA12 |
| Un guasto della persistenza blocca tutte le azioni | Scelta accettata (DA-A3-07, DA-B2-04); segnale ad A5; CA9 |
| Opt-in extra-UE ancora attivo dopo la caduta dello strumento, per ritardo del bundle | DA-A3-08; CA13 |
| Strumenti di invio verso terzi senza controllo di consenso nell'ondata 1 | DA-A3-09; CA16 |
| Nessun segnale perché nessuna soglia locale: A5 non esiste in ondata 1 | I segnali vanno comunque nella tabella minima, conservati sempre (C2) |

## 12. Stima e priorità

- **Taglia:** M con valutatore proprio in libreria; M-L con OPA in sidecar. Stima non verificata.
- **Dipendenze critiche:** B2 (intercettazione e transazione), C3 (token), formato del bundle con A2, registro delle variabili di A6.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (DX-01, PV-03): idee da riprendere e difetti da non ripetere; nulla viene esteso o portato. **Questi riferimenti sono ripresi dalla v1.4 e non sono stati riverificati sul codice nella v1.5**.

- `gravya-app/services/agents/src/tools/_scope_enforcement.py`: enforcer con `ScopeViolation` ed evento `tool.scope.denied` best-effort. Controlli: contratto, default-deny di tassonomia, dominio, assi `SCOPE_ARG_MAP`, spesa, token HITL monouso. Idee da riprendere: ordine dei controlli, default-deny di tassonomia, token monouso. Da non ripetere: copertura parziale (councils esclusi), regole fisse negli attributi di classe, evento best-effort, audit saltato.
- `run_scope_contract.py`: contratto di scope immutabile per run. `grant-evaluator.ts`: grant con condizioni DSL che falliscono chiuse (piccolo compilatore di policy lato server, non OPA).
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` §1-3: modello permessi «una chiave per azione» (gravya-app#998) e barriere «irraggiungibili finché gli agenti non eseguono i tool».

**Lezioni:** (1) OPA è assente nel sistema precedente (enforcer custom in-process); (2) le regole sono attributi di classe dei tool, non un bundle versionato con hash; (3) in v2 nessuna eccezione di copertura; (4) il modello permessi (Admin, Membro, Kloud, Supervisore, Agente) non coincide con i nodi A1: mappatura in A1/A2; (5) commenti incoerenti sullo stato di attivazione: in v2 lo stato è verificato da test.

## Appendice B — Non verificato

- Tutta l'Appendice A: ripresa dalla v1.4, non riletta nella v1.5. In particolare l'**ordine dei controlli** di §6 poggia su `_scope_enforcement.py` (non ricontrollato) e l'inserimento del controllo «destinazione» è una proposta di questo documento.
- Il contratto con B2: nome dei campi `destination`, codici `reason`, e l'esatta scrittura dell'esito `deny` per `record_not_persisted` quando il commit fallisce. Il testo di B2 su `tool.invoked` e sui campi di destinazione non è stato riletto per intero in questa versione; la copertura della transazione unica per gli esiti `deny` e `require_approval` non è verificata.
- Struttura della tabella di audit minima di ondata 1 (non ancora definita) e come A5 la assorbe.
- Valori, intervalli min/max e nomi di `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` (da definire con A5 e A6); valori dei budget `a3.latency.*` (proposta da validare con misura); nome e destinatario degli alert di latenza.
- Come arrivano ad A3 le impostazioni di `hitl.approval_required_default` per le classi diverse da `ALWAYS_HITL` e `MONEY_WRITE` (compilate da A2, definite in C3): non verificato.
- Formato e distribuzione dei bundle A2; se A2 firma i bundle e dove sta la chiave di verifica (non presente tra le voci credenziali del catalogo §15).
- Funzioni remote di OPA da disabilitare: elenco da verificare sulla documentazione della versione scelta.
- Decisioni del 2026-11-04 DA-CV-18..23 comunicate dall'utente il 2026-11-04: non ancora in DECISIONS.md. Nel catalogo 1.2 DA-CV-18..23 sono ancora «aperte».
- Norme (registro v1.6): Codice privacy artt. 122 e 130 e ePrivacy ◐ (solo estratti); DPF: elenco non consultato e impugnazione C-703/25 P ◐; Reg. 2024/2690 applicabile solo se Gravya è fornitore cloud in ambito NIS2 (ambito non accertato).
- Identità dell'attore e log cross-tenant: schema di A6 non ancora redatto.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-A3-01 | Motore di policy | (a) OPA/Rego locale; (b) valutatore proprio; (c) (b) in ondata 1, poi OPA | Conformità e perimetro, carico operativo, fedeltà al master | (c), con contratto indipendente dal motore |
| DA-A3-02 | Topologia | (a) sidecar; (b) libreria; (c) servizio centrale | Latenza, isolamento, coerenza con B1; da decidere con DX-06 | (a) con OPA, altrimenti (b) |
| DA-A3-03 | Granularità del bundle | (a) per tenant; (b) globale con dati per tenant | Isolamento contro numero di artefatti; con A2 | (a) |
| DA-A3-04 | Stato dinamico (spesa, token) | (a) nell'input da B2; (b) letto dal runtime | Valutazione stateless | (a) |
| DA-A3-08 | Propagazione dello stato di uno strumento di trasferimento al bundle | (a) ricompilazione del bundle di A2 a ogni cambio di stato, con ritardo massimo misurato; (b) documento di dati separato ricaricato da A3 | Ritardo massimo tra caduta dello strumento e deny; GDPR artt. 44-46 e 28(2); semplicità del percorso caldo | (a), con il ritardo massimo come variabile del catalogo (da definire con A2 e A6). **DA RIPORTARE ALL'UTENTE** (trasferimenti) |
| DA-A3-09 | Strumenti di invio verso terzi (email, SMS, post) nell'ondata 1, senza controllo di consenso né opt-out | (a) negati nel bundle fino ai controlli di D1-D4; (b) ammessi con approvazione dell'admin agenzia (DA-CV-18 (b)) | PV-01 esteso: conformità prima della velocità; Codice privacy art. 130 (◐) | (a). **DA RIPORTARE ALL'UTENTE** (perimetro e conformità) |
| — | Intervalli min/max di `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` | — | — | **Aperti** in DECISIONS §4 («Intervalli min/max…»; D4): valori con A5 e A6 prima della produzione |

**Chiuse o decise (per riferimento):** DA-A3-05 (DX-01: l'enforcer esistente non entra in v2); DA-A3-06 (assorbita da DX-09); DA-A3-07 (decisa 2026-11-03: fail-closed sul record, coda con fsync, tabella minima); DX-14 (decisa: A6); soglia di latenza complessiva (decisa, DECISIONS §6: budget separati, alert); opt-in extra-UE (decisa, DECISIONS §6: A6 → A2 → A3 → B2, per destinazione, C9); DA-CV-07 (segnali senza soglia locale); DA-CV-15 (non declassabile da UI); DA-CV-18 (b), DA-CV-19 (a), DA-CV-20 (b), DA-CV-21 (a), DA-CV-22 (a), DA-CV-23 (a) comunicate dall'utente il 2026-11-04, in attesa di registrazione in DECISIONS.md.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span di decisione allineati ai nomi E1 (`gravya.decision.*`, `gravya.policy.*`, `gravya.company_id`) in §7 e CA6; aggiunti B1, E3, E2 in "È richiesto da" perché quei documenti dichiarano di dipendere da A3; rimando a B2 per `budget_state`. Motivo: interfacce non combacianti tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): eliminati riuso e parità shadow con `_scope_enforcement.py` (DA-A3-05 chiusa), compatibilità con `tool.scope.denied` rimossa, Appendice A rinominata "Riferimenti dal sistema precedente" come lezioni, rischi Beta rimossi, taglia ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: tracce di decisione DB-native nel modello E1 al posto degli span OTel (§3, §7, CA6, F5), OPA ammessa solo locale con funzioni remote disabilitate (CA8), nuova voce §7 "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI). DA-A3-01 riformulata; nuove DA-A3-06 (retention) e DA-A3-07 (allow senza record), da riportare all'utente. Riferimenti a Neo4j resi neutri rispetto al backend A1. (rev. coerenza) §7: `gravya.company_id` come attributo sostituito dalla colonna `company_id` del segmento (E1 §4.1). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-A3-07 decisa (fail-closed sul record di decisione, coerente con DA-B2-04): §6, nota di latenza §7, CA9, test di sicurezza, F3, nuovo rischio. DA-A3-06 assorbita da DX-09: retention rimandata alla politica unica, elencate le classi di dati prodotte. §7 allineata a DX-10 (segnali ad A5 per la notifica NIS2) e DX-11 (Gravya responsabile art. 28; artt. 12/14 AI Act ridotti a buona pratica); rimossa la relativa voce dall'Appendice B. Recepite DA-A1-01 (PostgreSQL+RLS), DA-B1-06 (self-hosted UE), DA-E1-05 (vocabolario GenAI semconv/traceparent ammesso in E1). CA riordinati (7, 8). Taglia invariata. Motivo: decisioni registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: default di retention di DECISIONS §5 (decisioni 12 mesi, eventi 90 giorni). DX-13: soglie di A3 e durate come variabili di piattaforma gestite dal superadmin (tabella §4, `config_version` nel record, fail-closed sulla configurazione), accesso cross-tenant solo da superadmin con log. DECISIONS §6 decise: coda durevole con fsync conta come salvato, segnale ad A5 e coda di recupero dopo l'esecuzione, tabella di audit minima in ondata 1, base giuridica DA-A1-08. Nuovi CA10-12, test, F5b, rischi; DX-14 citata come dipendenza proposta da riportare; latenza complessiva e opt-in extra-UE restano aperte. Motivo: decisioni registrate in DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo v1.2 e al registro v1.6. Latenza: tre budget come variabili `a3.latency.*` per alert, non per bloccare. Record di decisione e audit `tool.invoked` in un'unica transazione eseguita da B2. Variabili rinominate (`_s`, `_months`, `_days`) e valori fissi sostituiti dai nomi; tolto il ripiego «valore più restrittivo» a favore di DX-17/DA-CV-17; `a3.*` di sicurezza con intervallo min/max richiesto prima della produzione (D4). Nuovo controllo «destinazione» e opt-in extra-UE per destinazione (A6→A2→A3→B2, DA-CV-06, DA-CV-19). `ALWAYS_HITL`/`MONEY_WRITE` non declassabili da UI (DA-CV-15); senza token l'esito è `require_approval` (prima il CA2 diceva `deny`, incoerente con il flusso). Segnali ad A5 senza soglia locale (DA-CV-07). Accesso del superadmin allineato a DX-18/DX-19. Citazioni corrette: log e integrità → Reg. 2024/2690 all. 3.2 e 11 (non «NIS2 art. 21»); notifica 24 h/72 h/un mese, CSIRT Italia, flusso presente ma non attivo; GDPR art. 33(2); DPF; EDPB 01/2025; AI Act dal 2.8.2026 e Reg. 2026/1744; PV-01 esteso al marketing. Retention per classe con rimando a DX-09, DA-CV-20..22. Chiavi in parallelo (DA-CV-23). DX-14 e opt-in segnati come decisi. Nuove DA-A3-08 e DA-A3-09. Appendice A dichiarata non riverificata; testo tagliato dove superato. Motivo: un solo giro di revisione prima dell'approvazione. |
