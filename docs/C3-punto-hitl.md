# C3 — Punto HITL

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C3 |
| Nome | Punto HITL (Human-in-the-Loop) |
| Componente padre | C — Orchestrazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.5 |
| Data | 2026-11-04 |

## 2. Scopo

**Cosa fa.** Il master plan lo definisce come "nodo di approvazione umana con UI di revisione e payload di contesto" (Piano generale §6, Componente C). In pratica C3 mette in pausa un run del grafo (C1) prima di un'azione irreversibile, cioè un invio o la modifica di un record. Salva la chiamata esatta da eseguire (tool e argomenti), la espone a una persona insieme al contesto e riprende il run in base alla decisione. Dopo un'approvazione la chiamata viene eseguita **una sola volta** e **con gli argomenti che la persona ha visto**.

**Cosa NON fa.**
- Non è la coda di revisione G2 (ondata 2). C3 espone solo l'interfaccia minima di §5.
- Non decide *se* un'azione richiede approvazione: lo stabiliscono la policy (A3, esito `require_approval`) e l'impostazione per azienda, cliente e task. C3 applica il risultato.
- Non approva testo libero: si approva **l'azione (il tool), non il testo** (kloudify, `docs/visione/controlli-e-conformita.md` §2).
- Non verifica base giuridica, consenso o opt-out del destinatario di un invio (diritto del marketing: D1-D4).
- Non decide l'autonomia graduata: è fuori ondata 1.

**Perché esiste.** Senza C3 non è possibile concedere agli agenti la scrittura in sicurezza. Il principio P7 (kloudify, `docs/visione/README.md`) parte da "approvazione richiesta".

## 3. Contesto e dipendenze

**Dipende da:**
- **C1** (grafo che ospita il nodo) e **B5** (checkpointer, ondata 2: `interrupt()` richiede uno stato persistito; DX-08 aperta).
- **A3** (esito `require_approval`; `tool_class` arriva da B2 dal catalogo, A3 non lo assegna) e **B2** (esegue il tool approvato, verifica il token monouso).
- **E1** (tracce DB-native delle transizioni) e **A5** (audit della decisione e destinatario dei segnali, ondata 2). In ondata 1 la conferma del salvataggio dà la tabella di audit minima che A5 assorbirà (DECISIONS §6).
- **A6** (ondata 2, DX-14 decisa): identità e ruoli, MFA, registro versionato delle variabili, log degli accessi cross-tenant (DX-18), pagina credenziali.
- **F1** (tabelle con `company_id` e RLS) e **F6** (ondata 2, DX-12): applica la retention.

**È richiesto da:** C1 (semantica del nodo `hitl`), A3 e B2 (`require_approval` e token monouso), E3 (casi che arrivano all'HITL), E2 (promozione di un prompt, solo se DA-E2-04 sceglie (b)), G2 (UI coda, ondata 2), D1-D3 (scritture CRM, ads, email con HITL), C4 (dead-letter dei casi scaduti o falliti), E4 ed E5 (metriche di rifiuto).

**Assunzioni:**
- v2 si costruisce da zero (DX-01, PV-03): i riferimenti a gravya-app sono idee e lezioni, non codice.
- Motore LangGraph come libreria self-hosted in UE, senza LangSmith né LangGraph Platform (DA-C1-01, DA-C1-05, DA-B1-06). Il nodo HITL gira nel servizio di orchestrazione, non nei job B1 (DECISIONS §6).
- Il checkpointer è Postgres; la scelta spetta a B5 (DX-08).
- Il default è "approvazione richiesta": variabile `hitl.approval_required_default`. Il default di piattaforma è di sola lettura (DA-CV-15); se la policy non è risolvibile vale "richiesta" (fail-closed, DX-17).
- Nessun valore è fisso nel codice (DX-22): ogni durata, soglia o limite è una variabile di `docs/catalogo-variabili.md`, citata qui per nome.
- **Invarianti (catalogo §18):** le classi `ALWAYS_HITL` e `MONEY_WRITE` richiedono sempre approvazione umana e non sono declassabili da UI (DECISIONS §7, DA-CV-05, DA-CV-15). Per i contenuti verso terzi (email, post, messaggi per conto delle agenzie) non sono una classe `ALWAYS_HITL` nell'ondata 1: decide l'admin agenzia tramite `hitl.approval_required_default`, con audit dell'attore (DA-CV-18; da riesaminare con D1-D4). Fail-closed, token monouso e MFA (DX-20) sono invarianti.

## 4. Contratti

**4.1 Payload di interrupt** (modellato su `services/agents/src/kloud/hitl_types.py` di gravya-app; formato condiviso: DA-C3-03). Unione discriminata su `type`:
- `approval_required`: `task`, `preview`, `supervisor?`, `structured_data`, più:
  - `ai_generated` (`model`, `prompt_ref`): obbligatorio per i contenuti generati dall'AI, definito nel contratto di output dei nodi agent di C1 e **mostrato all'approvatore** (DECISIONS §6);
  - l'indicazione di marcatura leggibile da macchina (AI Act art. 50(2), invariante, anche per il testo: modalità e campi in C1 e D1-D4); C3 non la altera, perché gli argomenti eseguiti sono quelli approvati (AC-5);
  - `destination`: destinazione, giurisdizione e categorie di dati dichiarate nel catalogo di B2 (DA-B2-07), mostrate all'approvatore.
- `input_required`: gli stessi campi più `input_schema[]` (`key`, `label`, `type` ∈ {text, textarea, number, email, url, image_url, date, select, boolean, json}, `required`, `options?`, `default?`).

**4.2 Payload di ripresa:** `{approved: bool, feedback?: str}` oppure `{approved: true, input_data: {...}}`.

**4.3 Record di scrittura parcheggiata** (tabella nuova di v2). Campi minimi:

| Campo | Note |
|---|---|
| `id`, `company_id`, `run_id` (= thread LangGraph) | RLS FORCE |
| `tool_key`, `permission_key`, `arguments` (JSON) | la chiamata esatta mostrata alla persona |
| `context` | task, cliente, anteprima, riferimento alla traccia E1 |
| `status` | `pending` → `approved`/`rejected`/`cancelled` |
| `created_at`, `expires_at` | scadenza della richiesta (§6; quando `expires_at` si fissa: DA-C3-07) |
| `claimed_at`, `outcome` (`ok`/`refused`/`error` + codice) | garanzia di esecuzione unica; l'esito è riconciliato con l'audit di B2 (§6) |
| `decided_by_user_id`, `decided_at`, `feedback` | scritti solo da un actor `human`; l'identità è fornita da A6 (DX-21) |

`arguments` e `context` possono contenere dati personali (destinatari, contenuti di record CRM): valgono la minimizzazione di §7 e la classe `retention.sensitive_payload_days`; nella decisione resta solo l'hash degli argomenti. Anche `preview`, `structured_data` e `input_data` finiscono nel checkpoint (B5): seguono `retention.run_state_days`. `feedback` è testo libero e segue `retention.audit_decisions_months`: la card avverte di non inserirvi dati personali non necessari.

**4.4 Eventi emessi:** `hitl_requested`, `hitl_approved`, `hitl_denied`, `hitl_input_provided`, `hitl_expired`, `hitl_outcome`. Di questi gravya-app ha `hitl_denied`, `hitl_input_provided` e `hitl_approved`; gli altri nomi sono **proposta da validare**. Gli altri documenti dell'ondata 1 usano nomi puntati (`tool.*`, `workflow.*`): il formato è la decisione aperta DX-07. C1 emette `workflow.run.interrupted` verso C3; in gravya-app il segnale passa per `interrupt()` di LangGraph. Gli eventi sono registrati nel modello DB-native di E1 (PV-02), senza SDK né export OpenTelemetry; per i nomi degli attributi E1 può usare il vocabolario GenAI semantic conventions e `traceparent` (DA-E1-05). Ogni transizione registra la `config_version` in vigore (DX-21).

## 5. Interfacce

Interfaccia minima che C3 espone; G2 la consumerà senza aggiungere logica.

| Operazione | Chiamante | Riferimento in gravya-app (solo idea) |
|---|---|---|
| Parcheggia una chiamata | B2 (esito `require_approval` di A3) o run: dipende da DX-05, aperta | `POST /companies/:companyId/kloud/approvals` (`kloud-approvals.ts`) |
| Elenca le richieste `pending` dell'azienda | persona | pagina approvals (`approvals.ts`, non letta in dettaglio) |
| Decidi (approva, rifiuta, fornisce input) e riprendi | persona con ruolo abilitato da A6 e MFA (DX-20); chi è abilitato: DA-C3-10 | `resumeKloudThread` → `POST /api/v1/resume/:taskId` firmato HMAC (`kloud-resume.ts`) |
| Claim esclusivo | chi esegue | `POST .../approvals/:approvalId/claim` (`runOnly`) |
| Emetti il token monouso (solo dopo il claim, legato all'hash degli argomenti approvati) | C3; verificato da B2 e A3 | `write_replay.py` |
| Esito | chi esegue; riconciliato con l'audit di B2 | `POST .../approvals/:approvalId/outcome` |
| Risolvi la policy di approvazione | servizio | `kloud-approval.ts`: task → cliente → azienda → default |
| Scadenza (job periodico) | servizio | `kloud-hitl-expiry-sweeper.ts`; scheduler: DA-C3-11 |
| Lettura delle variabili | servizio | registro di A6 |

La chiave HMAC di resume e la firma del token monouso stanno nella pagina credenziali di A6 (catalogo §15; sostituzione senza interruzione: DA-CV-23). In ondata 1 la UI è una card minima per `approval_required` e `input_required`, sul modello di `AskKloud.tsx`: mostra `ai_generated`, `destination` e gli argomenti esatti. Endpoint e nomi di v2 si definiscono sul contratto nuovo.

## 6. Comportamento

**Flusso principale.**
1. Un tool classificato `REQUIRES_HITL` o `MONEY_WRITE` nel catalogo di B2 (o una policy di approvazione risolta a "richiesta") produce `require_approval`; chi parcheggia è deciso da DX-05.
2. La chiamata viene parcheggiata (`pending`) e il passo termina con `requires_hitl=true`.
3. `node_interrupt_check` valida il payload e chiama `interrupt()`; lo stato va nel checkpoint.
4. Decide un actor `human` con ruolo abilitato e MFA. Il superadmin non decide richieste di un tenant.
5. In caso di approvazione: claim, ricostruzione del tool dal catalogo, ricontrollo di scope e tetto di spesa, token monouso, chiamata unica tramite B2 (che chiede la decisione ad A3 con il token), esito.

**Casi limite.**
- **Payload malformato:** il nodo interrompe comunque (fail-closed).
- **Nessun checkpointer:** errore bloccante, non no-op (AC-2).
- **Doppio resume o replay del token:** il secondo claim riceve 409, la scrittura non si riesegue, segnale ad A5.
- **Scadenza (DA-C3-04, DA-C3-08).** Una richiesta `pending` o approvata ma non reclamata oltre `hitl.request_ttl_hours` diventa `cancelled`: è una **scadenza programmata**, non un'azione. Usa l'ultimo valore valido versionato (DX-17, DA-C3-08 (a)), emette `hitl_expired`, invia un segnale ad A5 e porta solo alla non esecuzione. Chiude anche il run in pausa (così lo stato scade con `retention.run_state_days` e C4 riceve il caso). Il TTL lo sceglie l'admin agenzia entro `hitl.request_ttl_hours_min` e `hitl.request_ttl_hours_max`; fuori intervallo il valore non è valido (DX-16). Una modifica del TTL sulle richieste già aperte: DA-C3-07. Il job gira ogni `hitl.sweeper_interval_minutes`.
- **Claim senza esito:** prima si controlla l'audit di B2; se la chiamata risulta eseguita si riconcilia l'esito reale, altrimenti `error/reaped`. Mai riesecuzione.
- **Variabile non leggibile o non valida (DX-17).** Le azioni (claim, ripresa, esecuzione) si bloccano; le cancellazioni programmate usano l'ultimo valore valido versionato; in entrambi i casi parte un segnale ad A5. Senza alcun valore valido vale il valore «deciso» del catalogo (DA-CV-17); se è «da definire» l'azione dipendente si blocca.
- **Audit o traccia della decisione non salvati (prima dell'esecuzione):** fail-closed (DA-B2-04, DA-A3-07). La ripresa non avviene, la chiamata non si esegue, la richiesta resta nello stato precedente. Conta come salvato solo il DB o una coda durevole con fsync (DECISIONS §6).
- **Audit dell'esito non salvato dopo l'esecuzione:** l'azione non si annulla; B2 invia il segnale ad A5 e mette l'esito in una coda di recupero; C3 non riesegue e riconcilia l'esito al recupero (DECISIONS §6).
- **`ai_generated` mancante** su un contenuto verso terzi generato dall'AI: la richiesta non è approvabile (Appendice B).
- **Rifiuto:** il run si chiude con `rejected:human_denied`.
- **Scrittura diventata obsoleta** (403/409/412): l'esito è riportato alla persona e non si riprova.

## 7. Requisiti non funzionali

- **Sicurezza tecnica.** Fail-closed su ogni errore. Decisioni solo con actor `human`, isolamento per `company_id` e RLS FORCE. Il token è monouso, emesso solo dopo il claim, legato all'hash degli argomenti approvati. B2 rifiuta un tool `REQUIRES_HITL` o `MONEY_WRITE` senza token valido: il vincolo è strutturale, non solo un test campionario (AC-1). L'esito non è autodichiarato: si riconcilia con l'audit di B2.
- **Idempotenza:** sulla riga, tramite UPDATE condizionale.
- **Osservabilità.** Un record di traccia E1 per ogni transizione (segmento `kind=decision`, `gravya.decision.kind=hitl`), con identificativi, pseudonimo del revisore, hash degli argomenti e `config_version`, mai i valori (DA-C3-06 (a), DA-E1-02). Gli attributi `kind=decision` che C3 richiede (richiesta, hash, revisore, esito, `config_version`) vanno nella whitelist di E1 (Appendice B). Il segmento è fail-open; il record di audit della decisione è fail-closed e porta `trace_id`, hash degli argomenti, `ai_generated` e `config_version`: l'attribuzione non dipende da un buffer che può perdere dati.
- **Performance.** La latenza decisione→ripresa, esclusa l'esecuzione del tool, resta sotto `hitl.resume_latency_p95_ms` al p95 (soglia con metrica a runtime, usata per gli alert).
- **Sicurezza e conformità (PV-01).**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per conto delle agenzie (DX-11); C3 esegue il trattamento del tool approvato, non ne introduce. Minimizzazione: `arguments` e `context` contengono solo ciò che serve a decidere. Gli identificativi pseudonimi (revisore, richiesta) restano dati personali (GDPR considerando 26); le linee guida EDPB 01/2025 sulla pseudonimizzazione sono solo in consultazione e non si citano come requisito. La mappa di re-identificazione ha una classe di retention propria (`retention.pseudonym_map_months`, F6). **Retention (DX-09, F6).** Classi prodotte da C3: righe parcheggiate (`arguments`, `context`) → `retention.sensitive_payload_days`; decisioni e feedback → `retention.audit_decisions_months`; eventi e record E1 → `retention.traces_days`; checkpoint del run in pausa → `retention.run_state_days`; segnali di incidente → `retention.incident_signals_months`; log degli accessi → `retention.cross_tenant_access_log_months` (schema di A6). I dati di un incidente aperto seguono le **evidenze di incidente** (`retention.incident_evidence_months`); la sospensione delle scadenze vale solo per i dati di Gravya, per i dati delle agenzie serve un'istruzione nel DPA e un parere legale (DA-CV-21). Le durate sono di sola lettura finché l'intervallo del contratto/DPA non è definito (DA-CV-01); l'override per agenzia (`retention.tenant_override_enabled`, `retention.<classe>.tenant_value`) si attiva solo con l'intervallo (DA-C3-09). I backup scadono entro `retention.data_backup_days` e al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22). A fine contratto valgono `retention.tenant_offboarding_choice` e `retention.tenant_offboarding_days` come periodo minimo di recupero (Data Act art. 25(2); qualificazione del SaaS da confermare con un legale). Se il tool approvato invia dati a terzi o fuori dall'UE valgono destinazione dichiarata, strumento di trasferimento valido, sub-responsabile autorizzato e opt-in per destinazione (DA-B2-07, applicati da B2; il Data Privacy Framework copre solo le organizzazioni USA dell'elenco ed è impugnato). Base giuridica degli identificativi di chi decide: del titolare per i suoi utenti, di Gravya per superadmin e operatori (DA-A1-08). Per una violazione di dati personali l'art. 33(2) GDPR non dà ore al responsabile: il termine verso l'agenzia è un obbligo del DPA (DA-CV-08); C3 invia il segnale ad A5.
  - *Accesso cross-tenant.* Le righe HITL di un'azienda non sono visibili da altre aziende (RLS FORCE). Il superadmin vede di default solo dati aggregati senza identificativi, con gruppo minimo `access.aggregate_min_group_size_count`; la lettura di una singola richiesta è ammessa solo su richiesta dell'agenzia o per un incidente, entro le istruzioni del titolare (art. 28), per `access.superadmin_trace_access_ttl_hours`, con riga nel log di A6 (DX-18, DX-19). MFA obbligatoria per superadmin e admin agenzia (DX-20).
  - *NIS2 (ready by design, DX-10).* Gravya oggi non è soggetto NIS2; log, accessi privilegiati e MFA sono requisiti di progetto sul Reg. di esecuzione (UE) 2024/2690, allegato 3.2 (registrazione delle attività e degli accessi privilegiati, protezione dei log) e 11 (account privilegiati, MFA), non sull'art. 21 della direttiva, che non nomina i log. Qui: solo actor `human` decide, RLS FORCE, token monouso, fail-closed. C3 **produce sempre** i segnali verso A5, anche con `incident.nis2_flow_active` falso, e li conserva (ondata 1: tabella di audit minima); le soglie vivono in A5 (DA-CV-07): decisione forgiata o actor non umano, esecuzione senza approvazione, doppio resume o replay del token, claim senza esito, chiusura per scadenza, variabile non leggibile, audit dell'esito non salvato, accesso cross-tenant fuori motivo. La notifica (preallarme `incident.nis2.early_warning_hours`, notifica `incident.nis2.notification_hours`, relazione finale `incident.nis2.final_report_days`, destinatario CSIRT Italia, decorrenza dalla conoscenza) è di A5 ed è una funzione presente ma non attiva.
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica, comunque applicabili ai sistemi ad alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 è applicabile dal 2.8.2026: C3 mostra `ai_generated` e non altera la marcatura; disclosure e marcatura per canale spettano a D1-D4. L'informativa a chi interagisce con un'IA (art. 50(1)) non riguarda C3, che non dialoga con l'utente finale. La persona vede la chiamata esatta e può rifiutarla.
  - *Marketing (PV-01).* L'approvazione non verifica consenso, opt-out o tracciamento (Codice privacy artt. 122 e 130, ePrivacy): dettaglio in D1-D4.
  - *Perimetro dati.* Tutto in PostgreSQL controllato da Gravya in UE (DA-B1-06); nessun servizio esterno di tracing o eval (DA-C1-05, DA-E3-09).
  - *Osservabilità AI.* Richieste, approvazioni, rifiuti, scadenze, input forniti; tempo di decisione; esiti delle chiamate; correlazione con run e prompt versionato (E2) tramite gli identificativi E1.

## 8. Criteri di accettazione

| ID | Criterio | Verifica |
|---|---|---|
| AC-1 | Nessuna scrittura `REQUIRES_HITL` o `MONEY_WRITE` viene eseguita senza riga `approved` reclamata. B2 rifiuta la chiamata con token assente, già usato o con hash diverso | test di integrazione su un campione di run senza decisione (parametro di test, DA-CV-04): 0 chiamate tool; test congiunto con B2 e A3 |
| AC-2 | Avviare il grafo senza checkpointer fallisce invece di saltare l'interrupt | unit test |
| AC-3 | Il doppio resume esegue al massimo una scrittura e produce un segnale ad A5 | test su Postgres reale |
| AC-4 | Un payload malformato porta comunque a un interrupt | unit test su `node_interrupt_check` |
| AC-5 | Gli argomenti eseguiti sono uguali byte per byte a quelli approvati, marcatura compresa | confronto tra hash degli argomenti approvati ed eseguiti |
| AC-6 | Lo sweeper chiude il 100% delle righe oltre il TTL effettivo del proprio tenant (due tenant con valori diversi di `hitl.request_ttl_hours`) senza rieseguirne nessuna | test su Postgres reale |
| AC-7 | Isolamento: l'azienda B non vede né decide le righe dell'azienda A | test RLS |
| AC-8 | Almeno 1 approvazione end-to-end con `outcome=ok` su staging v2, con dati sintetici (DA-E3-08) | query sulla tabella delle richieste |
| AC-9 | Ogni transizione produce un record di traccia E1 con identificativi, hash e `config_version` e nessun valore in chiaro degli argomenti; il record di audit della decisione porta `trace_id`, hash, `ai_generated` e `config_version` | test di integrazione su tracce E1 e audit |
| AC-10 | Se il record di audit A5 della decisione o il record di decisione A3 non si salva, la chiamata approvata non viene eseguita; con audit dell'esito non salvato dopo l'esecuzione c'è 1 sola esecuzione, 1 segnale ad A5 e 1 voce nella coda di recupero | test di integrazione con scrittura forzata in errore |
| AC-11 | `arguments` e `context` delle righe decise o eseguite da oltre `retention.sensitive_payload_days` vengono cancellati e l'hash resta; il checkpoint scade con `retention.run_state_days` | test su Postgres reale con durata impostata nel registro |
| AC-12 | Variabili non leggibili o non valide (DX-17, DA-C3-08): (a) con registro non disponibile o valore fuori da `hitl.request_ttl_hours_min`/`_max`, chiusura per TTL e cancellazioni usano l'ultimo valore valido versionato e nessun dato resta oltre la scadenza nota; (b) un claim con TTL non leggibile esegue 0 chiamate tool; (c) in entrambi i casi arriva un segnale ad A5; (d) senza alcun valore valido vale il valore deciso del catalogo | test di integrazione |
| AC-13 | Accesso cross-tenant del superadmin: senza motivo ammesso la lettura di una singola richiesta è negata e le metriche sono aggregate senza identificativi; con richiesta dell'agenzia o incidente è ammessa e produce una riga nel log di A6; se il log non si salva, l'accesso è negato | test di integrazione |
| AC-14 | Il p95 della latenza decisione→ripresa non supera `hitl.resume_latency_p95_ms` | test di carico su staging |
| AC-15 | Dopo la scadenza il run non resta in attesa e `hitl_expired` è emesso una sola volta | test su Postgres reale |
| AC-16 | La card mostra `model` e `prompt_ref` di `ai_generated` e la destinazione dichiarata; senza `ai_generated` su un contenuto AI verso terzi la richiesta non è approvabile | test di componente |
| AC-17 | Una decisione da una sessione senza MFA o da un ruolo non abilitato è rifiutata; il superadmin non può decidere | test di integrazione con identità simulate di A6 |
| AC-18 | Ogni caso elencato in §7 (NIS2) produce 1 segnale ad A5, anche con `incident.nis2_flow_active` falso, conservato in `retention.incident_signals_months` | test di integrazione |

## 9. Piano di implementazione

**Tecnologie:** LangGraph (libreria self-hosted, DA-C1-01, DA-C1-05) con `interrupt()` e checkpointer Postgres (scelta finale in B5), schema condiviso per i contratti (DA-C3-03), PostgreSQL con RLS, tracce DB-native E1.

**Fasi ordinate.**
1. Congelare i contratti di §4 in uno schema condiviso Python/TS (DA-C3-03), con `ai_generated`, `destination` e la marcatura.
2. Costruire da zero parcheggio, claim, token monouso, esito riconciliato e risoluzione della policy, con gravya-app come riferimento (Appendice A).
3. Implementare il nodo come nodo generico di C1 (DA-C3-02, chiusa).
4. Rendere fail-closed l'assenza di checkpointer; collegare tracce E1, audit A5 e segnali.
5. Implementare sweeper, TTL per agenzia e chiusura del run (DA-C3-04; scheduler DA-C3-11), con variabili lette dal registro di A6 (DX-13, DX-17) e cancellazione di `arguments`/`context` (AC-11).
6. Collegare identità, MFA e log degli accessi di A6 (AC-13, AC-17).
7. Pubblicare l'interfaccia minima per G2 ed eseguire il test end-to-end su staging (AC-8).

**Rischi:** vedi §11.

## 10. Test e valutazione

- **Unit:** builder dei payload, rami di `node_interrupt_check`, replay.
- **Integration:** ciclo completo parcheggio → decisione → resume → claim → esito, su Postgres reale con dati sintetici.
- **Eval (E3):** casi golden "scrittura che deve fermarsi", solo dati sintetici (DA-E3-08); vale l'invariante E3 di zero fallimenti bloccanti (catalogo §18). La corrispondenza con la metrica "fermate" di C3 non è detta nei documenti (Appendice B).
- **Fail-closed:** audit o record di decisione forzati in errore durante la ripresa (AC-10).
- **Security:** decisione forgiata da un actor non umano, resume cross-tenant, replay del token, path traversal su `taskId`, decisione senza MFA (AC-17), accesso del superadmin senza motivo o log (AC-13), auto-approvazione (DA-C3-10).
- **Configurazione:** registro non disponibile o valore non valido (AC-12); modifica del TTL con effetto senza rilascio e valore dell'agenzia dentro i limiti (AC-6).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| L'approvazione riguarda un testo e non l'azione (difetto segnalato da kloudify) | parcheggiare la chiamata esatta; AC-5 |
| Interrupt saltato in silenzio senza checkpointer | AC-2 |
| Doppia esecuzione dopo un retry | claim condizionale, un unico writer, lo sweeper non riesegue mai |
| Esito autodichiarato falsificabile | riconciliazione con l'audit di B2; segnale ad A5 |
| Dati personali oltre la scadenza (righe, checkpoint, feedback, tracce) | classi di §7, chiusura del run alla scadenza, AC-9, AC-11 |
| Variabile modificata male | modifica versionata e auditata (DX-13), fuori intervallo non valida (DX-16), regola DX-17 (AC-12) |
| A6 e F6 non ancora scritti (ondata 2) | C3 dipende da un'interfaccia di lettura del registro; nomi e pagine delle variabili sono provvisori finché A6 non li fissa |
| Approvazione di un contenuto AI verso terzi senza vederne l'origine | `ai_generated` e `destination` nella card; AC-16 |
| Audit non disponibile che blocca le approvazioni | scelta accettata (DA-B2-04, DA-A3-07); AC-10 |
| Fatica da approvazione | metriche di rifiuto; autonomia graduata fuori ondata 1 |

## 12. Stima e priorità

- **Taglia:** L. Vanno costruiti contratto condiviso, tabella con RLS, parcheggio, claim, token, esito, risoluzione della policy, nodo in C1, resume, sweeper per agenzia, card, tracce E1 e test. Il progetto è validato come idea in gravya-app, il che riduce il rischio ma non il lavoro. Stima non verificata.
- **Dipendenze critiche:** C1, B5 (DX-08), A3, B2; A6 e F6 (ondata 2) per variabili, ruoli e retention.
- **Thin-slice MVP:** sì. Senza C3 il walking skeleton non può eseguire scritture.

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è solo riferimento (DX-01, PV-03): nulla si porta in v2 come codice.

**Soluzioni da riprendere come idea (letto, commit `349118b11`):**
- `kloud/hitl_types.py`: forma dei contratti (unione discriminata).
- `kloud/graph.py`: `node_interrupt_check`, fail-closed su payload malformato.
- `kloud/write_replay.py`: esecuzione unica della chiamata approvata.
- `routes/kloud-approvals.ts`: parcheggio, claim, esito, `runOnly`.
- `services/kloud-approval.ts`: policy task → cliente → azienda → default; tabella HSAR; migrazione 0393.
- `services/kloud-resume.ts` e `kloud-hitl-expiry-sweeper.ts`: TTL di 24 h come costante.
- `services/approvals.ts`: FORCE RLS.
- `executors/generic_executor.py`: `requires_hitl`.
- UI `AskKloud.tsx` e i test come modello dei test v2.

**Difetti da non ripetere:** `interrupt()` no-op senza checkpointer (AC-2); approvazione del testo invece dell'azione; contratto TS gemello citato ma inesistente (`ui/src/lib/hitl.ts`); due motori di workflow con HITL in uno solo; nomi evento non uniformi; TTL fisso nel codice (in v2 è una variabile per DX-22 e DA-C3-04).

**Kloudify (letto):** `docs/visione/controlli-e-conformita.md` §2 e `.claude/plans/2026-10-15-issue-998-pezzo-4/design.md`.

**Divergenze dal master plan (riferite a gravya-app):**
1. Il master prevede una "UI di revisione" in C3; il codice ha una card in chat e una pagina approvals, mentre la coda vera è G2.
2. Kloudify (16/10) dice che si approva il testo e non si esegue nulla; il codice al 02/11 contiene parcheggio ed esecuzione unica. Il documento di stato potrebbe essere superato; non verificato su staging.
3. Il master colloca HITL nel solo layer LangGraph; gravya-app ha anche un motore DAG Node senza nodo HITL verificato.
4. Il master non prevede livelli di approvazione per azienda, cliente e task né un TTL: sono aggiunte del codice e della visione.

## Appendice B — Non verificato

- Schema completo di `approvals` e `kloud_hitl`; `approvals.ts` letto solo in parte; contratto TS in `ui/src/api/ask-kloud.ts`.
- Se il percorso parcheggio/replay sia attivo su staging (kloudify: 0 eventi di approvazione); nodo HITL nel motore Node; `c2_hitl_timeout.py`.
- Nomi e pagine delle variabili: provvisori fino ad A6 (catalogo); valori «da definire» o «proposta da validare» nel catalogo (per C3: `hitl.sweeper_interval_minutes`, `hitl.approval_token.ttl_s`, `hitl.resume_latency_p95_ms`). Con `hitl.sweeper_interval_minutes` «da definire» lo sweeper non è attivabile in produzione (catalogo, regola 4): l'ondata 1 non va in produzione.
- DX-05 (chi parcheggia e chi chiama `interrupt()`), DX-07, DX-08, DX-04 aperte.
- Le righe DA-CV-18..23 e il periodo minimo di recupero a fine contratto non sono ancora in DECISIONS.md (registrazione in corso): il testo segue il brief della v1.5. DA-CV-18 e DA-CV-21 sono decise lì, ma il catalogo v1.2 le elenca come aperte.
- Come il Codice di buone pratiche art. 50 voglia marcare il testo (strati, metadati nel testo libero, soglia): non letto (registro §9, punto 1); C3 non definisce la marcatura.
- Comportamento per un contenuto AI verso terzi privo di `ai_generated`: il documento assume «non approvabile» (fail-closed), non deciso.
- Attributi che C3 richiede nel segmento `kind=decision` di E1 (richiesta, hash degli argomenti, revisore, esito, `config_version`): E1 §4.2 ne ha solo alcuni; da allineare con E1.
- Che il decorso di `retention.sensitive_payload_days` per una richiesta chiusa per scadenza parta dalla chiusura (assunzione).
- Corrispondenza tra «100 % di fermate» (C3) e «zero fallimenti bloccanti» (E3).
- Un eventuale divieto di auto-approvazione nel codice di riferimento: non riverificato.
- Ambito NIS2 di Gravya, Allegati 3-4 della Det. ACN 379907/2025 e termini della coorte: aperti (DECISIONS §4).

## Appendice C — Decisioni

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C3-01 | Riuso in gravya-app-v2 | — | — | **Chiusa da DX-01**: costruzione da zero |
| DA-C3-02 | Dove vive il nodo HITL | — | — | **Chiusa (2026-11-03, utente)** da DA-C1-01: solo nel motore LangGraph |
| DA-C3-03 | Fonte del contratto condiviso | (a) Pydantic con TS generato; (b) Zod; (c) JSON Schema neutro | un solo punto di verità, niente drift | (c), proposta da validare. Aperta (= DX-04) |
| DA-C3-04 | TTL della richiesta | — | — | **Decisa (2026-11-03, utente)**: variabile `hitl.request_ttl_hours`, con `_min` e `_max`; il superadmin fissa default e limiti, l'admin agenzia sceglie entro i limiti. Valori nel catalogo |
| DA-C3-05 | Retention dei dati HITL | — | — | **Assorbita da DX-09**: variabili del catalogo (§7) |
| DA-C3-06 | Cosa della chiamata entra nelle tracce | — | — | **Decisa (a)** (DECISIONS §6): identificativi e hash degli argomenti |
| DA-C3-07 | Effetto di una modifica del TTL sulle richieste già aperte, e quando `expires_at` si fissa | (a) fissato al parcheggio; (b) ricalcolato a ogni passaggio dello sweeper; (c) ricalcolo solo verso il basso: una riduzione vale subito, un aumento solo per le nuove richieste | prevedibilità per chi decide; nessuna richiesta oltre il TTL in vigore; finestra di approvazione non estesa a posteriori | (c), proposta da validare. Non tocca dati o perimetro |
| DA-C3-08 | Chiusura per TTL: azione o scadenza programmata | — | — | **Decisa (2026-11-04, utente)**: scadenza programmata con ultimo valore valido versionato, segnale ad A5, solo non esecuzione |
| DA-C3-09 | Override della retention per agenzia | — | — | **Decisa (2026-11-04, utente)**: previsto nel modello, attivo solo con l'intervallo del contratto/DPA (F6); fino ad allora valgono i default |
| DA-C3-10 | Chi può decidere una richiesta, divieto di auto-approvazione, MFA dei membri | (a) solo admin agenzia (MFA già obbligatoria, DX-20); (b) anche i membri con permesso di decisione; (c) membri con MFA a gradino. In ogni caso valutare il divieto che chi ha avviato il run decida la propria richiesta | DX-20 copre solo superadmin e admin agenzia; rischio di decisione forgiata contro fatica da approvazione | (a) in ondata 1, con divieto di auto-approvazione; (b) o (c) dopo che A6 ha deciso l'MFA dei membri. **DA RIPORTARE ALL'UTENTE** (conformità) |
| DA-C3-11 | Scheduler dello sweeper | (a) job periodico interno al servizio di orchestrazione; (b) C5 (ondata 3); (c) arq (citato per B1) | indipendenza da componenti non ancora disponibili | (a), proposta da validare |
| DA-C3-12 | Forma dell'hash degli argomenti | (a) SHA-256 semplice (invariante di formato, DA-CV-05); (b) HMAC-SHA-256 con chiave per tenant, la cui distruzione rende l'hash non più riconducibile all'argomento | un hash di argomenti a bassa entropia (email, testo breve) resta dato personale (GDPR considerando 26) e sopravvive alla cancellazione degli argomenti; il confronto di AC-5 resta possibile | (b); la chiave sta nella pagina credenziali (DA-CV-23). **DA RIPORTARE ALL'UTENTE** (dati e conformità) |

Decisioni di processo recepite: DA-CV-15 (default `hitl.approval_required_default` in sola lettura; `ALWAYS_HITL` e `MONEY_WRITE` non declassabili), DA-CV-18 (contenuti verso terzi decisi dall'admin agenzia nell'ondata 1), DA-CV-07 (segnali senza soglia locale), DA-CV-17 (primo valore valido).

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunti in "È richiesto da" C1, A3, B2, E3 ed E2 (condizionale), che dichiarano di dipendere da C3; span allineato al tipo `gravya.decision` (kind=hitl) di E1; segnalata la divergenza di convenzione dei nomi evento e l'evento C1 non consumato. Motivo: dipendenze dichiarate in un solo verso e interfacce non combacianti. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): riferimenti a gravya-app riformulati come idee e lezioni, Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere, DA-C3-01 chiusa, DA-C3-02 riformulata, fasi §9 e test §8 riscritti per costruzione da zero, taglia da M a L. Applicate DX-02/PV-01/PV-02: osservabilità su tracce DB-native E1 senza OpenTelemetry, nuova voce "Sicurezza e conformità" in §7 (GDPR, NIS2, AI Act, osservabilità AI), AC-9, nuove DA-C3-05 (retention, da riportare) e DA-C3-06 (contenuto delle tracce). (rev. coerenza) §7 osservabilità: `tipo gravya.decision` → segmento `kind=decision` (E1 §4.2). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente (DECISIONS.md). DA-C1-01/DA-C1-05/DA-B1-06 recepite come scelte (§3, §7, §9) e rischio dei due motori chiuso; DA-E1-02 e DA-E1-05 in §4.4 e §7 (vocabolario GenAI semconv e `traceparent` ammessi, senza SDK OTel); DA-B2-04/DA-A3-07 fail-closed in §6, §7, nuovo AC-10, test §10 e rischio §11; DA-B2-07 e DA-E3-08 richiamate in §7 e §10. DX-09: DA-C3-05 assorbita, retention specifica rimossa, elencate le classi di dati prodotte. DX-10: notifica incidenti ad A5, C3 invia segnali. DX-11: Gravya responsabile ex art. 28, artt. 12/14 AI Act ridotti a buona pratica, art. 50 mantenuto. Taglia invariata (L). Motivo: decisioni dell'utente del 2026-11-03. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: durate di default di DECISIONS.md §5 per le classi di dati C3 (§4.3, §7, Appendice C), nuovo AC-11. DX-13: TTL, soglia di latenza e durate come variabili di piattaforma gestite dal superadmin, fail-closed (AC-12); accesso cross-tenant solo da superadmin con log (§7, AC-13); dipendenze da F6 e dal registro, con DX-14 (A6) da riportare. §6 di DECISIONS.md: DA-C3-06 (a) decisa (§6, §7, AC-9); base giuridica DA-A1-08; etichetta art. 50 resta aperta. Rischi §11 e test §10 aggiornati. Motivo: decisioni dell'utente. |
| 1.5 | 2026-11-04 | Allineamento a DECISIONS.md, al catalogo v1.2 e al registro delle norme v1.6, nel testo abbreviato (nessun valore fisso: solo nomi di variabile). DA-C3-04 (TTL per agenzia con limiti), DA-C3-08 (scadenza programmata, ultimo valore valido, run chiuso), DA-C3-09 (override con intervallo) decise; AC-12 e §6 corretti secondo DX-17. Nuove DA-C3-07, DA-C3-10, DA-C3-11, DA-C3-12 aperte. DX-14 (A6), DX-18, DX-19, DX-20, DX-21 recepite; DX-05 dichiarata aperta nelle interfacce, con emissione del token e riconciliazione dell'esito. `ai_generated`, marcatura art. 50(2) e `destination` nel payload; invarianti `ALWAYS_HITL` e `MONEY_WRITE` (DA-CV-15, DA-CV-18). §7: «NIS2 (art. 21)» sostituito dal Reg. 2024/2690 (DX-10), «legal hold» da evidenze di incidente, segnali sempre prodotti, pseudonimi, trasferimenti, calendario AI Act, marketing. Nuovi AC-14…18. Motivo: decisioni dell'utente del 2026-11-03 e 04. |
