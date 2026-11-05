# Plan-auditor, catalogo delle variabili v1.2

Esito: **RIPORTA**. Nessuna violazione di un PV. Nessuna riga del catalogo contraddice una riga «Decisa» già presente in DECISIONS.md. Ci sono incoerenze con decisioni del 2026-11-04 non ancora registrate in DECISIONS e punti che richiedono una scelta dell'utente.

Perimetro: `docs/catalogo-variabili.md` v1.2, letto per intero (1-477 di 477). Letti anche PRINCIPI.md (1-15 di 15) e DECISIONS.md (1-253 di 253).
Altre letture:
- `brief-doc-writer-v1.5.md`: righe 12 e 25-47, più grep di DA-CV-18..23.
- `norme-di-riferimento.md` v1.6: righe 1-4 e 785-800, più grep.
- I nove documenti dell'ondata 1: solo grep dei nomi di variabile, non letti. §16 è quindi verificato solo a campione (A1 §4.5 `a1.sweeper.interval`, C3 `hitl.request_ttl_hours`, E2 CA13 `e2.template.pii_check_mode`, E3 `eval.*` senza suffisso). I campioni combaciano con le righe di §16.

## Rilievi

### R1 (da riportare, verificato): il catalogo non recepisce la decisione «Fine contratto» (Data Act art. 25(2))
- Dove: catalogo §2 righe `retention.tenant_offboarding_days` e `retention.tenant_offboarding_choice`; §17.1 punto 8; regola RR; intestazione («Registro delle norme: v1.5»).
- Testo del catalogo: «30 giorni dalla fine del contratto: restituzione o cancellazione, salvo obblighi di legge», con «sola lettura (RR)». Il vincolo Data Act è «non verificato (registro ◐)» e «se il Data Act imponesse… la riga diventerebbe un limite minimo».
- Testo del brief (righe 38 e 46): «non più "restituzione o cancellazione entro 30 giorni", ma periodo di recupero dei dati di almeno 30 giorni dalla fine del periodo di passaggio, poi cancellazione; `retention.tenant_offboarding_days` diventa un minimo».
- Registro v1.6 §9 punto 5: art. 25(2) letto sul testo.
- Problema: la riga resta un default fisso a 30 giorni, senza tipo di limite («minimo, solo in aumento») e con decorrenza sbagliata (fine contratto invece di fine del periodo di passaggio). Anche `retention.tenant_offboarding_choice` («restituzione oppure cancellazione») va riletta. Il registro è v1.6, non v1.5.
- Fonte: decisione utente del 2026-11-04 riportata nel brief e non ancora in DECISIONS; DA-CV-12.
- Azione: registrare la decisione in DECISIONS, poi allineare la riga.

### R2 (da riportare, verificato): DA-CV-18..23 sono elencate come «Aperte» ma risultano decise
- Dove: catalogo §17.2 «Aperte»; regola 10 («non è un'invariante finché non è deciso … DA-CV-18»); §18 riga «Approvazione umana… è aperto: DA-CV-18»; regole 12 e 13; riga `retention.incident_evidence_months` («da confermare con un legale (DA-CV-21)»); `retention.data_backup_days` (DA-CV-22); §15 (DA-CV-23); §14 (DA-CV-19).
- Il brief (righe 40-45) le dà come decise il 2026-11-04. Tutte coincidono con le raccomandazioni del catalogo, tranne DA-CV-20: il brief dice «tetto provvisorio fissato dall'utente prima dell'avvio in produzione», cioè (b) ma con il valore ancora aperto.
- Problema: il catalogo rimanda al lettore scelte già prese e il suo stato diverge da DECISIONS dopo l'aggiornamento del registrar. Due punti restano aperti perché il testo del brief non li chiude:
  - il valore del tetto di DA-CV-20;
  - il parere legale di DA-CV-21.
- Azione: dopo che il registrar ha scritto DA-CV-18..23, marcarle «decise» (o far riportare il catalogo a DECISIONS come fonte). È l'unico punto da sistemare nel catalogo.

### R3 (da riportare, verificato): nessun primo valore valido per le righe «proposta da validare»
- Dove: catalogo §1 regola 4 (D3, DA-CV-17 (a)).
- Testo: «(1) Per le righe con stato «deciso» il primo valore valido è il default di questo catalogo. (2) Per le righe «da definire» l'azione… si blocca.»
- Problema: restano senza regola circa 25 righe con stato «proposta da validare» e un default numerico. Esempi: `a1.delegation.max_depth`, `c1.max_steps`, `c1.max_duration_ms`, `hitl.resume_latency_p95_ms`, `a3.latency.*`, `b1.job.kill_grace_s`, `e1.partition_interval_months`, `e2.cache.max_ttl_s`, `e2.rollback.propagation_max_s`, `eval.*`. Al primo avvio nessuna delle due regole si applica: il comportamento è indefinito e l'implementatore sceglie. La riga di DA-CV-17 («i valori «deciso» valgono come primo valore valido») ha la stessa lacuna.
- Fonte: DA-CV-17, DX-17.
- Scelta richiesta all'utente: (a) il default proposto vale come primo valore; (b) vale come «da definire» e blocca.

### R4 (da riportare, verificato): fallback delle variabili `incident.*` incompleto
- Dove: regole 4 e 6; §13 «Valore non leggibile» (elenco delle quattro righe senza limite di legge).
- Testo: «Con una variabile `incident.*` non leggibile vale il limite di legge»; le sole eccezioni elencate sono `csirt_channel`, `csirt_contact`, `initial_assessment_max_hours`, `scope_review_interval_days`.
- Problema: altre due `incident.*` non hanno limite di legge né sono nell'elenco, quindi per loro la regola 6 non ha un valore da applicare.
  - `incident.annual_turnover_eur`: la riga dice solo «nel dubbio vale il più basso valore noto»; il dato non leggibile non è coperto.
  - `incident.gdpr.processor_notice_hours`: «nessun numero».
  - `dsar.assist_max_days` non è `incident.*`: vale il fail-closed generale (regola 4), cioè bloccare l'assistenza all'agenzia, effetto non voluto e non detto.
- Azione: estendere l'elenco o dire che vale l'ultimo valore valido versionato; per `annual_turnover_eur`, il più basso noto.

### R5 (da riportare, dedotto): nomi instabili della famiglia `_min` / `_max` della retention
- Dove: §2, «Famiglia protetta (DX-16)» e riga `retention.<classe>.tenant_value`.
- Testo: «Ogni variabile `retention.*_days` o `retention.*_months` ha due variabili gemelle `<nome>_min` e `<nome>_max`». La riga per agenzia dice «tra `<classe>_min` e `<classe>_max`», con `<classe>` definito «senza il prefisso `retention.`».
- Problemi:
  - Letta alla lettera, la famiglia si applica anche a `retention.incident_evidence_max_total_months` e `retention.incident_evidence_review_interval_days`, che non sono durate di classe. Si ottengono nomi come `…max_total_months_max`. Esiste già un massimo proprio, `incident_evidence_max_total_months`, diverso da un eventuale `retention.incident_evidence_months_max`: due massimi per la stessa classe, con nomi quasi uguali.
  - `<classe>_min` senza prefisso non è un nome di variabile: il nome pieno è `retention.<classe>_min`.
  - Il codice non può derivare con certezza l'elenco delle variabili gemelle.
- Azione: elencare esplicitamente le classi che hanno `_min` e `_max`, e scrivere il nome completo.

### R6 (da riportare, dedotto): le regole 8c e 8d non coprono `retention.traces_days.tenant_value`
- Dove: regola 8 (c, d), riga `retention.<classe>.tenant_value` (perimetro con `traces_days`) e E1 §4.1 (cancellazione per partizione).
- Testo: «`retention.traces_days` non è inferiore a `e1.partition_interval_months` … perché E1 cancella per partizione».
- Problema: il valore per agenzia è inferiore o uguale al valore di piattaforma, ma E1 cancella partizioni di tutti i tenant insieme. Una durata per agenzia più corta del ciclo di partizione non è realizzabile con la cancellazione per partizione. Non è detto se 8c e 8d valgano anche per il valore per agenzia, né chi cancella le righe del singolo tenant (E1 o F6).
- Azione: dire che 8c e 8d si applicano anche a `tenant_value` e assegnare la cancellazione per tenant.

## Minori

- **M1 (verificato).** Legenda «Stato del valore» non rispettata in alcune righe. Esempio: `hitl.approval_required_default`, «requisito ripreso da C3 §3; limiti dalle decisioni C7 e D3». Gli stati ammessi sono tre: deciso, proposta da validare, da definire.
- **M2 (verificato).** Schemi di nome diversi per la stessa idea di valore con limiti:
  - `hitl.request_ttl_hours` con `_min` e `_max`;
  - `b1.job.*_default` con `_max`;
  - `b2.idempotency.window_hours` con `_max`;
  - le durate di retention con `_min` e `_max`.
  La regola 8 scrive «`_default` ≤ `_max`» in modo generico. Non è un'incoerenza bloccante, ma peggiora la ricerca per nome.
- **M3 (verificato).** Testata e §17.1 (punti 3, 10, 15, 16): citano il registro v1.5 e dicono «non verificato / ○» per fonti ora ✔ nel registro v1.6:
  - Reg. 1182/71 (le conversioni 28, 89 e 184 giorni sono confermate nel registro v1.6 §9 punto 10a);
  - Raccomandazione 2003/361/CE;
  - GDPR artt. 15-22;
  - Data Act;
  - Reg. 2024/2690 sezioni 7, 8, 10, 12, 13, senza valori numerici.
  Il punto 10 dice «i nove documenti (v1.4)», ma sono in v1.5.
- **M4 (verificato).** Regole 8c e 8d usano «31 giorni per mese (per eccesso)», mentre la regola 7 usa i mesi consecutivi reali (184 per sei mesi, non 186). Il 31 è prudente per N=1 e un po' largo per N≥3. Va dichiarato che è una scelta prudente.

## Controllato senza rilievi
- Principi: nessun OpenTelemetry né servizi gestiti extra-UE; nessuna durata di retention propria fuori da DECISIONS §5 (le durate rimandano a DECISIONS §5 e alla regola RR).
- Valori fissi (DX-22): nessuna riga descrive un valore fisso senza la qualifica di invariante. Fanno eccezione `incident.recurring_min_count` (tipo «fisso», D6) e `API_ENV` (invariante di deploy, D2(b)): sono coerenti con DECISIONS.
- Coerenza con DECISIONS (D1-D8, DA-CV-01..17): confrontate riga per riga:
  - `incident.nis2_flow_active` (D1);
  - `hitl.approval_required_default` in sola lettura (D3);
  - override per classe (D3);
  - token unico B1/B2 (D3);
  - `tenant_offboarding_choice` (D2a);
  - regole 8b, 8d e 11 (D4, D5).
  Nessuna contraddizione, salvo R1 e R2.
- Conversioni mese→giorni: 28, 89 e 184 sono giuste (febbraio-aprile 89, luglio-dicembre 184). Coincidono con registro v1.6 §9 punto 10a.
- Nomi: nessun duplicato tra tabelle. I nomi nuovi sono dichiarati in §17.1 punto 11.
- Righe «Da riportare» di DECISIONS §4: non riproposte (Data Act come punto di partenza di R1 è nuovo solo perché il brief lo ha deciso; backup; chiavi HMAC; perimetro per agenzia; limite dei 89 giorni).
- §16 contro i documenti: solo a campione (vedi sopra).
