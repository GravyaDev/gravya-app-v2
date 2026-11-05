# Report compliance-auditor — PR claude/impl-e1 (E1 v1.6, passi 0, 2, 3)

Diff a tre punti `origin/claude/docs-ondata-1...HEAD` (head 5c07805). Sola lettura. Esito: **BLOCCA** (1 bloccante, 8 da riportare, 5 minori).
Norme: registro v1.7 (GDPR artt. 5, 25, 28, 32 ✔; NIS2 art. 21 ✔; Reg. 2024/2690 ✔). Nessuna norma da aggiungere al registro.

## Rilievi

### R-01 BLOCCANTE — Colonne di testo libero non coperte dalla whitelist (DA-E1-02, GDPR 5(1)(c), 25) — verificato
- `src/gravya_e1/models.py` righe 14-47 e `tracing.py` righe 165-245: `SegmentStart.name`, `TraceStart.run_id`, `execution_ticket_id`, `workflow_id`, `workflow_version`, `retention_class`, `TraceEnd.status`, `SegmentEnd.status` sono `str` senza alcuna validazione e vengono scritti in chiaro nelle colonne `text` di `migrations/versions/0002_schema.py` (righe 58-92).
- E1 §4.2: «`name`, sorgenti, esiti e codici di errore sono valori di un vocabolario chiuso, non testo libero». Criterio 4: «nessun valore fuori formato viene scritto».
- Un contenuto (testo di prompt o risposta, PII) passato in `name` o `status` entra nella traccia senza scarto né segnale; i test del criterio 4 provano solo `attributes`.
- Proposta: applicare agli stessi campi i validatori di `whitelist.py` (identificativo opaco con lunghezza massima da `e1.attributes.max_value_bytes`; `status` e `root_kind` come insiemi chiusi); in produzione scartare e segnalare, fuori produzione fallire; aggiungere test con sentinella in `name` e `status`.

### R-02 DA RIPORTARE — Il vincolo opaco/identificativo lascia passare testo e PII senza spazi (GDPR 5(1)(c), 25; DA-E1-02) — verificato
- `whitelist.py` righe 275-293: `opaque_id` accetta `[A-Za-z0-9_\-:./]+` fino a `max_value_bytes` (2048 nello sviluppo). Vale per `gen_ai.agent.name`, `gravya.retrieval.source`, `gravya.decision.reviewer_ref`, `gen_ai.tool.call.id`, `gravya.prompt.key` ecc.
- Passano «mario.rossi», «3331234567», o una frase con underscore al posto degli spazi. `reviewer_ref` è uno pseudonimo (dato personale, E1 §4.3) e non ha un formato che lo distingua da un nome. Il report implementer lo dichiara (decisioni_mancanti 7), ma E1 §4.2 chiede un vocabolario chiuso o un formato.
- Proposta: per ogni campo un formato stretto (pattern e lunghezza breve per tipo, per esempio UUID o prefisso fisso per `reviewer_ref`, `tool.call.id`, `decision.id`) o un elenco chiuso da catalogo/E16; il valore massimo 2048 byte è eccessivo per un identificativo. Serve la scelta dell'utente sugli elenchi.

### R-03 DA RIPORTARE — `args_hash` accettato da qualunque esadecimale a 64 cifre, senza HMAC né `key_ref` (GDPR 25, 32, considerando 26; DA-E1-09; criteri 11 e 15) — verificato
- `whitelist.py` righe 306-313 e 353-360: `gravya.tool.args_hash`, `gravya.decision.args_hash`, `gravya.policy.bundle_hash` e `gravya.prompt.hash` sono validati solo come esadecimale a 64 cifre. `tracing.py` righe 109-124: `hash_tool_args` è un metodo separato; `start_segment` non lo chiama e non richiede `gravya.hash.key_ref` insieme all'hash.
- Un chiamante può scrivere un SHA-256 semplice di argomenti a bassa entropia, che E1 §4.3 considera dato personale riconducibile. E1 §5: «L'HMAC lo calcola l'helper… senza chiave valida l'attributo non è scritto». Qui l'attributo è scritto anche senza chiave valida, se il chiamante lo fornisce.
- Proposta: `start_segment` riceve i byte degli argomenti (non l'hash), calcola l'HMAC con la chiave del tenant e imposta `key_ref`; un `args_hash` fornito dal chiamante viene scartato; `args_hash` senza `key_ref` è scartato. Il criterio 16 resta un limite strutturale, già dichiarato.

### R-04 DA RIPORTARE — Il tenant del contesto non esiste: il WITH CHECK è tautologico (isolamento tra tenant; DA-E1-10; E1 §6 «rifiutato dal WITH CHECK e dall'helper») — verificato
- `tracing.py` righe 165-245 e `db.py` righe 17-31: il GUC `app.tenant_id` è impostato con `tenant_id` preso dal modello stesso (`segment.tenant_id`) che fornisce anche il `tenant_id` della riga. Riga e sessione concordano per costruzione, quindi RLS non intercetta un chiamante che passa il tenant sbagliato (per esempio per un errore nella propagazione dal job). L'helper non confronta con un tenant di contesto autenticato.
- Il test del criterio 3 prova solo SQL diretto con GUC e riga discordi.
- Proposta: l'helper si lega a un tenant di contesto (costruttore o parametro di sessione fornito dal chiamante autenticato) e rifiuta ogni modello con `tenant_id` diverso; test sull'helper, non solo su SQL.

### R-05 DA RIPORTARE — Il writer può modificare tracce e segmenti già chiusi e aggirare la whitelist con SQL diretto (Reg. 2024/2690 allegato 3.2.5 come buona pratica, DX-10(a); E1 §6 e §7) — verificato
- `0002_schema.py` riga 109: `GRANT SELECT, INSERT, UPDATE` sulle tabelle a `gravya_writer`, su tutte le colonne, senza trigger né condizione. `end_trace` e `end_segment` (`tracing.py` righe 190-245) non hanno `WHERE ended_at IS NULL`; `end_segment` fa `attributes || nuovo` e può sovrascrivere chiavi già scritte (anche hash e `key_ref`).
- E1 §6: «Le tracce non sono modificabili dopo la chiusura»; §7: «nessuna modifica dopo la chiusura». Nessun CHECK sul DB limita le chiavi di `attributes`: la whitelist è solo applicativa.
- Proposta: trigger o policy `UPDATE` che ammette solo righe con `ended_at IS NULL`; privilegi di colonna (nessun UPDATE su `tenant_id`, `trace_id`, `kind`); eventualmente funzioni `SECURITY DEFINER` per le scritture o un CHECK sulle chiavi ammesse per `kind`. Serve scelta di progetto; non blocca il passo 6 (DELETE per riga andrà concesso a un ruolo F6 separato).

### R-06 DA RIPORTARE — Tabella provvisoria dei segnali: SELECT al writer senza RLS (isolamento tra tenant; C2) — verificato
- `0003_signals_provisional.py` righe 28-38: `gravya_signals_min_audit` ha `tenant_id` nullable, nessuna RLS, e `GRANT SELECT, INSERT … TO gravya_writer`. Il ruolo che opera nel contesto di un tenant legge i segnali di tutti i tenant, che contengono `tenant_id`, nomi di chiavi scartate, tabelle e motivi.
- Proposta: togliere il SELECT al writer (solo INSERT) oppure abilitare RLS e `FORCE`; ricordare nella migrazione che la tabella definitiva è di A5. Nota: la tabella è dichiarata provvisoria, ma il GRANT è codice reale.

### R-07 DA RIPORTARE — Il segnale scarta il valore, ma non vincola il nome della chiave e il sink accetta payload arbitrario (DA-E1-02; GDPR 5(1)(c)) — verificato
- `tracing.py` righe 133-141: `key=d.key` è il nome della chiave del dizionario fornito dal chiamante, non limitato per lunghezza né formato; una chiave come `"Ciao Mario Rossi, …"` finisce nella tabella di audit. `signals.py` righe 58-66: `emit(**payload)` serializza qualunque argomento; il docstring («chiavi del payload dichiarate esplicite dal chiamante») non è imposto dal codice.
- Proposta: nel segnale riportare il nome solo se è un identificativo di formato valido e breve, altrimenti un segnaposto più un hash HMAC della chiave o la lunghezza; il sink accetta un insieme chiuso di chiavi del payload per `kind` e scarta il resto. E1 §5 prevede «nome della chiave»: la scelta è da confermare.

### R-08 DA RIPORTARE — Il fail-open si rompe con il sink su PostgreSQL e non esiste ripiego per il segnale (NIS2 art. 21(2)(b)-(c) come progetto; E1 §6 e §5, C2) — verificato
- `tracing.py` righe 144-153: `_fail_open` chiama `self._signals.emit` senza protezione. Con `PostgresSignalSink` (`signals.py` righe 55-67, stessa connessione) un DB non disponibile fa sollevare l'eccezione dentro il gestore, che arriva al chiamante: l'esecuzione si interrompe e il segnale va perso. I test (criterio 5) usano solo il sink in memoria.
- `loss_count` (riga 101) è un contatore in memoria della singola istanza: non è persistito (E1 §4.1 prevede la classe «contatori di perdita»).
- Anche `end_segment(kind: str)` con kind non valido solleva `ValueError` (riga 58) fuori dal try, quindi non è fail-open in produzione; `start_segment` è protetto da `Literal` solo se il modello è costruito con Pydantic.
- Proposta: `emit` non deve mai propagare dal percorso fail-open; definire il ripiego se il segnale non si salva (log strutturato senza contenuti verso lo stesso A5 appena possibile) e persistere i contatori. Scelta da riportare.

### R-09 DA RIPORTARE — Supply chain della CI e delle dipendenze non fissate (NIS2 art. 21(2)(d); Reg. 2024/2690 5.1) — verificato per il testo, dedotto per l'impatto
- `.github/workflows/ci.yml` righe 11, 27-29, 32: immagine `postgres:16` e action `checkout@v4` e `setup-python@v5` per tag mobile, nessun `permissions:` (il token può avere permessi di scrittura secondo le impostazioni del repository). `pyproject.toml` righe 6-17: dipendenze con soli `>=`, nessun lockfile con hash. `fastapi` è dichiarata ma non usata da questo perimetro (dedotto da grep su src e tests).
- La CI non contiene segreti (`trust`, utente `root`, nessuna password: conforme a DX-22(b)/C11).
- Proposta: `permissions: contents: read`, action fissate per SHA, lockfile con hash, togliere `fastapi` finché non serve. Il livello di rigore è una scelta dell'utente.

### R-10 MINORE — Writer con LOGIN senza password e architettura di connessione con ruolo elevato (NIS2 21(2)(i), controllo accessi) — dedotto
- `0002_schema.py` righe 39, 46-54: `gravya_writer … LOGIN` senza password; `GRANT gravya_writer TO current_user` dentro una migrazione. `db.py`: l'app si connette con un ruolo amministrativo e fa `SET LOCAL ROLE`, quindi chi ha il controllo della connessione può fare `RESET ROLE`; con un superuser (come in CI) RLS non si applica.
- Proposta: ruolo `NOLOGIN` o con credenziale dalla pagina credenziali e connessione applicativa diretta come writer; il grant al `current_user` solo per i test. Il report segnala già la questione del pool (non verificato).

### R-11 MINORE — Difese in profondità sulle partizioni (isolamento tra tenant) — dedotto
- `partitions.py` righe 70-81: le partizioni sono create con `PARTITION OF` senza `ENABLE/FORCE ROW LEVEL SECURITY` né policy; la RLS del padre non si applica agli accessi diretti alla partizione. Oggi nessun GRANT sulle partizioni, quindi nessun accesso del writer. Rischio per il passo 6 (ruolo aggregato del superadmin, DA-E1-11): un GRANT diretto aggirerebbe RLS.
- Proposta: abilitare RLS e policy anche su ogni partizione creata.

### R-12 MINORE — Nessuna partizione di default né creazione anticipata; perdita silenziosa al cambio intervallo (NIS2 21(2)(c) come progetto) — dedotto
- Senza una partizione per `started_at`, l'INSERT fallisce e la traccia è persa (fail-open, con segnale ma con `loss_count` in memoria). Il job che crea le partizioni è del passo 6, fuori perimetro: nessun difetto in questo diff, da non dimenticare. La creazione è dentro `partitions.py` solo come funzione; `UPDATE` di `end_trace` e `end_segment` non segnala quando non trova righe (0 righe aggiornate = traccia chiusa persa senza conteggio).

### R-13 MINORE — Guardia `API_ENV` permissiva di default e override nel codice (DX-22, DA-A1-10) — verificato
- `config/env.py` riga 9: se `API_ENV` non è impostata il codice si comporta come sviluppo (valori «da definire» ammessi, errori sollevati invece di scarto). `TracingHelper` e `SnapshotVariableRegistry` hanno il parametro `production_override`, che spegne la guardia da codice. La guardia è un'invariante di deploy (decisa), quindi è coerente con il testo; la scelta del valore predefinito è da confermare.
- Proposta: valutare un default sicuro (variabile mancante = produzione) o un segnale all'avvio se non impostata.

### R-14 MINORE — Nessun attributo obbligatorio per `kind`; chiave HMAC senza lunghezza minima (osservabilità AI, art. 32) — dedotto
- `whitelist.py` e `hashing.py`: un segmento `llm` si scrive senza modello, versione e hash del prompt; `hmac.new` accetta una chiave vuota. Il criterio 12 è del passo 5; per la chiave è da fissare con A6 (lunghezza minima come invariante).
- `end_segment(kind)` valida contro il `kind` passato dal chiamante, non da quello della riga: si può aggiungere a un segmento `agent` attributi di `decision`.

## Letture
Vedi JSON. Altri file letti: tutti i file del diff (sorgenti, migrazioni, CI, istantanea), test conftest, criteri 3, 4, 5, 11, 15, 16, 17.

## Controllato e senza rilievi
- PV-02: nessun SDK, collector o export OTel (grep); solo `gen_ai.*` e `gravya.*`.
- Nessun segreto, chiave o password nel repository o nella CI; chiavi dei test sintetiche; dati dei test sintetici (esempi con `example.com`, numero fittizio): DA-E3-08 ok.
- RLS: `ENABLE` + `FORCE`, policy `USING` e `WITH CHECK` sullo stesso predicato, `NOBYPASSRLS` verificato dai test, writer senza DELETE; GUC non impostato fornisce 0 righe.
- Segnale per attributo scartato: il valore non compare (verificato dal test sentinella e dal codice); in produzione scarto + segnale con `kind`, chiave, motivo e conteggio.
- Variabili (DX-22/DX-17): nessuna costante numerica di configurazione nel codice; istantanea unica; `da_definire` bloccata in produzione; `proposta_da_validare` con segnale.
- Nessuna ritenzione propria: nessun DELETE, nessuna durata nel codice; retention/export/cancellazione non pregiudicati (tenant_id indicizzato, attributi in JSONB interrogabili per pseudonimo; servirà un indice al passo 6).
- HMAC-SHA-256 esadecimale per tenant, rotazione a due chiavi e distruzione coerenti con DA-E1-09/DA-CV-23 a livello di interfaccia (la sorgente reale è di A6).
- Nessun trasferimento extra-UE, nessun servizio esterno.
