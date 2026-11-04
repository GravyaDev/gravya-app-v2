# Revisione di conformità: docs/catalogo-variabili.md v1.2 (terza revisione, ultimo giro)

Revisore: compliance-auditor · Data: 2026-11-04 · Oggetto: catalogo 1.2 (commit a16cf38) · Registro delle norme: v1.6 (commit e57952c). Esito: **RIPORTA**. Nessun BLOCCA: nessuna violazione di principio, nessun contenuto in produzione, nessun trasferimento extra-UE non dichiarato, nessun dato visibile tra tenant. Lo stato è quello di un catalogo scritto sul registro 1.5 e sulle decisioni del 2026-11-04 prima della loro conferma: i rilievi sono in gran parte allineamenti. Da registrare in DECISIONS §4 come «Da riportare». Il catalogo non è modificato qui.

Letture: catalogo 1-477 di 477; PRINCIPI 1-15 di 15; DECISIONS 1-253 di 253; brief doc-writer v1.5 1-47 di 47; registro 1-828 di 828 (letto a blocchi). Report v1.1 del compliance-auditor: solo grep (per non riproporre i punti già trattati).

## 1. Controllo 1: righe toccate dal registro v1.6

| Punto v1.6 | Dove nel catalogo | Esito |
|---|---|---|
| Conversioni 28 / 89 / 184 giorni (N-TERMINI ✔: 1 mese max 28; 3 mesi max 89; 6 mesi min 184; 12 mesi 365 come intervallo massimo) | regola 7; §13.2 (`final_report_days`, `progress_report_interval_days`, `final_report_after_closure_days`, `recurring_window_days`, `recurring_review_interval_days`); §19.2 (365); §17.1 punti 15 e 16 | **Valori confermati**, direzione corretta (max per difetto, min per eccesso). **Testi superati**: «Il calcolo è del redattore, non della norma», «reg. 1182/71, ○», «da confermare con un legale». Nuova avvertenza non riportata: il reg. 1182/71 vale per lettera solo per gli atti del Consiglio o della Commissione; per GDPR e NIS2 (atti di Parlamento e Consiglio) e per l'art. 25 d.lgs. 138/2024 (atto nazionale, computo non verificato) è interpretazione. Per le ore (24 h, 72 h) il registro dice di contare dal momento esatto della conoscenza e che non slittano nei giorni non lavorativi: il catalogo non lo dice (R3-05) |
| Data Act art. 25(2) ✔ (testo EN integrale) | §2 `retention.tenant_offboarding_days` e `_choice`; §17.1 punto 8 | **Non allineato**: R3-02, R3-03 |
| GDPR art. 12(3) e proroga (87 giorni in sequenza); artt. 15-22 | §13.3 `dsar.assist_max_days`, `incident.gdpr.processor_notice_hours` | Natura corretta (obbligo del titolare, DPA per Gravya, art. 28(3)(e)); nessun vincolo normativo attribuito a Gravya. Manca il riferimento di coerenza (28 giorni, 87 con proroga) e un intervallo protetto: R3-06 |
| Soglie PMI (N-PMI ✔) | §13 contesto, §17.1 punti 5 e 15, `incident.scope_review_interval_days` | Il catalogo non riporta soglie e dice «non accertato»: nessuna cifra errata. Punto 15 superato («raccomandazione non verificata»). Criteri di ambito da completare: R3-09 |
| Art. 22(4) d.lgs. 101/2018 ◐ e sei mesi ADS | §17.1 punto 6; §2 `retention.cross_tenant_access_log_months` (12 mesi, scelta di DECISIONS §5) | **OK**: i sei mesi non sono marcati «vincolo normativo» in nessuna riga, la durata è «ordinaria». Il punto 6 dice «vigenza non verificata»: da precisare («in quanto compatibili», ◐, nessuna fonte accerta la compatibilità, v. registro N-GAR-ADS) |
| Reg. 2024/2690 sezioni 7, 8, 10, 12, 13 ✔ (lotto 6) | §17.1 punto 7 («restano non lette le sezioni 7, 8, 10, 12, 13»), §19.2 («due valori numerici») | **Non allineato**: 10.1.3 fissa un terzo valore, R3-04 |

## 2. Rilievi

### R3-01 · da_riportare · DECISIONS (brief, decisioni del 2026-11-04) / DA-CV-18..23: il catalogo le tiene aperte
- **Dove:** §17.2 «Aperte», righe DA-CV-18..23; §14 righe `transfer_instrument` («da definire (A6)») e `subprocessor_authorization`; §2 righe `retention.incident_signals_months`, `config_audit_months`, `auth_events_months`, `credential_access_months`; regola 4 punti (3) e (4); §15 ultimo capoverso.
- **Testo citato:** «Aperte. Sono le sole scelte che emergono dall'applicazione di D1-D8… DA-CV-20 … (a) conservazione senza scadenza fino al primo valore di A6 o F6; (b) tetto provvisorio»; brief: «DA-CV-20: … avranno un tetto provvisorio fissato dall'utente prima dell'avvio in produzione».
- **Problema:** le sei scelte sono confermate dall'utente (brief): DA-CV-18 (b), 19 (a), 20 (b), 21 (a), 22 (a), 23 (a). Il catalogo le presenta ancora come aperte e a DA-CV-19 lascia «da definire (A6)» chi imposta strumento e sub-responsabile, mentre è il superadmin con fonte, riferimento al DPA e audit. Finché la regola 4 (3) e (4) resta senza il tetto di DA-CV-20 (b), segnali e audit sono «esclusi dal blocco» ma senza valore di retention: per il GDPR art. 5(1)(e) è conservazione senza scadenza di fatto. Il rischio è contenuto perché l'ondata 1 non va in produzione.
- **Proposta:** nel catalogo 1.3 spostare DA-CV-18..23 tra le decise con la scelta; in §14 attribuire al superadmin strumento e autorizzazione; nella regola 4 scrivere che le quattro classi non vanno in produzione senza il tetto fissato dall'utente; ricollegare le righe di §2.
- **Verifica:** verificato (brief del 2026-11-04, raccomandazioni confermate); la conseguenza sulla regola 4 è dedotta.

### R3-02 · da_riportare · N-DATAACT art. 25(2)(a), (g), (h), art. 25(3), art. 1(5) (✔ v1.6, testo EN); GDPR art. 28(3)(g): `retention.tenant_offboarding_days` è un massimo
- **Dove:** catalogo §2, righe `retention.tenant_offboarding_days` e `retention.tenant_offboarding_choice`; §17.1 punto 8; §16 riga A1 §7 «30 giorni (fine contratto)».
- **Testo citato:** «30 giorni dalla fine del contratto: restituzione o cancellazione, salvo obblighi di legge … Possibile vincolo Data Act artt. 25 e 29: non verificato (registro ◐) … ordinaria»; registro §9 punto 5: «DX-09 §5 … e `retention.tenant_offboarding_days` = 30 non possono essere un massimo per i clienti che esercitano il passaggio»; brief: «`retention.tenant_offboarding_days` diventa un minimo».
- **Problema:** (1) il default cancella a 30 giorni dalla fine del contratto, mentre il testo (art. 25(2)(g)-(h)) vieta di cancellare prima della scadenza di un periodo di recupero di almeno 30 giorni di calendario che inizia dopo la fine del periodo transitorio. Se il SaaS è un «servizio di trattamento dei dati» (da confermare con un legale), Gravya cancellerebbe prima del minimo. (2) Tipo «ordinaria» e «sola lettura (RR)»: manca il limite di legge (minimo, solo in aumento) distinto dal valore operativo (regola 6, C1). Con la RR il superadmin potrebbe abbassare il valore dentro un intervallo DPA ancora indefinito. (3) «Periodo di uscita» in `_choice` è ambiguo: l'esportazione deve durare almeno il recupero, misurato dalla fine del periodo transitorio. (4) La nota «registro ◐, art. 25(2) non letto» è superata. (5) Il caso del cliente che sceglie solo la cancellazione (art. 25(3)(c)) è aperto nel registro: per prudenza 30 giorni anche lì, con istruzione scritta dell'agenzia.
- **Proposta:** riscrivere la riga come vincolo normativo condizionato: limite di legge «minimo: solo in aumento», 30 giorni di calendario dalla fine del periodo transitorio; valore operativo non inferiore; massimo, se serve, a carico di F6 e non inferiore a 60 giorni dall'avvio del passaggio (registro, N-DATAACT); qualificazione del SaaS da confermare con un legale; aggiornare il punto 8 di §17.1 e allineare DX-09 §5 (§4 di DECISIONS ha già la riga «Da riportare»: qui si segnala che la decisione del brief non è applicata e il registro è ora ✔).
- **Verifica:** verificato (testo della norma, registro v1.6); applicabilità a Gravya dedotta.

### R3-03 · da_riportare · N-DATAACT artt. 25(2)(a), (d), 25(4), 29(1) (✔): termini contrattuali del passaggio senza variabile né invariante
- **Dove:** catalogo §2 e §18 (assenti).
- **Testo citato:** registro: «periodo transitorio massimo obbligatorio di 30 giorni di calendario … preavviso massimo non superiore a due mesi … 14 giorni lavorativi … non superiore a sette mesi … dal 12 gennaio 2027 i fornitori non possono imporre alcun costo di passaggio».
- **Problema:** se Gravya è in ambito, i contratti con le agenzie devono contenere questi termini. Nel catalogo non c'è nulla: né un limite («massimo, solo in diminuzione»: transizione 30 giorni, preavviso 59 giorni per difetto, notifica di irrealizzabilità 14 giorni lavorativi, periodo alternativo 7 mesi), né un'invariante (costi di passaggio a zero dal 12.1.2027; fino ad allora solo ridotti). Un valore operativo oltre il limite non sarebbe bloccato da nulla.
- **Proposta:** decisione dell'utente se catalogare questi termini come righe «vincolo normativo» in §2, con condizione «solo se Gravya è servizio di trattamento dei dati», e se i costi di passaggio entrano in §18. 59 e 12 mesi = 365 giorni derivano da N-TERMINI; i giorni lavorativi non hanno conversione valida.
- **Verifica:** verificato (norma); inclusione nel catalogo dedotta.

### R3-04 · da_riportare · N-NIS2-REG allegato 10.1.3 (✔ lotto 6); DX-10 (a)-(c): terzo valore fissato dalla norma non catalogato
- **Dove:** catalogo §19.2, intro («Due valori numerici fissati dall'allegato») e §17.1 punto 7.
- **Testo citato:** registro: «riesame dell'assegnazione del personale ai ruoli e dell'impegno di risorse umane "a intervalli pianificati e quanto meno una volta l'anno" (10.1.3)»; registro §9 punto 10(d): «l'unico numero nuovo è il riesame almeno annuale dell'assegnazione del personale ai ruoli (10.1.3)».
- **Problema:** DX-10 (c) e DX-22(a) vogliono i valori fissati dalla norma come vincoli. Il riesame 1.1.2 e 2.1.4 è in §19.2, quello di 10.1.3 manca perché il catalogo poggia sul registro 1.5. Per Gravya (due persone, ma accesso superadmin e admin) il riesame degli accessi ai ruoli è pertinente.
- **Proposta:** aggiungere a §19.2 `security.role_assignment_review_interval_days` (nome assegnato dal redattore): massimo, solo in diminuzione, 365 giorni, valida solo se Gravya è fornitore cloud in ambito, con intervallo richiesto (regola 11); correggere «due» in «tre» e il punto 7 (le sezioni 7, 8, 12, 13 non aggiungono valori).
- **Verifica:** verificato.

### R3-05 · minore · N-TERMINI ✔, N-GAR-ADS (art. 22(4) ◐): testata e punti non verificati superati; ore e applicabilità
- **Dove:** testata e regola 6 («questa versione: v1.5»), regola 7, §17.1 punti 6, 7, 15, 16, 22; §13.2 e §13.3 (termini in ore).
- **Testo citato:** «Il calcolo è del redattore del catalogo, non della norma»; «il computo del "mese" (reg. 1182/71, ○) … la raccomandazione 2003/361/CE … GDPR artt. 15-16, 18-22 (○)»; «la vigenza dopo il GDPR non è verificata».
- **Problema:** per la regola 6 il limite di legge cambia solo con una nuova versione del catalogo collegata a una versione del registro: il collegamento è alla v1.5, il registro è v1.6. Per le righe che citano le conversioni il valore non cambia (controllato). Mancano: (a) l'avvertenza di applicabilità (1182/71 per lettera solo atti di Consiglio e Commissione: vale per il reg. 2024/2690; per GDPR, NIS2 e d.lgs. 138/2024 art. 25 è interpretazione, ma 28 giorni restano prudenti in ogni lettura); (b) la regola delle ore (dal momento esatto della conoscenza; nessuno slittamento per giorni non lavorativi); (c) lo slittamento dell'art. 3(4) non va usato per i massimi; (d) art. 22(4) d.lgs. 101/2018 ◐: i sei mesi del Garante sono buona pratica, non vincolo.
- **Proposta:** portare la testata e la regola 6 al registro v1.6; riscrivere i punti 6, 7, 15, 16, 22; aggiungere alla regola 7 le ore e l'avvertenza; la conferma con un legale resta solo per l'applicabilità.
- **Verifica:** verificato (registro v1.6, N-TERMINI e §9 punto 10).

### R3-06 · minore · GDPR artt. 12(3), 28(3)(e) ✔; N-TERMINI: `dsar.assist_max_days` e `incident.gdpr.processor_notice_hours` senza intervallo protetto
- **Dove:** catalogo §13.3, righe `incident.gdpr.processor_notice_hours` e `dsar.assist_max_days`; regola 11 (non le include).
- **Testo citato:** «da definire; deve lasciare al titolare il tempo per rispondere entro il suo termine … Modificabile dal superadmin solo come attuazione di una modifica del DPA»; registro §9 punto 10(b): «coerenza utile: restare entro i 28 giorni, il massimo prudente per il mese dell'agenzia».
- **Problema:** un termine di assistenza oltre il mese (o oltre 87 giorni se l'agenzia proroga) toglie all'agenzia la possibilità di rispondere (diritti artt. 15-22). Il catalogo non ha un tetto e non cita 28/87 come riferimento. La protezione è solo il rinvio al DPA, che non esiste ancora. Il termine è contrattuale, non di legge: nessuna violazione, ma un rischio per i diritti degli interessati.
- **Proposta:** con una nuova variabile ordinaria `dsar.assist_max_days` e un massimo deciso dall'utente (riferimento: 28 giorni per il mese, 87 con proroga contata in sequenza), da fissare con F6 prima dell'attivazione; l'intervallo vale come per la regola 11.
- **Verifica:** verificato (norma e registro); necessità del tetto dedotta.

### R3-07 · da_riportare · GDPR artt. 44-46, 28(3)(a); N-DPF (✔ decisione, ◐ sito) ; DA-B2-07, D5: lo stato dello strumento di trasferimento non scade
- **Dove:** catalogo §14, regole D5, D7 e riga `transfer_instrument_status`.
- **Testo citato:** «Lo stato lo aggiorna il superadmin, con la fonte e l'audit»; registro N-DPF: «lo stato cambia con la ricertificazione annuale … nuovo controllo a intervalli o prima di ogni nuovo trasferimento … il controllo va fatto sull'entità giuridica che figura nel contratto … per l'ambito non HR».
- **Problema:** lo stato «valido» è un dato manuale senza data di verifica né scadenza: se nessuno lo aggiorna, l'opt-in resta attivo su uno strumento caduto (adesione DPF non rinnovata, decisione sospesa), e il segnale ad A5 parte solo quando qualcuno cambia lo stato. Contro il fail-closed (DX-17) e la regola di §14 («strumento caduto = disattivazione»). Gli intervalli sono una scelta di gestione, non di legge (registro).
- **Proposta:** aggiungere data e fonte dell'ultima verifica e una variabile `transfer.instrument_review_interval_days` con massimo protetto (regola 11); alla scadenza lo stato diventa «non valido», l'opt-in si disattiva e parte il segnale ad A5. Il controllo deve indicare entità giuridica, ambito dei dati e data di consultazione.
- **Verifica:** dedotto (la lacuna), verificato (indicazioni del registro).

### R3-08 · minore · GDPR artt. 5(1)(c), (e), 17, considerando 26; DA-CV-22: riapplicazione delle cancellazioni al ripristino
- **Dove:** catalogo §17.2 DA-CV-22 (a); §2 `retention.data_backup_days`.
- **Testo citato:** «al ripristino, le cancellazioni già eseguite si riapplicano»; brief: «al ripristino di un backup le cancellazioni già eseguite si riapplicano».
- **Problema:** per riapplicare le cancellazioni serve un registro delle cancellazioni con gli identificativi delle persone cancellate. È un dato personale (o pseudonimo) che sopravvive alla cancellazione. Senza durata e minimizzazione diventa una struttura append-only con dati di chi ha chiesto di essere cancellato.
- **Proposta:** il registro contiene solo identificativi tecnici (hash o pseudonimo), non l'identità; durata non oltre `retention.data_backup_days`; classe di retention propria assegnata da F6.
- **Verifica:** dedotto.

### R3-09 · minore · N-NIS2-IT art. 3(2)-(4), (9)(f), (10), art. 7; N-PMI ✔: `incident.scope_review_interval_days` senza i criteri dell'ambito
- **Dove:** catalogo §13.1 riga `incident.scope_review_interval_days`; §17.1 punto 5.
- **Testo citato:** «Riesame periodico dell'ambito NIS2 di Gravya (qualificazione come fornitore cloud, dimensione, contratti con agenzie soggette NIS2)»; registro N-PMI: «contano i dati consolidati … dell'ultimo esercizio approvato … il superamento non cambia la categoria salvo due esercizi consecutivi»; N-NIS2-IT: registrazione annuale (1.1-28.2).
- **Problema:** il riesame non cita i casi che rendono soggetto NIS2 a prescindere dalla dimensione (art. 3(9)(f) individuazione dell'ACN, art. 3(10) impresa collegata che fornisce servizi TIC) né i dati consolidati. Dedotto: se il riesame guarda solo ai propri numeri, Gravya può non accorgersi di essere stata individuata dall'ACN. Il registro ha il dato sul forfettario (DX-10), non sui consolidati.
- **Proposta:** nella riga elencare i criteri (qualificazione, dimensione consolidata, individuazione ACN, imprese collegate, contratti); massimo protetto non oltre 365 giorni, coerente con il ciclo di registrazione annuale (dedotto); valore da A5.
- **Verifica:** verificato (registro), dedotto (la proposta di intervallo).

## 3. Da aggiungere al registro (per il regulatory-researcher)

1. **Reg. 1182/71 applicato a GDPR, NIS2 e d.lgs. 138/2024 art. 25**: giurisprudenza o prassi (R3-05); computo dei termini nel diritto italiano per l'art. 25(5) d.lgs. 138/2024.
2. **Data Act, testo italiano dell'art. 25 e autorità competente (art. 37)**; clausole contrattuali tipo della Commissione; caso del cliente che sceglie solo la cancellazione (R3-02, R3-03).
3. **Art. 22(4) d.lgs. 101/2018** su Normattiva o GU (◐ → ✔) e atti del Garante dell'era GDPR che richiamino il provvedimento ADS (R3-05).
4. **Elenco DPF** e modo di consultarlo con evidenza datata (R3-07).
5. **Computo dei termini di notifica NIS2 in ore nel diritto italiano**, se diverso da 1182/71 (R3-05).

## 4. Controllato, senza rilievi

- Direzione e conversioni di §13.2 contro N-TERMINI: 1 mese → 28 (max), 3 mesi → 89 (max), 6 mesi → 184 (min), 12 mesi → 365 (massimo dell'intervallo): corretti. `incident.recurring_window_days` come minimo (almeno due volte in sei mesi), `recurring_review_interval_days` come scelta prudente: coerenti col registro.
- Soglie art. 3(1)(a) e art. 7 (30 min, 1 h, 5 %, 1.000.000, 500.000 EUR, 5 %): uguali al registro; verso «massimo, solo in diminuzione» corretto.
- Sei mesi ADS e art. 22(4): nessuna riga li marca come vincolo normativo.
- Art. 12(3): nessuna variabile attribuisce il mese a Gravya; «un mese» non riscritto come «30 giorni» in un vincolo; art. 34 a carico del titolare.
- §18: invarianti coerenti con DX-17, DA-B2-04, DA-A3-07, DA-B2-07, DA-E1-02, DA-E3-08, DX-19, DX-20, art. 50(1) e (2). Nessun `*_enabled` per attenuarle.
- §14: opt-in per destinazione, superadmin che non attiva, sub-responsabile anche per l'UE (art. 28(2), (4)): coerente con D5, D7.
- §15: credenziali mai rilette, archivio cifrato self-hosted UE, superadmin che non inserisce credenziali per un'agenzia (DA-CV-16), CI senza dati reali.
- Regola 8 e regole relazionali (token, partizioni, traces_days + partizione ≤ max): nessun modo di scendere sotto un obbligo di legge.
- Regole 11 e 12: nessuna variabile di sicurezza attivabile senza intervallo; sospensione per evidenze non attivabile senza massimo, riesame e categorie.
- DA-CV-18 (b): non riproposta (decisa); art. 50(4) resta del deployer.
- Isolamento tra tenant, minimizzazione, contenuti di prompt e risposte, trasferimenti verso provider LLM: nessuna riga del catalogo li indebolisce.
