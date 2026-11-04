# gravya-app — HITL Kloud: TTL, sweeper, flusso di ripresa, override

Commit letti: gravya-app@349118b1 (come richiesto); gravya-app-kloudify@e43f15e (solo per contraddizioni documentali).
Sola lettura. Nessun checkout, nessuna modifica.

## Q1 — TTL delle richieste HITL (kloud_hitl)
- Valore: 24 h = `KLOUD_HITL_TTL_MS = 24 * 60 * 60 * 1000` (server/src/services/kloud-hitl-expiry-sweeper.ts:41). Fisso nel codice: nessuna lettura di env, DB o impostazione per azienda (nessun `process.env` nel file; grep su `TTL`/`HITL_TTL` nel repo non trova altri punti).
- Punti in cui il valore compare:
  1. server/src/services/kloud-hitl-expiry-sweeper.ts:41 — definizione della costante.
  2. server/src/services/kloud-hitl-expiry-sweeper.ts:190 — `cutoffIso = now - KLOUD_HITL_TTL_MS` (unico uso nel codice).
  3. server/src/services/kloud-hitl-expiry-sweeper.ts:17-19, 36-40 — commenti che dicono che 24 h replica `_ASK_KLOUD_HITL_TIMEOUT_HOURS` (vedi contraddizione C1).
  4. server/src/__tests__/998-p4-pr3b-decide-expire.pglite.test.ts:66, 339 — il test usa la costante.
  5. docs/compliance/audits/2026-11-02-scribe-wave-4r.md:130-131 e :420; docs/compliance/ai-act/system-register.md:280 — documentano le 24 h citando il sweeper.
- Valore separato, stesso numero, in un altro servizio: services/agents/src/job_queue/cron_dispatchers.py:89 `_ASK_KLOUD_HITL_TIMEOUT_HOURS = 24`, usato a :824 (SQL `interrupt_since < now() - make_interval(hours => ...)`) e :904. Non è condiviso con il server (nessun import né lettura cross-servizio): sono due costanti indipendenti.
- Il TTL del sweeper è misurato da `created_at` (pending) o `COALESCE(decided_at, created_at)` (approved non reclamato) o `payload.claimedAt` (claimed); il timer del cron agents è misurato da `gravya_ask_kloud_tasks.interrupt_since` (ledger). Due basi temporali diverse.

## Q2 — Sweeper (sweepKloudHitlApprovals)
Fonte: server/src/services/kloud-hitl-expiry-sweeper.ts. Ciclo ogni ora (:224 `SWEEP_INTERVAL_MS = 60*60*1000`), avviato da server/src/app.ts:751-752 e fermato a :771. Guard `running` (:231). Scansione cross-tenant con `bypassRls: true` (:203) su `type='kloud_hitl' AND status IN ('pending','approved')`; per ogni azienda, tre UPDATE in transazioni separate (:68-186).

Stati di partenza e azioni:
- `pending`, `created_at < cutoff` (:83-89) → `status='cancelled'`, activity `kloud.approval.expired` reason `pending_ttl_expired` (:99).
- `approved`, `payload->>'claimedAt' IS NULL`, `COALESCE(decided_at, created_at) < cutoff` (:117-122) → `status='cancelled'`, activity `kloud.approval.expired` reason `approved_unclaimed_ttl_expired` (:133).
- `approved`, `payload->>'claimedAt' IS NOT NULL`, `payload->>'outcome' IS NULL`, `claimedAt < cutoff` (:157-162) → NON cambia `status` (resta `approved`); `payload` ottiene `outcome='error'`, `outcomeCode='reaped'`, `executedAt=now` (:151-155); activity `kloud.approval.reaped`, reason `claimed_no_outcome` (:170-173).
- Riesecuzione della scrittura: NO. Il commento (:10-13) dice esplicitamente che la riga reclamata senza esito "is NEVER re-run here". Nel codice dello sweeper non c'è alcuna chiamata HTTP/agents né replay.
- Non tocca `gravya_ask_kloud_tasks` (nessun riferimento nel file): il ledger del run resta com'è (vedi Q3, C3).
- Le UPDATE hanno `company_id = $1` e la predicate di stato, quindi una decisione/claim concorrente vince (commento :63-67).

## Q3 — Flusso HITL completo (kloud_hitl)
Componenti e passi (verificato dove indicato):
1. Park. services/agents/src/executors/generic_executor.py:~700-760: un tool REQUIRES_HITL non viene eseguito; POST `/api/companies/{cid}/kloud/approvals` (:736). Lato server: server/src/routes/kloud-approvals.ts:98-193 inserisce `approvals` con `type='kloud_hitl'`, `status='pending'`, `requested_by_user_id=NULL`, `payload` = body + `runId`, `onBehalfOfUserId`, `requestedAt` (:156-166). Idempotenza su `idempotencyKey` (:137-154). Se la riga è `approved` e non reclamata, il re-park rigioca la riga (generic_executor.py ~:760, `replay_approved_write`).
2. Interrupt del grafo. services/agents/src/kloud/graph.py:1124 `node_interrupt_check`; `interrupt(...)` a :1205 (approval_required sull'output dell'executor). Il run va in GraphInterrupt in services/agents/src/api/runtime.py:~535-545 → `_write_task_status(status='waiting_approval', mark_interrupt=True)` (runtime.py:~200-330: `interrupt_since = COALESCE(interrupt_since, now())`). Notifica a `/internal/ask-kloud/task-notice` solo per `waiting_approval` e `completed` (runtime.py:317-337).
   Tabella ledger: `gravya_ask_kloud_tasks` (migrazione packages/db/src/migrations/0271_ask_gravya_tasks_status_ledger.sql).
3. Lettura lato UI: GET status (runtime.py ~1584-1600): se il checkpoint ha un interrupt e il ledger non è terminale, risponde `waiting_approval` con `payload`.
4. Decisione persona. Pagina approvals: server/src/routes/approvals.ts `/approvals/:id/approve` (~:340-400) e `/reject` (~:440-480). Richiede `approvals:decide` (:348), blocca auto-approvazione (:350-352), `svc.approve/reject` (server/src/services/approvals.ts:63-94: pending→approved/rejected, `decided_at`). Un secondo decide su riga già decisa → 409 `KLOUD_DECIDED_ALREADY` (approvals.ts:365, :443). Poi `recordKloudHitlDecided` e `resumeDecidedKloudThread` (approvals.ts:148-190) → `resumeKloudThread` (server/src/services/kloud-resume.ts:173-185) → POST `${GRAVYA_AGENTS_URL}/api/v1/resume/{runId}?company_id=…`, firmato HMAC.
   Alternativa: UI chat `POST /companies/:companyId/ask-kloud/resume/:taskId` (server/src/routes/ask-kloud.ts:~650-745) → stessa `resumeKloudThread`. ATTENZIONE: questa rotta non legge né aggiorna la riga `approvals` (grep `approvals` in ask-kloud.ts: solo commenti :649, :730). Vedi C4.
5. Resume nel runtime. services/agents/src/api/runtime.py `resume()` (~1690-1790): 400 senza company_id; 409 se non ci sono interrupt (:1760-1770); `_claim_resume` (runtime.py:1684): `UPDATE gravya_ask_kloud_tasks SET status='running', started_at=now(), interrupt_since=NULL WHERE status='waiting_approval' OR (status='running' AND started_at < now()-180s)`; 409 se perso. Poi `_resume_graph_background` (runtime.py ~580-640): entry write `running` con `resume_entry=True`, `graph.ainvoke(Command(resume=...))`.
   `_RESUME_RECLAIM_AFTER_SECONDS = 180` (runtime.py:1446).
6. Replay della scrittura. graph.py:1290-1320 chiama `replay_approved_write` (services/agents/src/kloud/write_replay.py) solo se la decisione è approvata: claim `POST /api/companies/{cid}/kloud/approvals/{id}/claim` (write_replay.py:191; route kloud-approvals.ts:195-265: UPDATE con `status='approved' AND claimedAt IS NULL AND runId = run`, activity `kloud.approval.claimed`), poi chiamata del tool (whitelist `WRITE_TOOLS` write_replay.py:~40-46), poi `POST .../outcome` (write_replay.py:203; route kloud-approvals.ts:267-334: scrive `outcome`, `executedAt`, `outcomeCode`; activity `kloud.approval.executed`).
7. Fine. Il grafo termina: runtime scrive `completed` (o `waiting_approval` se un nuovo interrupt, o `failed`). Se il processo muore: cron `_reclaim_ask_kloud_tasks` (cron_dispatchers.py:840-925) fa dead-letter dei `running` > 60 min (`_ASK_KLOUD_STUCK_RUNNING_RECLAIM_MINUTES = 60`, :88) e alerta gli `waiting_approval` con `interrupt_since` più vecchio di 24 h (:824, :904). L'alert NON cancella né riesegue.

Tabelle: `approvals` (type='kloud_hitl', status pending|approved|rejected|cancelled, payload jsonb con runId, tool, permissionKey, args, preview, idempotencyKey, claimedAt, outcome, outcomeCode, executedAt); `gravya_ask_kloud_tasks` (status: running|waiting_approval|completed|failed, interrupt_since, started_at); `activity_log` per le azioni `kloud.approval.parked|claimed|executed|expired|reaped`, `kloud.hitl_decided|hitl_forward_failed` (gravya event).

Contraddizioni documentali/codice: vedi sezione contraddizioni.

## Q4 — Override TTL per azienda/agenzia; soglia p95
- Override TTL: NO. `kloud_approval_settings` (packages/db/src/schema/kloud_approval_settings.ts:12-19; server/src/services/kloud-approval.ts:21-87) configura solo `approval_required` (boolean) per scope company/client/task — non il TTL. Nessun campo TTL nello schema né nelle rotte.
- Soglia p95 di ripresa: NON TROVATA. Nel repo non c'è una soglia di latenza per la ripresa HITL. Unica occorrenza di p95 non legata: doc/SPEC-implementation.md:739 "API p95 latency under 250 ms for standard CRUD at 1k tasks/agency" (generica CRUD, non HITL).

## Contraddizioni (senza scegliere)
- C1 — kloud-hitl-expiry-sweeper.ts:17-19 e :38 dicono che l'agents service "waits 24 hours for a HITL answer" (`_ASK_KLOUD_HITL_TIMEOUT_HOURS`). Nel codice agents quella costante (cron_dispatchers.py:89) serve solo a un alert di escalation (cron_dispatchers.py:814-824, :851-857, :891-907: "no automated remedy … ESCALATION ALERT"). Nessun codice cancella o fa scadere il thread del grafo dopo 24 h. Il commento del sweeper descrive un'attesa che il codice agents non applica. Inoltre il commento cita "services/agents/src/..." senza nome di file.
- C2 — doc/CRM_PLAN_RESOLVED.md:167 (E11): "`gravya-hitl.ts` returns 410 Gone + UI 'Approval window expired' … already in `gravya-hitl-boot.test.ts`". Nel codice: server/src/routes/gravya-hitl.ts non contiene nessun 410 (grep `410` nel file: nessun risultato; risposte 503/401/400/502/upstream status); il test gravya-hitl-boot.test.ts esiste ma verifica il boot, non un 410 (non letto in dettaglio). Inoltre gravya-hitl.ts non è montato in produzione: server/src/app.ts non lo importa (grep `gravyaHitlRoutes|routes/gravya-hitl` → solo test). Il file usa `approval.payload.task_id`, mentre il codice di scrittura usa `payload.runId` (kloud-approvals.ts:159; kloud-resume.ts:7).
- C3 — La documentazione del sweeper (wave-4r, :131) dice "the 24 h expiry for unresolved approvals"; ma il sweeper non tocca `gravya_ask_kloud_tasks`: la riga `approvals` diventa `cancelled` mentre il ledger del run può restare `waiting_approval` (nessuna scrittura cross-tabella nel file). L'alert agents scatta comunque dopo 24 h da `interrupt_since`. Due timer che non si coordinano.
- C4 — Path di decisione: approvals page (approvals.ts) aggiorna la riga e poi riprende il thread; la rotta chat `ask-kloud/resume` (ask-kloud.ts ~:650-745) riprende il thread senza toccare `approvals`. Se un thread `kloud_hitl` è ripreso dalla chat con approved=true, la riga resta `pending`, e il claim (kloud-approvals.ts:207 richiede `status='approved'`) fallisce → la scrittura è rifiutata. Non ho trovato nel codice se la UI usa la rotta chat per i thread kloud_hitl (non verificato).
- C5 — Documentazione kloudify (fuori ambito gravya-app, solo riferimento): .claude/plans/2026-10-15-paperclip-removal/README.md:33 dice "`kloud_hitl` è morto … Il webhook `routes/gravya-hitl.ts:77` non ha chiamanti fuori dai test"; .claude/plans/2026-10-22-issue-2470/plan.md:79 dice "No server code acts on an approved `kloud_hitl`". Entrambi sono in contrasto con il codice di gravya-app@349118b1 (kloud-approvals.ts e approvals.ts agiscono su kloud_hitl). Sono piani datati; il codice di gravya-app è più recente. Riportato senza scegliere.
- C6 — docs/compliance/audits/2026-11-02-scribe-wave-4r.md:131 "introduces a 24 h expiry for unresolved approvals; rows are cancelled, not deleted" — vero per pending/approved-unclaimed; per claimed-senza-esito la riga NON è cancellata ma marcata `reaped` (sweeper :157-173). Dettaglio omesso nel doc.

## Fuori perimetro (segnalazioni)
- server/src/routes/gravya-hitl.ts: webhook HMAC non montato in app.ts; `HITL_WEBHOOK_SECRET` è in server/src/index.ts:141 (prodRequired). Nessun segreto letto né riportato.
- services/agents/src/automation/handlers/c2_hitl_timeout.py è un altro HITL (automazioni, run `gravya_automation_runs`, warning 24 h / cancel 48 h, default in :35-36): non è il flusso kloud_hitl. Non approfondito oltre.
- Nessun segreto o credenziale è stato copiato nel report.

## Non trovato
- TTL configurabile da env/DB/azienda: non trovato (verifica: grep TTL/HITL_TTL/timeout in server, services/agents, packages).
- Soglia p95 o misura di latenza della ripresa HITL: non trovata.
- Chiamata della UI chat `ask-kloud/resume` per i thread kloud_hitl: non verificato (solo server e agents letti; apps/ui non letta, fuori dal perimetro di questa domanda).
- Test `gravya-hitl-boot.test.ts` non letto nel dettaglio (solo citato).

## Letture
- server/src/services/kloud-hitl-expiry-sweeper.ts: 1-264 di 264
- server/src/services/kloud-approval.ts: 1-145 di 145
- server/src/services/kloud-resume.ts: 1-41 di 41
- server/src/routes/kloud-approvals.ts: 1-337 di 337
- server/src/routes/approvals.ts: 36-200 di ~600; 340-480 di ~600 (parziale)
- server/src/routes/ask-kloud.ts: 640-745 (parziale; grep su `approvals`, `kloud_hitl`)
- server/src/routes/gravya-hitl.ts: 1-40 di 158 + grep (parziale)
- server/src/services/approvals.ts: grep (decided_at, applied) + 60-95 (parziale)
- server/src/app.ts: grep (import/mount)
- services/agents/src/job_queue/cron_dispatchers.py: 75-100 + 790-930 (parziale; file non intero)
- services/agents/src/api/runtime.py: 200-330, 520-560, 575-640, 1440-1500, 1580-1860 (parziale)
- services/agents/src/kloud/write_replay.py: 1-60 + 170-230 di 355 (parziale)
- services/agents/src/kloud/graph.py: 1124-1140, 1185-1215, 1290-1345 (parziale)
- services/agents/src/executors/generic_executor.py: 700-760 (parziale)
- services/agents/src/automation/handlers/c2_hitl_timeout.py: 1-70 di ~110 (parziale)
- packages/db/src/schema/kloud_approval_settings.ts: grep (parziale)
- doc/CRM_PLAN_RESOLVED.md:167 (grep); docs/compliance/audits/2026-11-02-scribe-wave-4r.md:130-131, 420 (grep)
- docs/compliance/ai-act/system-register.md:280 (grep)
- gravya-app-kloudify: .claude/plans/2026-10-15-paperclip-removal/README.md:33 e .claude/plans/2026-10-22-issue-2470/plan.md:79 (grep)
