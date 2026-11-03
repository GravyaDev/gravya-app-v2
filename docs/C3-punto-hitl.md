# C3 — Punto HITL

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C3 |
| Nome | Punto HITL (Human-in-the-Loop) |
| Componente padre | C — Orchestrazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.3 |
| Data | 2026-11-03 |

## 2. Scopo

**Cosa fa.** Il master plan lo definisce come "nodo di approvazione umana con UI di revisione e payload di contesto". In pratica C3 mette in pausa un run del grafo (C1) prima di un'azione irreversibile, cioè un invio o la modifica di un record. Salva la chiamata esatta da eseguire (tool e argomenti), la espone a una persona insieme al contesto e riprende il run in base alla decisione. Dopo un'approvazione la chiamata viene eseguita **una sola volta** e **con gli argomenti che la persona ha visto**.

**Cosa NON fa.**
- Non è la coda di revisione G2 (ondata 2). C3 espone solo l'interfaccia minima descritta in §5.
- Non decide *se* un'azione richiede approvazione. Lo stabiliscono la policy (A3) e l'impostazione per azienda, cliente e task. C3 applica il risultato.
- Non approva testo libero. Si approva **l'azione (il tool), non il testo** (`docs/visione/controlli-e-conformita.md` §2, kloudify).
- Non decide l'autonomia graduata, cioè il passaggio all'esecuzione automatica: è fuori ondata 1.

**Perché esiste.** Senza C3 non è possibile concedere agli agenti la scrittura in sicurezza. Il principio P7 (kloudify, `docs/visione/README.md`) parte da "approvazione richiesta".

## 3. Contesto e dipendenze

**Dipende da:** C1 (grafo che ospita il nodo), B5 (checkpointer: `interrupt()` di LangGraph richiede uno stato persistito), A3 (classifica il tool come `REQUIRES_HITL`/`MONEY_WRITE`), B2 (esegue il tool approvato), E1 (tracce DB-native delle decisioni), A5 (audit della decisione), F1 (tabelle con `company_id` e RLS).

**È richiesto da:** C1 (semantica del nodo `hitl`), A3 e B2 (esito `require_approval` e token monouso), E3 (casi che arrivano all'HITL), E2 (approvazione umana della promozione, solo se DA-E2-04 sceglie (b)), G2 (UI coda, ondata 2), D1/D2/D3 (scritture CRM, ads ed email con HITL), C4 (dead-letter per i casi scaduti o falliti), E4/E5 (metriche di rifiuto).

**Assunzioni:**
- v2 si costruisce da zero (DX-01, PV-03): i riferimenti a gravya-app in questo documento indicano idee e lezioni, non codice da portare.
- Il motore è LangGraph, unico, usato come libreria open source self-hosted, senza LangSmith né LangGraph Platform (DA-C1-01, DA-C1-05 decise). Il deploy è self-hosted su infrastruttura UE (DA-B1-06).
- Il checkpointer è Postgres (`langgraph-checkpoint-postgres`, come in gravya-app e nel master plan). La scelta definitiva spetta a B5 (vedi DX-08); se B5 sceglie diversamente C3 si riallinea.
- Il default è "approvazione richiesta" (in gravya-app: `KLOUD_APPROVAL_DEFAULT = true`, `server/src/services/kloud-approval.ts`); v2 lo riprende come requisito.

## 4. Contratti

**4.1 Payload di interrupt** (modellato sui contratti di gravya-app `services/agents/src/kloud/hitl_types.py`, da ridefinire nello schema condiviso di DA-C3-03). È un'unione discriminata su `type`:
- `approval_required`: `task`, `preview`, `supervisor?`, `structured_data`.
- `input_required`: gli stessi campi più `input_schema[]` (`key`, `label`, `type` ∈ {text, textarea, number, email, url, image_url, date, select, boolean, json}, `required`, `options?`, `default?`).

**4.2 Payload di ripresa:**
- `{approved: bool, feedback?: str}`
- oppure `{approved: true, input_data: {...}}`

**4.3 Record di scrittura parcheggiata** (tabella nuova di v2; in gravya-app l'analogo è la riga `kloud_hitl` in `approvals`). Campi minimi richiesti a C3:

| Campo | Note |
|---|---|
| `id`, `company_id`, `run_id` (= thread LangGraph) | RLS FORCE |
| `tool_key`, `permission_key`, `arguments` (JSON) | la chiamata esatta mostrata alla persona |
| `context` | task, cliente, anteprima, riferimento alla traccia DB-native E1 |
| `status` | `pending` → `approved`/`rejected`/`cancelled` |
| `claimed_at`, `outcome` (`ok`/`refused`/`error` + codice) | garanzia di esecuzione unica |
| `decided_by_user_id`, `decided_at`, `feedback` | scritti solo da un actor `human` (HSAR) |

Lo schema DB completo di `approvals` in gravya-app non è stato letto riga per riga (vedi Non verificato); serve solo come riferimento. Per `arguments` e `context`, che possono contenere dati personali (destinatari, contenuti di record CRM), valgono la minimizzazione di §7 e la politica di retention unica DX-09.

**4.4 Eventi emessi:** `hitl_requested`, `hitl_approved`, `hitl_denied`, `hitl_input_provided`, `hitl_expired`, `hitl_outcome`. In gravya-app esistono `hitl_denied`, `hitl_input_provided` e `hitl_approved` come `log_event` in `graph.py`. Gli altri nomi sono **proposta da validare**. Nota di revisione: gli altri documenti dell'ondata 1 usano nomi puntati (`tool.*`, `workflow.*`, `policy.*`); la convenzione dei nomi evento è un problema aperto trasversale (vedi `revisione-ondata-1.md`). C1 emette `workflow.run.interrupted` "verso C3", ma C3 non dichiara eventi consumati: in gravya-app il segnale passa per `interrupt()` di LangGraph. Gli eventi sono registrati nel modello dati DB-native di E1 (PV-02), non come span OpenTelemetry. Per i nomi degli attributi si può usare il vocabolario delle GenAI semantic conventions e il formato `traceparent` per la correlazione, senza SDK né export OTel (DA-E1-05).

## 5. Interfacce

Interfaccia minima che C3 espone. G2 la consumerà senza aggiungere logica.

| Operazione | Chiamante | Riferimento in gravya-app (solo come idea) |
|---|---|---|
| Parcheggia una chiamata | run (solo il servizio) | `POST /companies/:companyId/kloud/approvals` (`server/src/routes/kloud-approvals.ts`) |
| Elenca le richieste pending dell'azienda | persona | pagina approvals (`server/src/routes/approvals.ts`, non letta in dettaglio) |
| Decidi (approva, rifiuta, fornisce input) e riprendi | persona | `resumeKloudThread` → `POST /api/v1/resume/:taskId` firmato HMAC (`server/src/services/kloud-resume.ts`) |
| Claim esclusivo | run | `POST .../kloud/approvals/:approvalId/claim` (`runOnly`) |
| Esito | run | `POST .../kloud/approvals/:approvalId/outcome` |
| Risolvi la policy di approvazione | servizio | `kloud-approval.ts`: task → cliente → azienda → default `true` |

In ondata 1 la UI di v2 è una card minima che gestisce `approval_required`/`input_required`, sul modello della card in chat di gravya-app (`ui/src/components/AskKloud.tsx`). Endpoint e nomi di v2 si definiscono sul contratto nuovo.

## 6. Comportamento

**Flusso principale.**
1. L'esecutore propone una scrittura. A3 la classifica come soggetta a HITL e la policy risolta restituisce `approvalRequired=true`.
2. La chiamata viene parcheggiata (`pending`) e il passo termina con `requires_hitl=true`.
3. `node_interrupt_check` valida il payload e chiama `interrupt()`. Lo stato viene salvato nel checkpoint.
4. La persona decide e il server riprende il thread.
5. In caso di approvazione, il replay (idea validata in gravya-app `kloud/write_replay.py`) esegue claim, ricostruzione del tool dal catalogo, ricontrollo di scope e tetto di spesa, emissione del token monouso, chiamata unica e invio dell'esito.

**Casi limite.**
- **Payload malformato:** il nodo interrompe comunque, in modo fail-closed (come in gravya-app `graph.py`, "E-7").
- **Nessun checkpointer:** in gravya-app `interrupt()` diventa no-op; in v2 deve essere un errore bloccante (§8, AC-2).
- **Doppio resume:** il secondo claim riceve 409 e la scrittura non viene rieseguita.
- **Scadenza:** dopo un TTL di 24 h la richiesta `pending` o approvata ma non reclamata diventa `cancelled`. Se c'è un claim senza esito si registra `error/reaped` **senza rieseguire** (comportamento ripreso da gravya-app: `kloud-hitl-expiry-sweeper.ts`, `_ASK_KLOUD_HITL_TIMEOUT_HOURS = 24`).
- **Audit o traccia della decisione non salvati:** fail-closed (DA-B2-04, DA-A3-07). Se il record della decisione (A5) o il record di decisione della policy non si salva, la ripresa non avviene e la chiamata parcheggiata non viene eseguita; la richiesta resta nello stato precedente.
- **Rifiuto:** il run si chiude con `rejected:human_denied`.
- **Scrittura diventata obsoleta** (403/409/412): l'esito viene riportato alla persona e non si riprova.

## 7. Requisiti non funzionali

- **Sicurezza tecnica:** fail-closed su ogni errore. Le decisioni si scrivono solo con actor `human`, con isolamento per `company_id` e RLS FORCE. Il token HITL è monouso e viene emesso solo dopo il claim. Se il record di audit o di decisione non si salva, l'azione si blocca (DA-B2-04, DA-A3-07).
- **Idempotenza:** si applica alla riga, non al messaggio, attraverso un UPDATE condizionale.
- **Osservabilità:** un record di traccia DB-native E1 per ogni transizione di stato (segmento `kind=decision` con `gravya.decision.kind=hitl`, vocabolario E1 §4.1, modello dati definito da E1). Nessun SDK OpenTelemetry, OTLP o collector (PV-02); i nomi GenAI semantic conventions e il formato `traceparent` sono ammessi come vocabolario (DA-E1-05). I contenuti di prompt e risultati non sono mai catturati in produzione (DA-E1-02); cosa della chiamata parcheggiata entra nella traccia è DA-C3-06.
- **Sicurezza e conformità (PV-01).**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per conto delle agenzie (DX-11). Minimizzazione: `arguments` e `context` contengono solo ciò che serve a decidere ed eseguire; la traccia E1 porta identificativi e hash degli argomenti, non i valori (proposta, DA-C3-06). C3 non introduce trattamenti nuovi, esegue quello del tool approvato. Se il tool approvato invia dati a terzi o fuori dall'UE valgono la destinazione dichiarata, il deny se manca e l'opt-in del tenant per l'extra-UE (DA-B2-07, applicato da B2). Retention: segue la politica unica DX-09 (durate non ancora fissate). Classi di dati prodotte da C3: righe di scrittura parcheggiata (`arguments`, `context`), decisioni e feedback umani, eventi `hitl_*`/record di traccia E1 delle transizioni, checkpoint del run in pausa (prodotti tramite B5/C1). Diritti: le righe sono per `company_id` e devono essere trovabili e cancellabili/pseudonimizzabili per interessato, nei limiti della conservazione dell'audit stabilita da DX-09.
  - *NIS2 (art. 21).* Controllo degli accessi (solo actor `human` decide, RLS FORCE), registrazione delle decisioni in A5, token monouso, fail-closed. Un'esecuzione senza approvazione o una decisione forgiata è un incidente di sicurezza: C3 invia il segnale ad A5, responsabile della notifica (DX-10, ondata 2). C3 non gestisce la notifica.
  - *AI Act.* I casi d'uso v2 non sono ad alto rischio (DX-11): sorveglianza umana e log (artt. 12, 14) non sono obblighi ma buona pratica, che C3 realizza comunque per scelta di progetto (P7, approvazione richiesta): la persona vede la chiamata esatta e può rifiutarla; ogni decisione è registrata con autore, momento, hash degli argomenti ed esito. Trasparenza art. 50 (applicabile): se le azioni approvate inviano a terzi contenuti generati dall'AI (email, ads), l'obbligo di informativa va valutato nei documenti D1–D3; se C3 debba mostrare all'approvatore o allegare un'etichetta "generato da AI" resta un dubbio da riportare all'utente.
  - *Perimetro dati.* Tutto in PostgreSQL controllato da Gravya su infrastruttura UE (DA-B1-06); nessun servizio esterno di tracing o di eval (DA-C1-05, DA-E3-09).
  - *Cosa rende osservabile sul piano AI:* tasso di richieste, approvazioni, rifiuti, scadenze, input forniti; tempo di decisione; esiti (`ok`/`refused`/`error`) delle chiamate eseguite; correlazione con il run e il prompt versionato (E2) tramite gli identificativi E1.
- **Performance:** la latenza tra decisione e ripresa del run, esclusa l'esecuzione del tool, deve stare sotto 2 s al p95 (**proposta da validare**).

## 8. Criteri di accettazione

| ID | Criterio | Verifica |
|---|---|---|
| AC-1 | Nessuna scrittura `REQUIRES_HITL` viene eseguita senza una riga `approved` reclamata | test di integrazione: 0 chiamate tool su 100 run senza decisione (**proposta da validare**) |
| AC-2 | Avviare il grafo senza checkpointer fallisce invece di saltare l'interrupt | unit test (oggi è no-op: va cambiato) |
| AC-3 | Il doppio resume esegue al massimo una scrittura | test nuovo di v2, sul modello di gravya-app `test_998_p4_pr3_kloud_write_replay.py` |
| AC-4 | Un payload malformato porta comunque a un interrupt | unit test su `node_interrupt_check` |
| AC-5 | Gli argomenti eseguiti sono uguali byte per byte a quelli approvati | test che confronta l'hash degli argomenti approvati con quelli eseguiti |
| AC-6 | Lo sweeper chiude il 100% delle righe oltre il TTL senza rieseguirne nessuna | test su Postgres reale sul modello di gravya-app `server/src/__tests__/kloud-write-approvals.realpg.test.ts` |
| AC-7 | Isolamento: l'azienda B non vede né decide le righe dell'azienda A | test RLS, sul modello di gravya-app `approvals-force-rls-services.realpg.test.ts` |
| AC-8 | Esiste almeno 1 approvazione end-to-end registrata su staging v2 (in gravya-app, secondo kloudify, 0) | query sulla tabella delle richieste HITL con `outcome=ok` |
| AC-9 | Ogni transizione di stato produce un record di traccia E1 DB-native senza valori in chiaro degli argomenti (salvo esito di DA-C3-06) | test di integrazione sulla tabella delle tracce E1 |
| AC-10 | Fail-closed: se il record di audit A5 della decisione o il record di decisione A3 non si salva, la chiamata approvata non viene eseguita (DA-B2-04, DA-A3-07) | test di integrazione con scrittura dell'audit forzata in errore: 0 chiamate tool |

## 9. Piano di implementazione

**Tecnologie:** LangGraph (libreria self-hosted, DA-C1-01/DA-C1-05) `interrupt()` con checkpointer Postgres (master plan; scelta finale in B5), schema condiviso per i contratti (DA-C3-03), PostgreSQL con RLS, tracce DB-native E1.

**Fasi ordinate.**
1. Congelare i contratti di §4 in un unico schema condiviso Python/TS (DA-C3-03).
2. Costruire da zero parcheggio della chiamata, claim, esito e risoluzione della policy, usando gravya-app come riferimento di progetto (Appendice A).
3. Implementare il nodo C3 come nodo generico di C1, non legato solo al grafo Kloud (DA-C3-02).
4. Rendere fail-closed l'assenza di checkpointer e collegare le tracce DB-native E1 e l'audit A5.
5. Implementare sweeper e TTL (DA-C3-04) e il collegamento a C4.
6. Pubblicare l'interfaccia minima per G2 ed eseguire un test end-to-end su staging (AC-8).

**Rischi:** con DA-C1-01 decisa (LangGraph motore unico) il rischio di dover replicare il nodo HITL in più motori, difetto di gravya-app, non si presenta.

## 10. Test e valutazione

- **Unit:** builder dei payload, rami di `node_interrupt_check`, replay.
- **Integration:** ciclo completo parcheggio → decisione → resume → claim → esito, su Postgres reale.
- **Eval (E3):** casi golden di "scrittura che deve fermarsi", costruiti solo con dati sintetici (DA-E3-08), con soglia 100% di fermate (**proposta da validare**).
- **Fail-closed:** errore forzato sul salvataggio dell'audit/record di decisione durante la ripresa (AC-10).
- **Security:** decisione forgiata da un actor non umano, resume cross-tenant, replay del token, path traversal su `taskId` (validazione dell'identificativo, come `KLOUD_TASK_ID_RE` in gravya-app).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| L'approvazione riguarda un testo e non l'azione (difetto segnalato da kloudify) | parcheggiare la chiamata esatta e verificarla con AC-5 |
| Interrupt saltato in silenzio senza checkpointer | AC-2 |
| Doppia esecuzione dopo un retry | claim condizionale e un unico writer (lo sweeper non riesegue mai) |
| Due trasporti di resume che divergono | una sola funzione di resume |
| Dati personali conservati senza limite in righe e tracce HITL | politica di retention unica DX-09, DA-C3-06, AC-9 |
| Audit non disponibile che blocca le approvazioni | scelta accettata (fail-closed, DA-B2-04/DA-A3-07): meglio un'azione bloccata che una non registrata; AC-10 |
| Fatica da approvazione con il default "sempre" | metriche di rifiuto; l'autonomia graduata resta fuori ondata 1 |

## 12. Stima e priorità

- **Taglia:** L (ricalcolata per costruzione da zero, DX-01; era M per il riuso). Vanno costruiti contratto condiviso, tabella con RLS, parcheggio/claim/esito, risoluzione della policy, nodo generico in C1, resume, sweeper, card UI minima, tracce E1 e test. Il progetto è già validato in gravya-app, il che riduce il rischio ma non il lavoro. Stima non verificata.
- **Dipendenze critiche:** C1, B5, A3.
- **Thin-slice MVP:** sì. Senza C3 il walking skeleton non può eseguire scritture.

---

## Appendice A — Riferimenti dal sistema precedente

gravya-app è solo riferimento (DX-01, PV-03): nulla di quanto segue si porta in v2 come codice.

**Soluzioni da riprendere come idea (letto, commit `349118b11`):**
- `services/agents/src/kloud/hitl_types.py`: forma dei contratti (unione discriminata `approval_required`/`input_required`).
- `services/agents/src/kloud/graph.py`: `node_interrupt_check`, fail-closed su payload malformato, rami rifiuto, input e approvazione.
- `services/agents/src/kloud/write_replay.py`: esecuzione unica della chiamata approvata.
- `server/src/routes/kloud-approvals.ts`: parcheggio, claim ed esito, `runOnly`.
- `server/src/services/kloud-approval.ts`: risoluzione della policy task → cliente → azienda → default, tabella HSAR, migrazione 0393.
- `server/src/services/kloud-resume.ts` e `kloud-hitl-expiry-sweeper.ts`: TTL di 24 h.
- `server/src/services/approvals.ts`: FORCE RLS.
- `services/agents/src/executors/generic_executor.py`: `requires_hitl` derivato da `hitl_level == "full_manual"` o da un'approvazione pending.
- UI `ui/src/components/AskKloud.tsx` e i test citati in §8, come modello dei test v2.

**Difetti da non ripetere:**
- `interrupt()` no-op senza checkpointer (AC-2).
- Approvazione del testo invece dell'azione (kloudify §2).
- Contratto TS gemello citato ma inesistente (`ui/src/lib/hitl.ts`): drift tra Python e TS.
- Due motori di workflow con HITL in uno solo.
- Nomi evento non uniformi (`hitl_*` contro `tool.*`).

**Kloudify (letto):** `docs/visione/controlli-e-conformita.md` §2 e `.claude/plans/2026-10-15-issue-998-pezzo-4/design.md`. Non esiste una cartella `docs/decisions`.

**Divergenze e note (riferite a gravya-app):**
1. Il master plan prevede una "UI di revisione" dentro C3. Il codice ha una card in chat e una pagina approvals, mentre la coda vera è G2.
2. Kloudify (stato al 16/10) dice che oggi si approva il testo e non si esegue nulla (`graph.py:863-867, 948-953`). Il codice al 02/11 contiene invece il parcheggio della chiamata esatta e il replay (#998 pezzo 4 PR 3/3b). **Il documento di stato potrebbe essere superato.** Non è stato verificato se il percorso sia attivo su staging.
3. Il docstring di `hitl_types.py` e la ricognizione `sviluppo.md` citano `ui/src/lib/hitl.ts` come schema Zod gemello: **il file non esiste**. Il contratto TS reale sta probabilmente in `ui/src/api/ask-kloud.ts`, ma non è stato letto.
4. Il master plan colloca HITL nel solo layer LangGraph. In gravya-app esiste anche un motore DAG Node (`workflow-executor.ts`) senza un nodo HITL verificato.
5. Il master plan non prevede livelli di approvazione per azienda, cliente e task né un TTL: sono aggiunte del codice e della visione.

## Appendice B — Non verificato

- Schema completo della tabella `approvals` e del tipo `kloud_hitl` (colonne, enum degli stati).
- Contenuto di `server/src/routes/approvals.ts` e della pagina UI approvals.
- Contratto TS in `ui/src/api/ask-kloud.ts`.
- Se il percorso parcheggio/replay sia attivo e raggiungibile su staging (kloudify: 0 eventi di approvazione).
- Presenza di un nodo HITL nel motore workflow Node.
- Contenuto di `c2_hitl_timeout.py` e rapporto tra il suo timeout e lo sweeper.
- Tutte le soglie numeriche marcate "proposta da validare".

## Appendice C — Decisioni

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C3-01 | Riuso in gravya-app-v2 | — | — | **Chiusa da DX-01**: costruzione da zero, gravya-app come riferimento (Appendice A) |
| DA-C3-02 | Dove vive il nodo HITL | (a) solo nel motore unico scelto da C1; (b) in più motori se C1 ne prevede più d'uno | esito di DA-C1-01 | (a). DA-C1-01 è decisa (LangGraph motore unico), quindi (b) non ha più presupposto; la chiusura formale resta da registrare in DECISIONS.md |
| DA-C3-03 | Fonte del contratto condiviso | (a) Pydantic come fonte con TS generato; (b) Zod come fonte; (c) JSON Schema neutro | un solo punto di verità e niente drift | (c) proposta da validare |
| DA-C3-04 | TTL della richiesta | (a) 24 h fisse (come gravya-app); (b) configurabile per azienda | casi d'uso di campagne lunghe | (a) in ondata 1 |
| DA-C3-05 | Retention di richieste, argomenti, decisioni e feedback HITL | — | — | **Assorbita da DX-09** (vedi `DECISIONS.md`): politica di retention unica; durate non ancora fissate |
| DA-C3-06 | Cosa della chiamata entra nelle tracce E1 | (a) solo identificativi e hash degli argomenti; (b) argomenti completi | minimizzazione, coerenza con DA-E1-02 | (a), coerente con DA-E1-02 (decisa: contenuti mai in produzione) |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunti in "È richiesto da" C1, A3, B2, E3 ed E2 (condizionale), che dichiarano di dipendere da C3; span allineato al tipo `gravya.decision` (kind=hitl) di E1; segnalata la divergenza di convenzione dei nomi evento e l'evento C1 non consumato. Motivo: dipendenze dichiarate in un solo verso e interfacce non combacianti. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): riferimenti a gravya-app riformulati come idee e lezioni, Appendice A rinominata "Riferimenti dal sistema precedente" con soluzioni da riprendere e difetti da non ripetere, DA-C3-01 chiusa, DA-C3-02 riformulata, fasi §9 e test §8 riscritti per costruzione da zero, taglia da M a L. Applicate DX-02/PV-01/PV-02: osservabilità su tracce DB-native E1 senza OpenTelemetry, nuova voce "Sicurezza e conformità" in §7 (GDPR, NIS2, AI Act, osservabilità AI), AC-9, nuove DA-C3-05 (retention, da riportare) e DA-C3-06 (contenuto delle tracce). (rev. coerenza) §7 osservabilità: `tipo gravya.decision` → segmento `kind=decision` (E1 §4.2). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente (DECISIONS.md). DA-C1-01/DA-C1-05/DA-B1-06 recepite come scelte (§3, §7, §9) e rischio dei due motori chiuso; DA-E1-02 e DA-E1-05 in §4.4 e §7 (vocabolario GenAI semconv e `traceparent` ammessi, senza SDK OTel); DA-B2-04/DA-A3-07 fail-closed in §6, §7, nuovo AC-10, test §10 e rischio §11; DA-B2-07 e DA-E3-08 richiamate in §7 e §10. DX-09: DA-C3-05 assorbita, retention specifica rimossa, elencate le classi di dati prodotte. DX-10: notifica incidenti ad A5, C3 invia segnali. DX-11: Gravya responsabile ex art. 28, artt. 12/14 AI Act ridotti a buona pratica, art. 50 mantenuto. Taglia invariata (L). Motivo: decisioni dell'utente del 2026-11-03. |
