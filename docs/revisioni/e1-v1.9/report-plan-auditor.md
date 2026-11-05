# Report plan-auditor: E1 v1.9 e catalogo v1.7 (verifica finale)

Esito: **RIPORTA**. Nessuna violazione di un PV e nessuna contraddizione netta con una riga decisa. I rilievi della v1.8 sono quasi tutti chiusi. Restano 3 punti da riportare (decisioni non registrate attribuite come decise) e 4 minori.

## Letture
- docs/E1-tracing-distribuito.md v1.9: 1-296 di 296, per intero.
- docs/revisioni/e1-v1.9/task-auditor.md: 1-15 di 15.
- docs/revisioni/e1-v1.8/report-compliance-auditor.md: 1-79 di 79. Il mio report v1.8 (righe 1-12 riviste) l'ho presente dalla sessione precedente.
- docs/revisioni/impl-e1/report-code-reviewer-giro4.md (branch del codice): 1-33 di 33.
- report dell'implementer (branch del codice), sezione «Giro 5»: righe 955-1040.
- docs/catalogo-variabili.md v1.7: 1-4, 16-20, 25, 164-165, 365, 446-451, 501-502, più grep su `e1.write_`, `32 byte`, `API_ENV`, `DX-07`. Non letti §2-§8 e §10-§15 e §19: **lettura parziale**.
- docs/DECISIONS.md (ristrutturato): solo grep delle righe `Mutazioni del grafo A1`, `API_ENV assente`, `E1: ambiente e avvio`, `write_tcp_user_timeout`; letti §4 r.152-153 e §6 r.185 nel candidato (stesso contenuto). **Lettura parziale.**
- Codice (branch `claude/impl-e1`, sola lettura): grep su `tracing.py`, `whitelist.py`, `config/variables.py`; `config/e5-snapshot.json` (grep con contesto); `migrations/versions/0006_giro4_fixes.py` (grep). Il commit corrente del worktree non l'ho verificato (task: `41607af`). Non ho eseguito i test.
- `git diff` non eseguibile (nessuno strumento shell): confronto con v1.8 sul testo letto e sul report della v1.8.

## 1. Rilievi della v1.8: stato

### Chiusi
- **PA N1 (E1 e catalogo sulla chiave minima e sui formati):** E1 App. B r.246 e r.256 coincidono con il catalogo §18 r.451 (invarianti provvisorie, riga unica; nessuna riga in §16). Chiuso.
- **PA N2 (`API_ENV` fuori insieme):** blocca l'avvio (E1 §5, §6, criterio 17, App. B; catalogo §18 r.446; DECISIONS §6 «E1: ambiente e avvio»); nel codice `EnvironmentInvalidError` dopo il segnale (`tracing.py` r.457). Chiuso. Resta il caso `API_ENV` assente (F1).
- **PA N3 (catalogo §18 senza E1):** ora cita E1 e il tenant di contesto (r.446). Chiuso.
- **PA N4 (residui del catalogo):** DX-07 decisa (r.29, §17.1 punto 1); regola 6 «questa versione: v1.6»; riferimenti al branch tolti; regola 4 richiama la deroga a C2. Chiuso.
- **PA N5, docstring di 0006:** corretto (il docstring dice ora che `CREATE` su `public` serve, verificato con grep). `e1.write_tcp_user_timeout_ms` è in `_EXPECTED_INT_VARIABLES` (`variables.py` r.77); `connect_timeout` ora in secondi interi (nome `_s`; `tracing.py` r.416, r.806, valore passato senza conversione). Chiuso.
- **PA N6 (dipendenza DA-E1-13; due nomi della tabella):** E1 §3 r.30, §12 e App. C. §2 dice che la tabella provvisoria dei segnali fa da tabella di audit minima per E1. Chiuso.
- **CA V-01 (`connect_timeout`):** variabile `e1.write_connect_timeout_s`, minimo 2 (`config/e5-snapshot.json`: `min: 2`), spiegazione libpq in E1 §5 e App. B. Chiuso con una precisazione (F5).
- **CA V-02 (isolamento e ruolo di migrazione):** E1 §5 «Isolamento e ruoli» e App. B «Isolamento e ruolo di migrazione» dicono ora che l'isolamento presuppone che solo l'helper imposti `app.tenant_id` e che i ruoli con privilegi non siano usati da altro codice; «requisiti di installazione» al posto di «non ha accesso». Chiuso.
- **CA V-03 (condizione di uscita):** E1 §9 «Condizione prima dei dati reali», coerente con DECISIONS §6 «E1: condizione prima dei dati reali»; §12 e App. C. Chiuso.
- **CA V-04, V-05, V-06, V-07:** «di norma», sink PostgreSQL, log locale; doppio uso di `tcp_user_timeout` nel catalogo e in E1; App. B allineata; docstring corretto. Chiusi.
- **CR giro 4:** rilievi 1-2 (`close()`): corretti nel codice, E1 §5 dichiara che i segmenti in coda sono contati solo nel log locale. Rilievo 3 (sink): connessione propria, riconnessione, rollback (E1 §5). Rilievo 4 e V2 (`connect_timeout`): variabile in secondi; V2 resta un fatto di libpq dichiarato in App. B. Rilievo 5 (`kind`): `safe_signal_kind` (`whitelist.py` r.349-352), E1 §5. V1 (`tcp_user_timeout`): tipo intero e regola relazionale in `tracing.py` r.436-440. README: corretto secondo il report dell'implementer (non letto da me).

### Aperti
- F1, F2, F3 (da riportare) e F4-F7 (minori), qui sotto.

## 2. Rilievi nuovi

### F1 (da_riportare, verificato). `API_ENV` assente: E1 e catalogo lo presentano come regola, DECISIONS lo dà come non deciso
- E1 §5: «la variabile non impostata è trattata come sviluppo, con il segnale `e5.environment_undeclared`». Catalogo §18 r.446: «assente vale sviluppo con segnale». App. B r.260: «`API_ENV` non impostata è trattata come sviluppo (con segnale): una guardia di deploy non impostata in produzione disattiva le garanzie legate alla produzione».
- DECISIONS §4 r.153 (punto aperto): «Oggi il codice di E1 e il catalogo §18 lo trattano come sviluppo, con segnale: comportamento non deciso dall'utente». La riga decisa («E1: ambiente e avvio») riguarda solo i valori fuori insieme e il tenant di contesto.
- Problema: il catalogo §18 (invariante) e E1 §5 scrivono come regola ciò che DECISIONS tiene aperto. App. B di E1 dichiara il limite di sicurezza ma non che la scelta non è deciso. Va scritto «provvisorio, non deciso» in §5 e nel catalogo, con rimando al punto aperto di DECISIONS §4.

### F2 (da_riportare, verificato). La regola `e1.write_tcp_user_timeout_ms` ≥ `e1.write_statement_timeout_ms` è attribuita a «decisioni del 2026-11-05» e non è una decisione registrata
- E1 §6 «Avvio senza configurazione valida»: «se `e1.write_tcp_user_timeout_ms` è inferiore a `e1.write_statement_timeout_ms` ... il servizio non si avvia e parte un segnale (decisioni del 2026-11-05)». E1 §5 e criterio 17 la riportano come requisito.
- DECISIONS §6 «E1: robustezza della scrittura e ruoli del database» cita `tcp_user_timeout` ma non la regola relazionale; nessuna altra riga la decide. La regola viene dal rilievo V-05 del compliance-auditor e dalla correzione dell'implementer (`tracing.py` r.436-440).
- Il catalogo la mette solo nella riga di `e1.write_tcp_user_timeout_ms`; la regola 8 elenca «quattro regole relazionali» (a)-(d) e non la include.
- Problema: una condizione di blocco dell'avvio presentata come decisione dell'utente. Va registrata (decisione o proposta da validare) e va aggiunta alla regola 8 del catalogo (o la regola 8 va riscritta senza il numero «quattro»).

### F3 (da_riportare, verificato). Chi redige gli elenchi di DA-E1-13: assegnazione del doc-writer, e DECISIONS non cita E16
- E1 §3 r.30, §12, App. B r.255, App. C r.281: «B1 (provider, modelli, agenti), B2 (tool e destinazioni) ed E16 (convenzioni e contratti); B1, B2 e C1 emettono come UUID gli identificativi generati da Gravya».
- DECISIONS §2 DA-E1-13 (dopo la ristrutturazione): «valori dai cataloghi esistenti per modelli, provider, strumenti e agenti (B1, B2) e UUID», senza E16, senza la ripartizione tra B1 e B2 e senza C1. L'unica traccia di E16 è nel testo di v1.6-v1.7 («con E16 o con i cataloghi»).
- Problema: l'assegnazione di responsabilità è una proposta del doc-writer scritta come parte di una decisione. Va marcata «proposta, da confermare con B1, B2 ed E16» o registrata.

### F4 (minore, verificato). Citazioni di DECISIONS obsolete dopo la ristrutturazione
- E1 §3 r.32: «A1 scrive il `trace_id` nell'audit delle mutazioni ... DECISIONS §4»: la decisione è ora in §6 («Mutazioni del grafo A1»). E1 §5 r.129: «DECISIONS §4, «Valori provvisori di E1 v1.6»»: il punto è ora «E1, valori provvisori» in §4.
- Va aggiornato nella prossima revisione (la stessa citazione è in A1 App. C r.251 e B1 §7).

### F5 (minore, verificato). «Minimo 2» di `e1.write_connect_timeout_s` e App. B sullo stato dell'implementazione
- E1 §5 e catalogo r.164 dicono «minimo 2». Nel codice il minimo tecnico generale è 1 (`variables.py`, validazione degli interi); il 2 viene dal campo `min` dell'istantanea (`config/e5-snapshot.json`), non dal codice (report dell'implementer: «minimo tecnico effettivo 2 tramite `min` nell'istantanea»). Con un registro senza `min` il valore 1 passerebbe (libpq lo porta a 2, quindi nessun danno). Va detto che il 2 è nell'intervallo della variabile, non nel codice.
- E1 App. B r.265 («Stato dell'implementazione») dichiara «non verificato sul codice» il comportamento del giro 5. Ho verificato per grep nel codice: `e1.write_connect_timeout_s` (`tracing.py` r.416, r.806), `EnvironmentInvalidError` (r.457), regola ≥ statement timeout (r.436-440), `safe_signal_kind` (`whitelist.py` r.349), `isinstance(self._signals, PostgresSignalSink)` (r.549), tcp nei tipi interi (`variables.py` r.77). Non ho eseguito i test né letto il README né verificato `close()` nel codice del giro 5. Aggiornare App. B dicendo che questi punti sono stati controllati per lettura del codice (non per esecuzione).

### F6 (minore, verificato). Regola 8 del catalogo e conteggio
- Catalogo §1 regola 8: «In più valgono quattro regole relazionali (a)-(d)»; la riga di `e1.write_tcp_user_timeout_ms` ne aggiunge una quinta fuori dall'elenco. E1 §5 parla di «regole relazionali di E1» (non nel catalogo). Allineare (collegato a F2).

### F7 (minore, dedotto). Il blocco dell'avvio per variabili del segnale non ha un criterio
- E1 §5 «Segnali non bloccanti»: i segnali emessi all'avvio sono sincroni e il servizio «deve comunque fallire o proseguire». Il criterio 17 verifica il segnale per le variabili «da definire» mancanti e per `API_ENV` fuori insieme, non per il caso `e1.write_tcp_user_timeout_ms` < statement (cfr. F2: nel testo il criterio 17 lo cita). Verificare che i test del giro 5 coprano i tre casi: il report dell'implementer dice di sì (`tests/test_giro5_misc.py`), non riverificato.

## 3. Coerenza E1-catalogo-DECISIONS (punto 2)
- `e1.write_connect_timeout_s` in secondi, minimo 2: E1 §5, §6, §11, criterio 17, catalogo r.164, DECISIONS §6 «E1: scrittura e parametri»: coerenti.
- Guardia `API_ENV` a insieme chiuso: E1, catalogo §18, DECISIONS §6 coerenti sul blocco dei valori fuori insieme; non coerenti su «assente» (F1).
- Deroga a C2: E1 §3, §4.1, §5, §7, §9; catalogo §18 r.442 e regola 4; DECISIONS §6 coerenti.
- Formati e chiave minima in §18: E1 App. B e catalogo r.451 coerenti; DECISIONS §6 «E1: identificativi e chiavi» coerente.
- DA-E1-13: testo coerente con DECISIONS tranne le aggiunte di F3.
- Condizione prima dei dati reali: E1 §9 estende la decisione a «nessuna agenzia reale attivata» e ai passi 4-6; coerente nello spirito, da segnalare come precisazione.

## 4. Storico (punto 4)
Righe 1.0-1.8 invariate nel contenuto (confrontate con il testo letto nelle revisioni precedenti, incluso 1.8); una sola riga nuova (1.9). Verificato per lettura, non per diff.

## 5. Controllato
- Template: sezioni 1-12, Appendici A-C e Storico in ordine; criteri 1-18 testabili (criterio 16 parziale, come da decisione); nessuna stima temporale (solo taglia M).
- Nessun OpenTelemetry come software, nessun servizio extra-UE o SaaS (PV-01, PV-02); retention per rimando a `retention.*`; variabili `e1.*` tutte nel catalogo con gli stessi nomi.
- Codice: i punti verificati sopra; nessuna affermazione di E1 sul giro 5 contraddetta dal codice letto.

## Domande per l'utente / registrazioni
1. F1: `API_ENV` assente in produzione: «trattata come sviluppo con segnale» o bloccare l'avvio? (punto aperto in DECISIONS §4)
2. F2: la regola `e1.write_tcp_user_timeout_ms` ≥ `e1.write_statement_timeout_ms` va registrata come decisione o proposta da validare.
3. F3: confermare con B1, B2 ed E16 la ripartizione degli elenchi di DA-E1-13.
