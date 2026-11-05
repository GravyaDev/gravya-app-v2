# Report plan-auditor 2: ristrutturazione di DECISIONS.md (candidato corretto)

Esito: **RIPORTA**. Le correzioni al candidato risolvono i due bloccanti e i punti da riportare del primo report. Restano 3 differenze minori e 2 aggiornamenti di citazioni da fare nei documenti. Nessuna decisione in vigore o aperta risulta persa.

## Letture
- docs/DECISIONS.md (originale): letto per intero nel primo giro (righe 1-329). Per questo giro ho riletto solo righe 295-299 e fatto grep mirati; il file ha ora 302 righe non vuote.
- docs/revisioni/decisions-ristrutturazione/DECISIONS-candidato.md (corretto): 1-244 di 244, per intero.
- docs/revisioni/decisions-ristrutturazione/decisioni-archivio-candidato.md: solo grep nel primo giro (306 righe non vuote = 302 dell'originale + 4 di intestazione); **non riletto riga per riga**. Verifica per campione.
- docs/revisioni/decisions-ristrutturazione/task-plan-auditor.md: 1-20 di 20 (primo giro).
- docs/agenti/README.md r.38: solo grep sulla regola RIPORTA/BLOCCA.
- docs/catalogo-variabili.md regola 8b: letto nel giro v1.8 (usa già il TTL effettivo).

## 1. Le mie correzioni: sono giuste?
- **R1 (mutazioni A1):** riga §6 r.185 «Mutazioni del grafo A1»: solo eventi di audit, tabella di audit poi A5, conservazione 12 mesi, collegamento con `trace_id`, non segmenti E1. Fedele all'originale. Giusta.
- **R2 (G1 (a)):** §4 r.152. Giusta, nella forma «resta da decidere».
- **R3 (quarto e terzo giro):** §6 r.211 riporta `tcp_user_timeout` da `e1.write_tcp_user_timeout_ms` «da definire», `close()` senza attese illimitate, segnali con coda e thread propri, ruolo di migrazione senza `BYPASSRLS` e migrazioni senza errori inghiottiti, funzione del `trace_id`, `production_override` solo irrigidisce. Giusta, con una differenza: vedi N1.
- **R4 (`incident.*` non leggibili):** DX-10 r.26 contiene la frase. Giusta.
- **R5 (tenant di contesto e `API_ENV`):** r.212 riporta «`production_override` da solo non lo attiva» e «fuori produzione è facoltativo, con segnale»; «assente vale sviluppo» è tolto e sta in §4 r.153 come punto aperto («non deciso dall'utente»). Giusta. La frase su cosa fanno oggi il codice e il catalogo §18 con `API_ENV` assente non l'ho riverificata (dedotto dal testo di E1 v1.8).
- **R6 (DA-E1-13):** campi ripristinati, E16 tolto, «(B1, B2)». Giusta.
- **R7 (DX-22, DX-19):** DX-22 ora ha «documenti di dettaglio citano solo il nome», responsabile A6, «valori mascherati, con data dell'ultima rotazione»; DX-19 ha «Invariante.». Giusta. La parola «Invariante.» in coda a DX-19 è ambigua (a cosa si riferisce), ma l'originale dice che sono invarianti sia il default aggregato sia il log; non è un errore di sostanza.
- **R8 (minori):** valori del Data Act (30 giorni, due mesi, sette mesi), metriche di H1, «meccanismo da definire in F6 e A5» per le evidenze, opzioni escluse di DA-CV-03 e DA-CV-09: presenti. Giusto.
- **R9 (TTL dei token, regola 8b):** il punto è tolto da §4. Il catalogo regola 8b usa già il TTL effettivo (D5), quindi la chiusura è corretta. Verificato nel giro v1.8.
- **R10 (regola «RIPORTA non blocca»):** è in docs/agenti/README.md r.38, quindi la perdita da DECISIONS non è un problema. Giusto.
- **R12 (struttura §6):** tabella unica. Giusto.

## 2. Verifica completa
- **DX-01..DX-22:** tutte presenti con stato corretto (DX-02 «Decisa in parte»; DX-03, DX-05, DX-06, DX-08 «Aperta»). Contenuti di DX-09, DX-10, DX-19, DX-22 verificati contro le precisazioni.
- **DA di §2 e §3:** tutte presenti come riga o alias; paragrafo di alias e chiusure di §2 corretto (9 assorbite da DX-09, alias DA-B1-09, DA-B2-08, DA-B2-10, DA-E1-09). Stati preservati (aperte, ipotesi di lavoro, decisa in parte, decisa con condizione).
- **DA-CV-01..23:** presenti con stato Decisa. Valori aperti in §4.
- **§5:** tutte le classi con durata (90 giorni, 12 mesi, 30 giorni, caso + 12 mesi, durata del servizio, fine contratto).
- **§4:** tutti i punti aperti dell'originale presenti, più G1 (a) e `API_ENV` assente. I punti omessi sono chiusi o superati (DA-CV-08 stato discordante e testi superati del catalogo v1.1 sono superati dal catalogo 1.2: chiusura implicita; basi giuridiche delle evidenze: chiusa).
- **Righe tolte (§4, §6) con valutazione:** invariata rispetto al primo report: giri di revisione di E1 conclusi, regole di processo della v1.5 e del catalogo 1.2, lotti 5 e 6 del registro, C14 senza Bash, processo per E1 v1.7: tutte passi di processo conclusi. Il rilievo V-02 e gli altri rilievi del giro v1.8 restano nei report puntati da §4 r.141.
- **Riferimenti:** §1 DX, §2 DA, §4, §5, §6, §7 mantenuti; §3 diventa «Escalation: nessuna» (nessun documento cita §3).
- **Archivio:** 306 righe non vuote = 302 dell'originale + 4: coerente con una copia integrale (verifica per campione).

## 3. Differenze minori residue
- **N1 (minore).** §6 r.211: «funzione di controllo del `trace_id` senza parametro del tenant (nessun oracolo con tenant arbitrario né blocco delle tracce altrui)». L'originale (terzo giro) dice «funzione di controllo del `trace_id` chiusa (niente oracolo né blocco delle tracce altrui)». E1 v1.8 App. B ammette un oracolo di esistenza residuo anche con il tenant letto dalla sessione. Il candidato riformula in modo più preciso, ma è una riformulazione del coordinator. Tenere il testo originale o dichiararlo come precisazione di E1.
- **N2 (minore).** Dal terzo e quarto giro cadono «solo inserimento sui segnali anche con ruolo non superuser» (r.207 dice «solo inserimento per il ruolo di scrittura») e «prova dei segnali e test con ruoli non superuser». Sono requisiti di verifica, non di prodotto; accettabile.
- **N3 (minore, dedotto).** §4 r.153 afferma che «il codice di E1 e il catalogo §18 lo trattano come sviluppo, con segnale»: è corretto per E1 v1.8; da riverificare con il catalogo v1.7.

## 4. Citazioni da aggiornare nei documenti (non nel registro)
- E1 §3 («DECISIONS §4», mutazioni A1) e A1 App. C r.251 → ora §6 («Mutazioni del grafo A1»).
- E1 §5 («DECISIONS §4, «Valori provvisori di E1 v1.6»») → §4 «E1, valori provvisori».
- B1 §7 («DECISIONS §4», base giuridica delle evidenze) → la base delle evidenze di incidente sta ora in §5.
- Il candidato rimanda a `decisioni-archivio.md`: il registrar deve usare questo nome per il file archivio.

## Esito
RIPORTA: sostituzione approvabile dopo N1 (scelta del testo) e con le citazioni del §4 da aggiornare nelle revisioni dei documenti.
