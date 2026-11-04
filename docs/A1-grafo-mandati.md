# A1 — Modello del grafo dei mandati

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A1 |
| Nome | Modello del grafo dei mandati |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.5 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Definisce lo schema canonico di *chi* è un agente (`Agent`), *quali mandati* ha (`Mandate`), *su quali domini* opera (`Domain`), *quali artefatti* produce o consuma (`Artifact`) e *quali deleghe* esistono (`Delegation`), con edge tipizzati. È la mappa da cui A2 compila le policy.

**Cosa NON fa.**
- Non contiene payload (brief, creatività, PDF, transcript): `Artifact` è un nodo-àncora con URI e hash verso l'object storage.
- Non è interrogato sul percorso caldo: A3 usa le policy compilate da A2.
- Non sostituisce PostgreSQL per i dati applicativi. Non estende né importa le tabelle di permessi di gravya-app: v2 si costruisce da zero (PV-03); quelle tabelle sono solo riferimento (Appendice A).
- Non gestisce identità, ruoli, registro delle variabili, log degli accessi cross-tenant e opt-in extra-UE: sono di A6 (§3).

**Perché esiste.** Nel sistema precedente i mandati erano distribuiti in più tabelle e in costanti nel codice (Appendice A). Un modello unico, ispezionabile e versionato rende la governance verificabile (master plan §1 punto 3).

## 3. Contesto e dipendenze

**Dipende da:**
- **A6** (DX-14, decisa; ondata 2): identità dell'attore (DX-21), ruoli superadmin e admin agenzia (DX-13), registro versionato delle variabili con `config_version` (DX-21), log degli accessi cross-tenant (DX-18: lo schema è di A6, A1 lo usa e non lo possiede), configurazione per tenant che contiene l'opt-in extra-UE (DECISIONS §6; non è nel grafo).
- **A5** (ondata 2): destinatario dei segnali (§6) e dell'audit; finché non esiste, tabella di audit minima di v2 scritta nella stessa transazione (DECISIONS §6).
- **F6** (DX-12, ondata 2): applica le durate di retention e assegna la classe a nodi ed edge (DX-21).
- **E1**: modello DB-native per eventuale correlazione (`trace_id`); vocabolario `gravya.*`, nomi GenAI semconv e formato traceparent senza SDK né export OTel (PV-02, DA-E1-05).
- **E2** (opzionale): `Agent.prompt_ref` (chiave+versione, E2 §4.1).

**È richiesto da:** A2 (compilatore policy), A3 (via A2), A4 (validatore round-trip), A5 (audit), B2 (allowlist tool, se deriva dal grafo: DA-A1-04), F6 (retention sulle classi di §7), A6 (registro delle variabili `a1.*`).

**Assunzioni (da validare):**
1. Object storage compatibile S3, self-hosted nell'UE (DA-B1-06); il backend è **non verificato** e non deciso.
2. Bus eventi da scegliere (DA-A1-03 = DX-03). Redis resta riferimento.
3. Fino ad A5, tabella di audit append-only minima di v2, che A5 assorbe (DECISIONS §6).
4. Fino ad A6, le variabili e il log cross-tenant non esistono come servizio: DA-A1-10 e §5.
5. Campo tenant: `tenant_id` (DX-07 aperta).

## 4. Contratti

### 4.1 Nodi

| Nodo | Proprietà minime | Opzionali |
|---|---|---|
| `Tenant` | `id`, `isolation_level` (`shared`/`dedicated`) | `region` |
| `Agent` | `id`, `kind` (`kloud`/`supervisor`/`executor`), `version`, `status` (`draft`/`active`/`retired`), `tenant_id` o `null` = piattaforma | `model_ref`, `prompt_ref` (E2) |
| `Mandate` | `id`, `permission_key`, `effect` (`allow`/`deny`/`hitl`), `constraints` (JSON), `valid_from`, `valid_until`, `tenant_id` | `max_uses`, `created_by`, `approved_by` |
| `Domain` | `id`, `name`, `tenant_id` | `parent_domain_id` |
| `Artifact` | `id`, `uri`, `content_hash`, `mime`, `size_bytes`, `tenant_id` | `storage_tier`, `unresolved` |
| `Delegation` | `id`, `scope`, `valid_until`, `depth` | `constraints` |

Ogni nodo porta `schema_version`. Il vocabolario di `permission_key` ed `effect` lo definisce v2 (DA-A1-02); `permission_defaults` di gravya-app è un riferimento. Per le chiavi `ALWAYS_HITL` e `MONEY_WRITE` non esiste `effect=allow` automatico e la classificazione non è declassabile da UI (invarianti, catalogo §18; DA-CV-15). Per i contenuti verso terzi non c'è una classe `ALWAYS_HITL` nell'ondata 1: l'approvazione la decide l'admin agenzia con audit (DA-CV-18), da riesaminare con D1-D4. Chi assegna la classe di una chiave: Appendice B.

### 4.2 Edge

| Edge | Da → A | Semantica |
|---|---|---|
| `HAS_MANDATE` | `Agent` → `Mandate` | L'agente detiene il mandato |
| `OPERATES_IN` | `Mandate` → `Domain` | Ambito di validità |
| `DELEGATES_TO` | `Agent` → `Delegation` | L'agente cede parte del proprio scope |
| `DELEGATION_TARGET` | `Delegation` → `Agent` | Destinatario della delega |
| `PRODUCES` / `CONSUMES` | `Agent` → `Artifact` | Output / input |
| `BELONGS_TO` | `Agent`, `Mandate`, `Domain`, `Artifact` → `Tenant` | Appartenenza |

Proprietà comuni: `created_at`, `valid_from`, `valid_until`, `metadata`. Invarianti: una `Delegation` non concede più scope del mandato del delegante; la profondità della catena non supera `a1.delegation.max_depth`.

### 4.3 Eventi emessi
`graph.mandate.created|updated|expired|revoked`, `graph.agent.retired`, `graph.delegation.created|revoked`; payload: `tenant_id`, `node_id`, `schema_version`, `before`, `after`, `actor`. Sono eventi di runtime (classe `retention.runtime_events_days`), non segmenti di traccia: le mutazioni del grafo non diventano segmenti E1 (DECISIONS §4, «Mutazioni del grafo A1»). Nessun SDK OTel né export esterno (PV-02). `actor` è un identificativo pseudonimo, non nome o email.

### 4.4 Audit delle mutazioni
Ogni mutazione scrive una riga append-only con `tenant_id`, `node_id`, `operation`, `before`, `after`, `actor` (pseudonimo, fornito da A6), `actor_role` (`agency_admin`/`superadmin`), `config_version` (versione delle variabili usata per validare), `trace_id` (opzionale, se la mutazione avviene dentro un run: DECISIONS §4), `created_at` (orologio del database, unica origine), `schema_version`. La riga è scritta **nella stessa transazione** della mutazione: se l'insert fallisce, rollback e nessuna mutazione (fail-closed; DECISIONS §6; DA-B2-04, DA-A3-07). Il ruolo applicativo non ha permessi di `UPDATE` né `DELETE` sulla tabella; la cancellazione per scadenza è del ruolo di F6.

### 4.5 Variabili di piattaforma (DX-13, DX-22)
Nessun valore è nel codice né in questo documento: nome, default, intervallo, chi modifica e pagina stanno nel catalogo (`catalogo-variabili.md`). A1 legge:

| Variabile | Uso | Catalogo |
|---|---|---|
| `a1.delegation.max_depth` | profondità delle catene di delega; si applica alle nuove deleghe | §5 |
| `a1.artifact.max_properties_bytes` | dimensione massima delle proprietà di `Artifact` | §5 |
| `a1.sweeper.interval_minutes` | cadenza dello sweeper di scadenza | §5 |
| `a1.read_batch_p99_ms`, `a1.write_p99_ms` | soglie di prestazione (alert e criteri) | §12 |
| `retention.runtime_events_days`, `retention.audit_decisions_months`, `retention.cross_tenant_access_log_months` | classi di §7; di sola lettura finché l'intervallo del DPA non è definito (RR) | §2 |
| `retention.tenant_offboarding_days`, `retention.tenant_offboarding_choice` | fine contratto | §2 |
| `access.aggregate_min_group_size_count` | dimensione minima dei gruppi nelle viste aggregate del superadmin | §19 |

Una variabile non leggibile o non valida blocca le scritture che ne dipendono (`503`, fail-closed, DX-17) con segnale ad A5; le scadenze programmate usano l'ultimo valore valido versionato (DX-17). Senza alcun valore valido: regola 4 del catalogo (DA-CV-17). La produzione dell'evento `platform.config.changed` è di A6 (DX-21).

## 5. Interfacce

- **Scrittura** (solo umani): `POST /v1/graph/agents`, `POST /v1/graph/mandates`, `POST /v1/graph/delegations`, `DELETE /v1/graph/nodes/{id}` (soft-delete: `retired`/`revoked`). Scrive l'admin agenzia sul proprio tenant, con MFA (DX-20). Le scritture del superadmin sui nodi di un tenant non sono implementate finché DA-A1-09 non è decisa. Validazione con schemi condivisi (formato: DX-04).
- **Lettura batch per A2:** `GET /v1/graph/mandates?tenant_id=…&status=active` (JSON compilabile, con `snapshot_hash`), `GET /v1/graph/agents/{id}/topology`. A1 calcola `snapshot_hash` alla lettura e non conserva gli snapshot; algoritmo e lunghezza dell'hash sono invarianti (catalogo §18).
- **Viste aggregate del superadmin:** `GET /v1/graph/aggregates` restituisce conteggi di nodi per tipo e stato, senza identificativi, solo per gruppi di almeno `access.aggregate_min_group_size_count` tenant (DX-19, D4).
- **Accesso cross-tenant.** Di default il superadmin vede solo dati aggregati senza identificativi; la lettura di un singolo tenant è ammessa solo su richiesta dell'agenzia o per un incidente, entro le istruzioni del titolare (art. 28(3)(a) GDPR; DX-13, DX-19). Ogni accesso, anche in lettura, scrive nel log di A6 (DX-18: chi, tenant, risorsa, motivo, quando); se il log non si salva, l'accesso è negato. Finché il log di A6 non esiste, ogni accesso cross-tenant è negato. Nessun bypass di RLS per gli admin delle agenzie.
- Gli agenti non accedono al grafo e non creano mandati (HSAR/P16 ripreso da gravya-app).

## 6. Comportamento

**Creazione mandato:** validazione (tenant esistente; dominio dello stesso tenant; nessun mandato attivo identico → idempotenza) → transazione unica nodo + edge + riga di audit in PostgreSQL (DA-A1-01, §4.4) → commit → evento → A2 ricompila.

**Casi limite:**
- *Scadenza:* la lettura batch esclude i mandati con `valid_until` passato anche prima dello sweeper; lo sweeper li marca `expired` ed emette l'evento (riferimento: `kloud-hitl-expiry-sweeper.ts`, non letto).
- *Agente ritirato:* mandati e deleghe collegati revocati nella stessa transazione.
- *Delega oltre scope o profondità:* `422`. *Fallimento parziale:* rollback, `409` strutturato.
- *Audit non salvato:* rollback, `503`, nessun evento, segnale ad A5.
- *Variabile non leggibile o non valida:* `503` sulle scritture dipendenti, segnale ad A5.
- *Errore di lettura per A2:* A2 mantiene l'ultimo bundle valido (fail-closed per i nuovi mandati, P8).
- *Segnali ad A5 (DX-10, DA-CV-07):* A1 invia ogni evento rilevante senza soglia locale; le soglie vivono in A5. Eventi: audit o log di accesso non salvato, scrittura rifiutata per ruolo o tenant, accesso cross-tenant negato o fuori istruzioni, variabile non leggibile, errore di RLS. I segnali si producono e si conservano sempre, anche con `incident.nis2_flow_active` falso (DX-10, C2); in ondata 1 nella tabella di audit minima.

## 7. Requisiti non funzionali

- **Prestazioni:** lettura batch entro `a1.read_batch_p99_ms` con 1.000 mandati per tenant (condizione di test); scrittura entro `a1.write_p99_ms`.
- **Scalabilità:** dataset di test di 10.000 `Agent` e 100.000 `Artifact` per tenant, senza superare le soglie (parametro di test, DA-CV-04 (b)).
- **Isolamento:** applicato dal database, non solo da `WHERE`: PostgreSQL con RLS FORCE (DA-A1-01).
- **Osservabilità:** ogni mutazione ha una riga di audit (chi, cosa, quando, prima/dopo); eventi `graph.*` DB-native.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per i dati delle agenzie (DX-11). Il grafo contiene configurazione di governance, non dati di clienti finali; `Artifact` è solo àncora. Dati personali: identificativi pseudonimi degli admin in `created_by`, `approved_by`, `actor`: restano dati personali (considerando 26); le linee guida EDPB 01/2025 sono solo in consultazione e non si citano come requisito. Base giuridica (DA-A1-08, DECISIONS §6): per i dati delle agenzie è del titolare; per gli utenti di Gravya (superadmin, operatori) è di Gravya, titolare. Per i propri utenti Gravya risponde dell'art. 33(1); per i dati delle agenzie vale l'art. 33(2), senza ore, con termine contrattuale nel DPA (DA-CV-08; `incident.gdpr.*` sempre attive). A1 non invia dati a terzi né fuori dall'UE; l'opt-in extra-UE è in A6. Dati e backup self-hosted nell'UE (DA-B1-06). Cancellazione di un admin: la storia dei mandati non si cancella; l'attore resta pseudonimo, la mappa di re-identificazione non è di A1 (`retention.pseudonym_map_months`, da definire in F6).
  - *Retention (DX-09, DX-12, DX-15, DX-16).* Politica unica; applicazione di F6; durate di sola lettura finché l'intervallo del DPA non è definito. Classi prodotte da A1: (1) nodi ed edge, comprese le versioni scadute e revocate: classe senza durata variabile, assegnata da F6 (DX-21); (2) eventi `graph.*`: `retention.runtime_events_days`; (3) audit delle mutazioni: `retention.audit_decisions_months`; (4) log cross-tenant (di A6): `retention.cross_tenant_access_log_months`; (5) segnali ad A5: `retention.incident_signals_months`, durata provvisoria fissata dall'utente prima della produzione (DA-CV-20); (6) backup: `retention.data_backup_days` (DA-CV-22: al ripristino le cancellazioni già eseguite si riapplicano). La sospensione per evidenze di incidente non è attivabile finché non sono definiti massimo, riesame e categorie (catalogo, regola 12); per i dati delle agenzie servono un'istruzione nel DPA e un parere legale prima di F6 (DA-CV-21). Fine contratto: periodo di recupero di almeno `retention.tenant_offboarding_days` dalla fine del periodo di passaggio, poi cancellazione (Data Act art. 25(2)); la scelta restituzione o cancellazione è `retention.tenant_offboarding_choice`, sempre disponibile all'agenzia (art. 28(3)(g) GDPR). Che il SaaS sia un «servizio di trattamento dei dati» va confermato con un legale.
  - *NIS2.* Gravya oggi non è soggetto NIS2; la progettazione è «NIS2 compliant ready by design» (DX-10). Per log e accessi privilegiati il riferimento è il Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11 (non l'art. 21 della direttiva, che non nomina i log): audit append-only protetto da modifiche, attività degli account amministrativi e accessi privilegiati registrati, orologio del database come origine unica, MFA per gli account privilegiati (DX-20). Il regolamento non fissa una durata di conservazione; dove usa «se opportuno» una deroga si documenta (art. 2(2)). Notifica degli incidenti: flusso di A5, presente ma non attivo finché `incident.nis2_flow_active` è falso (preallarme, notifica e relazione finale con i termini `incident.nis2.*`, destinatario CSIRT Italia, decorrenza dalla conoscenza); A1 invia i segnali di §6 senza soglia locale. Parametri `security.*` dell'allegato: catalogo §19, non attivabili senza intervallo deciso.
  - *AI Act.* A1 non contiene LLM, non genera contenuti né interagisce con persone: l'art. 50 (applicabile dal 2.8.2026) non si applica direttamente; etichetta «generato da AI» e marcatura sono di C1 e D1-D4. Gli artt. 12, 14, 19, 26 sono solo buona pratica (DX-11) e comunque dal 2.12.2027 per l'alto rischio (Reg. 2026/1744): i mandati sono definiti solo da umani, le chiavi `ALWAYS_HITL`/`MONEY_WRITE` impongono l'HITL.
  - *Marketing.* A1 non invia comunicazioni né traccia utenti: ePrivacy e artt. 122 e 130 del Codice privacy non sono toccati (dettaglio in D1-D4).
  - *Osservabilità AI.* `snapshot_hash` riconduce ogni decisione di policy alla versione dei mandati in vigore; la storia è ricostruibile da `valid_from`/`valid_until` e dall'audit.
  - *Credenziali.* Il modello non richiede credenziali; nessuna è in questo documento (DX-22 (b)).

## 8. Criteri di accettazione

1. **Integrità:** query di validazione sugli edge con estremi mancanti = 0 (CI).
2. **Isolamento:** due tenant: 0 nodi del tenant B nelle risposte del tenant A, anche con query diretta usando il ruolo runtime.
3. **Idempotenza:** due POST identici → 1 `Mandate` e 1 `HAS_MANDATE`.
4. **Scadenza:** un mandato con `valid_until` passato è assente dalla lettura batch senza attendere lo sweeper; dopo un giro dello sweeper (`a1.sweeper.interval_minutes`) ha stato `expired` ed è stato emesso l'evento.
5. **Delega:** scope maggiore del delegante → `422`; catena oltre `a1.delegation.max_depth` → `422`.
6. **Vocabolario chiuso:** `allow` automatico su `MONEY_WRITE`/`ALWAYS_HITL` → rifiutato; tentativo di declassamento da UI → rifiutato.
7. **Àncore:** 0 proprietà di `Artifact` oltre `a1.artifact.max_properties_bytes`; nessun payload.
8. **Audit:** N mutazioni → N righe con tutti i campi di §4.4; `UPDATE`/`DELETE` sulla tabella con il ruolo runtime → errore.
9. **Prestazioni:** p99 entro `a1.read_batch_p99_ms` e `a1.write_p99_ms` su dataset sintetico (§7).
10. **Audit fail-closed:** con l'insert forzato a fallire: `503`, 0 righe parziali, nessun evento `graph.*`, un segnale ad A5.
11. **Variabili:** con `a1.delegation.max_depth` impostata a un valore di prova N dal superadmin, una catena di profondità N+1 → `422` senza rilascio; la modifica produce una nuova `config_version` (di A6) e la riga di audit riporta quella versione; con la variabile illeggibile la creazione di una delega → `503` e un segnale; con lo sweeper e variabile illeggibile si usa l'ultimo valore valido.
12. **Accesso cross-tenant:** admin del tenant A che legge B → 0 risultati; superadmin: nessun identificativo nelle viste aggregate e nessun risultato per gruppi sotto `access.aggregate_min_group_size_count`; lettura di un singolo tenant → 1 riga nel log di A6 per richiesta; con il log forzato a fallire → accesso negato e segnale.
13. **Retention:** nel codice di A1 nessuna costante di durata (lint o grep in CI); i valori letti dal registro per le tre classi di §4.5 coincidono con il catalogo; un tentativo del superadmin di modificarli fuori dall'intervallo (non ancora definito: sola lettura) → rifiutato.
14. **Segnali:** per ogni evento elencato in §6, esattamente un segnale ad A5, senza soglia locale.

## 9. Piano di implementazione

1. **Decisioni preliminari:** DA-A1-02, DA-A1-03 (DX-03), DX-04, DX-07, DA-A1-09, DA-A1-10. Già decise: DA-A1-01, DA-A1-08, audit fail-closed, DX-13, DX-14, DX-18, DX-19, DX-21.
2. **Analisi del riferimento** (Appendice A): requisiti e casi d'uso; nessuna migrazione né codice.
3. **Schema:** vincoli di unicità su `id`, indici su `tenant_id`, `status`, `valid_until`, `schema_version`, RLS FORCE, tabella di audit append-only.
4. **API** di scrittura e lettura con validazione (DX-04).
5. **Eventi** (DA-A1-03) e **sweeper**.
6. **Interfacce verso A6** (variabili, identità, log cross-tenant) e **segnali ad A5**, con ripieghi dichiarati finché non esistono.
7. **Test** di integrità, isolamento, audit fail-closed, accesso cross-tenant, segnali, prestazioni.

**Tecnologie:** PostgreSQL con tabelle nodi/edge e RLS FORCE (DA-A1-01), self-hosted nell'UE (DA-B1-06); Neptune escluso; Neo4j solo se servissero traversal pesanti. Riferimenti da gravya-app (non scelte): Express 5, zod, Redis 7, client S3. Nessun SDK OpenTelemetry (PV-02).

## 10. Test e valutazione

- **Unit:** schemi, invarianti di delega, vocabolario chiuso, errori 404/409/422/503.
- **Integration:** due tenant; sweeper; ritiro agente con revoca a cascata; immutabilità dell'audit.
- **Security:** token manipolato → 403/404; scrittura con attore agente → rifiutata; audit senza nome o email in chiaro; variabile modificata da un admin agenzia → 403; accesso cross-tenant sempre loggato o negato.
- **Fault injection:** audit che fallisce → rollback; registro variabili o log di A6 non disponibili → `503` o accesso negato.
- **Performance:** 1.000 letture batch, p99 misurato.
- **Eval:** non applicabile (nessun LLM).

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Modello permessi frammentato (difetto di gravya-app) | Alto | DA-A1-02: una sola fonte |
| Traversal pesanti su PostgreSQL | Medio | Schema logico indipendente dal backend; Neo4j come alternativa (DA-A1-01); test di isolamento in CI |
| Grafo usato come magazzino | Medio | Criterio 7; review dello schema |
| Deriva schema/documento | Medio | `schema_version`, migrazioni versionate, A4 |
| Audit con dati personali oltre il necessario | Medio | Retention DX-09 con F6; attore pseudonimo; mappa di re-identificazione fuori da A1 |
| Mutazione senza audit | Alto | Stessa transazione, rollback (criterio 10) |
| Abuso dell'accesso cross-tenant | Alto | Solo aggregati di default, log di A6 fail-closed, accesso negato senza log (criterio 12) |
| Variabile modificata male | Medio | Versionata e auditata da A6; validazione; fail-closed |
| A6, A5 e F6 non ancora documentati | Medio | Interfacce con ripieghi dichiarati (DA-A1-10); accesso cross-tenant negato finché manca il log |

## 12. Stima e priorità

- **Dimensione:** M (costruzione da zero su PostgreSQL con RLS; DA-A1-01) — proposta da validare.
- **Dipendenze critiche:** DA-A1-02, DX-03, DX-04, DX-07, DA-A1-10; per il pieno funzionamento A6, A5 e F6 (ondata 2).
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è solo riferimento (PV-03). Quanto segue viene dal dossier del code-reader della v1.4 e **non è stato ricontrollato nella v1.5**.

**Soluzioni da riprendere come idea:**
- `principal_permission_grants.ts`: grant per `company_id`, `principal_type`, `permission_key`, `scope`, `valid_from/until`, `max_uses`, revoca soft, condizioni compilate: il concetto più vicino a `Mandate`.
- `grant-evaluator.ts`: ciclo di vita del grant; condizioni che falliscono chiuse. Commenti contraddittori sull'audit.
- `permission_defaults.ts`, `permission_exceptions.ts` (#998): default per classe di principal e righe di piattaforma; eccezioni fuori dai grant.
- `agent_registry` (migrazione 0054) e `0055_gravya_dynamic_agents.sql`: topologia agente→agente→tool già relazionale, senza `company_id`.
- `gravya_agent_policies.ts`: criteri di qualità per agente, versionati, immutabili, senza tenant.
- `dispatcher.py`: `MAX_CASCADE_DEPTH` riguarda le cascate di automazioni, non le deleghe.

**Da kloudify (`controlli-e-conformita.md`, via ricognizione):** classi Admin/Membro/Kloud/Supervisore/Agente; modello #998 in costruzione; enforcement «irraggiungibile finché gli agenti non eseguono i tool».

**Difetti da non ripetere:** permessi in tre tabelle; topologia senza tenant; commenti contraddittori; delega solo implicita nella pipeline.

**Divergenze dal master plan:** nessun graph database nel codice; nessun nodo `Delegation` né `Domain`; nessun `Artifact` àncora (esiste `gravya_files` con `storage_tier`); tre tabelle di permesso coesistono per scelta; topologia senza `company_id`; la Beta non vincola v2 (DX-01).

## Appendice B — Non verificato

- Contenuto del dossier della v1.4 (Appendice A) e suo stato attuale; migrazioni successive alla 0055; backend object storage di gravya-app; `collaborator-grants.ts`, `access.ts`, `tier-policy.ts`, `kloud-hitl-expiry-sweeper.ts`, migrazione 0218; issue #998, #1801, #1508; `docs/decisions/`.
- Che `MAX_CASCADE_DEPTH` equivalga a una profondità di delega: il valore di `a1.delegation.max_depth` è una proposta da validare nel catalogo.
- Base giuridica ex art. 6 GDPR per gli utenti di Gravya: DA-A1-08 non la indica e l'art. 6 è ○ nel registro.
- Chi assegna la classe `ALWAYS_HITL`/`MONEY_WRITE` a una `permission_key` (catalogo §17.1, punto 21).
- Se le righe di audit del tenant escono con la cancellazione a fine contratto, e se i nodi del grafo sono «dati esportabili» (Data Act art. 2(38)) con quale export: F6.
- Unità del «gruppo» di aggregazione (tenant o record) in DX-19 e valore massimo di `access.aggregate_min_group_size_count` (regola 11 del catalogo): A6.
- Che il segnale «audit non salvato» possa essere scritto se il fallimento è dello stesso archivio; struttura della tabella dei segnali (catalogo §17.1, punto 18): A5.
- Titolarità della mappa di re-identificazione dell'attore e suo ciclo di vita: A6 e F6.
- Differenze con DECISIONS: le decisioni DA-CV-18..23 e la fine contratto (Data Act) del 2026-11-04 sono prese dal brief della v1.5, non ancora in DECISIONS; il catalogo v1.2 descrive ancora `retention.tenant_offboarding_days` come restituzione o cancellazione «entro» 30 giorni; il catalogo cita il registro v1.5, questo documento il v1.6.
- Articoli di norma letti solo dal registro v1.6: Reg. 2024/2690 (sezioni 1-3 non lette per intero), Data Act (testo EN), applicazione del Reg. 1182/71 ai termini, provvedimento del Garante 27.11.2008 (vigenza ◐, non vincolo per Gravya come responsabile).
- Soglie e valori dei criteri di §8: tutti nel catalogo, in gran parte «proposta da validare» o «da definire».

## Appendice C — Decisioni

**Decise**
- **DA-A1-01 — Backend. Decisa** (2026-11-03, utente): PostgreSQL con RLS FORCE; Neptune escluso; Neo4j alternativa solo per traversal pesanti.
- **DA-A1-05 — Rapporto con gravya-app e Beta. Chiusa da DX-01.**
- **DA-A1-07 — Retention. Assorbita da DX-09** (§7).
- **DA-A1-08 — Base giuridica. Decisa** (2026-11-03, utente; DECISIONS §6): titolare per i dati delle agenzie, Gravya per i propri utenti.
- **Audit fail-closed. Decisa** (2026-11-03; DECISIONS §6): stessa transazione, rollback.
- **Mutazioni del grafo. Decisa** (2026-11-03; DECISIONS §4): solo eventi di audit, non segmenti E1; `trace_id` se dentro un run.
- **DX-14. Decisa:** responsabile A6. **DX-18, DX-19, DX-21. Decise:** log di A6; solo aggregati di default; `config_version`.
- **Opt-in extra-UE. Decisa** (DECISIONS §6; per destinazione, DA-CV-06): sta in A6, non in A1. Strumento di trasferimento e sub-responsabile per destinazione li imposta il superadmin (DA-CV-19, 2026-11-04).
- **DA-CV-07, DA-CV-15, DA-CV-17, DA-CV-18, DA-CV-20, DA-CV-21, DA-CV-22:** applicate in §4.1, §4.5, §6, §7.

**Aperte**
- **DA-A1-02 — Fonte di verità dei mandati.** Opzioni: (a) il grafo è l'unica fonte e A2 deriva i permessi; (b) modello relazionale separato con il grafo come proiezione. Criterio: nessuna doppia scrittura. Raccomandazione: (a). (comprende il vocabolario di `permission_key` e chi assegna la classe).
- **DA-A1-03 — Trasporto eventi** (= DX-03). Opzioni: Redis Stream; Redis pub/sub; pg NOTIFY. Criterio: consegna almeno-una-volta, dati nel perimetro. Raccomandazione: Redis Stream.
- **DA-A1-04 — Allowlist tool.** Opzioni: edge `CAN_USE` nel grafo; struttura di B2. Raccomandazione: rinviare a B2.
- **DA-A1-06 — Isolamento.** Opzioni: istanza condivisa con RLS; istanza dedicata per tenant enterprise. Criterio: isolamento contro costo. Raccomandazione: condivisa, dedicata come opzione (soglia da validare).
- **DA-A1-09 — Scritture del superadmin sul grafo (DA RIPORTARE ALL'UTENTE: perimetro, DX-19).** Opzioni: (a) solo nodi di piattaforma (`tenant_id` nullo), mai nodi di un tenant; (b) anche nodi di un tenant su istruzione scritta dell'agenzia, con log di A6. Criterio: DX-19 (visibilità minima) e art. 28(3)(a). Raccomandazione: (a). La v1.4 ammetteva (b) senza decisione.
- **DA-A1-10 — Sorgente delle variabili e del log cross-tenant prima di A6 (DA RIPORTARE ALL'UTENTE: DX-22).** Opzioni: (a) istantanea versionata modificabile solo via PR, come A3 ed E3, e accessi cross-tenant negati; (b) tabella minima di piattaforma in A1, poi assorbita da A6. Criterio: DX-22 non soddisfatta da nessuna delle due; minimo lavoro da scartare. Raccomandazione: (a).

## Storico modifiche

| Versione | Data | Modifiche |
|---|---|---|
| 1.0 | 2026-11-03 | Rispetto a "Esempio A1 - completo.md": rimossi testi conversazionali e la tabella edge duplicata; rimosse le stime temporali (fasi ordinate, solo taglia S/M/L); DA rinumerate DA-A1-NN e ampliate (01 backend con PostgreSQL+RLS come opzione dal codice, invece di AGE non presente nel codice; 02 fonte di verità; 03 trasporto eventi; 04 allowlist; 05 rapporto con Beta; 06 isolamento); `Mandate` allineato a `permission_key`/`effect`/`valid_*`/`max_uses` delle tabelle reali; aggiunti `Agent.kind`, invarianti di delega, vocabolario chiuso `MONEY_WRITE`/`ALWAYS_HITL`, criteri 5-7; soglie marcate "proposta da validare"; tolti FastAPI/Pydantic e LangGraph per lo sweeper (non necessari); dipendenze da E1, A5, B2 rese esplicite; aggiunte appendici su stato reale, non verificato e decisioni. Motivo: allineamento allo stato verificato del codice e alle regole dell'utente. |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: esplicitata la dipendenza opzionale da E2 (`prompt_ref`); DA-A1-03 marcata come trasversale perché B1, B2, C1, C3 ed E2 rimandano allo stesso trasporto eventi. Motivo: dipendenze dichiarate in un solo verso e decisione duplicata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): gravya-app trattata come riferimento e non come codice da estendere; Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere; assunzioni su object storage, bus, audit e tenant riformulate; fase "Mappatura" sostituita da analisi del riferimento; DA-A1-05 chiusa da DX-01; DA-A1-02 riformulata; rischio Beta rimosso; taglia §12 ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: nessun OpenTelemetry, eventi nel modello DB-native di E1; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); Neptune marcato come fuori perimetro e DA-A1-01 da riportare all'utente; nuove DA-A1-07 (retention) e DA-A1-08 (base giuridica). Motivo: decisioni dell'utente del 2026-11-03. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente: DA-A1-01 decisa (PostgreSQL+RLS) in §3, §6, §7, §9, §11, §12 e Appendice C; rimosso il rischio Neptune e sostituito quello Neo4j; taglia §12 fissata a M (l'ipotesi L dipendeva da Neo4j). DA-A1-07 assorbita da DX-09: tolte le retention specifiche, elencate in §7 le classi di dati prodotte. §7 allineata a DX-11 (Gravya responsabile del trattamento; artt. 12/14 AI Act come buona pratica, non obbligo) e a DX-10 (notifica incidenti ad A5, A1 invia segnali); DA-A1-08 resta aperta, inquadrata da DX-11. Vocabolario GenAI semconv e traceparent ammessi senza SDK (DA-E1-05); self-hosting UE (DA-B1-06). Rimossa dall'Appendice B la verifica sui tempi di conservazione. Motivo: decisioni dell'utente del 2026-11-03 registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente: audit delle mutazioni nella stessa transazione con rollback se fallisce (nuova §4.4, §6, criterio 10, rischio); DA-A1-08 decisa (base giuridica del titolare per i dati delle agenzie, di Gravya per i suoi utenti) in §7 e Appendice C; tabella di audit minima assorbita poi da A5. DX-13: nuova §4.5 con profondità di delega, dimensione delle àncore, intervallo dello sweeper e durate di retention come variabili di piattaforma gestite dal superadmin, versionate, auditate e fail-closed; accesso cross-tenant solo come superadmin con log degli accessi (§5, §7, criteri 11-13, test, rischi). Durate di retention di default da DECISIONS.md §5 (DX-09). DX-14 citata come dipendenza da riportare; opt-in extra-UE resta aperto. Motivo: decisione dell'utente del 2026-11-03 registrata in DECISIONS.md. |
| 1.5 | 2026-11-04 | Valori fissi sostituiti dai nomi del catalogo (§4.5, §7, §8; sweeper rinominato `a1.sweeper.interval_minutes`; soglie `a1.read_batch_p99_ms`, `a1.write_p99_ms`); DX-14 decisa (A6), DX-18 (log di A6), DX-19 (aggregati, `access.aggregate_min_group_size_count`), DX-21 (`config_version`, classi senza durata); eventi `graph.*` non più segmenti E1, `trace_id` nell'audit; audit non modificabile; scadenza anche in lettura; segnali ad A5 senza soglia locale (DA-CV-07) con criterio 14; opt-in extra-UE spostato in A6; citazioni NIS2 sul Reg. 2024/2690 all. 3.2 e 11 (DX-10), notifica come flusso di A5, AI Act con calendario dopo il Reg. 2026/1744, PV-01 esteso al marketing; fine contratto secondo il Data Act; DA-A1-01, 05, 07, 08 e le righe di DECISIONS segnate come decise; nuove DA-A1-09 e DA-A1-10; snapshot non conservati da A1; Appendice B riscritta. Motivo: decisioni dell'utente del 2026-11-03/04, catalogo v1.2, registro norme v1.6. |
