# E2 — Prompt registry

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E2 |
| Nome | Prompt registry |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.5 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È lo store versionato dei prompt della piattaforma (master plan §3 "Prompt management": esterni al codice, versionati, con templating e rollback; §6 E2: "Store versionato di prompt con templating, diff e rollback"). Ogni prompt ha una chiave stabile, una sequenza immutabile di versioni, un puntatore alla versione attiva, un renderer di template e operazioni di diff e rollback.

**Cosa NON fa.**
- Non decide quale prompt usa un agente: il legame agente→prompt sta nel catalogo agenti (master 3.2.1, G4) e, come riferimento `prompt_ref`, nel nodo `Agent` di A1.
- Non valuta la qualità di una versione: lo fa E3 (offline) ed E4 (online). E2 espone solo l'hook di promozione.
- Non conserva i testi renderizzati con dati dei clienti, né li fa entrare nelle tracce: in produzione i contenuti non si catturano (DA-E1-02, decisa).
- Non sceglie il modello LLM né il provider, e non invia dati a nessun provider: il testo renderizzato va al chiamante (B1, B2).
- Non applica l'etichetta "generato da AI", la marcatura leggibile da macchina (art. 50(2)) né l'informativa art. 50(1): sono invarianti applicate nel codice e nei connettori (§7); E2 fornisce solo l'identità del prompt (`prompt_ref`).

**Perché esiste.** Senza un registry, un cambio di prompt non è tracciabile, confrontabile né reversibile, e il gate di E3 ("a ogni PR che cambia prompt", master §5 Livello 1) non ha un oggetto da bloccare.

## 3. Contesto e dipendenze

**Dipende da:**
- **F1** (schema applicativo PostgreSQL con `tenant_id` e RLS, DA-A1-01): tabelle del registry. Ondata successiva; nell'ondata 1 si usa lo schema minimo di E2 (DA-E2-01).
- **E1** (tracing DB-native, PV-02): ogni render valorizza `gravya.prompt.key`/`gravya.prompt.version`/`gravya.prompt.hash` sul record di traccia della chiamata LLM (vocabolario di E1 §4.1). Per DA-E1-05 E1 può adottare i nomi GenAI semconv e il formato traceparent come vocabolario, senza SDK né export OpenTelemetry; se E1 rinomina gli attributi, E2 si allinea.
- **E3** (eval offline): gate di promozione (DA-E2-04; casi solo sintetici, giudice nell'UE: DA-E3-08, DA-E3-09).
- **C3** (punto HITL): approvazione umana della promozione, se DA-E2-04 sceglie (b); obbligatoria per le versioni proposte da AI (DA-E2-07).
- **A3** (runtime enforcement): autorizza le scritture. Fail-closed (DA-A3-07).
- **A5** (audit trail, ondata 2): riceve i segnali di E2; la notifica incidenti è sua (DX-10).
- **A6** (identità, ruoli e configurazione di piattaforma, DX-14, ondata 2): identità dell'attore e pseudonimo (DX-21), registro versionato delle variabili (DX-13), log degli accessi cross-tenant (DX-18).
- **F6** (retention e cancellazione, DX-12, ondata 2; l'ID è una proposta): applica le durate alle classi di E2.

**È richiesto da:** F6 (classi di dati), B1 (risolve il prompt da E2), C1 (`prompt_ref` dei nodi `agent` e campo `ai_generated`), C3 (mostra `prompt_ref` all'approvatore), A1 (`prompt_ref` del nodo `Agent`), E3, E4, G4 (mostra la versione), D1-D4 (marcatura per canale, via C1).

**Fatti decisi:** store PostgreSQL con RLS (DA-A1-01); infrastruttura self-hosted nell'UE (DA-B1-06); nessuna piattaforma SaaS di prompt, eval o tracing (PV-02, DA-E3-09, DA-C1-05).

**Assunzioni:** l'identità dell'attore (umano, superadmin, agente) è fornita da A6, non da A3 (DX-21).

## 4. Contratti

### 4.1 Schema dati (proposta)

| Tabella | Campi minimi |
|---|---|
| `prompts` | `id`, `key` (es. `supervisor.commercial.system`), `tenant_id` NULL = globale/seed, `active_version_id`, `created_at` |
| `prompt_versions` | `id`, `prompt_id`, `version` (intero monotono per prompt), `template`, `variables_schema` (JSON Schema), `content_hash` (SHA-256), `parent_version_id`, `source` (`seed`/`human`/`learning_proposal`/`rollback`), `created_by` (pseudonimo), `created_at`, `change_note` |
| `prompt_activations` | `id`, `prompt_id`, `from_version_id`, `to_version_id`, `reason` (`promote`/`rollback`), `actor` (pseudonimo), `created_at` (append-only) |

Regole: `prompt_versions` è **immutabile** per ogni attore applicativo (nessun UPDATE/DELETE, come trigger DB); la versione 0 di ogni prompt globale è il seed del repo; RLS su `tenant_id` con riga globale visibile in lettura. La cancellazione per retention o a fine contratto è di F6 e richiede un percorso dedicato e auditato (DA-E2-11).

### 4.2 Eventi emessi
`prompt.version.created`, `prompt.version.activated`, `prompt.version.rolled_back` — payload: `prompt_key`, `tenant_id`, `from_version`, `to_version`, `actor` (pseudonimo). Bus: DX-03 (aperta).

### 4.3 Output del render
`{ text, prompt_key, version, content_hash }` — `content_hash` è dell'output renderizzato, per correlazione in audit senza testo. Algoritmo SHA-256 e lunghezza dell'hash sono un formato invariante (catalogo §18); la lunghezza si fissa con E1.

## 5. Interfacce

- **Libreria di risoluzione** (usata da B1): `resolve(key, tenant_id) → version` e `render(version, variables) → output`, in TypeScript e Python (servizi Node e agenti Python, DX-04). In gravya-app i prompt erano letti da entrambi i linguaggi: è la lezione che motiva il requisito, non un vincolo.
- **API di gestione:**
  - `GET /v1/prompts/{key}/versions` — elenco.
  - `POST /v1/prompts/{key}/versions` — crea versione (non la attiva).
  - `GET /v1/prompts/{key}/diff?from=N&to=M` — diff testuale unificato.
  - `POST /v1/prompts/{key}/activate` `{version}` — promozione.
  - `POST /v1/prompts/{key}/rollback` `{to_version?}` — default: versione attiva precedente; `to_version=0` = seed.
- **CLI di seed/export**: carica i seed dal repo come versione 0 ed esporta il registry in file (portabilità; export del tenant a fine contratto).

## 6. Comportamento

**Flusso principale (nuova versione).**
1. Un attore autorizzato (A3) crea una versione; il sistema valida il template (variabili dichiarate = variabili usate; controllo dei dati personali, §7) e calcola `content_hash`.
2. Se l'hash coincide con una versione esistente, risponde con quella (idempotenza).
3. La promozione richiede, se DA-E2-04 sceglie (b) o (c) e comunque per le versioni `learning_proposal` (DA-E2-07, decisa), l'esito del gate E3 sulla versione candidata: **zero fallimenti bloccanti** (invariante, C7 (b)); con (b) anche l'approvazione umana via C3. Poi aggiorna `active_version_id` e scrive `prompt_activations` in una sola transazione.
4. Emette l'evento; le cache dei runtime si invalidano.

**Fail-closed sulle scritture (DA-A3-07, DA-B2-04).** Creazione, attivazione e rollback avvengono solo se il record di decisione di A3 e la riga di `prompt_activations` sono salvati; altrimenti l'operazione è annullata e il puntatore attivo non cambia.

**Rollback.** Sposta il puntatore a una versione esistente; non crea né cancella versioni. Il seed (v0) è sempre ripristinabile.

**Casi limite.**
- Variabile mancante al render → errore esplicito, nessun render parziale.
- Prompt di tenant assente → si usa il globale; se manca anche quello → errore, nessun fallback hard-coded.
- Promozione concorrente → lock sulla riga `prompts`; il secondo riceve `409`.
- Versione referenziata da un'attivazione o da un trace → non cancellabile da attori applicativi; fa eccezione il percorso di F6 (DA-E2-11).
- Azione riservata a umani (attivazione e rollback; HSAR/P16 di gravya-app, Appendice A) → scrittura AI rifiutata.
- Variabile di piattaforma non leggibile o non valida (DX-17) → le scritture e i render che richiedono il valore sono bloccati, con segnale ad A5; la cache ancora entro l'ultimo TTL valido continua a servire (lettura di E2, da confermare con A6). Senza nessun valore valido (primo avvio) valgono le regole del catalogo (regola 4): valore «deciso» come primo valore; per un valore «da definire» l'azione si blocca.
- **Superadmin.** Può ripristinare il seed dei prompt globali. Su un prompt di un tenant opera solo entro le istruzioni del titolare (art. 28(3)(a) GDPR): per analogia con DX-19 (non decisa per E2, DA-E2-09), di default vede solo metadati aggregati (conteggi, versioni, hash) e il testo del template solo su richiesta dell'agenzia o per un incidente. Ogni accesso o scrittura cross-tenant passa da A3, registra l'attore in `prompt_activations` e una riga nel log degli accessi di A6 (DX-18); se il log non si salva, l'operazione è rifiutata. Gli admin delle agenzie sono confinati al proprio tenant da RLS.

## 7. Requisiti non funzionali

- **Performance:** `resolve`+`render` da cache entro `e2.resolve_render_p99_ms`; propagazione di un rollback entro `e2.rollback.propagation_max_s`.
- **Variabili di piattaforma (DX-13, DX-22).** Nessun valore è nel codice. Variabili di E2: `e2.cache.max_ttl_s`, `e2.rollback.propagation_max_s`, `e2.resolve_render_p99_ms` e le durate di retention delle classi sotto. Il controllo dei dati personali nei template **non è una variabile**: è sempre `block` (invariante, C7 (a)). `e2.cache.max_ttl_s` non è attivabile in produzione senza un intervallo minimo-massimo deciso (D4, regola 11 del catalogo; valori con A5 e A6): l'ondata 1 non va in produzione (DA-CV-20). Ogni modifica è versionata e auditata.
- **Sicurezza e conformità (PV-01).**
  - *Perimetro dati.* Registry in PostgreSQL di Gravya, self-hosted nell'UE (DA-B1-06). Il testo renderizzato è consegnato a B1 e B2, che lo inviano solo a destinazioni dichiarate: extra-UE solo con opt-in dell'agenzia, strumento di trasferimento e stato validi; ogni destinazione, anche UE, con sub-responsabile autorizzato (riferimento al DPA, data), impostati dal superadmin con fonte e audit (DA-B2-07, DA-CV-19; GDPR art. 28(2) e (4), Cap. V). Il Data Privacy Framework copre solo le organizzazioni USA dell'elenco DPF ed è impugnato (C-703/25 P). Il giudice LLM dell'hook E3 elabora nell'UE (DA-E3-09).
  - *GDPR — ruolo.* Gravya è responsabile (art. 28) per i template e i dati dei tenant; titolare per i dati dei propri utenti (DA-A1-08). I template dei tenant sono dati dell'agenzia.
  - *GDPR — minimizzazione (art. 5(1)(c), art. 25).* Il registry conserva template e metadati, mai testi renderizzati con dati dei clienti. I template non devono contenere dati personali: controllo in validazione su pattern base (email, telefono), sempre in blocco; non garantisce l'assenza di dati personali (Appendice B). Dati personali trattati: identificativo pseudonimo di chi crea o attiva (`created_by`, `actor`) e il testo libero `change_note`. Un identificativo pseudonimo resta dato personale (considerando 26; le linee guida EDPB 01/2025 sono solo in consultazione). La mappa di re-identificazione non è in E2: è classe `retention.pseudonym_map_months` (F6); la regola «la richiesta di cancellazione del titolare elimina la riga della mappa entro il termine del DPA» è proposta in DECISIONS §4, non decisa.
  - *GDPR — retention e diritti.* Politica unica DX-09 (DECISIONS §5); le durate sono di sola lettura finché non esiste l'intervallo del DPA, con valore per agenzia `retention.<classe>.tenant_value` solo per le classi che sono dati dell'agenzia. Classi di E2: (1) versioni e puntatori (`prompt_versions`, `prompts`): artefatti di configurazione, durata del servizio, attore pseudonimo, nessuna variabile di durata; (2) `prompt_activations` (append-only): `retention.audit_decisions_months`; (3) eventi `prompt.version.*`: `retention.runtime_events_days` (assegnazione da validare); (4) segnali ad A5: `retention.incident_signals_months`, sempre prodotti e conservati (C2), durata provvisoria fissata dall'utente prima della produzione (DA-CV-20); (5) evidenze di incidente: `retention.incident_evidence_months`, sospensione non attivabile finché massimo, riesame e categorie non sono definiti e solo per dati di Gravya; per i dati delle agenzie serve istruzione nel DPA e parere legale prima di F6 (DA-CV-21); (6) log degli accessi cross-tenant: `retention.cross_tenant_access_log_months` (A6). I backup scadono entro `retention.data_backup_days`; al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22). **Fine contratto** (DECISIONS §5, Data Act art. 25(2), registro norme v1.6): export dei prompt del tenant disponibile per tutto il periodo di uscita (`retention.tenant_offboarding_days`, minimo di recupero di almeno 30 giorni dopo il periodo di passaggio), poi cancellazione; la scelta restituzione o cancellazione spetta all'agenzia (`retention.tenant_offboarding_choice`, sempre disponibile). La qualificazione del SaaS come «servizio di trattamento dei dati» è da confermare con un legale. Assistenza all'agenzia su richieste degli interessati: `dsar.assist_max_days` (obbligo del DPA); export per attore da `prompt_versions` e `prompt_activations`.
  - *NIS2 (ready by design, DX-10; Gravya oggi non è soggetto NIS2).* Log e controllo accessi: Reg. (UE) 2024/2690, allegato 3.2 (registrazione, anche degli accessi privilegiati e delle attività amministrative, 3.2.3(e)) e 11.2-11.3 (privilegio minimo, riesame), come requisiti di progetto. Gestione delle modifiche con test e valutazione prima dell'attuazione (allegato 6.4): gate di promozione. Integrità: `content_hash` e immutabilità a livello DB. Notifica incidenti: flusso presente ma non attivo (`incident.nis2_flow_active`); preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, decorrenza dalla conoscenza: tutto di A5. E2 invia ad A5 un segnale per ogni scrittura non autorizzata, ogni modifica del prompt attivo fuori flusso e ogni variabile non leggibile; i segnali sono esclusi dal blocco (DA-CV-17).
  - *AI Act (art. 50 applicabile dal 2.8.2026; DX-11: non alto rischio).* Etichetta «generato da AI» (non disattivabile dal tenant), informativa a chi interagisce con un'IA (art. 50(1)) e marcatura leggibile da macchina anche del testo (art. 50(2), nei limiti tecnici del canale; dettaglio in C1 e D1-D4) sono invarianti (catalogo §18): non dipendono da un testo di prompt modificabile, quindi stanno nel codice con il preambolo fisso e il blocco anti-invenzione (DA-E2-03). E2 espone `prompt_ref` (chiave, versione, hash) per il campo `ai_generated` di C1. Il dettaglio di marcatura del testo del Codice di buone pratiche non è verificato. Artt. 12, 14, 19, 26: solo buona pratica (DX-11), e per l'alto rischio dal 2.12.2027; qui: attivazione e rollback solo umani, registrazione di versione e attivazione con attore e motivo.
  - *Marketing (PV-01).* E2 non invia verso terzi; consensi, opt-out, art. 130 Codice privacy e ePrivacy sono di D1-D4.
  - *Isolamento.* RLS per tenant; scritture solo con attore autorizzato da A3.
- **Portabilità:** template testuali, export completo in file, nessun SaaS di prompt management.
- **Osservabilità AI:** ogni chiamata LLM è attribuibile a `prompt_key`+`version`+`content_hash` nel record di traccia di E1; attivazioni e rollback sono interrogabili in SQL e correlabili alle tracce.

## 8. Criteri di accettazione

1. **Immutabilità:** UPDATE e DELETE su `prompt_versions` da un ruolo applicativo → entrambi falliscono a livello DB.
2. **Rollback:** attiva v2, rollback, `resolve` restituisce v1 entro `e2.rollback.propagation_max_s`; `prompt_activations` ha 2 righe.
3. **Seed ripristinabile:** `rollback to_version=0` restituisce testo byte-identico al seed del repo (confronto hash).
4. **Isolamento:** con due tenant, il tenant A non legge né modifica versioni del tenant B (0 righe, `403/404`).
5. **Template fail-closed:** render con variabile mancante → errore.
6. **Diff:** `GET diff` tra due versioni note restituisce l'unified diff atteso (snapshot test).
7. **Nessun prompt nel codice:** check in CI (grep/lint sui pattern di DA-E2-03) sui moduli migrati → 0 occorrenze; i seed del registry non contengono il preambolo fisso né gli avvisi art. 50.
8. **Tracciabilità:** in un test end-to-end ogni record di traccia delle chiamate LLM ha `gravya.prompt.key` e `gravya.prompt.version`; nessuna eccezione.
9. **Portabilità:** export → import su DB vuoto → stesso insieme di `content_hash`.
10. **Fail-closed:** con il salvataggio del record A3 o della riga `prompt_activations` forzato a fallire, attivazione e rollback sono rifiutati, `active_version_id` invariato, nessuna versione creata.
11. **Segnale ad A5:** una scrittura non autorizzata produce un segnale verso A5 (o il suo stub).
12. **Accesso cross-tenant:** una lettura o un rollback del superadmin su un prompt di tenant produce 1 riga nel log degli accessi; con il log forzato a fallire l'operazione è rifiutata; l'admin di un'altra agenzia riceve `403/404`; senza richiesta dell'agenzia o incidente la lettura del testo è rifiutata (se DA-E2-09 sceglie (a)).
13. **Variabili:** cambiando `e2.rollback.propagation_max_s` senza rilascio, E2 applica il nuovo valore e la modifica è versionata e auditata; con la variabile non leggibile le scritture sono rifiutate e parte un segnale.
14. **Controllo dei dati personali:** un template con un'email o un telefono è rifiutato; nessuna configurazione o parametro di richiesta consente di attenuare il blocco (test sulla superficie di configurazione).
15. **Gate di promozione:** con E3 (o il suo stub) che restituisce almeno un fallimento bloccante, l'attivazione è rifiutata e `active_version_id` non cambia; una versione `learning_proposal` non è attivabile senza approvazione umana.
16. **Intervallo richiesto:** avviando E2 in produzione senza un intervallo deciso per `e2.cache.max_ttl_s`, l'avvio fallisce con errore esplicito (proposta; la guardia di produzione è un'invariante di deploy, catalogo §18).
17. **Retention:** ogni tabella di E2 è associata a una classe del catalogo (test con F6 o il suo stub); l'export di un tenant resta eseguibile per tutto il periodo di uscita.

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Decisioni DA-E2-01..04, 09, 10, 11.
2. Schema e migrazioni PostgreSQL con trigger di immutabilità e RLS.
3. Renderer di template (DA-E2-02), in TS e Python con test di parità.
4. API di gestione, diff, rollback; CLI seed/export.
5. Lettura delle variabili di piattaforma da A6; log degli accessi cross-tenant.
6. Cache con invalidazione su evento; attributi su E1; segnali ad A5.
7. Seed v2 per i prompt nel perimetro (DA-E2-03, DA-E2-08) e check CI.
8. Gate di promozione verso E3 (e C3 per l'approvazione).

**Tecnologie (dal master o da decidere):** PostgreSQL con RLS (DA-A1-01), TypeScript e Python, SHA-256. ORM e migrazioni con F1. Il motore di template non è nel master (DA-E2-02). Il master cita Redis per stato di sessione e rate limiting, non per la cache dei prompt: DA-E2-10.

## 10. Test e valutazione

- **Unit:** render, validazione variabili, controllo dei dati personali, hash, diff.
- **Integration (PostgreSQL reale):** immutabilità, RLS, rollback, concorrenza, gate di promozione.
- **Parità TS/Python:** stesso template e variabili → stesso output byte per byte.
- **Eval:** la promozione richiama E3 sulla versione candidata; E2 non implementa eval.
- **Security:** scrittura con attore non autorizzato (segnale ad A5); fail-closed con record A3 o attivazione forzati a fallire; template injection (una variabile con sintassi di template non è rivalutata); accesso del superadmin con e senza log; tentativo di attenuare il blocco dei dati personali.

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Prompt dispersi nel codice (fallback e prompt hard-coded di gravya-app) | Alto: verità divisa | Un solo punto di risoluzione, nessun fallback, check CI (§8.7); DA-E2-03 |
| Divergenza renderer TS/Python | Medio | Test di parità; motore senza logica (DA-E2-02) |
| Cache stantia dopo rollback | Medio | Invalidazione su evento; `e2.cache.max_ttl_s` con intervallo deciso prima della produzione |
| Dati personali in template o `change_note` | Alto (GDPR) | Blocco sempre attivo su pattern base, contenuti mai catturati in produzione (DA-E1-02); limite del controllo dichiarato |
| Etichetta o informativa art. 50 rimosse da un template del tenant | Alto (AI Act) | Invarianti nel codice, non nei prompt; check CI sui seed |
| Scrittura riuscita con audit non salvato | Alto (integrità, Reg. 2024/2690 all. 3.2) | Fail-closed in transazione unica (DA-A3-07, DA-B2-04); test §8.10 |
| Abuso dell'accesso superadmin ai prompt dei tenant | Alto (GDPR art. 28, all. 11.3) | Istruzioni del titolare, passaggio da A3, log fail-closed, segnale ad A5; DA-E2-09 |
| Immutabilità in conflitto con cancellazione a fine contratto o richiesta dell'interessato | Alto (GDPR art. 17, 28(3)(g)) | Percorso di cancellazione di F6 (DA-E2-11); pseudonimo al posto del nome |
| Variabile di piattaforma modificata male | Medio | Modifica versionata e auditata, intervallo deciso, fail-closed (DX-13, DX-17); test §8.13 |
| Rottura cache del prefisso prompt (#1781) | Medio: costo | Render deterministico; test di stabilità byte |

## 12. Stima e priorità

- **Dimensione:** M. Schema e API semplici; la complessità è nella doppia libreria TS/Python con parità, nei seed v2 e nei controlli di conformità §7. Le decisioni del 2026-11-04 non cambiano la taglia: aggiungono invarianti, un gate e un percorso di cancellazione concordato con F6.
- **Dipendenze critiche:** F1 (o schema minimo), A3, E1, A6 per variabili e identità, E3 per il gate.
- **Thin-slice MVP:** **Sì**, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è materiale di riferimento (PV-03): nessun file, tabella o dato entra in v2 da qui. I punti seguenti sono ripresi dalla versione 1.4 del documento e non sono stati riletti nel codice in questa versione (Appendice B).

**Idee da riprendere:**
- `gravya_supervisor_prompt_revisions.ts` e migrazione `0322`: storico before/after con RLS ENABLE+FORCE per azienda.
- `learning-proposal-apply.ts`: stale guard e revisione nella stessa transazione, per l'attivazione atomica.
- `llm/prompt-hash.ts`: SHA-256 troncato a 16 caratteri, testo mai nell'audit.
- `kloud_config.py` / `router.py`: blocco anti-invenzione non sovrascrivibile dal DB (P11): parte fissa nel codice per vincoli di sicurezza e trasparenza.
- `gravya-app-kloudify/docs/visione/README.md` P12 (prompt nel DB, seed nel repo, ripristino superadmin) e P16 (`system_prompt` solo umani); `architettura-agenti.md` §2.8.

**Difetti da non ripetere:** prompt sparsi (fallback `_default_system_prompt()`, `card_analyzer.py:113`); storico senza versione, puntatore, rollback né diff; prompt degli esecutori in un'altra tabella; cache con TTL 60 s senza invalidazione su evento; nessun motore di template né ADR sui prompt.

**Divergenze dal master plan:** prompt esterni al codice, ma il preambolo fisso resta nel codice (DA-E2-03); templating senza motore indicato (DA-E2-02); criteri di qualità versionati col prompt e attivazione solo umana non previsti dal master (DA-E2-04); OpenTelemetry sostituito da tracing DB-native (PV-02).

## Appendice B — Non verificato

- Il contenuto dell'Appendice A (file, funzioni e valori di gravya-app e kloudify) non è stato riletto in questa versione; l'elenco completo dei prompt hard-coded in `services/agents` non è noto.
- Lingua dei prompt v2 (P12 diceva inglese); stato delle issue #1801, #1494, #1781.
- Copertura del controllo dei dati personali: i pattern base (email, telefono) non rilevano altri dati personali (dedotto); `change_note` è testo libero e non è coperto.
- Meccanismo di cancellazione di dati immutabili a fine contratto e per l'art. 17 (DA-E2-11); regola sulla mappa degli pseudonimi (DECISIONS §4, non decisa).
- Applicazione di DX-19 ai template dei tenant (DA-E2-09) e dell'intervallo di `access.superadmin_trace_access_ttl_hours` ai prompt.
- Intervallo di `e2.cache.max_ttl_s` (D4: valori con A5 e A6, ondata 2); intervallo di `e2.rollback.propagation_max_s`, per cui D4 non lo richiede: lo stesso rischio di una cache stantia non è coperto.
- Classe di retention degli eventi `prompt.version.*` (non elencati in DECISIONS §5); perimetro per agenzia di `audit_decisions_months` e `runtime_events_days` (dedotto nel catalogo).
- Comportamento di cache e render con variabile non leggibile (§6): lettura di E2, non confermata da A6.
- Dettaglio della marcatura del testo del Codice di buone pratiche art. 50 (registro §9.1: testo non letto); eccezione per funzione assistiva di editing (art. 50(2)) non valutata.
- Qualificazione del SaaS come «servizio di trattamento dei dati» (Data Act); ambito NIS2 di Gravya, non accertato (DX-10).
- Contratto dei segnali verso A5 (tabella di audit minima in ondata 1, ondata 2 per A5); compatibilità delle durate con i contratti delle agenzie; volumi (numero di prompt, versioni, render): nessun dato.

## Appendice C — Decisioni aperte

- **DA-E2-01 — Modello dati:** (a) tabelle generiche come in §4.1; (b) colonne di prompt dentro le entità che li usano, con tabella di storico. Criterio: un'unica verità, immutabilità, rollback. Raccomandazione: (a). Aperta in DECISIONS.
- **DA-E2-02 — Motore di template:** (a) sostituzione `{{var}}` senza logica, in TS e Python; (b) motore con logica (Jinja-compatibile); (c) solo concatenazione nel codice. Criterio: parità TS/Python, sicurezza, assenza di lock-in. Raccomandazione: (a). Aperta in DECISIONS.
- **DA-E2-03 — Perimetro del registry:** (a) tutti i prompt; (b) supervisori, esecutori e Kloud, con il preambolo fisso (anti-invenzione, avvisi art. 50, informativa art. 50(1)) nel codice; (c) sottoinsieme minimo per lo skeleton. Criterio: un'unica verità, invarianti AI Act non disattivabili da un template. Raccomandazione: (b). Aperta in DECISIONS.
- **DA-E2-04 — Gate di promozione:** (a) solo umano; (b) E3 obbligatorio e approvazione umana (C3); (c) solo E3. Criterio: sorveglianza umana (buona pratica, DX-11), master §5, Reg. 2024/2690 all. 6.4. Raccomandazione: (b), con criteri di qualità versionati col prompt. Aperta in DECISIONS; il gate E3 senza fallimenti bloccanti è invariante (C7 (b)) dove si applica.
- **DA-E2-05 — Anticipo rispetto alla Beta:** **Decisa** (DX-01). E2 è nell'ondata 1.
- **DA-E2-06 — Retention di versioni e attivazioni:** **Assorbita da DX-09**; classi in §7.
- **DA-E2-07 — Versioni proposte da AI:** **Decisa (2026-11-03, utente)**: ammesse come candidate, mai attivabili senza un umano; attivazione tramite gate E3 e approvazione umana via C3.
- **DA-E2-08 — Testi dei seed:** **Decisa (2026-11-03, utente)**: testi di gravya-app come bozza, rivisti contro i contratti v2 e ripuliti dai residui della visione precedente; approvati come versione 0.
- **DA-E2-09 — Visibilità del superadmin sui template dei tenant — DA RIPORTARE ALL'UTENTE.** (a) come DX-19: di default solo metadati aggregati, testo solo su richiesta dell'agenzia o per incidente, con log; (b) lettura del testo con solo log. Criterio: DX-19, art. 28(3)(a) GDPR, minimizzazione. Raccomandazione: (a).
- **DA-E2-10 — Cache dei prompt:** (a) in-process con invalidazione su evento e TTL; (b) Redis (non indicato dal master per questo uso). Criterio: nessuna tecnologia non prevista, parità TS/Python, dipende dal bus (DX-03). Raccomandazione: (a).
- **DA-E2-11 — Cancellazione di versioni immutabili — DA RIPORTARE ALL'UTENTE.** (a) il trigger consente DELETE solo a un ruolo di retention di F6, con riga di audit; (b) cancellazione per tenant tramite partizioni o tabelle dedicate, gestita da F6. Criterio: art. 17 e 28(3)(g) GDPR, Data Act art. 25(2), integrità. Raccomandazione: (a), da concordare con F6.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi di span allineati a E1 (`gravya.prompt.*`); C3 spostato da "È richiesto da" a "Dipende da" (verso invertito: è E2 a usare C3 per la promozione) e aggiunta la dipendenza condizionale da E3; aggiunti C1 e A1 in "È richiesto da"; corretta l'affermazione che il master citi Redis Stream/Kafka (non li cita) e rimando a DA-A1-03. Motivo: interfacce e dipendenze non allineate, affermazione non supportata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). Attributi `gravya.prompt.*` su record di traccia DB-native di E1 anziché span; §7 con voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50, osservabilità AI); rimossi riuso e migrazione da gravya-app (storico 0322, Drizzle, librerie esistenti) e il vincolo Beta; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti da non ripetere); DA-E2-01 e DA-E2-03 riformulate, DA-E2-05 chiusa da DX-01, nuove DA-E2-06..08 da riportare all'utente; rischio "doppio registry" sostituito; taglia M confermata per costruzione da zero. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. Diventano scelte del documento: DA-A1-01 (PostgreSQL+RLS), DA-B1-06 (self-hosted UE), DA-E1-02 (contenuti mai in produzione), DA-E1-05 (vocabolario GenAI semconv/traceparent ammesso per E1, senza SDK), DA-A3-07 e DA-B2-04 (fail-closed sulle scritture: nuova regola §6, criterio §8.10, test §10, rischio §11), DA-E3-08/09 e DA-C1-05 (nessun SaaS, eval su dati sintetici con giudice UE). DA-E2-06 assorbita da DX-09: rimossa la retention propria, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica incidenti ad A5, E2 invia segnali; nuovo criterio §8.11) e DX-11 (responsabile art. 28; sorveglianza umana e log ridotti a buona pratica, art. 50 confermato). Tolte dall'Appendice B le ipotesi decise (regione hosting, classificazione AI Act). Taglia M invariata. Motivo: allineamento a DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: durate di default di DECISIONS.md §5 assegnate alle classi di dati di E2 in §7 (versioni e puntatori per la durata del servizio, attivazioni 12 mesi, eventi 90 giorni da validare, log accessi 12 mesi, evidenze di incidente), DA-E2-06 aggiornata, criterio §8.14. DX-13: soglie di E2 (TTL cache, propagazione rollback, modalità controllo PII, durate) diventano variabili di piattaforma del superadmin, versionate, auditate e fail-closed (§7, §6, §8.2, §8.13, rischio §11); accesso cross-tenant solo come superadmin entro le istruzioni del titolare e con log degli accessi fail-closed (§6, §7, §8.12, §10, rischio §11). DECISIONS.md §6 decisa: base giuridica degli identificativi degli attori (agenzia per i suoi utenti, Gravya per superadmin e operatori), tolta dall'Appendice B. Dipendenze aggiunte: F6 (DX-12) e registro delle variabili, con proprietario A6 solo proposto (DX-14 da riportare). Le altre righe della §6 non citano E2. Taglia M invariata. Motivo: allineamento a DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento a DECISIONS (C1-C14, D1-D8, DA-CV-18..23), catalogo delle variabili v1.2 e registro delle norme v1.6. Controllo dei dati personali sempre `block` (invariante, C7 (a)); gate E3 senza fallimenti bloccanti (C7 (b)) e criterio §8.15; valori fissi sostituiti con i nomi del catalogo (§7, §8) e intervallo richiesto per `e2.cache.max_ttl_s` (D4); art. 50(1), art. 50(2) e etichetta come invarianti fuori dai prompt (D6, D7); provider come sub-responsabili con destinazione dichiarata (DA-CV-19); «legal hold» sostituito da evidenze di incidente (DA-CV-21) e «NIS2 (art. 21)» per i log da Reg. 2024/2690 all. 3.2 e 11, con flusso NIS2 presente ma non attivo e segnali sempre conservati; DX-17 per le variabili non leggibili; fine contratto secondo il Data Act (D2); backup (DA-CV-22); mappa degli pseudonimi; A6 deciso (DX-14); DA-E2-07 e DA-E2-08 segnate decise; nuove DA-E2-09..11; testo tagliato e Appendice A segnata come non riletta. Motivo: un solo passaggio di allineamento prima dell'unica revisione. |
