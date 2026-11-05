# C3 — Punto HITL

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C3 |
| Nome | Punto HITL (Human-in-the-Loop) |
| Componente padre | C — Orchestrazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.6 |
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
- **A3** (esito `require_approval`; `tool_class` arriva da B2 dal catalogo, A3 non lo assegna; verifica firma e legame dell'`approval_token`) e **B2** (esegue il tool approvato e **consuma** il token monouso, tenendo il registro dei token consumati).
- **E1** (tracce DB-native delle transizioni) e **A5** (audit della decisione e destinatario dei segnali, ondata 2). In ondata 1 la conferma del salvataggio dà la tabella di audit minima che A5 assorbirà (DECISIONS §6).
- **A6** (ondata 2, DX-14 decisa): identità e ruoli, MFA, registro versionato delle variabili, log degli accessi cross-tenant (DX-18), pagina credenziali.
- **F1** (tabelle con `company_id` e RLS) e **F6** (ondata 2, DX-12): applica la retention.

**È richiesto da:** C1 (semantica del nodo `hitl`), A3 e B2 (`require_approval` e token monouso), E3 (casi che arrivano all'HITL), E2 (promozione di un prompt, solo se DA-E2-04 sceglie (b)), G2 (UI coda, ondata 2), D1-D3 (scritture CRM, ads, email con HITL), C4 (dead-letter dei casi scaduti o falliti), E4 ed E5 (metriche di rifiuto).

**Assunzioni:**
- v2 si costruisce da zero (DX-01, PV-03): i riferimenti a gravya-app sono idee e lezioni, non codice.
- Motore LangGraph come libreria self-hosted in UE, senza LangSmith né LangGraph Platform (DA-C1-01, DA-C1-05, DA-B1-06). Il nodo HITL gira nel servizio di orchestrazione, non nei job B1 (DECISIONS §6).
- Il checkpointer è Postgres; la scelta spetta a B5 (DX-08).
- Il default è "approvazione richiesta": variabile `hitl.approval_required_default`, che regola le azioni fuori dalle classi sotto. Il default di piattaforma è di sola lettura (DA-CV-15); se la policy non è risolvibile vale "richiesta" (fail-closed, DX-17).
- Nessun valore è fisso nel codice (DX-22): ogni durata, soglia o limite è una variabile di `docs/catalogo-variabili.md`, citata qui per nome. Finché A6 non esiste le variabili si leggono da un'istantanea versionata nel repository, modificabile solo con una PR e letta tramite un'unica interfaccia: è un ripiego dichiarato che non soddisfa DX-22. I valori «proposta da validare» valgono come primo valore valido, con segnale; i valori «da definire» hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione (decisione E5).
- **Invarianti (catalogo §18):** le classi `ALWAYS_HITL` e `MONEY_WRITE` richiedono sempre approvazione umana e non sono declassabili da UI (DECISIONS §7, DA-CV-05, DA-CV-15). La classe la assegna il superadmin nel catalogo dei tool di B2, con versione e audit; si può solo aggiungere, e toglierla richiede la conferma della seconda persona con accesso superadmin. Un tool senza classe dichiarata va in `require_approval` (DA-B2-11, decisione E4). Per i contenuti verso terzi (email, post, messaggi per conto delle agenzie) non sono una classe `ALWAYS_HITL` nell'ondata 1: decide l'admin agenzia tramite `hitl.approval_required_default`, con audit dell'attore (DA-CV-18; da riesaminare con D1-D4). Nell'ondata 1 i tool di invio verso terzi sono negati nel bundle (DA-A3-09) e B2 rifiuta un invio se gli argomenti non portano `ai_generated` (DA-B2-10). Fail-closed, token monouso e MFA (DX-20) sono invarianti.

## 4. Contratti

**4.1 Payload di interrupt** (modellato su `services/agents/src/kloud/hitl_types.py` di gravya-app; formato condiviso: DA-C3-03). Unione discriminata su `type`:
- `approval_required`: `task`, `preview`, `supervisor?`, `structured_data`, più:
  - `ai_generated` (`model`, `prompt_ref`): obbligatorio per i contenuti generati dall'AI, definito nel contratto di output dei nodi agent di C1 e **mostrato all'approvatore** (DECISIONS §6);
  - l'indicazione della marcatura leggibile da macchina prevista per il canale (AI Act art. 50(2), invariante, anche per il testo), fornita dal connettore. **Dove si applica:** come in C1 §4.4, `ai_generated` è l'unico input da cui i connettori D1-D4 derivano la marcatura, e la applicano a valle dell'approvazione; gli argomenti approvati (AC-5) sono quelli prima della marcatura. L'esecuzione registra nell'audit di B2 l'hash (HMAC per tenant, DA-C3-12) del **contenuto marcato** effettivamente inviato, per provare che l'inviato è l'approvato più la marcatura. Modalità e livelli di marcatura del testo: DA-C1-07 (c), da leggere sul Codice di buone pratiche prima del primo rilascio in produzione (l'art. 50 vale dal 2.8.2026);
  - `destination`: destinazione, giurisdizione e categorie di dati dichiarate nel catalogo di B2 (DA-B2-07), mostrate all'approvatore.
- `input_required`: gli stessi campi più `input_schema[]` (`key`, `label`, `type` ∈ {text, textarea, number, email, url, image_url, date, select, boolean, json}, `required`, `options?`, `default?`).

**4.2 Payload di ripresa:** `{approved: bool, reason_code?: enum, feedback?: str}` oppure `{approved: true, input_data: {...}}`. `reason_code` è un motivo da un elenco chiuso (contenuto da definire in implementazione) ed è ciò che resta nell'audit della decisione; `feedback` è testo libero e non entra nell'audit (§4.3).

**4.3 Record di scrittura parcheggiata** (tabella nuova di v2). Campi minimi:

| Campo | Note |
|---|---|
| `id`, `company_id`, `run_id` (= thread LangGraph) | RLS FORCE |
| `tool_key`, `permission_key`, `arguments` (JSON) | la chiamata esatta mostrata alla persona |
| `context` | task, cliente, anteprima, riferimento alla traccia E1 |
| `status` | `pending` → `approved`/`rejected`/`cancelled` (la chiusura per scadenza è `cancelled`) |
| `created_at`, `expires_at` | scadenza della richiesta (§6; `expires_at` si ricalcola solo verso il basso, DA-C3-07 (c)) |
| `claimed_at`, `outcome` (`ok`/`refused`/`error`/`reaped` + codice) | garanzia di esecuzione unica; l'esito è riconciliato con l'audit di B2 (§6) |
| `decided_by_user_id`, `decided_at`, `reason_code`, `feedback` | scritti solo da un actor `human` abilitato (DA-C3-10); l'identità è fornita da A6 (DX-21) |

`arguments` e `context` possono contenere dati personali (destinatari, contenuti di record CRM): valgono la minimizzazione di §7 e la classe `retention.sensitive_payload_days`; nella decisione resta solo l'hash degli argomenti, un HMAC-SHA-256 con chiave per tenant (DA-C3-12: la distruzione della chiave lo rende non più riconducibile all'argomento). Anche `preview`, `structured_data` e `input_data` finiscono nel checkpoint (B5): seguono `retention.run_state_days`. Il testo libero `feedback` può citare nomi e contenuti: segue `retention.sensitive_payload_days`, non l'audit; nell'audit della decisione resta solo `reason_code`, con la classe `retention.audit_decisions_months`.

**Esportazione dei dati del tenant (F6, ondata 2).** I dati di C3 sono esportabili con lo strumento di esportazione di F6, che li converte in un formato strutturato di uso universale (il formato è una proposta del coordinator in attesa di conferma dell'utente e qui non è fissato). Perimetro di C3: la tabella delle richieste di §4.3 (campi, stato, date, `reason_code`, `feedback` e, finché non scadono, `arguments` e `context`), i record di decisione nell'audit e le tracce E1 delle transizioni del tenant.

**4.4 Eventi emessi:** `hitl_requested`, `hitl_approved`, `hitl_rejected`, `hitl_input_provided`, `hitl_expired`, `hitl_outcome`. Gravya-app ha `hitl_denied`, `hitl_input_provided` e `hitl_approved`; in v2 `hitl_denied` diventa `hitl_rejected` per coincidere con lo stato `rejected`; i nomi nuovi sono **proposta da validare**. **Vocabolario di `gravya.decision.outcome` per `kind=hitl`** (E1 lo recepisce): `requested`, `approved`, `rejected`, `input_provided`, `expired`, e per l'esito dell'esecuzione `executed_ok`, `executed_refused`, `executed_error`, `reaped`. `gravya.decision.id` è l'`id` della richiesta di §4.3. Gli altri documenti dell'ondata 1 usano nomi puntati (`tool.*`, `workflow.*`): il formato è la decisione aperta DX-07. C1 emette `workflow.run.interrupted` verso C3; in gravya-app il segnale passa per `interrupt()` di LangGraph. Gli eventi sono registrati nel modello DB-native di E1 (PV-02), senza SDK né export OpenTelemetry; per i nomi degli attributi E1 può usare il vocabolario GenAI semantic conventions e `traceparent` (DA-E1-05). Ogni transizione registra la `config_version` in vigore (DX-21).

## 5. Interfacce

Interfaccia minima che C3 espone; G2 la consumerà senza aggiungere logica.

| Operazione | Chiamante | Riferimento in gravya-app (solo idea) |
|---|---|---|
| Parcheggia una chiamata | B2 (esito `require_approval` di A3) o run: dipende da DX-05, aperta | `POST /companies/:companyId/kloud/approvals` (`kloud-approvals.ts`) |
| Elenca le richieste `pending` dell'azienda | persona | pagina approvals (`approvals.ts`, non letta in dettaglio) |
| Decidi (approva, rifiuta, fornisce input) e riprendi | admin agenzia identificato da A6, con MFA (DX-20); chi ha avviato il run non decide la propria richiesta (DA-C3-10) | `resumeKloudThread` → `POST /api/v1/resume/:taskId` firmato HMAC (`kloud-resume.ts`) |
| Claim esclusivo | chi esegue | `POST .../approvals/:approvalId/claim` (`runOnly`) |
| Emetti l'`approval_token` monouso (solo dopo il claim, legato a tenant, tool e hash degli argomenti approvati) | C3; B2 lo consuma, A3 ne verifica firma e legame | `write_replay.py` |
| Esito | chi esegue; riconciliato con l'audit di B2 | `POST .../approvals/:approvalId/outcome` |
| Risolvi la policy di approvazione | servizio | `kloud-approval.ts`: task → cliente → azienda → default |
| Scadenza (job periodico) | servizio | `kloud-hitl-expiry-sweeper.ts`; scheduler: DA-C3-11 |
| Lettura delle variabili | servizio | registro di A6 |

La chiave HMAC di resume e la firma del token monouso stanno nella pagina credenziali di A6 (catalogo §15; sostituzione senza interruzione: DA-CV-23). In ondata 1 la UI è una card minima per `approval_required` e `input_required`, sul modello di `AskKloud.tsx`: mostra `ai_generated`, `destination` e gli argomenti esatti. Endpoint e nomi di v2 si definiscono sul contratto nuovo.

## 6. Comportamento

**Flusso principale.**
1. Un tool classificato `ALWAYS_HITL` o `MONEY_WRITE` nel catalogo di B2, un tool senza classe dichiarata, o una policy di approvazione risolta a "richiesta" per le altre azioni, produce `require_approval`; chi parcheggia è deciso da DX-05.
2. La chiamata viene parcheggiata (`pending`) e il passo termina con `requires_hitl=true`.
3. `node_interrupt_check` valida il payload e chiama `interrupt()`; lo stato va nel checkpoint.
4. Decide un actor `human` che sia admin agenzia, con MFA e diverso da chi ha avviato il run (DA-C3-10). Il superadmin non decide richieste di un tenant.
5. In caso di approvazione: claim, ricostruzione del tool dal catalogo, ricontrollo di scope e tetto di spesa, `approval_token` monouso, chiamata unica tramite B2 (che chiede la decisione ad A3: A3 verifica firma e legame del token, B2 lo consuma), esito.

**Casi limite.**
- **Payload malformato:** il nodo interrompe comunque (fail-closed).
- **Nessun checkpointer:** errore bloccante, non no-op (AC-2).
- **Doppio resume o replay del token:** il secondo claim riceve 409, la scrittura non si riesegue, segnale ad A5.
- **Scadenza (DA-C3-04, DA-C3-08).** Una richiesta `pending` o approvata ma non reclamata oltre `hitl.request_ttl_hours` diventa `cancelled`: è una **scadenza programmata**, non un'azione. Usa l'ultimo valore valido versionato (DX-17, DA-C3-08 (a)), emette `hitl_expired`, invia un segnale ad A5 e porta solo alla non esecuzione. Chiude anche il run in pausa (così lo stato scade con `retention.run_state_days` e C4 riceve il caso). Il TTL lo sceglie l'admin agenzia entro `hitl.request_ttl_hours_min` e `hitl.request_ttl_hours_max`; fuori intervallo il valore non è valido (DX-16). Una riduzione del TTL vale subito anche per le richieste già aperte; un aumento vale solo per le nuove richieste (DA-C3-07 (c), decisa). Il job è interno al servizio di orchestrazione (DA-C3-11 (a), decisa) e gira ogni `hitl.sweeper_interval_minutes`.
- **Claim senza esito:** prima si controlla l'audit di B2; se la chiamata risulta eseguita si riconcilia l'esito reale, altrimenti `error/reaped`. Mai riesecuzione.
- **Variabile non leggibile o non valida (DX-17).** Le azioni (claim, ripresa, esecuzione) si bloccano; le cancellazioni programmate usano l'ultimo valore valido versionato; in entrambi i casi parte un segnale ad A5. Senza alcun valore valido (primo avvio, versioni tutte non valide; DA-CV-17) il primo valore valido è il valore «deciso» del catalogo; segnali, audit e notifiche sono esclusi dal blocco; le classi di retention «da definire» non si scrivono in produzione finché A6 o F6 non fissano un valore; per le altre variabili «da definire» l'azione dipendente si blocca.
- **Audit o traccia della decisione non salvati (prima dell'esecuzione):** fail-closed (DA-B2-04, DA-A3-07). La ripresa non avviene, la chiamata non si esegue, la richiesta resta nello stato precedente. Conta come salvato solo il DB o una coda durevole con fsync (DECISIONS §6).
- **Audit dell'esito non salvato dopo l'esecuzione:** l'azione non si annulla; B2 invia il segnale ad A5 e mette l'esito in una coda di recupero; C3 non riesegue e riconcilia l'esito al recupero (DECISIONS §6).
- **`ai_generated` mancante** su un contenuto verso terzi generato dall'AI: B2 rifiuta la chiamata (DA-B2-10) e in C3 la richiesta non è approvabile.
- **Token con tenant, tool o hash diversi da quelli approvati, token già consumato o scaduto (`hitl.approval_token.ttl_s`):** A3 nega, B2 non esegue, segnale ad A5.
- **Rifiuto:** il run si chiude con `rejected:human_denied`.
- **Scrittura diventata obsoleta** (403/409/412): l'esito è riportato alla persona e non si riprova.

## 7. Requisiti non funzionali

- **Sicurezza tecnica.** Fail-closed su ogni errore. Decisioni solo con actor `human`, isolamento per `company_id` e RLS FORCE. L'`approval_token` è monouso, emesso solo dopo il claim, legato a tenant, tool e hash degli argomenti approvati; A3 ne verifica firma e legame, B2 lo consuma. B2 rifiuta un tool `ALWAYS_HITL` o `MONEY_WRITE` (o senza classe) senza token valido: il vincolo è strutturale, non solo un test campionario (AC-1). La chiave di firma e la chiave HMAC di resume sono nella pagina credenziali di A6 (§5). L'esito non è autodichiarato: si riconcilia con l'audit di B2.
- **Idempotenza:** sulla riga, tramite UPDATE condizionale.
- **Osservabilità.** Un record di traccia E1 per ogni transizione (segmento `kind=decision`, `gravya.decision.kind=hitl`), con `gravya.decision.id` (id della richiesta), `gravya.decision.reviewer_ref` (pseudonimo fornito da A6), `gravya.decision.args_hash`, `gravya.decision.outcome` dal vocabolario di §4.4 e `config_version`, mai i valori (DA-C3-06 (a), DA-E1-02). Gli hash sono HMAC-SHA-256 con chiave per tenant (DA-C3-12, decisa; E1 e B2 usano la stessa forma): modifica l'invariante «SHA-256» di DA-CV-05 senza cambiare l'algoritmo di base. Il segmento è fail-open; il record di audit della decisione è fail-closed e porta `trace_id`, hash degli argomenti, `ai_generated`, `reason_code` e `config_version`: l'attribuzione non dipende da un buffer che può perdere dati.
- **Performance.** La latenza decisione→ripresa, esclusa l'esecuzione del tool, resta sotto `hitl.resume_latency_p95_ms` al p95 (soglia con metrica a runtime, usata per gli alert).
- **Sicurezza e conformità (PV-01).**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per conto delle agenzie (DX-11); C3 esegue il trattamento del tool approvato, non ne introduce. Minimizzazione: `arguments` e `context` contengono solo ciò che serve a decidere. Gli identificativi pseudonimi (revisore, richiesta) restano dati personali (GDPR considerando 26); le linee guida EDPB 01/2025 sulla pseudonimizzazione sono solo in consultazione e non si citano come requisito. La mappa di re-identificazione ha una classe di retention propria (`retention.pseudonym_map_months`, F6). **Retention (DX-09, F6).** Classi prodotte da C3: righe parcheggiate (`arguments`, `context`) → `retention.sensitive_payload_days`; decisioni (con `reason_code`) → `retention.audit_decisions_months`; testo libero del revisore (`feedback`) → `retention.sensitive_payload_days`; eventi e record E1 → `retention.traces_days`; checkpoint del run in pausa → `retention.run_state_days`; segnali di incidente → `retention.incident_signals_months`; log degli accessi → `retention.cross_tenant_access_log_months` (schema di A6). I dati di un incidente aperto seguono le **evidenze di incidente** (`retention.incident_evidence_months`); la sospensione delle scadenze vale solo per i dati di Gravya, per i dati delle agenzie serve un'istruzione nel DPA e un parere legale (DA-CV-21). Le durate sono di sola lettura finché l'intervallo del contratto/DPA non è definito (DA-CV-01); l'override per agenzia (`retention.tenant_override_enabled`, `retention.<classe>.tenant_value`) si attiva solo con l'intervallo (DA-C3-09). I backup scadono entro `retention.data_backup_days` e al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22). A fine contratto valgono `retention.tenant_offboarding_choice` e `retention.tenant_offboarding_days` come periodo minimo di recupero (Data Act art. 25(2); qualificazione del SaaS da confermare con un legale). Se il tool approvato invia dati a terzi o fuori dall'UE valgono destinazione dichiarata, strumento di trasferimento valido, sub-responsabile autorizzato e opt-in per destinazione (DA-B2-07, applicati da B2; il Data Privacy Framework copre solo le organizzazioni USA dell'elenco ed è impugnato). Base giuridica degli identificativi di chi decide: del titolare per i suoi utenti, di Gravya per superadmin e operatori (DA-A1-08). Per una violazione di dati personali l'art. 33(2) GDPR non dà ore al responsabile: il termine verso l'agenzia è un obbligo del DPA (DA-CV-08); C3 invia il segnale ad A5.
  - *Accesso cross-tenant.* Le righe HITL di un'azienda non sono visibili da altre aziende (RLS FORCE). Il superadmin vede di default solo dati aggregati senza identificativi, con gruppo minimo `access.aggregate_min_group_size_count`; la lettura di una singola richiesta ha due sole vie (DX-19, E8), entrambe con perimetro, durata `access.superadmin_trace_access_ttl_hours` e riga nel log di A6 (DX-18): (a) **incidente dichiarato** dal superadmin, che abilita direttamente la lettura, con riferimento all'incidente; (b) **richiesta di assistenza** dell'agenzia, in cui l'admin agenzia concede l'accesso come parte della richiesta. Entro le istruzioni del titolare (art. 28). MFA obbligatoria per superadmin e admin agenzia (DX-20).
  - *NIS2 (ready by design, DX-10).* Gravya oggi non è soggetto NIS2; log, accessi privilegiati e MFA sono requisiti di progetto sul Reg. di esecuzione (UE) 2024/2690, allegato 3.2 (registrazione delle attività e degli accessi privilegiati, protezione dei log) e 11 (account privilegiati, MFA), non sull'art. 21 della direttiva, che non nomina i log. Qui: solo actor `human` decide, RLS FORCE, token monouso, fail-closed. C3 **produce sempre** i segnali verso A5, anche con `incident.nis2_flow_active` falso, e li conserva (ondata 1: tabella di audit minima); le soglie vivono in A5 (DA-CV-07): decisione forgiata o actor non umano, esecuzione senza approvazione, doppio resume o replay del token, claim senza esito, chiusura per scadenza, variabile non leggibile, audit dell'esito non salvato, accesso cross-tenant fuori motivo. La notifica (preallarme `incident.nis2.early_warning_hours`, notifica `incident.nis2.notification_hours`, relazione finale `incident.nis2.final_report_days`, destinatario CSIRT Italia, decorrenza dalla conoscenza) è di A5 ed è una funzione presente ma non attiva.
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica, comunque applicabili ai sistemi ad alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 è applicabile dal 2.8.2026: C3 mostra `ai_generated`; marcatura per canale e disclosure sono dei connettori D1-D4, a valle dell'approvazione (§4.1), e l'hash del contenuto marcato è registrato nell'audit di B2. L'informativa a chi interagisce con un'IA (art. 50(1)) non riguarda C3, che non dialoga con l'utente finale. La persona vede la chiamata esatta e può rifiutarla.
  - *Marketing (PV-01).* L'approvazione non verifica consenso, opt-out o tracciamento (Codice privacy artt. 122 e 130, ePrivacy): dettaglio in D1-D4.
  - *Perimetro dati.* Tutto in PostgreSQL controllato da Gravya in UE (DA-B1-06); nessun servizio esterno di tracing o eval (DA-C1-05, DA-E3-09).
  - *Osservabilità AI.* Richieste, approvazioni, rifiuti, scadenze, input forniti; tempo di decisione; esiti delle chiamate; correlazione con run e prompt versionato (E2) tramite gli identificativi E1.

## 8. Criteri di accettazione

| ID | Criterio | Verifica |
|---|---|---|
| AC-1 | Nessuna scrittura `ALWAYS_HITL` o `MONEY_WRITE`, né di un tool senza classe, viene eseguita senza riga `approved` reclamata. B2 rifiuta la chiamata con `approval_token` assente, già consumato, scaduto o legato a tenant, tool o hash diversi | test di integrazione su un campione di run senza decisione (parametro di test, DA-CV-04): 0 chiamate tool; test congiunto con B2 e A3 |
| AC-2 | Avviare il grafo senza checkpointer fallisce invece di saltare l'interrupt | unit test |
| AC-3 | Il doppio resume esegue al massimo una scrittura e produce un segnale ad A5 | test su Postgres reale |
| AC-4 | Un payload malformato porta comunque a un interrupt | unit test su `node_interrupt_check` |
| AC-5 | Gli argomenti eseguiti sono uguali byte per byte a quelli approvati (prima della marcatura); l'audit di B2 riporta l'hash HMAC del contenuto marcato inviato | confronto tra hash HMAC degli argomenti approvati ed eseguiti; verifica del campo nell'audit |
| AC-6 | Lo sweeper chiude il 100% delle righe oltre il TTL effettivo del proprio tenant (due tenant con valori diversi di `hitl.request_ttl_hours`) senza rieseguirne nessuna | test su Postgres reale |
| AC-7 | Isolamento: l'azienda B non vede né decide le righe dell'azienda A | test RLS |
| AC-8 | Almeno 1 approvazione end-to-end con `outcome=ok` su staging v2, con dati sintetici (DA-E3-08) | query sulla tabella delle richieste |
| AC-9 | Ogni transizione produce un record di traccia E1 con `gravya.decision.outcome` dal vocabolario di §4.4, identificativi, hash HMAC e `config_version` e nessun valore in chiaro degli argomenti; il record di audit della decisione porta `trace_id`, hash, `ai_generated`, `reason_code` e `config_version`, e nessun testo libero del revisore | test di integrazione su tracce E1 e audit |
| AC-10 | Se il record di audit A5 della decisione o il record di decisione A3 non si salva, la chiamata approvata non viene eseguita; con audit dell'esito non salvato dopo l'esecuzione c'è 1 sola esecuzione, 1 segnale ad A5 e 1 voce nella coda di recupero | test di integrazione con scrittura forzata in errore |
| AC-11 | `arguments`, `context` e `feedback` delle righe decise o eseguite da oltre `retention.sensitive_payload_days` vengono cancellati e l'hash resta; il checkpoint scade con `retention.run_state_days` | test su Postgres reale con durata impostata nel registro |
| AC-12 | Variabili non leggibili o non valide (DX-17, DA-C3-08): (a) con registro non disponibile o valore fuori da `hitl.request_ttl_hours_min`/`_max`, chiusura per TTL e cancellazioni usano l'ultimo valore valido versionato e nessun dato resta oltre la scadenza nota; (b) un claim con TTL non leggibile esegue 0 chiamate tool; (c) in entrambi i casi arriva un segnale ad A5; (d) senza alcun valore valido vale il valore deciso del catalogo, e segnali e audit non si bloccano (DA-CV-17) | test di integrazione |
| AC-13 | Accesso cross-tenant del superadmin: senza una delle due vie la lettura di una singola richiesta è negata e le metriche sono aggregate senza identificativi; con incidente dichiarato (con riferimento) o con richiesta di assistenza concessa dall'admin agenzia è ammessa per la durata `access.superadmin_trace_access_ttl_hours` e produce una riga nel log di A6; se il log non si salva, l'accesso è negato | test di integrazione |
| AC-14 | Il p95 della latenza decisione→ripresa non supera `hitl.resume_latency_p95_ms` | test di carico su staging |
| AC-15 | Dopo la scadenza il run non resta in attesa e `hitl_expired` è emesso una sola volta | test su Postgres reale |
| AC-16 | La card mostra `model` e `prompt_ref` di `ai_generated` e la destinazione dichiarata; senza `ai_generated` su un contenuto AI verso terzi la richiesta non è approvabile | test di componente |
| AC-17 | Una decisione da una sessione senza MFA, da un ruolo diverso da admin agenzia o dalla persona che ha avviato il run è rifiutata; il superadmin non può decidere | test di integrazione con identità simulate di A6 |
| AC-18 | Ogni caso elencato in §7 (NIS2) produce 1 segnale ad A5, anche con `incident.nis2_flow_active` falso, conservato in `retention.incident_signals_months` | test di integrazione |

## 9. Piano di implementazione

**Tecnologie:** LangGraph (libreria self-hosted, DA-C1-01, DA-C1-05) con `interrupt()` e checkpointer Postgres (scelta finale in B5), schema condiviso per i contratti (DA-C3-03), PostgreSQL con RLS, tracce DB-native E1.

**Fasi ordinate.**
1. Congelare i contratti di §4 in uno schema condiviso Python/TS (DA-C3-03), con `ai_generated`, `destination` e la marcatura.
2. Costruire da zero parcheggio, claim, token monouso, esito riconciliato e risoluzione della policy, con gravya-app come riferimento (Appendice A).
3. Implementare il nodo come nodo generico di C1 (DA-C3-02, chiusa).
4. Rendere fail-closed l'assenza di checkpointer; collegare tracce E1, audit A5 e segnali.
5. Implementare sweeper (job interno, DA-C3-11 (a)), TTL per agenzia e chiusura del run (DA-C3-04, DA-C3-07 (c)), con variabili lette dal registro di A6 (DX-13, DX-17) e cancellazione di `arguments`/`context` (AC-11).
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
- DX-05 (chi parcheggia e chi chiama `interrupt()`), DX-07, DX-08, DX-04 aperte. Le decisioni E1-E16 del 2026-11-04 sono recepite dal blocco di decisioni, non rilette in DECISIONS.md.
- Come il Codice di buone pratiche art. 50 voglia marcare il testo (strati, metadati nel testo libero, soglia): non letto (registro §9, punto 1); C3 non definisce la marcatura. Che la marcatura si applichi a valle, nel connettore, e che l'audit di B2 registri l'hash del contenuto marcato, è una scelta di C3 coerente con C1 §4.4: va confermata con C1 e D1-D4.
- Vocabolario di `gravya.decision.outcome` per `hitl` (§4.4): è definito da C3; E1 §4.2 lo recepisce (da verificare nella v1.6 di E1).
- Elenco chiuso di `reason_code`: contenuto non definito.
- Chiave HMAC per tenant degli hash (DA-C3-12): da aggiungere all'elenco di credenziali del catalogo §15; il confronto di AC-5 con due chiavi valide in parallelo (DA-CV-23) non è descritto.
- Il divieto di auto-approvazione (DA-C3-10) impedisce a un'agenzia con un solo admin di approvare un run avviato da lui stesso: conseguenza non valutata (nessuna decisione sul secondo approvatore).
- Che il decorso di `retention.sensitive_payload_days` per una richiesta chiusa per scadenza parta dalla chiusura (assunzione).
- Corrispondenza tra «100 % di fermate» (C3) e «zero fallimenti bloccanti» (E3).
- Un eventuale divieto di auto-approvazione nel codice di riferimento: non riverificato.
- Ambito NIS2 di Gravya, Allegati 3-4 della Det. ACN 379907/2025 e termini della coorte: aperti (DECISIONS §4).

## Appendice C — Decisioni

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C3-01 | Riuso in gravya-app-v2 | — | — | **Chiusa da DX-01**: costruzione da zero |
| DA-C3-02 | Dove vive il nodo HITL | — | — | **Chiusa (2026-11-03, utente)** da DA-C1-01: solo nel motore LangGraph |
| DA-C3-03 | Fonte del contratto condiviso | (a) Pydantic con TS generato; (b) Zod; (c) JSON Schema neutro | un solo punto di verità, niente drift | (a), in coerenza con E16 (a): backend tutto in Python e interfaccia TypeScript più avanti. Aperta in DECISIONS finché DX-04 non è chiusa (= DX-04) |
| DA-C3-04 | TTL della richiesta | — | — | **Decisa (2026-11-03, utente)**: variabile `hitl.request_ttl_hours`, con `_min` e `_max`; il superadmin fissa default e limiti, l'admin agenzia sceglie entro i limiti. Valori nel catalogo |
| DA-C3-05 | Retention dei dati HITL | — | — | **Assorbita da DX-09**: variabili del catalogo (§7) |
| DA-C3-06 | Cosa della chiamata entra nelle tracce | — | — | **Decisa (a)** (DECISIONS §6): identificativi e hash degli argomenti |
| DA-C3-07 | Effetto di una modifica del TTL sulle richieste già aperte | — | — | **Decisa (c)** (2026-11-04, utente, E13): una riduzione del TTL vale subito, un aumento solo per le nuove richieste |
| DA-C3-08 | Chiusura per TTL: azione o scadenza programmata | — | — | **Decisa (2026-11-04, utente)**: scadenza programmata con ultimo valore valido versionato, segnale ad A5, solo non esecuzione |
| DA-C3-09 | Override della retention per agenzia | — | — | **Decisa (2026-11-04, utente)**: previsto nel modello, attivo solo con l'intervallo del contratto/DPA (F6); fino ad allora valgono i default |
| DA-C3-10 | Chi può decidere una richiesta, divieto di auto-approvazione, MFA dei membri | — | — | **Decisa (2026-11-04, utente, E13)**: nell'ondata 1 decide solo l'admin agenzia (MFA già obbligatoria, DX-20), con divieto di auto-approvazione: chi ha avviato il run non decide la propria richiesta. I membri e la loro MFA restano a una decisione futura con A6 |
| DA-C3-11 | Scheduler dello sweeper | — | — | **Decisa (a)** (2026-11-04, utente, E13): job interno al servizio di orchestrazione |
| DA-C3-12 | Forma dell'hash degli argomenti (= DA-E1-09) | — | — | **Decisa (E1, 2026-11-04, utente)**: HMAC-SHA-256 con chiave per tenant, nella pagina credenziali con rotazione a due chiavi (DA-CV-23); la distruzione della chiave rende l'hash non riconducibile. Modifica l'invariante «SHA-256» di DA-CV-05. Vale per B2, A3, E1, E2 e A1 |
| DA-B2-11 (rimando) | Classi di approvazione | — | — | **Decisa (E4, 2026-11-04, utente)**: vocabolario unico `ALWAYS_HITL` e `MONEY_WRITE` (`REQUIRES_HITL` non esiste più); assegnazione del superadmin in catalogo B2, solo aggiunta, rimozione con la seconda persona; tool senza classe in `require_approval` |

Decisioni recepite: DA-CV-15 (default `hitl.approval_required_default` in sola lettura; `ALWAYS_HITL` e `MONEY_WRITE` non declassabili), DA-CV-18 (contenuti verso terzi decisi dall'admin agenzia nell'ondata 1), DA-CV-07 (segnali senza soglia locale), DA-CV-17 (testo deciso), E7 (token legato a tenant, tool e hash; B2 consuma, A3 verifica; il `run_token` non è monouso), E8 (due vie di accesso del superadmin), E15 (esportazione dei dati del tenant con lo strumento di F6).

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunti in "È richiesto da" C1, A3, B2, E3 ed E2 (condizionale), che dichiarano di dipendere da C3; span allineato al tipo `gravya.decision` (kind=hitl) di E1; segnalata la divergenza di convenzione dei nomi evento e l'evento C1 non consumato. Motivo: dipendenze dichiarate in un solo verso e interfacce non combacianti. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): riferimenti a gravya-app riformulati come idee e lezioni, Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere, DA-C3-01 chiusa, DA-C3-02 riformulata, fasi §9 e test §8 riscritti per costruzione da zero, taglia da M a L. Applicate DX-02/PV-01/PV-02: osservabilità su tracce DB-native E1 senza OpenTelemetry, nuova voce "Sicurezza e conformità" in §7 (GDPR, NIS2, AI Act, osservabilità AI), AC-9, nuove DA-C3-05 (retention, da riportare) e DA-C3-06 (contenuto delle tracce). (rev. coerenza) §7 osservabilità: `tipo gravya.decision` → segmento `kind=decision` (E1 §4.2). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente (DECISIONS.md). DA-C1-01/DA-C1-05/DA-B1-06 recepite come scelte (§3, §7, §9) e rischio dei due motori chiuso; DA-E1-02 e DA-E1-05 in §4.4 e §7 (vocabolario GenAI semconv e `traceparent` ammessi, senza SDK OTel); DA-B2-04/DA-A3-07 fail-closed in §6, §7, nuovo AC-10, test §10 e rischio §11; DA-B2-07 e DA-E3-08 richiamate in §7 e §10. DX-09: DA-C3-05 assorbita, retention specifica rimossa, elencate le classi di dati prodotte. DX-10: notifica incidenti ad A5, C3 invia segnali. DX-11: Gravya responsabile ex art. 28, artt. 12/14 AI Act ridotti a buona pratica, art. 50 mantenuto. Taglia invariata (L). Motivo: decisioni dell'utente del 2026-11-03. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: durate di default di DECISIONS.md §5 per le classi di dati C3 (§4.3, §7, Appendice C), nuovo AC-11. DX-13: TTL, soglia di latenza e durate come variabili di piattaforma gestite dal superadmin, fail-closed (AC-12); accesso cross-tenant solo da superadmin con log (§7, AC-13); dipendenze da F6 e dal registro, con DX-14 (A6) da riportare. §6 di DECISIONS.md: DA-C3-06 (a) decisa (§6, §7, AC-9); base giuridica DA-A1-08; etichetta art. 50 resta aperta. Rischi §11 e test §10 aggiornati. Motivo: decisioni dell'utente. |
| 1.5 | 2026-11-04 | Allineamento a DECISIONS.md, al catalogo v1.2 e al registro delle norme v1.6, nel testo abbreviato (nessun valore fisso: solo nomi di variabile). DA-C3-04 (TTL per agenzia con limiti), DA-C3-08 (scadenza programmata, ultimo valore valido, run chiuso), DA-C3-09 (override con intervallo) decise; AC-12 e §6 corretti secondo DX-17. Nuove DA-C3-07, DA-C3-10, DA-C3-11, DA-C3-12 aperte. DX-14 (A6), DX-18, DX-19, DX-20, DX-21 recepite; DX-05 dichiarata aperta nelle interfacce, con emissione del token e riconciliazione dell'esito. `ai_generated`, marcatura art. 50(2) e `destination` nel payload; invarianti `ALWAYS_HITL` e `MONEY_WRITE` (DA-CV-15, DA-CV-18). §7: «NIS2 (art. 21)» sostituito dal Reg. 2024/2690 (DX-10), «legal hold» da evidenze di incidente, segnali sempre prodotti, pseudonimi, trasferimenti, calendario AI Act, marketing. Nuovi AC-14…18. Motivo: decisioni dell'utente del 2026-11-03 e 04. |
| 1.6 | 2026-11-04 | Applicate le decisioni E1-E16 approvate dall'utente il 2026-11-04 e i rilievi della revisione unica della v1.5. E1: DA-C3-12 decisa, hash HMAC-SHA-256 con chiave per tenant (§4.3, §7, AC-5, AC-9). E4: `REQUIRES_HITL` sostituito da `ALWAYS_HITL` (§6, §7, AC-1), assegnazione della classe da parte del superadmin, tool senza classe in `require_approval`. E5: istantanea versionata delle variabili prima di A6. E7: `approval_token` legato a tenant, tool e hash, consumato da B2 e verificato da A3. E13: DA-C3-07 (c), DA-C3-10 (solo admin agenzia, divieto di auto-approvazione), DA-C3-11 (a) decise. E8: due vie di accesso del superadmin (incidente dichiarato, richiesta di assistenza). E15: perimetro di esportazione dei dati di C3 con lo strumento di F6. Marcatura art. 50(2) coerente con C1 (applicata dal connettore a valle, hash del contenuto marcato nell'audit di B2). Feedback del revisore: motivo codificato nell'audit, testo libero in `retention.sensitive_payload_days`. Vocabolario degli esiti `hitl` definito in C3 (§4.4) e `hitl_denied` rinominato `hitl_rejected`. DA-CV-17 con il testo deciso. Tolte le note «non ancora in DECISIONS». DA-C3-03 orientata da E16 (a). Motivo: allineamento alle decisioni E1-E16 e alla revisione unica. |
