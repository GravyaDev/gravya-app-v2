# Report compliance-auditor — verifica finale di E1 v1.9 e catalogo v1.7

Oggetto: `docs/E1-tracing-distribuito.md` v1.9 e `docs/catalogo-variabili.md` v1.7 (branch `claude/docs-ondata-1`), differenze `git diff f11e560..HEAD`. Task: `docs/revisioni/e1-v1.9/task-auditor.md`. Sola lettura. Norme dal registro v1.7: GDPR artt. 5, 25, 32 e considerando 26 ✔; Reg. 2024/2690 ✔. Nessuna norma da aggiungere al registro.

Codice letto in sola lettura nel worktree `/workspace/wt-impl-e1` (branch `claude/impl-e1`, il cui HEAD è `bd83852`, con il codice del giro 5 a `41607af`): `tracing.py` (init, segnali, connessioni), `signals.py`, `config/env.py`, `config/e5-snapshot.json`, report dell'implementer «Giro 5», `report-code-reviewer-giro4.md`. Il report del code-reviewer sul giro 5 non esiste ancora: non l'ho letto.

**Esito: RIPORTA, nessun bloccante e nessun rilievo grave.** I tre rilievi da riportare e i minori della v1.8 sono chiusi nel testo. E1 v1.9 descrive quasi tutto ciò che ho potuto confrontare con il codice del giro 5 in modo corretto. Restano cinque punti minori, di formulazione o di residuo dichiarato in modo incompleto.

## 1. Rilievi della v1.8 (`docs/revisioni/e1-v1.8/report-compliance-auditor.md`)

| Rilievo | Stato | Dove |
|---|---|---|
| V-01 timeout di connessione sotto 1 s disattivato | CHIUSO | `e1.write_connect_timeout_s` in secondi interi, minimo 2 (catalogo §9: «libpq legge secondi interi e tratta i valori inferiori a 2 come 2, e 0 come attesa infinita»; E1 §5, §6, §11). Codice: valore passato intero senza conversione (`_write_connect_timeout_s`), minimo 2 dichiarato nel campo `min` dell'istantanea, tecnico ≥ 1 per la validazione. |
| V-02 «non ha accesso ai dati» e RLS | CHIUSO | E1 §5 «Isolamento e ruoli»: l'isolamento presuppone che solo l'helper imposti `app.tenant_id` e che i ruoli con privilegi sulle tabelle non siano usati da altro codice; i requisiti di installazione sono «non garanzie del database»; revoca obbligatoria del superuser dopo le migrazioni. Residuo di formulazione: F-4. |
| V-03 condizione di uscita dall'ondata 1 | CHIUSO | §9: «Condizione prima dei dati reali» (DA-E1-13, segnali durevoli di A5, procedura di installazione approvata) per i passi 4, 5 e 6; §3 (B1, B2, E16, A5), §12, App. C (chi redige gli elenchi) e DECISIONS §6 «E1: condizione prima dei dati reali», coerenti. |
| V-04 formulazioni sui segnali | CHIUSO | «Di norma» non bloccanti, eccezione dei segnali sincroni all'avvio, limiti validi solo per il sink PostgreSQL con connessione propria, `close()` nel solo log locale (E1 §5, App. B). Corrisponde al codice (`isinstance(self._signals, PostgresSignalSink)`, `_emit_at_startup`). |
| V-05 `e1.write_tcp_user_timeout_ms` e regola relazionale | CHIUSO, con residuo F-2 | Doppio uso descritto in E1 e catalogo; regola «non inferiore a `e1.write_statement_timeout_ms`». |
| V-06 chiave 32 byte e formati | CHIUSO | E1 App. B e catalogo §18 concordano (invariante provvisoria, riga unica delle invarianti di E1, nessuna variabile). |
| V-07 docstring della migrazione 0006 | CHIUSO nel codice | Il report dell'implementer (correzione 7) lo dichiara corretto; E1 §5 già descriveva il `CREATE` su `public` e la revoca obbligatoria. Non riletto il docstring nel dettaglio. |

Del code-reviewer (giro 4) il testo chiude o dichiara: `close()` e connessione propria dei segnali (§5, App. B), campo `kind` del segnale (E1 §5: «se è un valore del vocabolario dei `kind`, altrimenti un segnaposto»), `API_ENV` bloccante, README, DX-22 su `e1.write_tcp_user_timeout_ms`. Aperti nel testo come limiti, correttamente: sink di altro tipo senza guardiano, segnali all'avvio sincroni, contatori in memoria, ruolo di migrazione, tabella dei segnali provvisoria con lettura permissiva.

## 2. Rilievi minori

### F-1 — «Stato dell'implementazione» è invecchiato e può ora essere aggiornato (E1 App. B) — verificato
Il paragrafo dice che i punti nuovi sono «comportamento atteso e non verificato sul codice». Ho confrontato con il codice del giro 5: `e1.write_connect_timeout_s` letto e passato intero (`tracing.py` riga ~774, istantanea con `min` 2); `API_ENV` fuori dall'insieme chiuso solleva `EnvironmentInvalidError` dopo il segnale `e5.environment_invalid`; il thread dei segnali ha una connessione propria con `connect_timeout`, `statement_timeout`, `tcp_user_timeout`, keepalive e guardiano, riconnessione dopo un errore e `rollback` in `PostgresSignalSink.emit`; `safe_signal_kind` sostituisce il `kind` con un segnaposto; la regola `e1.write_tcp_user_timeout_ms` ≥ `e1.write_statement_timeout_ms` blocca l'avvio con segnale. Non c'è nulla dichiarato come implementato che il codice non faccia: l'avvertenza è solo più prudente del necessario. Proposta: sostituire l'elenco «non verificato» con «verificato sul codice a `41607af` (lettura, non esecuzione dei test)» e indicare la sola eccezione di F-2.

### F-2 — Regola relazionale e guardia `API_ENV`: dove sono davvero imposte (E1 §5, §6; catalogo §9, §18) — verificato
- La regola `e1.write_tcp_user_timeout_ms` ≥ `e1.write_statement_timeout_ms` è imposta soltanto nel costruttore dell'helper, all'avvio; non nel registro delle variabili, e non è elencata tra le regole relazionali del catalogo §1 (regola 8(a)-(d)): è scritta solo nella riga di §9. E1 §5 e catalogo dicono «valore non valido, con segnale». Quando A6 permetterà di modificare il valore senza riavvio (DX-13), la regola va validata alla modifica, e non solo all'avvio; il testo non lo dice.
- Il blocco per `API_ENV` fuori dall'insieme chiuso scatta solo se l'helper è costruito senza `production_override` (`if self._production_override is None`); con l'override il controllo è saltato. E1 §5, il criterio 17 e il catalogo §18 lo presentano senza questa condizione. È una scelta voluta per le prove dei revisori; in produzione l'override non deve essere usato (può solo irrigidire).
- Proposta: aggiungere la regola come 8(e) del catalogo, con «validata anche alla modifica (A6)»; nel criterio 17 e in §5 precisare «senza `production_override`».

### F-3 — Residuo del guardiano per job non dichiarato (E1 §5, §11) — verificato nel report del code-reviewer
Il code-reviewer (giro 4) osserva che, se il guardiano scatta mentre il job sta per finire, interrompe una connessione sana: una perdita contata e una riconnessione. E1 dice solo che «un job interrotto è trattato come una scrittura fallita». Non è un obbligo, ma è un limite del fail-open. Proposta: una frase in App. B.

### F-4 — Frase sul `WITH CHECK` dei segnali ancora ottimista (E1 §5 «Segnali ad A5») — verificato sul codice
«Un segnale non può essere scritto a nome di un tenant diverso da quello della sessione»: `PostgresSignalSink.emit` imposta `app.tenant_id` dal `tenant_id` del segnale e poi inserisce con lo stesso valore, quindi il controllo vale contro un INSERT diretto del writer e non contro un errore del chiamante. Il nuovo paragrafo «Isolamento e ruoli» lo copre in generale; la frase di §5 non lo ricorda. Proposta: «… da un INSERT diretto; il sink imposta il tenant della sessione dal segnale».

### F-5 — Il catalogo non ricorda dove vale il minimo 2 (catalogo §9) — dedotto
`e1.write_connect_timeout_s` ha «intero ≥ 2» nel catalogo; il codice applica il minimo 2 solo tramite il campo `min` della voce di istantanea (il minimo tecnico invariante del codice è 1: un valore 1 sarebbe accettato dal codice e portato a 2 s da libpq, senza danno). Con il registro di A6 il minimo dovrà viaggiare con la variabile. Proposta: annotarlo in §9 (nessuna conseguenza di conformità immediata).

## 3. Punti 2, 3 e 4 del task

- **Coerenza E1 – DECISIONS correnti – catalogo:** DA-E1-13 (DECISIONS §2) e le righe di §6 su E1 (identificativi e chiavi; scrittura e parametri; ambiente e avvio; condizione prima dei dati reali) coincidono con E1 v1.9 (§4.2, §5, §6, §9, App. B e App. C) e con il catalogo (§1 punto 11, §9, §18). `e1.write_connect_timeout_s`: secondi con minimo 2 (catalogo e E1); regola tcp/statement presente in entrambi (con il limite F-2); guardia `API_ENV` a insieme chiuso e deroga a C2 in §18 coerenti con E1 §5 e §7. Nessun riferimento residuo a `e1.write_connect_timeout_ms` fuori dai testi storici (storico, DECISIONS archivio). Nessun riferimento ai «giri» nei due documenti.
- **Implementato o no:** vedi F-1: nulla è dichiarato come implementato senza esserlo. Le due precisazioni mancanti sono in F-2.
- **Storico di E1:** righe 1.0-1.8 intatte (0 righe rimosse o modificate nel diff) e una sola riga nuova (1.9).

## 4. Controllato e senza rilievi
- Condizione prima dei dati reali (§9): vale per i passi 4, 5 e 6, richiama (a) DA-E1-13, (b) segnali durevoli di A5 (fine della deroga a C2), (c) procedura di installazione approvata; coerente con la decisione e con le deroghe.
- Limiti sui dati personali: identificativi generici come solo formato, `execution_ticket_id`, `workflow_id`, `gen_ai.agent.id` ancora «prefisso_corpo» finché B1, B2 e C1 non emettono UUID; criterio 4 con il limite; nome della chiave solo se nota; `kind` del segnale con segnaposto.
- NIS2 come progetto: deroga a C2 temporanea e chiara in §3, §4.1, §5, §7, catalogo regola 4 e §18; conservazione garantita requisito di A5.
- DX-22: variabili «da definire», valori di sviluppo dichiarati, bloccate in produzione; regola 11 del catalogo include `e1.write_buffer_size` e le `e1.write_*`.
- Dati sintetici, PV-02, AI Act: nessuna differenza.

## Letture
`docs/E1-tracing-distribuito.md`: diff `f11e560..HEAD` per intero, App. C (DA-E1-13) e storico; `docs/catalogo-variabili.md`: diff per intero e §9, §18; `docs/DECISIONS.md`: grep delle righe DA-E1-13 e §6 di E1 (righe 98, 208-214); `docs/revisioni/e1-v1.8/report-compliance-auditor.md` (mio); `docs/revisioni/e1-v1.9/task-auditor.md`; worktree del codice: `tracing.py` (righe 405-560, 640-660, 770-815), `signals.py` (righe 75-140), `config/env.py` (righe 30-45), `config/e5-snapshot.json` (voce `e1.write_connect_timeout_s`), `report-implementer.md` «Giro 5» per intero, `report-code-reviewer-giro4.md` righe 1-80.
