# B2 — Tool gateway

## 1. Identità

| Campo | Valore |
|---|---|
| ID | B2 |
| Nome | Tool gateway |
| Componente padre | B — Runtime Agenti |
| Versione documento | 1.5 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È l'unico punto da cui un agente in esecuzione (B1) può invocare un tool. Per ogni chiamata: identifica agente e tenant dal `run_token`, controlla la destinazione dichiarata del tool, chiede la decisione `allow/deny/require_approval` ad A3, applica tre rate limit indipendenti, esegue o inoltra la chiamata e registra l'audit. All'agente espone **solo** l'elenco dei tool autorizzati per lui (master plan, §6 B2).

**Cosa NON fa.**
- Non decide le autorizzazioni: la decisione è di A3, su policy compilate da A2 a partire da A1. Il gateway applica l'esito e non contiene regole di permesso nel codice.
- Non implementa i connettori (D1–D4) né il protocollo MCP (D5, ondata 3); deve restare compatibile con un'esposizione MCP futura.
- Non gestisce l'approvazione umana: la richiede a C3 quando A3 risponde `require_approval`.
- Non è il registro permanente delle decisioni né notifica incidenti: emette eventi e segnali, A5 li conserva e decide (DX-10).
- Non verifica consensi di marketing né applica etichette art. 50: dichiara i flag di catalogo, il dettaglio è di D1–D4 e C1 (§7).

**Perché esiste.** Il master impone l'isolamento architetturale: l'agente non deve poter raggiungere un tool se non attraverso un confine che non controlla. Se i tool stanno nel processo dell'agente, l'isolamento dipende dalla disciplina del codice.

## 3. Contesto e dipendenze

**Dipende da:**
- **A3** (decisione sincrona; il record di decisione e l'audit `tool.invoked` stanno in un'unica transazione eseguita da B2, DECISIONS §6); **A1** e **A2** indirettamente tramite A3 (A2 compila in policy l'opt-in per destinazione).
- **B1**: emette il `run_token`, che è lo stesso oggetto del `tool_grant_ref` di B1 (un solo token, emesso da B1 e verificato da B2, DA-CV-13); egress-proxy con la stessa regola delle destinazioni.
- **C3**: rilascia l'`approval_token` monouso.
- **E1**: tracce DB-native, vocabolario `gravya.*` (niente OpenTelemetry, PV-02).
- **A5** (ondata 2): destinazione di audit e segnali di incidente (DX-10). Nell'ondata 1 audit e segnali vanno in una tabella di audit minima nel database di Gravya, che A5 assorbe (DECISIONS §6).
- **A6** (ondata 2, DX-14): ruoli superadmin e admin agenzia, registro versionato delle variabili (`config_version`, `platform.config.changed`), configurazione per tenant (opt-in), pagina credenziali, log degli accessi cross-tenant (DX-18).
- **F6** (ondata 2, DX-12): applica la retention DX-09 e assegna le classi senza durata.
- DX-13 (superadmin), DX-17 (variabile non valida), DX-22 (nessun valore fisso).

**È richiesto da:** B1 (gli agenti chiamano i tool solo da qui), C1 (nodi tool), C3 (riprende la chiamata dopo l'approvazione), A3 (B2 fornisce l'input della decisione), E3 (casi `act`/`refuse`), D1–D4 (si registrano come tool), D5 (MCP, ondata 3), E5 ed E6 (telemetria e costi per tool, ondata 3), A5 (segnali).

**Assunzioni (non verificate):** il contratto di decisione esatto è di A3; il formato del `run_token` è di B1; il gateway si costruisce da zero (DX-01, PV-03) e gravya-app è solo riferimento (Appendice A).

## 4. Contratti

**Input (richiesta di invocazione):**

| Campo | Tipo | Note |
|---|---|---|
| `run_token` | stringa firmata | emesso da B1, durata `b1.run_token.ttl_s`; da qui `agent_id`, `tenant_id`, `run_id` (mai dal corpo) |
| `tool_id` | stringa | id stabile nel catalogo |
| `args` | oggetto | validato contro lo schema del tool |
| `idempotency_key` | stringa | obbligatoria per i tool di scrittura |
| `approval_token` | stringa, opzionale | monouso, emesso da C3, durata `hitl.approval_token.ttl_s` |
| `trace_context` | oggetto | `trace_id`, `run_id` del modello DB-native di E1; formato ispirato a `traceparent` (DA-E1-05), senza SDK né export OTel |

**Output:** `{status: ok|denied|approval_required|rate_limited|error, result?, reason?, decision_id}`; `rate_limited` porta `retry_after`. `result` è sempre marcato come dato e non come istruzione (idea ripresa da gravya-app, Appendice A).

**Catalogo tool (schema minimo):** `tool_id`, versione, schema degli argomenti, classe (`read`/`write`/`money_write`), classe di approvazione (`ALWAYS_HITL`, `MONEY_WRITE`, vocabolario chiuso; la mappatura su classe e `requires_hitl` è di A3), `domain`, `creates_new`, mappa argomenti→assi di scope, destinazione d'esecuzione, **destinazione dei dati** (obbligatoria, DA-B2-07: `destination_id`, giurisdizione, categorie di dati trasferite, sub-responsabile autorizzato con riferimento al DPA e data), flag `outbound_to_third_parties` (il tool invia verso terzi: email, post, messaggi per conto delle agenzie), flag `ai_generated_output`, limite del tool (`b2.rate_limit.tool_calls_per_minute`). Un tool `outbound_to_third_parties` senza `ai_generated_output` dichiarato non si registra nel catalogo.

**Fatti sulla destinazione, impostati dal superadmin con fonte e audit (DA-CV-19):** strumento di trasferimento (`tenant.extra_eu_optin.<destination_id>.transfer_instrument`), suo stato (`..._status`), autorizzazione del sub-responsabile (`destination.<destination_id>.subprocessor_authorization`). L'**opt-in** (`tenant.extra_eu_optin.<destination_id>.enabled`) lo imposta solo l'admin agenzia, mai il superadmin. B2 non scrive nessuno di questi valori.

**Verso A3:** `DecisionRequest` con `tenant_id`, `agent_id`, `run_id` dal token, `tool_class` dal catalogo, `resource` da `args` tramite la mappa degli assi, `approval_token` se presente. Se DA-A3-04 sceglie (a), B2 deve fornire `budget_state`: la fonte non è definita in nessun documento dell'ondata 1.

**Eventi emessi** (trasporto: DA-A1-03): `tool.invoked`, `tool.denied`, `tool.rate_limited`, `tool.approval_requested`, `tool.completed`, `tool.failed`. Campi comuni: tenant, agente, run, tool, `decision_id`, versione/hash della policy di A3, durata, esito, anteprima redatta degli argomenti. **Segnali verso A5:** ogni evento rilevante per la sicurezza (§6), inviato **senza soglia locale**: le soglie vivono in A5 (DA-CV-07).

**Eventi consumati:** invalidazione di catalogo o policy (A2/A3); `platform.config.changed` (A6).

## 5. Interfacce

- `GET /tools` — elenco dei tool autorizzati per il run, con gli schemi. È l'elenco filtrato da A3, non il catalogo intero; esclude i tool che non superano il controllo della destinazione (§6).
- `POST /tools/{tool_id}/invoke` — invocazione con il contratto §4.
- **Interfaccia amministrativa del catalogo** (superadmin, DX-13; pagina «Piattaforma → Tool gateway», provvisoria finché A6 non la fissa). Ogni modifica è versionata e auditata; se l'audit non si salva, la modifica non si applica.
- **Destinazioni dei dati:** l'admin agenzia attiva l'opt-in in «Agenzia → Impostazioni → Destinazioni dei dati» (MFA, DX-20); il superadmin aggiorna strumento, stato e autorizzazione del sub-responsabile indicando la fonte.
- **Credenziali dei sistemi esterni:** pagina dedicata di A6 (credenziali di agenzia, inserite dall'admin agenzia; di piattaforma solo per i tool di piattaforma, inserite dal superadmin). Da UI solo inserimento o sostituzione, mai rilettura in chiaro; il superadmin non inserisce mai credenziali per conto di un'agenzia (DX-22(b), DA-CV-16). L'archivio è cifrato, self-hosted nell'UE.
- **Variabili di piattaforma lette da B2** (catalogo §7 e §2, modificabili dal superadmin senza rilascio, versionate e auditate): `b2.rate_limit.agent_calls_per_minute`, `b2.rate_limit.tool_calls_per_minute`, `b2.rate_limit.tenant_calls_per_minute`, `b2.recovery_queue.retry_interval_s`, `b2.idempotency.window_hours` (con il massimo `b2.idempotency.window_hours_max`), `b1.run_token.ttl_s`, `hitl.approval_token.ttl_s`, `a3.eval.timeout_ms`, `b2.overhead_p95_ms`, le classi `retention.*` di §7. Variabile non leggibile o non valida (DX-17, DA-CV-17): le azioni si bloccano (`error`, nessuna esecuzione) con segnale ad A5; le cancellazioni programmate usano l'ultimo valore valido versionato; senza alcun valore valido, per le righe «da definire» l'azione si blocca. Le durate di retention sono di sola lettura finché l'intervallo del DPA non è definito (DA-CV-01).
- Trasporto (HTTP interno, processo separato o libreria): DA-B2-02. Origine dell'elenco autorizzato: DA-B2-05.

## 6. Comportamento

**Flusso principale:** verifica di `run_token` → voce di catalogo → controllo della destinazione → validazione di `args` → decisione A3 → rate limit → transazione unica (record di decisione di A3 + audit `tool.invoked`, fail-closed) → esecuzione con le credenziali del gateway → audit `completed`/`failed` → risposta.

**Controllo della destinazione (DA-B2-07, DA-CV-19):**
1. Senza destinazione, giurisdizione e categorie dichiarate: `denied`.
2. Senza autorizzazione valida del sub-responsabile (riferimento al DPA e data): `denied`, **anche per una destinazione UE**, che non passa dall'opt-in (GDPR art. 28(2) e (4)).
3. Destinazione extra-UE: serve l'opt-in dell'agenzia per quella destinazione **e** uno strumento di trasferimento con stato valido; altrimenti `denied`. Il Data Privacy Framework vale solo per le organizzazioni dell'elenco DPF (decisione 2023/1795, art. 1) e la fonte indicata dal superadmin deve riferirsi a quell'elenco; per le altre serve uno strumento dell'art. 46 GDPR.
4. Se il superadmin segna non valido lo strumento (per esempio decisione di adeguatezza sospesa o revocata, art. 45(5) GDPR): l'opt-in della destinazione si disattiva, parte un segnale ad A5 e dalla chiamata successiva il tool è `denied`. La **riattivazione richiede un nuovo opt-in** dell'agenzia: tornare a valido lo stato non basta.
5. Dati non leggibili: `denied` (fail-closed). Chi valuta i punti 2-3, A3 su policy o B2 direttamente: DA-B2-08.

**Casi limite:**
- A3 non raggiungibile o oltre `a3.eval.timeout_ms`: **deny**.
- Tool assente dal catalogo o dall'elenco del run: `denied`, senza rivelare se esiste.
- `require_approval`: `approval_required` e richiesta a C3; alla ripresa serve un `approval_token` monouso, valido per una sola chiamata. Le classi `ALWAYS_HITL` e `MONEY_WRITE` richiedono sempre l'approvazione e non sono declassabili da UI (DA-CV-15). I contenuti verso terzi non sono classe `ALWAYS_HITL` nell'ondata 1: l'approvazione la decide l'admin agenzia, con audit (DA-CV-18), da riesaminare con D1–D4.
- `money_write` con budget illeggibile: deny.
- **Audit non salvato prima dell'esecuzione:** l'azione si blocca e la risposta è `error` (DA-B2-04). È «salvato» solo il commit in tabella o una coda locale **durevole su disco con fsync**; una coda in memoria non conta (DECISIONS §6). Con la coda, l'unità record di decisione + `tool.invoked` entra come entrata unica e si riscrive in un'unica transazione al ripristino (assunzione, App. B).
- **Audit di esito fallito dopo l'esecuzione:** l'azione non si annulla; l'evento va nella coda di recupero durevole, riprovata ogni `b2.recovery_queue.retry_interval_s` fino a riuscirci, con segnale di incidente ad A5. La risposta riporta l'esito reale.
- **Rate limit:** tre limiti indipendenti (agente, tool, tenant), vince il più restrittivo; superamento → `rate_limited` con `retry_after`, nessuna esecuzione. Archivio dei contatori: DA-B2-03.
- **Idempotenza:** retry con la stessa `idempotency_key` entro `b2.idempotency.window_hours` restituisce il primo esito senza rieseguire; la finestra non supera `b2.idempotency.window_hours_max`. Dopo la finestra: DA-B2-09.
- **Rotazione delle chiavi** (firma del `run_token`, HMAC del token monouso; DA-CV-23): durante il passaggio due chiavi sono valide in parallelo, ciascuna con data di attivazione e di disattivazione; B2 accetta un token firmato con una chiave valida in quel momento e rifiuta quello di una chiave disattivata. Le chiavi stanno nella pagina credenziali di piattaforma; frequenza: `security.credential_rotation_interval_days`.
- **Segnali ad A5 senza soglia locale:** ogni `tool.denied`, token falsificato o scaduto, tentativo di bypass, destinazione negata, strumento di trasferimento caduto, audit non salvato, variabile non leggibile. Sempre prodotti e conservati, anche con `incident.nis2_flow_active` falso (C2, DX-10).

## 7. Requisiti non funzionali

- **Esecuzione:** self-hosted su infrastruttura UE (DA-B1-06).
- **Sicurezza:** l'agente non ha credenziali dei sistemi esterni; restano al gateway, mai rilette in chiaro e fuori da log, audit e tracce. L'egress di B1 è consentito solo verso gateway e peer interni; l'egress-proxy applica la regola delle destinazioni dichiarate (DECISIONS §6). Il token monouso è un'invariante.
- **Isolamento tenant:** il tenant viene solo dal token; ogni accesso ai dati dei tool è in contesto RLS. Il superadmin vede di default solo dati aggregati senza identificativi (`access.aggregate_min_group_size_count`); una singola traccia o riga di audit di un tenant solo su richiesta dell'agenzia o per incidente, entro le istruzioni del titolare (art. 28), con log degli accessi (chi, quando, quale tenant, quale dato, motivo; proprietà di A6, DX-18, `retention.cross_tenant_access_log_months`).
- **Prestazioni:** overhead del gateway sotto `b2.overhead_p95_ms` (escluso il tool); i budget di A3 (`a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms`) servono per gli alert e non bloccano.
- **Osservabilità:** una traccia E1 DB-native per invocazione, collegata al run; nelle tracce gli argomenti compaiono solo come hash (DA-C3-06); nessun contenuto di prompt o risposte. Anteprime e risultati redatti prima della persistenza.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28, DX-11) per i dati delle agenzie; base giuridica del titolare, di Gravya per gli identificativi dei suoi utenti (DECISIONS §6). Minimizzazione: l'audit conserva identificativi e anteprima redatta, non payload né risultato. Gli identificativi pseudonimi nelle tracce sono dati personali (considerando 26); le linee guida EDPB 01/2025 sono solo in consultazione e non si citano come requisito. Diritti: identificativi e anteprime ricercabili per soggetto; l'assistenza alle agenzie è art. 28(3)(e), senza termine di legge (`dsar.assist_max_days` è un obbligo del DPA, A5/F6). Violazione di dati: art. 33(2), il responsabile avvisa il titolare senza ingiustificato ritardo e il termine verso le agenzie è un obbligo del DPA (DA-CV-08, A5). Trasferimenti (Cap. V): §6, opt-in per destinazione, strumento valido (art. 45 o 46) e sub-responsabile autorizzato (art. 28(2), (4)); la decisione DPF è impugnata (C-703/25 P) e copre solo le organizzazioni dell'elenco.
  - **Retention (DX-09, F6; variabili di sola lettura finché manca l'intervallo del DPA, DA-CV-01).** Classi prodotte da B2 e variabile: audit dei tool, `retention.audit_decisions_months`; anteprime redatte, `retention.sensitive_payload_days` (poi resta l'hash); tracce E1, `retention.traces_days`; log degli accessi cross-tenant, `retention.cross_tenant_access_log_months`; evidenze di incidente, `retention.incident_evidence_months` (sospensione non attivabile finché massimo, riesame e categorie sono da definire; per i dati delle agenzie serve l'istruzione nel DPA e un parere legale prima di F6, DA-CV-21); segnali di incidente, `retention.incident_signals_months` (tetto provvisorio dell'utente prima della produzione, DA-CV-20); esiti per `idempotency_key`, `b2.idempotency.window_hours`; catalogo e versioni: per tutta la durata del servizio; contatori di rate limit e token consumati: classe da assegnare in F6; accessi alle credenziali, `retention.credential_access_months`. Backup: scadono entro `retention.data_backup_days`; al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22). Fine contratto (Data Act art. 25(2)): periodo di recupero dei dati di almeno 30 giorni dopo il periodo di passaggio, poi cancellazione; `retention.tenant_offboarding_days` è un minimo; qualificare il SaaS come «servizio di trattamento dei dati» è da confermare con un legale.
  - *NIS2.* Gravya oggi non è soggetto NIS2; la progettazione è «NIS2 compliant ready by design» (DX-10). Log, protezione e backup dei log, accessi privilegiati: requisiti di progetto dal Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11 (non da «art. 21»). Il flusso di notifica è di A5, presente ma non attivo (`incident.nis2_flow_active`): preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, dalla conoscenza. B2 invia i segnali e le evidenze, sempre.
  - *AI Act.* Art. 50 applicabile dal 2.8.2026. B2 non genera contenuti ma porta il flag `ai_generated_output`: l'etichetta «generato da AI» sui contenuti verso terzi e l'informativa a chi interagisce con un'IA (50(1)) sono invarianti, la marcatura leggibile da macchina anche del testo (50(2)) è dettagliata in C1 e D1–D4. Artt. 12, 14, 19, 26: solo buona pratica (DX-11), e comunque per l'alto rischio dal 2.12.2027.
  - *Marketing (PV-01 esteso).* Per i tool `outbound_to_third_parties` valgono ePrivacy art. 13, Codice privacy artt. 122 e 130, d.lgs. 70/2003 artt. 8-9, linee guida del Garante sui pixel (registro, tutte ◐). Consenso, opt-out e variabili sono di D1–D4: B2 non ne introduce (catalogo §1, regola 10). Se Gravya debba bloccare un invio senza base registrata: DA-B2-10.
  - *Osservabilità AI.* Quale agente, quale tool, quale run, decisione e versione della policy, esito, durata, approvazione umana, costo (per E5/E6).

## 8. Criteri di accettazione

Le dimensioni dei campioni (numero di tentativi, di chiamate, valore di N) sono parametri del test (DA-CV-04 (b)); le soglie leggono le variabili del catalogo.

1. **Esposizione filtrata:** due agenti con permessi diversi ottengono da `GET /tools` insiemi diversi, uguali a quelli attesi dalla policy; sono assenti i tool negati per destinazione (criterio 9).
2. **Nessun bypass:** un test da dentro B1 che importa o chiama direttamente un tool o un host esterno fallisce; il 100% delle chiamate nei test e2e ha un evento di audit con lo stesso `run_id`.
3. **Fail-closed:** con A3 spento o oltre `a3.eval.timeout_ms`, 0 chiamate eseguite; con la scrittura dell'audit impossibile, 0 chiamate eseguite e ogni risposta è `error`.
4. **Rate limit indipendenti:** con limiti di prova diversi per agente, tool e tenant, per ciascuno N+1 chiamate producono esattamente 1 `rate_limited` e vince il più restrittivo; la modifica di una variabile si applica senza riavvio, con evento di audit (versione precedente e nuova); con variabile illeggibile 0 chiamate eseguite.
5. **Approvazione monouso:** due chiamate con lo stesso `approval_token` → la seconda `denied`; un token oltre `hitl.approval_token.ttl_s` → `denied`.
6. **Isolamento:** token del tenant A con un `record_id` del tenant B → `denied` o nessun risultato, mai dati di B.
7. **Audit completo:** per ogni esito di §4 esiste 1 evento con i campi obbligatori.
8. **Overhead:** benchmark su un campione di chiamate a un tool fittizio, p95 sotto `b2.overhead_p95_ms`.
9. **Destinazione e trasferimenti:** tabella di casi, ciascuno atteso: nessuna destinazione → `denied`; UE senza autorizzazione del sub-responsabile → `denied`; UE con autorizzazione → consentito senza opt-in; extra-UE senza opt-in → `denied`; extra-UE con opt-in, strumento valido e autorizzazione → consentito. Lo stato dello strumento portato a non valido produce, alla chiamata successiva, `denied`, `enabled` falso e 1 segnale ad A5; tornato valido, il tool resta `denied` finché l'agenzia non rifà l'opt-in. Un aggiornamento dello stato senza fonte è rifiutato.
10. **Transazione unica, coda durevole e recupero:** con iniezione di guasto tra record di decisione e `tool.invoked` esistono entrambi o nessuno; con tabella non disponibile e coda con fsync la chiamata è eseguita e le due scritture compaiono in tabella al ripristino; con coda senza fsync 0 chiamate eseguite; con l'audit di esito impossibile dopo l'esecuzione l'evento entra nella coda di recupero, si scrive al ripristino e partono i segnali.
11. **Retention e accessi cross-tenant:** un job con orologio simulato elimina le anteprime oltre `retention.sensitive_payload_days` lasciando l'hash e l'audit oltre `retention.audit_decisions_months`; con una variabile illeggibile il job usa l'ultimo valore valido e invia 1 segnale; l'accesso del superadmin a una traccia di un altro tenant produce 1 riga nel log e un admin di agenzia riceve un rifiuto.
12. **Credenziali:** nessuna risposta di API o UI e nessun log, audit o traccia contiene una credenziale di prova in chiaro (0 occorrenze); un tool con credenziale assente risponde `error`.
13. **Rotazione delle chiavi:** con chiamate continue durante il passaggio, token firmati con la chiave vecchia e con la nuova sono accettati finché entrambe sono valide e 0 chiamate fallite; dopo la disattivazione il token della chiave vecchia è `denied`.
14. **Segnali:** ogni caso del §6 produce 1 segnale per evento, senza soglia locale, anche con `incident.nis2_flow_active` falso.
15. **Idempotenza:** due chiamate con la stessa chiave entro la finestra producono 1 esecuzione e lo stesso esito; un valore di `b2.idempotency.window_hours` oltre il massimo è rifiutato.
16. **Flag di catalogo:** un tool `outbound_to_third_parties` senza `ai_generated_output` è rifiutato alla registrazione.

## 9. Piano di implementazione

1. Decidere DA-B2-02 (forma del confine). Base già decisa: gateway nuovo (DX-01).
2. Catalogo dei tool e contratto §4, con un tool fittizio.
3. Integrazione con A3: decisione, filtro di `GET /tools`, fail-closed, transazione unica.
4. Rate limit a tre livelli (DA-B2-03) e idempotenza con finestra.
5. Audit fail-closed, coda durevole, coda di recupero, eventi verso E1, segnali verso A5 (DX-10).
6. Campi di destinazione, controllo del §6 e disattivazione per strumento caduto (DA-B2-07).
7. Flusso `require_approval` con C3 e token monouso; rotazione delle chiavi con due chiavi parallele.
8. Primi tool di lettura, poi di scrittura, scritti sul contratto §4 (gravya-app come riferimento, non portando codice).

**Tecnologie:** proposta Python/FastAPI per il servizio, PostgreSQL con RLS, Redis (DA-B2-03), da confermare a livello di piattaforma (PV-03). Il master cita OPA/Rego per A3 (DA-A3-01) e MCP per D5. Niente SDK né export OpenTelemetry (PV-02). Self-hosted nell'UE (DA-B1-06); nessun servizio gestito che porti dati fuori dal perimetro senza decisione dell'utente.

**Rischi principali:** §11.

## 10. Test e valutazione

- **Unit:** schemi degli argomenti, mappatura degli esiti A3, contatori a tre livelli, token monouso e scadenza, redazione, matrice di destinazione.
- **Integration:** gateway + A3 + DB con due tenant; ripresa dopo C3; idempotenza; transazione unica con guasto iniettato.
- **Fail-closed:** audit non scrivibile; coda con fsync; audit di esito fallito dopo l'esecuzione; A3 non raggiungibile; variabile illeggibile.
- **Superadmin e retention:** modifica versionata e auditata delle variabili; stato dello strumento solo dal superadmin, con fonte; opt-in non attivabile dal superadmin; log degli accessi cross-tenant; cancellazione per classe.
- **Security:** bypass da B1, token falsificato, tenant spoofing via `args`, prompt injection nel risultato, tool senza destinazione, extra-UE senza opt-in, credenziali nei log, chiave disattivata.
- **Eval:** i golden set E3 che usano tool passano dal gateway.

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Logica di permesso nel codice dei tool (difetto di gravya-app) | Alto | Un solo punto di decisione: A3; test di bypass |
| Audit fail-closed riduce la disponibilità | Medio | Scelta accettata (DA-B2-04); coda con fsync; segnale ad A5; criteri 3 e 10 |
| Azione eseguita senza audit di esito | Alto | Coda di recupero e segnale; criterio 10 |
| Variabile errata (limite o retention) | Medio | Modifiche del superadmin, versionate e auditate; DX-17; criteri 4 e 11 |
| Abuso dell'accesso cross-tenant | Alto (GDPR art. 28) | Solo aggregati di default, singola traccia su richiesta o incidente, log; criterio 11 |
| Dati personali verso destinazioni non controllate o con strumento caduto | Alto (GDPR Cap. V) | Destinazione e sub-responsabile obbligatori, opt-in per destinazione, stato dal superadmin, nuovo opt-in dopo disattivazione; criterio 9 |
| Invio verso terzi senza base (marketing) | Alto (ePrivacy, Codice privacy) | Flag di catalogo, approvazione secondo DA-CV-18, DA-B2-10 con D1–D4 |
| Sostituzione chiavi con interruzione | Medio | Due chiavi parallele; criterio 13 |
| Latenza del salto di rete | Medio | DA-B2-02; criterio 8 |
| Cache dell'elenco tool non allineata | Alto | Invalidazione su evento; in dubbio decide A3 a ogni invocazione |

## 12. Stima e priorità

- **Taglia:** M per lo skeleton (servizio, catalogo con destinazioni, rate limit a tre livelli, idempotenza, audit fail-closed con transazione unica, HITL, chiavi parallele, un tool di lettura e uno di scrittura). Verso L con il numero di tool reali (D1–D4). Stima non validata.
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

- I punti dell'Appendice A sono ripresi dalla v1.0 e non ricontrollati nella v1.5: se `_run_tool_loop` sia raggiunto in produzione; `api-broker.ts`, egress e firewall; il valore di `RATE_LIMIT_RPM`; se i councils invochino tool; lo stato delle issue #998 e #1801.
- Contratto di decisione di A3, mappatura tra classi di approvazione (`ALWAYS_HITL`, `MONEY_WRITE`) e campi del catalogo, formato del `run_token` di B1: non letti nei rispettivi documenti per questa versione.
- Interazione tra coda locale con fsync e transazione unica con il record di A3: DECISIONS §6 decide entrambi, non il loro rapporto; l'entrata unica è un'assunzione da confermare con A3.
- Comportamento con archivio dei contatori non disponibile: fail-closed è una deduzione da DX-17, non una decisione.
- Granularità dell'audit degli accessi del gateway alle credenziali (per chiamata o per caricamento): di A6.
- Come B2 legge strumento, stato e autorizzazione (registro di A6): A6 non è documentato.
- Differenze con DECISIONS: DA-CV-18..23 e la regola sulla fine contratto sono riportate come decise secondo le conferme del 2026-11-04; DECISIONS e il catalogo 1.2 le registrano ancora come aperte o assenti (DA-CV-18, 20, 21, 22, 23 in catalogo §17.2).
- Registro delle norme: ePrivacy art. 13, Codice privacy artt. 122 e 130, d.lgs. 70/2003 artt. 8-9, linee guida del Garante sui pixel, Codice di buone pratiche art. 50 (dettaglio sulla marcatura del testo) sono ◐ o non letti; l'elenco DPF non è consultato; lo stato di C-703/25 P è ◐; la qualificazione del SaaS per il Data Act e per la NIS2 è aperta.
- Durate di contatori di rate limit e token consumati (F6); durate provvisorie di segnali e audit senza valore (DA-CV-20); intervalli `_min`/`_max` delle durate (DPA, F6).
- Valori delle variabili «da definire» del catalogo (limiti di rate limit, intervallo di recupero, finestra e massimo di idempotenza, TTL dei token) e soglie «proposta da validare».
- Struttura della tabella di audit minima e dei segnali dell'ondata 1.

## Appendice C — Decisioni (aperte e decise)

**Decise**
- **DA-B2-01 — Base di partenza.** Chiusa da DX-01: gateway nuovo.
- **DA-B2-04 — Audit fail-closed.** Decisa (2026-11-03): se l'audit non si salva l'azione si blocca; coda locale solo con fsync; audit di esito fallito: coda di recupero e segnale ad A5; tabella minima nell'ondata 1 (DECISIONS §6).
- **DA-B2-06 — Retention.** Assorbita da DX-09.
- **DA-B2-07 — Tool verso terzi o extra-UE.** Decisa (2026-11-03), precisata il 2026-11-04 (C9, D5, D7): destinazione, giurisdizione, categorie e sub-responsabile obbligatori, deny se mancano; opt-in per destinazione dichiarata nella configurazione per tenant di A6, dell'admin agenzia; strumento e stato dal superadmin con fonte e audit; strumento caduto → segnale ad A5 e disattivazione; riattivazione con nuovo opt-in. L'egress-proxy di B1 segue la stessa regola.
- **DX-14 — Identità, ruoli, variabili.** Decisa: A6.
- **DA-CV-13** (token unico), **DA-CV-15** (classificazione non declassabile), **DA-CV-16** (superadmin senza credenziali di agenzia), **DA-CV-17** (nessun valore valido), **DA-CV-07** (segnali senza soglia locale), **DA-CV-06** (rate limit indipendenti). Decise.
- **DA-CV-18, 19, 22, 23** — decise il 2026-11-04 (conferma dell'utente riportata dal coordinator, non ancora in DECISIONS): contenuti verso terzi non `ALWAYS_HITL` nell'ondata 1; strumento e sub-responsabile impostati dal superadmin; backup entro `retention.data_backup_days`; due chiavi parallele. **DA-CV-20 e 21:** decise come regole (tetto provvisorio fissato dall'utente prima della produzione; sospensione per evidenze solo per dati di Gravya, per le agenzie istruzione nel DPA e parere legale).

**Aperte**
- **DA-B2-02 — Forma del confine.** (a) servizio HTTP separato; (b) libreria in-process con A3 sidecar; (c) endpoint nel server Express. Criterio: isolamento, latenza. Raccomandazione: (a). Collegata a DX-06.
- **DA-B2-03 — Archivio dei contatori.** (a) Redis; (b) PostgreSQL. Criterio: atomicità, latenza. Raccomandazione: (a).
- **DA-B2-05 — Origine dell'allowlist.** (a) edge `CAN_USE` in A1; (b) tabella dedicata; (c) solo policy A3. Criterio: una sola fonte di verità. Nessuna raccomandazione; con DA-A1-02.
- **DA-B2-08 — Chi valuta strumento e sub-responsabile.** (a) A3 su policy compilata da A2, B2 applica (come per l'opt-in, DECISIONS §6); (b) B2 legge i fatti e decide la parte non di policy. Criterio: un solo punto di decisione (principio di §11). Raccomandazione: (a). **DA RIPORTARE ALL'UTENTE** (conformità).
- **DA-B2-09 — Chiave di idempotenza oltre la finestra.** (a) la chiamata è trattata come nuova; (b) `error`, chiave scaduta. Criterio: nessuna doppia esecuzione di scritture. Raccomandazione: (b) per le scritture. Non tocca dati personali oltre quanto già previsto.
- **DA-B2-10 — Blocco di invii verso terzi senza base registrata.** (a) il catalogo prevede, per i tool `outbound_to_third_parties`, una precondizione (base giuridica registrata, mittente identificato, meccanismo di opposizione) verificata dal connettore; (b) solo responsabilità dell'agenzia. Criterio: PV-01 esteso, registro N-PRIV-IT (interpretazione). Raccomandazione: (a), dettagliata in D1–D4. **DA RIPORTARE ALL'UTENTE** (perimetro, conformità).
- **DA-B2-11 — Chi assegna `ALWAYS_HITL` e `MONEY_WRITE` a un tool.** (a) il superadmin in catalogo, versionato e auditato; (b) derivata dalla tassonomia di A1/policy A3. Criterio: classificazione non declassabile da UI (DA-CV-15). Raccomandazione: (a). **DA RIPORTARE ALL'UTENTE** (perimetro HITL; catalogo §17.1, punto 21).

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
