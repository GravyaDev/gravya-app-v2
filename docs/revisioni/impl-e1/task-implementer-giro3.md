# Task per l'implementer, giro 3: correzioni dopo il secondo BLOCCA del code-reviewer

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente: «ok» ai punti 1-5 del coordinator (giro 3; `run_id` UUID; chiave HMAC minima 32 byte provvisoria; `reviewer_ref` prefisso fisso più UUID provvisorio; campi dei segnali in un insieme chiuso unico per ora e `gravya.tool.outcome` confermato).

Stesso documento (E1 v1.6), perimetro (§9 passi 0, 2, 3), worktree `/workspace/wt-impl-e1`, branch `claude/impl-e1` (ora `7dfc08d`; fai `git pull --ff-only`). Valgono `task-implementer.md` e `task-implementer-giro2.md`, salvo quanto cambia qui.

Fonti: `report-code-reviewer-giro2.md` (prove in `code-reviewer-giro2/`, oggi 43 falliti su 47), `report-compliance-auditor-giro2.md`.

## Criterio di fine (vincolante)
1. Passano `code-reviewer/` (39) e `code-reviewer-giro2/` (47), con `--basetemp` dentro il worktree, cancellato alla fine.
2. Passa `tests/`, sia come oggi sia con **ruolo non superuser**: migrazioni eseguite da un ruolo proprietario `NOSUPERUSER NOBYPASSRLS` e applicazione connessa con un ruolo non superuser (vedi punto 9). Due esecuzioni documentate nel report, entrambe verdi, anche con `PGHOST=127.0.0.1`.
3. Suite completa eseguita 10 volte di fila: 10 su 10 verdi (riporta il comando e l'esito).
4. Report: sottosezione «Giro 3» in coda, rilievo per rilievo (codice del rilievo, cosa cambia, test che lo prova). Non riscrivere i giri precedenti. **Ogni affermazione sul comportamento deve avere un test che la dimostra**: nel giro 2 il report dichiarava un buffer asincrono che non esisteva.

## Modifiche ai file di prova del code-reviewer (autorizzate dal coordinator, solo queste)
- `code-reviewer/test_repro_rilievi.py::test_R10d` (e solo quel test): la decisione dell'utente «tabella dei segnali provvisoria, solo inserimento» prevale. Il test deve accettare come corretto un errore di privilegio (`InsufficientPrivilege`) sulla lettura della tabella dei segnali da parte del writer, oltre a «0 righe». Commit separato con messaggio esplicito, citato nel report.
- `conftest.py` di `code-reviewer/` e `code-reviewer-giro2/`: aggiungere alle fixture di istantanea le sole voci delle variabili nuove (punto 2), con stato e forma delle voci già presenti. Commit separato.
- Nient'altro in quei file.

## Correzioni (bloccanti del code-reviewer, giro 2)
1. **G1, G2: formati.** Tutte le espressioni regolari con `re.fullmatch` (nessun `$` con `re.match`). UUID: si accetta solo la forma canonica minuscola con trattini (36 caratteri) e si confronta la stringa ricevuta con `str(uuid.UUID(x))`; ogni altra forma è scartata. Hash: `[0-9a-f]{64}` con fullmatch.
2. **G4a, G4b, G5, G7, G14a, G19: scrittura asincrona vera (decisione dell'utente, DECISIONS §6).**
   - Coda limitata di dimensione `e1.write_buffer_size` (numero di segmenti); `start_*`/`end_*` validano, mettono in coda con inserimento non bloccante e tornano subito. Coda piena: perdita contata e segnalata, nessuna attesa.
   - Un thread di scrittura in background con la propria connessione. I parametri di connessione li riceve l'helper alla creazione (DSN o parametri espliciti, compresa la credenziale da variabile d'ambiente nei test); **mai** dalla connessione del chiamante.
   - Timeout lato client: `connect_timeout` da una nuova variabile `e1.write_connect_timeout_ms` (stato «da definire», valore di sviluppo dichiarato, bloccata in produzione come le altre) e `statement_timeout` da `e1.write_statement_timeout_ms`; in più keepalive TCP o timeout di socket così che una rete bloccata non appenda il thread di scrittura. Se i keepalive richiedono parametri numerici, anche quelli vanno nell'istantanea come variabili «da definire» con valore di sviluppo (DX-22: nessun numero fisso).
   - `flush(timeout)` e `close()` dell'helper (per i test e lo spegnimento); riconnessione dopo un errore.
   - Test: dopo `start_segment` la riga **non** è necessariamente già scritta; dopo `flush` sì; con partizione bloccata o rete bloccata il chiamante torna entro un tempo misurato, piccolo e indipendente dal timeout; con coda piena la perdita è contata.
3. **G16 (CA R-04): tenant di contesto.** `TracingHelper` riceve il `tenant_id` di contesto alla creazione (un helper per tenant, oppure un oggetto di contesto esplicito per chiamata: scegli uno dei due e dichiaralo). Un modello con `tenant_id` diverso dal contesto: in produzione scartato con segnale, fuori produzione errore. Il GUC del tenant si imposta dal contesto, non dal modello. Test sull'helper.
4. **G15, G15b (CA): segnali.** Il writer ha solo `INSERT` sulla tabella dei segnali (togli `SELECT`). Il sink scrive impostando il tenant del segnale nella transazione (o con un ruolo dedicato di solo inserimento e policy `INSERT` esplicita): deve funzionare con ruolo non superuser e RLS forzata. Test con ruolo non superuser.
5. **G8a, G8b, G8c (CA): controllo cross-tenant del `trace_id`.** La funzione non accetta un tenant arbitrario: usa il tenant del GUC corrente (nessun parametro `p_tenant_id`). `start_trace` controlla anche lui che il `trace_id` non esista già per un altro tenant. Proprietario della funzione: un ruolo dedicato `NOLOGIN` con `BYPASSRLS` creato dalla migrazione e assegnato con `ALTER FUNCTION ... OWNER TO`; `SET search_path = pg_catalog, public, pg_temp` (pg_temp ultimo). Test con migrazioni eseguite da un proprietario non superuser. Se assegnare `BYPASSRLS` richiede un superuser alla migrazione, dichiaralo nel report come requisito di deploy.

## Rilievi da riportare e minori (stesse soluzioni del giro 2 dove non indicato)
- **`production_override` (G9, CA):** può solo attivare la guardia: `is_production() or override`. Nessun modo da codice di spegnerla.
- **G6 (CA): `end_segment` con `kind` sconosciuto:** in produzione nessuna eccezione, scarto con segnale.
- **G12: partizioni e fuso orario:** confini letti in UTC indipendentemente dal `TimeZone` della sessione (per esempio con `SET LOCAL TimeZone = 'UTC'` nella transazione o leggendo i confini dal catalogo in forma UTC). Test con `TimeZone = 'Europe/Rome'`.
- **G13 (CA): tipo atteso per variabile** nell'istantanea (intero, booleano, stringa di vocabolario); valore del tipo sbagliato, min o max non numerici, `0` dove il minimo è 1: `VariableUnavailableError` con segnale. Nessun `max(1, ...)` o altra correzione silenziosa.
- **G17: log di ripiego** con messaggio che contiene evento, tenant e campi chiusi (non solo in `extra`); nessun campo con nome riservato di `LogRecord`.
- **G18: nome della chiave scartata nel segnale:** solo se è una chiave della whitelist o ha il formato `segmento.segmento` con segmenti di lettere minuscole e al più un numero limitato di segmenti (invariante); altrimenti solo la lunghezza.
- **Formati provvisori (G3, CA minore), decisioni dell'utente:** `run_id` = UUID canonico generato da Gravya; `gravya.decision.reviewer_ref` = prefisso fisso più UUID canonico (provvisorio, fino ad A6); `MIN_KEY_BYTES` = 32 (provvisorio, fino ad A6); campi dei segnali in un insieme chiuso unico; `gravya.tool.outcome` confermato. Nel report, sezione dei vocabolari provvisori, correggi l'affermazione che i formati respingono codici fiscali, telefoni e IBAN: vale solo per la forma grezza.
- **CA minore: `raw_arguments`** con `repr=False` e riferimento azzerato dopo il calcolo dell'HMAC.
- **CA minore: CI.** Build senza isolamento o con strumenti di build fissati nel lockfile; `apt-get` non necessario se il client psql non serve; database di CI con ruolo proprietario non superuser per migrazioni e test (come nel punto 2 del criterio di fine).
- **Criterio 6 (test instabile):** con la scrittura asincrona il test misura il costo per il chiamante (validazione e accodamento). Soglia `e1.overhead_p95_ms` invariata.
- **Contatori di perdita in memoria (CA minore):** restano in memoria finché A5 non definisce la tabella; dichiaralo nel report come limite da riportare in E1 v1.7.

## Regole
Commit piccoli per gruppo, push su `claude/impl-e1`, niente merge. Non modificare `docs/` salvo il tuo report e i file di prova nei limiti indicati sopra. Nessun file fuori dal worktree. I ruoli PostgreSQL nuovi solo tramite migrazioni o fixture di test, con nomi che iniziano per `gravya_`; niente modifiche a `pg_hba.conf` o alla configurazione del cluster oltre a quelle già fatte nel giro 2.
