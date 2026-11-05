# Task per l'implementer, giro 2: correzioni dopo BLOCCA di code-reviewer e compliance-auditor

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisioni dell'utente: «ok» alle raccomandazioni 1 (a), 2 (a), 3 del coordinator; «Gli 8 rilievi da riportare li puoi risolvere direttamente tu» (soluzioni scelte dal coordinator, sotto).

Stesso documento (E1 v1.6), stesso perimetro (§9 passi 0, 2, 3), stesso worktree `/workspace/wt-impl-e1`, stesso branch `claude/impl-e1` (ora a `8d56cf0`). Valgono ancora tutti i vincoli di `task-implementer.md`.

Fonti dei rilievi: `report-code-reviewer.md`, `report-compliance-auditor.md` (questa cartella). Prove: `code-reviewer/test_repro_rilievi.py` e `code-reviewer/conftest.py` (oggi 33 falliti, 6 passati).

## Criterio di fine (vincolante)
1. Tutti i test di riproduzione del code-reviewer passano: `pytest -q -p no:cacheprovider --basetemp=docs/revisioni/impl-e1/code-reviewer/basetemp docs/revisioni/impl-e1/code-reviewer/`. Non modificare quei file: se un test riproduce un comportamento che resta voluto dopo le scelte sotto (per esempio per il criterio 16), riportalo nel report con il motivo, non riscriverlo. Cancella `basetemp` alla fine.
2. Tutta la suite del repository passa, anche con `PGHOST=127.0.0.1` (come nella CI, TCP), e i nuovi test dimostrano i comportamenti corretti (devono fallire sul codice di `8d56cf0`).
3. Il report `report-implementer.md` è aggiornato con una sezione «Giro 2» (non riscrivere la sezione del giro 1): rilievo per rilievo, cosa è cambiato e quale test lo prova.

## Bloccanti (entrambi i revisori)
- B1 (CR R17, CA bloccante). Nessun campo libero scritto: `name`, `status` (traccia e segmento), `run_id`, `execution_ticket_id`, `workflow_id`, `workflow_version`, `retention_class` passano dalla stessa validazione della whitelist. In produzione: scartato, contato e segnalato senza valore; fuori produzione: errore. Vocabolari e formati: vedi «Decisione 2».
- B2 (CR R3, CA 7). Fail-open vero: nessuna eccezione della scrittura delle tracce o dell'invio di un segnale esce dall'helper verso il chiamante. Segnale non salvabile: log strutturato senza contenuti (solo nome dell'evento, tenant, conteggi). Contatore delle perdite persistito (non solo in memoria) quando il DB torna disponibile.
- B3 (CR R2). Valori di tipo inatteso (liste, dict, non hashable) scartati e segnalati, mai un'eccezione.
- B4 (CR R1). Hash: esattamente 64 caratteri `[0-9a-f]` (minuscoli), con espressione regolare piena; niente `int(x, 16)`.
- B5 (CR R13, R8; E1 §5). L'helper scrive con **una connessione propria** (mai quella del chiamante) e con **scrittura asincrona bufferizzata** in background, dimensione `e1.write_buffer_size` (numero di segmenti, decisione 3), con limite di attesa: buffer pieno o DB lento = perdita contata e segnalata, il chiamante non aspetta. Ruolo `gravya_writer` e tenant valgono solo nella transazione dell'helper; nessun `commit()` sulla connessione di altri (anche il sink dei segnali).
- B6 (CR R5, R6; CA 2). L'HMAC lo calcola l'helper: il chiamante passa gli argomenti (byte o oggetto serializzabile in modo canonico), l'helper calcola HMAC-SHA-256 con la chiave del tenant e imposta `gravya.hash.key_ref`. Un `gravya.tool.args_hash`/`gravya.decision.args_hash` passato già calcolato dal chiamante è scartato e segnalato; senza chiave valida l'attributo non è scritto (segnale). Chiave vuota o sotto una lunghezza minima: non valida (la lunghezza minima è invariante di formato: dichiarala nel report come da confermare con A6). `gravya.prompt.hash` accettato solo insieme a `gravya.prompt.key` e `gravya.prompt.version`; il criterio 16 resta **parziale** finché E2 non esiste (l'helper non può distinguere l'hash del template da quello del render): dichiaralo.
- B7 (CR R4, CA 6). Nel segnale il nome della chiave scartata compare solo se rispetta il formato degli identificativi di chiave (nomi puntati della whitelist, breve); altrimenti al suo posto la lunghezza. Il sink accetta solo un insieme chiuso di campi per tipo di segnale.

## Rilievi da riportare e minori (soluzioni scelte dal coordinator)
- Identificativi opachi (CA 1, CR R9): formato stretto per campo: UUID dove l'identificativo è generato da Gravya; altrimenti prefisso fisso più carattere ammesso ristretto e lunghezza breve. `destination` solo come identificativo dichiarato (nessun punto di dominio né `/`). I formati sono invarianti della whitelist versionata (catalogo §18), non variabili.
- WITH CHECK non tautologico (CA 4): l'helper è legato a un tenant di contesto alla creazione (o per chiamata, da un contesto esplicito) e rifiuta un modello con `tenant_id` diverso; test sull'helper, non solo SQL. Segmento agganciato a un `trace_id` di un altro tenant: rifiutato (CR R11; vincolo o controllo nel DB).
- Nessuna modifica dopo la chiusura (CA 5, CR R7): UPDATE ammesso solo con `ended_at IS NULL` (imposto nel DB: policy o trigger); privilegi di colonna (niente UPDATE su `tenant_id`, `trace_id`, `segment_id`, `kind`, `started_at`); `end_segment` valida contro il `kind` salvato; un UPDATE con 0 righe è contato e segnalato.
- Tabella provvisoria dei segnali (CA, da riportare; CR, minore): al writer solo INSERT (niente SELECT); RLS abilitata e forzata.
- CI (CA 8): `permissions: contents: read`; action e immagine fissate per digest/SHA; dipendenze bloccate con hash (lockfile); togliere `fastapi` finché non serve. Nessun segreto.
- Ruolo writer (CA minore): `NOLOGIN`; il grant di membership al ruolo che esegue le migrazioni solo dove serve ai test, non come comodità in produzione; dichiara nel report come si connetterà l'applicazione.
- Partizioni (CA minore, CR R14): RLS abilitata e forzata anche su ogni partizione creata; conversione in UTC prima del calcolo dei confini; con intervallo cambiato non dichiarare coperta una partizione esistente con confini diversi (errore e segnale). `epoch_year`: dichiararlo come invariante di allineamento (commento e report), non variabile.
- Snapshot malformato (CR R18): blocco con segnale (DX-17), mai AttributeError. L'interfaccia accetta anche booleani e stringhe di vocabolario, non solo interi positivi.
- Guardia di ambiente (CA minore): con `API_ENV` non impostata resta sviluppo (testo deciso), ma all'avvio parte un segnale «ambiente non dichiarato». Rimuovi `production_override` se permette di spegnere la guardia da codice applicativo (nei test usa l'ambiente).
- `migrations/env.py` (CR minore): niente URL di default; senza `DATABASE_URL` la migrazione fallisce con messaggio chiaro.
- DSN fissi nei test (CR, da riportare): tutti i test leggono `GRAVYA_E1_TEST_DSN`/variabili PG*; niente socket Unix fisso né ruolo `root`.
- Asserzione con `or` in `test_criterio8_partizioni.py`: renderla stretta. `pytest.raises(Error)` troppo largo nel test del criterio 3: usare l'eccezione specifica.
- Attributi obbligatori per `kind` (CA minore): fuori perimetro (passo 5); non implementarli ora, citali nel report.

## Decisione 2 (utente, «ok»): vocabolari provvisori
Definisci tu, minimi e marcati come **provvisori** nella whitelist `redaction_version` 1, e riportali in una sezione del report «Vocabolari provvisori da recepire in E1 v1.7»: valori ammessi di `status` (traccia e segmento), formato o vocabolario di `name` per `kind`, formati di `run_id`, `execution_ticket_id`, `workflow_id`, `workflow_version`, `retention_class` (valori dalle classi di E1 §4.1 e del catalogo §2), nome dell'attributo con l'esito del tool (proposta: `gravya.tool.outcome`, valori `ok`, `denied`, `approval_required`, `rate_limited`, `error` di E1 §4.2) e vocabolari chiusi dei campi `gen_ai.*` (solo formato stretto dove l'elenco non è noto). Non inventare valori di business: dove un elenco dipende da altri documenti (C1 `router`, cataloghi di agenti e tool), usa un formato stretto e segnalalo.

## Decisione 3 (utente, «ok»)
`e1.write_buffer_size` = numero di segmenti, valore di sviluppo 100; `e1.attributes.max_value_bytes` valore di sviluppo 2048 (gli identificativi hanno formati propri più stretti); chiavi HMAC da interfaccia fino ad A6; tabella dei segnali provvisoria, solo inserimento; scelte tecniche confermate: `pyproject.toml`, Alembic, psycopg 3, pytest, istantanea JSON, layout `src/gravya_e1`. Aggiorna l'istantanea (unità del buffer) e il report di conseguenza.

## Regole
Commit piccoli per gruppo di rilievi, push su `claude/impl-e1`, niente merge. Non modificare `docs/` salvo il report e questo file non va toccato. Nessun file fuori dal worktree; usa `--basetemp` dentro il worktree per pytest; non creare ruoli PostgreSQL nel cluster diversi da quelli delle migrazioni e dei test (il ruolo `root` creato nel giro 1 resta, non crearne altri).
