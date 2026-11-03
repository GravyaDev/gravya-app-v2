# E1 — Tracing distribuito

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E1 |
| Nome | Tracing distribuito |
| Componente padre | E — Osservabilità e Valutazione |
| Ondata | 1 (walking skeleton) |
| Versione documento | 1.1 |
| Data | 2026-11-03 |

## 2. Scopo

**Cosa fa.** Strumenta con OpenTelemetry ogni esecuzione agente producendo una traccia correlata con span per: chiamata LLM, invocazione tool, retrieval, punto di decisione (policy/HITL). Gli attributi seguono le OpenTelemetry GenAI semantic conventions, così E3 può agganciare punteggi agli span e nessun backend è vincolante (master plan, "Osservabilità e valutazione").

**Cosa NON fa.** Non è l'eval harness (E3), non è il registry dei prompt (E2), non sostituisce l'audit legale (A5, `gravya_event_logs`), non è error tracking (resta GlitchTip). Non sceglie un vendor di visualizzazione.

**Perché esiste.** Master plan, principio 1 e §"Errori da evitare": senza tracing non si fanno eval, senza eval non si concede autonomia. È il primo componente, non l'ultimo.

## 3. Contesto e dipendenze

**Dipende da:** nessun sottoprodotto per esistere; per popolare gli span di tipo specifico serve l'aggancio a B1 (runtime agente), B2 (tool gateway), C1 (grafo workflow), A3 (decisioni di enforcement), C3 (HITL).

**È richiesto da:** B1, B2, C1, A3, C3, A1 (dichiarano di emettere span o eventi tracciati: vedi la tabella 4.1), E3 (eval offline, legge le tracce), E2 (riferimento prompt/versione negli span), E-successivi di guardrail telemetry e valutazione online (ID non assegnati nel master: Non verificato), A5 (audit trail, correlazione per `trace_id`).

**Assunzioni (non verificate):** esiste o verrà deciso un collector OTLP raggiungibile da `server/` (Node) e `services/agents/` (Python); i servizi possono propagare `traceparent` W3C su HTTP interno e sulla coda arq.

## 4. Contratti

### 4.1 Tipi di span

| Span | `gen_ai.operation.name` / nome | Attributi minimi | Emesso da |
|---|---|---|---|
| LLM | `chat` / `text_completion` | `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` | B1 / `llm-dispatch` |
| Tool | `execute_tool` | `gen_ai.tool.name`, `gen_ai.tool.call.id`, esito | B2 |
| Agente | `invoke_agent` | `gen_ai.agent.id`, `gen_ai.agent.name` | B1 |
| Retrieval | nome da DA-E1-04 | sorgente, n. risultati | pipeline memoria |
| Decisione | `gravya.decision` (attributi custom, namespace `gravya.*`) | `gravya.decision.kind` (policy/hitl/router), `gravya.decision.outcome`; se `kind=policy` anche `gravya.policy.bundle_version`, `gravya.policy.bundle_hash` (richiesti da A3) | A3, C3, C1 |
| Caso di eval | `gravya.eval.case` | `gravya.eval.case_id`, `gravya.eval.pass` (richiesti da E3) | E3 |

Attributi comuni Gravya: `gravya.company_id` (tenant, obbligatorio), `gravya.run_id`, `gravya.execution_ticket_id`; sugli span LLM `gravya.prompt.key`, `gravya.prompt.version`, `gravya.prompt.hash` (da E2); sugli span di C1 `gravya.workflow.id`, `gravya.workflow.version`, `gravya.workflow.node_id`. I nomi `gravya.policy.*`, `gravya.eval.*`, `gravya.prompt.*` e `gravya.workflow.*` sono stati unificati in revisione (v1.1) a partire da ciò che A3, E3, E2 e C1 dichiaravano di emettere: proposta da validare. I nomi `gen_ai.*` vanno allineati alla versione delle convenzioni scelta (le GenAI conventions sono in stato "Development": Non verificato quale versione adottare).

### 4.2 Contenuti

Per default **nessun contenuto di prompt/risposta** negli span (coerente con la decisione kloudify «non prompt e risultati»). Cattura contenuti solo se DA-E1-02 la autorizza.

## 5. Interfacce

- **Esportazione:** OTLP (gRPC o HTTP) verso un collector; il backend è sostituibile (DA-E1-03).
- **Propagazione:** header W3C `traceparent` tra `server/` e `services/agents/`; campo equivalente nei job arq.
- **Correlazione con audit:** `trace_id` scritto nel payload di `llm.inference` e di `gravya_tool_invocations` (oggi assente: issue #264 "not landed" citata in `timeline-engine.ts`).
- **API applicativa:** un helper per linguaggio (`startGenAiSpan`) che impone `gravya.company_id`.

## 6. Comportamento

**Flusso principale** (ricavato dai contratti §4-5 e dai requisiti §7; nessun comportamento nuovo introdotto in revisione):
1. All'avvio di un run il chiamante (B1, oppure C1 per un workflow) apre lo span radice tramite l'helper `startGenAiSpan`, che impone `gravya.company_id`.
2. Le chiamate verso altri servizi propagano `traceparent` (HTTP interno, job arq); i figli (LLM, tool, retrieval, decisione) si agganciano alla stessa traccia.
3. Gli span vengono esportati via OTLP al collector (DA-E1-03) dopo la redazione.

**Casi limite:**
- Collector irraggiungibile: l'esecuzione prosegue (fail-open, §7); la perdita di span non blocca il run.
- Contenuti di prompt/risposta: non registrati salvo DA-E1-02.
- Span senza `gravya.company_id`: Non verificato come debba comportarsi l'helper (rifiuto o scarto); da definire in fase 1.

## 7. Requisiti non funzionali

- **Multi-tenancy:** ogni span porta `gravya.company_id`; l'accesso in lettura alle tracce è filtrato per tenant (motivo dello scarto di Phoenix, #266).
- **PII:** redazione prima dell'export; `redactAll` esistente è solo key-based (vedi `timeline-engine.ts`), quindi non basta per testo libero.
- **Overhead:** latenza aggiunta p95 < 5 ms per span (proposta da validare).
- **Fail-open:** il collector giù non blocca le esecuzioni.
- **Retention:** da DA-E1-02 (AI Act art. 12/19: ≥6 mesi solo se alto rischio, secondo `controlli-e-conformita.md` §5 riportato da ricognizione, non letto).

## 8. Criteri di accettazione

1. Un'esecuzione agente di test produce una traccia unica con ≥1 span per ciascun tipo (LLM, tool, retrieval, decisione): test d'integrazione con exporter in-memory, 100% dei tipi presenti.
2. `traceparent` propagato server→agents: test che verifica stesso `trace_id` su entrambi i lati.
3. 100% degli span ha `gravya.company_id` non nullo: test sul set esportato.
4. Nessun attributo `gen_ai.input.messages`/`gen_ai.output.messages` presente con flag contenuti disattivato: test.
5. Collector irraggiungibile → l'esecuzione termina con successo: test.
6. Overhead p95 < 5 ms/span su benchmark (proposta da validare).
7. `trace_id` presente nel payload di `llm.inference` per il 100% delle chiamate da `llm-dispatch.ts`: test pglite.

## 9. Piano di implementazione

1. Fase 0: chiudere DA-E1-01 e DA-E1-02.
2. Fase 1: SDK OTel in `server/` e `services/agents/` (oggi non tra le dipendenze dichiarate), exporter configurabile, fail-open; trasformare l'hook TODO di `councils/runtime.py` in uso reale.
3. Fase 2: span LLM in `llm-dispatch.ts` e scrittura `trace_id` in `llm.inference` (#264).
4. Fase 3: span tool in `tools/_audit.py` / B2; propagazione `traceparent` e job arq.
5. Fase 4: span retrieval e decisione (A3, C1, C3).
6. Fase 5: redazione, filtro tenant in lettura, test §7.

**Tecnologie:** OpenTelemetry (master plan), condizionato a DA-E1-01.

## 10. Test e valutazione

Unit (helper attributi), integrazione con exporter in-memory (criteri 1-5, 7), test pglite su `llm.inference`, benchmark overhead (6), test di isolamento tenant in lettura.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Contraddice la decisione 2026-06-15 "NO OpenTelemetry" | DA-E1-01 esplicita prima di implementare |
| PII/contenuti dei clienti nelle tracce | default senza contenuti; gravya-app#1925 |
| Convenzioni GenAI instabili | versione fissata, mapping in un solo modulo |
| Doppia verità tracce vs timeline DB | DA-E1-01 opzione B |

## 12. Stima e priorità

- **Taglia:** M (L se DA-E1-01 sceglie A, per la migrazione della Timeline).
- **Dipendenze critiche:** DA-E1-01 (OTel contro Timeline DB-native) e DA-E1-02.
- **Thin-slice MVP:** sì, ondata 1.

## Appendice A — Allineamento con lo stato attuale

Letti:
- `gravya-app/server/src/services/timeline-engine.ts`: Timeline DB-native su `gravya_event_logs`, intestazione «NO OpenTelemetry, NO new vendor (plan §F.1, 2026-06-15)»; correlazione per company_id/created_at/agent/session/execution_ticket perché manca `trace_id` (#264). Riusabile come vista audit e modello di proiezione PII-safe (`summary` whitelist).
- `gravya-app/server/src/routes/superadmin-observability.ts`: route operatore cross-tenant con `assertInstanceAdmin` e bypass RLS. Riusabile come pattern di accesso.
- `gravya-app/server/src/observability/error-tracking.ts`: Sentry→GlitchTip solo errori, `enableOpenTelemetrySetup: false`.
- `gravya-app/services/agents/src/councils/runtime.py`: hook OTel opzionale (span `council.invoke`), fallback no-op, «TODO Phoenix span».
- `gravya-app/server/src/routes/llm-dispatch.ts` (righe con `llm.inference`) e `server/src/services/audit-event-kinds.ts`: evento `llm.inference` già emesso: punto d'aggancio naturale.
- `gravya-app/services/agents/src/tools/_audit.py`: righe begin/end in `gravya_tool_invocations`.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` (~r.178): Phoenix adottato 13/04, scartato 15/06 per multi-tenancy debole (#266); timeline senza prompt e risultati.

**Divergenze dal master:** (1) il codice esclude OTel per decisione esplicita; (2) Phoenix scartato per multi-tenancy, requisito che il master non cita; (3) niente `trace_id` né `traceparent`; (4) nessun contenuto prompt registrato, mentre eval GenAI tipicamente lo richiede; (5) span di retrieval e decisione inesistenti; (6) letture del router Kloud non passano dall'audit (da ricognizione kloudify).

## Appendice B — Non verificato

- Piano `.claude/plans/2026-06-15-phoenix-wave-d-trace-timeline/README.md` e §F.1 citato: non letti.
- Stato di #264, #266, #1925: non verificato sul tracker.
- `controlli-e-conformita.md` §5 e `docs/start/architecture.md`: non letti direttamente.
- Presenza di `opentelemetry` nei lockfile (non trovato in `services/agents/pyproject.toml` né `server/package.json` via grep; lockfile non controllati).
- Versione delle GenAI semantic conventions da adottare e nomi esatti degli attributi.
- ID dei sottoprodotti E di guardrail telemetry/eval online.
- Soglia overhead 5 ms: proposta da validare.

## Appendice C — Decisioni aperte

- **DA-E1-01 — OpenTelemetry vs Timeline DB-native.** Opzioni: (A) OTel completo, Timeline dismessa; (B) OTel per il tracing + Timeline/`gravya_event_logs` restano audit, correlate da `trace_id`; (C) restare DB-native (diverge dal master). Criterio: aderenza al master, multi-tenancy, costo di migrazione. Raccomandazione: B.
- **DA-E1-02 — Cattura contenuti prompt/risultati.** Opzioni: (A) mai; (B) opt-in per tenant con redazione; (C) solo in ambienti non di produzione. Criterio: base legale (#1925), necessità di E3. Raccomandazione: C fino a esito #1925.
- **DA-E1-03 — Backend delle tracce.** Opzioni: (A) collector OTel + storage self-hosted OTLP-compatibile; (B) export in PostgreSQL via collector, letto dalla Timeline; (C) piattaforma eval OTLP-compatibile. Criterio: multi-tenancy, no lock-in, self-hosting (coerente con GlitchTip). Raccomandazione: nessuna tecnologia specifica è indicata dal master o dal codice; scegliere tra A e B dopo DA-E1-01.
- **DA-E1-04 — Rappresentazione di retrieval e decisione.** Opzioni: (A) span custom `gravya.*`; (B) eventi su span esistenti. Criterio: interrogabilità in E3. Raccomandazione: A.

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: sezioni 6-12 riordinate secondo il template (aggiunta §6 Comportamento ricavata dal contenuto esistente; Decisioni aperte spostate dalla §9 all'Appendice C, eliminando il duplicato); aggiunti in §3 i sottoprodotti che dichiarano di emettere span; in §4.1 aggiunti gli attributi che A3, E2, E3 e C1 dichiarano di emettere (`gravya.policy.*`, `gravya.prompt.key/version/hash` al posto di `gravya.prompt.ref`, `gravya.eval.*`, `gravya.workflow.*`). Motivo: allineamento delle interfacce tra documenti scritti in parallelo. |
