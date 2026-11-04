# Plan-auditor — docs/catalogo-variabili.md v1.0

Esito: **RIPORTA**. Nessuna violazione di un PV. Nessuna interfaccia rotta tra i documenti dell'ondata. Restano scelte che spettano all'utente e imprecisioni da correggere prima che nove doc-writer citino il catalogo.

Perimetro: catalogo v1.0 (non committato) contro PRINCIPI, DECISIONS e i nove documenti dell'ondata 1 (v1.4). Il catalogo non è un documento di dettaglio, quindi il template (sezioni, CA) non gli si applica. Ho controllato però che non contenga stime temporali e che le soglie non derivate da decisioni siano marcate "proposta da validare".

## Cosa ho verificato (ok)

- **Tabelle integre.** Le righe che iniziano con `|` sono 183. Quelle a 7 colonne sono 109, a 4 colonne 64, a 6 colonne 10 (DA-CV). La somma è 183 e il conteggio per sezione (§2-§14) coincide.
- **Retention.** I default di §2 coincidono con DECISIONS §5: 90 g, 90 g, 12 m, 12 m, 30 g, 30 g, durata del caso + 12 m, 12 m, 30 g offboarding. L'override per agenzia (DA-C3-09, DX-09, DX-15) è coerente. DX-16 (famiglia `_min`/`_max`) e DX-17 sono riportati correttamente.
- **HITL.** TTL 24 h con intervallo 1-168 h (DA-C3-04). DA-C3-08 (a) è riportata correttamente. Le chiusure per TTL usano l'ultimo valore valido.
- **A3.** Budget 5/20/25 ms come da DECISIONS §6, con valori "proposta da validare con misura".
- **DX-10 e DX-22(a).** I valori di §13 corrispondono al registro norme (N-NIS2 art. 23(4)(a)(b)(d)(e); N-NIS2-IT art. 25(5); Reg. 2024/2690 art. 3(1)(a), art. 4, art. 7(a)(b)(d), allegato 3.4.2(b)). La direzione "più restrittivo" è coerente. Il destinatario CSIRT Italia è corretto. Sul perimetro NIS2 il catalogo rispetta DX-10: l'interruttore è falso di default e non c'è alcuna presunzione di assoggettamento.
- **PV-02 e PV-01.** Nessun OTel, nessun servizio extra-UE, nessuna durata di retention propria nei documenti.
- **Opt-in extra-UE.** `tenant.extra_eu_optin_enabled`: solo admin agenzia (DECISIONS §6).
- **Completezza.** Ho letto per intero tutti e nove i documenti. I valori numerici sono tutti nel catalogo (tabella o §16), salvo i rilievi R5, R6, R7 e R9. Citazioni §16 controllate a campione: A1 §4.5/§7/CA5/CA7/CA11/CA13, A3 §4/§7/CA1/CA5, B1 §4/§7/CA4/CA8/App. A, B2 §5/§6/§7/App. A, C1 §4.1/§4.3/§7, C3 §3/§5/§6/§7/§10, E1 §4.1/§5/§7/CA8, E2 §4.3/§7, E3 §4.2/§5/§6/§7/AC1/AC4. Tutte corrette, salvo R6.

## Rilievi

### R1 — da_riportare — DA-CV-01, DA-CV-03 e DA-CV-05 offrono come opzione scelte già escluse (verificato)

- **DA-CV-01 (c):** «superadmin libero entro un intervallo tecnico». DX-15 e DX-16 decidono che il superadmin modifica solo entro l'intervallo del contratto/DPA e che fuori intervallo il valore non è valido.
- **DA-CV-01 (a):** «valori di default non modificabili da UI» contraddice DECISIONS §5 e DX-09 («modificabili dal superadmin (DX-13)»). Il catalogo lo dichiara (è la tensione tra §5 e DX-15), ma tratta la questione come ancora aperta.
- **DA-CV-05 (c):** «tutte variabili». Comprende MFA obbligatoria (DX-20, decisa) e il fail-closed (DX-17, DX-13, decise). Rendere variabile la MFA contraddice DX-20.
- **DA-CV-03 (c):** «lasciarli impliciti». Contraddice DX-22 («niente hardcoded mai»).
- Da fare: togliere dalle DA le opzioni escluse da una decisione. Per DA-CV-01 riportare all'utente solo la tensione §5/DX-15, cioè se i default siano modificabili finché l'intervallo non esiste.
- Fonte violata: DX-15, DX-16, DX-20, DX-22.

### R2 — da_riportare — Intervalli ammessi quasi tutti "da definire" (verificato)

- DX-22 e le regole del perimetro chiedono, per ogni variabile, default, chi modifica e intervallo ammesso. Nel catalogo restano "da definire" gli intervalli di tutte le durate di retention (DA-CV-01), di quasi tutte le altre variabili (DA-CV-02) e anche molti default (`a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `b1.job.*`, `b2.rate_limit.*`, `e1.write_buffer_size`, `eval.run.*`). Il catalogo lo dichiara.
- Effetto pratico: DX-17 e DX-16 richiedono la nozione di «valore non valido». Per le durate di retention non esiste alcuna regola di validità finché l'intervallo manca. DA-CV-02 (a) copre la validità tecnica solo per le variabili non di retention. Il test E1 CA8 («valore non valido → il job non cancella») e C3 AC-12 non sono quindi eseguibili sulle durate.
- Da fare: dichiarare in §1/RR una validità minima per le durate (tipo, intero positivo, `_min` ≤ valore ≤ `_max` se definiti), oppure riportare la scelta all'utente.
- Fonte: DX-16, DX-17, DX-22.

### R3 — da_riportare — "Segreti della CI" esclusi dalla pagina credenziali (verificato)

- Testo (§15): «Segreti della CI | secret store della CI | non da UI di piattaforma».
- DX-22(b) dice che le credenziali stanno in una pagina dedicata, con valori in un archivio cifrato self-hosted nell'UE. Nessuna sotto-scelta prevede l'eccezione per la CI.
- E3 §7 rimanda al "secret store" della CI. Se la CI è GitHub (DA-E3-11 lascia la scelta aperta), quel secret store non è self-hosted UE.
- Nella lista manca anche la chiave del provider del giudice LLM (E3, DA-E3-09).
- Da fare: riportare all'utente l'eccezione (decisione da prendere), oppure inserire quelle credenziali nella pagina dedicata.
- Fonte: DX-22(b), PV-01.

### R4 — minore — "deciso" è sovrastimato per alcune righe di §13 (verificato)

- `incident.nis2.progress_report_interval_months`, `incident.nis2.final_report_after_closure_months` e `incident.recurring_review_interval_months` hanno Stato "deciso (DX-10 (b))" o "(DX-10, nota…)".
- Il testo di DX-10 (b) elenca solo preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario e decorrenza. La relazione mensile sui progressi e la valutazione trimestrale compaiono solo nella riga di DECISIONS §4 («Da riportare», registrata ma non una riga "Decisa").
- Anche `incident.cloud.*`, `incident.financial_*` e `incident.recurring_*` sono "deciso (DX-10 (c))", ma (c) decide solo di agganciarsi al Reg. 2024/2690. I valori vengono dal regolamento, non dalla decisione.
- Da fare: scrivere "vincolo normativo derivato da DX-10 (c) e dal registro norme" invece di "deciso" per i valori non elencati in DX-10.
- Fonte: DX-10, DX-22(a).

### R5 — minore — `incident.gdpr.*` fuori dall'ambito decisionale (verificato)

- `incident.gdpr.controller_notification_hours` e `incident.gdpr.processor_notice_hours` non sono emessi da nessuno dei nove documenti. Neppure DX-10 li copre: DX-10 riguarda la NIS2.
- Per DX-11 Gravya è responsabile del trattamento. Il 72 h dell'art. 33(1) non è dunque un obbligo di Gravya (il catalogo lo dice, ma lo cataloga comunque come variabile).
- La DA-CV-08 è davvero aperta e non contraddice nulla.
- Da fare: marcare le due righe come "ipotesi da confermare (DX-11, DA-CV-08)", non come variabili in uso.
- Fonte: DX-11.

### R6 — minore — Citazione errata e omissione "legal hold" in §16 (verificato)

- Riga «E1 §5, CA8, §9 | ultimo valore valido…». In E1 §9 non c'è nulla su questo punto. Il testo sta in §5 («il job di retention non cancella nulla su un valore non valido»), in CA8 e in Appendice B (ultimo punto). Va corretto in "§5, CA8, App. B".
- «Legal hold» compare in B1 §7 (riga presente in §16), ma anche in C3 §7 («legal hold di §5»), E1 §4.1 («legal hold, meccanismo di F6 e A5») ed E2 §7 («legal hold»). §16 non li elenca. DECISIONS §4 dice che «legal hold» non ha base normativa. I doc-writer di C3, E1 ed E2 non riceveranno l'istruzione di sostituirlo con «evidenze di incidente».

### R7 — minore — Variabili e parametri non catalogati (verificato; il punto sull'idempotenza è dedotto)

- `API_ENV=production` è una guardia di ambiente (B1 §6/CA6, E3 AC7). Non è in §16 né nelle tabelle, e nessun trattamento è dichiarato.
- Finestre implicite di B2:
  - La retention degli esiti per `idempotency_key` non ha durata. Senza una finestra, «Retry con la stessa idempotency_key: restituisce il primo esito» (B2 §6) non è definibile. Il catalogo la mette solo tra le "classi senza durata variabile" di §2.
  - Anche la finestra del rate limit è implicita: `default_calls_per_minute` assume un minuto senza dichiararlo.
- DX-22 chiede variabili anche per questi parametri; DX-21 rimanda le classi a F6. Va dichiarato che nessuna variabile esiste ancora e perché.

### R8 — minore — Legenda interna incoerente (verificato)

- La legenda definisce `da definire` come «nessun documento né decisione lo fissa» e `proposta da validare` come «il valore non deriva da una decisione». Molte righe hanno Default "da definire" e Stato "proposta da validare (…senza valore)": `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`, tutte le `b1.job.*` con default da definire, `b1.host/tenant.max_concurrent_jobs`, `b2.rate_limit.*`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s`.
- Una proposta senza valore è un controsenso. Lo Stato corretto è "da definire".

### R9 — minore — Retention e partizioni mensili (dedotto)

- `e1.partition_interval_months` = 1 (E1 §4.1: retention applicata con `DROP PARTITION`). `retention.traces_days` può essere abbassato, per esempio a 45 giorni, ma le partizioni mensili non permettono una cancellazione puntuale.
- Il catalogo annota solo «effetto sulle partizioni esistenti non descritto». Serve il vincolo tra le due variabili: la durata di retention non può essere inferiore all'intervallo di partizione, oppure il job usa una cancellazione per riga.

### R10 — minore — Variabile di attivazione per classe con condizione non decisa (verificato)

- `retention.class_override_enabled`: «vero richiede l'intervallo di classe definito». DX-09 dice solo «Override per classe previsto nel modello ma non attivo». La condizione di attivazione è decisa solo per il tenant (DA-C3-09).
- Manca inoltre, per DX-15, dove l'agenzia sceglie la propria durata quando l'override è attivo. Non esiste una variabile né una pagina "Agenzia → Retention". È una lacuna dedotta: A6/F6 la copriranno, ma il catalogo dovrebbe dirlo.

### R11 — minore — Possibile interfaccia da chiarire: `run_token` e `tool_grant_ref` (dedotto)

- B2 §4: `run_token` «emesso da B1». B1 §4 JobSpec: `tool_grant_ref` «Token di B2 limitato al job». Sono due nomi per lo stesso oggetto, oppure due token distinti, con emittenti contrapposti.
- Il catalogo assume l'esistenza di `b1.run_token.ttl_s` (e della chiave di firma in §15, B1/B2) senza dire se `tool_grant_ref` sia lo stesso token. È un'ambiguità preesistente nei documenti, che il catalogo eredita. Se i token sono due, manca la variabile della durata del secondo.
- Verificare con i doc-writer di B1 e B2 prima che citino il nome.

### R12 — minore — Altri punti (verificato)

- La convenzione dei nomi (suffissi `_ms/_s/…`) è assunta prima che DX-07 sia decisa. Il catalogo lo dichiara. Se DX-07 cambia, sono toccati in blocco tutti i documenti che citano i nomi.
- `eval.gate.max_blocking_failures_count` è citato come soglia di C3 §10 («100% di fermate»). Non sono la stessa metrica: C3 chiede che il 100% dei casi "fermata" si fermi, E3 AC4 che i casi bloccanti falliti siano 0. La corrispondenza è plausibile ma non è detta nei documenti.
- `eval.gate.pass_rate_min_percent` ha default 90, mentre DA-E3-07 (aperta) raccomanda l'alternativa (b). Il catalogo lo segnala. Il default non è una scelta presa.
- La DA-CV-06 sulla granularità del rate limit è in parte già risolta dal testo di B2 §2 e §5 («per agente, tool e tenant»). Resta aperta solo la regola di combinazione.
- Le variabili `hitl.approval_token.ttl_s` e `b1.run_token.ttl_s` sono in "Tool gateway" (§7) anziché nella pagina HITL / Runtime. È una scelta di pagina provvisoria; gli appigli nei documenti esistono (nessun nome inventato senza ancoraggio).

## Variabili senza appiglio

Ho verificato le variabili sospette, controllando una per una l'ancoraggio nei documenti o nelle decisioni. Quelle con appiglio solo nel registro norme sono le `incident.gdpr.*` (R5).

- Con ancoraggio nel testo: `b2.recovery_queue.retry_interval_s` (B2 §6, «fino a riuscirci»), `b1.run_token.ttl_s` (B2 §4), `hitl.approval_token.ttl_s` (C3 §6, B2 §6), `hitl.sweeper_interval_minutes` (C3 §6), `b1.job.kill_grace_s` (B1 CA4), `eval.run.repetitions_count` (E3 DA-E3-05), `eval.gate.max_blocking_failures_count` (E3 AC4), `e1.partition_interval_months` (E1 §4.1).
- Con ancoraggio nelle decisioni: `incident.nis2_flow_active` (DX-10 (b)), `retention.class_override_enabled` e `retention.tenant_override_enabled` (DX-09, DA-C3-09; vedi R10).
- Lo split `_default`/`_max` per B1 è un'assunzione dichiarata.

## Decisioni aperte DA-CV-01..08

- Autenticamente aperte, senza contraddire una riga decisa nel loro nucleo: DA-CV-01 (con la correzione di R1), 02, 04, 05 (con la correzione di R1), 06, 07, 08.
- DA-CV-03 è aperta ma l'opzione (c) va tolta.

## Non letto

- Master plan e template (`Piano generale.md`, `Prompt e workflow.md`): non letti. Il catalogo non è un documento con template e le fonti sono state le righe decise e i nove documenti.
- `norme-di-riferimento.md`: letto solo nei passi sui criteri di significatività e sui termini NIS2 (righe 318-322, 357-359, 396-416 e ricerche per parola chiave).
