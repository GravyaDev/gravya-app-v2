# E2 — Prompt registry

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E2 |
| Nome | Prompt registry |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.2 |
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
- **E1** (tracing DB-native, PV-02): ogni render valorizza gli attributi `gravya.prompt.key`/`gravya.prompt.version`/`gravya.prompt.hash` sul record di traccia della chiamata LLM, nel modello dati definito da E1 (vocabolario allineato a E1 §4.1; nessun SDK o esportatore OpenTelemetry).
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
`{ text, prompt_key, version, content_hash }` — `content_hash` è dell'output renderizzato, per correlazione in audit senza testo. La lunghezza dell'hash (completo o troncato, come faceva gravya-app: Appendice A) si fissa con E1.

## 5. Interfacce

- **Libreria di risoluzione** (usata da B1): `resolve(key, tenant_id) → version` e `render(version, variables) → output`. Serve in ogni linguaggio dei servizi v2 che chiamano LLM; nell'ipotesi attuale TypeScript e Python (servizi Node e agenti Python, vedi DX-04). In gravya-app i prompt erano letti da entrambi i linguaggi (Appendice A): è la lezione che motiva il requisito, non un vincolo di compatibilità.
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
- Azione riservata a umani (attivazione e rollback; principio ripreso da HSAR/P16 di gravya-app, Appendice A, da confermare per v2 con DA-E2-04) → scrittura AI rifiutata.

## 7. Requisiti non funzionali

- **Performance:** `resolve`+`render` da cache p99 < 5 ms; propagazione di un rollback ai runtime ≤ 60 s (allineato alla cache di 60 s esistente; *proposta da validare*).
- **Sicurezza e conformità (PV-01):**
  - *Perimetro dati.* Registry interamente in PostgreSQL di Gravya; nessun servizio SaaS di prompt management, eval o tracing (PV-02). Hosting e regione del database non sono definiti qui (F1/infrastruttura): non verificato che siano UE.
  - *GDPR — minimizzazione.* Il registry conserva template e metadati, mai testi renderizzati con dati dei clienti (quelli restano in E1 con le regole di DA-E1-02). I template non devono contenere dati personali: controllo in validazione su pattern base (email, telefono) con blocco o avviso (*soglia/modalità da definire*). Dati personali trattati dal registry: solo l'identità di chi crea/attiva una versione (`created_by`, `actor`) e il testo libero `change_note`.
  - *GDPR — base giuridica, retention, diritti.* Per l'identità degli operatori la base ipotizzata è contratto/legittimo interesse (tracciabilità delle modifiche); non verificata. Le versioni sono immutabili per scelta di integrità: il conflitto con cancellazione/retention si risolve registrando un identificativo pseudonimo dell'attore anziché nome o email, così la versione resta e il dato personale si cancella nell'anagrafica. Durata di conservazione di versioni e attivazioni: **DA-E2-06, DA RIPORTARE ALL'UTENTE**. Diritti di accesso: export per attore dalle tabelle `prompt_versions`/`prompt_activations`.
  - *NIS2 (art. 21).* Controllo accessi e minimo privilegio (A3, RLS per tenant); gestione delle modifiche con traccia append-only (`prompt_activations`) e integrità verificabile (`content_hash`, immutabilità a livello DB); continuità tramite export/import e seed sempre ripristinabile; sicurezza nello sviluppo (gate di promozione, DA-E2-04). Notifica incidenti: una modifica non autorizzata di un prompt attivo è un evento di sicurezza che va inoltrato al processo incidenti (A5/F, non ancora definito); se sia "incidente significativo" ai fini della notifica non lo decide E2.
  - *AI Act.* Art. 50: gli avvisi di trasparenza verso l'utente finale (contenuto generato da AI, interazione con un sistema AI) non devono dipendere da un prompt modificabile; restano nel preambolo fisso nel codice, insieme al blocco anti-invenzione (DA-E2-03). Sorveglianza umana: attivazione e rollback solo da umani (DA-E2-04). Log: ogni versione e attivazione è registrata con attore e motivo; la classificazione di rischio dei casi d'uso Gravya non è verificata in v2 (le analisi in `gravya-app/docs/compliance` vanno riverificate).
  - *Isolamento e autorizzazione.* RLS per tenant; scritture solo con attore autorizzato da A3.
- **Portabilità:** template in formato testuale, export completo in file; nessuna dipendenza da servizi SaaS di prompt management.
- **Osservabilità AI:** ogni chiamata LLM è attribuibile a `prompt_key`+`version`+`content_hash` nel record di traccia DB-native di E1; la cronologia di attivazioni e rollback è interrogabile in SQL e correlabile alle tracce per sapere quale versione ha prodotto ogni output e quando è cambiata.

## 8. Criteri di accettazione

1. **Immutabilità:** test di integrazione che tenta UPDATE e DELETE su `prompt_versions` → entrambi falliscono a livello DB.
2. **Rollback:** test che attiva v2, esegue rollback, e verifica che `resolve` restituisca v1 entro 60 s (*soglia proposta da validare*) e che `prompt_activations` abbia 2 righe.
3. **Seed ripristinabile:** `rollback to_version=0` restituisce testo byte-identico al file seed del repo (confronto hash).
4. **Isolamento:** test con due tenant: il tenant A non legge né modifica versioni del tenant B (0 righe, `403/404`).
5. **Template fail-closed:** render con variabile mancante → errore; test unitario.
6. **Diff:** `GET diff` fra due versioni note restituisce l'unified diff atteso (snapshot test).
7. **Nessun prompt nel codice:** check in CI (grep/lint su pattern definiti in DA-E2-03) sui moduli migrati → 0 occorrenze (*elenco moduli da validare*).
8. **Tracciabilità:** in un test end-to-end, il 100% dei record di traccia delle chiamate LLM (modello E1) ha `gravya.prompt.key` e `gravya.prompt.version` (*soglia proposta da validare*).
9. **Portabilità:** export → import su DB vuoto → stesso insieme di `content_hash`.

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Decisioni DA-E2-01..04.
2. Schema e migrazioni PostgreSQL con trigger di immutabilità e RLS.
3. Renderer di template (DA-E2-02) e validazione variabili, in TS e Python con test di parità.
4. API di gestione, diff, rollback; CLI seed/export.
5. Cache con invalidazione su evento; integrazione attributi su E1.
6. Definizione dei seed v2 per i prompt nel perimetro (DA-E2-03), usando i testi di gravya-app solo come riferimento rivisto, e check CI.
7. Hook di promozione verso E3.

**Tecnologie (da master o da decidere):** PostgreSQL con RLS, Redis (cache, master §3; ospitato nel perimetro Gravya), TypeScript e Python, SHA-256. ORM/strumento di migrazione da fissare con F1 (gravya-app usava Drizzle: riferimento, non vincolo). Il motore di template **non** è nel master: DA-E2-02.

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
| Prompt dispersi nel codice (lezione di gravya-app: fallback e prompt hard-coded) | Alto: verità divisa | Un solo punto di risoluzione, nessun fallback hard-coded, check CI (§8.7); DA-E2-03 |
| Divergenza renderer TS/Python | Medio | Test di parità in CI; motore senza logica (DA-E2-02) |
| Cache stantia dopo rollback | Medio | Invalidazione su evento + TTL massimo |
| Prompt con PII nei trace o nei template | Alto (GDPR) | Hash al posto del testo nelle tracce (E1, DA-E1-02); controllo PII sui template (§7) |
| Rottura cache del prefisso prompt (#1781) | Medio: costo | Render deterministico; test di stabilità byte |

## 12. Stima e priorità

- **Dimensione:** M (costruzione da zero: schema e API semplici; complessità nella doppia libreria TS/Python con parità, nella scrittura dei seed v2 e nei controlli di conformità §7. Non dipendeva dal riuso: senza migrazione dello storico 0322 il lavoro si sposta sulla stesura dei seed).
- **Dipendenze critiche:** F1 (o schema minimo), A3 per le autorizzazioni, E1 per gli attributi.
- **Thin-slice MVP:** **Sì**, ondata 1. Il calendario della Beta di gravya-app (versioning post-Beta, #1801) non vincola più v2 (DX-01).

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è materiale di riferimento (PV-03): qui ciò che insegna, non ciò che si riusa. Nessun file, tabella o dato entra in v2 da qui.

**Soluzioni da riprendere come idea (lette nel codice):**
- `packages/db/src/schema/gravya_supervisor_prompt_revisions.ts` e migrazione `0322`: storico before/after con RLS ENABLE+FORCE per azienda. Idea: RLS forzata anche per il proprietario della tabella.
- `server/src/services/learning-proposal-apply.ts`: stale guard (`before_content` deve coincidere col prompt attuale) e revisione nella stessa transazione. Idea per l'attivazione atomica con controllo di concorrenza.
- `server/src/services/llm/prompt-hash.ts`: SHA-256 troncato a 16 caratteri, testo mai nell'audit. Idea per `content_hash` e per la minimizzazione.
- `services/agents/src/kloud/kloud_config.py` / `router.py`: blocco anti-invenzione non sovrascrivibile dal DB (P11). Idea: parte fissa nel codice per vincoli di sicurezza e trasparenza.
- `gravya-app-kloudify/docs/visione/README.md` P12 (prompt nel DB, seed nel repo, ripristino superadmin, prompt in inglese), P16 (`system_prompt` solo umani); `architettura-agenti.md` §2.8 (criteri di qualità versionati col prompt).
- `timeline-engine.ts` (2026-06-15): scelta di tracing DB-native, ora principio PV-02.

**Difetti da non ripetere:**
1. Prompt sparsi: fallback `_default_system_prompt()` in `kloud_config.py` e prompt hard-coded in italiano in `card_analyzer.py:113`.
2. Storico senza modello di versione: 0322 copre solo `system_prompt` dei supervisori, scritto solo dal ciclo di miglioramento, senza numero di versione, puntatore attivo, rollback né diff.
3. Prompt degli esecutori in un'altra tabella (`gravya_executors`), con lettura non verificata: più fonti di verità.
4. Cache con TTL 60 s senza invalidazione su evento.
5. Nessun motore di template e nessun ADR sui prompt in `gravya-app/docs/decisions`.

**Divergenze dal master plan (valide per v2):**
1. Master: prompt esterni al codice. Il preambolo fisso (anti-invenzione, trasparenza art. 50) resta intenzionalmente nel codice (DA-E2-03).
2. Master: templating senza motore indicato (DA-E2-02).
3. Criteri di qualità versionati insieme al prompt: non previsti dal master (DA-E2-04).
4. Attivazione solo umana: il master non pone vincoli sull'attore (DA-E2-04).
5. Master: OpenTelemetry per il tracing. In v2 tracing DB-native (PV-02).

## Appendice B — Non verificato

- Elenco completo dei prompt hard-coded in `services/agents` di gravya-app (solo `card_analyzer.py` letto): utile solo come inventario di riferimento per i seed v2.
- Lingua dei prompt v2 (P12 di gravya-app diceva inglese): da confermare.
- Stato attuale delle issue #1801, #1494, #1781 su GitHub (ora solo come riferimento).
- Regione di hosting di PostgreSQL e Redis per v2 (F1/infrastruttura).
- Classificazione AI Act dei casi d'uso v2 e applicabilità dell'art. 12 (log per sistemi ad alto rischio).
- Base giuridica per il trattamento delle identità degli operatori e durata di conservazione.
- Volumi (numero prompt, versioni, frequenza di render): nessun dato; le soglie §7-§8 sono proposte.

## Appendice C — Decisioni aperte

- **DA-E2-01 — Modello dati (riformulata, DX-01):** (a) tabelle generiche `prompts`/`prompt_versions`/`prompt_activations` come in §4.1; (b) colonne di prompt dentro le entità che li usano (supervisori, esecutori) con tabella di storico, come in gravya-app. Criterio: un'unica verità, immutabilità, rollback. Raccomandazione: (a). Non c'è più migrazione dello storico 0322 (DX-01).
- **DA-E2-02 — Motore di template:** (a) sostituzione semplice `{{var}}` senza logica, implementata in TS e Python; (b) motore con logica (es. Jinja-compatibile); (c) nessun template, solo concatenazione nel codice. Criterio: parità TS/Python, sicurezza, assenza di lock-in. Raccomandazione: (a).
- **DA-E2-03 — Perimetro del registry (riformulata, DX-01):** quali prompt v2 stanno nel registry. (a) tutti; (b) supervisori, esecutori e Kloud, con il preambolo fisso (anti-invenzione e avvisi di trasparenza art. 50) escluso e tenuto nel codice; (c) solo un sottoinsieme minimo per lo skeleton. Criterio: un'unica verità, conformità AI Act, master. Raccomandazione: (b). Non è più "quali migrare": i seed si scrivono per v2.
- **DA-E2-04 — Gate di promozione:** (a) solo umano; (b) E3 obbligatorio + approvazione umana (C3); (c) solo E3. Criterio: sorveglianza umana (PV-01, AI Act) e master §5. Raccomandazione: (b), con criteri di qualità versionati col prompt.
- **DA-E2-05 — Anticipo rispetto alla Beta:** **chiusa da DX-01**. v2 si costruisce da zero e la Beta di gravya-app non vincola: E2 è nell'ondata 1.
- **DA-E2-06 — Retention di versioni e attivazioni (nuova) — DA RIPORTARE ALL'UTENTE.** (a) conservazione illimitata (integrità e audit); (b) durata fissa per versioni mai attivate o superate; (c) conservazione illimitata dei template con attore pseudonimizzato e anagrafica cancellabile. Criterio: GDPR (limitazione della conservazione), NIS2 (tracciabilità delle modifiche), AI Act (log). Proposta tecnica: (c). La liceità della durata e la base giuridica non sono verificate: decide l'utente.
- **DA-E2-07 — Versioni proposte da AI (nuova) — DA RIPORTARE ALL'UTENTE.** Il ciclo di miglioramento (`source=learning_proposal`) può creare versioni candidate? (a) sì, mai attivabili senza umano; (b) no in ondata 1. Criterio: sorveglianza umana e rischio di deriva non controllata. Proposta: (a), ma è una scelta di prodotto e conformità.
- **DA-E2-08 — Testi dei seed (nuova) — DA RIPORTARE ALL'UTENTE.** I seed v2 si scrivono da zero o possono partire dai testi dei prompt di gravya-app rivisti? PV-03 ammette l'ingresso solo se un documento lo prevede. Criterio: qualità già validata contro ripartenza pulita. Proposta: partire dai testi di gravya-app come bozza, rivista e approvata come versione 0; nessuna decisione presa.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi di span allineati a E1 (`gravya.prompt.*`); C3 spostato da "È richiesto da" a "Dipende da" (verso invertito: è E2 a usare C3 per la promozione) e aggiunta la dipendenza condizionale da E3; aggiunti C1 e A1 in "È richiesto da"; corretta l'affermazione che il master citi Redis Stream/Kafka (non li cita) e rimando a DA-A1-03. Motivo: interfacce e dipendenze non allineate, affermazione non supportata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). Attributi `gravya.prompt.*` su record di traccia DB-native di E1 anziché span; §7 con voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50, osservabilità AI); rimossi riuso e migrazione da gravya-app (storico 0322, Drizzle, librerie esistenti) e il vincolo Beta; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti da non ripetere); DA-E2-01 e DA-E2-03 riformulate, DA-E2-05 chiusa da DX-01, nuove DA-E2-06..08 da riportare all'utente; rischio "doppio registry" sostituito; taglia M confermata per costruzione da zero. |
