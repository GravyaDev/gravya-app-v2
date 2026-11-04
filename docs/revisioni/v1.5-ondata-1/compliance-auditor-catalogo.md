# Revisione di conformità: docs/catalogo-variabili.md v1.0

Revisore: compliance-auditor · Data: 2026-11-04 · Registro norme: v1.4 · Esito: **RIPORTA** (nessun rilievo bloccante: nessuna violazione letterale di una decisione; molti punti in cui il catalogo rende configurabile o lascia indefinito ciò che le decisioni chiedono protetto).

Sigle: *verificato* = riscontrato sul testo del catalogo, di DECISIONS o del registro. *dedotto* = ragionamento mio, o dipende da norma non nel registro o non verificata.

## 1. Sezione 13: numeri, norme e verso (punto 1 del task)

Riscontro riga per riga con il registro (N-NIS2 art. 23(4); N-NIS2-IT art. 25(5); N-NIS2-REG artt. 3, 4, 7; N-GDPR art. 33).

| Variabile | Valore e norma nel catalogo | Esito |
|---|---|---|
| `early_warning_hours` 24 | art. 23(4)(a), art. 25(5) IT: max 24 h dalla conoscenza | corretto |
| `notification_hours` 72 | 23(4)(b): 72 h dalla conoscenza | corretto |
| `final_report_months` 1 | 23(4)(d): un mese dalla trasmissione della notifica | corretto nel contenuto; unità da rivedere (R-08) |
| `progress_report_interval_months` 1 | art. 25(5)(e) IT: «mensile». La direttiva non dà cadenza | corretto e dichiarato |
| `final_report_after_closure_months` 1 | 23(4)(e) | corretto; unità da rivedere (R-08) |
| `gdpr.controller_notification_hours` 72 | 33(1): 72 h «ove possibile», con motivazione del ritardo oltre le 72 h | corretto; cfr. R-05 |
| `cloud.outage_total_minutes` 30 | art. 7(a): più di 30 min | corretto |
| `cloud.outage_partial_hours` 1 | art. 7(b): oltre 1 h | corretto |
| `users_affected_percent` 5 e `_count` 1.000.000 | art. 7(b) e (d): «5 % o 1 milione, se inferiore» | corretto, con regola del più basso |
| `financial_loss_eur` 500.000 e `_turnover_percent` 5 | art. 3(1)(a): 500.000 EUR o, se inferiore, 5 % del fatturato | corretto; cfr. R-08 |
| `recurring_min_count` 2 e `recurring_window_months` 6 | art. 4: almeno due volte in sei mesi | verso corretto (conteggio massimo 2, finestra minimo 6); cfr. R-08 |
| `recurring_review_interval_months` 3 | allegato 3.4.2(b): valutazione trimestrale | contenuto corretto; il 3.4.2 è fuori dalle sezioni ✔ dell'intestazione del registro (R-18) |

Il verso è giusto per tutte le righe: termini come massimo, finestra di osservazione come minimo, conteggio come massimo, soglie come massimo. Le esclusioni «senza soglia» (art. 7(c); art. 3(1)(b) ed (e)) sono corrette.

## 2. Rilievi

### R-01 · da_riportare · DX-22(a), DX-10: il «limite di legge» e il valore configurato non sono separati
- **Dove:** §1 regola 6; §13, colonna «Chi modifica» di tutte le righe `incident.*`.
- **Testo:** «Lo modifica solo il superadmin, con motivazione e audit.»; «massimo 24 (norma); minimo da definire».
- **Problema:** non è chiaro cosa il superadmin modifichi: il valore operativo (ammesso solo verso valori più restrittivi) o anche il limite di legge. Se il limite è modificabile con la sola motivazione, il superadmin può portare 24 h a 48 h senza un intervallo protetto. Questo viola la regola «solo verso valori più restrittivi» e lo scopo di N-NIS2 art. 23(4) e N-NIS2-REG art. 7. Il testo letterale di DX-22(a) è ambiguo.
- **Proposta:** per ogni vincolo normativo due elementi distinti: (1) limite di legge, non modificabile da UI, cambia solo con un aggiornamento versionato del catalogo che cita la versione del registro; (2) valore configurato, modificabile dal superadmin solo entro `[minimo, limite]`. Il minimo deve essere definito prima dell'attivazione (oggi «da definire» ovunque, con l'effetto di un intervallo aperto verso il basso, privo di senso: 0 h).
- **Verifica:** dedotto (la lettura di DX-22(a) è mia).

### R-02 · da_riportare · DX-10, DX-17, N-NIS2 art. 23: `incident.nis2_flow_active` è una variabile ordinaria e DX-17 contraddice il fine
- **Dove:** §13, riga `incident.nis2_flow_active`; §1 regola 4.
- **Testo:** «falso/vero», «ordinaria (interruttore di una funzione normativa)»; «Le azioni si bloccano (fail-closed)».
- **Problema:** (a) se Gravya diventa soggetto NIS2, il superadmin può lasciare l'interruttore a falso con sola motivazione e audit. Non c'è alcuna condizione protetta: ambito accertato, contratto con agenzia obbligata, doppia approvazione. (b) Con variabile non leggibile, DX-17 «blocca le azioni». Per l'interruttore e per i termini `incident.*` il blocco è controproducente: l'unico valore fail-safe è «flusso attivo» e termini pari al limite di legge. (c) Il catalogo non dice se i segnali verso A5 vengono comunque prodotti e conservati a flusso spento. Se non lo sono, all'attivazione non esistono le prove di quando l'incidente è stato conosciuto: la decorrenza (considerando 31 N-NIS2-REG: «ragionevolmente certo») non è ricostruibile.
- **Proposta:** classificare l'interruttore come «vincolo normativo condizionato», con condizioni di spegnimento documentate; per le variabili `incident.*` non leggibili usare il limite di legge e segnalare ad A5; i segnali si producono e conservano sempre.
- **Verifica:** dedotto (DX-17 e DX-10 verificati; il comportamento dell'interruttore non è specificato).

### R-03 · da_riportare · N-NIS2-REG considerando 31, art. 23(4): manca la variabile che limita il tempo di valutazione iniziale
- **Dove:** §13 (nessuna riga).
- **Testo (registro):** «il soggetto valuta tempestivamente un evento sospetto e si considera a conoscenza quando, dopo la valutazione iniziale, è ragionevolmente certo…».
- **Problema:** i termini di 24 h e 72 h decorrono dalla «conoscenza», ma senza un tempo massimo di triage la «conoscenza» può essere ritardata senza limite. Lo stesso vale per `incident.gdpr.processor_notice_hours` e per il tempo con cui il responsabile avvisa il titolare.
- **Proposta:** variabile del tempo massimo di valutazione iniziale (vincolo di progetto, non di legge: va dichiarato come tale), con intervallo protetto.
- **Verifica:** verificato (testo del registro); dedotto (la necessità della variabile).

### R-04 · da_riportare · N-NIS2-IT art. 25, DX-22(a): `incident.nis2.recipient` come variabile modificabile
- **Dove:** §13, riga `incident.nis2.recipient`.
- **Testo:** «CSIRT Italia … superadmin, con motivazione e audit … vincolo normativo (N-NIS2-IT art. 25 ✔)».
- **Problema:** il destinatario è fissato dalla legge (art. 25: CSIRT Italia). Un «vincolo normativo» non ha un verso «più restrittivo» per un destinatario. Si può configurare solo il canale e il contatto, non il destinatario. Inoltre la nota dice «canale e contatto … non nel registro»: la procedura/piattaforma ACN per le notifiche non è nel registro (la Det. 379887/2025 e la Det. 127437/2026 sono ◐).
- **Proposta:** destinatario invariante (nel catalogo delle invarianti); configurabili solo canale e contatto. Aggiungere la norma o la determinazione ACN sul canale al registro (§4).
- **Verifica:** verificato (testo del catalogo e art. 25 nel registro).

### R-05 · da_riportare · N-GDPR art. 33(1)-(2), art. 28(3)(e)-(f), DX-11: ruolo e collegamento tra le due variabili GDPR
- **Dove:** §13, righe `incident.gdpr.controller_notification_hours` e `incident.gdpr.processor_notice_hours`; DA-CV-08.
- **Testo:** «Vale per Gravya come titolare dei propri dati, non per i dati delle agenzie»; «da definire … l'art. 33(2) dice «senza ingiustificato ritardo» e non fissa ore».
- **Problemi.**
  1. **Ruolo.** L'attribuzione è corretta per lettera (titolare: 33(1); responsabile: 33(2), senza ore, confermato dal registro). Però il catalogo non dice che le due righe devono funzionare indipendentemente da `incident.nis2_flow_active` (dedotto): l'obbligo dell'art. 33(2) esiste oggi, perché Gravya è responsabile (DX-11), mentre il flusso NIS2 è spento. Il testo di apertura della §13 dice che le sole righe `incident.cloud.*` e `incident.financial_*` non producono notifiche a flusso spento. Le righe GDPR non sono menzionate: rischio di lettura per cui anche il GDPR sia «non attivo».
  2. **Etichetta.** `processor_notice_hours` è classificata «vincolo normativo», ma la norma non fissa alcun valore. È un valore contrattuale (DPA). Con l'etichetta «vincolo normativo» vale la regola «modificabile solo dal superadmin con motivazione»; un termine concordato nel DPA con le agenzie non dovrebbe poter essere cambiato unilateralmente da Gravya senza modificare il contratto.
  3. **Valore.** Finché è «da definire» (DA-CV-08), il rispetto dell'art. 33(2) non è testabile né misurabile. Il termine NIS2 di 24 h non va riusato come sostituto.
  4. **Assenti.** Nessuna variabile per l'assistenza del responsabile ai diritti degli interessati (art. 28(3)(e)) né per la comunicazione agli interessati (art. 34, a carico del titolare). Il termine di risposta alle richieste degli interessati (un mese, art. 12(3) GDPR) non è nel registro (○): v. §4.
- **Proposta:** dichiarare che le righe GDPR sono sempre attive; ritipare `processor_notice_hours` come «obbligo contrattuale (DPA)», con riferimento al contratto; chiudere DA-CV-08 prima di A5.
- **Verifica:** verificato (testi); dedotto (indipendenza dal flag, tipo della variabile).

### R-06 · da_riportare · GDPR art. 5(1)(e), DX-15, DX-16: retention senza intervallo protetto, e «modifica» non bloccata
- **Dove:** §1 RR; §2, colonna «Chi modifica» = «superadmin (RR)», «Intervallo ammesso: da definire (DA-CV-01)»; famiglia `_min`/`_max` «Default: da definire».
- **Testo:** «Il superadmin modifica solo il valore di default, e solo entro l'intervallo minimo-massimo fissato nel contratto/DPA… L'intervallo non è ancora definito».
- **Problema:** DX-15 e DX-16 vogliono la modifica solo dentro un intervallo protetto, con valori fuori intervallo non validi. Nella tabella la colonna «Chi modifica» dice «superadmin» per ogni durata, mentre `_min`/`_max` non esistono. Un'implementazione fedele alla tabella permette al superadmin di allungare qualsiasi durata senza massimo (art. 5(1)(e)) o accorciarla senza minimo (perdita delle prove, art. 5(2)). Inoltre, con intervallo non definito, la regola DX-16 «fuori intervallo è non valido» (DX-17) non è valutabile: o tutto è non valido (blocchi), o niente lo è. DA-CV-01 lo tratta come «decisione aperta (a)/(b)/(c)»; ma la regola (a) è già implicita nelle decisioni e non dovrebbe essere una scelta.
- **Proposta:** nella tabella, finché `_min`/`_max` non sono definiti, le durate sono «sola lettura» e il superadmin non le modifica. La modifica diventa possibile solo con `_min`/`_max` valorizzati dal DPA. Limite minimo tecnico per `retention.cross_tenant_access_log_months`: considerare un minimo non inferiore a 6 mesi come riferimento (N-GAR-ADS, vigenza non verificata), non come obbligo.
- **Verifica:** verificato (testo di DX-15, DX-16, catalogo); dedotto (conseguenze).

### R-07 · da_riportare · DA-C3-09, DX-15, GDPR art. 28(3)(a), (g): override per agenzia non catalogato, e «l'admin agenzia non modifica nessuna durata»
- **Dove:** §1 RR; §2 `retention.tenant_override_enabled`; §2 «famiglia protetta».
- **Testo:** «L'admin agenzia quindi non modifica nessuna durata di retention.»; «vero solo quando l'intervallo del contratto/DPA è definito (F6)».
- **Problemi.**
  1. DX-15 dice che per i dati di una specifica agenzia «l'agenzia può scegliere solo dentro quell'intervallo». Il catalogo cataloga l'interruttore ma non le variabili per agenzia (nome, chi le modifica, vincolo), né la scelta restituzione/cancellazione a fine contratto, che l'art. 28(3)(g) lascia al titolare.
  2. Non è definito chi decide sulla durata dei dati di una singola agenzia **mentre l'override è spento**: oggi il superadmin cambia il default per tutte le agenzie. Per i dati delle agenzie la durata è un'istruzione del titolare (art. 28(3)(a)); la modifica unilaterale del default è lecita solo dentro l'intervallo contrattuale (R-06).
  3. DECISIONS §5 e DX-09 testo («modificabili dal superadmin») e DX-15 non sono allineati (il catalogo lo nota in DA-CV-01). Va allineato nel testo di DECISIONS, non lasciato come decisione aperta.
  4. L'istruzione dell'agenzia è un atto auditabile: serve il riferimento (chi, quando, versione del DPA).
- **Proposta:** catalogare `retention.<classe>.tenant_value` (admin agenzia, entro `_min`/`_max`, MFA, audit, `config_version`) e `retention.tenant_offboarding_choice` (restituzione o cancellazione). Se si rinvia a F6, dichiararlo esplicitamente.
- **Verifica:** verificato (testi); dedotto (necessità delle righe).

### R-08 · minore · DX-22(a), registro: unità inadatte per vincoli espressi in mesi, e conteggi degenerati
- **Dove:** §13, righe `*_months`, `recurring_min_count`.
- **Testo:** «`incident.nis2.final_report_months` … massimo 1 (norma); minimo da definire»; «`incident.recurring_min_count` … massimo 2».
- **Problema:** con un massimo di 1 mese e un valore intero in mesi, l'unico valore ammesso è 1, quindi il vincolo non è «più restrittivo» configurabile. Per `recurring_min_count` (massimo 2, minimo ragionevole 2), il valore ammesso è uno solo: è un'invariante. Un valore di 1 renderebbe ogni incidente «ricorrente». Inoltre il «mese» di legge è calendariale, il giorno no. `financial_loss_*`: la soglia del 5 % del fatturato richiede un dato (il fatturato) che non è nel catalogo e che per Gravya (micro, forfettario) rende la soglia del 5 % quasi sempre la più bassa; serve indicare chi alimenta il dato.
- **Proposta:** unità in giorni per i termini di relazione, con regola di conversione dal mese di calendario; dichiarare invarianti le soglie senza spazio di configurazione; indicare la fonte del fatturato.
- **Verifica:** dedotto.

### R-09 · da_riportare · Reg. 2024/2690 all. 3.2 e 11, DX-18, DX-19, DX-20: variabili mancanti per accessi privilegiati (ready by design)
- **Dove:** §17.1 punto 7, che esclude volutamente gli intervalli «pianificati»; §2 (solo `retention.cross_tenant_access_log_months`).
- **Testo (catalogo):** «Non catalogati: sono materia di A5 e A6, ondata 2.»
- **Problema.** DX-10(a) fa di queste misure requisiti di progetto e DX-22 impone che nulla sia fisso nel codice. Il catalogo è l'«unico punto di verità»: se un parametro non vi compare, sarà scelto fuori dal registro. Mancano (dedotti dal registro e dalle decisioni):
  - intervallo di riesame periodico dei registri e delle risorse registrate (3.2.4, 3.2.7);
  - intervallo di riesame dei diritti di accesso e degli account privilegiati (11.2.3, 11.3.3);
  - periodo di conservazione delle copie di backup dei log (3.2.5: «per un periodo di tempo predefinito»);
  - tolleranza di sincronizzazione dell'orologio (3.2.6);
  - blocco dopo tentativi falliti, terminazione delle sessioni inattive, durata massima delle sessioni (11.6);
  - **durata dell'accesso del superadmin a una singola traccia** concesso su richiesta dell'agenzia o per un incidente (DX-19; 11.2.2 «limitato in portata e durata» per terzi);
  - **soglia minima di aggregazione** per i dati «aggregati senza identificativi» del superadmin (DX-19): senza una dimensione minima del gruppo un aggregato su un solo tenant o pochi record identifica;
  - frequenza di rotazione di chiavi e credenziali (21(2)(h); §15 non ha alcuna scadenza).
  Il catalogo può riportarli come righe «da definire (A5/A6)» senza inventare il valore.
- **Proposta:** aggiungere le righe con stato «da definire», tipo «ordinaria», e il rimando al punto del regolamento.
- **Verifica:** verificato (testi del registro e di DX-18-DX-20); dedotto (l'elenco delle variabili necessarie).

### R-10 · da_riportare · DX-20, DX-22: MFA obbligatoria presentata come scelta aperta
- **Dove:** §17.2 DA-CV-05.
- **Testo:** «Invarianti di sicurezza… MFA obbligatoria (DX-20) … (c) tutte variabili».
- **Problema:** DX-20 è decisa («MFA obbligatoria per superadmin e admin di agenzia»). Presentarla in una decisione con l'opzione «(c) tutte variabili» e «Da riportare: Sì» suggerisce che possa diventare configurabile. Il registro (N-NIS2-REG 11.7.1) dice «se opportuno»: il livello di DX-20 è più alto e va mantenuto. Idem per fail-closed (DA-B2-04, DA-A3-07), il deny per destinazione non dichiarata (DA-B2-07), la non-cattura dei contenuti in produzione (DA-E1-02), «solo dati sintetici» (DA-E3-08).
- **Proposta:** spostare le invarianti già decise in una sezione «Invarianti (non variabili)», con il riferimento alla decisione. Lasciare aperte in DA-CV-05 solo le invarianti non ancora decise.
- **Verifica:** verificato.

### R-11 · da_riportare · Invarianti mancanti dall'elenco di DA-CV-05
- **Dove:** DA-CV-05.
- **Problema:** l'elenco non include: (a) etichetta «generato da AI» / `ai_generated` per i contenuti verso terzi, «non disattivabile dal tenant» (DECISIONS §6; AI Act art. 50); (b) il divieto di registrare contenuti di prompt e risposte in produzione (DA-E1-02): non ci sono variabili che lo consentano, e va detto; (c) la regola per cui un tool senza destinazione/giurisdizione dichiarata è negato (DA-B2-07). Se non sono in una lista di invarianti, un doc-writer successivo può introdurre `*_enabled` per gestirli.
- **Proposta:** aggiungere (a)-(c) all'elenco, con il riferimento.
- **Verifica:** verificato (decisioni); dedotto (rischio).

### R-12 · da_riportare · HITL aggirabile: `hitl.approval_required_default`
- **Dove:** §3, riga `hitl.approval_required_default`; DA-CV-05.
- **Testo:** «admin agenzia, per azienda, cliente e task (C3 §2, §5) … vero/falso».
- **Problema:** il valore può essere impostato a falso per task dall'admin dell'agenzia, senza limiti. Il catalogo non dice se esistono azioni per cui l'approvazione resta obbligatoria (il vocabolario `ALWAYS_HITL`/`MONEY_WRITE` è citato solo in DA-CV-05 come possibile invariante). Per le azioni verso terzi si intrecciano l'art. 50 AI Act e le regole di marketing (PV-01): approvazione disattivabile significa contenuto generato che arriva a terzi senza persona. Gli artt. 14 e 26 non sono obbligatori (DX-11), ma l'osservabilità AI e l'art. 50 sì.
- **Proposta:** riportare all'utente: il valore `falso` è ammesso per tutte le classi di azione? Se no, un elenco di classi con approvazione sempre obbligatoria (invariante, fuori catalogo) e la variabile solo per le altre. La modifica dell'admin va in audit con identificazione dell'attore.
- **Verifica:** dedotto.

### R-13 · da_riportare · GDPR art. 25, 5(1)(c): `e2.template.pii_check_mode` ammette `warn`
- **Dove:** §10, riga `e2.template.pii_check_mode`.
- **Testo:** «`block` oppure `warn` … superadmin … proposta da validare».
- **Problema:** il controllo che impedisce a un template di incorporare dati personali è una misura di minimizzazione by design. Ammettere `warn` consente al superadmin di abbassarla per tutta la piattaforma, senza intervallo protetto e senza condizione. Il superadmin non è il titolare dei dati.
- **Proposta:** `block` come invariante, oppure `warn` consentito solo con motivazione e con segnale ad A5.
- **Verifica:** dedotto.

### R-14 · da_riportare · Osservabilità AI, art. 50: il gate E3 è abbassabile
- **Dove:** §11, righe `eval.gate.pass_rate_min_percent`, `eval.gate.max_blocking_failures_count`.
- **Testo:** «da definire; massimo tecnico 100»; «da definire; minimo tecnico 0».
- **Problema:** il gate è il controllo che impedisce l'attivazione di versioni di prompt che violano regole di conformità (HITL, art. 50, assenza di dati personali). Con `max_blocking_failures_count` configurabile verso l'alto e `pass_rate_min_percent` verso lo 0 il superadmin può disattivarlo. Il superadmin è soggetto a DX-13 ma non c'è un valore protetto.
- **Proposta:** `max_blocking_failures_count` = 0 come invariante per i casi bloccanti (in linea con DA-E3-07); `pass_rate_min_percent` solo per i casi non bloccanti.
- **Verifica:** dedotto.

### R-15 · da_riportare · GDPR art. 5(1)(e), 28(3)(g), 28(10), 17(3)(e): `retention.incident_evidence_months` senza massimo e con sospensione indefinita
- **Dove:** §2, riga `retention.incident_evidence_months`; DECISIONS §5 (riga «Evidenze di incidente»).
- **Testo:** «durata del caso + 12 mesi, sospendendo le altre scadenze per quei dati … meccanismo di sospensione da definire».
- **Problema.** (a) La «durata del caso» non ha limite: la sospensione di tutte le scadenze per i «dati collegati» è di fatto una conservazione senza termine, che può includere dati personali delle agenzie. (b) Dopo la fine del contratto (`retention.tenant_offboarding_days` 30 giorni) la sospensione può far conservare dati del titolare per scopi propri di Gravya: per la parte che non è obbligo di legge né istruzione dell'agenzia, rischio art. 28(3)(g) e art. 28(10) (dedotto, interpretazione da verificare con un legale). (c) Le basi citate: art. 23(4) della direttiva vale solo se Gravya è in ambito (flusso spento: DX-10); art. 17(3)(e) giustifica la conservazione solo nella misura necessaria a un diritto in sede giudiziaria; l'art. 5(2) è accountability, non una base di conservazione. (d) Manca un riesame periodico della sospensione e un limite alla categoria dei dati sospesi.
- **Proposta:** `_min`/`_max` per la sospensione; riesame a intervalli; elenco chiuso delle categorie di dati; per i dati delle agenzie, istruzione del titolare nel DPA. Da riportare all'utente prima di F6/A5.
- **Verifica:** dedotto (interpretazione); verificato (testi).

### R-16 · da_riportare · GDPR artt. 17, 5(1)(e), 32(1)(c), art. 28(3)(g): cancellazione, backup e pseudonimi
- **Dove:** §2; «Classi senza durata variabile»; DECISIONS §5 «Da verificare nella validazione».
- **Testo:** «artefatti di configurazione … per tutta la durata del servizio»; «attore pseudonimo».
- **Problemi.**
  1. **Backup assenti.** Nessuna variabile per la conservazione dei backup dei dati e dei log, né per la propagazione delle cancellazioni ai backup. Senza, la cancellazione a 30 giorni e la retention a 90 giorni non sono dimostrabili (art. 5(1)(e), art. 28(3)(g)). Il registro (3.2.5) richiede backup dei log «per un periodo predefinito».
  2. **Pseudonimi senza durata.** Gli artefatti «per tutta la durata del servizio» contengono l'attore pseudonimo (dato personale, considerando 26). Il catalogo non indica una variabile per la **mappa di re-identificazione**, né la regola di cancellazione dell'interessato (art. 17) sui record di 12 mesi. DECISIONS §5 propone di pseudonimizzare e conservare l'hash: nel catalogo non c'è la classe che lo realizza né la durata della mappa.
  3. **Cancellazione con valore non leggibile (DX-17).** La regola «ultimo valore valido versionato» è coerente con il fine, ma: (a) non copre il caso in cui non esista alcun valore valido (primo avvio, versioni tutte non valide); (b) se il superadmin ha accorciato la durata e la nuova versione diventa non leggibile, si cancella con la durata più lunga: i dati restano oltre la scadenza nota, accettato da DX-17 ma da documentare come limite; (c) insieme a R-06 (intervallo non definito) nessun valore può essere dichiarato «non valido».
  4. **Classi assenti.** Nessuna classe di retention per: audit delle modifiche alle variabili (`platform.config.changed`, DX-21), eventi di autenticazione e gestione utenti (Reg. 3.2.3(b), (d)), audit degli accessi alle credenziali (§15), consensi/opt-out e liste di soppressione (marketing, art. 17(1)(c) e art. 130).
- **Proposta:** aggiungere le classi e le variabili o dichiararle esplicitamente «assegnate a F6/A6 (ondata 2)», con scadenza per la definizione; definire il valore iniziale di fallback come primo valore versionato del registro.
- **Verifica:** verificato (testi); dedotto (lacune).

### R-17 · da_riportare · GDPR Cap. V, art. 28(2)-(3)(a), DA-B2-07, N-DPF: `tenant.extra_eu_optin_enabled` come unico booleano
- **Dove:** §14; §15 («Chiavi dei provider LLM per tenant … admin agenzia»).
- **Testo:** «falso/vero. Granularità (per tool o per destinazione) non specificata (DA-CV-06)».
- **Problemi.**
  1. **Coerenza con DA-B2-07 e DECISIONS §6.** Default falso e vincolo «il superadmin non può attivarlo» sono coerenti. Manca la regola tecnica che lo impone (ruolo, MFA DX-20, audit, `config_version`) e il fatto che l'opt-in è l'«istruzione documentata» dell'art. 28(3)(a).
  2. **Booleano unico.** Una sola attivazione apre ogni destinazione extra-UE presente e futura, senza che l'agenzia veda destinazione, giurisdizione, strumento di trasferimento (adeguatezza art. 45, garanzie art. 46) e sub-responsabile (art. 28(2): autorizzazione scritta e informazione delle modifiche). Con N-DPF la decisione 2023/1795 vale solo per i provider nell'elenco DPF (art. 1) ed è impugnata (C-703/25 P, ◐).
  3. **Revoca dell'adeguatezza.** Se la decisione è sospesa o revocata (art. 45(5) GDPR), nessun meccanismo del catalogo riporta a falso o rivaluta gli opt-in già dati.
  4. **LLM per tenant.** Se l'agenzia inserisce una chiave di un provider LLM extra-UE (§15), non è detto che l'egress passi dall'opt-in: lo dice B1 per l'egress-proxy (DECISIONS §6, «stessa regola»), ma il catalogo non indica la verifica sulla destinazione del provider LLM né il rapporto con DA-E3-09 (giudice LLM solo UE).
- **Proposta:** attivazione per destinazione dichiarata (come raccomanda DA-CV-06); il catalogo delle destinazioni deve riportare lo strumento di trasferimento e il suo stato; un segnale ad A5 e la disattivazione se lo strumento cade; verifica esplicita sul provider LLM.
- **Verifica:** verificato (testi); dedotto (rischi e proposta).

### R-18 · minore · Registro: `allegato 3.4.2(b)` citato come ✔ ma l'intestazione lo esclude
- **Dove:** catalogo §13, riga `incident.recurring_review_interval_months`; registro N-NIS2-REG, intestazione («✔ … Allegato 3.1-3.2, 11.1-11.7; ○ altre sezioni») e «Sezioni collegate: 3.4.2».
- **Problema:** il registro riporta il contenuto del 3.4.2(b) (valutazione trimestrale) ma l'intestazione dichiara ✔ solo 3.1-3.2 e 11. Il catalogo lo cita come «deciso». Può essere corretto, ma la verifica è ambigua.
- **Proposta:** far confermare 3.4.2(b) dal regulatory-researcher.
- **Verifica:** verificato (incoerenza interna del registro).

### R-19 · minore · Marketing (PV-01 esteso): punto 6 del task
- **Dove:** intero catalogo (nessuna riga).
- **Problema:** il catalogo dell'ondata 1 non contiene né prevede variabili o invarianti per ePrivacy, art. 130 e art. 122 Codice privacy, RPO, tracking pixel. È in gran parte materia di D1-D4, che non sono nel perimetro (A1, A3, B1, B2, C1, C3, E1, E2, E3). **Segnalo, non progetto:** (a) i punti di contatto con l'ondata 1 sono la disclosure art. 50 (R-11), l'approvazione prima dell'invio verso terzi (R-12) e le classi di retention per consensi/opt-out/soppressione (R-16.4); (b) il catalogo dovrebbe dichiarare in §1 che le variabili di marketing sono rinviate a D1-D4 e che l'ondata 1 non le introduce; (c) il termine di adeguamento alle linee guida sui pixel è scaduto il 29.10.2026 (N-GAR-PIXEL ◐).
- **Verifica:** verificato (assenza); dedotto (collegamenti).

### R-20 · minore · DX-22(b), NIS2 art. 21(2)(h): credenziali senza rotazione e chiavi
- **Dove:** §15.
- **Testo:** «da UI solo inserimento o sostituzione, mai rilettura in chiaro (mascherate, con data dell'ultima rotazione)».
- **Problema:** nessuna frequenza di rotazione né età massima; le chiavi HMAC e di firma del `run_token` non hanno una procedura di sostituzione senza interruzione. «Admin agenzia (superadmin)» per le credenziali dei sistemi esterni è ambiguo: se il superadmin può inserirle per conto dell'agenzia, è un accesso ai dati del tenant non coperto da DX-19. Il segreto della CI «non da UI» è un'eccezione a DX-22(b) dichiarata ma non decisa dall'utente.
- **Proposta:** variabili di rotazione (da definire), chiarimento del ruolo del superadmin sulle credenziali di agenzia, portare l'eccezione CI all'utente.
- **Verifica:** dedotto.

### R-21 · minore · DX-17 e A5 non operativo: segnali durante l'ondata 1
- **Dove:** §1 regola 4; §13.
- **Problema:** la regola 4 manda un segnale ad A5 per ogni variabile non valida, ma A5 non esiste nell'ondata 1 (tabella di audit minima, DECISIONS §6). Il catalogo non dice dove vanno i segnali nel frattempo, né che il «blocco» non deve essere silenzioso. Collegato a R-02.
- **Proposta:** indicare nel catalogo la destinazione provvisoria (tabella di audit minima).
- **Verifica:** dedotto.

### R-22 · minore · Valori e soglie senza minimo valido (fail-closed e sicurezza dei token)
- **Dove:** §4 (`a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`), §7 (`b1.run_token.ttl_s`, `hitl.approval_token.ttl_s`), §9 (`e2.cache.max_ttl_s`).
- **Problema:** «da definire»: senza un massimo valido un `ttl` di giorni o un `max_age` illimitato svuotano il fail-closed e la sicurezza dei token. DA-CV-02 (a) propone solo validità tecnica (positivo, minimo ≤ massimo) «ora». Per queste variabili il rischio non è tecnico.
- **Proposta:** per i token e per la validità del bundle indicare un massimo vincolato (ad esempio TTL del token ≤ vita del run o del TTL HITL, criterio già citato in DA-CV-03) già da ora, come regola e non come valore.
- **Verifica:** dedotto.

## 3. Da aggiungere al registro

Il coordinator le faccia verificare dal regulatory-researcher.

1. **GDPR art. 12(3), 15, 20 (○ nel registro).** Termine di risposta alle richieste degli interessati (un mese, prorogabile) e assistenza del responsabile (art. 28(3)(e)). Serve per R-05 e per una variabile «vincolo normativo» sul termine delle richieste degli interessati.
2. **GDPR art. 28(2), (4) letti ✔ ma da collegare** a sub-responsabili: i provider LLM e i servizi terzi sono sub-responsabili; verificare nel registro se esiste una scheda.
3. **Reg. (UE) 2024/2690, allegato, sezioni non lette (1, 2, 4-10, 12, 13):** in particolare continuità operativa e backup (RTO/RPO, conservazione dei backup), catena di approvvigionamento, crittografia e gestione delle chiavi, gestione delle vulnerabilità. Servono per R-09, R-16.1 e R-20.
4. **Reg. 2024/2690, allegato 3.4.2(b)** (R-18): confermare ✔.
5. **Det. ACN 379907/2025, Allegati 3 e 4** (incidenti «di base»), già segnalati nel registro §9.3; e il canale di notifica verso il CSIRT Italia (R-04).
6. **N-DPF: elenco ufficiale DPF** (stato di un singolo provider), e relazione con art. 46 GDPR per i provider non elencati (R-17).
7. **Data Act artt. 25 e 29** (◐): per `retention.tenant_offboarding_days` (già in DECISIONS §4).
8. **Norme di marketing:** N-PRIV-IT, N-EPRIVACY, N-RPO, N-GAR-PIXEL sono nel registro; restano non verificate le linee guida del Garante 2013 sullo spam e l'ordinanza Cass. 15881/2025 (registro §8 e N-PRIV-IT). Servono per D1-D4, non per il catalogo.
9. **N-GAR-ADS, art. 22(4) d.lgs. 101/2018** (vigenza dei provvedimenti del Garante): ○ nel registro; serve se si usa il minimo di sei mesi come riferimento (R-06).

## 4. Controllato, senza rilievi

- Default retention nella §2 contro DECISIONS §5: tutte le durate coincidono (90 gg, 90 gg, 12 m, 12 m, 30 gg, 30 gg, durata caso + 12 m, 12 m, 30 gg offboarding).
- Motivazioni della riga «evidenze di incidente» coerenti con la riscrittura di DECISIONS §5 (art. 23(4) direttiva, art. 17(3)(e), art. 5(2)), con le riserve di R-15.
- Il catalogo non contiene variabili che consentano la cattura dei contenuti di prompt e risposte (DA-E1-02), né dati reali nei test (DA-E3-08).
- Credenziali: nessun valore nel catalogo; rilettura in chiaro esclusa da UI; archivio cifrato self-hosted UE (DX-22(b)). Coerente salvo R-20.
- Nessun servizio gestito extra-UE introdotto dal catalogo; `tenant.extra_eu_optin_enabled` default falso, solo admin agenzia: coerente con DECISIONS §6 e DA-B2-07, con le riserve di R-17.
- Le note «non verificato» e la dichiarazione che qualificazione e dimensione NIS2 non sono accertate sono coerenti con il registro (N-NIS2, N-NIS2-IT art. 3).
- «Legal hold» già corretto in §16 (registro §9.4).
- Il catalogo non cita OpenTelemetry né SaaS.
- Le soglie di latenza non bloccano ma segnalano (DECISIONS §6); fail-closed di audit e decisioni (DA-B2-04, DA-A3-07) non reso configurabile.

## 5. Letture

- docs/catalogo-variabili.md: 1-303 di 303
- docs/PRINCIPI.md: 1-15 di 15
- docs/DECISIONS.md: 1-179 di 179
- docs/norme-di-riferimento.md: 1-666 di 666 non letto per intero. Letto: 84-108 (N-GDPR, tabella; celle lunghe troncate a 2.500 caratteri), 128-163 (N-DPF, celle troncate a 900), 304-431 (N-NIS2, N-NIS2-IT, N-NIS2-REG; riga 431 troncata), 432-459 (N-GAR-ADS, celle troncate a 1.200), 619-637 (§8-§9, righe lunghe troncate a 1.500). Ricerche per parola chiave sulle altre parti (intestazioni, indice): 1-83 e 160-303 non letti per intero, 460-618 e 638-666 solo grep.
