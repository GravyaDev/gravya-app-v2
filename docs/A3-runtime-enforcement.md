# A3 — Runtime di enforcement

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A3 |
| Nome | Runtime di enforcement |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.1 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Valuta `allow/deny` **prima** di ogni azione di un agente (chiamata di tool, delega, scrittura) usando policy già compilate e caricate in locale. Il master plan la descrive come "Sidecar/OPA agent" (Piano generale §6, riga A3). Le policy sono quelle compilate all'edge da A2. La valutazione avviene sul percorso caldo e **non interroga il grafo A1**.

**Cosa NON fa.**
- Non compila le policy: lo fa A2. Non legge Neo4j.
- Non verifica il drift tra policy e grafo: lo fa A4.
- Non conserva l'audit a lungo termine: emette la decisione, A5 la persiste.
- Non sostituisce l'isolamento fra tenant: RLS di PostgreSQL resta il confine dei dati (B1/B2).
- Non gestisce l'interfaccia di approvazione: la gestisce C3. A3 restituisce solo `require_approval`.

**Perché esiste.** Senza un punto di decisione unico e precedente all'azione, i controlli restano sparsi nel codice dei tool e non si possono verificare rispetto ai mandati.

## 3. Contesto e dipendenze

**Dipende da:**
- **A2** Compilatore policy (ondata 2, non ancora documentato). Vedi le assunzioni sotto.
- **A1** Grafo mandati: indirettamente, tramite gli identificativi (agente, mandato, dominio) che compaiono nell'input.
- **E1** Tracing: ogni decisione è uno span.
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

**Assunzioni.** L'identità dell'agente e del tenant arriva al runtime già autenticata da B1/B2. Nel codice esistente l'identità di Kloud sul server è una domanda aperta (kloudify `controlli-e-conformita.md` §1, gravya-app#998). Questa parte è **non verificata**.

## 4. Contratti

**Input della decisione (`DecisionRequest`):**

| Campo | Tipo | Note |
|---|---|---|
| `tenant_id` | string | Nel codice attuale corrisponde a `company_id` |
| `agent_id`, `agent_version` | string | Da A1 |
| `run_id`, `trace_id` | string | Da B1/E1 |
| `action` | string | Es. `tool.invoke`, `delegate` |
| `tool_id` | string | |
| `tool_class` | oggetto | `domain`, `money_write`, `requires_hitl`, `creates_new` (stessi attributi dei tool attuali) |
| `resource` | oggetto | Assi: `client_ids`, `record_ids`, `campaign_ids`, `object_slugs` |
| `approval_token` | string? | Monouso |
| `budget_state` | oggetto? | Spesa del run e del giorno |

**Output (`Decision`):** `result` ∈ {`allow`, `deny`, `require_approval`}, più `reason`, `axis`, `bundle_version`, `bundle_hash`, `decision_id` e `latency_ms`.

**Eventi emessi:** `policy.decision` (verso A5/E1) e `policy.bundle.loaded` / `policy.bundle.rejected`. Per i deny resta compatibile l'evento esistente `tool.scope.denied`.

**Eventi consumati:** `policy.bundle.published`, emesso da A2 con versione e hash.

## 5. Interfacce

- **Decisione:** chiamata locale verso il sidecar, oppure libreria in-process (**DA-A3-02**). Con OPA il percorso è `POST /v1/data/gravya/authz/decision`, l'API dati standard di OPA (endpoint da confermare in fase 1).
- **Salute:** `GET /health` restituisce la versione e l'hash del bundle attivo.
- **Bundle:** directory o URL configurabili. In ondata 1 un file nel repo, per esempio `policies/fixtures/`.
- **CLI di test:** `opa test policies/` se si sceglie OPA. In alternativa la suite equivalente nel linguaggio scelto.

## 6. Comportamento

**Flusso principale.** B2 riceve la chiamata di tool → costruisce `DecisionRequest` → A3 valuta → `allow`: B2 esegue · `deny`: errore tipizzato all'agente ed evento · `require_approval`: B2 sospende e passa a C3 → C3 rilascia il token monouso → nuova richiesta con il token → `allow`, poi il token viene consumato.

**Ordine dei controlli** (ripreso dal codice esistente, `_scope_enforcement.py` §4):
1. contratto del run presente;
2. tassonomia completa (default-deny per `MONEY_WRITE`/`REQUIRES_HITL` senza mappa degli assi, salvo `CREATES_NEW`);
3. dominio;
4. assi;
5. tetto di spesa;
6. token HITL.

**Casi limite ed errori:**
- **Bundle assente, scaduto o con hash non valido:** fail-closed (`deny`), con evento `policy.bundle.rejected`.
- **Timeout del sidecar:** `deny`, mai `allow`.
- **Errore nell'emissione dell'evento:** la decisione resta valida. È la stessa semantica di `_enforce_deny`, dove perdere l'evento non comporta mai un allow.
- **Token già usato:** `deny`.
- **Cambio di bundle durante un run:** vale la versione caricata all'inizio della decisione. Ogni decisione registra `bundle_version`.
- **Vocabolario `ALWAYS_HITL`/`MONEY_WRITE`:** mai `allow` senza token. È una regola A5 del progetto (kloudify `controlli-e-conformita.md` §3), da non confondere con il sottoprodotto A5.

## 7. Requisiti non funzionali

- **Latenza:** p99 della decisione ≤ 5 ms in locale, escluso il trasporto di rete (proposta da validare).
- **Sicurezza:** default-deny e fail-closed, il bundle viene verificato con l'hash prima del caricamento, nessun segreto nell'input.
- **Scalabilità:** valutazione stateless. Lo stato (token, spesa) è passato nell'input oppure risolto da B2 (**DA-A3-04**; B2 v1.1 registra la dipendenza nel proprio §6).
- **Osservabilità:** uno span `gravya.decision` per decisione con attributi `gravya.decision.kind=policy`, `gravya.decision.outcome` (= `result`), `gravya.policy.bundle_version`, `gravya.policy.bundle_hash` e `gravya.company_id` (nomi allineati a E1 §4.1). Metriche: `decisions_total{result}` e la latenza.

## 8. Criteri di accettazione

1. Con il bundle fixture, la suite di policy (`opa test policies/` o equivalente) passa al 100% su almeno 30 casi. Il numero dei casi è una proposta da validare. I casi coprono i sei controlli del §6.
2. Integration test con B2: un tool `MONEY_WRITE` chiamato senza token viene rifiutato (deny) e non produce side effect, perché la riga attesa non viene scritta.
3. Fail-closed: un bundle corrotto o rimosso porta il 100% delle richieste a `deny`, in un test automatico.
4. Nessuna chiamata al grafo sul percorso caldo: il test con Neo4j spento resta verde.
5. Benchmark: p99 ≤ 5 ms su 10.000 decisioni (proposta da validare).
6. Il 100% delle decisioni ha uno span E1 con `gravya.policy.bundle_hash`, verificato su una trace di test.
7. Il token monouso viene accettato una volta e rifiutato al secondo uso.

## 9. Piano di implementazione

**Fasi ordinate:**
- **F1 — Decisioni bloccanti:** **DA-A3-01** (motore), **DA-A3-02** (sidecar o libreria) e **DA-A3-05** (destino di `_scope_enforcement.py`).
- **F2 — Schema dei contratti:** `DecisionRequest`/`Decision` e bundle fixture che traduce le regole già codificate in `_scope_enforcement.py`.
- **F3 — Runtime:** caricamento e verifica del bundle, endpoint di decisione, fail-closed.
- **F4 — Integrazione:** con B2 (chokepoint) e con C3 (token).
- **F5 — Osservabilità:** span E1 ed eventi verso il futuro A5.
- **F6 — Parità:** test che confrontano il nuovo runtime con l'enforcer esistente sugli stessi casi (shadow).

**Tecnologie:**
- **OPA/Rego**, dal master plan (Piano §2, tabella Control Plane).
- In alternativa, Python per riusare il codice esistente, `services/agents`.

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
| Due enforcer paralleli (Python esistente + OPA) che divergono | DA-A3-05, test di parità della fase F6 |
| A2 non esiste in ondata 1: il bundle fixture diventa "la policy" de facto | Fixture marcata come temporanea; A4 la confronta quando arriva |
| Percorsi che bypassano il chokepoint (councils, oggi esclusi per scelta) | Mantenere la guardia `assert_no_council_invoking_tools` finché A3 non copre i councils |
| Latenza in più per ogni tool | Scelta sidecar o libreria (DA-A3-02), benchmark del CA5 |
| OPA introduce un servizio nuovo da gestire in Beta | Regola del 02/11 sulle priorità post-Beta (kloudify): da far decidere all'utente |

## 12. Stima e priorità

- **Taglia:** M (L se DA-A3-01 sceglie OPA con migrazione completa dell'enforcer esistente).
- **Dipendenze critiche:** B2 (punto di intercettazione), C3 (token), formato del bundle concordato con A2.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Allineamento con lo stato attuale

**Cosa esiste (file letti):**
- `gravya-app/services/agents/src/tools/_scope_enforcement.py` (letto: header e righe 220-300 circa). Enforcer in modalità enforce che solleva `ScopeViolation` ed emette `tool.scope.denied` best-effort, fail-closed. Implementa gli stessi controlli del §6: contratto, default-deny di tassonomia, dominio, assi `SCOPE_ARG_MAP`, spesa, token HITL monouso in ContextVar.
  - La copertura dichiarata è limitata ai tool `_load_tool`/`AuditedBaseTool`: i councils sono esclusi.
  - È il candidato principale al riuso, come specifica delle regole o come implementazione.
- `gravya-app/services/agents/src/utils/run_scope_contract.py` (letto: header). Contratto di scope immutabile per run.
- `_enforce_scope_contract` è referenziato in `kloud/graph.py`, `executors/generic_executor.py`, `automation/dispatcher.py`, `kloud/write_replay.py`, `tools/_audit.py` e in due tool CRM. Il riferimento è verificato con grep, ma non ho letto i punti di chiamata.
- `gravya-app/server/src/services/grant-evaluator.ts` (letto: header). Grant di capability con ciclo di vita e condizioni DSL compilate (`grant-condition/{parse,compile,evaluate}.ts`) che falliscono chiuse. È di fatto un piccolo "compilatore di policy" lato server, non OPA.
- `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` §1-3 (letto). Contiene:
  - modello permessi "una chiave per azione, una tabella per azienda" (in costruzione in gravya-app#998, pezzo 4 da riscrivere);
  - le barriere esistenti, che secondo il documento ci sono ma sono "irraggiungibili finché gli agenti non eseguono i tool".
- Ricognizioni `docs/stato/sviluppo.md` e `kloudify.md`: OPA/Rego non trovato in gravya-app.

**Divergenze dal master plan:**
1. Il master prevede OPA/Rego in un sidecar. Il codice ha un enforcer custom in Python in-process più un valutatore TS dei grant: **OPA è assente**.
2. Il master fa derivare le policy dal grafo (A1→A2). Nel codice le regole sono attributi di classe dei tool (`DOMAIN`, `MONEY_WRITE`, `REQUIRES_HITL`, `SCOPE_ARG_MAP`, con `REQUIRES_HITL` "fisso nel codice per scelta") e righe di tabella. Non c'è un grafo né un bundle versionato con hash.
3. Il master non prevede eccezioni di copertura. Il codice esclude i councils dal chokepoint.
4. Il modello permessi del progetto (classi Admin, Membro, Kloud, Supervisore, Agente; tabella per azienda) non coincide con i nodi A1 (Agent, Mandate, Domain, Delegation). La mappatura è da decidere in A1/A2.
5. Kloudify classifica come post-Beta i temi non legati a sicurezza o isolamento. Se l'enforcement OPA debba entrare in Beta va deciso dall'utente.

## Appendice B — Non verificato

- Il corpo completo di `_scope_enforcement.py` (letto solo in parte) e i punti di chiamata nei file che lo referenziano.
- Se l'enforcer sia raggiungibile in produzione o staging. Il docstring di `run_scope_contract.py` dice "NOT YET WIRED", `_scope_enforcement.py` dice "enforce mode" e kloudify dice "irraggiungibile". I commenti sono incoerenti tra loro.
- Contenuto di `capability_check.py`, `compliance/*`, `llm_guard.py`, `tier-policy.ts` (letti solo i nomi).
- Lo stato di gravya-app#998 e l'identità di Kloud sul server.
- Il formato e la distribuzione dei bundle A2 (A2 non è documentato).
- La soglia di latenza (5 ms), il numero di casi di test (30) e l'esistenza in gravya-app di un ambiente dove eseguire OPA.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-A3-01 | Motore di policy | (a) OPA/Rego come da master; (b) enforcer Python esistente esteso con bundle versionato; (c) (b) in ondata 1, poi OPA | Fedeltà al master contro riuso del codice già in enforce e carico operativo in Beta | (c), con contratto `DecisionRequest`/`Decision` indipendente dal motore |
| DA-A3-02 | Topologia | (a) sidecar per runtime agente; (b) libreria in-process; (c) servizio centrale | Latenza, isolamento, coerenza con B1 | (a) se si sceglie OPA, altrimenti (b) |
| DA-A3-03 | Granularità del bundle | (a) un bundle per tenant; (b) un bundle globale con dati per tenant | Isolamento contro numero di artefatti; da concordare con A2 | (a): rispecchia l'isolamento del master |
| DA-A3-04 | Stato dinamico (spesa, token) | (a) passato nell'input da B2; (b) letto dal runtime | Mantenere stateless la valutazione | (a) |
| DA-A3-05 | Destino di `_scope_enforcement.py` | (a) resta come seconda difesa; (b) diventa un adattatore verso A3; (c) viene rimosso | Evitare due fonti di verità | (b), con test di parità |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span di decisione allineati ai nomi E1 (`gravya.decision.*`, `gravya.policy.*`, `gravya.company_id`) in §7 e CA6; aggiunti B1, E3, E2 in "È richiesto da" perché quei documenti dichiarano di dipendere da A3; rimando a B2 per `budget_state`. Motivo: interfacce non combacianti tra documenti scritti in parallelo. |
