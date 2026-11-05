# Report plan-auditor: E1 v1.7 e catalogo v1.5 (commit 27cdae4)

Esito: **RIPORTA**. Nessuna violazione di un PV. Nessuna riga «Decisa» contraddetta in modo netto. Ci sono incoerenze interne a E1, tra E1 e catalogo e tra E1 e DECISIONS, e punti che richiedono una scelta dell'utente.

## Letture
- docs/E1-tracing-distribuito.md: 1-286 di 286.
- docs/PRINCIPI.md: 1-15 di 15.
- docs/DECISIONS.md: 1-120, 196-210, 268-318 di 318. Non letti §3 (righe 121-195) né §5 (righe 211-267): **lettura parziale**. Per le righe di E1 ho usato anche una ricerca per parola chiave (`E1 v1.6`, `reviewer_ref`, `run_id` e simili) sulle righe 121-318.
- docs/catalogo-variabili.md: 1-34, 152-205, 296-300, 360-452, 491-502 di 502. Sono lette per intero le tabelle di §9 e §12 e gli indici di §15-§16 (solo grep sulle righe E1 e HMAC). Non letti §2-§8, §10-§11, §13-§14, §15 e §19: **lettura parziale**.
- docs/fonti/Prompt e workflow.md (template): 1-113 di 113.
- Piano generale.md: non letto. Il template è in Prompt e workflow.md; il perimetro (E1) è nel documento di dettaglio.
- Altri documenti dell'ondata 1 (A1, B2, C3, A3): solo grep per `company_id`, `hitl_*`, `gravya.*`, `run_id`. Non sono stati letti per intero.
- /workspace/wt-impl-e1/src: solo grep (`statement_timeout`, `MIN_KEY_BYTES`, formati). Non è una lettura.
- /tmp/s8/E1-storico-v16.txt, righe 1-11 di 11: confrontato con lo Storico di E1 (righe 1.0-1.6).
- `git diff` non eseguibile (nessuno strumento shell). Il confronto con v1.6 usa solo l'estratto dello Storico.

## Rilievi

### R1 (da_riportare, verificato). Segnali ad A5 fail-open e perdibili contro «sempre conservati»
- E1 §5, «Segnali non bloccanti»: «Anche l'invio di un segnale è fail-open: se la destinazione non è scrivibile, ... l'evento va in un log locale di ripiego senza contenuti ... I contatori di perdita sono in memoria del processo ... si perdono al riavvio».
- Catalogo §18: «I segnali di incidente sono sempre prodotti e conservati, anche a `incident.nis2_flow_active` falso» (C2). Stesso testo in E1 §5, «Segnali ad A5»: «sempre prodotto e conservato».
- Problema: E1 dichiara nello stesso paragrafo che i segnali sono sempre conservati e che possono andare persi (log locale senza contenuti, contatori in memoria). Il fail-open sui segnali nasce dal rilievo CA G3-01 del terzo giro e non è una riga di DECISIONS (la riga del 2026-11-05 sul quarto giro cita «segnali con coda e thread propri», non il fail-open).
- Serve una scelta dell'utente: o si dichiara una deroga all'invariante C2 per E1 nell'ondata 1, o i segnali diventano fail-closed o durevoli.

### R2 (da_riportare, verificato). `e1.write_statement_timeout_ms`: client o server?
- E1 §5: «I timeout sono lato client: `e1.write_connect_timeout_ms`, `e1.write_statement_timeout_ms`, i keepalive TCP ... e `e1.write_tcp_user_timeout_ms`».
- Catalogo §9, riga `e1.write_statement_timeout_ms`: «tempo massimo di una singola istruzione di scrittura dell'helper (lato server)».
- Codice (`db.py` r.64, `set_config('statement_timeout', ...)`): è un limite del server PostgreSQL.
- Problema: E1 e catalogo si contraddicono. Il codice conferma il catalogo, quindi E1 è sbagliato. Va corretta anche la voce di rischio «timeout e keepalive lato client» in §11.

### R3 (da_riportare, verificato). «Vocabolario chiuso» dichiarato e poi smentito dalla tabella provvisoria
- E1 §4.2, «Validazione»: «`name`, sorgenti, esiti e codici di errore sono valori di un vocabolario chiuso, non testo libero». Così anche §4.2 sui vocabolari HITL («`gravya.decision.exec_code` (vocabolario chiuso)») e §4.3 («codici di errore da vocabolario»).
- E1 §4.2 «Vocabolari e formati PROVVISORI»: `name`, `gravya.retrieval.source` e `gravya.decision.exec_code` sono solo formato «prefisso_corpo». Il «Limite dichiarato» ammette che l'obiettivo non è raggiunto.
- Problema: le frasi normative di §4.2, §4.3 e §7 descrivono il target come se fosse lo stato attuale. Il criterio 4 («nessun valore fuori formato») non garantisce quanto dice §4.3 («non si cattura... nomi, email... in chiaro»).
- Va riscritto al condizionale o con rimando al limite. Il tema tocca PV-01 e DA-E1-02 («invariante»): oggi l'invariante «niente dati personali» vale per i formati, non per gli elenchi chiusi (vedi R4).

### R4 (da_riportare, verificato). Manca la nuova decisione aperta sugli elenchi chiusi (DA-E1-13)
- La decisione non è né in E1 Appendice C né in DECISIONS §2 o §4. Una ricerca per `DA-E1-13` e `elenchi chiusi` non trova nulla.
- E1 §4.2 «Limite dichiarato» rimanda a «DECISIONS §6, riga sui rilievi del compliance-auditor su E1 v1.6». La riga esiste (r.279) e dice solo «l'elenco chiuso dei valori di business resta da decidere con E16 o il catalogo». Non ha un ID, uno stato né opzioni.
- DECISIONS r.5 afferma che ogni decisione aperta nasce in Appendice C con ID `DA-{ID}-NN`. E1 cita il punto in §4.2, §7, §11 e App. B senza ID.
- Sì, manca: va aggiunta come DA-E1-13 in App. C e registrata in DECISIONS §2. Il doc-writer l'ha solo proposta. Serve la scelta dell'utente sulle opzioni (elenchi con E16, cataloghi di agenti, tool e modelli, oppure accettare il limite).

### R5 (da_riportare, verificato). Valori fissi (DX-22) non catalogati: lunghezza minima della chiave HMAC e formati numerici
- E1 §5: «Una chiave è valida se è lunga almeno 32 byte». App. B: «è nel codice, non nel catalogo: se debba essere un'invariante o una variabile (DX-22) è da decidere con A6».
- Codice: `MIN_KEY_BYTES = 32` (`hashing.py`).
- E1 §4.2: «I formati sono invarianti della whitelist (catalogo §18), non variabili». Il catalogo §18 (r.451) elenca solo «whitelist degli attributi E1, nomi degli header ... formato `traceparent`». Non elenca le lunghezze (2-16, 1-40, 48, 32 caratteri di versione, 128 di modello, 1-8 cifre di `key_ref`, 4 segmenti del nome di chiave del segnale) né la chiave minima.
- Catalogo §16 non ha righe per questi valori.
- Problema: i numeri sono fissi e non compaiono in §18 né in §16. La decisione del 2026-11-05 (r.279) approva «formati stretti ... invarianti ... non variabili», ma non cita la lunghezza della chiave né il limite dei 4 segmenti. Il «catalogo §18» citato da E1 non dice quello che E1 gli attribuisce.
- Azione: aggiungere in §18 e §16 del catalogo righe esplicite per i formati e per la chiave minima (con il loro stato «provvisorio»), oppure renderli variabili.

### R6 (da_riportare, verificato). «Invariante di deploy, catalogo §18» attribuita al tenant di contesto
- E1 §5: il tenant di contesto è «obbligatorio con `API_ENV=production` reale (invariante di deploy, catalogo §18)». Stesso testo nel criterio 17.
- Catalogo §18 r.446: la guardia `API_ENV=production` è un'invariante di deploy «B1 CA6, E3 AC7». Non c'è nessun riferimento a E1 né al tenant di contesto.
- L'obbligo di tenant di contesto è una scelta del coordinator (handoff) e non una riga di DECISIONS (le righe 282-286 non lo citano).
- Va aggiunto E1 tra i documenti della riga §18 e registrato in DECISIONS (come proposta da validare), oppure E1 non lo definisce invariante.

### R7 (da_riportare, dedotto). Regola DX-17 contro fail-open: mancanza di una variabile «da definire» in produzione blocca l'avvio dell'helper
- E1 §5: «in produzione la loro mancanza blocca l'avvio dell'helper»; E1 §6 e §7: tracce fail-open.
- Non è chiaro se, a helper non avviato, il run prosegue senza tracce (fail-open, ma tracciamento perso in silenzio) o si blocca (fail-closed sul tracing). Va specificato, con il segnale ad A5.
- DX-17 e catalogo regola 4(2): «l'azione che dipende dalla variabile si blocca». Il criterio 17 testa solo che l'avvio fallisce.

### R8 (minore, verificato). Riferimenti e affermazioni obsolete in E1 App. B e §4.2
- E1 §4.2 e App. B: «l'invariante "SHA-256" del catalogo §18 va aggiornata (coordinator)». Il catalogo v1.4 §18 r.451 riporta già HMAC-SHA-256 con chiave per tenant.
- E1 App. B: «La voce "chiave HMAC per tenant" non è nell'elenco credenziali del catalogo §15». È nel catalogo §15 r.289.
- E1 §3 dichiara in «È richiesto da» A1 («non emette segmenti»). A1 §3 cita E1 solo come «correlazione eventuale» e l'audit di A1 (DECISIONS §4). Verificare la simmetria quando A1 sarà allineato.

### R9 (minore, dedotto). Criterio 9 non testabile come scritto
- E1 §5: header `x-gravya-trace-id` e `x-gravya-parent-segment-id` con il valore «nel formato W3C `traceparent`». App. B ammette che il formato del `parent-id` è «non definito». B2 §4 dice «formato ispirato a `traceparent`».
- Criterio 9: «L'header di correlazione ha il formato `traceparent` e i nomi concordati». Non esiste un header `traceparent`, quindi il criterio non è verificabile. Va precisato cosa si controlla (32 cifre esadecimali nel campo trace-id).

### R10 (minore, verificato). Contratto e implementazione mescolati con affermazioni non verificate
- E1 §5: «Il ruolo che esegue le migrazioni è distinto dal ruolo applicativo...» e la funzione di controllo cross-tenant sono presentati come contratto. App. B ammette che sono «una proposta dell'implementazione, non una procedura di deploy approvata». Il quarto giro è in corso.
- E1 §5 riporta «`e1.write_tcp_user_timeout_ms` (in corso)» e App. B dice che «l'effetto ... non è verificato». Il testo è corretto sull'implementazione («non ricontrollata»), ma va tolto dal contratto «(in corso)» una volta unito il giro 4.
- §9 «implementati» è accompagnato da «in revisione e non ancora uniti» e da App. B («65 test dichiarati, non rieseguiti»). L'affermazione è onesta e non va corretta.

### R11 (minore, verificato). Catalogo
- Catalogo «Assunzione sui nomi» e §17.1 punto 1: «La convenzione dei nomi (DX-07) è ancora aperta». DX-07 è **Decisa** (F2, 2026-11-04). È testo obsoleto, già presente nella v1.4.
- Catalogo regola 6: «(questa versione: v1.5)» riferita al registro, mentre la testata dice registro v1.6.
- Catalogo §9, `e1.write_connect_timeout_ms`: «conversione da definire nel giro 4» è una nota di processo dentro il catalogo, e `e1.write_tcp_user_timeout_ms` ha «valore di sviluppo indicato dall'implementazione (giro 4)» senza valore. Il criterio 17 di E1 non può citare un valore.
- Le variabili `e1.write_*` dichiarano «intervallo minimo-massimo da fissare prima della produzione», ma non sono elencate nella regola 11 (che elenca le variabili con intervallo richiesto). Incoerenza di regola.
- Catalogo §9, `e1.write_buffer_size`: stato «da definire» con «unità: numero di segmenti (DECISIONS §6)». La decisione del 2026-11-05 (r.281) fissa unità e valore di sviluppo 100 e non il valore di produzione; la riga è coerente.

## Allineamento ai documenti dell'ondata 1 (lavoro da fare, non errori di E1)
- C3 usa ancora `company_id` (§4.3, §3 «F1... `company_id`»), `hitl_expired` (AC-15) e dice che il vocabolario `gravya.decision.outcome` per `hitl` «è definito da C3; E1 lo recepisce» (§4.4, App. B). DECISIONS (F4, r.277) dice il contrario: «vale il vocabolario di E1 v1.6, C3 si allinea». Inoltre `run_id (= thread LangGraph)` non è garantito UUID (E1 richiede UUID canonico, decisione 2026-11-05): da recepire in B1 e C1.
- B2 non nomina `gravya.tool.outcome` (decisione 2026-11-05: «va scritto anche in B2»). B2 §4 usa `trace_context` con `run_id` e `trace_id` e «ispirato a `traceparent`».
- A1, A3, B1, C1, E2, E3: non ancora allineati a F2 (`tenant_id`, nomi puntati). Non verificati uno per uno.

## Controllato (esito positivo)
- Storico di E1: righe 1.0-1.6 identiche all'estratto v1.6 (/tmp/s8/E1-storico-v16.txt). Riga 1.7 aggiunta in coda.
- Nessun OpenTelemetry come SDK o export (PV-02, DA-E1-05): solo vocabolario `gen_ai.*`.
- Nessun servizio extra-UE o SaaS di tracing (PV-01): storage in PostgreSQL self-hosted UE (DA-E1-03).
- Nessuna durata di retention propria: tutte rimandano a `retention.*` e a DX-09. Nessuna stima temporale (solo taglia M).
- Vocabolario HITL: sette transizioni e `ok`/`refused`/`error` coincidono con F4 (DECISIONS r.277). `gravya.tool.outcome` e i cinque valori coincidono con r.280 e r.285. `run_id` UUID (r.283), chiave da 32 byte e `reviewer_ref` (r.284) sono marcati provvisori come in DECISIONS. Unità e valori di sviluppo del buffer (r.281) coerenti col catalogo.
- Variabili: tutte e dieci le `e1.*` citate in E1 §5 hanno una riga in catalogo §9 e §12 con lo stesso nome. Le otto «da definire» di E1 §5 sono «da definire» nel catalogo. Nessun default o intervallo ripetuto in E1.
- `retention.traces_days` e le classi di §4.1 coincidono con catalogo §2 r.41 e regole 8c e 8d.
- Template: sezioni 1-12 in ordine, più Appendici A-C e Storico. Criteri 1-18 con test o metrica. Criterio 16 dichiarato parziale, come da decisione.
- Decisioni «Decise con riserva» (E14, partizioni): E1 le tratta con «da confermare in F6», senza darle per chiuse.

## Domande aperte per l'utente
1. R1: i segnali ad A5 sono fail-open e perdibili (deroga a C2 per l'ondata 1) o devono essere durevoli?
2. R4: opzioni per DA-E1-13 (elenchi chiusi per gli identificativi generici).
3. R5 e R6: i formati numerici, la chiave minima e il tenant di contesto obbligatorio sono invarianti (da registrare in §18) o variabili?
