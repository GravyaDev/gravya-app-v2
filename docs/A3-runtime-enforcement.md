# A3 — Runtime di enforcement

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A3 |
| Nome | Runtime di enforcement |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.2 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Valuta `allow/deny` **prima** di ogni azione di un agente (chiamata di tool, delega, scrittura) usando policy già compilate e caricate in locale. Il master plan la descrive come "Sidecar/OPA agent" (Piano generale §6, riga A3). Le policy sono quelle compilate all'edge da A2. La valutazione avviene sul percorso caldo e **non interroga il grafo A1**.

**Cosa NON fa.**
- Non compila le policy: lo fa A2. Non legge il grafo A1 (qualunque sia il backend, vedi DA-A1-01).
- Non verifica il drift tra policy e grafo: lo fa A4.
- Non conserva l'audit a lungo termine: emette la decisione, A5 la persiste.
- Non sostituisce l'isolamento fra tenant: RLS di PostgreSQL resta il confine dei dati (B1/B2).
- Non gestisce l'interfaccia di approvazione: la gestisce C3. A3 restituisce solo `require_approval`.

**Perché esiste.** Senza un punto di decisione unico e precedente all'azione, i controlli restano sparsi nel codice dei tool e non si possono verificare rispetto ai mandati.

## 3. Contesto e dipendenze

**Dipende da:**
- **A2** Compilatore policy (ondata 2, non ancora documentato). Vedi le assunzioni sotto.
- **A1** Grafo mandati: indirettamente, tramite gli identificativi (agente, mandato, dominio) che compaiono nell'input.
- **E1** Tracing DB-native (PV-02): ogni decisione produce un record di traccia nel modello dati definito da E1, con il vocabolario `gravya.*`. Niente OpenTelemetry.
- **B2** Tool gateway e **B1** Agent runtime: sono i chiamanti, cioè il punto di intercettazione.
- **C3** Punto HITL: riceve gli esiti `require_approval` e rilascia il token di approvazione.
- **A5** Audit trail (ondata 2): consuma gli eventi di decisione.

**È richiesto da:** B2, B1 (valutazione all'avvio del job), C1 e C3, E3 (casi di rifiuto), E2 (autorizzazione delle scritture sul registry: vedi problema aperto in `revisione-ondata-1.md`, perché A3 è progettato per azioni di agenti, non di umani). **A4** (ondata 2) confronta l'hash del bundle caricato.

**Cosa A3 assume da A2 (da confermare quando si scrive A2):**
1. Un bundle per tenant, oppure globale con dati per tenant (**DA-A3-03**), con `bundle_version` e `content_hash` (Piano §6 A2: "con versione e hash").
2. Il formato è Rego/OPA, se si conferma OPA (**DA-A3-01**).
3. Una distribuzione di tipo pull o push, con firma o almeno hash verificabile.
4. Il bundle è autosufficiente: nessuna chiamata al grafo durante la valutazione.

**In ondata 1, senza A2:** si usa un bundle scritto a mano e versionato nel repo (fixture), con lo stesso formato previsto per A2.

**Assunzioni.** L'identità dell'agente e del tenant arriva al runtime già autenticata da B1/B2. Come B1/B2 la garantiscano in v2 è da definire in quei documenti; in gravya-app la stessa domanda era rimasta aperta (kloudify `controlli-e-conformita.md` §1, gravya-app#998), ed è una lezione da non ripetere. Questa parte è **non verificata**.

## 4. Contratti

**Input della decisione (`DecisionRequest`):**

| Campo | Tipo | Note |
|---|---|---|
| `tenant_id` | string | In gravya-app si chiamava `company_id`; il nome definitivo dipende da DX-07 |
| `agent_id`, `agent_version` | string | Da A1 |
| `run_id`, `trace_id` | string | Da B1/E1 |
| `action` | string | Es. `tool.invoke`, `delegate` |
| `tool_id` | string | |
| `tool_class` | oggetto | `domain`, `money_write`, `requires_hitl`, `creates_new` (tassonomia ripresa come idea dai tool di gravya-app) |
| `resource` | oggetto | Assi: `client_ids`, `record_ids`, `campaign_ids`, `object_slugs`. Solo identificativi, mai contenuti dei record (minimizzazione GDPR) |
| `approval_token` | string? | Monouso |
| `budget_state` | oggetto? | Spesa del run e del giorno |

**Output (`Decision`):** `result` ∈ {`allow`, `deny`, `require_approval`}, più `reason`, `axis`, `bundle_version`, `bundle_hash`, `decision_id` e `latency_ms`.

**Eventi emessi:** `policy.decision` (verso A5/E1) e `policy.bundle.loaded` / `policy.bundle.rejected`. Non si mantiene la compatibilità con l'evento `tool.scope.denied` di gravya-app (DX-01): i deny sono `policy.decision` con `result=deny`. Il formato puntato o underscore segue DX-07.

**Eventi consumati:** `policy.bundle.published`, emesso da A2 con versione e hash.

## 5. Interfacce

- **Decisione:** chiamata locale verso il sidecar, oppure libreria in-process (**DA-A3-02**). Con OPA il percorso è `POST /v1/data/gravya/authz/decision`, l'API dati standard di OPA (endpoint da confermare in fase 1).
- **Salute:** `GET /health` restituisce la versione e l'hash del bundle attivo.
- **Bundle:** directory o URL configurabili. In ondata 1 un file nel repo, per esempio `policies/fixtures/`.
- **CLI di test:** `opa test policies/` se si sceglie OPA. In alternativa la suite equivalente nel linguaggio scelto.

## 6. Comportamento

**Flusso principale.** B2 riceve la chiamata di tool → costruisce `DecisionRequest` → A3 valuta → `allow`: B2 esegue · `deny`: errore tipizzato all'agente ed evento · `require_approval`: B2 sospende e passa a C3 → C3 rilascia il token monouso → nuova richiesta con il token → `allow`, poi il token viene consumato.

**Ordine dei controlli** (ripreso come idea da `gravya-app/.../_scope_enforcement.py`, soluzione validata nel sistema precedente; in v2 si riprogetta sul contratto `DecisionRequest`):
1. contratto del run presente;
2. tassonomia completa (default-deny per `MONEY_WRITE`/`REQUIRES_HITL` senza mappa degli assi, salvo `CREATES_NEW`);
3. dominio;
4. assi;
5. tetto di spesa;
6. token HITL.

**Casi limite ed errori:**
- **Bundle assente, scaduto o con hash non valido:** fail-closed (`deny`), con evento `policy.bundle.rejected`.
- **Timeout del sidecar:** `deny`, mai `allow`.
- **Errore nell'emissione dell'evento:** perdere l'evento non comporta mai un allow. Se un `allow` senza record di decisione persistito sia accettabile (best-effort, come in gravya-app) o vada trasformato in `deny` per le scritture è legato a DA-B2-04 e alla tracciabilità richiesta da PV-01: **DA-A3-07, DA RIPORTARE ALL'UTENTE**.
- **Token già usato:** `deny`.
- **Cambio di bundle durante un run:** vale la versione caricata all'inizio della decisione. Ogni decisione registra `bundle_version`.
- **Vocabolario `ALWAYS_HITL`/`MONEY_WRITE`:** mai `allow` senza token. È una regola A5 del progetto (kloudify `controlli-e-conformita.md` §3), da non confondere con il sottoprodotto A5.

## 7. Requisiti non funzionali

- **Latenza:** p99 della decisione ≤ 5 ms in locale, escluso il trasporto di rete (proposta da validare).
- **Sicurezza:** default-deny e fail-closed, il bundle viene verificato con l'hash prima del caricamento, nessun segreto nell'input.
- **Scalabilità:** valutazione stateless. Lo stato (token, spesa) è passato nell'input oppure risolto da B2 (**DA-A3-04**; B2 v1.1 registra la dipendenza nel proprio §6).
- **Osservabilità (DB-native, PV-02):** un record di traccia per decisione nel modello dati di E1, con attributi `gravya.decision.kind=policy`, `gravya.decision.outcome` (= `result`), `gravya.policy.bundle_version`, `gravya.policy.bundle_hash`, con `company_id` come colonna del segmento (E1 §4.1; il nome del tenant segue DX-07). Metriche: `decisions_total{result}` e la latenza, calcolate dagli stessi dati nel DB di Gravya. Nessun SDK, collector o esportatore OpenTelemetry. Se si sceglie OPA, i suoi *decision logs* e la *status/discovery API* verso servizi remoti restano disabilitati: le decisioni escono solo verso E1/A5.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Minimizzazione: input e record di decisione contengono solo identificativi (agente, run, tool, assi della risorsa), mai contenuti di record CRM né prompt. Gli identificativi di clienti/record possono comunque essere dati personali pseudonimizzati. Base giuridica: il log di decisione è una misura di sicurezza e responsabilizzazione (art. 5.2, 32); l'inquadramento preciso (legittimo interesse o obbligo legale) **non è verificato** e va confermato. Retention: definita da A5/E1, non da A3; durata **DA RIPORTARE ALL'UTENTE** (DA-A3-06). Diritti degli interessati: i record sono interrogabili per `tenant_id` e identificativo; la cancellazione o anonimizzazione segue la politica di A5 (conflitto possibile tra diritto alla cancellazione e integrità dell'audit, da decidere in A5).
  - *NIS2 (art. 21).* Controllo degli accessi e default-deny, integrità del bundle (hash, firma se A2 la prevede), fail-closed, registrazione di ogni decisione. Picchi di `deny` o `policy.bundle.rejected` sono segnali utili al rilevamento di incidenti; la procedura di notifica (24 h / 72 h) non è di A3 ma A3 fornisce le evidenze. Tutto il runtime gira nel perimetro controllato da Gravya: nessuna dipendenza da servizi gestiti esterni.
  - *AI Act.* A3 è un presidio di sorveglianza umana (art. 14): le azioni `MONEY_WRITE`/`REQUIRES_HITL` non passano senza approvazione umana (C3). I record di decisione contribuiscono ai log (art. 12) del sistema. La trasparenza art. 50 non riguarda A3 direttamente (non genera contenuti né interagisce con persone). La classificazione di rischio di Gravya **non è verificata** in questo documento.
  - *Osservabilità AI.* Rende osservabile, per ogni azione di un agente: chi l'ha chiesta, su quali risorse, con quale versione di policy, con quale esito e perché (`reason`, `axis`), e se è passata da un'approvazione umana.

## 8. Criteri di accettazione

1. Con il bundle fixture, la suite di policy (`opa test policies/` o equivalente) passa al 100% su almeno 30 casi. Il numero dei casi è una proposta da validare. I casi coprono i sei controlli del §6.
2. Integration test con B2: un tool `MONEY_WRITE` chiamato senza token viene rifiutato (deny) e non produce side effect, perché la riga attesa non viene scritta.
3. Fail-closed: un bundle corrotto o rimosso porta il 100% delle richieste a `deny`, in un test automatico.
4. Nessuna chiamata al grafo sul percorso caldo: il test con il backend di A1 spento resta verde.
5. Benchmark: p99 ≤ 5 ms su 10.000 decisioni (proposta da validare).
6. Il 100% delle decisioni ha un record di traccia E1 (DB-native) con `gravya.policy.bundle_hash`, verificato su una traccia di test.
8. Nessun dato di decisione esce dal perimetro: con OPA, configurazione verificata senza decision logs/status remoti; test che controlla l'assenza di traffico in uscita dal runtime.
7. Il token monouso viene accettato una volta e rifiutato al secondo uso.

## 9. Piano di implementazione

**Fasi ordinate:**
- **F1 — Decisioni bloccanti:** **DA-A3-01** (motore), **DA-A3-02** (sidecar o libreria), **DA-A3-06** (retention) e **DA-A3-07** (allow senza record).
- **F2 — Schema dei contratti:** `DecisionRequest`/`Decision` e bundle fixture scritto da zero; le regole di `_scope_enforcement.py` servono come elenco di requisiti e casi di test, non come codice da tradurre.
- **F3 — Runtime:** caricamento e verifica del bundle, endpoint di decisione, fail-closed.
- **F4 — Integrazione:** con B2 (chokepoint) e con C3 (token).
- **F5 — Osservabilità:** record di traccia DB-native E1 ed eventi verso il futuro A5.
- **F6 — Casi di riferimento:** i casi coperti dall'enforcer di gravya-app diventano casi di test di A3 (stessi esiti attesi dove la regola resta valida). Niente shadow mode contro il codice esistente, che non gira in v2 (DX-01).

**Tecnologie:**
- **OPA/Rego**, dal master plan (Piano §2, tabella Control Plane).
- In alternativa, un valutatore scritto da zero nel linguaggio del runtime (DA-A3-01). Entrambe le opzioni restano nel perimetro: OPA è open source ed eseguibile in locale, quindi PV-02 non la esclude a patto di disabilitarne le funzioni remote.

**Rischi:** vedi §11.

## 10. Test e valutazione

- **Unit:** test di policy per ogni controllo e per ogni asse.
- **Integration:** B2 → A3 → C3 su un tool reale di scrittura CRM (`crm_update_values` usa già il chokepoint).
- **Eval:** casi di E3 con azioni che devono essere rifiutate, con tasso di falsi allow = 0.
- **Security:**
  - manomissione del bundle;
  - replay del token;
  - input con `tenant_id` diverso da quello del contesto;
  - fuzz dei campi `resource`.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Regole di gravya-app perse nella riprogettazione | Casi di riferimento della fase F6 derivati da `_scope_enforcement.py` |
| A2 non esiste in ondata 1: il bundle fixture diventa "la policy" de facto | Fixture marcata come temporanea; A4 la confronta quando arriva |
| Percorsi che bypassano il chokepoint (lezione da gravya-app, dove i councils erano esclusi) | In v2 nessuna eccezione di copertura: ogni azione di agente passa da B2/A3; test che lo verifica |
| Latenza in più per ogni tool | Scelta sidecar o libreria (DA-A3-02), benchmark del CA5 |
| OPA introduce un componente in più da gestire | Valutarlo in DA-A3-01; la Beta di gravya-app non vincola più (DX-01) |
| Funzioni remote di OPA (decision logs, bundle da servizi esterni) attivate per errore | Configurazione bloccata e CA8 |
| Log di decisione con dati personali conservati troppo a lungo | Minimizzazione nell'input, retention decisa con DA-A3-06/A5 |

## 12. Stima e priorità

- **Taglia (costruzione da zero):** M con valutatore proprio in libreria; M-L con OPA in sidecar (bundle Rego, configurazione chiusa, gestione del processo). Non c'è più migrazione dell'enforcer esistente. Stima non verificata.
- **Dipendenze critiche:** B2 (punto di intercettazione), C3 (token), formato del bundle concordato con A2.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (DX-01, PV-03): soluzioni da riprendere come idea e difetti da non ripetere. Nulla di questo codice viene esteso o portato.

**Cosa esiste (file letti):**
- `gravya-app/services/agents/src/tools/_scope_enforcement.py` (letto: header e righe 220-300 circa). Enforcer in modalità enforce che solleva `ScopeViolation` ed emette `tool.scope.denied` best-effort, fail-closed. Implementa gli stessi controlli del §6: contratto, default-deny di tassonomia, dominio, assi `SCOPE_ARG_MAP`, spesa, token HITL monouso in ContextVar.
  - La copertura dichiarata è limitata ai tool `_load_tool`/`AuditedBaseTool`: i councils sono esclusi.
  - Da riprendere come idea: ordine dei controlli, default-deny di tassonomia, token monouso, fail-closed. Da non ripetere: copertura parziale (councils esclusi), regole fisse negli attributi di classe, evento best-effort.
- `gravya-app/services/agents/src/utils/run_scope_contract.py` (letto: header). Contratto di scope immutabile per run.
- `_enforce_scope_contract` è referenziato in `kloud/graph.py`, `executors/generic_executor.py`, `automation/dispatcher.py`, `kloud/write_replay.py`, `tools/_audit.py` e in due tool CRM. Il riferimento è verificato con grep, ma non ho letto i punti di chiamata.
- `gravya-app/server/src/services/grant-evaluator.ts` (letto: header). Grant di capability con ciclo di vita e condizioni DSL compilate (`grant-condition/{parse,compile,evaluate}.ts`) che falliscono chiuse. È di fatto un piccolo "compilatore di policy" lato server, non OPA.
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` §1-3 (letto). Contiene:
  - modello permessi "una chiave per azione, una tabella per azienda" (in costruzione in gravya-app#998, pezzo 4 da riscrivere);
  - le barriere esistenti, che secondo il documento ci sono ma sono "irraggiungibili finché gli agenti non eseguono i tool".
- Ricognizioni `docs/stato/sviluppo.md` e `kloudify.md`: OPA/Rego non trovato in gravya-app.

**Lezioni e divergenze rispetto al master plan:**
1. Il master prevede OPA/Rego in un sidecar. Il codice ha un enforcer custom in Python in-process più un valutatore TS dei grant: **OPA è assente**.
2. Il master fa derivare le policy dal grafo (A1→A2). Nel codice le regole sono attributi di classe dei tool (`DOMAIN`, `MONEY_WRITE`, `REQUIRES_HITL`, `SCOPE_ARG_MAP`, con `REQUIRES_HITL` "fisso nel codice per scelta") e righe di tabella. Non c'è un grafo né un bundle versionato con hash.
3. Il master non prevede eccezioni di copertura. Il codice esclude i councils dal chokepoint.
4. Il modello permessi del progetto (classi Admin, Membro, Kloud, Supervisore, Agente; tabella per azienda) non coincide con i nodi A1 (Agent, Mandate, Domain, Delegation). La mappatura è da decidere in A1/A2.
5. (Superato da DX-01) Il tema "OPA in Beta" non vincola più v2.
6. Da non ripetere: commenti incoerenti sullo stato di attivazione ("NOT YET WIRED" contro "enforce mode"). In v2 lo stato del chokepoint è verificato da test (CA2, CA8).

## Appendice B — Non verificato

- Il corpo completo di `_scope_enforcement.py` (letto solo in parte) e i punti di chiamata nei file che lo referenziano.
- Se l'enforcer sia raggiungibile in produzione o staging. Il docstring di `run_scope_contract.py` dice "NOT YET WIRED", `_scope_enforcement.py` dice "enforce mode" e kloudify dice "irraggiungibile". I commenti sono incoerenti tra loro.
- Contenuto di `capability_check.py`, `compliance/*`, `llm_guard.py`, `tier-policy.ts` (letti solo i nomi).
- Lo stato di gravya-app#998 e l'identità di Kloud sul server.
- Il formato e la distribuzione dei bundle A2 (A2 non è documentato).
- La soglia di latenza (5 ms) e il numero di casi di test (30).
- La base giuridica GDPR dei log di decisione e la classificazione AI Act del sistema.
- Le funzioni remote di OPA da disabilitare: elenco da verificare sulla documentazione della versione scelta.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-A3-01 | Motore di policy | (a) OPA/Rego locale come da master; (b) valutatore proprio scritto da zero con bundle versionato; (c) (b) in ondata 1, poi OPA | Conformità e perimetro (PV-01: entrambe locali), carico operativo, fedeltà al master. Il riuso del codice esistente non è più un criterio (DX-01) | (c), con contratto `DecisionRequest`/`Decision` indipendente dal motore. *Modificata in 1.2* |
| DA-A3-02 | Topologia | (a) sidecar per runtime agente; (b) libreria in-process; (c) servizio centrale | Latenza, isolamento, coerenza con B1 | (a) se si sceglie OPA, altrimenti (b). Da decidere con DX-06 |
| DA-A3-03 | Granularità del bundle | (a) un bundle per tenant; (b) un bundle globale con dati per tenant | Isolamento contro numero di artefatti; da concordare con A2 | (a): rispecchia l'isolamento del master |
| DA-A3-04 | Stato dinamico (spesa, token) | (a) passato nell'input da B2; (b) letto dal runtime | Mantenere stateless la valutazione | (a) |
| DA-A3-05 | Destino di `_scope_enforcement.py` | — | — | **Chiusa da DX-01**: non entra in v2; resta riferimento per regole e casi di test (F6) |
| DA-A3-06 | Retention dei record di decisione | (a) come l'audit A5; (b) breve per i record con identificativi personali, lunga per aggregati | GDPR (limitazione della conservazione) contro obblighi di evidenza NIS2/AI Act art. 12 | **DA RIPORTARE ALL'UTENTE**: durata e liceità non verificate |
| DA-A3-07 | `allow` se il record di decisione non si persiste | (a) best-effort come gravya-app; (b) fail-closed per scritture e `MONEY_WRITE`; (c) fail-closed sempre | Tracciabilità (PV-01) contro disponibilità; coerenza con DA-B2-04 | Propensione per (b), allineata a DA-B2-04, ma **DA RIPORTARE ALL'UTENTE** |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span di decisione allineati ai nomi E1 (`gravya.decision.*`, `gravya.policy.*`, `gravya.company_id`) in §7 e CA6; aggiunti B1, E3, E2 in "È richiesto da" perché quei documenti dichiarano di dipendere da A3; rimando a B2 per `budget_state`. Motivo: interfacce non combacianti tra documenti scritti in parallelo. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): eliminati riuso e parità shadow con `_scope_enforcement.py` (DA-A3-05 chiusa), compatibilità con `tool.scope.denied` rimossa, Appendice A rinominata "Riferimenti dal sistema precedente" come lezioni, rischi Beta rimossi, taglia ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: tracce di decisione DB-native nel modello E1 al posto degli span OTel (§3, §7, CA6, F5), OPA ammessa solo locale con funzioni remote disabilitate (CA8), nuova voce §7 "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI). DA-A3-01 riformulata; nuove DA-A3-06 (retention) e DA-A3-07 (allow senza record), da riportare all'utente. Riferimenti a Neo4j resi neutri rispetto al backend A1. (rev. coerenza) §7: `gravya.company_id` come attributo sostituito dalla colonna `company_id` del segmento (E1 §4.1). |
