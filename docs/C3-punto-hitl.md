# C3 — Punto HITL

## 1. Identità

| Campo | Valore |
|---|---|
| ID | C3 |
| Nome | Punto HITL (Human-in-the-Loop) |
| Componente padre | C — Orchestrazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.1 |
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

**Dipende da:** C1 (grafo che ospita il nodo), B5 (checkpointer: `interrupt()` di LangGraph richiede uno stato persistito), A3 (classifica il tool come `REQUIRES_HITL`/`MONEY_WRITE`), B2 (esegue il tool approvato), E1 (span delle decisioni), A5 (audit della decisione), F1 (tabelle con `company_id` e RLS).

**È richiesto da:** C1 (semantica del nodo `hitl`), A3 e B2 (esito `require_approval` e token monouso), E3 (casi che arrivano all'HITL), E2 (approvazione umana della promozione, solo se DA-E2-04 sceglie (b)), G2 (UI coda, ondata 2), D1/D2/D3 (scritture CRM, ads ed email con HITL), C4 (dead-letter per i casi scaduti o falliti), E4/E5 (metriche di rifiuto).

**Assunzioni:**
- Il checkpointer è Postgres (`langgraph-checkpoint-postgres`, già in uso). La scelta per gravya-app-v2 resta aperta in DA-C3-01.
- Il default è "approvazione richiesta" (`KLOUD_APPROVAL_DEFAULT = true`, `server/src/services/kloud-approval.ts`).

## 4. Contratti

**4.1 Payload di interrupt** (riuso di `services/agents/src/kloud/hitl_types.py`). È un'unione discriminata su `type`:
- `approval_required`: `task`, `preview`, `supervisor?`, `structured_data`.
- `input_required`: gli stessi campi più `input_schema[]` (`key`, `label`, `type` ∈ {text, textarea, number, email, url, image_url, date, select, boolean, json}, `required`, `options?`, `default?`).

**4.2 Payload di ripresa:**
- `{approved: bool, feedback?: str}`
- oppure `{approved: true, input_data: {...}}`

**4.3 Record di scrittura parcheggiata** (il riferimento esistente è la riga `kloud_hitl` in `approvals`). Campi minimi richiesti a C3:

| Campo | Note |
|---|---|
| `id`, `company_id`, `run_id` (= thread LangGraph) | RLS FORCE |
| `tool_key`, `permission_key`, `arguments` (JSON) | la chiamata esatta mostrata alla persona |
| `context` | task, cliente, anteprima, riferimento al trace E1 |
| `status` | `pending` → `approved`/`rejected`/`cancelled` |
| `claimed_at`, `outcome` (`ok`/`refused`/`error` + codice) | garanzia di esecuzione unica |
| `decided_by_user_id`, `decided_at`, `feedback` | scritti solo da un actor `human` (HSAR) |

Lo schema DB completo di `approvals` non è stato letto riga per riga (vedi Non verificato).

**4.4 Eventi emessi:** `hitl_requested`, `hitl_approved`, `hitl_denied`, `hitl_input_provided`, `hitl_expired`, `hitl_outcome`. Oggi esistono `hitl_denied`, `hitl_input_provided` e `hitl_approved` come `log_event` in `graph.py`. Gli altri nomi sono **proposta da validare**. Nota di revisione: gli altri documenti dell'ondata 1 usano nomi puntati (`tool.*`, `workflow.*`, `policy.*`); la convenzione dei nomi evento è un problema aperto trasversale (vedi `revisione-ondata-1.md`). C1 emette `workflow.run.interrupted` "verso C3", ma C3 non dichiara eventi consumati: oggi il segnale passa per `interrupt()` di LangGraph.

## 5. Interfacce

Interfaccia minima che C3 espone. G2 la consumerà senza aggiungere logica.

| Operazione | Chiamante | Riferimento esistente |
|---|---|---|
| Parcheggia una chiamata | run (solo il servizio) | `POST /companies/:companyId/kloud/approvals` (`server/src/routes/kloud-approvals.ts`) |
| Elenca le richieste pending dell'azienda | persona | pagina approvals (`server/src/routes/approvals.ts`, non letta in dettaglio) |
| Decidi (approva, rifiuta, fornisce input) e riprendi | persona | `resumeKloudThread` → `POST /api/v1/resume/:taskId` firmato HMAC (`server/src/services/kloud-resume.ts`) |
| Claim esclusivo | run | `POST .../kloud/approvals/:approvalId/claim` (`runOnly`) |
| Esito | run | `POST .../kloud/approvals/:approvalId/outcome` |
| Risolvi la policy di approvazione | servizio | `kloud-approval.ts`: task → cliente → azienda → default `true` |

In ondata 1 la UI si limita alla card esistente in chat (`ui/src/components/AskKloud.tsx`), che gestisce `approval_required`/`input_required`.

## 6. Comportamento

**Flusso principale.**
1. L'esecutore propone una scrittura. A3 la classifica come soggetta a HITL e la policy risolta restituisce `approvalRequired=true`.
2. La chiamata viene parcheggiata (`pending`) e il passo termina con `requires_hitl=true`.
3. `node_interrupt_check` valida il payload e chiama `interrupt()`. Lo stato viene salvato nel checkpoint.
4. La persona decide e il server riprende il thread.
5. In caso di approvazione, `replay_approved_write` (`kloud/write_replay.py`) esegue claim, ricostruzione del tool dal catalogo, ricontrollo di scope e tetto di spesa, emissione del token monouso, chiamata unica e invio dell'esito.

**Casi limite.**
- **Payload malformato:** il nodo interrompe comunque, in modo fail-closed (`graph.py`, "E-7").
- **Nessun checkpointer:** `interrupt()` diventa no-op. Va reso un errore bloccante (§8, AC-2).
- **Doppio resume:** il secondo claim riceve 409 e la scrittura non viene rieseguita.
- **Scadenza:** dopo un TTL di 24 h la richiesta `pending` o approvata ma non reclamata diventa `cancelled`. Se c'è un claim senza esito si registra `error/reaped` **senza rieseguire** (`kloud-hitl-expiry-sweeper.ts`; lato agenti `_ASK_KLOUD_HITL_TIMEOUT_HOURS = 24` in `job_queue/cron_dispatchers.py`).
- **Rifiuto:** il run si chiude con `rejected:human_denied`.
- **Scrittura diventata obsoleta** (403/409/412): l'esito viene riportato alla persona e non si riprova.

## 7. Requisiti non funzionali

- **Sicurezza:** fail-closed su ogni errore. Le decisioni si scrivono solo con actor `human`, con isolamento per `company_id` e RLS FORCE. Il token HITL è monouso e viene emesso solo dopo il claim.
- **Idempotenza:** si applica alla riga, non al messaggio, attraverso un UPDATE condizionale.
- **Osservabilità:** uno span E1 per ogni transizione di stato (span `gravya.decision` con `gravya.decision.kind=hitl`, E1 §4.1). Il contenuto di prompt e risultati segue la decisione aperta di E1 (kloudify: "non prompt e risultati").
- **Performance:** la latenza tra decisione e ripresa del run, esclusa l'esecuzione del tool, deve stare sotto 2 s al p95 (**proposta da validare**).

## 8. Criteri di accettazione

| ID | Criterio | Verifica |
|---|---|---|
| AC-1 | Nessuna scrittura `REQUIRES_HITL` viene eseguita senza una riga `approved` reclamata | test di integrazione: 0 chiamate tool su 100 run senza decisione (**proposta da validare**) |
| AC-2 | Avviare il grafo senza checkpointer fallisce invece di saltare l'interrupt | unit test (oggi è no-op: va cambiato) |
| AC-3 | Il doppio resume esegue al massimo una scrittura | estensione di `services/agents/tests/unit/test_998_p4_pr3_kloud_write_replay.py` |
| AC-4 | Un payload malformato porta comunque a un interrupt | unit test su `node_interrupt_check` |
| AC-5 | Gli argomenti eseguiti sono uguali byte per byte a quelli approvati | test che confronta l'hash degli argomenti approvati con quelli eseguiti |
| AC-6 | Lo sweeper chiude il 100% delle righe oltre il TTL senza rieseguirne nessuna | test realpg sul modello di `server/src/__tests__/kloud-write-approvals.realpg.test.ts` |
| AC-7 | Isolamento: l'azienda B non vede né decide le righe dell'azienda A | test RLS, sul modello di `approvals-force-rls-services.realpg.test.ts` |
| AC-8 | Esiste almeno 1 approvazione end-to-end registrata su staging (oggi sono 0) | query su `approvals` di tipo `kloud_hitl` con `outcome=ok` |

## 9. Piano di implementazione

**Tecnologie:** LangGraph `interrupt()` con checkpointer Postgres (master plan e codice), Pydantic e Zod per i contratti, PostgreSQL con RLS.

**Fasi ordinate.**
1. Decidere la strategia di riuso (DA-C3-01) e congelare i contratti di §4 in un unico schema condiviso Python/TS (DA-C3-03).
2. Portare o riusare il parcheggio della chiamata, il claim, l'esito e la risoluzione della policy.
3. Implementare il nodo C3 come nodo generico di C1, non legato solo al grafo Kloud (DA-C3-02).
4. Rendere fail-closed l'assenza di checkpointer e collegare gli span E1 e l'audit A5.
5. Implementare sweeper e TTL (DA-C3-04) e il collegamento a C4.
6. Pubblicare l'interfaccia minima per G2 ed eseguire un test end-to-end su staging (AC-8).

**Rischi:** C1 oggi ha due motori (DAG su Node e LangGraph su Python), quindi il nodo HITL potrebbe dover esistere in entrambi.

## 10. Test e valutazione

- **Unit:** builder dei payload, rami di `node_interrupt_check`, replay.
- **Integration:** ciclo completo parcheggio → decisione → resume → claim → esito, su Postgres reale.
- **Eval (E3):** casi golden di "scrittura che deve fermarsi", con soglia 100% di fermate (**proposta da validare**).
- **Security:** decisione forgiata da un actor non umano, resume cross-tenant, replay del token, path traversal su `taskId` (regex `KLOUD_TASK_ID_RE` già presente).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| L'approvazione riguarda un testo e non l'azione (difetto segnalato da kloudify) | parcheggiare la chiamata esatta e verificarla con AC-5 |
| Interrupt saltato in silenzio senza checkpointer | AC-2 |
| Doppia esecuzione dopo un retry | claim condizionale e un unico writer (lo sweeper non riesegue mai) |
| Due trasporti di resume che divergono | una sola funzione `resumeKloudThread` |
| Fatica da approvazione con il default "sempre" | metriche di rifiuto; l'autonomia graduata resta fuori ondata 1 |

## 12. Stima e priorità

- **Taglia:** M. Gran parte del meccanismo esiste già. Il lavoro principale riguarda la generalizzazione a C1, il fail-closed e il contratto unico.
- **Dipendenze critiche:** C1, B5, A3.
- **Thin-slice MVP:** sì. Senza C3 il walking skeleton non può eseguire scritture.

---

## Appendice A — Allineamento con lo stato attuale

**Esiste in gravya-app (letto, commit `349118b11`):**
- `services/agents/src/kloud/hitl_types.py`: contratti Pydantic, riusabili così come sono.
- `services/agents/src/kloud/graph.py`: `node_interrupt_check`, fail-closed su payload malformato, rami rifiuto, input e approvazione.
- `services/agents/src/kloud/write_replay.py`: esecuzione unica della chiamata approvata.
- `server/src/routes/kloud-approvals.ts`: parcheggio, claim ed esito, `runOnly`.
- `server/src/services/kloud-approval.ts`: risoluzione della policy task → cliente → azienda → default, tabella HSAR, migrazione 0393.
- `server/src/services/kloud-resume.ts` e `kloud-hitl-expiry-sweeper.ts`: TTL di 24 h.
- `server/src/services/approvals.ts`: FORCE RLS.
- `services/agents/src/executors/generic_executor.py`: `requires_hitl` derivato da `hitl_level == "full_manual"` o da un'approvazione pending.
- UI `ui/src/components/AskKloud.tsx` e i test esistenti citati in §8.

**Kloudify (letto):** `docs/visione/controlli-e-conformita.md` §2 e `.claude/plans/2026-10-15-issue-998-pezzo-4/design.md`. Non esiste una cartella `docs/decisions`.

**Divergenze:**
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

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-C3-01 | Riuso in gravya-app-v2 | (a) portare i moduli esistenti; (b) riscriverli sullo stesso contratto; (c) usare gravya-app come servizio | test esistenti riusabili e debito ereditato | (a), con il contratto congelato |
| DA-C3-02 | Dove vive il nodo HITL | (a) solo LangGraph; (b) LangGraph più passo DAG Node; (c) motore unico dopo C1 | esito della decisione sul motore C1 | (a) in ondata 1, da riallineare a C1 |
| DA-C3-03 | Fonte del contratto condiviso | (a) Pydantic come fonte con TS generato; (b) Zod come fonte; (c) JSON Schema neutro | un solo punto di verità e niente drift | (c) proposta da validare |
| DA-C3-04 | TTL della richiesta | (a) 24 h fisse (codice attuale); (b) configurabile per azienda | casi d'uso di campagne lunghe | (a) in ondata 1 |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunti in "È richiesto da" C1, A3, B2, E3 ed E2 (condizionale), che dichiarano di dipendere da C3; span allineato al tipo `gravya.decision` (kind=hitl) di E1; segnalata la divergenza di convenzione dei nomi evento e l'evento C1 non consumato. Motivo: dipendenze dichiarate in un solo verso e interfacce non combacianti. |
