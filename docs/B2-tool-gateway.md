# B2 — Tool gateway

## 1. Identità

| Campo | Valore |
|---|---|
| ID | B2 |
| Nome | Tool gateway |
| Componente padre | B — Runtime Agenti |
| Versione documento | 1.2 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È l'unico punto da cui un agente in esecuzione (B1) può invocare un tool. Per ogni chiamata: identifica l'agente e il tenant, chiede la decisione `allow/deny` al runtime di enforcement (A3), applica un rate limit per agente, tool e tenant, esegue o inoltra la chiamata e registra un evento di audit. All'agente espone **solo** l'elenco dei tool autorizzati per lui (master plan, §6 B2).

**Cosa NON fa.**
- Non decide le autorizzazioni. La decisione è di A3, su policy compilate da A2 a partire da A1. Il gateway applica l'esito e non contiene regole di permesso nel codice.
- Non implementa i connettori (D1–D4) né il protocollo MCP (D5, ondata 3). Deve però restare compatibile con un'esposizione MCP futura.
- Non gestisce l'approvazione umana: la richiede a C3 quando A3 risponde «serve approvazione».
- Non è il registro permanente delle decisioni (A5): emette gli eventi, A5 li conserva.

**Perché esiste.** Il master impone l'isolamento architetturale: l'agente non deve poter raggiungere un tool se non attraverso un confine che non controlla. Se i tool vengono caricati nello stesso processo dell'agente, l'isolamento dipende dalla disciplina del codice.

## 3. Contesto e dipendenze

**Dipende da:** A3 (decisione allow/deny), A1 e A2 (indirettamente, tramite A3), B1 (identità del run e confine di rete), E1 (traccia DB-native per ogni chiamata a un tool, con il vocabolario `gravya.*` e il modello dati definiti da E1; niente OpenTelemetry, PV-02), A5 (destinazione degli eventi di audit; ondata successiva: fino ad allora vedi DA-B2-04).

**È richiesto da:** E3 (casi `act`/`refuse`), B1 (gli agenti chiamano i tool solo da qui), C1 (i nodi tool del workflow), C3 (riprende la chiamata dopo l'approvazione), D1–D4 (si registrano come tool dietro il gateway), D5 (MCP sopra il gateway), E5 ed E6 (telemetria e costi per tool).

**Assunzioni (non verificate, da confermare):**
- A3 espone una chiamata di decisione sincrona con esito `allow`, `deny` o `require_approval`. Il contratto esatto lo fissa il documento A3.
- B1 fornisce a ogni run un'identità verificabile (token firmato con `agent_id`, `tenant_id`, `run_id`).
- Il gateway si costruisce da zero in v2 (DX-01, PV-03). gravya-app è solo riferimento (Appendice A); la sua Beta non vincola questo documento.

## 4. Contratti

**Input (richiesta di invocazione):**

| Campo | Tipo | Note |
|---|---|---|
| `run_token` | stringa firmata | emesso da B1; da qui il gateway ricava `agent_id`, `tenant_id`, `run_id` (mai dal corpo) |
| `tool_id` | stringa | id stabile nel catalogo |
| `args` | oggetto | validato contro lo schema del tool |
| `idempotency_key` | stringa | obbligatoria per i tool di scrittura |
| `approval_token` | stringa, opzionale | monouso, emesso da C3 |
| `trace_context` | oggetto | identificativi di correlazione (`trace_id`, `run_id`) del modello DB-native di E1; nessuna propagazione OTel |

**Output:** `{status: ok|denied|approval_required|rate_limited|error, result?, reason?, decision_id}`. `result` è sempre marcato come dato e non come istruzione (soluzione già validata in gravya-app, ripresa come idea: vedi Appendice A).

**Catalogo tool (schema minimo):** `tool_id`, versione, schema degli argomenti, classe (`read`/`write`/`money_write`), flag `requires_hitl`, `domain`, flag `creates_new`, mappa argomenti→assi di scope (equivalente di `SCOPE_ARG_MAP`), destinazione d'esecuzione, limiti di default. `domain`, `creates_new` e la mappa degli assi sono stati aggiunti in revisione (v1.1) perché A3 li richiede nel `DecisionRequest` (`tool_class`, `resource`).

**Verso A3:** il gateway costruisce il `DecisionRequest` di A3 (§4 di A3) ricavando `tenant_id`, `agent_id`, `run_id` dal `run_token`, `tool_class` dal catalogo, `resource` da `args` tramite la mappa degli assi, e inoltra `approval_token`. Se DA-A3-04 sceglie (a), il gateway deve anche fornire `budget_state` (spesa del run e del giorno): la fonte di questo dato non è definita in nessun documento dell'ondata 1.

**Eventi emessi:** (il trasporto è la decisione trasversale DA-A1-03) `tool.invoked`, `tool.denied`, `tool.rate_limited`, `tool.approval_requested`, `tool.completed`, `tool.failed`. Campi comuni: tenant, agente, run, tool, `decision_id` e versione/hash della policy di A3, durata, esito, anteprima redatta degli argomenti.

**Eventi consumati:** invalidazione del catalogo o delle policy (da A2/A3).

## 5. Interfacce

- `GET /tools` — elenco dei tool autorizzati per il run, con gli schemi. È l'elenco filtrato da A3, non il catalogo intero.
- `POST /tools/{tool_id}/invoke` — invocazione con il contratto §4.
- Interfaccia amministrativa del catalogo, riservata al superadmin.
- Trasporto (HTTP interno, processo separato o libreria nel runtime): DA-B2-02.
- Origine dell'elenco autorizzato (grafo A1, tabella dedicata o policy A3): DA-B2-05.

## 6. Comportamento

**Flusso principale:** verifica di `run_token` → caricamento della voce di catalogo → validazione di `args` → decisione A3 → rate limit → esecuzione → audit `completed`/`failed` → risposta.

**Casi limite:**
- A3 non raggiungibile o in timeout: **deny** (fail-closed).
- Tool assente dal catalogo o non presente nell'elenco del run: `denied`, senza rivelare se il tool esiste.
- `require_approval`: risposta `approval_required` e richiesta a C3; alla ripresa serve un `approval_token` monouso, valido per una sola chiamata.
- `money_write` con budget illeggibile: deny (fail-closed, principio ripreso da gravya-app come lezione).
- Scrittura dell'audit fallita: comportamento da decidere (DA-B2-04). In gravya-app il codice va avanti e salta l'audit: difetto da non ripetere.
- Superamento del rate limit: `rate_limited` con `retry_after` e nessuna esecuzione.
- Retry con la stessa `idempotency_key`: restituisce il primo esito e non riesegue.

## 7. Requisiti non funzionali

- **Sicurezza:** l'agente non ha credenziali dei sistemi esterni; queste restano al gateway. L'egress di B1 è consentito solo verso il gateway e i peer interni.
- **Isolamento tenant:** il tenant viene solo dal token; ogni accesso ai dati dei tool è in contesto RLS del tenant.
- **Performance:** overhead del gateway (escluso il tool) p95 < 50 ms (proposta da validare).
- **Osservabilità:** una traccia E1 DB-native per ogni invocazione, collegata al run tramite `trace_id`/`run_id`, scritta nel database di Gravya. Nessun SDK, collector o esportatore OpenTelemetry (PV-02).
- **Redazione:** le anteprime di argomenti e risultati sono redatte prima della persistenza.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Minimizzazione: l'evento di audit conserva identificativi (tenant, agente, run, tool, `decision_id`) e un'anteprima **redatta** degli argomenti, non il payload completo né il risultato. Base giuridica: i dati personali che transitano nei tool (record CRM dei clienti dell'agenzia) sono trattati da Gravya come responsabile per conto del tenant (art. 28); l'audit serve a sicurezza e accountability (art. 5.2, 32). Retention di audit e anteprime: **non definita, DA RIPORTARE ALL'UTENTE** (DA-B2-06). Diritti: l'anteprima redatta e gli identificativi devono essere ricercabili per soggetto, in modo che A5 possa rispondere ad accesso/cancellazione; come conciliare cancellazione e audit append-only è un tema di A5, segnalato qui. Trasferimenti: il gateway non invia dati a tool la cui destinazione non è dichiarata nel catalogo (DA-B2-07).
  - *NIS2 (art. 21).* Controllo degli accessi e minimo privilegio (elenco tool filtrato, default-deny, fail-closed su A3), gestione dei segreti (le credenziali dei sistemi esterni restano al gateway, mai all'agente), sicurezza della catena di fornitura (destinazioni dei tool dichiarate in catalogo), registrazione degli eventi per rilevare incidenti. Gli eventi `tool.denied` ripetuti, i tentativi di bypass e i token falsificati sono segnali che alimentano la gestione incidenti; la notifica (art. 23) non è di competenza di B2, che fornisce le evidenze.
  - *AI Act.* B2 è il punto in cui un sistema AI agisce sul mondo: registra ogni azione dell'agente (log, art. 12 per i casi ad alto rischio, se applicabile: classificazione non verificata qui) e applica la sorveglianza umana (art. 14) tramite `require_approval` e token monouso di C3. La trasparenza verso le persone (art. 50) riguarda i contenuti generati e non è di B2, salvo i tool che pubblicano o inviano contenuti: per questi il catalogo deve indicare se l'output è generato da AI (requisito per D1–D4).
  - *Osservabilità AI.* Rende osservabili: quale tool ha chiamato quale agente in quale run, con quale decisione e versione della policy di A3, esito, durata, eventuale approvazione umana e costo (per E5/E6).

## 8. Criteri di accettazione

1. **Esposizione filtrata:** un test di integrazione con due agenti con permessi diversi verifica che `GET /tools` restituisca insiemi diversi, ciascuno uguale all'insieme atteso dalla policy.
2. **Nessun bypass:** un test da dentro B1 che tenta di importare o chiamare direttamente un tool o un host esterno fallisce; il 100% delle chiamate a tool nei test e2e ha un evento di audit con lo stesso `run_id`.
3. **Fail-closed:** con A3 spento, 0 chiamate eseguite su 100 tentativi.
4. **Rate limit:** con limite N/minuto, N+1 chiamate producono esattamente 1 `rate_limited` (N=10 nel test, proposta da validare).
5. **Approvazione monouso:** due chiamate con lo stesso `approval_token` → la seconda è `denied`.
6. **Isolamento:** un token del tenant A con un `record_id` del tenant B → `denied` o nessun risultato, mai dati di B.
7. **Audit completo:** per ogni esito di §4 esiste un test che verifica 1 evento con i campi obbligatori.
8. **Overhead:** benchmark su 1.000 chiamate a un tool fittizio, p95 < 50 ms (proposta da validare).

## 9. Piano di implementazione

**Fasi ordinate:**
1. Decidere DA-B2-02 (forma del confine). La base è già decisa: gateway nuovo (DX-01).
2. Catalogo dei tool e contratto di invocazione (§4), con un tool fittizio.
3. Integrazione con A3: decisione e filtro di `GET /tools`, fail-closed.
4. Rate limit (DA-B2-03) e idempotenza.
5. Audit ed eventi verso E1 e A5 (DA-B2-04).
6. Flusso `require_approval` con C3 e token monouso.
7. Primi tool reali di lettura, poi di scrittura, scritti sul contratto §4 (eventualmente ripensando tool di gravya-app come riferimento, non portandoli).

**Tecnologie:** proposta Python/FastAPI per il servizio, PostgreSQL con RLS, Redis (vedi DA-B2-03), in linea con le scelte di riferimento; lo stack di v2 non è fissato da gravya-app (PV-03) e va confermato a livello di piattaforma. Il master cita OPA/Rego per A3 (DA-A3-01) e MCP per D5. Niente OpenTelemetry (PV-02). Nessun servizio gestito che porti dati fuori dal perimetro controllato senza decisione dell'utente.

**Rischi principali:** vedi §11.

## 10. Test e valutazione

- **Unit:** validazione degli schemi degli argomenti, mappatura degli esiti A3, contatori del rate limit, consumo del token monouso, redazione.
- **Integration:** gateway + A3 + DB con due tenant; ripresa dopo l'approvazione C3; idempotenza.
- **Security:** tentativi di bypass da B1 (import diretto, egress diretto), token falsificato, tenant spoofing via `args`, prompt injection nel risultato di un tool.
- **Eval:** le regressioni dei golden set E3 che usano tool passano dal gateway.

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Logica di permesso che rientra nel codice dei tool (difetto di gravya-app) | Alto | Un solo punto di decisione: A3. I tool non contengono controlli di autorizzazione; revisione del codice e test di bypass |
| Audit best-effort perde eventi | Alto (conformità) | DA-B2-04; test 7 |
| Latenza del salto di rete | Medio | DA-B2-02; criterio 8 |
| Cache dell'elenco tool non allineata alla policy | Alto | Invalidazione su evento A2/A3; in caso di dubbio decide A3 a ogni invocazione |
| Dati personali verso destinazioni di tool non controllate | Alto (GDPR/NIS2) | Destinazione obbligatoria in catalogo; DA-B2-07 |

## 12. Stima e priorità

- **Taglia:** M per lo skeleton costruito da zero (servizio, catalogo, integrazione A3, rate limit, idempotenza, audit, flusso HITL, un tool di lettura e uno di scrittura). Non c'è più migrazione di tool esistenti (DX-01); la crescita verso L dipende dal numero di tool reali, che sono di D1–D4. Stima non validata.
- **Dipendenze critiche:** A3, B1.
- **Thin-slice MVP:** sì, ondata 1. Basta un tool di lettura e uno di scrittura con HITL.

---

## Appendice A — Riferimenti dal sistema precedente

Legenda: [L] = letto nel file indicato; [K] = da `docs/visione` di gravya-app-kloudify (fotografia del 16/10).

Per DX-01/PV-03 nulla di quanto segue si porta in v2: è materiale da cui riprendere idee e lezioni.

**Cosa c'è in gravya-app (soluzioni da riprendere come idea):**
- [L] `services/agents/src/tools/_scope_enforcement.py`: enforce mode con `ScopeViolation`, assi di scope (campaign/record/client ids, object_slugs), `REQUIRES_HITL` con token di approvazione monouso, `MONEY_WRITE` con tetto di spesa fail-closed, default-deny per i tool senza tassonomia, audit `tool.scope.denied`. Il file stesso dichiara che i councils **non** passano da questo punto.
- [L] `services/agents/src/tools/_audit.py`: `AuditedBaseTool` e `wrap_tool_with_audit` chiamano `_enforce_scope_contract` prima dell'audit (righe ~446-501); una riga per chiamata in `gravya_tool_invocations`, con redazione. È **best-effort**: se il pool DB non è disponibile, l'audit viene saltato e il tool viene eseguito lo stesso.
- [L] `services/agents/src/executors/generic_executor.py`: i tool sono caricati con importlib (whitelist `src.tools.`, `_load_tool`), legati agli esecutori via `gravya_executor_tools`. Esiste `_run_tool_loop` con `llm_invoke_with_tools`, al massimo 8 chiamate per risposta, risultati troncati a 16.000 caratteri e delimitati come dati, `_park_write` per le scritture.
- [L] `services/agents/src/api/_shared.py`: slowapi con `RATE_LIMIT_RPM` **per IP** sulle route FastAPI.
- Dalla ricognizione `sviluppo.md` (non riletto qui): API Broker `server/src/services/api-broker.ts` (cost ledger, circuit breaker, idempotenza; ho letto il commento «OQ-1 … emit-only — no cap enforcement»), egress-proxy con allowlist e HMAC, firewall `OUTPUT DROP` nei container agents.

**Difetti da non ripetere** (erano le divergenze dal master plan):
1. **Nessun gateway separato:** i tool girano nello stesso processo dell'agente (import diretto). Il confine è una convenzione di codice, non architetturale.
2. **Autorizzazione nel codice:** gli attributi di classe `REQUIRES_HITL`/`MONEY_WRITE` e i controlli in `_scope_enforcement.py` sono logica Python, non policy A3/OPA. La visione kloudify vuole invece «permessi come dati» (P6).
3. **Rate limit per agente/tool assente:** esiste solo il limite per IP sull'API e il tetto di giri/spesa. Lo status `rate_limited` compare solo nei tool web come errore del provider.
4. **Audit non garantito** (best-effort), mentre il master chiede audit e A5 append-only.
5. **MCP:** non presente nel codice; [K] `architettura-agenti.md` (~r. 310-314) rinvia la rivalutazione dell'MCP Meta Ads a dopo la Beta, «dietro i nostri blocchi». Coerente con D5 in ondata 3.
6. **Visione kloudify superata:** [K] `architettura-agenti.md` r. 81-82 dice che i tool «non vengono mai eseguiti» e che il gate è «irraggiungibile»; il codice attuale ha invece un ciclo di tool in `generic_executor.py`. Il documento di visione va considerato non aggiornato su questo punto.
7. In `docs/decisions` di gravya-app c'è un solo ADR (canvas gamma), non pertinente. In kloudify non c'è una cartella `docs/decisions`. Nessun task aperto nella Task Board riguarda B2.

## Appendice B — Non verificato

- Se `_run_tool_loop` sia effettivamente raggiunto dal percorso Kloud → supervisore → esecutore in produzione/staging.
- Il contenuto completo di `api-broker.ts`, dei file egress e di `firewall-entrypoint.sh` (fonte: ricognizione di terzi).
- Il valore di `RATE_LIMIT_RPM` in `config/settings.py`.
- Se i councils oggi invochino tool (il codice afferma di no tramite `assert_no_council_invoking_tools`).
- Il contratto di decisione di A3 e il formato del token di B1.
- Lo stato attuale delle issue citate (#998, #1801).
- Tutte le soglie numeriche marcate «proposta da validare».

## Appendice C — Decisioni aperte

- **DA-B2-01 — Base di partenza.** **Chiusa da DX-01:** gateway nuovo in v2; `_scope_enforcement.py`, `_audit.py` e il caricatore di gravya-app sono solo riferimento (tassonomia degli assi e casi di test come idea, Appendice A).
- **DA-B2-02 — Forma del confine.** Opzioni: (a) servizio HTTP separato (FastAPI) raggiungibile da B1 solo via rete; (b) libreria in-process con A3 come sidecar; (c) endpoint dentro il server Express. Criterio: isolamento architetturale (vincolo del master), latenza. Raccomandazione: (a); (b) non soddisfa l'isolamento.
- **DA-B2-03 — Archivio dei contatori di rate limit.** Opzioni: (a) Redis (già nello stack); (b) PostgreSQL. Criterio: atomicità e latenza. Raccomandazione: (a).
- **DA-B2-04 — Audit fail-open o fail-closed.** Opzioni: (a) fail-closed per tutti i tool; (b) fail-closed solo per scritture/`money_write`, best-effort per le letture (oggi è best-effort per tutto); (c) coda durevole con flush asincrono. Criterio: conformità (A5, AI Act) contro disponibilità. Raccomandazione (v1.2, rivista per PV-01): (a) o (c) — l'audit è requisito di conformità e prevale sulla disponibilità; (b) lascerebbe azioni dell'agente non registrate. **DA RIPORTARE ALL'UTENTE**: la scelta tra (a) e (c), e se per le letture sia accettabile un'eccezione.

- **DA-B2-05 — Origine dell'allowlist dei tool per agente** (aggiunta in revisione v1.1 perché DA-A1-04 rinvia la scelta a B2, che non la trattava). Opzioni: (a) edge `CAN_USE` nel grafo A1, compilato da A2; (b) tabella dedicata in v2 agente→tool (sul modello di `gravya_executor_tools` di gravya-app, solo come riferimento); (c) solo policy A3. Criterio: una sola fonte di verità. Raccomandazione: nessuna; da decidere insieme a DA-A1-02 (che con DX-01 non riguarda più la proiezione da gravya-app).
- **DA-B2-06 — Retention dell'audit dei tool e delle anteprime redatte** (nuova in v1.2, PV-01). Opzioni: (a) allineata alla retention di A5 per tutti gli eventi; (b) differenziata: identificativi ed esito più a lungo, anteprime redatte per un periodo breve; (c) configurabile per tenant entro limiti. Criterio: minimizzazione GDPR contro obblighi di log (AI Act, NIS2) e contratti con i tenant. Raccomandazione: (b), ma la durata lecita non è verificata. **DA RIPORTARE ALL'UTENTE.**
- **DA-B2-07 — Tool che inviano dati fuori dal perimetro controllato** (nuova in v1.2, PV-01). Molti tool (connettori pubblicitari, email, LLM esterni) trasferiscono per natura dati a terzi, anche extra-UE. Opzioni: (a) campo obbligatorio in catalogo con destinazione, giurisdizione e categorie di dati, e deny se mancante; (b) in più, consenso/abilitazione esplicita del tenant per ogni destinazione extra-UE; (c) gestione solo a livello contrattuale. Criterio: GDPR capo V, NIS2 catena di fornitura. Raccomandazione: (a)+(b). **DA RIPORTARE ALL'UTENTE** (scelta di prodotto e legale).

---

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: catalogo tool esteso con `domain`, `creates_new` e mappa degli assi, richiesti dal `DecisionRequest` di A3; descritto come il gateway costruisce il `DecisionRequest` e segnalata la fonte mancante di `budget_state` (DA-A3-04); aggiunta DA-B2-05 (allowlist), rinviata qui da DA-A1-04 ma assente; rimando a DA-A1-03 per il trasporto eventi; aggiunto E3 in "È richiesto da". Motivo: interfacce non combacianti. |
| 1.2 | 2026-11-03 | Adeguamento a DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). DA-B2-01 chiusa da DX-01; rimossi assunzione e rischio sulla Beta; tecnologie, fasi e taglia §12 riformulate per costruzione da zero (resta M, senza migrazione di tool); Appendice A rinominata «Riferimenti dal sistema precedente» (idee da riprendere, difetti da non ripetere); span E1 sostituiti da tracce DB-native; aggiunta in §7 la voce «Sicurezza e conformità» (GDPR, NIS2, AI Act, osservabilità AI); DA-B2-04 raccomandazione rivista verso fail-closed e riportata all'utente; DA-B2-05 riformulata senza tabella esistente; nuove DA-B2-06 (retention audit) e DA-B2-07 (destinazioni dei tool fuori perimetro). |
