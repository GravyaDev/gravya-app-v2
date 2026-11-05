# A1 — Modello del grafo dei mandati

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A1 |
| Nome | Modello del grafo dei mandati |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.6 |
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
- **F6** (DX-12, ondata 2): applica le durate di retention, assegna la classe a nodi ed edge (DX-21) e fornisce lo strumento di esportazione dei dati di un tenant (E15, §7).
- **B2**: catalogo dei tool, dove il superadmin assegna la classe `ALWAYS_HITL`/`MONEY_WRITE` (E4; fonte unica della classificazione).
- **E1**: modello DB-native per eventuale correlazione (`trace_id`); vocabolario `gravya.*`, nomi GenAI semconv e formato traceparent senza SDK né export OTel (PV-02, DA-E1-05).
- **E2** (opzionale): `Agent.prompt_ref` (chiave+versione, E2 §4.1).

**È richiesto da:** A2 (compilatore policy), A3 (via A2), A4 (validatore round-trip), A5 (audit), B2 (allowlist tool, se deriva dal grafo: DA-A1-04), F6 (retention ed esportazione sulle classi di §7), A6 (registro delle variabili `a1.*`).

**Assunzioni (da validare):**
1. Object storage compatibile S3, self-hosted nell'UE (DA-B1-06); il backend è **non verificato** e non deciso.
2. Bus eventi da scegliere (DA-A1-03 = DX-03, aperta): il primo perimetro di A1 non lo usa; gli eventi `graph.*` sono registrati in una tabella di A1 (§4.3) e il trasporto arriva con la decisione (E13).
3. Fino ad A5, tabella di audit append-only minima di v2, che A5 assorbe (DECISIONS §6).
4. Fino ad A6, le variabili vengono da un'istantanea versionata nel repository, modificabile solo con una PR, letta tramite una sola interfaccia comune a tutti i documenti: ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste (E5). I valori «proposta da validare» valgono come primo valore valido, con segnale; i valori «da definire» hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione.
5. Campo tenant: `tenant_id` (DX-07 aperta).
6. Ipotesi di lavoro approvate (E13): il grafo è l'unica fonte dei mandati (DA-A1-02) e l'istanza è condivisa con RLS (DA-A1-06).

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

Ogni nodo porta `schema_version`. Il vocabolario di `permission_key` ed `effect` lo definisce v2 (DA-A1-02); `permission_defaults` di gravya-app è un riferimento.

**Classi di approvazione (E4).** Il vocabolario è unico: `ALWAYS_HITL` e `MONEY_WRITE` (non esiste `REQUIRES_HITL`); le altre azioni seguono `hitl.approval_required_default`. La classe la assegna il superadmin nel catalogo dei tool di B2, versionata e auditata: si può solo aggiungere, e toglierla richiede la conferma di una seconda persona con accesso superadmin; un tool senza classe dichiarata va in `require_approval` (A3, B2). A1 non conserva la classe: la legge dal catalogo di B2 per validare i mandati. Per queste classi non esiste `effect=allow` automatico e la classificazione non è declassabile da UI (invarianti, catalogo §18; DA-CV-15). Per i contenuti verso terzi non c'è una classe `ALWAYS_HITL` nell'ondata 1: l'approvazione la decide l'admin agenzia con audit (DA-CV-18), da riesaminare con D1-D4.

**Dati dei clienti delle agenzie.** `Mandate.constraints`, `Delegation.constraints`, `scope` e i nomi di `Domain` possono contenere identificativi di clienti e di record dell'agenzia (per esempio `client_ids`, `record_ids`): sono dati personali di cui Gravya è responsabile (art. 28 GDPR) e anche gli identificativi interni restano dati personali (considerando 26). Sono ammessi solo identificativi interni, mai nome, email o altri dati leggibili: `constraints` è validato con uno schema a chiavi ammesse, definito con DA-A1-02 (proposta da validare). Classe di retention: quella di nodi ed edge (senza durata variabile, assegnata da F6: DX-21); le loro copie in `before`/`after` dell'audit seguono `retention.audit_decisions_months`.

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
`graph.mandate.created|updated|expired|revoked`, `graph.agent.retired`, `graph.delegation.created|revoked`; payload: `tenant_id`, `node_id`, `schema_version`, `before`, `after`, `actor`. Sono eventi di runtime (classe `retention.runtime_events_days`), registrati in una tabella di A1 e pubblicati sul bus quando DA-A1-03 sarà decisa; non sono segmenti di traccia: le mutazioni del grafo non diventano segmenti E1 (DECISIONS §4, «Mutazioni del grafo A1»). Nessun SDK OTel né export esterno (PV-02). `actor` è un identificativo pseudonimo, non nome o email.

**Propagazione di scadenza e revoca.** Un mandato scaduto o revocato non deve restare efficace in A3: la lettura batch lo esclude subito (§6) e l'evento `graph.mandate.expired|revoked` è emesso entro `a1.mandate_propagation_max_s` dal commit o da `valid_until`. Il ritardo complessivo fino al bundle in uso da A3 compone questo valore con quelli di A2 e A3 (`a3.bundle.max_age_s`): da fissare con A2 e A6 (proposta di variabile, valore da definire).

### 4.4 Audit delle mutazioni
Ogni mutazione scrive una riga append-only con `tenant_id`, `node_id`, `operation`, `before`, `after`, `actor` (pseudonimo, fornito da A6), `actor_role` (`agency_admin`/`superadmin`), `config_version` (versione delle variabili usata per validare), `trace_id` (opzionale, se la mutazione avviene dentro un run: DECISIONS §4), `created_at` (orologio del database, unica origine), `schema_version`. La riga è scritta **nella stessa transazione** della mutazione: se l'insert fallisce, rollback e nessuna mutazione (fail-closed; DECISIONS §6; DA-B2-04, DA-A3-07). Il ruolo applicativo non ha permessi di `UPDATE` né `DELETE` sulla tabella, e un trigger rifiuta `UPDATE`/`DELETE` dagli altri ruoli; la cancellazione per scadenza è del ruolo di F6, con audit. Questo è un controllo di accesso, non una verifica di integrità: DA-A1-11.

### 4.5 Variabili di piattaforma (DX-13, DX-22)
Nessun valore è nel codice né in questo documento: nome, default, intervallo, chi modifica e pagina stanno nel catalogo (`catalogo-variabili.md`). A1 legge:

| Variabile | Uso | Catalogo |
|---|---|---|
| `a1.delegation.max_depth` | profondità delle catene di delega; si applica alle nuove deleghe | §5 |
| `a1.artifact.max_properties_bytes` | dimensione massima delle proprietà di `Artifact` | §5 |
| `a1.sweeper.interval_minutes` | cadenza dello sweeper di scadenza | §5 |
| `a1.mandate_propagation_max_s` | ritardo massimo tra scadenza o revoca di un mandato ed evento emesso | da aggiungere (proposta, valore da definire) |
| `a1.read_batch_p99_ms`, `a1.write_p99_ms` | soglie di prestazione (alert e criteri) | §12 |
| `retention.runtime_events_days`, `retention.audit_decisions_months`, `retention.cross_tenant_access_log_months` | classi di §7; di sola lettura finché l'intervallo del DPA non è definito (RR) | §2 |
| `retention.tenant_offboarding_days`, `retention.tenant_offboarding_choice` | fine contratto | §2 |
| `access.aggregate_min_group_size_count` | dimensione minima dei gruppi nelle viste aggregate del superadmin | §19 |
| `access.superadmin_trace_access_ttl_hours` | durata dell'accesso del superadmin ai dati di un tenant (E8) | §19 |

Una variabile non leggibile o non valida blocca le scritture che ne dipendono (`503`, fail-closed, DX-17) con segnale ad A5; le scadenze programmate usano l'ultimo valore valido versionato (DX-17). Senza alcun valore valido: regola 4 del catalogo (DA-CV-17) e ripiego dell'istantanea (§3, assunzione 4). La produzione dell'evento `platform.config.changed` è di A6 (DX-21).

**Hash.** Algoritmo e chiave di `content_hash` e `snapshot_hash` seguono la decisione E1 sugli hash di contenuti (HMAC-SHA-256 con chiave per tenant, nella pagina credenziali, rotazione a due chiavi: DA-CV-23); applicazione ad A1 da confermare con E1, A2 e A4 (Appendice B).

## 5. Interfacce

- **Scrittura** (solo umani): `POST /v1/graph/agents`, `POST /v1/graph/mandates`, `POST /v1/graph/delegations`, `DELETE /v1/graph/nodes/{id}` (soft-delete: `retired`/`revoked`). Scrive l'admin agenzia sul proprio tenant, con MFA (DX-20). Il superadmin scrive solo nodi di piattaforma (`tenant_id` nullo), mai nodi di un'agenzia (DA-A1-09 (a), E13). Validazione con schemi condivisi (formato: DX-04).
- **Lettura batch per A2:** `GET /v1/graph/mandates?tenant_id=…&status=active` (JSON compilabile, con `snapshot_hash`), `GET /v1/graph/agents/{id}/topology`. A1 calcola `snapshot_hash` alla lettura e non conserva gli snapshot (hash: §4.5).
- **Viste aggregate del superadmin:** `GET /v1/graph/aggregates` restituisce conteggi di nodi per tipo e stato, senza identificativi, solo per gruppi di almeno `access.aggregate_min_group_size_count` tenant (DX-19, D4). Le viste sono imposte dal database (viste e ruolo dedicato senza accesso alle tabelle dei nodi), non dal solo codice applicativo.
- **Accesso cross-tenant.** Di default il superadmin vede solo dati aggregati senza identificativi (DX-19, invariante). La lettura dei dati di un singolo tenant ha due vie (E8, con l'aggiunta dell'utente): (a) **incidente dichiarato** dal superadmin, che abilita direttamente la lettura, con riferimento all'incidente (di A5 quando esisterà); (b) **richiesta di assistenza**, in cui l'admin agenzia concede l'accesso come parte della richiesta. In entrambi i casi l'accesso ha perimetro (tenant e risorse) e durata `access.superadmin_trace_access_ttl_hours` (nome scritto per le tracce, esteso qui: Appendice B), entro le istruzioni del titolare (art. 28(3)(a) GDPR; DX-13). Ogni accesso, anche in lettura, scrive nel log di A6 (DX-18: chi, tenant, risorsa, via (a) o (b), riferimento, quando). Sotto RLS FORCE la lettura passa solo da un ruolo di database dedicato e limitato, che scrive il log di A6 nella stessa transazione della lettura: se l'insert fallisce, la lettura non restituisce nulla (fail-closed; non solo garanzia applicativa). Finché il log di A6 non esiste, ogni accesso cross-tenant è negato. Nessun bypass di RLS per gli admin delle agenzie.
- Gli agenti non accedono al grafo e non creano mandati (HSAR/P16 ripreso da gravya-app).

## 6. Comportamento

**Creazione mandato:** validazione (tenant esistente; dominio dello stesso tenant; nessun mandato attivo identico → idempotenza) → transazione unica nodo + edge + riga di audit in PostgreSQL (DA-A1-01, §4.4) → commit → evento → A2 ricompila.

**Casi limite:**
- *Scadenza:* la lettura batch esclude i mandati con `valid_until` passato anche prima dello sweeper; lo sweeper li marca `expired` ed emette l'evento entro `a1.mandate_propagation_max_s` (riferimento: `kloud-hitl-expiry-sweeper.ts`, non letto).
- *Agente ritirato o mandato revocato:* mandati e deleghe collegati revocati nella stessa transazione; l'esclusione dalla lettura batch è immediata, l'evento segue entro `a1.mandate_propagation_max_s`.
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
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per i dati delle agenzie (DX-11). Il grafo contiene configurazione di governance e riferimenti a dati dei clienti delle agenzie (identificativi in `constraints`, `scope`, nomi di dominio: §4.1, con classe di retention dichiarata); `Artifact` è solo àncora. Dati personali: identificativi pseudonimi degli admin in `created_by`, `approved_by`, `actor`, e identificativi dei clienti: restano dati personali (considerando 26); le linee guida EDPB 01/2025 sono solo in consultazione e non si citano come requisito. Base giuridica (DA-A1-08, DECISIONS §6): per i dati delle agenzie è del titolare; per gli utenti di Gravya (superadmin, operatori) è di Gravya, titolare. Per i propri utenti Gravya risponde dell'art. 33(1); per i dati delle agenzie vale l'art. 33(2), senza ore, con termine contrattuale nel DPA (DA-CV-08; `incident.gdpr.*` sempre attive). A1 non invia dati a terzi né fuori dall'UE; l'opt-in extra-UE è in A6. Dati e backup self-hosted nell'UE (DA-B1-06). Cancellazione di un admin o di un cliente su richiesta del titolare: la storia dei mandati non si riscrive; l'attore resta pseudonimo, la mappa di re-identificazione non è di A1 (`retention.pseudonym_map_months`, da definire in F6); le righe di audit con identificativi del cliente scadono con la loro classe (se basti, Appendice B). Cifratura a riposo e in transito (art. 32(1)(a) GDPR; Reg. 2024/2690 all. 9) e gestione delle chiavi sono di A6, i backup di F6 (E11).
  - *Retention (DX-09, DX-12, DX-15, DX-16).* Politica unica; applicazione di F6; durate di sola lettura finché l'intervallo del DPA non è definito. Classi prodotte da A1: (1) nodi ed edge, comprese le versioni scadute e revocate e i riferimenti ai clienti delle agenzie che contengono: classe senza durata variabile, assegnata da F6 (DX-21); (2) eventi `graph.*`: `retention.runtime_events_days`; (3) audit delle mutazioni: `retention.audit_decisions_months`; (4) log cross-tenant (di A6): `retention.cross_tenant_access_log_months`; (5) segnali ad A5: `retention.incident_signals_months`, durata provvisoria fissata dall'utente prima della produzione (DA-CV-20); (6) backup: `retention.data_backup_days` (DA-CV-22: al ripristino le cancellazioni già eseguite si riapplicano). La sospensione per evidenze di incidente non è attivabile finché non sono definiti massimo, riesame e categorie (catalogo, regola 12); per i dati delle agenzie servono un'istruzione nel DPA e un parere legale prima di F6 (DA-CV-21). Fine contratto: periodo di recupero di almeno `retention.tenant_offboarding_days` dalla fine del periodo di passaggio, poi cancellazione (Data Act art. 25(2)); la scelta restituzione o cancellazione è `retention.tenant_offboarding_choice`, sempre disponibile all'agenzia (art. 28(3)(g) GDPR). Che il SaaS sia un «servizio di trattamento dei dati» va confermato con un legale.
  - *Esportabilità (E15).* I dati di un tenant conservati da A1 sono esportabili con lo strumento di F6 (formato strutturato; il formato non è fissato qui, proposta del coordinator in attesa di conferma dell'utente). Sono: le righe di `Tenant`, `Agent`, `Mandate`, `Domain`, `Delegation` e `Artifact` del tenant (per `Artifact` solo URI, hash e metadati: il payload sta nell'object storage e non è di A1), gli edge con le loro proprietà, gli eventi `graph.*` e le righe di audit del tenant. A1 espone a F6 una lettura per tenant; se le righe di audit escano con la cancellazione a fine contratto è aperto (Appendice B).
  - *NIS2.* Gravya oggi non è soggetto NIS2; la progettazione è «NIS2 compliant ready by design» (DX-10). Per log e accessi privilegiati il riferimento è il Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11 (non l'art. 21 della direttiva, che non nomina i log): audit append-only con modifica impedita a ruoli e trigger (senza verifica di integrità: DA-A1-11), attività degli account amministrativi e accessi privilegiati registrati, orologio del database come origine unica, MFA per gli account privilegiati (DX-20). Il regolamento non fissa una durata di conservazione; dove usa «se opportuno» una deroga si documenta (art. 2(2)). Notifica degli incidenti: flusso di A5, presente ma non attivo finché `incident.nis2_flow_active` è falso (preallarme, notifica e relazione finale con i termini `incident.nis2.*`, destinatario CSIRT Italia, decorrenza dalla conoscenza); A1 invia i segnali di §6 senza soglia locale. Parametri `security.*` dell'allegato: catalogo §19, non attivabili senza intervallo deciso.
  - *AI Act.* A1 non contiene LLM, non genera contenuti né interagisce con persone: l'art. 50 (applicabile dal 2.8.2026) non si applica direttamente; etichetta «generato da AI» e marcatura sono di C1 e D1-D4. Gli artt. 12, 14, 19, 26 sono solo buona pratica (DX-11) e comunque dal 2.12.2027 per l'alto rischio (Reg. 2026/1744): i mandati sono definiti solo da umani, le chiavi `ALWAYS_HITL`/`MONEY_WRITE` impongono l'HITL.
  - *Marketing.* A1 non invia comunicazioni né traccia utenti: ePrivacy e artt. 122 e 130 del Codice privacy non sono toccati (dettaglio in D1-D4).
  - *Osservabilità AI.* `snapshot_hash` riconduce ogni decisione di policy alla versione dei mandati in vigore; la storia è ricostruibile da `valid_from`/`valid_until` e dall'audit.
  - *Credenziali.* Il modello non richiede credenziali; nessuna è in questo documento (DX-22 (b)).

## 8. Criteri di accettazione

1. **Integrità:** query di validazione sugli edge con estremi mancanti = 0 (CI).
2. **Isolamento:** due tenant: 0 nodi del tenant B nelle risposte del tenant A, anche con query diretta usando il ruolo runtime.
3. **Idempotenza:** due POST identici → 1 `Mandate` e 1 `HAS_MANDATE`.
4. **Scadenza e revoca:** un mandato con `valid_until` passato o revocato è assente dalla lettura batch senza attendere lo sweeper; l'evento `graph.mandate.expired|revoked` è emesso entro `a1.mandate_propagation_max_s` (misurato su N mandati di prova, N parametro del test) e dopo un giro dello sweeper (`a1.sweeper.interval_minutes`) lo stato è `expired`.
5. **Delega:** scope maggiore del delegante → `422`; catena oltre `a1.delegation.max_depth` → `422`.
6. **Vocabolario chiuso:** `allow` automatico su `MONEY_WRITE`/`ALWAYS_HITL` → rifiutato; tentativo di declassamento da UI → rifiutato.
7. **Àncore:** 0 proprietà di `Artifact` oltre `a1.artifact.max_properties_bytes`; nessun payload.
8. **Audit:** N mutazioni → N righe con tutti i campi di §4.4; `UPDATE`/`DELETE` sulla tabella con il ruolo runtime → errore.
9. **Prestazioni:** p99 entro `a1.read_batch_p99_ms` e `a1.write_p99_ms` su dataset sintetico (§7).
10. **Audit fail-closed:** con l'insert forzato a fallire: `503`, 0 righe parziali, nessun evento `graph.*`, un segnale ad A5.
11. **Variabili:** con `a1.delegation.max_depth` impostata a un valore di prova N dal superadmin, una catena di profondità N+1 → `422` senza rilascio; la modifica produce una nuova `config_version` (di A6) e la riga di audit riporta quella versione; con la variabile illeggibile la creazione di una delega → `503` e un segnale; con lo sweeper e variabile illeggibile si usa l'ultimo valore valido.
12. **Accesso cross-tenant:** admin del tenant A che legge B → 0 risultati; superadmin: nessun identificativo nelle viste aggregate e nessun risultato per gruppi sotto `access.aggregate_min_group_size_count`; lettura di un singolo tenant senza incidente dichiarato né concessione dell'admin agenzia → negata; con incidente dichiarato (via a) o concessione nella richiesta di assistenza (via b) → letta, con 1 riga nel log di A6 per richiesta che riporta la via e il riferimento; dopo `access.superadmin_trace_access_ttl_hours` → negata; con il log forzato a fallire → nessun dato restituito e segnale.
13. **Retention:** nel codice di A1 nessuna costante di durata (lint o grep in CI); i valori letti dal registro per le tre classi di §4.5 coincidono con il catalogo; un tentativo del superadmin di modificarli fuori dall'intervallo (non ancora definito: sola lettura) → rifiutato.
14. **Segnali:** per ogni evento elencato in §6, esattamente un segnale ad A5, senza soglia locale.
15. **Scritture del superadmin:** `POST` del superadmin su un nodo di un tenant → `403`; su un nodo di piattaforma (`tenant_id` nullo) → eseguito, con riga di audit.
16. **Dati dei clienti ed esportazione:** `constraints` con una chiave non ammessa (per esempio un nome o un'email) → `422`; l'esportazione per tenant di prova contiene tutte le tabelle elencate in §7 e 0 righe di altri tenant.
17. **Variabili prima di A6:** con il valore letto dall'istantanea «da definire» fuori produzione si usa il valore di sviluppo; con `a1.delegation.max_depth` valore «proposta da validare» si usa il valore e parte un segnale; in produzione una variabile «da definire» blocca la scrittura dipendente (`503`).

## 9. Piano di implementazione

1. **Decisioni preliminari:** DA-A1-03 (DX-03; non serve al primo perimetro), DX-04, DX-07, DA-A1-04, DA-A1-11. Già decise o in ipotesi di lavoro: DA-A1-01, DA-A1-02, DA-A1-06, DA-A1-08, DA-A1-09, DA-A1-10, audit fail-closed, DX-13, DX-14, DX-18, DX-19, DX-21, E4, E8, E15.
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
| Abuso dell'accesso cross-tenant | Alto | Solo aggregati di default, due vie di accesso (incidente dichiarato, concessione dell'admin agenzia) con perimetro e durata, ruolo di database dedicato che scrive il log di A6 nella stessa transazione, accesso negato senza log (criterio 12) |
| Mandato scaduto o revocato ancora efficace in A3 | Alto | Esclusione immediata dalla lettura batch, evento entro `a1.mandate_propagation_max_s` (criterio 4) |
| Identificativi di clienti nei nodi e nell'audit | Medio | Schema a chiavi ammesse (criterio 16), classe di retention dichiarata, esportazione e cancellazione tramite F6 |
| Variabile modificata male | Medio | Versionata e auditata da A6; validazione; fail-closed |
| A6, A5 e F6 non ancora documentati | Medio | Interfacce con ripieghi dichiarati (DA-A1-10); accesso cross-tenant negato finché manca il log |

## 12. Stima e priorità

- **Dimensione:** M (costruzione da zero su PostgreSQL con RLS; DA-A1-01) — proposta da validare.
- **Dipendenze critiche:** DX-04, DX-07, DA-A1-04, DA-A1-11; ipotesi di lavoro DA-A1-02 e DA-A1-06; per il pieno funzionamento A6, A5, F6 (ondata 2) e il catalogo dei tool di B2.
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
- Corrispondenza tra `permission_key` e tool del catalogo di B2, da cui A1 legge la classe `ALWAYS_HITL`/`MONEY_WRITE` (E4): non definita (DA-A1-04).
- Se le righe di audit del tenant escono con la cancellazione a fine contratto; se i nodi del grafo siano «dati esportabili» (Data Act art. 2(38)): l'elenco di §7 è la scelta di A1, F6 conferma; il formato dell'esportazione è una proposta del coordinator non confermata.
- Se la scadenza delle righe di audit con identificativi di un cliente soddisfi una richiesta di cancellazione (art. 17 GDPR; DECISIONS §5, «Da verificare»).
- Applicazione ad A1 della decisione E1 sugli hash (HMAC-SHA-256 con chiave per tenant) a `content_hash` e `snapshot_hash`: A4 deve poter verificare lo snapshot; la chiave per tenant non è ancora nel catalogo §15.
- Estensione di `access.superadmin_trace_access_ttl_hours` (definita per le tracce) agli accessi ai dati del grafo; schema del log di A6 e struttura del riferimento all'incidente (A5, A6).
- Nome e valore di `a1.mandate_propagation_max_s` (proposta di variabile, non nel catalogo); coerenza con la variabile di propagazione che A3 e A2 proporranno.
- Unità del «gruppo» di aggregazione (tenant o record) in DX-19 e valore massimo di `access.aggregate_min_group_size_count` (regola 11 del catalogo): A6.
- Che il segnale «audit non salvato» possa essere scritto se il fallimento è dello stesso archivio; struttura della tabella dei segnali (catalogo §17.1, punto 18): A5.
- Titolarità della mappa di re-identificazione dell'attore e suo ciclo di vita: A6 e F6.
- Le decisioni E1-E16 del 2026-11-04 sono applicate dal testo del blocco E e del brief della v1.6; il registrar le sta registrando in DECISIONS e non ho verificato che il testo coincida.
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
- **DA-A1-09 — Scritture del superadmin. Decisa (a)** (2026-11-04, utente, E13): solo nodi di piattaforma, mai nodi di un'agenzia.
- **DA-A1-10 — Sorgente delle variabili prima di A6. Decisa** (2026-11-04, utente, E5): istantanea versionata nel repository, modificabile solo con una PR, una sola interfaccia; ripiego che non soddisfa DX-22.
- **DA-A1-02 e DA-A1-06 — ipotesi di lavoro approvate** (2026-11-04, utente, E13): il grafo come unica fonte dei mandati; istanza condivisa con RLS, dedicata come opzione futura. Non sono decisioni formali di DECISIONS.
- **E4, E8, E11, E15** (2026-11-04, utente): classi di approvazione e chi le assegna (§4.1); accesso del superadmin per incidente dichiarato o concessione dell'admin agenzia (§5); cifratura e backup (§7); esportazione dei dati del tenant con lo strumento di F6 (§7).

**Aperte**
- **DA-A1-03 — Trasporto eventi** (= DX-03). Opzioni: Redis Stream; Redis pub/sub; pg NOTIFY. Criterio: consegna almeno-una-volta, dati nel perimetro. Raccomandazione: Redis Stream. Il primo perimetro di A1 non la usa (E13).
- **DA-A1-04 — Allowlist tool e corrispondenza `permission_key`–tool.** Opzioni: edge `CAN_USE` nel grafo; struttura di B2. Criterio: fonte unica. Raccomandazione: rinviare a B2.
- **DA-A1-11 — Verifica di integrità dell'audit (conformità: DA RIPORTARE ALL'UTENTE).** Opzioni: (a) solo permessi e trigger; (b) catena di hash per riga, verificata periodicamente; (c) esportazione periodica su supporto non riscrivibile. Criterio: Reg. 2024/2690 all. 3.2.5 (protezione da modifiche non autorizzate; nessuna inalterabilità richiesta), costo. Raccomandazione: (a) per l'ondata 1, poi (b) con A5, che assorbe l'audit.

## Storico modifiche

| Versione | Data | Modifiche |
|---|---|---|
| 1.0 | 2026-11-03 | Rispetto a "Esempio A1 - completo.md": rimossi testi conversazionali e la tabella edge duplicata; rimosse le stime temporali (fasi ordinate, solo taglia S/M/L); DA rinumerate DA-A1-NN e ampliate (01 backend con PostgreSQL+RLS come opzione dal codice, invece di AGE non presente nel codice; 02 fonte di verità; 03 trasporto eventi; 04 allowlist; 05 rapporto con Beta; 06 isolamento); `Mandate` allineato a `permission_key`/`effect`/`valid_*`/`max_uses` delle tabelle reali; aggiunti `Agent.kind`, invarianti di delega, vocabolario chiuso `MONEY_WRITE`/`ALWAYS_HITL`, criteri 5-7; soglie marcate "proposta da validare"; tolti FastAPI/Pydantic e LangGraph per lo sweeper (non necessari); dipendenze da E1, A5, B2 rese esplicite; aggiunte appendici su stato reale, non verificato e decisioni. Motivo: allineamento allo stato verificato del codice e alle regole dell'utente. |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: esplicitata la dipendenza opzionale da E2 (`prompt_ref`); DA-A1-03 marcata come trasversale perché B1, B2, C1, C3 ed E2 rimandano allo stesso trasporto eventi. Motivo: dipendenze dichiarate in un solo verso e decisione duplicata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): gravya-app trattata come riferimento e non come codice da estendere; Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere; assunzioni su object storage, bus, audit e tenant riformulate; fase "Mappatura" sostituita da analisi del riferimento; DA-A1-05 chiusa da DX-01; DA-A1-02 riformulata; rischio Beta rimosso; taglia §12 ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: nessun OpenTelemetry, eventi nel modello DB-native di E1; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); Neptune marcato come fuori perimetro e DA-A1-01 da riportare all'utente; nuove DA-A1-07 (retention) e DA-A1-08 (base giuridica). Motivo: decisioni dell'utente del 2026-11-03. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente: DA-A1-01 decisa (PostgreSQL+RLS) in §3, §6, §7, §9, §11, §12 e Appendice C; rimosso il rischio Neptune e sostituito quello Neo4j; taglia §12 fissata a M (l'ipotesi L dipendeva da Neo4j). DA-A1-07 assorbita da DX-09: tolte le retention specifiche, elencate in §7 le classi di dati prodotte. §7 allineata a DX-11 (Gravya responsabile del trattamento; artt. 12/14 AI Act come buona pratica, non obbligo) e a DX-10 (notifica incidenti ad A5, A1 invia segnali); DA-A1-08 resta aperta, inquadrata da DX-11. Vocabolario GenAI semconv e traceparent ammessi senza SDK (DA-E1-05); self-hosting UE (DA-B1-06). Rimossa dall'Appendice B la verifica sui tempi di conservazione. Motivo: decisioni dell'utente del 2026-11-03 registrate in DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente: audit delle mutazioni nella stessa transazione con rollback se fallisce (nuova §4.4, §6, criterio 10, rischio); DA-A1-08 decisa (base giuridica del titolare per i dati delle agenzie, di Gravya per i suoi utenti) in §7 e Appendice C; tabella di audit minima assorbita poi da A5. DX-13: nuova §4.5 con profondità di delega, dimensione delle àncore, intervallo dello sweeper e durate di retention come variabili di piattaforma gestite dal superadmin, versionate, auditate e fail-closed; accesso cross-tenant solo come superadmin con log degli accessi (§5, §7, criteri 11-13, test, rischi). Durate di retention di default da DECISIONS.md §5 (DX-09). DX-14 citata come dipendenza da riportare; opt-in extra-UE resta aperto. Motivo: decisione dell'utente del 2026-11-03 registrata in DECISIONS.md. |
| 1.5 | 2026-11-04 | Valori fissi sostituiti dai nomi del catalogo (§4.5, §7, §8; sweeper rinominato `a1.sweeper.interval_minutes`; soglie `a1.read_batch_p99_ms`, `a1.write_p99_ms`); DX-14 decisa (A6), DX-18 (log di A6), DX-19 (aggregati, `access.aggregate_min_group_size_count`), DX-21 (`config_version`, classi senza durata); eventi `graph.*` non più segmenti E1, `trace_id` nell'audit; audit non modificabile; scadenza anche in lettura; segnali ad A5 senza soglia locale (DA-CV-07) con criterio 14; opt-in extra-UE spostato in A6; citazioni NIS2 sul Reg. 2024/2690 all. 3.2 e 11 (DX-10), notifica come flusso di A5, AI Act con calendario dopo il Reg. 2026/1744, PV-01 esteso al marketing; fine contratto secondo il Data Act; DA-A1-01, 05, 07, 08 e le righe di DECISIONS segnate come decise; nuove DA-A1-09 e DA-A1-10; snapshot non conservati da A1; Appendice B riscritta. Motivo: decisioni dell'utente del 2026-11-03/04, catalogo v1.2, registro norme v1.6. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 dell'utente: ripiego comune delle variabili (E5, DA-A1-10 decisa); DA-A1-09 (a) decisa, DA-A1-02 e DA-A1-06 in ipotesi di lavoro, DA-A1-03 non usata dal primo perimetro (E13); classi `ALWAYS_HITL`/`MONEY_WRITE` assegnate dal superadmin nel catalogo di B2 (E4); accesso del superadmin per incidente dichiarato o concessione dell'admin agenzia, con ruolo di database dedicato che scrive il log (E8 e aggiunta, rilievo R-13); esportazione dei dati del tenant con lo strumento di F6 (E15); cifratura e backup (E11, rilievo R-10); hash secondo E1; dati dei clienti delle agenzie dichiarati con classe di retention e schema a chiavi ammesse (rilievo R-01); propagazione di scadenza e revoca entro `a1.mandate_propagation_max_s` (rilievo R-02); audit append-only senza pretesa di integrità, nuova DA-A1-11 (rilievo R-11); tolte le note «non ancora in DECISIONS» (catalogo v1.3); nuovi criteri 15-17. Motivo: revisione unica della v1.5 (plan-auditor e compliance-auditor, RIPORTA) e decisioni del 2026-11-04. |
