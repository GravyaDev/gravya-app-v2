# E2 — Prompt registry

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E2 |
| Nome | Prompt registry |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È lo store versionato dei prompt della piattaforma (master plan §3 "Prompt management": esterni al codice, versionati, con templating e rollback; §6 E2: "Store versionato di prompt con templating, diff e rollback"). Ogni prompt ha una chiave stabile, una sequenza immutabile di versioni, un puntatore alla versione attiva, un renderer di template e operazioni di diff e rollback.

**Cosa NON fa.**
- Non decide quale prompt usa un agente: il legame agente→prompt sta nel catalogo agenti (master 3.2.1, G4) e, come riferimento `prompt_ref`, nel nodo `Agent` di A1.
- Non valuta la qualità di una versione: lo fa E3 (offline, in CI) ed E4 (online). E2 non chiama E3 a runtime: all'attivazione verifica l'esito che E3 ha già registrato (§6).
- Non conserva i testi renderizzati con dati dei clienti, né li fa entrare nelle tracce: in produzione i contenuti non si catturano (DA-E1-02, decisa).
- Non sceglie il modello LLM né il provider, e non invia dati a nessun provider: il testo renderizzato va al chiamante (C1, che lo passa al job di B1).
- Non applica l'etichetta «generato da AI», la marcatura leggibile da macchina (art. 50(2)) né l'informativa art. 50(1): le applicano il codice di C1 e dei connettori (§7); E2 fornisce solo l'identità del prompt (`prompt_ref`).

**Perché esiste.** Senza un registry, un cambio di prompt non è tracciabile, confrontabile né reversibile, e il gate di E3 ("a ogni PR che cambia prompt", master §5 Livello 1) non ha un oggetto da bloccare.

## 3. Contesto e dipendenze

**Dipende da:**
- **F1** (schema applicativo PostgreSQL con `tenant_id` e RLS, DA-A1-01): tabelle del registry. Ondata successiva; nell'ondata 1 si usa lo schema minimo di E2 (DA-E2-01).
- **E1** (tracing DB-native, PV-02): ogni render valorizza `gravya.prompt.key`/`gravya.prompt.version`/`gravya.prompt.hash` sul record di traccia della chiamata LLM; E1 registra **solo l'hash del template** (E1, decisione del 2026-11-04), mai quello del render. Per DA-E1-05 E1 può adottare i nomi GenAI semconv e il formato traceparent come vocabolario, senza SDK né export OpenTelemetry; se E1 rinomina gli attributi, E2 si allinea.
- **E3** (eval offline in CI): produce un esito registrato per ogni versione (versione, hash del template, esito, data); E2 lo verifica all'attivazione (gate obbligatorio, E6). Interfaccia di trasferimento: DA-E2-12.
- **C3** (punto HITL): approvazione umana della promozione, obbligatoria per le versioni proposte da AI (DA-E2-07); per le altre DA-E2-04.
- **A3** (runtime enforcement): autorizza le scritture. Fail-closed (DA-A3-07). Valuta anche, sulla policy compilata da A2, strumento di trasferimento e sub-responsabile delle destinazioni; B2 e l'egress-proxy di B1 applicano lo stesso esito.
- **A5** (audit trail, ondata 2): riceve i segnali di E2; la notifica incidenti è sua (DX-10).
- **A6** (identità, ruoli e configurazione di piattaforma, DX-14, ondata 2): identità e pseudonimo dell'attore (DX-21), registro versionato delle variabili (DX-13), log degli accessi cross-tenant (DX-18), cifratura a riposo e in transito e gestione delle chiavi (compresa la chiave HMAC per tenant, §4.3).
- **F6** (retention, cancellazione e backup, DX-12, ondata 2; l'ID è una proposta): durate delle classi di E2, cancellazione delle versioni (DA-E2-11), strumento di esportazione dei dati di un tenant.

**È richiesto da:** F6 (classi di dati), C1 (risolve il prompt da E2, prepara il testo e passa al job di B1 il testo renderizzato tramite `input_ref`; `prompt_ref` dei nodi `agent`; campo `ai_generated`), B1 (riceve il testo renderizzato e non chiama E2), C3 (mostra `prompt_ref` all'approvatore), A1 (`prompt_ref` del nodo `Agent`), E3 (versioni dei prompt nel report; stesso controllo dei dati personali per il validatore, E10), E4, G4 (mostra la versione), D1-D4 (marcatura per canale, via C1).

**Fatti decisi:** store PostgreSQL con RLS (DA-A1-01); infrastruttura self-hosted nell'UE (DA-B1-06); nessuna piattaforma SaaS di prompt, eval o tracing (PV-02, DA-E3-09, DA-C1-05); backend in Python in un solo repository, interfaccia in TypeScript più avanti (E16): contratti in Pydantic.

**Assunzioni:** l'identità dell'attore (umano, superadmin, agente) è fornita da A6, non da A3 (DX-21).

## 4. Contratti

### 4.1 Schema dati (proposta)

| Tabella | Campi minimi |
|---|---|
| `prompts` | `id`, `key` (es. `supervisor.commercial.system`), `tenant_id` NULL = globale/seed, `active_version_id`, `created_at` |
| `prompt_versions` | `id`, `prompt_id`, `version` (intero monotono per prompt), `template`, `variables_schema` (JSON Schema), `template_hash` (SHA-256 del template), `parent_version_id`, `source` (`seed`/`human`/`learning_proposal`/`rollback`), `created_by` (pseudonimo), `created_at`, `change_note` |
| `prompt_activations` | `id`, `prompt_id`, `from_version_id`, `to_version_id`, `reason` (`promote`/`rollback`), `actor` (pseudonimo), `incident_ref` o `assistance_ref` (solo per accessi del superadmin, §6), `created_at` (append-only) |
| `prompt_eval_outcomes` | `prompt_version_id`, `template_hash`, `outcome`, `evaluated_at` (esito registrato da E3, §6; interfaccia: DA-E2-12) |

Regole: `prompt_versions` è **immutabile** per ogni attore applicativo (nessun UPDATE/DELETE, come trigger DB); la cancellazione per retention o a fine contratto è consentita solo al ruolo di retention di F6, con una riga di audit (DA-E2-11 (a), decisa). La versione 0 di ogni prompt globale è il seed del repo; RLS su `tenant_id` con riga globale visibile in lettura. Una `learning_proposal` nasce solo da dati sintetici, da metadati aggregati o da un'istruzione scritta del titolare nel DPA, e mai attraversando tenant (E9). `change_note` passa lo stesso controllo dei dati personali dei template, in blocco, e ha una lunghezza massima `e2.change_note.max_chars` (proposta).

### 4.2 Eventi emessi
`prompt.version.created`, `prompt.version.activated`, `prompt.version.rolled_back` — payload: `prompt_key`, `tenant_id`, `from_version`, `to_version`, `actor` (pseudonimo). Bus: DX-03 (aperta).

### 4.3 Output del render
`{ text, prompt_key, version, template_hash, render_hmac }`. Due nomi distinti: `template_hash` è lo SHA-256 del template (nessun dato di cliente) e coincide con l'hash che E1 registra; `render_hmac` è l'HMAC-SHA-256 del testo renderizzato con una chiave per tenant, per correlazione in audit senza testo: il testo contiene dati dei clienti e un SHA-256 semplice di un dato breve sarebbe riconducibile al dato (E1, decisione del 2026-11-04). La chiave per tenant sta nella pagina credenziali (inserimento o sostituzione, mai rilettura) con rotazione a due chiavi valide in parallelo, con data di attivazione e disattivazione (DA-CV-23); distruggere la chiave rende l'hash non riconducibile. `render_hmac` non è scritto nelle tracce di E1.

## 5. Interfacce

- **Libreria di risoluzione** (usata da C1, Python): `resolve(key, tenant_id) → version` e `render(version, variables) → output`. In gravya-app i prompt erano letti da due linguaggi: la lezione che motivava il requisito non vale più con un solo linguaggio di backend (E16); se se ne aggiungesse un altro, serve un test di parità.
- **API di gestione:**
  - `GET /v1/prompts/{key}/versions` — elenco (metadati).
  - `POST /v1/prompts/{key}/versions` — crea versione (non la attiva).
  - `GET /v1/prompts/{key}/diff?from=N&to=M` — diff testuale unificato.
  - `POST /v1/prompts/{key}/activate` `{version}` — promozione.
  - `POST /v1/prompts/{key}/rollback` `{to_version?}` — default: versione attiva precedente; `to_version=0` = seed.
- **CLI di seed** (carica i seed del repo come versione 0) ed **esportazione dei dati di un tenant**: i dati di E2 di un tenant (`prompts`, `prompt_versions` con template, schema variabili, hash, `source`, `change_note`, `prompt_activations`) sono esportabili con lo strumento di esportazione in formato strutturato di F6, previsto sin da subito (E15). Il formato non è fissato qui (proposta del coordinator in attesa di conferma dell'utente).

## 6. Comportamento

**Flusso principale (nuova versione).**
1. Un attore autorizzato (A3) crea una versione; il sistema valida il template e `change_note` (variabili dichiarate = variabili usate; controllo dei dati personali, §7) e calcola `template_hash`.
2. Se l'hash coincide con una versione esistente, risponde con quella (idempotenza).
3. L'attivazione richiede un esito E3 registrato per quella versione (stesso `template_hash`) con **zero fallimenti bloccanti** (invariante, C7 (b); E6): obbligatorio per ogni versione. Per le versioni `learning_proposal` serve anche l'approvazione umana via C3 (DA-E2-07). Attivazione e rollback sono azioni di attori umani. L'attivazione aggiorna `active_version_id` e scrive `prompt_activations` in una sola transazione.
4. Emette l'evento; le cache dei runtime si invalidano.

**Fail-closed sulle scritture (DA-A3-07, DA-B2-04).** Creazione, attivazione e rollback avvengono solo se il record di decisione di A3 e la riga di `prompt_activations` sono salvati; altrimenti l'operazione è annullata e il puntatore attivo non cambia.

**Rollback.** Sposta il puntatore a una versione esistente con esito E3 registrato; non crea né cancella versioni. Il seed (v0) è sempre ripristinabile.

**Casi limite.**
- Variabile mancante al render → errore esplicito, nessun render parziale.
- Prompt di tenant assente → si usa il globale; se manca anche quello → errore, nessun fallback hard-coded.
- Promozione concorrente → lock sulla riga `prompts`; il secondo riceve `409`.
- Attivazione senza esito E3 registrato, o con un fallimento bloccante → rifiutata, `active_version_id` invariato.
- Versione referenziata da un'attivazione o da un trace → non cancellabile da attori applicativi; la cancella solo il ruolo di retention di F6, con audit.
- Scrittura da un attore AI → rifiutata (HSAR/P16 di gravya-app, Appendice A).
- **Variabili di piattaforma.** Nell'ondata 1, prima di A6, E2 le legge dall'istantanea versionata del repository tramite l'interfaccia comune (ripiego dichiarato, non soddisfa DX-22; E5): i valori «proposta da validare» valgono come primo valore valido, con segnale; i valori «da definire» hanno un valore di sviluppo ammesso solo fuori produzione. Se una variabile non è leggibile o non è valida (DX-17), scritture e render che ne dipendono sono bloccati, con segnale ad A5. Se la cache già popolata continui a servire entro l'ultimo TTL valido è un'eccezione a DX-17 non decisa: DA-E2-13; finché non è decisa vale il blocco.
- **Superadmin.** Può ripristinare il seed dei prompt globali. Di default vede solo metadati aggregati (conteggi, versioni, hash). Lettura del testo, attivazione e rollback di un prompt di un'agenzia sono possibili solo (a) per un incidente dichiarato dal superadmin, che abilita direttamente l'accesso, con riferimento all'incidente; (b) su accesso concesso dall'admin agenzia come parte di una richiesta di assistenza, con riferimento alla richiesta (E8 e aggiunta dell'utente). In entrambi i casi l'accesso ha perimetro e durata (`access.superadmin_trace_access_ttl_hours`), passa da A3, registra l'attore in `prompt_activations` e una riga nel log degli accessi di A6 (DX-18); se il log non si salva, l'operazione è rifiutata. Gli admin delle agenzie sono confinati al proprio tenant da RLS.

## 7. Requisiti non funzionali

- **Performance:** `resolve`+`render` da cache entro `e2.resolve_render_p99_ms`; propagazione di un rollback entro `e2.rollback.propagation_max_s`.
- **Variabili di piattaforma (DX-13, DX-22).** Nessun valore è nel codice. Variabili di E2: `e2.cache.max_ttl_s`, `e2.rollback.propagation_max_s`, `e2.resolve_render_p99_ms`, `e2.change_note.max_chars` (proposta) e le durate di retention delle classi sotto. Il controllo dei dati personali nei template e in `change_note` **non è una variabile**: è sempre `block` (invariante, C7 (a)). `e2.cache.max_ttl_s` non è attivabile in produzione senza un intervallo minimo-massimo deciso (D4, regola 11 del catalogo; valori con A5 e A6): l'ondata 1 non va in produzione (DA-CV-20). Ogni modifica è versionata e auditata. La cache è in-process con invalidazione su evento (DA-E2-10 (a), decisa); finché il bus è aperto (DX-03) vale il solo TTL.
- **Sicurezza e conformità (PV-01).**
  - *Perimetro dati.* Registry in PostgreSQL di Gravya, self-hosted nell'UE (DA-B1-06). Il testo renderizzato è consegnato a C1 e da questo a B1, che lo inviano solo a destinazioni dichiarate: extra-UE solo con opt-in dell'agenzia, strumento di trasferimento e stato validi; ogni destinazione, anche UE, con sub-responsabile autorizzato (riferimento al DPA, data), impostati dal superadmin con fonte e audit (DA-B2-07, DA-CV-19; GDPR art. 28(2) e (4), Cap. V). Il Data Privacy Framework copre solo le organizzazioni USA dell'elenco DPF ed è impugnato (C-703/25 P). Il giudice LLM dei controlli E3 elabora nell'UE (DA-E3-09).
  - *Cifratura e backup.* Cifratura a riposo e in transito e gestione delle chiavi sono di A6; backup di F6 (art. 32(1) GDPR; Reg. 2024/2690 all. 9 e 4.2). I backup scadono entro `retention.data_backup_days`; al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22).
  - *GDPR — ruolo.* Gravya è responsabile (art. 28) per i template e i dati dei tenant; titolare per i dati dei propri utenti (DA-A1-08). I template dei tenant sono dati dell'agenzia e per l'accesso del superadmin vale DX-19 (E8).
  - *GDPR — minimizzazione (art. 5(1)(c), art. 25).* Il registry conserva template e metadati, mai testi renderizzati con dati dei clienti. Template e `change_note` non devono contenere dati personali: controllo in validazione su pattern base (email, telefono), sempre in blocco; non garantisce l'assenza di dati personali (Appendice B). Dati personali trattati: identificativo pseudonimo di chi crea o attiva (`created_by`, `actor`). Un identificativo pseudonimo resta dato personale (considerando 26; le linee guida EDPB 01/2025 sono solo in consultazione). La mappa di re-identificazione non è in E2: è classe `retention.pseudonym_map_months` (F6); la regola «la richiesta di cancellazione del titolare elimina la riga della mappa entro il termine del DPA» è proposta in DECISIONS §4. Le proposte automatiche non usano dati di tenant oltre quanto indicato in §4.1 (E9; art. 28(3)(a) e 28(10)).
  - *GDPR — retention e diritti.* Politica unica DX-09 (DECISIONS §5); le durate sono di sola lettura finché non esiste l'intervallo del DPA, con valore per agenzia `retention.<classe>.tenant_value` solo per le classi che sono dati dell'agenzia. Classi di E2: (1) versioni e puntatori (`prompt_versions`, `prompts`): artefatti di configurazione, durata del servizio, attore pseudonimo, nessuna variabile di durata; (2) `prompt_activations` e `prompt_eval_outcomes`: `retention.audit_decisions_months` (assegnazione di `prompt_eval_outcomes` da validare); (3) eventi `prompt.version.*`: `retention.runtime_events_days` (assegnazione da validare); (4) segnali ad A5: `retention.incident_signals_months`, sempre prodotti e conservati (C2), durata provvisoria fissata dall'utente prima della produzione (DA-CV-20); (5) evidenze di incidente: `retention.incident_evidence_months`, sospensione non attivabile finché massimo, riesame e categorie non sono definiti e solo per dati di Gravya; per i dati delle agenzie serve istruzione nel DPA e parere legale prima di F6 (DA-CV-21); (6) log degli accessi cross-tenant: `retention.cross_tenant_access_log_months` (A6). **Fine contratto** (DECISIONS §5, Data Act art. 25(2), registro v1.6): export dei prompt del tenant, con lo strumento di F6, disponibile per tutto il periodo di uscita (`retention.tenant_offboarding_days`, minimo di recupero di almeno 30 giorni dopo il periodo di passaggio), poi cancellazione; la scelta restituzione o cancellazione spetta all'agenzia (`retention.tenant_offboarding_choice`, sempre disponibile). La qualificazione del SaaS come «servizio di trattamento dei dati» è da confermare con un legale. Assistenza all'agenzia su richieste degli interessati: `dsar.assist_max_days` (obbligo del DPA).
  - *NIS2 (ready by design, DX-10; Gravya oggi non è soggetto NIS2).* Log e controllo accessi: Reg. (UE) 2024/2690, allegato 3.2 (registrazione, anche degli accessi privilegiati e delle attività amministrative, 3.2.3(e)) e 11.2-11.3 (privilegio minimo, riesame), come requisiti di progetto. Gestione delle modifiche con test e valutazione prima dell'attuazione (allegato 6.4): gate di promozione. Integrità: `template_hash` e immutabilità a livello DB. Notifica incidenti: flusso presente ma non attivo (`incident.nis2_flow_active`); preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, decorrenza dalla conoscenza: tutto di A5. E2 invia ad A5 un segnale per ogni scrittura non autorizzata, ogni modifica del prompt attivo fuori flusso e ogni variabile non leggibile; i segnali portano identificativi e motivo, non testi, e sono esclusi dal blocco (DA-CV-17).
  - *AI Act (art. 50 applicabile dal 2.8.2026; DX-11: non alto rischio).* Etichetta «generato da AI» (non disattivabile dal tenant), informativa a chi interagisce con un'IA (art. 50(1)) e marcatura leggibile da macchina anche del testo (art. 50(2), nei limiti tecnici del canale) sono invarianti (catalogo §18) **applicate dal codice di C1 e dei connettori** (D1-D4) e verificate da E3; il preambolo del prompt (anti-invenzione) non le sostituisce: il modello può ometterle e un template modificabile non è una garanzia. DA-E2-03 (b) è condizione dell'invariante. E2 espone `prompt_ref` (chiave, versione, `template_hash`) per il campo `ai_generated` di C1. Il dettaglio di marcatura del testo del Codice di buone pratiche non è verificato (DA-C1-07). Artt. 12, 14, 19, 26: solo buona pratica (DX-11), e per l'alto rischio dal 2.12.2027; qui: attivazione e rollback solo umani, registrazione di versione e attivazione con attore e motivo.
  - *Marketing (PV-01).* E2 non invia verso terzi; consensi, opt-out, art. 130 Codice privacy e ePrivacy sono di D1-D4.
  - *Isolamento.* RLS per tenant; scritture solo con attore autorizzato da A3.
- **Portabilità:** template in formato testuale; export con lo strumento di F6; nessuna dipendenza da SaaS di prompt management.
- **Osservabilità AI:** ogni chiamata LLM è attribuibile a `prompt_key`+`version`+`template_hash` nel record di traccia di E1; attivazioni e rollback sono interrogabili in SQL e correlabili alle tracce.

## 8. Criteri di accettazione

1. **Immutabilità:** UPDATE e DELETE su `prompt_versions` da un ruolo applicativo → entrambi falliscono a livello DB; DELETE dal ruolo di retention di F6 riesce e scrive una riga di audit.
2. **Rollback:** attiva v2, rollback, `resolve` restituisce v1 entro `e2.rollback.propagation_max_s`; `prompt_activations` ha 2 righe.
3. **Seed ripristinabile:** `rollback to_version=0` restituisce testo byte-identico al seed del repo (confronto di `template_hash`).
4. **Isolamento:** con due tenant, il tenant A non legge né modifica versioni del tenant B (0 righe, `403/404`).
5. **Template fail-closed:** render con variabile mancante → errore.
6. **Diff:** `GET diff` tra due versioni note restituisce l'unified diff atteso (snapshot test).
7. **Nessun prompt nel codice:** check in CI (grep/lint sui pattern di DA-E2-03) sui moduli migrati → 0 occorrenze; i seed del registry non contengono il preambolo fisso.
8. **Tracciabilità:** in un test end-to-end ogni record di traccia delle chiamate LLM ha `gravya.prompt.key`, `gravya.prompt.version` e `gravya.prompt.hash` uguale al `template_hash`; nessun record di E1 contiene `render_hmac`.
9. **Portabilità:** export di un tenant con lo strumento di F6 (o il suo stub) → import su DB vuoto → stesso insieme di `template_hash`.
10. **Fail-closed:** con il salvataggio del record A3 o della riga `prompt_activations` forzato a fallire, attivazione e rollback sono rifiutati, `active_version_id` invariato, nessuna versione creata.
11. **Segnale ad A5:** una scrittura non autorizzata produce un segnale verso A5 (o il suo stub), senza testi né valori.
12. **Accesso del superadmin:** senza incidente dichiarato né accesso concesso dall'admin agenzia, la lettura del testo, l'attivazione e il rollback di un prompt di tenant sono rifiutati; con uno dei due, producono 1 riga nel log degli accessi con il riferimento; con il log forzato a fallire sono rifiutati; scaduta la durata (`access.superadmin_trace_access_ttl_hours`) l'accesso è rifiutato; l'admin di un'altra agenzia riceve `403/404`.
13. **Variabili:** cambiando `e2.rollback.propagation_max_s` senza rilascio, E2 applica il nuovo valore e la modifica è versionata e auditata; con la variabile non leggibile le scritture sono rifiutate e parte un segnale.
14. **Controllo dei dati personali:** un template o una `change_note` con un'email o un telefono è rifiutato; nessuna configurazione o parametro di richiesta consente di attenuare il blocco (test sulla superficie di configurazione); `change_note` oltre `e2.change_note.max_chars` è rifiutata.
15. **Gate di promozione:** senza esito E3 registrato, o con almeno un fallimento bloccante, l'attivazione è rifiutata e `active_version_id` non cambia; un esito con `template_hash` diverso dalla versione non vale; una versione `learning_proposal` non è attivabile senza approvazione umana.
16. **Intervallo richiesto:** avviando E2 in produzione senza un intervallo deciso per `e2.cache.max_ttl_s`, o con un valore di sviluppo, l'avvio fallisce con errore esplicito (proposta; la guardia di produzione è un'invariante di deploy, catalogo §18).
17. **Retention:** ogni tabella di E2 è associata a una classe del catalogo (test con F6 o il suo stub); l'export di un tenant resta eseguibile per tutto il periodo di uscita.
18. **Hash del render:** due render dello stesso testo per tenant diversi producono `render_hmac` diversi; dopo la sostituzione della chiave per tenant (due chiavi in parallelo) il vecchio e il nuovo `render_hmac` sono verificabili finché la vecchia chiave è attiva.

## 9. Piano di implementazione

**Fasi (ordinate):**
1. Decisioni DA-E2-01..04, 12, 13.
2. Schema e migrazioni PostgreSQL con trigger di immutabilità, ruolo di retention e RLS.
3. Renderer di template (DA-E2-02) e validazione variabili, in Python.
4. API di gestione, diff, rollback; CLI seed; controllo dei dati personali condiviso con E3.
5. Lettura delle variabili dall'istantanea del repository (ripiego, poi A6) e log degli accessi cross-tenant.
6. Cache in-process con invalidazione su evento; attributi su E1; segnali ad A5.
7. Seed v2 per i prompt nel perimetro (DA-E2-03, DA-E2-08) e check CI.
8. Verifica dell'esito E3 all'attivazione; HMAC del render con chiave per tenant.

**Tecnologie (dal master o da decidere):** PostgreSQL con RLS (DA-A1-01), Python (E16), SHA-256 per il template, HMAC-SHA-256 per il render. ORM e migrazioni con F1. Il motore di template non è nel master (DA-E2-02). Nessun uso di Redis per la cache (DA-E2-10 (a)).

## 10. Test e valutazione

- **Unit:** render, validazione variabili, controllo dei dati personali (template e `change_note`), hash e HMAC, diff.
- **Integration (PostgreSQL reale):** immutabilità e ruolo di retention, RLS, rollback, concorrenza, gate di promozione.
- **Eval:** il gate è un esito registrato da E3 in CI e verificato da E2 all'attivazione; E2 non implementa eval né chiama E3.
- **Security:** scrittura con attore non autorizzato (segnale ad A5); fail-closed con record A3 o attivazione forzati a fallire; template injection (una variabile con sintassi di template non è rivalutata); accesso del superadmin per le due vie, con e senza log; tentativo di attenuare il blocco dei dati personali.

## 11. Rischi e mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| Prompt dispersi nel codice (fallback e prompt hard-coded di gravya-app) | Alto: verità divisa | Un solo punto di risoluzione, nessun fallback, check CI (§8.7); DA-E2-03 |
| Cache stantia dopo rollback | Medio | Invalidazione su evento; `e2.cache.max_ttl_s` con intervallo deciso prima della produzione; DA-E2-13 |
| Dati personali in template o `change_note` | Alto (GDPR) | Blocco sempre attivo su pattern base, lunghezza massima, contenuti mai catturati in produzione (DA-E1-02); limite del controllo dichiarato |
| Hash del render riconducibile al dato | Alto (GDPR) | HMAC con chiave per tenant, due chiavi in rotazione, mai nelle tracce |
| Etichetta o informativa art. 50 omesse o rimosse | Alto (AI Act) | Applicate dal codice di C1 e dei connettori, verificate da E3; il preambolo non le sostituisce |
| Versione attivata senza valutazione | Alto | Esito E3 registrato obbligatorio per ogni versione, legato al `template_hash`; test §8.15 |
| Scrittura riuscita con audit non salvato | Alto (integrità, Reg. 2024/2690 all. 3.2) | Fail-closed in transazione unica (DA-A3-07, DA-B2-04); test §8.10 |
| Abuso dell'accesso superadmin ai prompt dei tenant | Alto (GDPR art. 28, all. 11.3) | Solo incidente dichiarato o accesso concesso dall'agenzia, con durata, riferimento e log fail-closed; passaggio da A3; segnale ad A5 |
| Proposte automatiche che usano dati di tenant | Alto (GDPR art. 28(10)) | Fonti ammesse limitate (§4.1), mai tra tenant |
| Immutabilità in conflitto con cancellazione a fine contratto o richiesta dell'interessato | Alto (GDPR art. 17, 28(3)(g)) | Ruolo di retention di F6 con audit (DA-E2-11 (a)); pseudonimo al posto del nome |
| Variabile di piattaforma modificata male | Medio | Modifica versionata e auditata, intervallo deciso, fail-closed (DX-13, DX-17); test §8.13 |
| Rottura cache del prefisso prompt (#1781) | Medio: costo | Render deterministico; test di stabilità byte |

## 12. Stima e priorità

- **Dimensione:** M. Schema e API semplici; la complessità è nei seed v2, nel gate con esito registrato e nei controlli di conformità §7. Le decisioni del 2026-11-04 aggiungono HMAC del render, ruolo di retention e regole di accesso, senza cambiare la taglia; un solo linguaggio (E16) la riduce.
- **Dipendenze critiche:** F1 (o schema minimo), A3, E1, A6 per variabili e identità, E3 per l'esito del gate, C1 per la risoluzione.
- **Thin-slice MVP:** **Sì**, ondata 1.

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è materiale di riferimento (PV-03): nessun file, tabella o dato entra in v2 da qui. I punti seguenti sono ripresi dalla versione 1.4 del documento e non sono stati riletti nel codice in questa versione (Appendice B).

**Idee da riprendere:**
- `gravya_supervisor_prompt_revisions.ts` e migrazione `0322`: storico before/after con RLS ENABLE+FORCE per azienda.
- `learning-proposal-apply.ts`: stale guard e revisione nella stessa transazione, per l'attivazione atomica.
- `llm/prompt-hash.ts`: SHA-256 troncato a 16 caratteri, testo mai nell'audit (qui superato per il render: HMAC per tenant).
- `kloud_config.py` / `router.py`: blocco anti-invenzione non sovrascrivibile dal DB (P11): parte fissa nel codice per vincoli di sicurezza.
- `gravya-app-kloudify/docs/visione/README.md` P12 (prompt nel DB, seed nel repo, ripristino superadmin) e P16 (`system_prompt` solo umani); `architettura-agenti.md` §2.8.

**Difetti da non ripetere:** prompt sparsi (fallback `_default_system_prompt()`, `card_analyzer.py:113`); storico senza versione, puntatore, rollback né diff; prompt degli esecutori in un'altra tabella; cache con TTL 60 s senza invalidazione su evento; nessun motore di template né ADR sui prompt.

**Divergenze dal master plan:** prompt esterni al codice, ma il preambolo fisso resta nel codice (DA-E2-03); templating senza motore indicato (DA-E2-02); criteri di qualità versionati col prompt e attivazione solo umana non previsti dal master; OpenTelemetry sostituito da tracing DB-native (PV-02).

## Appendice B — Non verificato

- Il contenuto dell'Appendice A (file, funzioni e valori di gravya-app e kloudify) non è stato riletto in questa versione; l'elenco completo dei prompt hard-coded in `services/agents` non è noto.
- Lingua dei prompt v2 (P12 diceva inglese); stato delle issue #1801, #1494, #1781.
- Nomi `template_hash` e `render_hmac` e attributo `gravya.prompt.hash` (= `template_hash`): da allineare con E1 e B2.
- Copertura del controllo dei dati personali: i pattern base (email, telefono) non rilevano altri dati personali (dedotto).
- Validità nel tempo di un esito E3 registrato (per esempio se cambia il dataset) e gate per il rollback verso il seed v0 (esito del rilascio che lo contiene: da confermare con E3).
- Regola sulla mappa degli pseudonimi (DECISIONS §4); applicazione di `access.superadmin_trace_access_ttl_hours` ai prompt (dedotta dall'aggiunta dell'utente a E8).
- Intervallo di `e2.cache.max_ttl_s` (D4: valori con A5 e A6); intervallo di `e2.rollback.propagation_max_s`, che D4 non richiede ma con lo stesso rischio di una cache stantia.
- Classe di retention degli eventi `prompt.version.*` e di `prompt_eval_outcomes`; perimetro per agenzia di `audit_decisions_months` e `runtime_events_days` (dedotto nel catalogo).
- Dettaglio della marcatura del testo del Codice di buone pratiche art. 50 (registro §9.1: testo non letto); eccezione per funzione assistiva di editing (art. 50(2)) non valutata.
- Formato dello strumento di esportazione di F6 (proposta in attesa di conferma); qualificazione del SaaS come servizio di trattamento dei dati (Data Act); ambito NIS2 di Gravya, non accertato (DX-10).
- Contratto dei segnali verso A5 (tabella di audit minima in ondata 1); compatibilità delle durate con i contratti delle agenzie; volumi (numero di prompt, versioni, render): nessun dato.

## Appendice C — Decisioni aperte

- **DA-E2-01 — Modello dati:** (a) tabelle generiche come in §4.1; (b) colonne di prompt dentro le entità che li usano, con tabella di storico. Criterio: un'unica verità, immutabilità, rollback. Raccomandazione: (a). Aperta in DECISIONS.
- **DA-E2-02 — Motore di template:** (a) sostituzione `{{var}}` senza logica, in Python; (b) motore con logica (Jinja-compatibile); (c) solo concatenazione nel codice. Criterio: sicurezza, assenza di lock-in. Raccomandazione: (a). Aperta in DECISIONS.
- **DA-E2-03 — Perimetro del registry:** (a) tutti i prompt; (b) supervisori, esecutori e Kloud, con il preambolo fisso (anti-invenzione) nel codice; (c) sottoinsieme minimo per lo skeleton. Criterio: un'unica verità; le invarianti art. 50 sono applicate dal codice di C1 e dei connettori in ogni caso. Raccomandazione: (b). Aperta in DECISIONS.
- **DA-E2-04 — Approvazione umana via C3 per le versioni scritte da umani.** Il gate E3 per ogni versione è deciso (E6, 2026-11-04); resta: (a) basta l'attore umano che attiva; (b) approvazione di una seconda persona via C3. Criterio: sorveglianza umana (buona pratica, DX-11), Reg. 2024/2690 all. 6.4. Raccomandazione: (b). Aperta in DECISIONS per questa parte.
- **DA-E2-05 — Anticipo rispetto alla Beta:** **Decisa** (DX-01). E2 è nell'ondata 1.
- **DA-E2-06 — Retention di versioni e attivazioni:** **Assorbita da DX-09**; classi in §7.
- **DA-E2-07 — Versioni proposte da AI:** **Decisa (2026-11-03, utente)**: ammesse come candidate, mai attivabili senza un umano; attivazione tramite gate E3 e approvazione umana via C3. Fonti ammesse: E9 (2026-11-04).
- **DA-E2-08 — Testi dei seed:** **Decisa (2026-11-03, utente)**: testi di gravya-app come bozza, rivisti contro i contratti v2 e ripuliti dai residui della visione precedente; approvati come versione 0.
- **DA-E2-09 — Visibilità del superadmin sui template dei tenant:** **Decisa (E8, 2026-11-04, utente)** con l'aggiunta dell'utente: metadati aggregati di default; lettura, attivazione e rollback solo per incidente dichiarato dal superadmin o su accesso concesso dall'admin agenzia in una richiesta di assistenza, con log (§6).
- **DA-E2-10 — Cache dei prompt:** **Decisa (E13, 2026-11-04, utente)**: (a) in-process con invalidazione su evento e TTL.
- **DA-E2-11 — Cancellazione di versioni immutabili:** **Decisa (E13, 2026-11-04, utente)**: (a) solo il ruolo di retention di F6, con audit.
- **DA-E2-12 — Come l'esito E3 arriva in E2.** (a) E3 esporta in CI un artefatto con versione, `template_hash`, esito e data, importato nel registry da un passo di rilascio; (b) E3 scrive direttamente nel database del registry. Criterio: E3 gira su un DB non di produzione (E3 §2) e non deve avere accesso ai dati reali. Raccomandazione: (a), da concordare con E3.
- **DA-E2-13 — Cache con variabile illeggibile — DA RIPORTARE ALL'UTENTE.** (a) blocco di scritture e render, DX-17 alla lettera; (b) la cache già popolata continua a servire entro l'ultimo TTL valido, con segnale ad A5 (eccezione a DX-17). Criterio: DX-17 (decisa) contro la disponibilità dei runtime; la staleness è limitata dall'ultimo TTL valido. Raccomandazione: (b). Finché non è decisa vale (a).

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi di span allineati a E1 (`gravya.prompt.*`); C3 spostato da "È richiesto da" a "Dipende da" (verso invertito: è E2 a usare C3 per la promozione) e aggiunta la dipendenza condizionale da E3; aggiunti C1 e A1 in "È richiesto da"; corretta l'affermazione che il master citi Redis Stream/Kafka (non li cita) e rimando a DA-A1-03. Motivo: interfacce e dipendenze non allineate, affermazione non supportata. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (conformità prioritaria, niente OpenTelemetry). Attributi `gravya.prompt.*` su record di traccia DB-native di E1 anziché span; §7 con voce "Sicurezza e conformità" (GDPR, NIS2 art. 21, AI Act art. 50, osservabilità AI); rimossi riuso e migrazione da gravya-app (storico 0322, Drizzle, librerie esistenti) e il vincolo Beta; Appendice A rinominata "Riferimenti dal sistema precedente" (idee e difetti da non ripetere); DA-E2-01 e DA-E2-03 riformulate, DA-E2-05 chiusa da DX-01, nuove DA-E2-06..08 da riportare all'utente; rischio "doppio registry" sostituito; taglia M confermata per costruzione da zero. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. Diventano scelte del documento: DA-A1-01 (PostgreSQL+RLS), DA-B1-06 (self-hosted UE), DA-E1-02 (contenuti mai in produzione), DA-E1-05 (vocabolario GenAI semconv/traceparent ammesso per E1, senza SDK), DA-A3-07 e DA-B2-04 (fail-closed sulle scritture: nuova regola §6, criterio §8.10, test §10, rischio §11), DA-E3-08/09 e DA-C1-05 (nessun SaaS, eval su dati sintetici con giudice UE). DA-E2-06 assorbita da DX-09: rimossa la retention propria, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica incidenti ad A5, E2 invia segnali; nuovo criterio §8.11) e DX-11 (responsabile art. 28; sorveglianza umana e log ridotti a buona pratica, art. 50 confermato). Tolte dall'Appendice B le ipotesi decise (regione hosting, classificazione AI Act). Taglia M invariata. Motivo: allineamento a DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: durate di default di DECISIONS.md §5 assegnate alle classi di dati di E2 in §7 (versioni e puntatori per la durata del servizio, attivazioni 12 mesi, eventi 90 giorni da validare, log accessi 12 mesi, evidenze di incidente), DA-E2-06 aggiornata, criterio §8.14. DX-13: soglie di E2 (TTL cache, propagazione rollback, modalità controllo PII, durate) diventano variabili di piattaforma del superadmin, versionate, auditate e fail-closed (§7, §6, §8.2, §8.13, rischio §11); accesso cross-tenant solo come superadmin entro le istruzioni del titolare e con log degli accessi fail-closed (§6, §7, §8.12, §10, rischio §11). DECISIONS.md §6 decisa: base giuridica degli identificativi degli attori (agenzia per i suoi utenti, Gravya per superadmin e operatori), tolta dall'Appendice B. Dipendenze aggiunte: F6 (DX-12) e registro delle variabili, con proprietario A6 solo proposto (DX-14 da riportare). Le altre righe della §6 non citano E2. Taglia M invariata. Motivo: allineamento a DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento a DECISIONS (C1-C14, D1-D8, DA-CV-18..23), catalogo delle variabili v1.2 e registro delle norme v1.6. Controllo dei dati personali sempre `block` (invariante, C7 (a)); gate E3 senza fallimenti bloccanti (C7 (b)) e criterio §8.15; valori fissi sostituiti con i nomi del catalogo (§7, §8) e intervallo richiesto per `e2.cache.max_ttl_s` (D4); art. 50(1), art. 50(2) e etichetta come invarianti fuori dai prompt (D6, D7); provider come sub-responsabili con destinazione dichiarata (DA-CV-19); «legal hold» sostituito da evidenze di incidente (DA-CV-21) e «NIS2 (art. 21)» per i log da Reg. 2024/2690 all. 3.2 e 11, con flusso NIS2 presente ma non attivo e segnali sempre conservati; DX-17 per le variabili non leggibili; fine contratto secondo il Data Act (D2); backup (DA-CV-22); mappa degli pseudonimi; A6 deciso (DX-14); DA-E2-07 e DA-E2-08 segnate decise; nuove DA-E2-09..11; testo tagliato e Appendice A segnata come non riletta. Motivo: un solo passaggio di allineamento prima dell'unica revisione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 del 2026-11-04 e revisione unica della v1.5. E1: `content_hash` sostituito da `template_hash` (SHA-256, l'unico registrato da E1) e `render_hmac` (HMAC con chiave per tenant, rotazione a due chiavi); E6: C1 risolve il prompt e passa il testo al job, gate E3 obbligatorio per ogni versione con esito registrato verificato da E2 all'attivazione (nuova tabella `prompt_eval_outcomes`, criterio §8.15, DA-E2-12); E8 con l'aggiunta dell'utente: accesso del superadmin ai prompt di un'agenzia (lettura, attivazione, rollback) solo per incidente dichiarato o su accesso concesso dall'admin agenzia in una richiesta di assistenza, con riferimento, durata e log (DA-E2-09 decisa, criterio §8.12); E9: fonti ammesse per `learning_proposal`; E13: DA-E2-10 (a) e DA-E2-11 (a) decise, ruolo di retention di F6; `change_note` con il controllo dei dati personali e lunghezza massima (proposta); avvisi art. 50 applicati dal codice di C1 e dei connettori, non dal preambolo; cache con variabile illeggibile come decisione aperta (DA-E2-13); E5: variabili dall'istantanea del repository prima di A6; E11: cifratura e chiavi ad A6, backup a F6; E16: backend in Python, test di parità TS/Python tolto; E15: esportazione dei dati di E2 con lo strumento di F6; DA-E2-04 ridotta all'approvazione via C3; note «non ancora in DECISIONS» tolte. Motivo: portare il documento allo stato delle decisioni dell'utente e dei rilievi di plan-auditor (R5, R12, R13) e compliance-auditor (R-01, R-02, R-03, R-04, R-08, R-09). |
