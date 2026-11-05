> **Nota di allineamento (v1.1, 2026-11-03).** Documento sorgente dell'utente. Le decisioni prese durante la pianificazione prevalgono sul testo originale (ordine: `docs/PRINCIPI.md`, `docs/DECISIONS.md`, documenti di dettaglio, questo file). Dove il testo è superato, una nota **[→ …]** rimanda alla decisione, senza ripeterne il contenuto: la fonte resta `DECISIONS.md`. **Questo file è un modello di forma, non di contenuto.** Il documento A1 in uso è `docs/A1-grafo-mandati.md`. Non imitare: le stime in settimane (§9; solo taglie S/M/L), i valori fissi come 5 s, 5 minuti, 100 ms (DX-22: vanno resi variabili), Neo4j come scelta (DA-A1-01), il bus Kafka non previsto, le decisioni aperte senza ID `DA-{ID}-NN`.

# A1 — Modello del grafo dei mandati

## 1. Identità

| Campo | Valore |
|---|---|
| ID | A1 |
| Nome | Modello del grafo dei mandati |
| Componente padre | A — Control Plane (governance) |
| Versione documento | 1.0 |
| Data | 2026-11-03 |

## 2. Scopo

**Cosa fa.** Definisce lo schema del grafo canonico che rappresenta *chi* è un agente, *quali mandati* ha, *su quali domini* opera, *quali artefatti* produce e *quali deleghe* esistono tra agenti. È la "mappa" del sistema: il punto di verità per la governance, non il magazzino dei dati.

**Cosa NON fa.**
- Non contiene payload grandi (brief, creatività, PDF, transcript). Contiene solo nodi-àncora con URI e hash verso l'object storage.
- Non è interrogato sul percorso caldo delle richieste. Il runtime A3 usa policy compilate da A2; il grafo serve A2 in batch.
- Non è un database applicativo. Non sostituisce PostgreSQL per CRM, campagne, report.

**Perché esiste.** Senza un grafo esplicito, i mandati degli agenti vivrebbero impliciti nel codice o in tabelle sparse, e la governance diventerebbe un insieme di controlli ad hoc non verificabili. Il grafo rende la topologia degli agenti un artefatto ispezionabile, versionabile e compilabile in policy.

## 3. Contesto e dipendenze

**Dipende da:** nessun sottoprodotto (è la base del Control Plane).

**È richiesto da:** A2 (compilatore policy), A3 (runtime di enforcement, che ne consuma le policy compilate, non il grafo), A4 (validatore round-trip), A5 (audit trail dei mandati).

**Assunzioni:**
- Esiste un object storage (S3/Garage) per gli artefatti referenziati.
- Esiste un bus di eventi (Redis Stream o Kafka) per notificare le mutazioni.
- Il team ha accesso a un graph database scelto secondo DA1 (vedi §9).

## 4. Contratti

### 4.1 Schema dei nodi

| Nodo | Proprietà minime | Proprietà opzionali |
|---|---|---|
| `Tenant` | `id`, `name`, `isolation_level` (`shared`/`dedicated`) | `region`, `created_at` |
| `Agent` | `id`, `name`, `version`, `status` (`draft`/`active`/`retired`) | `owner_tenant_id`, `model_ref`, `prompt_ref` |
| `Mandate` | `id`, `scope` (stringa strutturata), `constraints` (JSON), `expires_at` | `created_by`, `approved_by` |
| `Domain` | `id`, `name`, `tenant_id` | `parent_domain_id` |
| `Artifact` | `id`, `uri`, `content_hash`, `mime`, `size_bytes`, `owner_tenant_id` | `retention_class`, `unresolved` (bool) |
| `Delegation` | `id`, `scope`, `expires_at` | `constraints` |

### 4.2 Schema degli edge

| Edge | Da → A | Semantica |
|---|---|---|
| `HAS_MANDATE` | `Agent` → `Mandate` | L'agente possiede quel mandato |
| `OPERATES_IN` | `Mandate` → `Domain` | Il mandato è valido in quel dominio |
| `PRODUCES` | `Agent` → `Artifact` | L'agente ha prodotto quell'artefatto |
| `DELEGATES_TO` | `Agent` → `Delegation` | L'agente delega parte del suo scope |
| `DELEGATION_TARGET` | `Delegation` → `Agent` | L'agente a cui è delegato lo scope |
| `CONSUMES` | `Agent` → `Artifact` | L'artefatto è usato come input dall'agente |
| `BELONGS_TO` | `Agent`, `Domain`, `Artifact` → `Tenant` | Isolamento multi-tenant a livello di nodo |

**Proprietà comuni agli edge:** `created_at` (timestamp), `valid_from`, `valid_until` (per gestire la validità temporale della delega o dell'operazione), `metadata` (JSON per estensioni future).

---

## 5. Interfacce

**API di scrittura (Control Plane):**
- `POST /v1/graph/agents` — Crea o aggiorna un nodo `Agent`.
- `POST /v1/graph/mandates` — Crea un mandato e lo collega a un agente e a un dominio.
- `POST /v1/graph/delegations` — Crea una delega tra due agenti.
- `DELETE /v1/graph/nodes/{id}` — Soft-delete di un nodo (marca `status='retired'`, non cancella la storia).

**API di lettura (batch per A2):**
- `GET /v1/graph/mandates?tenant_id={id}&status=active` — Restituisce tutti i mandati attivi per un tenant, in formato JSON compilabile.
- `GET /v1/graph/agents/{id}/topology` — Restituisce l'albero delle deleghe per un agente.

**Eventi emessi:**
- `graph.mandate.created`, `graph.mandate.updated`, `graph.mandate.expired` — pubblicati su un bus eventi (Redis Stream o Kafka) per notificare A2 e A3.

---

## 6. Comportamento

**Flusso principale (creazione di un mandato):**
1. L'admin (o un agente superadmin) invia una richiesta `POST /v1/graph/mandates`.
2. Il sistema valida che `tenant_id` esista, che `domain_id` appartenga allo stesso tenant, e che l'agente non abbia già un mandato attivo identico (idempotenza).
3. Crea il nodo `Mandate` e l'edge `HAS_MANDATE` in una transazione atomica.
4. Emette l'evento `graph.mandate.created`.
5. A2 (compilatore policy) riceve l'evento e aggiorna le regole compilate in meno di 5 secondi.

**Casi limite e gestione errori:**
- **Mandato scaduto:** un job schedulato (`mandate-ttl-sweeper`) gira ogni 5 minuti, marca i mandati con `expires_at < now()` come `status='expired'` ed emette l'evento corrispondente.
- **Conflitto di dominio:** se un agente tenta di operare su un dominio non assegnato, il controllo avviene in A3, ma A1 rifiuta la creazione del mandato se il dominio non esiste o è di un altro tenant.
- **Agente dismesso:** se un agente viene marcato `retired`, tutti i suoi mandati vengono invalidati automaticamente (`valid_until = now()`) e le deleghe revocate.
- **Errore di transazione:** se la creazione del nodo riesce ma l'edge fallisce, l'intera transazione viene annullata (rollback) e l'API risponde con `409 Conflict` e un messaggio d'errore strutturato.

---

## 7. Requisiti non funzionali

- **Performance:** le letture batch per A2 devono rispondere in < 100ms per tenant con meno di 1.000 mandati. Le scritture devono completarsi in < 50ms.
- **Sicurezza:** ogni query deve filtrare obbligatoriamente per `tenant_id` a livello di database (non solo a livello applicativo). L'accesso al grafo è limitato al Control Plane, non esposto direttamente agli agenti.
- **Osservabilità:** ogni mutazione del grafo (creazione, modifica, cancellazione) deve generare un evento di audit (chi, cosa, quando, valore precedente e nuovo) scritto su un log append-only (A5).
- **Scalabilità:** il grafo deve supportare fino a 10.000 nodi `Agent` e 100.000 `Artifact` per tenant senza degradamento delle performance di lettura.

---

## 8. Criteri di accettazione

1. **Test di integrità:** nessun edge può esistere senza i nodi corrispondenti (testabile via query di validazione periodica).
2. **Test di isolamento:** un'API con `tenant_id=A` non deve mai restituire nodi di `tenant_id=B` (testabile con un test di integrazione che crea due tenant e verifica l'assenza di leakage).
3. **Test di idempotenza:** due richieste identiche per lo stesso mandato producono un solo nodo e un solo edge (testabile con due POST consecutivi e un conteggio sul DB).
4. **Test di scadenza:** un mandato con `expires_at` nel passato non deve essere restituito dalle query di lettura per A2 (testabile manipolando la data nel DB).
5. **Test di audit:** ogni mutazione produce una riga nel log di audit con i campi obbligatori (testabile con un mock del logger e un'asserzione sul numero di righe).

---

## 9. Piano di implementazione

**Fasi:**
1. **Scelta del database** (Decisione Aperta DA1): Neo4j (nativo, ottimo per query di traversal), Amazon Neptune (gestito, se si è su AWS), o PostgreSQL con l'estensione Apache AGE (se si vuole ridurre il numero di tecnologie). **Raccomandazione:** Neo4j per la maturità dell'ecosistema, con un'istanza dedicata per tenant (o un'istanza condivisa con partizionamento logico).
2. **Definizione schema** (settimana 1): creare i constraint di unicità sui nodi `Agent.id`, `Mandate.id`, `Tenant.id`, e gli indici sulle proprietà `tenant_id`, `status`, `expires_at`.
3. **API REST** (settimana 1–2): implementare gli endpoint di scrittura e lettura, con validazione Zod/Pydantic.
4. **Event bus** (settimana 2): integrare Redis Stream per l'emissione degli eventi.
5. **TTL sweeper** (settimana 2): job schedulato con cron o con LangGraph (se si vuole usare lo stesso orchestratore).
6. **Test e hardening** (settimana 3): scrivere i test di integrazione, i test di isolamento multi-tenant, e i test di performance.

**Tecnologie dal master plan:** Neo4j (o alternativa DA1), Redis Stream, API REST con Express (Node.js) o FastAPI (Python), validazione Zod/Pydantic.

---

## 10. Test e valutazione

- **Unit test:** validazione degli schemi (Zod/Pydantic), idempotenza dell'API, gestione degli errori (400, 404, 409).
- **Integration test:** creazione di due tenant con agenti e mandati, verifica che le query restituiscano solo i dati del tenant corretto; verifica che il TTL sweeper rimuova i mandati scaduti.
- **Performance test:** eseguire 1.000 query di lettura batch su un tenant con 1.000 mandati e misurare il p99 (deve essere < 100ms).
- **Security test:** tentare di accedere a un nodo di un altro tenant via API con un token manipolato (deve fallire con 403 o 404).

---

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| **Il grafo diventa un collo di bottiglia** | Alto: A2 non riesce a compilare in tempo | Letture batch con cache (Redis) e compilazione asincrona; A3 usa regole compilate, non il grafo |
| **Deriva dello schema** | Medio: i documenti non corrispondono al codice | Versionamento dello schema (`schema_version` in ogni nodo) e migrazioni gestite |
| **Perdita di dati in caso di failure** | Alto: mandati orfani o inconsistenza | Transazioni ACID (Neo4j supporta transazioni); backup giornaliero del grafo |
| **Isolamento multi-tenant imperfetto** | Critico: leakage di dati tra tenant | Test di isolamento obbligatori in CI; review di sicurezza su ogni query che tocca il grafo |

---

## 12. Stima e priorità

- **Dimensione:** L (Large) — è la base del Control Plane, richiede scelte architetturali (DA1) e integrazione con A2, A3, A5.
- **Dipendenze critiche:** nessuna (è il primo componente), ma è richiesto da A2, A3, A4, A5.
- **Thin-slice MVP:** **Sì.** Senza A1, non esiste governance. È parte dell'ondata 1 (walking skeleton).

---

**Decisioni aperte da registrare in `DECISIONS.md`:**
- **DA1:** Scelta del graph database (Neo4j vs Neptune vs PostgreSQL+AGE). Data: 2026-11-03. Opzioni: [Neo4j, Neptune, AGE]. Criterio: maturità, costo, integrazione con lo stack esistente. Raccomandazione: Neo4j.
- **DA2:** Strategia di isolamento (istanza per tenant vs istanza condivisa con `tenant_id`). Criterio: costo vs sicurezza. Raccomandazione: istanza condivisa per tenant < 50, istanza dedicata per tenant enterprise.

---
*Fine documento A1. Pronto per essere salvato come `A1-grafo-mandati.md`.*

---

## Storico modifiche

| Versione | Data | Cosa è cambiato e perché |
|---|---|---|
| 1.0 | 2026-11-03 | Versione originale caricata dall'utente. |
| 1.1 | 2026-11-03 | Rimossi i residui di chat (frase di ripresa, offerta finale) e le righe duplicate della tabella degli edge §4.2; aggiunta la nota su cosa non imitare. |
