# Report plan-auditor: ristrutturazione di DECISIONS.md

Esito: **BLOCCA**. Nel candidato si perdono una decisione in vigore e una decisione aperta, e vanno corrette prima della sostituzione. Il resto è fedele, con differenze di sostanza minori elencate sotto (R3-R12).

## Letture
- docs/DECISIONS.md (originale, 329 righe): lette per intero. Righe 1-12 e 114-119 riletture per verifica; righe 119-329 lette in questa sessione; righe 1-120 lette in una sessione precedente. Nel frattempo il file è cresciuto (DA-E1-13 e le righe del giro unico): ho usato la versione corrente.
- docs/revisioni/decisions-ristrutturazione/DECISIONS-candidato.md: 1-241 di 241.
- docs/revisioni/decisions-ristrutturazione/decisioni-archivio-candidato.md: solo grep (306 righe non vuote, intestazioni, righe 126, 306, 307, 337). Il confronto integrale non è stato fatto riga per riga: **verifica dell'archivio per campione**. Totale 337 righe = 329 dell'originale più 8 di intestazione, coerente con una copia integrale.
- docs/revisioni/decisions-ristrutturazione/task-plan-auditor.md: 1-20 di 20.
- Riferimenti incrociati: grep di `DECISIONS §` nei nove documenti dell'ondata 1.

## Rilievi

### R1 (bloccante, verificato). Persa la decisione sulle mutazioni del grafo A1 (non segmenti E1, `trace_id` dentro un run)
- Originale §4 r.159 (riga barrata, decisa il 2026-11-03): «Mutazioni del grafo A1: solo eventi di audit (tabella di audit, poi A5), conservazione 12 mesi; se la mutazione avviene dentro un run, collegamento alla traccia tramite `trace_id`. Non diventano segmenti E1».
- Candidato: la decisione non compare in nessuna sezione. §6 ha solo «Fail-closed dell'audit delle mutazioni di A1», e §5 ha i 12 mesi dell'audit. Mancano «non segmenti E1» e il collegamento con `trace_id`.
- Riferimenti rotti: E1 §3 («A1 scrive il `trace_id` nell'audit delle mutazioni ... non emette segmenti, DECISIONS §4») e A1 App. C r.251 («Mutazioni del grafo. Decisa (2026-11-03; DECISIONS §4)») citano proprio questa riga.
- Correzione: aggiungere una riga a §6 («Mutazioni del grafo A1») con il testo in vigore e aggiornare le citazioni di E1 e A1 da §4 a §6.

### R2 (bloccante, verificato). Persa una decisione aperta: creazione del sottoprodotto (a) di G1
- Originale §4 r.202 (riga barrata per H1-H3, ma con un residuo aperto): «La creazione del sottoprodotto (a) di G1 non è necessaria per H1-H3 e resta da decidere».
- Candidato: nessuna traccia di G1 (a), né in §4 né in §6 (la riga G2 cita solo «da zero»).
- Correzione: aggiungere in §4 un punto «G1 (a): creazione di un sottoprodotto per il miglioramento del servizio, da decidere (non necessaria per H1-H3)».

### R3 (da_riportare, verificato). Contenuto del quarto giro di E1 non riportato
- Originale §6 «Quarto giro di correzioni a E1 v1.6» (decisa 2026-11-05): timeout lato client sulla connessione del thread di scrittura con `tcp_user_timeout` da una nuova variabile `e1.write_tcp_user_timeout_ms` «da definire»; `close()` senza attese illimitate; segnali con coda e thread propri e connessione con gli stessi timeout; ruolo di migrazione senza appartenenza al ruolo `BYPASSRLS`; migrazioni senza errori inghiottiti; prova dei segnali da ruolo non superuser.
- Candidato: la riga è assente. «E1: scrittura e parametri» cita solo buffer, connessione propria e `e1.write_connect_timeout_s`. `e1.write_tcp_user_timeout_ms` e la regola su `BYPASSRLS` non compaiono.
- Terzo giro (originale §6): anche «funzione di controllo del `trace_id` chiusa (niente oracolo)», «`production_override` che può solo irrigidire la guardia», «solo inserimento sui segnali anche con ruolo non superuser» (quest'ultimo è nel candidato) e test con ruoli non superuser. I primi due mancano.
- Sono decisioni dell'utente applicate a E1 §5. Non vanno perse per riferimento: riportare in una riga «E1: robustezza della scrittura e dei ruoli» oppure dichiararle assorbite da E1 §5 con rimando esplicito.

### R4 (da_riportare, verificato). DX-10: manca il comportamento delle variabili `incident.*` non leggibili
- Originale DX-10 (precisazione C2): «Con una variabile `incident.*` non leggibile vale il limite di legge, con segnale ad A5».
- Candidato DX-10 e DA-CV-09: conservano solo il caso di `incident.nis2_flow_active` non leggibile (flusso attivo). La regola generale per le altre `incident.*` manca (è in catalogo regola 4 e 6, ma DECISIONS è la fonte).
- Correzione: aggiungere la frase a DX-10.

### R5 (da_riportare, verificato). Tenant di contesto e `API_ENV`: sostanza alterata
- Originale §6 «Tenant di contesto dell'helper» (decisa): «obbligatorio solo con `API_ENV=production` reale; **`production_override` da solo non lo attiva**; **fuori produzione è facoltativo, con segnale**».
- Candidato «E1: ambiente e avvio»: ripete «obbligatorio solo con `API_ENV=production` reale» ma toglie «`production_override` non lo attiva» e «facoltativo con segnale fuori produzione». Aggiunge «assente vale sviluppo con segnale», che nella decisione originale non c'è (viene da E1, `e5.environment_undeclared`).
- Originale §6 «Valore di `API_ENV` fuori dall'insieme chiuso» (decisa): «un valore fuori dall'insieme blocca l'avvio con un segnale (sostituisce "segnala e prosegue")». Il candidato riporta il blocco; manca solo la nota sul test `test_R15b` (non è una decisione, può restare nell'archivio).
- Correzione: ripristinare le due clausole e togliere o marcare come «da E1» il caso «assente vale sviluppo».

### R6 (da_riportare, verificato). DA-E1-13 alterata
- Originale §2 r.118: «(a) valori dai cataloghi esistenti per modelli, provider, strumenti e agenti (B1, B2); (b) UUID ...; (c) solo formato accettabile solo nell'ondata 1», con l'elenco dei campi coperti (`opaque_id`, `model_identifier`, `name`, `destination`, `exec_code`).
- Candidato: «(B1, B2, E16)»: E16 non è nella decisione originale. L'elenco dei campi è tolto, ma è quello che dice il perimetro della decisione.
- Correzione: allineare l'elenco dei responsabili all'originale (o dichiarare E16 come aggiunta del coordinator) e ripristinare l'elenco dei campi.

### R7 (da_riportare, verificato). Dati sul contenuto di DX-22 e DA-E1-xx omessi
- DX-22: nel candidato mancano (c) «i documenti di dettaglio citano solo il nome della variabile», la mascheratura con «data dell'ultima rotazione» e il responsabile del catalogo e del registro versionato (A6; il candidato dice «il modello è di A6»). «Il giudice LLM di E3 gira nell'UE» è in DA-E3-09, ok.
- DX-19: l'originale dice «(invariante)» sul solo dato aggregato e sul log di ogni accesso; il candidato non lo marca.
- DX-10: il criterio dimensionale NIS2 «non documentato nel registro» è in §4 (ok).
- Correzione: rimettere le tre frasi di DX-22 e il termine «invariante» di DX-19.

### R8 (minore, verificato). Valori persi in sintesi
- Originale §6 «Data Act e trasferimenti (E15)»: periodo transitorio fino a 30 giorni, preavviso massimo di due mesi, alternativa fino a sette mesi. Candidato: «termini dell'art. 25 nel catalogo» senza i valori (sono nel catalogo `dataact.*`).
- Originale H1: elenco delle metriche («latenze, errori, costi, tassi di rifiuto HITL, esiti delle valutazioni»). Candidato: non elencate.
- DA-CV-03 (opzioni (b) e (c) escluse), DA-CV-09 (opzione (c) esclusa), DA-CV-20 (elenco delle classi senza durata), DA-CV-04 (elenco dei campioni dei test): omessi in sintesi. Nessuna di queste tolte cambia una regola; sono motivazioni.
- §5 originale, evidenze di incidente: «meccanismo da definire in F6 e A5» omesso; E1 §4.1 dice «non deciso», quindi il candidato dovrebbe segnalarlo come aperto.

### R9 (minore, verificato). Punti «Da riportare» omessi dall'originale §4, non chiusi con scrittura esplicita
- «DA-CV-08, stato discordante» (r.191): superato dal catalogo 1.2, che si allinea a §7; non è barrato nell'originale. Superata, ma la chiusura è implicita.
- «Testi superati nel catalogo v1.1» (r.195): il catalogo 1.2 li riscrive, non barrato. Superata, chiusura implicita.
- «TTL dei token, regola 8b» (r.193): il candidato la mantiene aperta; il catalogo regola 8b usa già il TTL effettivo (D5). Presente nel candidato ma probabilmente già risolta. Controllare con il catalogo.
- Basi giuridiche delle evidenze di incidente (r.197): chiusa; per i dati di Gravya le basi sono in §5, e B1 §7 la cita come «DECISIONS §4» («la base resta da scegliere con un legale»). Il riferimento diventa vuoto.

### R10 (minore, verificato). Righe di processo tolte
Righe dell'originale non riportate nel candidato, con la mia valutazione:
- §4: righe barrate sulla notifica NIS2, TTL HITL, DX-22 (4 righe), A1, ruoli GDPR, art. 50(2), conflitto token, orfani; soglie incidenti ricorrenti; sub-responsabili; credenziali; valori senza massimo; override per classe; strumento di esportazione; dati per il miglioramento: **chiuse e riportate in DX/DA/§6** (eccezione: A1 e G1 (a), R1 e R2).
- §4: «Bloccante» E1 v1.6 (giro 1 e giro 2), «Terzo giro», «Revisione E1 v1.7», «Revisione E1 v1.8»: **giri di revisione conclusi** o in chiusura. Il candidato tiene «E1, chiusura della v1.8» come punto aperto con puntatore ai report. Il rilievo V-02 (la revoca di `BYPASSRLS` non chiude l'isolamento, che dipende da `app.tenant_id` impostato dal chiamante, da dichiarare come requisito di deploy) e i rilievi CR 1, 3, 4, 5, V1, V2 sono nei report e non nel candidato: accettabile se il puntatore resta.
- §6 processo conclusi: dossier del code-reader per la v1.5; catalogo per la v1.5 (solo la regola «doc-writer non scrive nel catalogo» è tenuta); C13 lotto 5; C14 doc-writer senza Bash; D8 processo del catalogo 1.2 e lotto 6; «Processo di revisione della v1.5» (un giro; RIPORTA non blocca; solo BLOCCA ferma); «Correzioni a E1 v1.6 dopo il blocco: un solo giro»; «Rilievi del compliance-auditor su E1 v1.6»; «Terzo giro»; «Quarto giro»; «Processo per E1 v1.7 e catalogo»; «Variabili mancanti da aggiungere al catalogo (C8)». Sono passi conclusi. Dubbio: la regola «un esito RIPORTA non blocca, solo BLOCCA ferma il documento» è una regola di processo che potrebbe valere ancora (è applicata nelle sequenze del README degli agenti): verificare se è nel README, altrimenti tenerla in §6.
- §6 «Il fail-closed ... stato: l'utente ha confermato tutte le raccomandazioni» e la riga «Il grafo C1 ...» sono riportate.

### R11 (minore, dedotto). Intestazione e riferimenti
- Il candidato rinomina §3 («Escalation: nessuna») e §6 («Regole trasversali di progetto»). Gli altri documenti citano solo §1, §4, §5, §6, §7: nessun riferimento a §3. Nessun problema di numerazione, salvo R1 (§4).
- E1 §5 cita «DECISIONS §4, «Valori provvisori di E1 v1.6»»; il candidato ha «E1, valori provvisori» in §4 (titolo diverso). E1 App. B citava anche «DECISIONS §6, riga sui rilievi del compliance-auditor su E1 v1.6» (nelle v1.7/v1.8: nel testo letto v1.8 è sostituita da DA-E1-13). Aggiornare le citazioni nella v1.9.
- Il candidato rimanda a `decisioni-archivio.md`, mentre il file candidato si chiama `decisioni-archivio-candidato.md`: coerente se il registrar lo rinomina. Verificare.

### R12 (minore, verificato). Struttura dell'originale
- L'originale ha una riga vuota tra la tabella di §6 e le ultime cinque righe (r.294), che le stacca dalla tabella. Il candidato le ha integrate nella tabella: miglioramento.

## Controllato
- **DX-01..DX-22:** tutte presenti (stati: DX-02 «Decisa in parte», DX-03, DX-05, DX-06, DX-08 «Aperta»). Contenuti DX-09, DX-10, DX-19, DX-22 verificati con le precisazioni (eccezioni R4, R7).
- **DA di §2 e §3:** tutte presenti come riga o alias. Verificate una per una le 94 ID (DA-A1-xx, A3, B1, B2, C1, C3, E1, E2, E3). Stati preservati (Aperta per A1-03, A1-04, A3-01..04, B1-01..03, B2-03, B2-05, C1-03, E2-01..03, E3-01, E3-03..05; «Decisa (ipotesi di lavoro)» per A1-02, A1-06, E1-03, E1-04, E1-07; «Decisa in parte» per DA-E2-04; «Decisa con condizione» per DA-C1-07). Paragrafo di alias e chiusure di §2 corretto: elenco delle DA assorbite da DX-09 completo (9 su 9).
- **DA-CV-01..23:** tutte presenti con stato Decisa. Valori aperti (DA-CV-01 `_min` `_max`, DA-CV-08, `incident.initial_assessment_max_hours`, ecc.) sono in §4.
- **§5:** tutte le classi presenti con durate (90 giorni, 90 giorni, 12 mesi, 12 mesi, 30 giorni, 30 giorni, caso + 12 mesi, durata del servizio, 12 mesi, fine contratto).
- **§4:** tutti i punti ancora aperti dell'originale, tranne R2. Le righe aperte presenti nel candidato: marketing, ambito NIS2, Data Act, AI Act, log, DPF, EDPB, valori aperti, E1, cancellazione con versione non leggibile, catalogo, legal hold, rate limit B2, metrica gate E3, registro norme, marketing nel catalogo, incidenti ricorrenti, nomi retention, TTL token, CSIRT, E14, marcatura testo.
- **Archivio:** 337 righe = originale integrale (329) più intestazione (8); righe 126, 306, 307, 337 verificate identiche all'originale. Intestazioni abbassate di un livello.

## Esito e correzioni richieste prima della sostituzione
1. R1 e R2 (bloccanti): reintegrare la decisione sulle mutazioni A1 e il punto G1 (a).
2. R3-R7: reintegrare le clausole di sostanza (tcp_user_timeout, regola BYPASSRLS, `incident.*` non leggibili, tenant di contesto, DA-E1-13, DX-22).
3. R8-R12: facoltative; aggiornare le citazioni in E1 e A1 dopo la sostituzione.
