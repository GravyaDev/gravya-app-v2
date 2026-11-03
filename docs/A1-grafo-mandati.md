# A1 — Modello del grafo dei mandati

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A1 |
| Nome | Modello del grafo dei mandati |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.2 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** Definisce lo schema canonico di *chi* è un agente (`Agent`), *quali mandati* ha (`Mandate`), *su quali domini* opera (`Domain`), *quali artefatti* produce o consuma (`Artifact`) e *quali deleghe* esistono (`Delegation`), con edge tipizzati. È la mappa da cui A2 compila le policy.

**Cosa NON fa.**
- Non contiene payload (brief, creatività, PDF, transcript): `Artifact` è un nodo-àncora con URI e hash verso l'object storage.
- Non è interrogato sul percorso caldo: A3 usa le policy compilate da A2.
- Non sostituisce PostgreSQL per i dati applicativi. Non estende né importa le tabelle di permessi di gravya-app: v2 si costruisce da zero (PV-03); quelle tabelle sono solo riferimento (Appendice A).

**Perché esiste.** Nel sistema precedente (gravya-app) i mandati erano distribuiti in più tabelle relazionali e in costanti nel codice (Appendice A). Un modello unico, ispezionabile e versionato rende la governance verificabile (master plan §1 punto 3).

## 3. Contesto e dipendenze

**Dipende da:** nessun sottoprodotto per lo schema. Per gli eventi di audit si appoggia ad A5 (ondata successiva); finché A5 non esiste, registra le mutazioni in una tabella di audit propria di v2 (Assunzione 3). Per tracciare le mutazioni usa il modello DB-native di E1 (vocabolario `gravya.*`, nessun OpenTelemetry: PV-02). Il campo opzionale `Agent.prompt_ref` referenzia E2 (chiave+versione, E2 §4.1).

**È richiesto da:** A2 (compilatore policy), A3 (indirettamente, via A2), A4 (validatore round-trip), A5 (audit trail), B2 (allowlist tool per agente, se deriva dal grafo — DA-A1-04).

**Assunzioni (da validare):**
1. L'object storage di v2 è compatibile S3 e ospitato nel perimetro controllato (UE); gravya-app usava tier `general`/`protected` con Garage citato come destinazione, da prendere come riferimento. Il backend effettivo è **Non verificato** e non deciso.
2. Il bus eventi è da scegliere (DA-A1-03 = DX-03); gravya-app usava Redis 7, che resta solo un riferimento.
3. Fino a A5 le mutazioni si registrano in una tabella di audit append-only di v2 (in gravya-app l'analogo era `gravya_event_logs`).
4. Il nome del campo tenant (`tenant_id` o `company_id`) segue DX-07; in questo documento si usa `tenant_id`.

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

Ogni nodo porta `schema_version`. Il vocabolario di `permission_key` ed `effect` è definito da v2 (DA-A1-02); il modello permessi di gravya-app (`permission_defaults`) è un riferimento da cui partire. Le chiavi `ALWAYS_HITL`/`MONEY_WRITE` non possono avere `effect=allow` automatico (regola ripresa dalla visione kloudify, A5, e dalla migrazione 0218 di gravya-app — citata, non letta).

### 4.2 Edge

| Edge | Da → A | Semantica |
|---|---|---|
| `HAS_MANDATE` | `Agent` → `Mandate` | L'agente detiene il mandato |
| `OPERATES_IN` | `Mandate` → `Domain` | Ambito di validità |
| `DELEGATES_TO` | `Agent` → `Delegation` | L'agente cede parte del proprio scope |
| `DELEGATION_TARGET` | `Delegation` → `Agent` | Destinatario della delega |
| `PRODUCES` / `CONSUMES` | `Agent` → `Artifact` | Output / input |
| `BELONGS_TO` | `Agent`, `Mandate`, `Domain`, `Artifact` → `Tenant` | Appartenenza |

Proprietà comuni: `created_at`, `valid_from`, `valid_until`, `metadata`. Invariante: una `Delegation` non può concedere più scope del mandato del delegante, e la catena ha profondità massima configurabile (proposta da validare: 3, valore ripreso da `MAX_CASCADE_DEPTH` di gravya-app, che però riguarda le cascate di automazioni, non le deleghe).

### 4.3 Eventi emessi
`graph.mandate.created|updated|expired|revoked`, `graph.agent.retired`, `graph.delegation.created|revoked`; payload: `tenant_id`, `node_id`, `schema_version`, `before`, `after`, `actor`. Gli eventi sono registrati nel modello dati DB-native di E1 con attributi `gravya.*` (PV-02); nessun export verso collector o servizi esterni. `actor` è un identificativo pseudonimo dell'utente, non nome o email (minimizzazione).

## 5. Interfacce

- Scrittura (solo Control Plane, attore umano admin/superadmin): `POST /v1/graph/agents`, `POST /v1/graph/mandates`, `POST /v1/graph/delegations`, `DELETE /v1/graph/nodes/{id}` (soft-delete: `status=retired`/`revoked`). Validazione con schemi condivisi (formato da DX-04; zod era lo standard in gravya-app).
- Lettura batch per A2: `GET /v1/graph/mandates?tenant_id=…&status=active` (JSON compilabile, con `snapshot_hash`), `GET /v1/graph/agents/{id}/topology`.
- Gli agenti non hanno accesso al grafo. I campi di mandato sono scrivibili solo da umani (principio HSAR/P16 ripreso da gravya-app): un agente non può creare mandati.

## 6. Comportamento

**Creazione mandato:** validazione (tenant esiste; dominio dello stesso tenant; nessun mandato attivo identico → idempotenza) → transazione unica nodo+edge → evento → A2 ricompila.

**Casi limite:**
- *Scadenza:* uno sweeper marca `expired` i mandati con `valid_until < now()` ed emette l'evento. Riferimento: `kloud-hitl-expiry-sweeper.ts` di gravya-app (citato, non letto).
- *Agente ritirato:* mandati e deleghe in uscita/entrata revocati nella stessa transazione.
- *Delega che eccede lo scope del delegante o la profondità massima:* rifiutata con `422`.
- *Fallimento parziale:* rollback totale, risposta `409` con errore strutturato.
- *Errore di lettura per A2:* A2 mantiene l'ultimo bundle valido (fail-closed per i nuovi mandati, coerente con P8).

## 7. Requisiti non funzionali

- **Prestazioni (proposta da validare):** lettura batch p99 < 100 ms per tenant con ≤ 1.000 mandati; scrittura p99 < 50 ms.
- **Sicurezza:** isolamento per tenant applicato dal database, non solo da `WHERE` (master plan §7). Se il backend è PostgreSQL: RLS FORCE (soluzione validata in gravya-app). Se è Neo4j: meccanismo da definire (DA-A1-01).
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Il grafo contiene configurazione di governance, non dati di clienti finali: `Artifact` è solo àncora (URI + hash), nessun payload (criterio 7). Dati personali presenti: identificativi degli utenti admin in `created_by`/`approved_by`/`actor` (pseudonimi). Base giuridica proposta: legittimo interesse/obbligo di accountability della governance (art. 6.1.f, art. 5.2) — **DA RIPORTARE ALL'UTENTE** (DA-A1-08). Retention di mandati revocati/scaduti e dei relativi audit: non decisa — **DA RIPORTARE ALL'UTENTE** (DA-A1-07). Diritti dell'interessato: la cancellazione di un utente admin non può cancellare la storia dei mandati; proposta pseudonimizzazione dell'`actor`, da validare in DA-A1-07. Dati e backup nel perimetro controllato UE.
  - *NIS2 (art. 21).* Controllo accessi: scrittura solo per admin/superadmin, mai agenti; isolamento tenant con RLS; log di audit append-only di ogni mutazione (supporto a gestione e notifica incidenti, art. 23); crittografia a riposo e in transito; backend unico nel perimetro (no servizi gestiti extra-UE di default: Amazon Neptune escluso salvo decisione dell'utente, DA-A1-01).
  - *AI Act.* A1 non contiene LLM; contribuisce alla sorveglianza umana (art. 14) perché i mandati sono definiti solo da umani e le chiavi `ALWAYS_HITL`/`MONEY_WRITE` impongono l'HITL; i log delle mutazioni concorrono alla tracciabilità (art. 12). Trasparenza art. 50: non applicabile direttamente (nessuna interazione con persone).
  - *Osservabilità AI.* Rende osservabile chi poteva fare cosa quando: `snapshot_hash` del grafo letto da A2 permette di ricondurre ogni decisione di policy di un agente alla versione dei mandati in vigore; eventi `graph.*` nel modello DB-native di E1.
- **Osservabilità:** ogni mutazione genera un evento di audit (chi, cosa, quando, prima/dopo), DB-native (PV-02).
- **Scalabilità (proposta da validare):** 10.000 `Agent` e 100.000 `Artifact` per tenant senza degrado oltre le soglie sopra.

## 8. Criteri di accettazione

1. **Integrità:** query di validazione che conta edge con estremi mancanti = 0 (test automatico in CI).
2. **Isolamento:** test di integrazione con due tenant: 0 nodi del tenant B nelle risposte del tenant A, anche con query diretta al DB usando il ruolo runtime.
3. **Idempotenza:** due POST identici → 1 nodo `Mandate` e 1 edge `HAS_MANDATE`.
4. **Scadenza:** mandato con `valid_until` passato assente dalla lettura batch dopo un giro di sweeper.
5. **Delega:** delega con scope maggiore del delegante → `422`; catena oltre la profondità massima → `422`.
6. **Vocabolario chiuso:** mandato `allow` automatico su chiave `MONEY_WRITE`/`ALWAYS_HITL` → rifiutato.
7. **Àncore:** 0 proprietà di nodo `Artifact` oltre una dimensione massima (proposta da validare: 4 KB); nessun payload nel grafo.
8. **Audit:** N mutazioni → N righe di audit con campi obbligatori.
9. **Prestazioni:** soglie §7 misurate su dataset sintetico (proposta da validare).

## 9. Piano di implementazione

Fasi ordinate:
1. **Decisioni preliminari:** DA-A1-01 (backend), DA-A1-02 (modello unico dei permessi in v2), DA-A1-07 (retention), DA-A1-08 (base giuridica).
2. **Analisi del riferimento:** studio delle tabelle di gravya-app (`agent_registry`, `gravya_supervisors`, `gravya_executors`, `gravya_supervisor_pipeline`, `gravya_executor_tools`, `principal_permission_grants`, `permission_defaults`, `permission_exceptions`) per estrarre requisiti e casi d'uso da coprire nello schema nuovo; nessuna migrazione di dati né codice.
3. **Schema:** vincoli di unicità su `id`, indici su `tenant_id`, `status`, `valid_until`; `schema_version`.
4. **API** di scrittura e lettura con validazione degli schemi (DX-04).
5. **Eventi** (DA-A1-03) e **sweeper** di scadenza.
6. **Test** di integrità, isolamento, prestazioni.

**Tecnologie:** dal master plan Neo4j/Neptune (Neptune è un servizio gestito AWS: sposta i dati fuori dal perimetro controllato, non scelto di default); come riferimento validato in gravya-app PostgreSQL 17 + RLS, Express 5, zod, Redis 7, client S3. La scelta è aperta (DA-A1-01). Nessun SDK OpenTelemetry (PV-02).

## 10. Test e valutazione

- **Unit:** schemi zod, invarianti di delega, vocabolario chiuso, errori 409/422/404.
- **Integration:** due tenant, isolamento; sweeper; ritiro agente con revoca a cascata.
- **Security:** token di tenant manipolato → 403/404; tentativo di scrittura con attore agente → rifiutato; audit senza nome/email in chiaro dell'attore.
- **Performance:** 1.000 letture batch, p99 misurato.
- **Eval:** non applicabile (nessun LLM).

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Modello permessi frammentato in più strutture (difetto osservato in gravya-app: grants, defaults, exceptions) | Alto | DA-A1-02: una sola fonte in v2 |
| Nuova tecnologia (Neo4j) senza RLS equivalente | Alto | DA-A1-01; test di isolamento obbligatori in CI |
| Grafo usato come magazzino | Medio | Criterio 7; review dello schema |
| Deriva schema/documento | Medio | `schema_version`, migrazioni versionate, A4 |
| Backend fuori dal perimetro controllato (Neptune o servizio gestito extra-UE) | Alto | DA-A1-01 da riportare all'utente (PV-01) |
| Audit con dati personali conservati senza limite | Medio | DA-A1-07, pseudonimizzazione dell'attore |

## 12. Stima e priorità

- **Dimensione:** L per costruzione da zero se DA-A1-01 sceglie Neo4j; M se sceglie PostgreSQL + RLS (tecnologia già nello stack v2, nessun riuso di tabelle) — proposta da validare.
- **Dipendenze critiche:** DA-A1-01, DA-A1-02, DX-03, DX-07; nessun sottoprodotto a monte.
- **Thin-slice MVP:** sì, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (riferimento, non codice da riusare: PV-03).

**Soluzioni da riprendere come idea (letto):**
- `packages/db/src/schema/principal_permission_grants.ts`: grant per `company_id`, `principal_type` (users/agents/services), `permission_key`, `scope` jsonb, `valid_from/until`, `max_uses`, revoca soft, `condition_dsl`/`compiled_condition`. È il concetto più vicino a `Mandate`.
- `server/src/services/grant-evaluator.ts`: verifica del ciclo di vita del grant; condizioni compilate che falliscono chiuse (`grant-condition/`). Nota: il commento iniziale dice "No audit event is written here", mentre il docblock della funzione dice che scrive l'audit — incoerenza interna da verificare.
- `permission_defaults.ts`, `permission_exceptions.ts` (gravya-app#998, pezzo 1): tabella per classe di principal per azienda + righe piattaforma (`company_id IS NULL`); eccezioni per persona tenute **deliberatamente fuori** da `principal_permission_grants`.
- `gravya_agent_registry.ts` (`agent_registry`, migrazione 0054): registry di supervisori/esecutori con `rules_accepts/rejects/escalates`, senza `company_id`.
- Migrazione `0055_gravya_dynamic_agents.sql`: `gravya_supervisors`, `gravya_executors`, `gravya_tools`, `gravya_supervisor_pipeline`, `gravya_executor_tools` — la topologia agente→agente→tool è già relazionale.
- `gravya_agent_policies.ts`: criteri di qualità per agente, versionati, immutabili, solo superadmin, senza tenant.
- `services/agents/src/automation/dispatcher.py`: `MAX_CASCADE_DEPTH = 3`.

**Da kloudify (`docs/visione/controlli-e-conformita.md`, via ricognizione):** classi Admin/Membro/Kloud/Supervisore/Agente; modello permessi #998 in costruzione, pezzo 4 da riscrivere; enforcement in `tools/_scope_enforcement.py` "irraggiungibile finché gli agenti non eseguono i tool".

**Difetti e lezioni da non ripetere:** modello permessi frammentato in tre tabelle; topologia agenti senza tenant; commenti contraddittori in `grant-evaluator`; delega solo implicita nella pipeline.

**Divergenze di gravya-app dal master plan (per contesto):**
1. Nessun graph database (grep `neo4j`: 0 risultati); i mandati sono relazionali con RLS.
2. Nessun nodo `Delegation` né `Domain`: la delega è implicita nella pipeline supervisore→esecutore e nella catena Kloud→supervisore→agente.
3. Nessun `Artifact` àncora nel modello permessi; esiste `gravya_files` con `storage_tier`.
4. Tre tabelle di permesso coesistono (grants, defaults, exceptions) per scelta esplicita: il grafo non può essere "l'unica fonte" senza decidere su di esse.
5. Le tabelle della topologia agenti non hanno `company_id` (sono di piattaforma), mentre il master prevede agenti per tenant.
6. Nessun documento in kloudify cita gravya-app-v2. La Beta di gravya-app non vincola v2 (DX-01).

## Appendice B — Non verificato

- Backend object storage di gravya-app in produzione (S3 o Garage), utile solo come riferimento.
- Se migrazioni successive alla 0055 di gravya-app abbiano aggiunto `company_id`/RLS alle tabelle agenti.
- Che la base giuridica e i tempi di conservazione proposti in §7 siano leciti (non verificato con le analisi `gravya-app/docs/compliance/gdpr`, da riverificare).
- Contenuto di `collaborator-grants.ts`, `access.ts`, `tier-policy.ts`, `kloud-hitl-expiry-sweeper.ts`, migrazione 0218.
- Se `grant-evaluator` scriva davvero l'audit (commenti contraddittori).
- Che `MAX_CASCADE_DEPTH` equivalga a una profondità di delega.
- Stato attuale delle issue #998, #1801, #1508.
- Che `docs/decisions/` contenga ADR pertinenti: contiene un solo file (`2026-09-13-image-pipes-evaluation-canvas-gamma.md`), non pertinente dal nome, non letto.
- Tutte le soglie numeriche di §7-8.

## Appendice C — Decisioni aperte

- **DA-A1-01 — Backend del grafo. DA RIPORTARE ALL'UTENTE.** Opzioni: (a) Neo4j (master plan), self-hosted nel perimetro UE; (b) Amazon Neptune (master plan): servizio gestito AWS, sposta i dati fuori dal controllo diretto di Gravya — non scelto di default (PV-01); (c) PostgreSQL 17 con tabelle nodi/edge e RLS FORCE (soluzione validata in gravya-app come idea). Criterio: isolamento per tenant applicato dal DB, dati nel perimetro controllato, numero di tecnologie. Raccomandazione: (c) per l'ondata 1, con schema logico identico a §4 per migrare a (a) se le query di traversal lo richiedono; da confermare dall'utente perché diverge dal master plan.
- **DA-A1-02 — Fonte di verità dei mandati in v2** (riformulata da DX-01). Opzioni: (a) il grafo è l'unica fonte e i permessi di runtime sono derivati da A2; (b) un modello permessi relazionale separato con il grafo come proiezione. Criterio: assenza di doppia scrittura, nessuna frammentazione come in gravya-app. Raccomandazione: (a). Le opzioni legate alle tabelle di gravya-app decadono.
- **DA-A1-03 — Trasporto eventi** (= DX-03). Opzioni: Redis Stream; Redis pub/sub; pg NOTIFY. Criterio: consegna almeno-una-volta, dati nel perimetro. Raccomandazione: Redis Stream. Decisione trasversale (B1, B2, C1, C3, E2).
- **DA-A1-04 — Allowlist tool nel grafo.** Opzioni: edge `CAN_USE` `Agent`→`Tool` nel grafo; struttura propria di B2. Raccomandazione: rinviare a B2.
- **DA-A1-05 — Rapporto con gravya-app e Beta.** **Chiusa da DX-01**: ripartenza da zero, gravya-app solo riferimento, la Beta non vincola A1.
- **DA-A1-06 — Isolamento.** Opzioni: istanza condivisa con `tenant_id` + RLS; istanza dedicata per tenant enterprise. Raccomandazione: condivisa, dedicata come opzione (soglia da validare).
- **DA-A1-07 — Retention di mandati scaduti/revocati e del loro audit. DA RIPORTARE ALL'UTENTE.** Opzioni: conservazione per la durata del contratto col tenant + periodo fisso; conservazione illimitata con pseudonimizzazione dell'attore; cancellazione a scadenza. Criterio: accountability (GDPR art. 5.2), tracciabilità (AI Act art. 12, NIS2) contro minimizzazione. Nessuna raccomandazione: la liceità dei tempi non è verificata.
- **DA-A1-08 — Base giuridica per i dati degli admin nell'audit. DA RIPORTARE ALL'UTENTE.** Proposta: legittimo interesse/accountability; da validare con l'analisi GDPR.

## Storico modifiche

| Versione | Data | Modifiche |
|---|---|---|
| 1.0 | 2026-11-03 | Rispetto a "Esempio A1 - completo.md": rimossi testi conversazionali e la tabella edge duplicata; rimosse le stime temporali (fasi ordinate, solo taglia S/M/L); DA rinumerate DA-A1-NN e ampliate (01 backend con PostgreSQL+RLS come opzione dal codice, invece di AGE non presente nel codice; 02 fonte di verità; 03 trasporto eventi; 04 allowlist; 05 rapporto con Beta; 06 isolamento); `Mandate` allineato a `permission_key`/`effect`/`valid_*`/`max_uses` delle tabelle reali; aggiunti `Agent.kind`, invarianti di delega, vocabolario chiuso `MONEY_WRITE`/`ALWAYS_HITL`, criteri 5-7; soglie marcate "proposta da validare"; tolti FastAPI/Pydantic e LangGraph per lo sweeper (non necessari); dipendenze da E1, A5, B2 rese esplicite; aggiunte appendici su stato reale, non verificato e decisioni. Motivo: allineamento allo stato verificato del codice e alle regole dell'utente. |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: esplicitata la dipendenza opzionale da E2 (`prompt_ref`); DA-A1-03 marcata come trasversale perché B1, B2, C1, C3 ed E2 rimandano allo stesso trasporto eventi. Motivo: dipendenze dichiarate in un solo verso e decisione duplicata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): gravya-app trattata come riferimento e non come codice da estendere; Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere; assunzioni su object storage, bus, audit e tenant riformulate; fase "Mappatura" sostituita da analisi del riferimento; DA-A1-05 chiusa da DX-01; DA-A1-02 riformulata; rischio Beta rimosso; taglia §12 ricalcolata per costruzione da zero. Applicate DX-02/PV-01/PV-02: nessun OpenTelemetry, eventi nel modello DB-native di E1; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); Neptune marcato come fuori perimetro e DA-A1-01 da riportare all'utente; nuove DA-A1-07 (retention) e DA-A1-08 (base giuridica). Motivo: decisioni dell'utente del 2026-11-03. |
