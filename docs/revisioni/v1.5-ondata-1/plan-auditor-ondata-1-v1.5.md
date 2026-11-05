# Plan-auditor — ondata 1, v1.5 (A1, A3, B1, B2, C1, C3, E1, E2, E3)

Esito: **RIPORTA**. Non ho trovato violazioni di un PV né contraddizioni con una riga decisa di DECISIONS che fermino un documento. Ho trovato diverse interfacce che non combaciano tra documenti scritti in parallelo e alcune scelte aperte descritte in modo diverso. Nessuna rende impossibile l'implementazione, ma R1-R7 vanno sciolte prima del codice.

Letti per intero: i nove documenti v1.5, DECISIONS (fino a DA-CV-23), catalogo v1.2, PRINCIPI. Il template e il master plan non sono stati riletti: il perimetro era la coerenza tra documenti e con le righe decise.

## Rilievi da riportare all'utente

### R1 — Chi valuta strumento di trasferimento e sub-responsabile (punto 3) — da_riportare, verificato
- **A3 §3 punto 5, §6 («Destinazioni e extra-UE»), CA13:** A3 valuta tutto (opt-in, strumento, sub-responsabile, anche UE); il bundle incorpora lo stato effettivo; la propagazione è DA-A3-08.
- **B2 §6 («Controllo della destinazione», punti 1-4) e CA9:** B2 descrive questi controlli come propri, prima della chiamata ad A3. Dopo la caduta dello strumento «dalla chiamata successiva il tool è `denied`», immediato. B2 punto 5 e DA-B2-08 lasciano aperto chi valuta.
- **Contraddizione tra i criteri:** A3 CA13 ammette un ritardo (ricaricamento del bundle); B2 CA9 richiede il deny alla chiamata successiva. Non possono essere veri entrambi se valuta solo A3.
- **DECISIONS §6 (decisa):** «A2 la compila in policy, A3 la valuta, B2 la applica». Per l'opt-in vale quindi A3. DA-B2-08 (b), «B2 legge i fatti e decide», contraddice la riga decisa per la parte opt-in.
- **B1 §6 (egress-proxy):** è un terzo valutatore, senza fonte dello stato né meccanismo per leggere il bundle. Lo stato non leggibile vale deny.
- DA-A3-08 (come arriva lo stato ad A3) e DA-B2-08 (chi decide) sono due facce della stessa scelta. Vanno unite in una sola decisione trasversale con B1.

### R2 — Hash degli argomenti: C3 DA-C3-12 ed E1 DA-E1-09 sono la stessa decisione (punto 4) — da_riportare, verificato
- Entrambe propongono (a) SHA-256 semplice contro (b) HMAC-SHA-256 con chiave per tenant. E1 aggiunge un'opzione (c). Entrambe raccomandano (b) e sono «DA RIPORTARE».
- La raccomandazione (b) modifica l'invariante deciso DA-CV-05 (SHA-256 e lunghezza dell'hash, catalogo §18). E1 lo dichiara; C3 chiama «invariante» solo (a).
- La chiave per tenant, citata in entrambe come «nella pagina credenziali (DA-CV-23)», non è nell'elenco credenziali del catalogo §15.
- Va registrata una sola decisione (E1, C3, B2, E2, A1 per `snapshot_hash`).

### R3 — Invio verso terzi: A3 DA-A3-09, B2 DA-B2-10, C1, C3, DA-CV-18 (punto 5) — da_riportare, verificato
- **DECISIONS DA-CV-18 (decisa):** i contenuti verso terzi non sono `ALWAYS_HITL`; decide l'admin agenzia, con audit.
- **A3 DA-A3-09 (a) e CA16:** negare nel bundle fixture ogni invio verso terzi nell'ondata 1. L'opzione (b) richiama DA-CV-18 come alternativa, ma DA-CV-18 non è un'alternativa al blocco per mancanza di consenso (sono piani diversi).
- **B2 DA-B2-10:** precondizione verificata dal connettore (base giuridica, mittente, opposizione).
- **C1 §4.4 punto 5, C3 §3:** assumono che l'invio avvenga con l'approvazione dell'admin; niente di tutto ciò fa riferimento al blocco di A3.
- **Problemi:**
  - DA-A3-09 e DA-B2-10 pongono la stessa domanda (blocco degli invii senza base registrata) con soluzioni diverse (A3 nega, il connettore verifica).
  - A3 trasforma un'opzione aperta in un criterio di accettazione (CA16).
  - B2, C1 e C3 non dicono cosa succede se A3 nega un invio.
- Da fare: una sola DA, collegata a D1-D4.

### R4 — Lettura delle variabili prima di A6 (punto 6) — da_riportare, verificato
- **Aperta come DA in A1 (DA-A1-10) e in B1 (DA-B1-09):** stessa scelta, due decisioni.
- **Dichiarata come fatto da A3 (F5b, §4), E1 (§3), E3 (§5):** snapshot o file nel repository, modificabile solo via PR.
- **C1 §9 fase 5:** «una tabella minima» (non un file).
- **B2, C3, E2:** non dicono nulla del ripiego.
- **Valori «da definire» nel catalogo (regola 4):**
  - B1 §9 dichiara che il submit fallisce.
  - A3 §4 usa «valori di prova» nel file fixture, mentre il suo §4 («Regole di lettura») dice che con valore «da definire» la decisione è `deny`.
  - B2 (limiti di rate limit, finestra di idempotenza, TTL dei token) non dice come parte nell'ondata 1.
  - C3 App. B accenna a `hitl.sweeper_interval_minutes` «da definire».
- L'ondata 1 non è eseguibile senza una regola comune per i valori di prova. Serve un'unica decisione: file o tabella, e se i valori di prova ammessi sono quelli del solo repository.

### R5 — Prompt e input al job senza DB, e gate E3 per E2 e C1 (punto 7) — da_riportare, verificato
- **E2 §3 («È richiesto da B1: risolve il prompt da E2»), §5 (libreria di risoluzione «usata da B1»), §7 («il testo renderizzato è consegnato a B1 e B2»):** B1 chiama E2 e riceve il testo.
- **B1 §2 («Non accede al database»), §3, §4 (`prompt_ref`, `input_ref`), DA-B1-10:** raccomanda (a) «C1 risolve il prompt da E2 e prepara l'input». Il job riceve solo `prompt_ref` e `input_ref` e non ha DB: da dove prende il testo?
- **C1:** non dice di risolvere il prompt né di preparare un `input_ref` (§3 cita solo E2). Il campo `input_ref` non è in C1.
- **Retention:** B1 §7 elenca `outputs_ref` ma non `input_ref`. Un `input_ref` su object storage con dati dei clienti non ha classe di retention.
- **Gate E3:**
  - E2 §6 punto 3 e C1 §6 punto 2 richiedono l'esito di E3 al momento della promozione o della pubblicazione (via API, a runtime).
  - E3 §2/§5 dice che gira in CI, su DB non di produzione, e non ha un'interfaccia richiamabile. DA-E2-04 (aperta) e DA-E3-01 non indicano come l'esito arrivi.
  - L'invariante «zero fallimenti bloccanti» non è verificabile da E2 senza un'interfaccia.

### R6 — Transazione unica A3 + B2, esiti e interfaccia di `DecisionRequest` (punto 2) — da_riportare (R6a, R6c) e minore (R6b), verificato
- **R6a — Esito per il record non salvato.** A3 §6: B2 «registra l'esito come `deny` con `record_not_persisted`». B2 §6 e CA3: «la risposta è `error`». L'enum di B2 §4 ha `denied` e `error`: ne serve uno solo.
- **R6b — `DecisionRequest`.** A3 §4 richiede anche `destination`, `action`, `tool_id`, `agent_version`, `trace_id`. B2 §4 («Verso A3») elenca solo `tenant_id`, `agent_id`, `run_id`, `tool_class`, `resource`, `approval_token`. Il campo `destination` (A3 §6, controllo 3) non è fornito da B2.
- **R6c — Esiti `deny`, `require_approval`, `rate_limited`.**
  - A3 §6: «B2 salva e poi esegue» (solo per `allow`); per gli altri esiti non dice se B2 persiste il record.
  - B2 §6 pone il rate limit tra la decisione di A3 e la transazione: una chiamata `rate_limited` o un `deny` non producono il record di decisione. A3 §7 chiede un record per ogni decisione.
  - A3 App. B lo dichiara «non verificato». DECISIONS §6 decide la transazione unica ma non il suo perimetro.
- **R6d — Timeout.** A3 §4 dice che `a3.record.persist_timeout_ms` è «letta da B2». B2 §5 («Variabili lette da B2») non la elenca, ma elenca `a3.eval.timeout_ms`.

### R7 — Classi `ALWAYS_HITL` / `MONEY_WRITE` / `REQUIRES_HITL`: nomi e chi assegna (punto 1) — da_riportare, verificato
- **Nomi.** DECISIONS DA-CV-05 e catalogo §18 usano `ALWAYS_HITL` e `MONEY_WRITE` (vocabolario chiuso). C3 §6, AC-1 e §3 usano `REQUIRES_HITL`; A3 §6 (controllo 2) usa «`MONEY_WRITE`/`REQUIRES_HITL`»; A3 §4 ha il campo `tool_class.requires_hitl`.
- **Mappatura circolare.** B2 §4 dice che la mappatura tra la propria classe di approvazione e `requires_hitl` «è di A3»; A3 §4 dice che `tool_class` è «assegnato dal catalogo dei tool (B2)». Il flag `requires_hitl` della v1.4 di B2 è sparito.
- **Chi assegna.** B2 DA-B2-11 e A1 App. B tengono la questione aperta. A3 §4 la dà per decisa («non da UI»). C1 §4.4 punto 5 la dichiara «da confermare».
- **Semantica.** Non è chiaro se `REQUIRES_HITL` (esito dipendente da `hitl.approval_required_default`) sia una classe distinta da `ALWAYS_HITL`. Va fissata: la scelta tocca la sicurezza.

## Rilievi minori (da correggere, nessuna scelta dell'utente)

### R8 — Token (punto 1) — minore, verificato
- Il `run_token` è descritto in modo coerente: B1 §4 lo emette dopo il via libera di A3 con scadenza `b1.run_token.ttl_s`; B2 §3-§4 lo verifica e ne ricava `agent_id`, `tenant_id`, `run_id`. A3 non lo cita. DA-CV-13 è applicata.
- **Monouso.** Il catalogo §18 elenca «Token monouso» con B1 tra i documenti. B2 usa il `run_token` a ogni chiamata del run (non monouso). B1 App. B lo segnala, ma il catalogo non è corretto: la voce vale per l'`approval_token`.
- **`approval_token`:**
  - Per C3 §5, §7 è legato all'hash degli argomenti approvati e verificato da «B2 e A3». B2 CA5 e A3 CA7 verificano solo monouso e scadenza; nessuno dei due descrive il controllo del legame con l'hash (C3 AC-1: «con hash diverso»).
  - Due verificatori (A3 al controllo 7, B2 in CA5), e A3 è stateless: chi traccia i token consumati è B2 (§7 classi), ma A3 §6 dice «token consumato» senza dire da chi.

### R9 — Attributi di E1 per `kind=decision` (punto 4) — minore, verificato
- **Corrispondenza:**
  - A3 (`kind`, `outcome`, `bundle_version`, `bundle_hash`, `config_version`) ed E1 §4.2 combaciano.
  - C3 §7 chiede richiesta, hash, revisore, esito e `config_version`: E1 ha `gravya.decision.id`, `args_hash`, `reviewer_ref`, `outcome`, `config_version`. C3 App. B («da allineare») è superata.
- **Residui:**
  - **Vocabolario hitl.** E1 elenca per `hitl` `requested, approved, denied, input_provided, expired, outcome`, ma lo stato di C3 usa `rejected` e l'esito `ok`/`refused`/`error`. L'attributo `outcome=outcome` non porta il risultato d'esecuzione.
  - **Identificativo.** `gravya.decision.id` è «record di decisione di A3» (kind `tool`) ma E1 §4.2 non dice cosa sia per C3 (id della richiesta HITL?).
  - **Nome non catalogato.** E1 usa `e1.attributes.max_value_bytes`, che non esiste nel catalogo (E1 §4.2 e §5). Violerebbe «un solo punto di verità» (DX-22(c)).

### R10 — Nomi di variabili e valori fissi (punto 8) — minore, verificato
- **Riferimento errato:** E3 §5 dice «valori nel catalogo §10»; le variabili `eval.*` sono nella §11 (la §10 è «Prompt»).
- **Nome inesistente:** `e1.attributes.max_value_bytes` (R9).
- **Variabili proposte nei documenti, non nel catalogo (dichiarate «da proporre»):**
  - B1 DA-B1-08: variabile per l'attesa massima del job in coda.
  - A3 DA-A3-08: ritardo massimo di propagazione.
  - C1 DA-C1-09: due variabili (opzione c).
  - A3: canale degli alert di latenza.
- Gli altri nomi controllati esistono nel catalogo, con i nomi giusti: `a1.*`, `a3.*`, `b1.job.*`, `b1.host/tenant.max_concurrent_jobs`, `b1.run_token.ttl_s`, `b2.rate_limit.*`, `b2.idempotency.*`, `b2.recovery_queue.retry_interval_s`, `c1.*`, `hitl.*`, `e1.*` (tranne il caso sopra), `e2.*`, `eval.*`, `retention.*` (comprese `incident_signals`, `config_audit`, `data_backup_days`, `tenant_offboarding_choice`), `access.*`, `security.credential_rotation_interval_days`, `incident.nis2.*`, `dsar.assist_max_days`. I nomi tolti dal catalogo (`e2.template.pii_check_mode`, `eval.gate.max_blocking_failures_count`, `b2.rate_limit.default_calls_per_minute`, `tool_grant_ref`) non compaiono più come variabili.
- **Valori fissi rimasti:** nessuno. Restano solo invarianti e campioni di test, citati come tali; i valori del sistema precedente sono dichiarati riferimenti. Cifre di legge (24 h, 72 h, un mese, almeno 30 giorni dopo il passaggio) appaiono in A3, B2, B1, E1 e C1 come termini normativi senza ripetere i default del catalogo.

### R11 — Stato di DECISIONS superato nei documenti e nel catalogo — minore, verificato
- **A3 App. B, C; B1 App. B; B2 App. B, C; C1 App. B; C3 App. B; A1 App. B:** dicono che DA-CV-18..23 e la fine contratto sono «non ancora in DECISIONS» o «in attesa di registrazione». DECISIONS §7 contiene ora DA-CV-01..23 e §5 la nuova riga di fine contratto. (E3 App. B dice invece di averle lette.)
- **Catalogo v1.2:**
  - §17.2 elenca ancora DA-CV-18..23 come «Aperte».
  - Il §2 descrive `retention.tenant_offboarding_days` come «30 giorni dalla fine del contratto: restituzione o cancellazione», mentre DECISIONS §5 dice «almeno 30 giorni dalla fine del periodo di passaggio, poi cancellazione; 30 giorni è un minimo».
  - Il §17.1 punto 17 non è più vero. I documenti (A1, B2, C1 App. B) lo segnalano e usano il testo di DECISIONS.

### R12 — Doppioni e rapporto con le decisioni già prese (punto 10) — minore, verificato
- **DA-E2-09:** tratta DX-19 come «non decisa per E2». DX-19 vale per i dati dei tenant in generale; resta da decidere solo se il template è dato del tenant.
- **DA-C3-10 (chi decide, MFA dei membri):** non contraddice DX-20, ma lo estende; coerente. DA-C3-07 e DA-C3-11 sono nuove e non duplicano nulla.
- **DA-E1-12:** raccomanda che l'audit di B2/A5 porti chiave, versione e hash del prompt, modello, `config_version`. B2 §4 (campi comuni) e §7 non li prevedono: se (a) è scelta, B2 va modificato. È un'altra decisione da portare con R6.
- **E3 DA-E3-07:** la regola dei bloccanti è già un invariante deciso (DA-CV-05); resta aperto solo il valore del catalogo (90 contro 0 della raccomandazione di E3). Coerente, ma il catalogo §11 propone 90, E3 raccomanda 0.
- **Tutte le DA «decise» nei documenti combaciano con DECISIONS:** DA-B1-04, DA-C3-04, DA-C3-08, DA-C3-09, DA-E1-08, DA-E2-07, DA-E2-08, DA-E3-08, DA-E3-09, DA-CV-xx citate.

### R13 — Altri punti — minore
- **Variabile non leggibile in E2 (§6):** il render si blocca ma la cache «continua a servire» fino all'ultimo TTL: è un'eccezione a DX-17 non decisa (E2 la dichiara «da confermare»).
- **C1 `nodes[].audience` e B2 `outbound_to_third_parties`:** due meccanismi per lo stesso concetto (destinatario esterno). C1 App. B lo dichiara non verificato con B2.
- **B1 `JobResult`:** non ha un campo per `ai_generated`. La frase «B1 fornisce modello e prompt effettivi e non altera il campo» (B1 §4) presuppone che il campo viaggi in `outputs_ref`: non detto.

## Controlli senza rilievi

- **Testata e storico:** tutti e nove i documenti hanno «Versione documento 1.5», data 2026-11-04, riga 1.5 nello storico (punto 9).
- **Dipendenze:** simmetriche tra i nove documenti (A1/E2, A3/B2/B1/C3/E1/E2/E3, B1/E3, C1/E3, C3/E2, E1/E3). Le dipendenze verso A2, A5, A6, B5, F6 sono dichiarate come ondata 2.
- **Template:** sezioni 1-12 e appendici A-C in ordine in tutti i documenti. Nessuna stima temporale (solo taglie S/M/L). Soglie non derivate da decisioni marcate nel catalogo.
- **PV-01, PV-02, PV-03:** nessuna violazione. Niente OpenTelemetry come SDK o export, niente SaaS extra-UE, retention solo per rimando al catalogo (DX-09). Nessuna durata propria.
- **DX-17, DA-C3-08, DA-CV-17:** applicate in A1, A3, B1, B2, C1, C3, E1, E3. E2 ha l'eccezione di R13.
- **Fine contratto, DA-CV-21, DA-CV-22:** trattate in modo coerente (minimo di 30 giorni, sospensione solo per i dati di Gravya, backup, due chiavi in parallelo).
