# Revisione di conformità: docs/catalogo-variabili.md v1.1 (seconda revisione)

Revisore: compliance-auditor · Data: 2026-11-04 · Registro norme: v1.5 · Esito: **RIPORTA** (nessun rilievo bloccante: nessuna violazione letterale di una decisione registrata; restano scelte per l'utente e alcune leve che aggirano decisioni prese).

Sigle: *verificato* = riscontrato sul testo del catalogo, di DECISIONS o del registro. *dedotto* = ragionamento mio o norma non nel registro. I numeri di riga del catalogo sono quelli del file letto (424 righe).

## 1. Stato dei rilievi della prima revisione (R-01..R-22)

| R | Esito | Nota |
|---|---|---|
| R-01 limite di legge e valore operativo | risolto | regola 6 e §13.2; vedi R2-01 per una riga |
| R-02 interruttore NIS2 e segnali | in parte | segnali sempre conservati (§13), ma condizione di spegnimento e valore se non leggibile aperti (DA-CV-09); R2-07, R2-08 |
| R-03 valutazione iniziale | in parte | variabile istituita, senza valore né massimo (R2-11) |
| R-04 destinatario | risolto | §18; resta il canale libero (R2-16) |
| R-05 GDPR 33(1)-(2) | risolto nella forma, aperto nel valore | DA-CV-08; R2-05 |
| R-06 retention senza intervallo | risolto | sola lettura (RR); ma R2-10 (leve laterali) |
| R-07 override per agenzia | risolto | `retention.tenant.<classe>`; R2-13 sulla scelta a fine contratto |
| R-08 unità | in parte | giorni e conversione ok; `recurring_min_count` ancora tipato «massimo» (R2-19); fatturato (R2-06) |
| R-09 variabili di sicurezza | in parte | §19 aggiunta; senza intervallo protetto (R2-11) |
| R-10, R-11 invarianti | risolto | §18; mancano alcune (R2-17) |
| R-12 HITL | in parte | classi `ALWAYS_HITL` e `MONEY_WRITE`; default di piattaforma aperto (R2-14) |
| R-13 pii_check_mode | risolto | invariante `block` |
| R-14 gate E3 | risolto | zero fallimenti bloccanti |
| R-15 evidenze di incidente | in parte | tre variabili «da definire» (R2-09) |
| R-16 backup, pseudonimi | in parte | variabili «da definire»; R2-04, R2-07, R2-20 |
| R-17 opt-in per destinazione | in parte | R2-12 |
| R-18 3.4.2(b) | risolto nel registro v1.5, ma il catalogo non è aggiornato (R2-01, R2-02) |
| R-19 marketing | risolto | regola 10 |
| R-20 credenziali | in parte | DA-CV-16, C11; R2-18 |
| R-21 segnali in ondata 1 | risolto | regola 4: tabella di audit minima |
| R-22 massimi dei valori | **non risolto** | DECISIONS §4 lo tiene aperto, il catalogo non ha una DA (R2-11) |

## 2. Controllo specifico 1: §13 contro il registro v1.5

| Punto del registro v1.5 | Riga del catalogo | Esito |
|---|---|---|
| 3.4.2(b) dice «trimestralmente», senza «al massimo» (N-NIS2-REG, riga 435; §9 punto 9(a)) | `incident.recurring_review_interval_days`, l. 224: «massimo: solo in diminuzione», colonna «Limite di legge» | **non allineato**: presentato come limite di legge un massimo che è un'interpretazione. R2-01 |
| Il Reg. non fissa valori per backup, RTO/RPO, patch, scansioni, rotazione chiavi (riga 471, §9 punto 9(b)) | §2 `retention.data_backup_days`, `retention.log_backup_months`; §19 `security.credential_rotation_interval_days` | allineato per i valori: tutti «da definire», tipo ordinaria, nessuno è «vincolo normativo». Restano testi superati (R2-02) |
| Art. 12(3) GDPR è un termine del titolare (riga 101, 127) | l. 230: «il termine di risposta agli interessati non è nel registro (§17.1, punto 15)» | superato: ora è nel registro (✔) e non dà termini a Gravya. Nessuna variabile creata: corretto che non sia «vincolo normativo». Resta la questione R2-05 |
| Canale CSIRT: Portale dei Servizi ACN, maschera NIS, ◐ (riga 398-408) | `csirt_channel`, `csirt_contact`, l. 201-202: «canale non nel registro» | superato. R2-16 |
| Annex fissa solo 3.4.2(b) trimestrale e riesami almeno annuali 1.1.2 e 2.1.4 (riga 467-471) | catalogo: nessuna riga per 1.1.2 e 2.1.4; §19 intro: «Il regolamento non dà nessun valore» | **mancano due limiti fissati dalla norma**. R2-03 |
| 24 h, 72 h, un mese, art. 7 (30 min, 1 h, 5 %, 1 milione), art. 3(1)(a) (500.000 EUR o 5 %), art. 4 (due in sei mesi) | l. 211-223 | corretti rispetto al registro (verificato, righe 433-436 e 338, 376) |

## 3. Controllo specifico 2: tipo, verso e conversioni (regola C1 alla lettera in DX-22)

| Variabile | Norma | Tipo e verso nel catalogo | Mio esito |
|---|---|---|---|
| `early_warning_hours` 24 | «entro 24 ore» dalla conoscenza | massimo, in diminuzione | corretto |
| `notification_hours` 72 | «entro 72 ore» | massimo, in diminuzione | corretto |
| `final_report_days` 28 | «entro un mese dalla trasmissione della notifica» | massimo, 28 (mese più breve, febbraio) | corretto; il computo del mese (reg. 1182/71) non è nel registro (○): dedotto |
| `progress_report_interval_days` 28 | art. 25(5)(e) IT «mensile» | massimo, 28 | corretto; la direttiva non dà cadenza (dichiarato) |
| `final_report_after_closure_days` 28 | art. 23(4)(e) | massimo, 28 | corretto |
| `outage_total_minutes` 30, `outage_partial_hours` 1, `users_affected_percent` 5, `users_affected_count` 1.000.000 | art. 7 | massimo, in diminuzione | verso corretto: soglie più basse qualificano più incidenti. Vedi R2-19 sulla parola «esaustivi» |
| `financial_loss_eur` 500.000, `_turnover_percent` 5 | art. 3(1)(a) | massimo, in diminuzione | verso corretto per le due soglie; **il dato di fatturato** no (R2-06) |
| `recurring_min_count` 2 | art. 4 «almeno due volte» | massimo, in diminuzione | verso corretto, ma l'unico valore utile è 2: di fatto fisso (R2-19) |
| `recurring_window_days` 184 | art. 4 «sei mesi» | **minimo**, in aumento; 184 = luglio-dicembre | corretto (per eccesso, valore legale rispettato) |
| `recurring_review_interval_days` 89 | 3.4.2(b) «trimestralmente» | massimo, in diminuzione; 89 = febbraio-aprile | 89 rispetta il trimestre in ogni caso (prudente); il tipo «massimo» è interpretazione (R2-01) |
| `gdpr.controller_notification_hours` 72 | art. 33(1) | massimo | corretto |
| `gdpr.processor_notice_hours` | art. 33(2) senza ore | obbligo contrattuale (DPA) | corretto; valore aperto (DA-CV-08) |

Nessuna riga è di tipo «fisso»: coerente, perché nessun valore letto è fisso per legge senza verso. Le conversioni 28, 89, 184 rispettano C1; il catalogo le dichiara calcolo del redattore (§17.1 punto 16).

## 4. Rilievi

### R2-01 · da_riportare · N-NIS2-REG all. 3.4.2(b) (✔ v1.5): «massimo 89 giorni» presentato come limite di legge
- **Dove:** catalogo l. 224, colonna «Limite di legge» e «Tipo del limite»; l. 224 «nell'intestazione del registro la sezione 3.4 non è tra le ✔: §17.1, punto 15»; l. 20 regola 7; registro riga 435 e §9 punto 9(a).
- **Testo:** catalogo «3 mesi (valutazione trimestrale degli incidenti ricorrenti) | massimo: solo in diminuzione. Conversione: 89 giorni»; registro «il testo non dice né "almeno" né "al massimo"» e «la lettura "massimo 3" è un'interpretazione».
- **Problema:** il catalogo tratta come limite di legge un valore che la norma fissa come cadenza («trimestralmente»). Il massimo è una lettura prudente. Il rischio non è di non conformità (89 giorni è più stretto di ogni trimestre), ma di far passare un'interpretazione per «vincolo normativo» (DX-22(a)). Il testo sull'intestazione del registro è superato: 3.4.2(b) è ✔ in v1.5.
- **Proposta:** dichiarare il tipo come «valore fissato dalla norma (cadenza trimestrale); massimo di 89 giorni scelta prudente del progetto», stato «da confermare con un legale»; togliere la nota sull'intestazione. Decisione all'utente: tenerlo come massimo per C1 (raccomandato).
- **Verifica:** verificato.

### R2-02 · minore · C1 (collegamento al registro) e testi superati sul registro
- **Dove:** catalogo l. 3, regola 6 (l. 18); §17.1 punti 7, 15, 17; l. 50, 54, 201-202, 230, 414.
- **Testo:** «Letto il registro v1.4 (non la v1.5 in corso)»; «il limite di legge ... cambia solo con una nuova versione di questo catalogo collegata a una versione del registro»; «canale non nel registro»; «norma sui backup non letta»; «punto del regolamento non verificato».
- **Problema:** la regola 6 impone il collegamento a una versione del registro, ma l'intestazione del catalogo non ne indica nessuna. Il punto 15 dice v1.4. Con la v1.5 sono letti: GDPR 12(3), 28(2), 28(3)(e), 28(4); Reg. 2024/2690 3.4.2(b), 4, 5, 6, 9 (backup, chiavi); canale CSIRT (◐). Diverse righe dicono ancora «non letto».
- **Proposta:** aggiungere in testata «Registro norme: v1.5» e riscrivere i punti superati. In particolare: `retention.data_backup_days` («4.2.2(f): periodi di conservazione secondo obblighi commerciali e normativi, nessun numero»); `security.credential_rotation_interval_days` («9.2(c): la politica deve definire le tempistiche di modifica delle chiavi, nessuna periodicità fissa»); §17.1 punto 7 e 15.
- **Verifica:** verificato.

### R2-03 · da_riportare · N-NIS2-REG all. 1.1.2 e 2.1.4 (✔ v1.5), DX-10(a): due limiti fissati dalla norma non catalogati
- **Dove:** catalogo §19 (l. 403) e §13.
- **Testo:** catalogo «Il regolamento non dà nessun valore: tutti da definire»; registro riga 467 «riesame ... almeno annualmente» (politica di sicurezza, 1.1.2) e «almeno con cadenza annuale» (valutazione dei rischi, 2.1.4); riga 471 «i soli valori fissati ... oltre alle soglie».
- **Problema:** per §19 la frase è vera (le sezioni 3.2, 11 non hanno valori), ma nel Reg. due cadenze minime sono fissate. Se DX-10(a) rende requisiti di progetto le misure del Reg., queste due sono limiti di legge tipo «massimo dell'intervallo» (almeno annuale = al più 365 giorni), con la regola C1 (conversione per difetto: 365). Oggi saranno scelte altrove, fuori dal catalogo (DX-22).
- **Proposta:** portare all'utente se adottarle: `security.policy_review_interval_days` e `security.risk_assessment_review_interval_days` (limite 365, massimo, in diminuzione; nota «solo se in ambito»), con documento responsabile A5 o A6.
- **Verifica:** verificato (testo del registro); dedotto (che DX-10(a) le comprenda: la lista di DX-10(a) non le nomina).

### R2-04 · da_riportare · GDPR art. 32(1)(c) ✔, NIS2 art. 21(2)(c), (d), (e), (h): parametri di continuità, vulnerabilità, catena di fornitura e chiavi senza variabile
- **Dove:** catalogo §2 (backup), §15, §19; DECISIONS §4 (righe «Cancellazione con valori non validi e backup» e «Credenziali»).
- **Testo:** registro righe 459-466 (RTO/RPO, backup, patch, scansioni, riesame dei fornitori, chiavi: «No», nessun valore); catalogo `retention.data_backup_days` «da definire (F6)».
- **Problema:** il registro v1.5 dice che questi sono scelte di Gravya, da definire e documentare (art. 2(2)). Il catalogo, che è l'unico punto di verità (DX-22), non ha righe per: obiettivi di ripristino (RTO, RPO), frequenza dei test di ripristino, tempo di applicazione delle patch, frequenza delle scansioni, riesame dei fornitori (5.1.6-5.1.7), riesame della politica crittografica (9.3). Mancano anche: la regola di propagazione delle cancellazioni ai backup (DECISIONS §4, rilievo R-16 punto 3 ancora aperto) e la procedura di sostituzione delle chiavi HMAC senza interruzione.
- **Proposta:** aggiungere righe «da definire», tipo ordinaria, dichiarando che non sono vincoli normativi (registro §9 punto 9(b)), con il documento responsabile (F6, A5, A6); propagare le cancellazioni ai backup come regola di F6.
- **Verifica:** verificato (assenza e testi); dedotto (necessità: dipende da quanto DX-10(a) comprende e da chi è il fornitore).

### R2-05 · da_riportare · GDPR art. 12(3), 28(2), 28(3)(e), 28(4) (✔ v1.5): assistenza ai diritti e sub-responsabili senza variabile né decisione
- **Dove:** catalogo l. 230, §14; DECISIONS §4 («Variabili GDPR mancanti», «Sub-responsabili»).
- **Testo:** catalogo «Non esistono variabili per l'assistenza ai diritti degli interessati (art. 28(3)(e))»; registro riga 127 «un termine interno di Gravya ... è una scelta contrattuale o di prodotto, non un valore fissato dalla legge».
- **Problema:** (1) senza un termine con cui Gravya inoltra o evade le richieste degli interessati, l'impegno verso il titolare (un mese, art. 12(3), prorogabile di due) non è testabile; non è «vincolo normativo» ma un valore del DPA. (2) Il catalogo §14 regola l'opt-in extra-UE ma non l'autorizzazione dei sub-responsabili (28(2): autorizzazione scritta specifica o generale, informazione delle modifiche). Un destinatario UE (per esempio un provider LLM europeo) è anch'esso sub-responsabile e non passa dall'opt-in. (3) Nessuna delle due è nelle DA-CV-09..17.
- **Proposta:** DA nuova: `dsar.forward_max_hours` (o giorni) come obbligo contrattuale (DPA, non vincolo normativo, stesso schema di `processor_notice_hours`) e un campo «sub-responsabile autorizzato (riferimento al DPA, data)» nel record della destinazione dichiarata, valido anche in UE; il tool senza sub-responsabile autorizzato resta negato.
- **Verifica:** verificato (testi); dedotto (campo e variabile).

### R2-06 · da_riportare · N-NIS2-REG art. 3(1)(a) ✔: il dato di fatturato è l'unico elemento che alza la soglia, ed è un valore libero
- **Dove:** catalogo l. 221 e DA-CV-14 (l. 375, «Da riportare: No»).
- **Testo:** «5 % del fatturato totale annuo dell'esercizio precedente | massimo: solo in diminuzione | Fonte del dato di fatturato: DA-CV-14»; «(a) valore inserito dal superadmin e versionato».
- **Problema:** la soglia effettiva è il più basso tra 500.000 EUR e il 5 % del fatturato. La regola «solo in diminuzione» tiene la percentuale, non il fatturato: con un fatturato dichiarato più alto del reale la soglia sale (fino a 500.000) e meno incidenti risultano significativi: è la direzione non ammessa da C1. Per Gravya (due persone fisiche in forfettario, DX-10) il 5 % è quasi certamente la soglia in vigore. L'opzione (c) «non applicabile finché il flusso è spento» è in contrasto con C2 (i segnali si producono e si conservano comunque, e la classificazione serve per ricostruire la «conoscenza»). La DA è segnata «No»: toccando la conformità deve andare all'utente.
- **Proposta:** portare DA-CV-14 all'utente; il fatturato non è una variabile ordinaria: valore versionato con attore, documento di origine (bilancio, dichiarazione), modifica solo da superadmin con motivazione e confronto con il valore precedente; in dubbio si usa il valore più basso noto.
- **Verifica:** verificato (testo della norma e del catalogo); dedotto (la lettura sulla direzione).

### R2-07 · da_riportare · DX-17, C2, GDPR art. 5(1)(e): DA-CV-17 (raccomandazione (a)) incrocia la regola dei segnali e le classi «da definire»
- **Dove:** catalogo l. 16 (regola 4), l. 46 `retention.incident_signals_months` «da definire», l. 49-55 (sette classi «da definire»), DA-CV-17 l. 378.
- **Testo:** «primo valore versionato = default di questo catalogo per le righe "deciso"; per le righe "da definire" l'azione si blocca»; «I segnali di incidente si conservano sempre».
- **Problema:** (1) per `incident.*` senza limite di legge (canale CSIRT, valutazione iniziale) «l'azione si blocca» può bloccare la notifica o la produzione del segnale: l'opposto di C2 e della regola 4. (2) Le classi di retention «da definire» (`incident_signals`, `config_audit`, `auth_events`, `credential_access`, `consent_optout`, `log_backup`, `data_backup`, `pseudonym_map`) non hanno un valore valido al primo avvio: o blocca tutto (la piattaforma non parte), o la cancellazione non avviene e i dati restano senza termine (art. 5(1)(e)). In particolare i segnali di incidente devono essere conservati sempre (C2) ma senza una durata definita. (3) Il caso «nuova versione non leggibile con durata più lunga» (DECISIONS §4) non è documentato come limite.
- **Proposta:** portare DA-CV-17 anche come «Sì (conformità)»: escludere dal blocco la produzione e la conservazione dei segnali e dell'audit e la notifica; per le classi «da definire» fissare un tetto provvisorio per decisione dell'utente prima dell'ondata 1, altrimenti nessun dato di quella classe va scritto.
- **Verifica:** verificato (testi); dedotto (conseguenze).

### R2-08 · da_riportare · DX-10, N-NIS2-IT art. 25, N-NIS2-IT art. 7: interruttore NIS2, valore se non leggibile e attivazione
- **Dove:** catalogo l. 200 (`incident.nis2_flow_active`), DA-CV-09 (l. 370), regola 4 e 6.
- **Testo:** «Condizione di spegnimento e valore da usare se non leggibile: DA-CV-09»; «flusso attivo» come valore sicuro (dedotto, raccomandazione).
- **Problema:** (1) Finché DA-CV-09 è aperta, con la variabile non leggibile vale la regola 4 generale (azioni bloccate), non quella di `incident.*` (limite di legge), che per un booleano non esiste. Il comportamento atteso dalla regola 6 non è definito per l'interruttore. (2) Nulla nel catalogo controlla quando Gravya entra in ambito (dimensione, agenzia obbligata, qualificazione come fornitore cloud): l'interruttore parte da falso e dipende da una decisione umana non scadenzata; il registro (N-NIS2-IT) dice che la registrazione ACN e le comunicazioni sono annuali (1.1-28.2; 15.4-31.5) e che l'ambito non è accertato. (3) Con flusso spento le variabili `incident.*` possono non essere lette: la regola «limite di legge» non copre il caso di una soglia con base di calcolo mancante (R2-06).
- **Proposta:** portare DA-CV-09 con raccomandazione (a)+(b) e «non leggibile = flusso attivo, con segnale»; aggiungere una verifica periodica dell'ambito (variabile `incident.scope_review_interval_days`, da definire, con documento responsabile A5) e il trigger del contratto con un'agenzia obbligata.
- **Verifica:** verificato (testi del catalogo e del registro); dedotto (la verifica periodica).

### R2-09 · da_riportare · GDPR art. 5(1)(e), 17(3)(e), 5(2), 28(3)(g); N-NIS2 art. 23(4): evidenze di incidente: sospensione operativa senza massimo, riesame, categorie
- **Dove:** catalogo l. 42-45; DECISIONS §5 riga «Evidenze di incidente» e «Precisazioni C10».
- **Testo:** «durata del caso + 12 mesi, sospendendo le altre scadenze per quei dati ... sola lettura (RR)»; `incident_evidence_max_total_months`, `review_interval_days`, `categories` «da definire (F6)».
- **Problema:** la durata di default è già valida e di sola lettura, mentre i tre limiti decisi da C10 sono «da definire». Finché non lo sono, la sospensione può avvenire senza massimo, senza riesame e senza elenco chiuso: la conservazione senza termine che R-15 voleva escludere. Inoltre la motivazione cita l'art. 5(2) GDPR come base: il registro (riga 97) lo definisce accountability, non base di conservazione; l'art. 23(4) vale solo se Gravya è in ambito (flusso spento oggi) e l'art. 17(3)(e) solo nella misura necessaria a un diritto in sede giudiziaria (dedotto: lettura da confermare con un legale).
- **Proposta:** «sospensione non attivabile finché `max_total`, `review_interval` e `categories` sono da definire» (regola nel catalogo); riportare la base alla scelta dell'utente con parere legale (per i dati delle agenzie, istruzione del titolare nel DPA).
- **Verifica:** verificato (testi); dedotto (basi giuridiche).

### R2-10 · da_riportare · GDPR art. 5(1)(e), DX-15, DX-16, C6: leve che allungano la retention fuori dalla sola lettura
- **Dove:** catalogo l. 20 (regola 8c), l. 149 `e1.partition_interval_months`, l. 129 `b2.idempotency.window_hours`, l. 157 `e2.cache.max_ttl_s`.
- **Testo:** «`retention.traces_days` non è inferiore a `e1.partition_interval_months` ..., perché E1 cancella per partizione»; `e1.partition_interval_months`: «validità tecnica ... Effetto sulle partizioni esistenti non descritto».
- **Problema:** se E1 cancella per partizione (testo del catalogo), un dato resta fino a durata + intervallo di partizione: con 90 giorni e partizioni mensili fino a circa 121 giorni. Il superadmin può alzare `e1.partition_interval_months` senza massimo (solo validità tecnica): le tracce restano mesi oltre il valore di sola lettura e oltre l'intervallo che il DPA fisserà. Stessa logica, più debole, per la finestra degli esiti di idempotenza (può contenere dati dell'esito) e per la cache dei prompt. È un aggiramento di C6 e DX-16.
- **Proposta:** regola relazionale 8(d): `retention.traces_days + e1.partition_interval_months` (per eccesso) non supera `retention.traces_days_max`; stesso schema per le altre classi; massimo per `b2.idempotency.window_hours`. Dichiarare nella tabella che il valore di retention è «massimo effettivo» e non «durata minima».
- **Verifica:** dedotto (E1 non letto: mi baso sulla frase del catalogo).

### R2-11 · da_riportare · NIS2 art. 21(2)(i), (j) e Reg. 2024/2690 11.6, 3.2.6, art. 2(2); DX-19: variabili di sicurezza e accesso senza intervallo protetto
- **Dove:** catalogo §19 (l. 407-416), regola 8 (l. 20), §4 (`a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`), §13.1 `incident.initial_assessment_max_hours` (l. 203); DECISIONS §4 («Valori senza massimo valido»).
- **Testo:** «validità tecnica» per tutte; «Massimo operativo da fissare in A5».
- **Problema:** la validità tecnica ammette ogni intero positivo: tentativi prima del blocco = 1.000.000; sessione inattiva = 10^6 minuti; `access.aggregate_min_group_size_count` = 1 (un aggregato su un record identifica e svuota DX-19); `access.superadmin_trace_access_ttl_hours` senza massimo; `incident.initial_assessment_max_hours` senza massimo ritarda la «conoscenza» senza limite (considerando 31, ✔). Per `a3.*` e `e2.cache.max_ttl_s`: un valore enorme annulla il fail-closed (DA-A3-07, DA-B2-04). Il Reg. non dà valori ma, in caso di deroga, vuole la documentazione (art. 2(2)); il catalogo permette la deroga di fatto senza documentarla. La riga di DECISIONS §4 resta aperta e non ha una DA nel catalogo.
- **Proposta:** DA nuova (conformità): per queste variabili, intervallo protetto (minimo e massimo) fissato dall'utente prima dell'attivazione; fino ad allora, valore di default prudente e modifica con motivazione e segnale ad A5; minimo ≥ 2 per la dimensione di aggregazione.
- **Verifica:** verificato (regola 8 e righe); dedotto (rischio).

### R2-12 · da_riportare · GDPR artt. 28(2), 44-46, 49; N-DPF; DA-B2-07, C9: opt-in per destinazione, strumento e stato senza titolare del dato
- **Dove:** catalogo §14 (l. 243-245).
- **Testo:** `transfer_instrument` «Chi modifica: da definire (A6)»; `transfer_instrument_status` «da definire»; `enabled` «falso/vero».
- **Problema:** (1) nulla vieta che `enabled` sia vero con strumento «da definire» o stato non valido: la regola è solo il contrario (strumento che cade → disattivazione). (2) Non è detto chi aggiorna lo stato (la decisione 2023/1795 vale solo per le organizzazioni nell'elenco DPF, che il registro non ha potuto consultare): se è l'agenzia, può dichiarare «valido» e attivare; se nessuno, lo stato non cambia mai. (3) Dopo la disattivazione non è detto se il nuovo opt-in richiede una nuova decisione e se i trattamenti in corso si fermano. (4) La destinazione non porta il sub-responsabile (R2-05).
- **Proposta:** regola: `enabled` attivabile solo con strumento e stato validi, altrimenti deny (come per la destinazione non dichiarata); stato aggiornato dal superadmin con riferimento alla fonte e audit, mai dall'agenzia; la riattivazione richiede un nuovo opt-in dell'agenzia.
- **Verifica:** verificato (testo); dedotto (conseguenze).

### R2-13 · da_riportare · GDPR art. 28(3)(g) ✔; N-DATAACT artt. 25 e 29 (◐): scelta a fine contratto e default
- **Dove:** catalogo l. 48, 59; DA-CV-12 (l. 373).
- **Testo:** `retention.tenant_offboarding_choice`: «default da definire ... attiva con `retention.tenant_override_enabled`».
- **Problema:** l'art. 28(3)(g) lascia la scelta al titolare. Con l'override spento (stato iniziale, fino al DPA) l'agenzia non può scegliere, e il default della scelta non esiste: a 30 giorni dalla fine del contratto non è definito se si cancella o si restituisce. Il registro (◐) avverte che 30 giorni possono essere un minimo da superare se il Data Act (art. 25) prevede un periodo di recupero di almeno 30 giorni dopo la transizione: in quel caso `retention.tenant_offboarding_days` sarebbe un limite «minimo, solo in aumento».
- **Proposta:** DA-CV-12 con raccomandazione (b) (sempre disponibile); default da decidere con l'utente (restituzione, poi cancellazione, entro il termine); verifica del Data Act prima di fissare la riga come ordinaria.
- **Verifica:** verificato (testi); dedotto (conseguenza).

### R2-14 · da_riportare · AI Act art. 50(1), (2) ✔; DA-CV-15; C7(c)-(d): HITL, classi e interazione con persone
- **Dove:** catalogo l. 74, §18 (l. 392, 397), DA-CV-15 (l. 376).
- **Testo:** «Per i contenuti verso terzi l'approvazione la decide l'admin agenzia»; «Etichetta "generato da AI" sui contenuti verso terzi»; «chi lo modifica è aperto (DA-CV-15)».
- **Problema:** (1) Chi modifica il default di piattaforma di `hitl.approval_required_default` è aperto: nel frattempo la tabella non indica nessuno. (2) Non è detto chi classifica un tool come `ALWAYS_HITL` o `MONEY_WRITE` e se il superadmin può declassarlo: la classificazione nel catalogo tool (B2) è un modo per aggirare l'invariante. (3) L'etichetta copre il contenuto uscente; l'art. 50(1) (informare chi parla con un'IA alla prima interazione) riguarda la conversazione diretta (risposte automatiche) e non ha un'invariante. Il registro dice che l'art. 50 vale dal 2.8.2026 (già applicabile oggi). (4) La marcatura leggibile da macchina anche per il testo (art. 50(2)) resta «Da riportare» (DECISIONS §4): l'esposizione non è più futura.
- **Proposta:** portare DA-CV-15 con (a); aggiungere in §18: classificazione `ALWAYS_HITL` e `MONEY_WRITE` non declassabile da UI; invariante per l'informativa «stai parlando con un'IA» nelle interazioni dirette; decisione sul punto 50(2) prima dell'ondata 1.
- **Verifica:** verificato (testi e date del registro); dedotto (gli aggiramenti).

### R2-15 · minore · DA-CV-09..17: quali toccano la conformità
Vedi §5 di questo report (tabella). Segnalo che DA-CV-14 e DA-CV-17 sono segnate «No» ma toccano la conformità, e che DA-CV-13 resta «No» in modo corretto.
- **Verifica:** dedotto.

### R2-16 · minore · N-NIS2-IT art. 25 ✔, canale ◐; C4: `csirt_channel` libero
- **Dove:** catalogo l. 201-202.
- **Testo:** `csirt_channel` «validità tecnica»; «canale non nel registro».
- **Problema:** il destinatario è invariante, ma il canale è una stringa libera: si può configurare un canale che non porta al CSIRT Italia. Il registro v1.5 riporta il Portale dei Servizi ACN (maschera NIS) come canale ufficiale visto solo in estratti (◐; riga 398-408), con contatti di emergenza e designazione del referente non verificati.
- **Proposta:** elenco chiuso di canali ufficiali ACN; rimuovere «non nel registro» e citare la scheda ◐; riverificare sulla pagina ACN prima di usarla come requisito.
- **Verifica:** verificato (testi); dedotto (rischio).

### R2-17 · minore · C2, C5, DX-19, DX-22(b): invarianti non elencate in §18
- **Dove:** catalogo §18 (l. 384-399), §13 (l. 191, 194), §15.
- **Problema:** i segnali di incidente sempre prodotti e conservati (C2), le variabili GDPR sempre attive (C5), le credenziali mai rilette in chiaro (DX-22(b)), l'accesso del superadmin ai dati dei tenant solo aggregato e con log (DX-19, DX-18) sono solo in altre sezioni. Il principio del catalogo («configurabile non vuol dire disattivabile») vale solo per ciò che è in §18: un doc-writer può introdurre un `*_enabled`.
- **Proposta:** aggiungere le quattro righe a §18 con riferimento alla decisione.
- **Verifica:** verificato (assenza).

### R2-18 · minore · DX-22(b) con C11, DA-E3-09: segreti della CI
- **Dove:** catalogo l. 251, 261, 398.
- **Testo:** «Segreti della CI ... solo se non danno accesso a dati reali»; «chiave del provider del giudice LLM di E3, se il giudice gira in CI».
- **Problema:** la condizione «non danno accesso a dati reali» non è verificabile come scritta. Fuori dalla pagina credenziali non c'è audit di accesso, né registro dei segreti né rotazione (NIS2 art. 21(2)(h)). Manca il vincolo di DA-E3-09: il giudice LLM solo con elaborazione nell'UE. Il secret store della CI può essere un servizio gestito di un terzo (supply chain, art. 21(2)(d)).
- **Proposta:** progetto/account del provider dedicato ai test e distinto da quello di produzione, inventario dei segreti con data e rotazione, destinazione UE per il giudice (o §14); dedotto che sia accettato da C11.
- **Verifica:** dedotto.

### R2-19 · minore · N-NIS2-REG art. 4 e considerando 30; C1: `recurring_min_count` e soglie più basse
- **Dove:** catalogo l. 222; §13 intro (l. 188).
- **Testo:** «massimo: solo in diminuzione. Il valore 1 renderebbe ricorrente ogni incidente»; «I criteri ... sono "esaustivi"».
- **Problema:** (1) con minimo operativo 2 non c'è intervallo: è un valore fisso e la riga dovrebbe essere di tipo «fisso» (C1: i valori fissi non sono modificabili) o un'invariante. (2) Abbassare le soglie di significatività (verso ammesso da C1) fa classificare «significativi» incidenti che per il regolamento, con criteri esaustivi, non lo sono: per la parte non obbligatoria la notifica sarebbe volontaria (art. 26 d.lgs. 138/2024, ✔). Non è una violazione, ma il termine «vincolo normativo» per il verso «più restrittivo» è una scelta del progetto. (3) I minimi operativi «da definire (A5)» lasciano il valore a validità tecnica (1 ora per il preallarme è ammesso).
- **Proposta:** tipo «fisso» per `recurring_min_count`; dichiarare nel §13 che le soglie più basse sono scelta di progetto con effetto di notifica volontaria; fissare i minimi operativi prima dell'attivazione.
- **Verifica:** verificato (testi); dedotto (conseguenze).

### R2-20 · minore · GDPR artt. 4(5), 17, considerando 26: mappa di re-identificazione e cancellazione
- **Dove:** catalogo l. 55 `retention.pseudonym_map_months`, §2 «classi senza durata variabile».
- **Problema:** gli pseudonimi restano dati personali (considerando 26, ✔). Finché la durata della mappa è «da definire» non è detto che una richiesta di cancellazione, passata dal titolare, permetta di eliminare prima del termine la riga della mappa (rende l'attore non più identificabile in strutture append-only). Gli artefatti «per tutta la durata del servizio» contengono lo pseudonimo dell'attore.
- **Proposta:** regola in F6: la richiesta di cancellazione elimina la riga della mappa entro il tempo del DPA; la durata di `pseudonym_map_months` è un massimo.
- **Verifica:** dedotto.

## 5. Controllo specifico 4: DA-CV-09..17 da portare all'utente

| DA | Tocca la conformità? | Da riportare? | Nota |
|---|---|---|---|
| DA-CV-08 | sì (GDPR 33(2), 28(3)) | sì | valore del termine verso l'agenzia; senza valore il rispetto non è testabile, e il termine dell'art. 33(2) vale già oggi (DX-11) |
| DA-CV-09 | sì (DX-10, NIS2) | sì | R2-08; raccomandazione (a)+(b), non leggibile = flusso attivo |
| DA-CV-10 | sì (art. 5(1)(e)) | sì | (a) coerente con l'agenzia |
| DA-CV-11 | sì (indiretta: DA-E1-02, DA-E3-08) | sì | (a) invariante di deploy; è un'eccezione a DX-22 «niente hardcoded mai» che l'utente deve confermare |
| DA-CV-12 | sì (28(3)(g)) | sì | (b); R2-13 |
| DA-CV-13 | no | no | superficie dei token |
| DA-CV-14 | sì (soglia di incidente) | **sì, la segnalazione «No» va cambiata** | R2-06 |
| DA-CV-15 | sì (HITL, art. 50) | sì | R2-14 |
| DA-CV-16 | sì (DX-19, 28(3)(a)) | sì | (a) mai; è un accesso ai dati del tenant |
| DA-CV-17 | sì (DX-17, C2, art. 5(1)(e)) | **sì, la segnalazione «No» va cambiata** | R2-07 |
| Mancanti | | sì | DA per R2-05 (assistenza ai diritti e sub-responsabili), R2-11 (intervalli protetti), R2-03 (annuale) |

## 6. Controllo specifico 3: interruttore NIS2 (C2), destinatario (C4), GDPR (C5), retention (C6), invarianti (C7), opt-in (C9), evidenze (C10), segreti CI (C11)

| Decisione | Esito |
|---|---|
| C2 segnali sempre conservati e interruttore | recepita in §13 e §2; limiti in R2-07, R2-08 |
| C4 destinatario invariante | recepita (§18, l. 394); canale libero (R2-16) |
| C5 GDPR sempre attive; termine verso le agenzie come obbligo DPA | recepita (l. 194, 230-235); valore aperto (DA-CV-08) |
| C6 retention di sola lettura | recepita (RR, l. 28-58); leve laterali (R2-10) |
| C7 invarianti | recepita (§18); lacune R2-14, R2-17 |
| C9 opt-in per destinazione con strumento | recepita (§14); R2-12 |
| C10 evidenze di incidente | recepita nelle variabili, ma valori «da definire» (R2-09) |
| C11 segreti CI | recepita (§15, §18); R2-18 |

## 7. Da aggiungere al registro (per il regulatory-researcher)

1. **Reg. (CEE, Euratom) n. 1182/71** (computo dei termini): per il «mese» dell'art. 12(3) GDPR e dell'art. 23(4)(d) NIS2 e per le conversioni 28, 89, 184 giorni (registro riga 101: «non letta»). Verifica: dedotto.
2. **Reg. 2024/2690, allegato, sezioni 7, 8, 10, 12, 13 e parti di 1-3** (○): valutazione dell'efficacia (possibili intervalli), formazione, personale, gestione degli attivi, sicurezza fisica. Servono per R2-03, R2-04.
3. **Det. ACN 379907/2025, Allegati 3 e 4** (incidenti «di base») e Allegati 1-2 (misure): già segnalati nel registro; servono per `incident.*` se Gravya è in ambito ma non come fornitore cloud.
4. **Raccomandazione 2003/361/CE** (soglie dimensionali, ○): dedotto, serve per accertare l'ambito NIS2 (R2-08).
5. **Portale dei Servizi ACN, «Guida alla notifica degli incidenti informatici»** (◐): canale, referente CSIRT, campi (R2-16).
6. **Data Act art. 25(2)** (◐): periodo di recupero e transizione (R2-13).
7. **GDPR artt. 15, 16, 18-22** (○): per l'assistenza del responsabile (art. 28(3)(e)), `dsar` (R2-05); art. 19 ◐.
8. **Elenco DPF** e stato per provider; **art. 22(4) d.lgs. 101/2018** (vigenza dei provvedimenti del Garante): già nel registro §10.
9. **AI Act art. 50, Codice di buone pratiche sul testo sintetico e linee guida** (N-AIACT-COM): per R2-14.
10. **Art. 26 d.lgs. 138/2024** è ✔; applicazione dell'art. 3(9)(f) e (10): già nel registro §10.

## 8. Controllato, senza rilievi

- Valori e unità dei termini NIS2 e GDPR di §13 contro il registro v1.5; tipo e verso di ogni riga; conversioni 28, 89, 184 (aritmetica del calendario ricontrollata: gennaio-marzo 90, dicembre-febbraio 90 o 91, febbraio-aprile 89; luglio-dicembre 184).
- §13.3: ruolo titolare/responsabile, 72 h solo per i dati propri, 33(2) senza ore, nessun numero proposto.
- Retention: ogni durata di §2 coincide con DECISIONS §5; sola lettura e override coerenti con DX-09, DX-15, DX-16, DA-C3-09.
- Il catalogo non contiene variabili che consentano contenuti di prompt e risposte nelle tracce (DA-E1-02), dati reali nei test (DA-E3-08), servizi extra-UE senza decisione (DA-B2-07); `pii_check_mode` e gate E3 invarianti; MFA invariante (DX-20); fail-closed invariante (DX-17, DA-B2-04, DA-A3-07); token monouso; HITL: la chiusura per TTL porta solo alla non esecuzione.
- Credenziali: nessun valore nel catalogo, solo inserimento o sostituzione da UI, archivio cifrato self-hosted nell'UE, audit.
- Isolamento tra tenant e RLS: non è materia del catalogo (A6 non è documentato): non verificabile qui.
- Nessun OpenTelemetry né SaaS nel catalogo.

## 9. Letture

- docs/catalogo-variabili.md: 1-424 di 424
- docs/DECISIONS.md: 1-224 di 224
- docs/PRINCIPI.md: 1-15 di 15
- docs/revisioni/v1.5-ondata-1/compliance-auditor-catalogo.md: 1-234 di 234
- docs/norme-di-riferimento.md: 1-132, 320-510 (con righe lunghe) e 619-718 di 718; 511-545 (righe troncate a 1.800 caratteri). Non letti: 133-319 (N-DPF, N-EDPB, N-PRIV-IT, N-EPRIVACY, N-RPO, cookie, pixel, e-commerce), 546-618 (Omnibus IA, CRA).
