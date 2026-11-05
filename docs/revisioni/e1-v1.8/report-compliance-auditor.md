# Report compliance-auditor — E1 v1.8 e catalogo delle variabili v1.6

Oggetto: `docs/E1-tracing-distribuito.md` v1.8 e `docs/catalogo-variabili.md` v1.6 (branch `claude/docs-ondata-1`), differenze `git diff 0cf35f6..HEAD`. Task: `docs/revisioni/e1-v1.8/task-auditor.md`. Sola lettura. Norme dal registro v1.7: GDPR artt. 5, 25, 32 e considerando 26 ✔; Reg. 2024/2690 allegato 3.2 ✔; AI Act art. 50 ✔. Nessuna norma da aggiungere al registro.

Per i confronti con il codice ho riletto nel worktree `/workspace/wt-impl-e1` (branch `claude/impl-e1`, sola lettura): `migrations/versions/0006_giro4_fixes.py`, `scripts/test-non-superuser.sh`, `tracing.py` (init, `_safe_emit`, worker dei segnali), il report dell'implementer (sezione «Giro 4»). Ho inoltre eseguito una prova di connessione con `psycopg.connect` verso un indirizzo che scarta i pacchetti (nessun file scritto, nessun database toccato) per verificare l'effetto di `connect_timeout` (V-01).

**Esito: RIPORTA.** Dei miei rilievi sulla v1.7 (D-01..D-08) sei sono chiusi e due sono chiusi solo in parte; il testo dichiara quasi tutti i limiti residui in modo corretto. Nessuna violazione di decisioni o PV, e il documento non presenta come risolto ciò che è aperto in modo grave. Restano tre rilievi da riportare e quattro minori.

## 1. Stato dei rilievi della v1.7 (`docs/revisioni/e1-v1.7/report-compliance-auditor.md`)

| Rilievo | Stato | Dove / nota |
|---|---|---|
| D-01 segnali non bloccanti e C2 | CHIUSO, con residui V-04 | E1 §5: coda e thread propri dei segnali; deroga C2 solo per l'ondata 1 (DECISIONS §6); catalogo §18 e E1 §4.1, §7, §3 coerenti; criterio 5 esteso ai segnali con prova su proxy congelabile (esiste nel codice, `tests/test_giro4_misc.py`). |
| D-02 ruolo di migrazione e `BYPASSRLS` | PARZIALE, vedi V-02 | E1 §5 «Ruoli di deploy» e App. B ora dichiarano il requisito di revoca; la formulazione lascia intendere che la revoca chiuda l'accesso, ma non è così. |
| D-03 tabella dei segnali con RLS | CHIUSO | E1 §5: solo inserimento, `WITH CHECK` sul tenant, lettura permissiva «da definire con A5»; prova dello script con ruolo non superuser dichiarata in App. B. Nota in V-02. |
| D-04 variabili `e1.write_*` e regola 11 | PARZIALE, vedi V-01 e V-05 | Regola 11 ora le elenca (catalogo §1 punto 11); valore di sviluppo di `e1.write_tcp_user_timeout_ms` presente (5000); tolti i riferimenti ai «giri». Resta un'affermazione sul timeout di connessione non corretta. |
| D-05 criterio 4 e limiti | CHIUSO | Criterio 4 con il limite sugli identificativi generici; nome della chiave solo se nota; whitelist applicata dall'helper dichiarata in App. B. |
| D-06 `API_ENV` | CHIUSO | `e5.environment_invalid` e limite in App. B; criterio 17. |
| D-07 contatori e coda alla chiusura | CHIUSO, con residuo V-04 | App. B: segmenti in coda contati e segnalati solo se `close()` è chiamato. |
| D-08 chiave minima nel catalogo | CHIUSO, con incoerenza V-06 | Catalogo §18 ora cita i 32 byte provvisori. |

## 2. Rilievi

### V-01 DA RIPORTARE — «Passato al driver senza arrotondamento»: un `e1.write_connect_timeout_ms` sotto 1000 ms disattiva il timeout di connessione (DX-22, PV-01; E1 §5; catalogo §9) — verificato con una prova
- Catalogo §9, riga `e1.write_connect_timeout_ms`: «il valore è passato al driver senza arrotondamento»; il codice passa `ms/1000` come numero decimale a `psycopg.connect(connect_timeout=...)` (`tracing.py`, nel ramo della connessione propria).
- Prova eseguita in questa sessione contro un indirizzo che scarta i pacchetti: `connect_timeout=0.4` non è onorato (la connessione resta in attesa per oltre 20 secondi; una prova precedente senza limite di tempo ha atteso 130 s, cioè il tempo del kernel); 1.0 e 1.5 diventano 2 s (minimo di libpq); 2.5 diventa 2 s (parte intera); 2 e 2.0 danno 2 s. La validazione della variabile ammette ogni intero ≥ 1.
- Effetto: la frase del catalogo è vera solo alla lettera, ma con i valori 1-999 ms il timeout di connessione non esiste, e per gli altri valori è troncato o portato a 2 s. E1 §5 e §11 presentano `e1.write_connect_timeout_ms` come uno dei limiti che impediscono al thread di scrittura di restare appeso. Questo è in contrasto con la soluzione dichiarata per il rilievo N11 («nessun arrotondamento»), che rimuove un arrotondamento visibile e lascia uno nascosto del driver.
- Proposta: nel catalogo e in E1 dichiarare l'unità effettiva (secondi interi, minimo 2) e la conseguenza per i valori più piccoli; scegliere se la variabile è in millisecondi con validazione (multiplo di 1000 e ≥ 2000) oppure è rinominata in secondi; il minimo «validità tecnica ≥ 1» non è coerente con questo comportamento. Il catalogo deve spiegarlo nella regola 11 (intervallo minimo-massimo richiesto).

### V-02 DA RIPORTARE — «Il ruolo di migrazione non ha accesso ai dati a runtime»: la revoca di `BYPASSRLS` non basta, e la RLS dipende da un parametro impostato dal chiamante (isolamento tra tenant, DX-18/DX-19; E1 §5, App. B) — dedotto dal codice e dal disegno
- E1 §5, «Ruoli di deploy»: «il ruolo di migrazione non ha accesso ai dati a runtime … entrambe le concessioni vanno revocate subito dopo la migrazione»; App. B: «Se l'appartenenza al proprietario con `BYPASSRLS` non è revocata dopo la migrazione, il ruolo di migrazione può leggere le tracce di ogni tenant».
- Le due tabelle sono create dal ruolo di migrazione, che ne è quindi il proprietario con tutti i privilegi. La policy è `USING (tenant_id = current_setting('app.tenant_id'))`, e `app.tenant_id` è un parametro che la sessione imposta da sola. Un ruolo con privilegi sulle tabelle (il proprietario, e qualunque ruolo membro del writer) legge i dati di un tenant qualsiasi impostando quel parametro, anche senza `BYPASSRLS` e dopo la revoca. Quindi la revoca chiude solo il percorso più diretto; «non ha accesso ai dati» è una regola di deploy (quel ruolo non va usato a runtime), non una garanzia del database. Lo stesso vale per il `WITH CHECK` della tabella dei segnali: `PostgresSignalSink.emit` imposta il parametro dal `tenant_id` del segnale e poi inserisce con lo stesso valore, quindi il controllo protegge da un INSERT diretto del writer, non da un errore del chiamante.
- Non è un difetto nuovo né un obbligo normativo, ma ciò che il documento dichiara può far credere a un lettore che l'isolamento valga a prescindere da come il ruolo è usato.
- Proposta: in App. B scrivere che l'isolamento in lettura e scrittura tra tenant presuppone che solo l'helper imposti `app.tenant_id` e che i ruoli con privilegi sulle tabelle (proprietario e writer) non siano usati da altro codice; scrivere «il ruolo di migrazione non deve essere usato a runtime» come requisito di deploy invece di «non ha accesso».

### V-03 DA RIPORTARE — La deroga a C2 e il solo controllo di formato valgono «solo nell'ondata 1 con dati sintetici», ma il piano non contiene la condizione di uscita (PV-01; GDPR art. 5(1)(c), art. 25, art. 32; DX-10 C2; E1 §9, App. B, App. C) — verificato
- DA-E1-13 e la deroga a C2 sono decise come temporanee perché l'ondata 1 usa soli dati sintetici (E1 §5, §4.2, DECISIONS §6). Nel documento il solo riferimento ad attuarle è «non ancora attuata» in §4.2, App. B e App. C. §9 (piano) non è stato modificato nel resto: nessun passo o verifica richiede, prima dell'ondata 2 o prima che dati reali di un'agenzia entrino nelle tracce, che (a) gli elenchi chiusi e gli UUID di DA-E1-13 siano attuati, (b) i segnali durevoli di A5 sostituiscano la tabella provvisoria e (c) la procedura di deploy (revoche, ruoli) sia approvata. Il passo 4 (segmenti LLM e tool) è il primo che riceve dati dagli altri documenti.
- Senza questa condizione scritta le due deroghe possono diventare permanenti per omissione: gli identificativi generici accettano nomi con prefisso (dati personali, considerando 26) e i segnali di incidente possono restare solo nel log locale (decorrenza dei termini ricostruibile solo se conservati, DX-10).
- Proposta: aggiungere in §9, come condizione dei passi 4-6 e dell'attivazione per un'agenzia reale: «dati reali di un'agenzia solo dopo l'attuazione di DA-E1-13, i segnali durevoli di A5 e la procedura di deploy approvata», e nell'App. C una riga di responsabilità per DA-E1-13 (chi redige gli elenchi: B1, B2, E16).

## 3. Rilievi minori

### V-04 MINORE — Qualche affermazione sui segnali va più in là del codice (E1 §5; App. B) — verificato
- «Il chiamante non attende mai l'invio di un segnale, nemmeno con il database bloccato»: vero per le emissioni accodate, ma all'avvio l'helper emette in modo sincrono (`_emit_at_startup`, senza timeout) i segnali di tenant di contesto assente, e il registro delle variabili emette in modo sincrono i segnali `e5.*`; con un database bloccato all'avvio l'avvio si ferma. Non è un problema per un avvio che deve comunque fallire, ma il testo dice «mai».
- «La connessione del sink è soggetta allo stesso guardiano per job»: il codice lo fa solo se il sink espone una connessione `psycopg` (`PostgresSignalSink`, per riconoscimento tramite attributo); un altro sink di A5 non ne beneficia. Il testo lo presenta come regola generale.
- `close()`: «conta e segnala i segmenti rimasti in coda»: la segnalazione avviene solo nel log locale di ripiego, non verso la tabella dei segnali (i thread sono già fermi). Con la deroga a C2 è accettabile, ma «segnala ad A5» non è.
- Proposta: tre correzioni di formulazione («di norma», «per il sink di PostgreSQL», «nel log locale»).

### V-05 MINORE — Catalogo ed E1 non descrivono allo stesso modo `e1.write_tcp_user_timeout_ms` (coerenza E1-catalogo; catalogo §1 regola 8) — verificato
- E1 §5: è sia il parametro `tcp_user_timeout` della connessione sia la durata massima applicativa di un job (un guardiano interrompe il job che la supera). Catalogo §9: «tempo massimo lato client per dati non confermati su una connessione già aperta», senza la durata del job. Manca anche una regola relazionale: un valore di `e1.write_tcp_user_timeout_ms` minore di `e1.write_statement_timeout_ms` interrompe il job prima del timeout lato server e lo fa fallire (valori di sviluppo: 5000 ms contro 2000 ms, coerenti, ma la regola non è nel catalogo, a differenza di 8(a)-(d)).
- Proposta: completare la riga del catalogo e aggiungere la regola relazionale «`e1.write_tcp_user_timeout_ms` non inferiore a `e1.write_statement_timeout_ms`».

### V-06 MINORE — App. B ed E1 §5 contraddicono il catalogo §18 sulla chiave minima e sui formati (coerenza E1-catalogo) — verificato
- App. B: «La lunghezza minima di 32 byte è provvisoria fino ad A6 ed è nel codice, non nel catalogo» e «I formati numerici … non sono nel catalogo §16-§18 con una riga propria». Il catalogo v1.6 §18 ora cita i formati della whitelist e i 32 byte come invarianti provvisorie, nella riga delle invarianti di E1, non in righe separate.
- Proposta: dire «è nel catalogo §18 come invariante provvisoria (riga unica delle invarianti di E1) ed è nel codice»; resta da decidere con A6 se invariante o variabile.

### V-07 MINORE — Il testo della migrazione 0006 non concorda con lo script e con il report (codice, non documento; punto 3 del task) — verificato
- `0006_giro4_fixes.py`, docstring: «Rimosso anche il `GRANT CREATE ON SCHEMA public TO gravya_e1_so_owner` … non serve». Lo script `scripts/test-non-superuser.sh` concede quel `CREATE` (riga 94) e lo revoca (riga 126) e il report dell'implementer spiega che PostgreSQL lo richiede al nuovo proprietario per `ALTER FUNCTION … OWNER TO`. E1 v1.8 §5 segue il report (corretto): «PostgreSQL lo richiede al nuovo proprietario … entrambe le concessioni vanno revocate subito dopo la migrazione».
- Sulla revoca best-effort: E1 dichiara correttamente che la migrazione «tenta la revoca dell'appartenenza» e che il `CREATE` non è revocato dalla migrazione; la revoca reale è nello script di deploy, e App. B dichiara la procedura come proposta non approvata. Nessuna presentazione eccessiva.
- Proposta: correggere il docstring della migrazione (fuori da questo incarico, nel codice).

## 4. Punti 2-4 del task
- **Coerenza E1-catalogo:** timeout lato server (`e1.write_statement_timeout_ms`) e lato client (`e1.write_connect_timeout_ms`, `e1.write_tcp_user_timeout_ms`, keepalive) coerenti nei nomi e nella classificazione «da definire»; regola 11 ora include `e1.write_buffer_size` e le `e1.write_*` (catalogo §1 punto 11, con la motivazione PV-01); deroga a C2 nella riga di §18 in accordo con E1 §5 e DECISIONS §6; riferimenti ai «giri» tolti; incoerenze residue in V-01, V-05, V-06.
- **Cosa E1 presenta come garantito:** la revoca nella 0006 è dichiarata best-effort e reale nello script (corretto); il resto è coerente con il codice, salvo V-01 (connessione), V-02 (isolamento) e V-04.
- **Storico di E1:** righe 1.0-1.7 intatte (nessuna riga rimossa o modificata), una sola riga nuova (1.8): verificato sul diff.

## 5. Controllato e senza rilievi
- Limiti dichiarati correttamente: identificativi generici e dati personali con DA-E1-13 (a) cataloghi, (b) UUID, (c) solo formato accettabile solo in ondata 1; criterio 4 e 16; whitelist applicata dall'helper; funzione cross-tenant con l'oracolo di esistenza; contatori in memoria; tabella provvisoria dei segnali; tenant di contesto obbligatorio solo con `API_ENV=production` reale e `e5.environment_invalid` per i valori fuori dall'insieme; `router` non accettato.
- «Vocabolario chiuso» tolto dove c'è solo il formato (§4.2, §4.3, §11); esiti (stati, `outcome`, `exec_result`, `gravya.tool.outcome`) correttamente descritti come insiemi chiusi.
- Avvio senza configurazione valida: servizio non parte (installazione fallisce) e segnale, non applicabile il fail-open (§5, §6, criterio 17); coerente con la decisione del 2026-11-05.
- NIS2 come progetto: §7 aggiornato con la deroga; nessuna affermazione di obbligo nuova. AI Act e PV-02 invariati. DX-22: variabili «da definire», valori di sviluppo ammessi solo fuori produzione, catalogo come punto di verità.

## Letture
`docs/E1-tracing-distribuito.md`: diff `0cf35f6..HEAD` per intero (§3, §4.1-§4.3, §5, §6, §7, §8 criteri 4, 5, 9, 17, §9, §11, App. B, App. C, storico); `docs/catalogo-variabili.md`: diff per intero e §9, §1 punto 11, §18; `docs/DECISIONS.md`: solo grep delle righe DA-E1-13, «Segnali e C2», «Tenant di contesto», «Da riportare. Revisione di E1 v1.7»; `docs/revisioni/e1-v1.7/report-compliance-auditor.md` (mio); worktree dell'implementazione: `0006_giro4_fixes.py`, `scripts/test-non-superuser.sh` (righe 90-130), `tracing.py` (init, segnali, righe 360-480, 640-700), report dell'implementer «Giro 4». Un tentativo di rendere il diff in un file temporaneo mi ha fatto scrivere `/tmp/x.diff`: l'ho cancellato subito.
