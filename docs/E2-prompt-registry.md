# E2 — Prompt registry

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E2 |
| Nome | Prompt registry |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.3 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È lo store versionato dei prompt della piattaforma (master plan §3 "Prompt management": esterni al codice, versionati, con templating e rollback; §6 E2: "Store versionato di prompt con templating, diff e rollback"). Ogni prompt ha una chiave stabile, una sequenza immutabile di versioni, un puntatore alla versione attiva, un renderer di template e operazioni di diff e rollback.

**Cosa NON fa.**
- Non decide quale prompt usa un agente: il legame agente→prompt sta nel catalogo agenti (master 3.2.1, G4) e, come riferimento `prompt_ref`, nel nodo `Agent` di A1.
- Non valuta la qualità di una versione: lo fa E3 (offline) ed E4 (online). E2 espone solo l'hook di promozione.
- Non conserva i testi renderizzati con dati dei clienti, né li fa entrare nelle tracce: in produzione i contenuti non si catturano (DA-E1-02, decisa).
- Non sceglie il modello LLM.

**Perché esiste.** Senza un registry, un cambio di prompt non è tracciabile, confrontabile né reversibile, e il gate di E3 ("a ogni PR che cambia prompt", master §5 Livello 1) non ha un oggetto da bloccare.

## 3. Contesto e dipendenze

**Dipende da:**
- **F1** (schema applicativo PostgreSQL con `tenant_id` e RLS, backend confermato da DA-A1-01): tabelle del registry. Ondata successiva; nell'ondata 1 si usa lo schema minimo di E2 (vedi DA-E2-01).
- **E1** (tracing DB-native, PV-02): ogni render valorizza gli attributi `gravya.prompt.key`/`gravya.prompt.version`/`gravya.prompt.hash` sul record di traccia della chiamata LLM, nel modello dati definito da E1 (vocabolario allineato a E1 §4.1). Per DA-E1-05 (decisa) E1 può adottare i nomi delle GenAI semantic conventions e il formato traceparent come vocabolario, senza SDK né export OpenTelemetry: se E1 rinomina gli attributi della chiamata LLM, E2 si allinea; i nomi `gravya.prompt.*` restano finché E1 non fissa un equivalente.
- **E3** (eval offline): hook di promozione, se DA-E2-04 sceglie (b) o (c).
- **C3** (punto HITL): approvazione umana della promozione, solo se DA-E2-04 sceglie (b).
- **A3** (runtime enforcement): autorizza le scritture (crea versione, attiva, rollback). Fail-closed (DA-A3-07, decisa): se il record di decisione di A3 non si salva, la scrittura è bloccata.
- **A5** (audit trail, ondata 2): riceve i segnali di sicurezza di E2 ed è responsabile della notifica incidenti NIS2 (DX-10).

**È richiesto da:** B1 (l'agent runtime risolve il prompt da E2), C1 (`prompt_ref` dei nodi `agent`), A1 (`prompt_ref` opzionale del nodo `Agent`), E3 (registra le versioni dei prompt nel report), E4, G4 (registro agenti, mostra versione).

**Fatti decisi:** lo store è PostgreSQL con RLS (DA-A1-01), nessun database dedicato ai prompt; infrastruttura self-hosted nell'UE (DA-B1-06).

**Assunzioni (non verificate per v2):**
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

**Fail-closed sulle scritture (DA-A3-07, DA-B2-04, decise).** Creazione, attivazione e rollback avvengono solo se la decisione di A3 e la riga di `prompt_activations` (per attivazione e rollback) sono salvate; se un record non si salva, l'operazione è annullata e il puntatore attivo non cambia.

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
  - *Perimetro dati.* Registry interamente in PostgreSQL di Gravya, self-hosted su infrastruttura UE (DA-B1-06); nessun servizio SaaS di prompt management, eval o tracing (PV-02, DA-E3-09, DA-C1-05).
  - *Ruolo GDPR (DX-11).* Gravya tratta i dati come responsabile del trattamento (art. 28 GDPR) per conto delle agenzie.
  - *GDPR — minimizzazione.* Il registry conserva template e metadati, mai testi renderizzati con dati dei clienti (che in produzione non vengono catturati nemmeno da E1: DA-E1-02). I template non devono contenere dati personali: controllo in validazione su pattern base (email, telefono) con blocco o avviso (*soglia/modalità da definire*). Dati personali trattati dal registry: solo l'identità di chi crea/attiva una versione (`created_by`, `actor`) e il testo libero `change_note`.
  - *GDPR — base giuridica, retention, diritti.* Base giuridica per l'identità degli operatori: aperta, da confermare nella politica DX-09 (come DA-A1-08 per A1). Retention: si applica la politica unica DX-09 (durate non ancora fissate; override per classe e tenant previsti ma non attivi); E2 non definisce durate proprie. Classi di dati prodotte da E2: (1) versioni dei prompt (`prompt_versions`: template, schema variabili, hash, `change_note`, attore); (2) attivazioni e rollback (`prompt_activations`, append-only); (3) puntatori attivi (`prompts`); (4) eventi `prompt.version.*`; (5) segnali di sicurezza inviati ad A5. Le versioni sono immutabili per integrità: per conciliare immutabilità e cancellazione si registra un identificativo pseudonimo dell'attore anziché nome o email (proposta tecnica, da verificare con la politica DX-09). Diritti di accesso: export per attore da `prompt_versions`/`prompt_activations`.
  - *NIS2 (art. 21).* Controllo accessi e minimo privilegio (A3, RLS per tenant); gestione delle modifiche con traccia append-only (`prompt_activations`) e integrità verificabile (`content_hash`, immutabilità a livello DB); continuità tramite export/import e seed sempre ripristinabile; sicurezza nello sviluppo (gate di promozione, DA-E2-04). Notifica incidenti (DX-10): la responsabilità è di A5 (ondata 2). E2 invia ad A5 un segnale per ogni tentativo di scrittura non autorizzato e per ogni modifica di prompt attivo fuori dal flusso previsto; la qualificazione come incidente significativo e la notifica spettano ad A5.
  - *AI Act (DX-11: casi d'uso non ad alto rischio).* Art. 50 (obbligatorio): gli avvisi di trasparenza verso l'utente finale non devono dipendere da un prompt modificabile; restano nel preambolo fisso nel codice, insieme al blocco anti-invenzione (DA-E2-03). Buona pratica, non obbligo (artt. 12 e 14 non applicabili): attivazione e rollback solo da umani (DA-E2-04) e registrazione di ogni versione e attivazione con attore e motivo.
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
10. **Fail-closed:** test di integrazione che simula il fallimento del salvataggio del record di decisione A3 o della riga `prompt_activations` → attivazione/rollback rifiutati, `active_version_id` invariato, nessuna versione creata.
11. **Segnale ad A5:** un tentativo di scrittura non autorizzato produce un segnale verso A5 (o verso il suo stub finché A5 non esiste).

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Decisioni DA-E2-01..04.
2. Schema e migrazioni PostgreSQL (DA-A1-01) con trigger di immutabilità e RLS.
3. Renderer di template (DA-E2-02) e validazione variabili, in TS e Python con test di parità.
4. API di gestione, diff, rollback; CLI seed/export.
5. Cache con invalidazione su evento; integrazione attributi su E1 (vocabolario DA-E1-05); invio segnali ad A5 (DX-10).
6. Definizione dei seed v2 per i prompt nel perimetro (DA-E2-03), usando i testi di gravya-app solo come riferimento rivisto, e check CI.
7. Hook di promozione verso E3 (casi solo sintetici, giudice solo UE: DA-E3-08, DA-E3-09).

**Tecnologie (da master o da decidere):** PostgreSQL con RLS (deciso, DA-A1-01), Redis (cache, master §3; self-hosted UE, DA-B1-06), TypeScript e Python, SHA-256. ORM/strumento di migrazione da fissare con F1 (gravya-app usava Drizzle: riferimento, non vincolo). Il motore di template **non** è nel master: DA-E2-02.

**Rischi:** vedi §11.

## 10. Test e valutazione

- **Unit:** render, validazione variabili, hash, diff.
- **Integration (PostgreSQL reale):** immutabilità, RLS, rollback, concorrenza.
- **Parità TS/Python:** stesso template + variabili → stesso output byte-per-byte su un set di casi.
- **Eval:** la promozione richiama E3 sulla versione candidata; nessuna eval è implementata in E2.
- **Security:** tentativo di scrittura con attore non autorizzato (con verifica del segnale ad A5); fail-closed con salvataggio del record A3 o dell'attivazione forzato a fallire; template injection (variabile contenente sintassi di template non deve essere rivalutata).

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Prompt dispersi nel codice (lezione di gravya-app: fallback e prompt hard-coded) | Alto: verità divisa | Un solo punto di risoluzione, nessun fallback hard-coded, check CI (§8.7); DA-E2-03 |
| Divergenza renderer TS/Python | Medio | Test di parità in CI; motore senza logica (DA-E2-02) |
| Cache stantia dopo rollback | Medio | Invalidazione su evento + TTL massimo |
| Prompt con PII nei trace o nei template | Alto (GDPR) | Contenuti mai catturati in produzione, solo hash (DA-E1-02); controllo PII sui template (§7) |
| Audit non salvato con scrittura riuscita | Alto (NIS2, integrità) | Fail-closed in transazione unica (DA-A3-07, DA-B2-04); test §8.10 |
| Rottura cache del prefisso prompt (#1781) | Medio: costo | Render deterministico; test di stabilità byte |

## 12. Stima e priorità

- **Dimensione:** M (costruzione da zero: schema e API semplici; complessità nella doppia libreria TS/Python con parità, nella scrittura dei seed v2 e nei controlli di conformità §7. Le decisioni del 2026-11-03 non cambiano la taglia: il fail-closed è una transazione già prevista, la retention passa a DX-09, la notifica incidenti ad A5. Non dipendeva dal riuso: senza migrazione dello storico 0322 il lavoro si sposta sulla stesura dei seed).
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
- Base giuridica per il trattamento delle identità degli operatori (da confermare nella politica DX-09).
- Contratto e interfaccia dei segnali verso A5 (ondata 2).
- Volumi (numero prompt, versioni, frequenza di render): nessun dato; le soglie §7-§8 sono proposte.

## Appendice C — Decisioni aperte

- **DA-E2-01 — Modello dati (riformulata, DX-01):** (a) tabelle generiche `prompts`/`prompt_versions`/`prompt_activations` come in §4.1; (b) colonne di prompt dentro le entità che li usano (supervisori, esecutori) con tabella di storico, come in gravya-app. Criterio: un'unica verità, immutabilità, rollback. Raccomandazione: (a). Non c'è più migrazione dello storico 0322 (DX-01).
- **DA-E2-02 — Motore di template:** (a) sostituzione semplice `{{var}}` senza logica, implementata in TS e Python; (b) motore con logica (es. Jinja-compatibile); (c) nessun template, solo concatenazione nel codice. Criterio: parità TS/Python, sicurezza, assenza di lock-in. Raccomandazione: (a).
- **DA-E2-03 — Perimetro del registry (riformulata, DX-01):** quali prompt v2 stanno nel registry. (a) tutti; (b) supervisori, esecutori e Kloud, con il preambolo fisso (anti-invenzione e avvisi di trasparenza art. 50) escluso e tenuto nel codice; (c) solo un sottoinsieme minimo per lo skeleton. Criterio: un'unica verità, conformità AI Act, master. Raccomandazione: (b). Non è più "quali migrare": i seed si scrivono per v2.
- **DA-E2-04 — Gate di promozione:** (a) solo umano; (b) E3 obbligatorio + approvazione umana (C3); (c) solo E3. Criterio: sorveglianza umana (PV-01; per DX-11 buona pratica, non obbligo AI Act) e master §5. Raccomandazione: (b), con criteri di qualità versionati col prompt.
- **DA-E2-05 — Anticipo rispetto alla Beta:** **Decisa** (chiusa da DX-01, vedi [DECISIONS.md](DECISIONS.md)). v2 si costruisce da zero e la Beta di gravya-app non vincola: E2 è nell'ondata 1.
- **DA-E2-06 — Retention di versioni e attivazioni:** **Assorbita da DX-09** (vedi [DECISIONS.md](DECISIONS.md)): si applica la politica di retention unica; durate non ancora fissate. Le classi di dati prodotte da E2 sono elencate in §7.
- **DA-E2-07 — Versioni proposte da AI (nuova) — DA RIPORTARE ALL'UTENTE.** Il ciclo di miglioramento (`source=learning_proposal`) può creare versioni candidate? (a) sì, mai attivabili senza umano; (b) no in ondata 1. Criterio: sorveglianza umana (buona pratica per DX-11) e rischio di deriva non controllata. Proposta: (a), ma è una scelta di prodotto e conformità.
- **DA-E2-08 — Testi dei seed (nuova) — DA RIPORTARE ALL'UTENTE.** I seed v2 si scrivono da zero o possono partire dai testi dei prompt di gravya-app rivisti? PV-03 ammette l'ingresso solo se un documento lo prevede. Criterio: qualità già validata contro ripartenza pulita. Proposta: partire dai testi di gravya-app come bozza, rivista e approvata come versione 0; nessuna decisione presa.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi di span allineati a E1 (`gravya.prompt.*`); C3 spostato da "È richiesto da" a "Dipende da" (verso invertito: è E2 a usare C3 per la promozione) e aggiunta la dipendenza condizionale da E3; aggiunti C1 e A1 in "È richiesto da"; corretta l'affermazione che il master citi Redis Stream/Kafka (non li cita) e rimando a DA-A1-03. Motivo: interfacce e dipendenze non allineate, affermazione non supportata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). Attributi `gravya.prompt.*` su record di traccia DB-native di E1 anziché span; §7 con voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50, osservabilità AI); rimossi riuso e migrazione da gravya-app (storico 0322, Drizzle, librerie esistenti) e il vincolo Beta; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti da non ripetere); DA-E2-01 e DA-E2-03 riformulate, DA-E2-05 chiusa da DX-01, nuove DA-E2-06..08 da riportare all'utente; rischio "doppio registry" sostituito; taglia M confermata per costruzione da zero. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. Diventano scelte del documento: DA-A1-01 (PostgreSQL+RLS), DA-B1-06 (self-hosted UE), DA-E1-02 (contenuti mai in produzione), DA-E1-05 (vocabolario GenAI semconv/traceparent ammesso per E1, senza SDK), DA-A3-07 e DA-B2-04 (fail-closed sulle scritture: nuova regola §6, criterio §8.10, test §10, rischio §11), DA-E3-08/09 e DA-C1-05 (nessun SaaS, eval su dati sintetici con giudice UE). DA-E2-06 assorbita da DX-09: rimossa la retention propria, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica incidenti ad A5, E2 invia segnali; nuovo criterio §8.11) e DX-11 (responsabile art. 28; sorveglianza umana e log ridotti a buona pratica, art. 50 confermato). Tolte dall'Appendice B le ipotesi decise (regione hosting, classificazione AI Act). Taglia M invariata. Motivo: allineamento a DECISIONS.md. |
