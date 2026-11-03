# E2 — Prompt registry

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E2 |
| Nome | Prompt registry |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.1 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È lo store versionato dei prompt della piattaforma (master plan §3 "Prompt management": esterni al codice, versionati, con templating e rollback; §6 E2: "Store versionato di prompt con templating, diff e rollback"). Ogni prompt ha una chiave stabile, una sequenza immutabile di versioni, un puntatore alla versione attiva, un renderer di template e operazioni di diff e rollback.

**Cosa NON fa.**
- Non decide quale prompt usa un agente: il legame agente→prompt sta nel catalogo agenti (master 3.2.1, G4) e, come riferimento `prompt_ref`, nel nodo `Agent` di A1.
- Non valuta la qualità di una versione: lo fa E3 (offline) ed E4 (online). E2 espone solo l'hook di promozione.
- Non conserva i testi renderizzati con dati dei clienti: quelli sono tracing (E1), con i vincoli di §7.
- Non sceglie il modello LLM.

**Perché esiste.** Senza un registry, un cambio di prompt non è tracciabile, confrontabile né reversibile, e il gate di E3 ("a ogni PR che cambia prompt", master §5 Livello 1) non ha un oggetto da bloccare.

## 3. Contesto e dipendenze

**Dipende da:**
- **F1** (schema applicativo PostgreSQL con `tenant_id` e RLS): tabelle del registry. Ondata successiva; nell'ondata 1 si usa lo schema minimo di E2 (vedi DA-E2-01).
- **E1** (tracing): ogni render emette attributi `gravya.prompt.key`/`gravya.prompt.version`/`gravya.prompt.hash` sullo span LLM (nomi allineati a E1 §4.1).
- **E3** (eval offline): hook di promozione, se DA-E2-04 sceglie (b) o (c).
- **C3** (punto HITL): approvazione umana della promozione, solo se DA-E2-04 sceglie (b).
- **A3** (runtime enforcement): autorizza le scritture (crea versione, attiva, rollback).

**È richiesto da:** B1 (l'agent runtime risolve il prompt da E2), C1 (`prompt_ref` dei nodi `agent`), A1 (`prompt_ref` opzionale del nodo `Agent`), E3 (registra le versioni dei prompt nel report), E4, G4 (registro agenti, mostra versione).

**Assunzioni (non verificate per v2):**
- Lo store è PostgreSQL (master §3). Nessun database dedicato ai prompt.
- Esiste un'identità di attore (umano/superadmin/agente) fornita da A3.

## 4. Contratti

### 4.1 Schema dati (proposta)

| Tabella | Campi minimi |
|---|---|
| `prompts` | `id`, `key` (es. `supervisor.commercial.system`), `tenant_id` NULL = globale/seed, `active_version_id`, `created_at` |
| `prompt_versions` | `id`, `prompt_id`, `version` (intero monotono per prompt), `template` (testo), `variables_schema` (JSON Schema), `content_hash` (SHA-256), `parent_version_id`, `source` (`seed`/`human`/`learning_proposal`/`rollback`), `created_by`, `created_at`, `change_note` |
| `prompt_activations` | `id`, `prompt_id`, `from_version_id`, `to_version_id`, `reason` (`promote`/`rollback`), `actor`, `created_at` (append-only) |

Regole: `prompt_versions` è **immutabile** (nessun UPDATE/DELETE, come trigger DB); la versione 0 di ogni prompt globale è il seed del repo; RLS su `tenant_id` con riga globale visibile in lettura.

### 4.2 Eventi emessi
- `prompt.version.created`, `prompt.version.activated`, `prompt.version.rolled_back` — payload: `prompt_key`, `tenant_id`, `from_version`, `to_version`, `actor`. Bus: decisione trasversale DA-A1-03 (opzioni Redis Stream, Redis pub/sub, `pg_listener`/NOTIFY). Correzione di revisione: il master plan non cita né Redis Stream né Kafka.

### 4.3 Output del render
`{ text, prompt_key, version, content_hash }` — `content_hash` è dell'output renderizzato, troncato come nel codice esistente (vedi Appendice A) per correlazione in audit senza testo.

## 5. Interfacce

- **Libreria di risoluzione** (usata da B1): `resolve(key, tenant_id) → version` e `render(version, variables) → output`. Deve esistere sia in TypeScript sia in Python, perché il codice esistente legge i prompt da entrambi (Appendice A).
- **API di gestione:**
  - `GET /v1/prompts/{key}/versions` — elenco.
  - `POST /v1/prompts/{key}/versions` — crea versione (non la attiva).
  - `GET /v1/prompts/{key}/diff?from=N&to=M` — diff testuale unificato.
  - `POST /v1/prompts/{key}/activate` `{version}` — promozione.
  - `POST /v1/prompts/{key}/rollback` `{to_version?}` — default: versione attiva precedente; `to_version=0` = seed.
- **CLI di seed/export**: carica i seed dal repo come versione 0 ed esporta il registry in file (portabilità, nessun lock-in).

## 6. Comportamento

**Flusso principale (nuova versione).**
1. Un attore autorizzato (A3) crea una versione; il sistema valida il template (variabili dichiarate = variabili usate) e calcola `content_hash`.
2. Se l'hash coincide con una versione esistente, risponde con quella (idempotenza).
3. La promozione esegue l'hook E3 (se DA-E2-04 lo richiede) e, a esito positivo, aggiorna `active_version_id` e scrive `prompt_activations` in una sola transazione.
4. Emette l'evento; le cache dei runtime si invalidano.

**Rollback.** Sposta il puntatore a una versione esistente; non crea né cancella versioni. Il seed (v0) è sempre ripristinabile.

**Casi limite.**
- Variabile mancante al render → errore esplicito, nessun render parziale (fail-closed).
- Prompt di tenant assente → si usa il globale; se manca anche quello → errore, nessun fallback hard-coded.
- Promozione concorrente → lock sulla riga `prompts`; il secondo riceve `409`.
- Versione referenziata da un'attivazione o da un trace → mai cancellabile.
- Colonna/azione riservata a umani (regola HSAR esistente) → scrittura AI rifiutata (Appendice A).

## 7. Requisiti non funzionali

- **Performance:** `resolve`+`render` da cache p99 < 5 ms; propagazione di un rollback ai runtime ≤ 60 s (allineato alla cache di 60 s esistente; *proposta da validare*).
- **Sicurezza:** isolamento per tenant con RLS; scritture solo con attore autorizzato; i testi renderizzati con dati cliente non sono salvati dal registry.
- **Portabilità:** template in formato testuale, export completo in file; nessuna dipendenza da servizi SaaS di prompt management.
- **Osservabilità:** ogni chiamata LLM è attribuibile a `prompt_key`+`version` (via E1).

## 8. Criteri di accettazione

1. **Immutabilità:** test di integrazione che tenta UPDATE e DELETE su `prompt_versions` → entrambi falliscono a livello DB.
2. **Rollback:** test che attiva v2, esegue rollback, e verifica che `resolve` restituisca v1 entro 60 s (*soglia proposta da validare*) e che `prompt_activations` abbia 2 righe.
3. **Seed ripristinabile:** `rollback to_version=0` restituisce testo byte-identico al file seed del repo (confronto hash).
4. **Isolamento:** test con due tenant: il tenant A non legge né modifica versioni del tenant B (0 righe, `403/404`).
5. **Template fail-closed:** render con variabile mancante → errore; test unitario.
6. **Diff:** `GET diff` fra due versioni note restituisce l'unified diff atteso (snapshot test).
7. **Nessun prompt nel codice:** check in CI (grep/lint su pattern definiti in DA-E2-03) sui moduli migrati → 0 occorrenze (*elenco moduli da validare*).
8. **Tracciabilità:** in un test end-to-end, il 100% degli span LLM ha `gravya.prompt.key` e `gravya.prompt.version` (*soglia proposta da validare*).
9. **Portabilità:** export → import su DB vuoto → stesso insieme di `content_hash`.

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Decisioni DA-E2-01..04.
2. Schema e migrazioni PostgreSQL con trigger di immutabilità e RLS.
3. Renderer di template (DA-E2-02) e validazione variabili, in TS e Python con test di parità.
4. API di gestione, diff, rollback; CLI seed/export.
5. Cache con invalidazione su evento; integrazione attributi su E1.
6. Migrazione dei prompt esistenti (DA-E2-03) e check CI.
7. Hook di promozione verso E3.

**Tecnologie (da master o codice):** PostgreSQL con RLS, Redis (cache, master §3), TypeScript (Drizzle per lo schema, come in `packages/db`) e Python (servizio agenti), SHA-256 come in `prompt-hash.ts`. Il motore di template **non** è nel master: DA-E2-02.

**Rischi:** vedi §11.

## 10. Test e valutazione

- **Unit:** render, validazione variabili, hash, diff.
- **Integration (PostgreSQL reale):** immutabilità, RLS, rollback, concorrenza.
- **Parità TS/Python:** stesso template + variabili → stesso output byte-per-byte su un set di casi.
- **Eval:** la promozione richiama E3 sulla versione candidata; nessuna eval è implementata in E2.
- **Security:** tentativo di scrittura con attore non autorizzato; template injection (variabile contenente sintassi di template non deve essere rivalutata).

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Doppio registry (tabelle esistenti + E2) | Alto: verità divisa | DA-E2-03; un solo punto di risoluzione |
| Divergenza renderer TS/Python | Medio | Test di parità in CI; motore senza logica (DA-E2-02) |
| Cache stantia dopo rollback | Medio | Invalidazione su evento + TTL massimo |
| Prompt con PII nei trace | Alto (GDPR) | Hash al posto del testo, coerente con il codice esistente |
| Rottura cache del prefisso prompt (#1781) | Medio: costo | Render deterministico; test di stabilità byte |

## 12. Stima e priorità

- **Dimensione:** M (schema e API semplici; complessità nella migrazione dei prompt esistenti e nella doppia libreria).
- **Dipendenze critiche:** F1 (o schema minimo), A3 per le autorizzazioni, E1 per gli attributi.
- **Thin-slice MVP:** **Sì**, ondata 1. Nota: nel piano registrato il versioning dei prompt è **post-Beta** (Appendice A).

---

## Appendice A — Allineamento con lo stato attuale

**Esiste (letto):**
- `packages/db/src/schema/gravya_supervisor_prompt_revisions.ts` e `packages/db/src/migrations/0322_gravya_supervisor_prompt_revisions.sql`: storico before/after del solo `gravya_supervisors.system_prompt`, scritto **solo** dal ciclo di miglioramento (`source` CHECK = `learning_proposal`, `field` CHECK = `system_prompt`), RLS ENABLE+FORCE, per azienda. Non ha numero di versione, puntatore attivo, rollback né diff. Riusabile come modello RLS e come fonte da migrare.
- `server/src/services/learning-proposal-apply.ts`: saga di applicazione con stale guard (`before_content` deve coincidere col prompt attuale) e revisione nella stessa transazione. Pattern riusabile per l'attivazione.
- `server/src/services/llm/prompt-hash.ts`: SHA-256 troncato a 16 caratteri, il prompt completo mai nell'audit. Riusabile per `content_hash` del render.
- `services/agents/src/kloud/kloud_config.py` / `router.py`: prompt di Kloud letto dal DB con TTL 60 s, con fallback `_default_system_prompt()` nel codice, e un blocco anti-invenzione che il DB non può sovrascrivere (principio P11).
- `services/agents/src/kloud/card_analyzer.py:113`: prompt **hard-coded nel codice, in italiano**.
- `gravya-app-kloudify/docs/visione/README.md` P12 (prompt nel DB, seed nel repo, ripristino superadmin, prompt in inglese), P16 (`system_prompt` colonna HSAR, solo umani); `docs/visione/architettura-agenti.md` §2.8 e righe 183-189 (versioni = punto 5 epic #1801, post-Beta; criteri qualità A2 versionati insieme al prompt; prompt degli esecutori in `gravya_executors`).
- Nessun ADR sui prompt in `gravya-app/docs/decisions`.

**Divergenze dal master plan:**
1. Master: prompt esterni al codice. Codice: fallback e prompt hard-coded (`kloud_config.py`, `card_analyzer.py`); P11 impone un preambolo fisso **nel codice**, intenzionalmente non esternalizzabile.
2. Master: versioning con rollback in walking skeleton. Piano registrato: versioning **post-Beta** (#1801).
3. Master: templating. Nessun motore di template per prompt individuato.
4. Visione A2: criteri di qualità versionati **insieme** al prompt; il master non lo prevede in E2 (DA-E2-04).
5. HSAR: `system_prompt` scrivibile solo da umani; il master non pone vincoli sull'attore.

## Appendice B — Non verificato

- Elenco completo dei prompt hard-coded in `services/agents` (solo `card_analyzer.py` letto).
- Schema e modalità di lettura di `gravya_executors` (prompt degli esecutori) e se abbiano cache 60 s.
- Stato attuale delle issue #1801, #1494, #1781 su GitHub.
- Quali prompt e dati migrano da gravya-app a v2 (non documentato nel repo di stato).
- Se `promptHash` sia già propagato sugli span di tracing (oggi è in audit `llm.inference`, secondo il commento del file).
- Volumi (numero prompt, versioni, frequenza di render): nessun dato; le soglie §7-§8 sono proposte.

## Appendice C — Decisioni aperte

- **DA-E2-01 — Modello dati:** (a) nuove tabelle generiche `prompts`/`prompt_versions`; (b) estendere `gravya_supervisor_prompt_revisions` e colonne esistenti; (c) ibrido con viste. Criterio: un'unica verità e costo di migrazione. Raccomandazione: (a), migrando 0322 come storico.
- **DA-E2-02 — Motore di template:** (a) sostituzione semplice `{{var}}` senza logica, implementata in TS e Python; (b) motore con logica (es. Jinja-compatibile); (c) nessun template, solo concatenazione nel codice. Criterio: parità TS/Python, sicurezza, assenza di lock-in. Raccomandazione: (a).
- **DA-E2-03 — Perimetro della migrazione:** (a) tutti i prompt; (b) solo supervisori/esecutori/Kloud, preambolo P11 escluso esplicitamente; (c) solo i nuovi in v2. Criterio: rispetto di P11 e del master. Raccomandazione: (b).
- **DA-E2-04 — Gate di promozione:** (a) solo umano (HSAR); (b) E3 obbligatorio + approvazione umana (C3); (c) solo E3. Criterio: P16 e master §5. Raccomandazione: (b), con criteri di qualità versionati col prompt.
- **DA-E2-05 — Anticipo rispetto alla Beta:** (a) E2 in v2 ora; (b) attendere post-Beta come da #1801. Decide l'utente (Daniele). Nessuna raccomandazione tecnica.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi di span allineati a E1 (`gravya.prompt.*`); C3 spostato da "È richiesto da" a "Dipende da" (verso invertito: è E2 a usare C3 per la promozione) e aggiunta la dipendenza condizionale da E3; aggiunti C1 e A1 in "È richiesto da"; corretta l'affermazione che il master citi Redis Stream/Kafka (non li cita) e rimando a DA-A1-03. Motivo: interfacce e dipendenze non allineate, affermazione non supportata. |
