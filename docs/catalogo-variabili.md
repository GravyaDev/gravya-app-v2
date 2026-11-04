# Catalogo delle variabili di piattaforma

**Versione:** 1.0 · **Data:** 2026-11-04 · **Stato:** primo catalogo, da validare con A6 e F6.

## 1. Scopo e regole

Questo documento è l'unico punto di verità per nome, default, intervallo ammesso, chi modifica e pagina di UI di ogni durata, soglia, limite o parametro dei documenti dell'ondata 1 (A1, A3, B1, B2, C1, C3, E1, E2, E3). Lo prevede DX-22(c). La regola di fondo è quella dell'utente (DX-22): «TUTTO DEVE ESSERE CONFIGURABILE DA UI SUPERADMIN O ADMIN AGENZIA, NIENTE HARDCODED MAI».

Regole d'uso:

1. **I documenti di dettaglio citano solo il nome** della variabile, senza ripetere default e intervalli.
2. **Minimo, massimo e valori decisi stanno qui**, non solo i default. Il codice li legge dal registro e non li replica come costanti.
3. **Il modello** (registro versionato, ruoli, pagine di UI) è di A6 (DX-14, decisa il 2026-11-03). A6 non è ancora documentato (ondata 2): le pagine indicate sono **provvisorie** finché A6 non le fissa.
4. **Variabile non leggibile o non valida (DX-17).** Le azioni si bloccano (fail-closed). Le cancellazioni programmate usano l'ultimo valore valido versionato. In entrambi i casi parte un segnale ad A5. Per la chiusura per TTL di una richiesta HITL vale DA-C3-08 (a): ultimo valore valido versionato e segnale ad A5.
5. **Ogni modifica** è versionata e auditata (DX-13). Il superadmin gestisce le variabili di piattaforma; l'admin agenzia solo quelle indicate come tali.
6. **Vincoli normativi (DX-22(a)).** Sono configurabili solo verso valori più restrittivi della norma. Il limite di legge è catalogato con il riferimento al registro `norme-di-riferimento.md`. Lo modifica solo il superadmin, con motivazione e audit.
7. **Credenziali (DX-22(b)).** Non sono nel catalogo come valori: §15.

**Assunzione sui nomi.** La convenzione dei nomi (DX-07) è ancora aperta. Qui si assume la notazione puntata in minuscolo con l'unità nel nome. Suffissi usati: `_ms`, `_s`, `_minutes`, `_hours`, `_days`, `_months`, `_bytes`, `_mb`, `_usd`, `_eur`, `_percent`, `_count`. Se DX-07 cambia, si rinominano le righe qui e i documenti che le citano.

**Legenda delle colonne.** *Tipo*: `ordinaria` oppure `vincolo normativo` con la norma. *Stato del valore*: `deciso` con riferimento, `proposta da validare` (il valore non deriva da una decisione) oppure `da definire` (nessun documento né decisione lo fissa). *Intervallo*: minimo e massimo, oppure `da definire` con il motivo.

**Regola retention (RR).** Il superadmin modifica solo il valore di default, e solo entro l'intervallo minimo-massimo fissato nel contratto/DPA con le agenzie (DX-15, DX-16). L'intervallo non è ancora definito (F6): vedi DA-CV-01. L'override per agenzia è previsto nel modello ma si attiva solo quando l'intervallo è definito; fino ad allora valgono i default (DX-09, DA-C3-09). L'admin agenzia quindi non modifica nessuna durata di retention.

## 2. Retention (Piattaforma → Retention)

Politica unica di default (DX-09). Durate approvate dall'utente il 2026-11-03 (DECISIONS §5); la verifica legale e sui contratti con le agenzie resta consigliata. Nessuna norma fissa un valore per queste classi: sono scelte di minimizzazione (GDPR art. 5(1)(e)). L'applicazione è di F6 (DX-12).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `retention.traces_days` | 90 giorni | superadmin (RR) | da definire: contratto/DPA non definito (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09) | E1 (tracce e segmenti), C1, B2, C3 (tracce delle transizioni HITL). I contatori di perdita dei segmenti di E1 sono assegnati a questa classe: proposta da validare |
| `retention.runtime_events_days` | 90 giorni | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09) | A1 (`graph.*`), A3 (`policy.bundle.*`), B1 (`runtime.*`), C1 (`workflow.*`), E2 (`prompt.version.*`: assegnazione alla classe proposta da validare) |
| `retention.audit_decisions_months` | 12 mesi | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09; audit delle mutazioni A1: DECISIONS §4) | A1 (audit mutazioni), A3 (record di decisione), B2 (audit dei tool), C3 (decisioni e feedback), E2 (attivazioni) |
| `retention.cross_tenant_access_log_months` | 12 mesi | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09). Il log appartiene ad A6 (DX-18) | A1, A3, B1, B2, C1, C3, E1, E2, E3 |
| `retention.sensitive_payload_days` | 30 giorni dopo la decisione o l'esecuzione; poi resta l'hash | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09) | C3 (`arguments`, `context`), B2 (anteprime redatte) |
| `retention.run_state_days` | 30 giorni dopo la chiusura del run | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09) | C1 (stato), C3 (checkpoint in pausa), B1 (checkpoint via B5) |
| `retention.incident_evidence_months` | durata del caso + 12 mesi, sospendendo le altre scadenze per quei dati | superadmin (RR) | da definire (DA-CV-01). Meccanismo di sospensione da definire in F6 e A5 | ordinaria | deciso (DECISIONS §5, riga modificata il 2026-11-04: motivazioni art. 23(4) direttiva, GDPR artt. 17(3)(e) e 5(2)) | B1, B2, C1, C3, E1, E2 |
| `retention.eval_reports_months` | 12 mesi | superadmin (RR) | da definire (DA-CV-01) | ordinaria | deciso (DECISIONS §5, DX-09) | E3 (report e segmenti `eval_case`), E1 |
| `retention.tenant_offboarding_days` | 30 giorni dalla fine del contratto: restituzione o cancellazione, salvo obblighi di legge | superadmin (RR) | da definire (DA-CV-01) | ordinaria. Possibile vincolo Data Act artt. 25 e 29: non verificato (registro ◐) | default deciso (DECISIONS §5, art. 28(3)(g) GDPR, che non fissa una durata); compatibilità con il Data Act da riportare (DECISIONS §4) | A1, C1, E1, E2 |
| `retention.class_override_enabled` | falso | superadmin | solo falso/vero; vero richiede l'intervallo di classe definito | ordinaria | deciso (DX-09: override per classe previsto nel modello, non attivo) | E1 (`retention_class`), tutti |
| `retention.tenant_override_enabled` | falso | superadmin | vero solo quando l'intervallo del contratto/DPA è definito (F6) | ordinaria | deciso (DA-C3-09, DX-15) | tutti |

**Famiglia protetta (DX-16).** Ogni variabile `retention.*_days` o `retention.*_months` ha due variabili gemelle di intervallo, `<nome>_min` e `<nome>_max`, con lo stesso suffisso di unità. Default: da definire (contratto/DPA, F6). Le modifica il superadmin con motivazione e audit. Un valore di durata fuori dall'intervallo non è valido (DX-16). Tipo: ordinaria. Stato: da definire (DA-CV-01).

**Classi senza durata variabile** (DX-21: le assegna F6 e i documenti le citano come tali): artefatti di configurazione (versioni di prompt, bundle di policy, definizioni di workflow, catalogo tool: «per tutta la durata del servizio», DECISIONS §5); nodi ed edge del grafo A1 (classe non assegnata: A1 App. B); `outputs_ref` di B1; contatori di rate limit, esiti per `idempotency_key` e token di approvazione consumati di B2; token consumati. Per le ultime tre categorie nessuna durata è fissata in DECISIONS §5.

## 3. HITL (Piattaforma → HITL; Agenzia → Approvazioni)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `hitl.request_ttl_hours` | 24 h | superadmin: default e limiti; admin agenzia: valore della propria agenzia entro i limiti (DA-C3-04) | tra `hitl.request_ttl_hours_min` e `hitl.request_ttl_hours_max` | ordinaria | deciso (DA-C3-04, 2026-11-03) | C3 (§6, sweeper) |
| `hitl.request_ttl_hours_min` | 1 h | superadmin | numero intero positivo e ≤ `hitl.request_ttl_hours_max`. Estremi assoluti: da definire, nessuna decisione li fissa (DA-CV-02) | ordinaria | deciso (DA-C3-04) | C3 |
| `hitl.request_ttl_hours_max` | 168 h | superadmin | intero ≥ `hitl.request_ttl_hours_min`. Estremi assoluti: da definire (DA-CV-02) | ordinaria | deciso (DA-C3-04) | C3 |
| `hitl.sweeper_interval_minutes` | da definire | superadmin | da definire: nessun documento fissa la frequenza dello sweeper; determina il ritardo massimo tra scadenza e chiusura (DA-CV-03) | ordinaria | da definire | C3 (§6, AC-6) |
| `hitl.resume_latency_p95_ms` | 2000 ms | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare | C3 (§7) |
| `hitl.approval_required_default` | vero («approvazione richiesta» di default) | admin agenzia, per azienda, cliente e task (C3 §2, §5); default di piattaforma: chi lo modifica è da definire (DA-CV-05) | vero/falso | ordinaria | requisito ripreso da C3 §3; nessuna riga di DECISIONS | C3, A3 |

Chiusura per TTL (DA-C3-08 (a)): scadenza programmata che usa l'ultimo valore valido versionato; la chiusura porta solo alla non esecuzione. Se il valore letto è fuori da `hitl.request_ttl_hours_min`/`_max`, non è valido (DX-16, DX-17).

## 4. Enforcement e latenze (Piattaforma → Enforcement e latenze)

Le tre soglie di latenza sono budget separati, usati per gli alert e non per bloccare (DECISIONS §6, decisa il 2026-11-03: «tutti proposte da validare con misura»). Per evitare la doppia scrittura, record di decisione di A3 e audit `tool.invoked` di B2 stanno in un'unica transazione eseguita da B2.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a3.latency.eval_p99_ms` | 5 ms (valutazione, escluso il trasporto) | superadmin | da definire (DA-CV-02) | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3 (§7, CA5) |
| `a3.latency.persist_p99_ms` | 20 ms (salvataggio sincrono del record) | superadmin | da definire (DA-CV-02) | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3, B2 |
| `a3.latency.total_p99_ms` | 25 ms (totale per azione) | superadmin | da definire (DA-CV-02). Con i default proposti vale 5 + 20 = 25 ms; il legame tra i tre valori non è fissato da DECISIONS §6 | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3, B2 |
| `a3.bundle.max_age_s` | da definire | superadmin | da definire: A3 richiede un valore minimo valido per il ripiego fail-closed (A3 §4) (DA-CV-02) | ordinaria | proposta da validare (A3 §4, senza valore) | A3 (§4, §6) |
| `a3.eval.timeout_ms` | da definire | superadmin | da definire, con minimo valido (DA-CV-02) | ordinaria | proposta da validare (A3 §4, senza valore) | A3 (§4, §6, CA11) |
| `a3.record.persist_timeout_ms` | da definire | superadmin | da definire, con minimo valido (DA-CV-02) | ordinaria | proposta da validare (A3 §4, senza valore) | A3 (§4, §6) |

## 5. Grafo dei mandati (Piattaforma → Grafo mandati)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a1.delegation.max_depth` | 3 | superadmin | da definire; minimo tecnico 1 (DA-CV-02). Si applica alle nuove deleghe, non retroattivamente | ordinaria | proposta da validare (A1 §4.5) | A1 (§4.2, CA5, CA11) |
| `a1.artifact.max_properties_bytes` | 4 KB (A1 non dice se 4.000 o 4.096 byte) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (A1 §4.5) | A1 (CA7) |
| `a1.sweeper.interval_minutes` | da definire | superadmin | da definire: determina il ritardo massimo tra `valid_until` e lo stato `expired` (DA-CV-03) | ordinaria | da definire (A1 §4.5) | A1 (§6, CA4) |

## 6. Runtime agenti (Piattaforma → Runtime agenti)

Per i limiti del job B1 §4 parla di «tetti e valori di default» come variabili di piattaforma; il `JobSpec` può solo restringerli. Si assumono due variabili per limite, `_default` e `_max` (Non verificato: B1 non dice se siano distinte). I valori del sistema precedente (300 s di timeout arq in gravya-app; 10 minuti, $2 e 8 giri di tool per run, riferiti da kloudify) sono riferimenti e non default di v2.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `b1.job.wall_s_default` | da definire | superadmin | da definire; ≤ `b1.job.wall_s_max` (DA-CV-02) | ordinaria | proposta da validare (B1 §4, senza valore) | B1 (§4, CA11) |
| `b1.job.wall_s_max` | da definire | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare | B1 |
| `b1.job.memory_mb_default` | da definire | superadmin | da definire; ≤ `b1.job.memory_mb_max` | ordinaria | proposta da validare | B1 (§4) |
| `b1.job.memory_mb_max` | da definire | superadmin | da definire | ordinaria | proposta da validare | B1 |
| `b1.job.pids_default` | da definire | superadmin | da definire; ≤ `b1.job.pids_max` | ordinaria | proposta da validare | B1 (§4) |
| `b1.job.pids_max` | da definire | superadmin | da definire | ordinaria | proposta da validare | B1 |
| `b1.job.tool_turns_default` | da definire | superadmin | da definire; ≤ `b1.job.tool_turns_max` | ordinaria | proposta da validare | B1 (§4) |
| `b1.job.tool_turns_max` | da definire | superadmin | da definire | ordinaria | proposta da validare | B1 |
| `b1.job.cost_usd_default` | da definire | superadmin | da definire; ≤ `b1.job.cost_usd_max` | ordinaria | proposta da validare | B1 (§4) |
| `b1.job.cost_usd_max` | da definire | superadmin | da definire | ordinaria | proposta da validare | B1 |
| `b1.job.kill_grace_s` | 5 s oltre `wall_s` | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (B1 CA4) | B1 (CA4) |
| `b1.host.max_concurrent_jobs` | da definire | superadmin | da definire | ordinaria | proposta da validare (B1 §7, senza valore) | B1 (§7) |
| `b1.tenant.max_concurrent_jobs` | da definire | superadmin | da definire. B1 §7 dice «quota per tenant» senza unità: assunzione «job concorrenti» (DA-CV-06) | ordinaria | proposta da validare (B1 §7, senza valore) | B1 (§7) |

## 7. Tool gateway (Piattaforma → Tool gateway)

Il catalogo dei tool (B2 §4) contiene anche «limiti di default» per tool, gestiti dall'interfaccia amministrativa del catalogo del superadmin (B2 §5). Gli ultimi tre parametri sono **impliciti**: nessun documento li fissa, ma servono al comportamento descritto (token monouso, coda di recupero «fino a riuscirci»).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `b2.rate_limit.default_calls_per_minute` | da definire | superadmin | da definire. Granularità (agente, tool, tenant) da decidere (DA-CV-06) | ordinaria | proposta da validare (B2 §5, senza valore) | B2 (§5, CA4) |
| `b2.recovery_queue.retry_interval_s` | da definire | superadmin | da definire (DA-CV-03) | ordinaria | da definire (parametro implicito, B2 §6) | B2 (§6, CA10) |
| `b1.run_token.ttl_s` | da definire | superadmin | da definire; ≤ `b1.job.wall_s_max` come criterio, non come decisione (DA-CV-03) | ordinaria | da definire (parametro implicito, B2 §3-§4) | B1, B2 |
| `hitl.approval_token.ttl_s` | da definire | superadmin | da definire (DA-CV-03) | ordinaria | da definire (parametro implicito, C3 §6, B2 §6) | C3, B2, A3 |

## 8. Workflow (Piattaforma → Workflow)

Il campo `max_steps`/`max_duration_ms` di una definizione può solo restringere i tetti di piattaforma (C1 §4.1).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `c1.max_steps` | 500 | superadmin | da definire; minimo tecnico 1 (DA-CV-02) | ordinaria | proposta da validare (C1 §4.1) | C1 (§4.1, §6, CA10) |
| `c1.max_duration_ms` | 300000 ms (5 min) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (C1 §4.1) | C1 (§4.1, §6, CA10) |

## 9. Tracing (Piattaforma → Tracing)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `e1.write_buffer_size` | da definire (unità non specificata da E1: segmenti o byte) | superadmin | da definire (DA-CV-02) | ordinaria | da definire (E1 §5, «non fissati») | E1 (§5, §6) |
| `e1.segment_loss_alert_threshold` | da definire (unità e finestra non specificate) | superadmin | da definire (DA-CV-02, DA-CV-07) | ordinaria | da definire (E1 §5, «non fissati») | E1 (§5), A5 |
| `e1.partition_interval_months` | 1 (partizioni mensili) | superadmin | da definire; effetto sulle partizioni esistenti non descritto (DA-CV-02) | ordinaria | proposta da validare (E1 §4.1) | E1 (§4.1) |

## 10. Prompt (Piattaforma → Prompt)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `e2.cache.max_ttl_s` | 60 s | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E2 §7) | E2 (§7) |
| `e2.rollback.propagation_max_s` | 60 s | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E2 §7) | E2 (§7, CA2, CA13) |
| `e2.template.pii_check_mode` | `block` | superadmin | `block` oppure `warn` | ordinaria | proposta da validare (E2 §7) | E2 (§7, CA13) |

## 11. Eval (Piattaforma → Eval)

Il job CI legge un'istantanea versionata delle variabili (E3 §5). Finché il registro non esiste l'istantanea è un file nel repository modificabile solo tramite PR: è un ripiego dell'ondata 1, non soddisfa DX-22 (vedi §17).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `eval.gate.pass_rate_min_percent` | 90 | superadmin | da definire; massimo tecnico 100 | ordinaria | proposta da validare. Il default è oggetto di DA-E3-07 (aperta: E3 AC4 propone 90 % più zero bloccanti; DA-E3-07 raccomanda 100 % sui bloccanti e solo report sul resto) | E3 (§5, AC4) |
| `eval.gate.max_blocking_failures_count` | 0 | superadmin | da definire; minimo tecnico 0 | ordinaria | proposta da validare (E3 AC4, DA-E3-07) | E3 (AC4), C3 (§10, soglia di fermate) |
| `eval.run.cost_cap_usd` | da definire | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E3 §7, senza valore) | E3 (§5, §6, §7) |
| `eval.run.timeout_s` | da definire | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E3 §5, senza valore) | E3 (§5) |
| `eval.ingestion.timeout_s` | da definire | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E3 §6, senza valore) | E3 (§6, R4 e R5) |
| `eval.run.repetitions_count` | 1 | superadmin | da definire (N da validare, DA-E3-05) | ordinaria | proposta da validare; DA-E3-05 aperta | E3 (DA-E3-05) |

## 12. Soglie di prestazione (Piattaforma → Soglie di prestazione)

Obiettivi misurabili con metrica a runtime: servono sia per gli alert sia come soglia dei criteri di accettazione, così il test legge lo stesso valore. Alcuni documenti li dichiarano «obiettivo di test, non variabile» (A1 §4.5, C1 §7, E2 §7): il conflitto con DX-22 è DA-CV-04. Le tre soglie di A3 sono in §4.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a1.read_batch_p99_ms` | 100 ms (≤ 1.000 mandati per tenant) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (A1 §7) | A1 (§7, CA9) |
| `a1.write_p99_ms` | 50 ms | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (A1 §7) | A1 (§7, CA9) |
| `b1.job.start_overhead_p95_ms` | 3000 ms | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (B1 §7, CA8) | B1 (§7, CA8, DA-B1-01) |
| `b2.overhead_p95_ms` | 50 ms (escluso il tool) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (B2 §7, CA8) | B2 (§7, CA8) |
| `c1.node_overhead_p95_ms` | 50 ms (per nodo, esclusi LLM e tool) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (C1 §7) | C1 (§7) |
| `e1.overhead_p95_ms` | 5 ms per segmento | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E1 §5, §7) | E1 (§5, §7, CA6) |
| `e2.resolve_render_p99_ms` | 5 ms (da cache) | superadmin | da definire (DA-CV-02) | ordinaria | proposta da validare (E2 §7) | E2 (§7) |

## 13. Incidenti e conformità (Piattaforma → Incidenti e conformità)

**Contesto (DX-10, decisa).** Oggi Gravya non è soggetto NIS2. La progettazione è «NIS2 compliant ready by design» (proposte (a)-(c) confermate il 2026-11-04). A5 predispone il flusso di notifica come funzione presente ma non attiva finché Gravya non diventa soggetto NIS2 o un contratto con un'agenzia obbligata non lo richiede. I termini e i criteri qui sotto sono catalogati come vincoli normativi di quella funzione. Qualificazione di Gravya come fornitore di cloud computing e dimensione non sono accertate (registro, N-NIS2): le righe `incident.cloud.*` e `incident.financial_*` si applicano solo se Gravya è fornitore cloud in ambito, e non producono notifiche finché `incident.nis2_flow_active` è falso. I criteri del Reg. (UE) 2024/2690 sono «esaustivi» (considerando 30): una soglia interna più alta di quella del regolamento non è ammessa. Per i vincoli normativi «più restrittivo» significa: per i termini di notifica, più breve; per le soglie di significatività, che qualifichino più incidenti (soglie più basse, finestra più lunga, conteggio minimo più basso). Il minimo di ogni vincolo non è fissato da alcuna norma né decisione: da definire in A5 (DA-CV-02).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `incident.nis2_flow_active` | falso | superadmin, con motivazione e audit | falso/vero | ordinaria (interruttore di una funzione normativa) | deciso (DX-10 (b)) | A5, A1, A3, B1, B2, C1, C3, E1, E2 (segnali) |
| `incident.nis2.recipient` | CSIRT Italia | superadmin, con motivazione e audit | canale e contatto di notifica: da definire (non nel registro) | vincolo normativo (N-NIS2-IT art. 25 ✔; destinatario del d.lgs. 138/2024) | deciso (DX-10 (b)); contatto da definire | A5 |
| `incident.nis2.early_warning_hours` | 24 h dalla conoscenza | superadmin, con motivazione e audit | massimo 24 (norma); minimo da definire | vincolo normativo (N-NIS2 art. 23(4)(a); N-NIS2-IT art. 25(5)) | deciso (DX-10, DX-22(a)) | A5 e tutti i produttori di segnali |
| `incident.nis2.notification_hours` | 72 h dalla conoscenza (non dal preallarme) | superadmin, con motivazione e audit | massimo 72 (norma); minimo da definire | vincolo normativo (N-NIS2 art. 23(4)(b); N-NIS2-IT art. 25(5)) | deciso (DX-10, DX-22(a)) | A5 |
| `incident.nis2.final_report_months` | 1 mese dalla trasmissione della notifica | superadmin, con motivazione e audit | massimo 1 (norma); minimo da definire | vincolo normativo (N-NIS2 art. 23(4)(d); N-NIS2-IT art. 25(5)) | deciso (DX-10 (b)) | A5 |
| `incident.nis2.progress_report_interval_months` | 1 mese (incidente ancora in corso) | superadmin, con motivazione e audit | massimo 1 (testo italiano, art. 25(5)(e); la direttiva dice «relazione sui progressi» senza cadenza); minimo da definire | vincolo normativo (N-NIS2-IT art. 25(5)(e)) | deciso (DX-10 (b)) | A5 |
| `incident.nis2.final_report_after_closure_months` | 1 mese dalla conclusione della gestione (incidente in corso alla scadenza della relazione finale) | superadmin, con motivazione e audit | massimo 1 (norma); minimo da definire | vincolo normativo (N-NIS2 art. 23(4)(e); N-NIS2-IT art. 25(5)(e)) | deciso (DX-10 (b)) | A5 |
| `incident.gdpr.controller_notification_hours` | 72 h dalla conoscenza, ove possibile | superadmin, con motivazione e audit | massimo 72 (norma); minimo da definire. Vale per Gravya come titolare dei propri dati, non per i dati delle agenzie | vincolo normativo (N-GDPR art. 33(1)) | termine di legge; uso da parte di Gravya da confermare (DX-11) | A5 |
| `incident.gdpr.processor_notice_hours` | da definire | superadmin, con motivazione e audit | massimo da definire: l'art. 33(2) dice «senza ingiustificato ritardo» e non fissa ore; il valore deve lasciare al titolare il tempo per le 72 h (DA-CV-08) | vincolo normativo (N-GDPR art. 33(2), qualitativo) | da definire (DA-CV-08) | A5, DPA con le agenzie |
| `incident.cloud.outage_total_minutes` | 30 min: indisponibilità completa di un servizio cloud oltre questa durata | superadmin, con motivazione e audit | massimo 30 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 7(a)) | deciso (DX-10 (c)) | A5 |
| `incident.cloud.outage_partial_hours` | 1 h: disponibilità limitata oltre questa durata | superadmin, con motivazione e audit | massimo 1 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 7(b)) | deciso (DX-10 (c)) | A5 |
| `incident.cloud.users_affected_percent` | 5 % degli utenti del servizio nell'Unione (si applica il più basso fra questo e `incident.cloud.users_affected_count`) | superadmin, con motivazione e audit | massimo 5 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 7(b) e (d)) | deciso (DX-10 (c)) | A5 |
| `incident.cloud.users_affected_count` | 1000000 utenti | superadmin, con motivazione e audit | massimo 1000000 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 7(b) e (d)) | deciso (DX-10 (c)) | A5 |
| `incident.financial_loss_eur` | 500000 EUR di perdita finanziaria diretta (si applica il più basso fra questo e il 5 % del fatturato) | superadmin, con motivazione e audit | massimo 500000 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 3(1)(a)) | deciso (DX-10 (c)) | A5 |
| `incident.financial_loss_turnover_percent` | 5 % del fatturato totale annuo dell'esercizio precedente | superadmin, con motivazione e audit | massimo 5 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 3(1)(a)) | deciso (DX-10 (c)) | A5 |
| `incident.recurring_min_count` | 2 incidenti con la stessa causa apparente | superadmin, con motivazione e audit | massimo 2 (norma); minimo da definire | vincolo normativo (N-NIS2-REG art. 4) | deciso (DX-10 (c)) | A5 |
| `incident.recurring_window_months` | 6 mesi | superadmin, con motivazione e audit | minimo 6 (norma); massimo da definire | vincolo normativo (N-NIS2-REG art. 4) | deciso (DX-10 (c)) | A5 |
| `incident.recurring_review_interval_months` | 3 mesi (valutazione trimestrale degli incidenti ricorrenti) | superadmin, con motivazione e audit | massimo 3 (norma); minimo da definire | vincolo normativo (N-NIS2-REG, allegato 3.4.2(b)) | deciso (DX-10, nota del 2026-11-04 in DECISIONS §4) | A5 |

Senza soglia (nessuna variabile): art. 7(c) del Reg. 2024/2690 (compromissione di integrità, riservatezza o autenticità dei dati per azione sospettata malevola, senza soglia di utenti); art. 3(1)(b) (esfiltrazione di segreti commerciali) ed (e) (accesso non autorizzato sospettato malevolo con rischio di grave perturbazione); termine di 24 h per i prestatori di servizi fiduciari (non pertinente a Gravya).

## 14. Destinazioni extra-UE (Agenzia → Impostazioni → Destinazioni dei dati)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `tenant.extra_eu_optin_enabled` | falso (extra-UE negato senza opt-in) | admin agenzia. Il superadmin non può attivarlo al posto dell'agenzia | falso/vero. Granularità (per tool o per destinazione) non specificata (DA-CV-06) | ordinaria | deciso (DECISIONS §6, 2026-11-03: registrato nella configurazione per tenant di A6, versionato e auditato) | A1, A3, B1 (egress-proxy), B2 (DA-B2-07) |

## 15. Credenziali (Piattaforma → Credenziali; Agenzia → Credenziali)

Nessun valore è nel catalogo (DX-22(b)). Le credenziali stanno nella pagina dedicata di A6, separata tra credenziali di piattaforma (superadmin) e di agenzia (admin agenzia). I valori sono in un archivio cifrato self-hosted nell'UE; da UI solo inserimento o sostituzione, mai rilettura in chiaro (mascherate, con data dell'ultima rotazione); ogni accesso e modifica è in audit.

| Voce | Pagina | Chi inserisce o sostituisce | Documenti |
|---|---|---|---|
| Chiave di firma del `run_token` | credenziali di piattaforma | superadmin | B1, B2 |
| Chiave HMAC di resume e firma del token monouso | credenziali di piattaforma | superadmin | C3, A3, B2 |
| Chiave HMAC dell'egress-proxy | credenziali di piattaforma | superadmin | B1 |
| Chiavi dei provider LLM per tenant | credenziali di agenzia | admin agenzia | B1 |
| Credenziali dei sistemi esterni dietro i tool | credenziali di agenzia (o di piattaforma, se il tool è di piattaforma) | admin agenzia (superadmin) | B2 |
| Segreti della CI | secret store della CI | non da UI di piattaforma | E3 |

## 16. Valori fissi trovati nei documenti

Elenco documento §sezione → variabile, per chi aggiorna i documenti. Sostituire il valore con il nome della variabile. I valori del sistema precedente citati come riferimento non sono default di v2.

| Documento §sezione | Valore fisso trovato | Variabile o trattamento | Correzione richiesta |
|---|---|---|---|
| A1 §4.2, §4.5, CA5, CA11 | profondità 3 | `a1.delegation.max_depth` | citare solo il nome; CA11 usa il nome e un valore di prova |
| A1 §4.5, CA7 | 4 KB | `a1.artifact.max_properties_bytes` | citare il nome |
| A1 §4.5 | `a1.sweeper.interval` | `a1.sweeper.interval_minutes` | rinominare |
| A1 §4.5, §7, CA13 | 90 giorni, 12 mesi | `retention.runtime_events_days`, `retention.audit_decisions_months`, `retention.cross_tenant_access_log_months` | il test CA13 confronta con il catalogo |
| A1 §7 | 30 giorni (fine contratto) | `retention.tenant_offboarding_days` | citare il nome |
| A1 §7 | p99 < 100 ms (≤ 1.000 mandati), p99 < 50 ms | `a1.read_batch_p99_ms`, `a1.write_p99_ms` | 1.000 mandati è condizione di test (DA-CV-04) |
| A1 §7 | 10.000 `Agent`, 100.000 `Artifact` per tenant | dimensione del dataset di test | DA-CV-04 |
| A1, B1, B2, C1, C3, E1, E2, E3, A3 §7 | 12 mesi del log di accesso | `retention.cross_tenant_access_log_months` | citare il nome |
| A3 §4 | `a3.bundle.max_age` | `a3.bundle.max_age_s` | rinominare; aggiungere il minimo valido |
| A3 §4 | `retention.audit_decisions`, `retention.runtime_events` | `retention.audit_decisions_months`, `retention.runtime_events_days` | rinominare |
| A3 §4 («ripiego sul valore più restrittivo») | regola implicita | DX-17: azioni bloccate, segnale ad A5 | allineare il testo a DX-17 |
| A3 §7, CA5 | p99 ≤ 5 ms; soglia complessiva «aperta» | `a3.latency.eval_p99_ms`, `a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms` | la soglia complessiva è decisa (DECISIONS §6) |
| A3 CA1, CA5 | ≥ 30 casi; 10.000 decisioni | campioni di test | DA-CV-04 |
| B1 §4 | `limits` senza valori; «10 min e $2 per run, 8 giri» | `b1.job.*_default`, `b1.job.*_max` | i valori citati sono riferimento, non default |
| B1 §7, CA8 | p95 sotto 3 s; 200 job | `b1.job.start_overhead_p95_ms` | 200 job è campione di test |
| B1 CA4 | wall_s + 5 s | `b1.job.kill_grace_s` | citare il nome |
| B1 §7 | concorrenza per host, quota per tenant | `b1.host.max_concurrent_jobs`, `b1.tenant.max_concurrent_jobs` | definire l'unità della quota (DA-CV-06) |
| B1 §7 | 90 giorni, 30 giorni, 12 mesi, «legal hold» | `retention.runtime_events_days`, `retention.run_state_days`, `retention.incident_evidence_months`, `retention.cross_tenant_access_log_months` | «legal hold» non ha base nell'art. 23 né nel Reg. 2024/2690 (registro §9, punto 4): usare «evidenze di incidente» |
| B1 App. A | 300 s, 512M, 2G e 1G, pids 512, uid 10001 | riferimenti del sistema precedente | non default; il profilo di hardening v2 è da definire (DA-B1-02) |
| B1 CA3 | 169.254.169.254, 169.254.0.0/16 | invariante di rete | DA-CV-05 |
| B2 §5, CA4 | «N = 10», limiti di default | `b2.rate_limit.default_calls_per_minute` | N=10 è il valore di prova della variabile |
| B2 §7, CA8 | p95 < 50 ms; 1.000 chiamate | `b2.overhead_p95_ms` | 1.000 è campione di test |
| B2 §7 | 12 mesi, 30 giorni, 90 giorni | `retention.audit_decisions_months`, `retention.sensitive_payload_days`, `retention.traces_days` | citare i nomi |
| B2 App. A | 16.000 caratteri, 8 chiamate per risposta, `RATE_LIMIT_RPM` | riferimenti del sistema precedente | non default |
| B2 §6 | coda di recupero «fino a riuscirci» | `b2.recovery_queue.retry_interval_s` | aggiungere l'intervallo |
| B2 §4, C3 §6 | token monouso senza durata | `b1.run_token.ttl_s`, `hitl.approval_token.ttl_s` | definire (DA-CV-03) |
| C1 §4.1, §6, CA10 | 500 step e 5 min | `c1.max_steps`, `c1.max_duration_ms` | citare i nomi |
| C1 §4.3, §7 | 30, 90 giorni, 12 mesi | `retention.run_state_days`, `retention.runtime_events_days`, `retention.traces_days` | citare i nomi |
| C1 §7 | p95 < 50 ms «non variabile» | `c1.node_overhead_p95_ms` | DA-CV-04 |
| C3 §3, §5 | `KLOUD_APPROVAL_DEFAULT = true` | `hitl.approval_required_default` | DA-CV-05 |
| C3 §4.3, §7, AC-11 | 30 giorni, 12 mesi, 90 giorni | `retention.sensitive_payload_days`, `retention.audit_decisions_months`, `retention.traces_days`, `retention.run_state_days` | citare i nomi |
| C3 §6, App. C | 24 h, «DA-C3-04 resta aperta» | `hitl.request_ttl_hours` con `_min` e `_max` | DA-C3-04 è decisa; 24 h di gravya-app è solo riferimento |
| C3 §6, §7, AC-12 | sweeper che «non chiude» e retention che «non cancella» con valore non leggibile | DX-17, DA-C3-08 (a) | riscrivere: ultimo valore valido versionato e segnale ad A5 |
| C3 §7, §10 | 2 s al p95; 100 % di fermate | `hitl.resume_latency_p95_ms`; `eval.gate.max_blocking_failures_count` | citare i nomi |
| C3 §5 | HMAC e firma del resume | credenziali (§15) | rimandare alla pagina credenziali |
| E1 §4.1, §7, CA8 | 90 giorni, 12 mesi; «oltre 90 giorni» | `retention.traces_days`, `retention.cross_tenant_access_log_months`, `retention.eval_reports_months` | il test legge il valore dal registro |
| E1 §4.1, §5 | partizioni «per mese» | `e1.partition_interval_months` | citare il nome |
| E1 §5 | `x-gravya-trace-id`, `x-gravya-parent-segment-id`, 32 cifre esadecimali | nomi e formato | DA-CV-05 |
| E1 §5 | «soglia di overhead p95 (default 5 ms)», buffer, soglia di perdita | `e1.overhead_p95_ms`, `e1.write_buffer_size`, `e1.segment_loss_alert_threshold` | citare i nomi |
| E1 §5, CA8, §9 | «ultimo valore valido; non cancella nulla su valore non valido» | DX-17 | il job di retention usa l'ultimo valore valido versionato |
| E2 §7, CA2, CA13 | `e2.cache.max_ttl_s` 60, `e2.rollback.propagation_max_s` 60, `e2.template.pii_check_mode` | stessi nomi | ripetere solo i nomi |
| E2 §7 | p99 < 5 ms «non variabile» | `e2.resolve_render_p99_ms` | DA-CV-04 |
| E2 §4.3 | lunghezza dell'hash «da fissare con E1» | formato | DA-CV-05 |
| E3 §5, AC4 | `eval.gate.pass_rate_min`, `eval.run.cost_cap`, `eval.run.timeout`, `eval.ingestion.timeout`; 90 % | `eval.gate.pass_rate_min_percent`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s` | rinominare; DA-E3-07 aperta |
| E3 AC1 | 10–30 casi (master 0.3.1) | dimensione del dataset iniziale | DA-CV-04 |
| E3 §6 | R1 vale circa 20 giorni dal seed | dato della fixture | non è una variabile; scompare con il re-seed (DA-E3-04) |
| E3 §7 | $2 e 10 minuti per run agente (kloudify) | riferimento | non default di `eval.run.cost_cap_usd` |
| E3 §7 | 12 mesi; scadenza dell'artefatto GitHub non superiore al default | `retention.eval_reports_months` | la scadenza GitHub è ≤ questo valore; limiti GitHub non verificati |
| E3 §4.2 | exit code 0, 1, 2 | formato | DA-CV-05 |
| A1, B1, B2 App. C | opt-in extra-UE «aperto» | `tenant.extra_eu_optin_enabled` | decisa (DECISIONS §6) |
| A1, A3, B1, B2, C1, C3, E1, E2, E3 §3 | DX-14 «da riportare» | A6 | DX-14 è decisa (2026-11-03) |

## 17. Non verificato / da decidere

### 17.1 Non verificato

1. **Nomi e pagine.** I nomi dipendono da DX-07 (aperta); le pagine da A6 (non documentato).
2. **Valori del sistema precedente** (300 s, 512M, 2G, pids 512, 16.000 caratteri, 8 chiamate, `MAX_CASCADE_DEPTH = 3`, 24 h, 10 minuti e $2 per run): ripresi dai documenti dell'ondata 1, non riletti nel codice. I valori di kloudify arrivano da una ricognizione (B1 App. A).
3. **Master plan.** I valori «master 0.3.1» (10–30 casi) sono citati da E3, non riletti nel master.
4. **Incidenti «di base».** I casi degli Allegati 3 e 4 della Det. ACN 379907/2025 non sono nel registro (non letti): non catalogati. Restano aperti anche i termini della coorte di Gravya (DECISIONS §4).
5. **Ambito NIS2.** La qualificazione di Gravya come fornitore cloud e il criterio dimensionale non sono accertati (registro, N-NIS2). L'interruttore `incident.nis2_flow_active` resta falso finché non lo sono.
6. **Durata dei log.** Nessuna norma letta fissa una durata per i log di un responsabile: il Reg. 2024/2690 (allegato 3.2.5) non indica una durata; le sei mensilità del Garante (N-GAR-ADS) sono un riferimento, non un vincolo per il responsabile, e la vigenza dopo il GDPR non è verificata. Il valore di 12 mesi di `retention.cross_tenant_access_log_months` resta una scelta di DECISIONS §5.
7. **Altri intervalli «pianificati» del Reg. 2024/2690** (riesame periodico dei registri 3.2.4 e 3.2.7, riesame dei diritti di accesso 11.2.3 e 11.3.3, blocco dopo tentativi falliti e terminazione delle sessioni inattive 11.6): il regolamento non dà valori. Non catalogati: sono materia di A5 e A6, ondata 2.
8. **Data Act.** Il valore di `retention.tenant_offboarding_days` va riverificato contro gli artt. 25 e 29 (registro ◐; DECISIONS §4).
9. **Fixture dell'ondata 1.** I valori di default versionati nel repository (A3 F5b, E3 §5) e la tabella minima di C1 non soddisfano DX-22 finché A6 non esiste: sono ripieghi dichiarati dai documenti.
10. **Documenti non aggiornati.** I nove documenti (v1.4) descrivono ancora come aperte o proposte decisioni ora prese: DX-14, DX-17-DX-22, DA-C3-04, DA-C3-08, DA-C3-09, DECISIONS §6 (soglie di latenza di A3, registrazione dell'opt-in extra-UE, DA-C3-06).
11. **Unità e semantica incerte:** `b1.tenant.max_concurrent_jobs` (unità della quota), `e1.write_buffer_size`, `e1.segment_loss_alert_threshold`, granularità del rate limit (B2 §5), «4 KB» (A1), esistenza distinta di `_default` e `_max` per i limiti B1.
12. **Altri parametri senza valore:** A1 DA-A1-06 (soglia dell'istanza dedicata «da validare»); soglie dei segnali verso A5 (picchi di `deny`, `tool.denied` ripetuti, mutazioni anomale): nessun documento le fissa (DA-CV-07).
13. **Etichetta usata in B1:** «limiti A6 di kloudify» indica un'etichetta di kloudify e non il sottoprodotto A6.

### 17.2 Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione | Da riportare |
|---|---|---|---|---|---|
| DA-CV-01 | Intervalli minimo-massimo delle durate di retention | (a) valori di default non modificabili da UI finché l'intervallo del contratto/DPA non è definito; (b) intervalli provvisori proposti e poi validati con un legale; (c) superadmin libero entro un intervallo tecnico | DX-15 e DX-16 (il superadmin modifica solo entro l'intervallo contrattuale; fuori intervallo è non valido); GDPR art. 5(1)(e); DA-C3-09. DECISIONS §5 e DX-15 oggi non sono allineate: §5 dice modificabili dal superadmin, DX-15 solo entro l'intervallo | (a), in coerenza con DA-C3-09 | Sì (dati e conformità) |
| DA-CV-02 | Intervalli ammessi delle variabili non di retention | (a) solo validità tecnica (tipo, positivo, minimo ≤ massimo) fino alla definizione; (b) intervalli proposti nei documenti, «proposta da validare» e misurati; (c) li fissa l'utente in blocco | DX-17 richiede una nozione di «non valido»; A3 richiede un minimo valido per il ripiego; niente costanti nel codice (DX-22) | (a) ora; (b) nella versione successiva dei documenti, con misura | No |
| DA-CV-03 | Intervalli di sweeper e code, durata dei token | (a) fissarli con misura, con il ritardo massimo tra scadenza e chiusura/cancellazione come criterio; (b) un limite unico per tutti gli sweeper; (c) lasciarli impliciti | GDPR art. 5(1)(e) (dati oltre la scadenza); sicurezza dei token (validità non oltre la vita del run o del TTL HITL) | (a) | No |
| DA-CV-04 | Soglie di test e di prestazione dichiarate «non variabili» (A1 §4.5, C1 §7, E2 §7) e dimensioni dei campioni dei test | (a) tutto nel catalogo; (b) nel catalogo le sole soglie con metrica a runtime (§12), mentre i campioni di test (100 esecuzioni, 10.000 decisioni, 30 casi, 1.000 chiamate, N=10, dimensioni dei dataset) restano parametri dei test, citando il catalogo; (c) nessuna | DX-22 alla lettera («niente hardcoded mai»), praticità dei test | (b) | Sì (perimetro di DX-22) |
| DA-CV-05 | Invarianti di sicurezza e formati non configurabili: MFA obbligatoria (DX-20), fail-closed, token monouso, vocabolario chiuso `MONEY_WRITE`/`ALWAYS_HITL`, SHA-256 e lunghezza dell'hash, whitelist degli attributi E1, nomi degli header di correlazione e formato `traceparent`, exit code di E3, regole di rete 169.254.0.0/16, `synthetic: true`, e chi modifica il default `hitl.approval_required_default` | (a) invarianti di progetto, elencati nei documenti e non variabili; (b) variabili modificabili solo verso valori più restrittivi; (c) tutte variabili | DX-22 contro integrità dei controlli di sicurezza | (a), con elenco esplicito nei documenti | Sì (perimetro di DX-22, sicurezza) |
| DA-CV-06 | Granularità del rate limit B2 e unità della quota per tenant B1; granularità dell'opt-in extra-UE | (a) tre limiti indipendenti (agente, tool, tenant), vince il più restrittivo; (b) una chiave composta; (c) solo per tenant. Quota B1: job concorrenti. Opt-in: per destinazione dichiarata | Isolamento dal «vicino rumoroso», semplicità di UI, DA-B2-07 | (a); quota in job concorrenti; opt-in per destinazione | No |
| DA-CV-07 | Soglie dei segnali verso A5 | (a) variabili con default da misura; (b) ogni evento rilevante inviato ad A5 senza soglia locale, la soglia vive in A5; (c) soglie locali fisse | Il registro (N-NIS2-REG, considerando 30) non ammette soglie interne più alte dei criteri del regolamento | (b) | No |
| DA-CV-08 | Termine di Gravya verso l'agenzia titolare per segnalare una violazione di dati personali | (a) un numero di ore fissato nel DPA, tale da lasciare al titolare il tempo per le 72 h; (b) «senza ingiustificato ritardo» senza numero; (c) allineato al preallarme NIS2 | N-GDPR art. 33(1)-(2) (nessuna ora per il responsabile); art. 28(3); serve un valore per renderlo testabile | (a), con il valore deciso dall'utente dopo verifica legale; nessun numero è proposto qui | Sì (conformità) |

## Storico modifiche

| Versione | Data | Cosa | Perché |
|---|---|---|---|
| 1.0 | 2026-11-04 | Creazione del catalogo: retention (DX-09, DX-15, DX-16), HITL, enforcement e latenze, grafo, runtime, gateway, workflow, tracing, prompt, eval, soglie di prestazione, incidenti e conformità con i vincoli normativi di DX-10 e DX-22(a), opt-in extra-UE, rimando alle credenziali, valori fissi per documento, non verificato e decisioni aperte DA-CV-01..08. | DX-22(c): documento trasversale unico per le variabili, prima dell'aggiornamento dei documenti dell'ondata 1. |
