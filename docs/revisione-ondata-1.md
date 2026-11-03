# Revisione incrociata — Ondata 1

Data: 2026-11-03. Ho letto insieme i nove documenti di `docs/`, il template di `Prompt e workflow.md` §1 e le ricognizioni di `docs/stato/`. Ho controllato a campione le affermazioni sul codice in `/workspace/gravya-app` al commit `349118b11`. Tutti i documenti sono ora alla versione 1.1. Per ciascuno, la riga 1.1 dello "Storico modifiche" spiega cosa è cambiato e perché.

Legenda della matrice: **D** = dipendenza dichiarata nel documento della riga. **D\*** = dipendenza aggiunta in revisione perché l'altro documento la dichiarava e qui mancava. **(c)** = dipendenza condizionata a una decisione aperta. **i** = dipendenza indiretta. Ondata delle colonne: 1 = A1, A3, B1, B2, C1, C3, E1, E2, E3; 2 = A2, A4, A5, B5, C2, C4, D1, G2; 3 = C5, D2–D5, E4–E6, F1, G4.

## 1. Matrice delle dipendenze incrociate (riga dipende da colonna)

| ↓ dipende da → | A1 | A2 | A3 | A5 | B1 | B2 | B5 | C1 | C3 | C4 | E1 | E2 | E3 | F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A1** | — | | | D | | | | | | | D | D\* (opz.) | | |
| **A3** | i | D (fixture in ondata 1) | — | D | D (chiamante) | D (chiamante) | | | D | | D | | | |
| **B1** | | i | D | | — | D | D\* | D (chiamante) | | D | D | D\* | | |
| **B2** | i | i | D | D | D | — | | | D\* (approvazione) | | D | | | |
| **C1** | i | i | D | | D | D | D (ondata 2; skeleton: checkpointer esistente) | — | D | D | D | D | D | |
| **C3** | | | D | D | | D | D (**critica**) | D | — | | D | | | D |
| **E1** | | | i | | i | i | | i | i | | — | | | |
| **E2** | | | D | | | | | | D\* (c) | | D | — | D\* (c) | D (o schema minimo) |
| **E3** | | | D | | D | D | | D | D | | D (c: DA-E1-01) | D | — |

Dipendenze verso ondate successive non presenti in colonna: A1 → (richiesto da A2, A4); A3 → A4 (confronto hash); B1 → richiesto da C4, D1–D5; B2 → richiesto da D1–D5, E5, E6; C1 → C2, C5, G2 (Non verificato quale UI); C3 → richiesto da G2, D1–D3, C4, E4/E5; E1 → richiesto da E4 e dagli ID non assegnati di guardrail telemetry; E2 → richiesto da E4, G4; E3 → richiesto da E4 e dal trigger di auto-disable (master 0.4.2).

**Cicli da tenere presenti:** A3↔B2 (B2 chiama A3; A3 elenca B2 come chiamante), B1↔C1 (ciascuno elenca l'altro sotto "Dipende da"), C1↔C3, C1↔E3 (C1 usa E3 come gate; E3 esegue il workflow di C1). Sono reciproci nei contratti, non errori. Fissano però l'ordine di costruzione: prima i contratti di tutti, poi le implementazioni.

## 2. Correzioni fatte

1. **E1: struttura del template.** Le sezioni 6-12 erano fuori ordine e con titoli sbagliati. Mancava "Comportamento", "Decisioni aperte" occupava la §9 ed era duplicata nell'Appendice C. Le ho riordinate secondo il template. La nuova §6 "Comportamento" è ricavata solo dal contenuto che il documento già aveva. Il caso "span senza company_id" è segnato come Non verificato. Le decisioni ora stanno solo nell'Appendice C.
2. **Nomi degli attributi di span unificati in E1 §4.1.** Ogni documento usava nomi propri:
   - A3: `policy.result`, `policy.bundle_hash`, `tenant_id`;
   - E2: `prompt.key/version/hash`, mentre E1 aveva `gravya.prompt.ref`;
   - E3: `eval.case_id`, `eval.pass`;
   - C1: `workflow_id`, `version`, `node_id`.

   Ora valgono `gravya.policy.*`, `gravya.prompt.*`, `gravya.eval.*`, `gravya.workflow.*` e `gravya.company_id`. Ho allineato A3 (§7, CA6), E2 (§3, CA8), E3 (§4.3), C1 (§7, CA6) e C3 (§7, kind=hitl). In E1 ho aggiunto il tipo di span "Caso di eval". I nomi restano una proposta da validare.
3. **B2 ↔ A3: contratto della decisione.** Il catalogo di B2 non aveva i campi che servono al `DecisionRequest` di A3 (`domain`, `creates_new`, assi di scope). Li ho aggiunti e ho descritto come B2 costruisce la richiesta. Ho segnalato che nessun documento indica la fonte di `budget_state` (DA-A3-04).
4. **C1: flusso dei nodi tool.** C1 diceva "A3 e poi B2" e nel CA7 chiedeva "0 chiamate a B2" per un tool negato. Questo non era compatibile con B2, che è l'unico punto che consulta A3. Ora il nodo invoca B2, B2 consulta A3, e il CA7 verifica 0 esecuzioni del tool.
5. **C1: formato dei riferimenti.** `prompt_ref` era scritto "id@versione": ora è `{prompt_key}@{version}`, come in E2. `tool_ref` ora è il `tool_id` del catalogo B2.
6. **B1: affermazione sul codice smentita.** B1 diceva che "oggi non c'è un ciclo di tool" (preso dalla ricognizione kloudify, non riletto), in contraddizione con B2. Ho verificato `generic_executor.py`: `_MAX_TOOL_CALLS_PER_RESPONSE = 8` alla riga 40 e `_run_tool_loop` alla riga 438. Ho corretto l'Appendice A e la §9 di B1 e aggiunto una nota in E3 §12.
7. **E2: affermazione sul master smentita.** E2 diceva "Redis Stream/Kafka fra quelli del master". Il master non cita né l'uno né l'altro (grep sul file). Ho corretto il testo e rimandato a DA-A1-03.
8. **Dipendenze dichiarate in un solo verso**, ora completate:
   - E1: aggiunti B1, B2, C1, A3, C3, A1 tra i richiedenti;
   - A3: aggiunti B1, E3, E2;
   - B2: aggiunto E3;
   - C1: aggiunti C3, B1, E3;
   - C3: aggiunti C1, A3, B2, E3, E2 (c);
   - E3: aggiunti C1, E2;
   - B1: aggiunte le dipendenze da E2 e B5;
   - A1: aggiunta la dipendenza opzionale da E2.
9. **E2: verso invertito.** C3 era tra i richiedenti di E2, ma è E2 che usa C3 per la promozione. L'ho spostato in "Dipende da" (condizionale). Ho aggiunto anche la dipendenza condizionale da E3.
10. **Decisione aperta mancante.** DA-A1-04 rinviava a B2 la scelta dell'allowlist dei tool, ma B2 non la trattava. Ho aggiunto DA-B2-05 senza raccomandazione.
11. **Trasporto eventi.** A1, B2, C1 ed E2 ora rimandano tutti a DA-A1-03, che ho marcato come trasversale.
12. **B1:** aggiunta la riga "Ondata" in Identità, che mancava solo qui.

Ho controllato le stime temporali in tutti i documenti: non ce ne sono, si usano solo le taglie S/M/L. Le occorrenze di "giorni" e "mesi" che restano sono dati (scadenza di R1, retention AI Act), non stime.

**Verifiche a campione confermate** (commit `349118b11`): `MAX_CASCADE_DEPTH = 3` (A1); `job_timeout = 300` (B1); `KLOUD_APPROVAL_DEFAULT = true` (C3); "NOT YET WIRED" in `run_scope_contract.py` (A3); `MAX_STEPS_PER_RUN = 500` e `5 * 60 * 1000` (C1); "TODO Phoenix span" in `councils/runtime.py` ed evento `llm.inference` in `llm-dispatch.ts` (E1); prompt in italiano hard-coded in `card_analyzer.py` intorno alla riga 113 (E2); nessun workflow di eval in `.github/workflows` (E3); limiti di memoria e pids nel compose prod (B1).

## 3. Problemi aperti (richiedono una scelta: non decisi in revisione)

1. **Rapporto tra gravya-app e v2 e priorità Beta (30/11).** La stessa domanda compare in sei documenti, con raccomandazioni diverse:
   - DA-A1-05 e DA-A1-02(c);
   - DA-B2-01: raccomanda un gateway nuovo che usa il codice solo come riferimento;
   - DA-C3-01: raccomanda di portare i moduli esistenti;
   - DA-C1-04, DA-E2-05, DA-E3-06: rimettono la scelta all'utente.

   B2 e C3 si contraddicono sulla strategia di riuso. Serve un'unica decisione dell'utente, da cui poi derivano le altre.
2. **Chi parcheggia la chiamata da approvare.** In A3 e B2 è B2 a rispondere `approval_required` e a passare la chiamata a C3. In C3 è il run/esecutore a parcheggiarla via `POST .../kloud/approvals` (codice esistente) e poi `write_replay` la riesegue. Va scelto chi possiede il parcheggio nel modello v2.
3. **HITL come nodo esplicito o come esito di policy.** C1 prevede un nodo `kind=hitl` nel grafo. A3, B2 e C3 prevedono un'interruzione scatenata dall'esito `require_approval` dentro una chiamata di tool. Le due semantiche vanno riconciliate: possono convivere solo se si definisce chi chiama `interrupt()`.
4. **B5 è critico ma è in ondata 2.** C3 indica B5 come dipendenza critica e B1 ne ha bisogno per la ripresa. Lo skeleton presuppone il checkpointer esistente (`kloud/checkpointer.py`), come dichiara C1. Va deciso se accettarlo esplicitamente per l'ondata 1 o anticipare B5.
5. **A2 assente in ondata 1.** A3 lavora su un bundle fixture scritto a mano. A1 produce un grafo che in ondata 1 nessuno compila. Il percorso A1→A2→A3 non è verificabile fino all'ondata 2.
6. **A3 per le scritture umane.** E2 chiede ad A3 di autorizzare le scritture sul registry (attori umani o superadmin). A3 è progettato per azioni di agenti, con `DecisionRequest` incentrato su agente e tool. Le opzioni sono estendere A3 agli attori umani oppure usare il modello permessi esistente lato server (grant-evaluator / HSAR).
7. **Convenzione dei nomi evento.** Quasi tutti i documenti usano nomi puntati (`graph.*`, `policy.*`, `tool.*`, `runtime.job.*`, `workflow.*`, `prompt.*`). C3 propone `hitl_requested` ecc., con underscore, come i `log_event` esistenti. C1 emette `workflow.run.interrupted` "verso C3", ma C3 non dichiara eventi consumati. B2 emette `tool.denied` e A3 `policy.decision` più `tool.scope.denied`: per un singolo diniego ci sono potenzialmente tre eventi. Servono una convenzione unica e un'assegnazione di chi emette cosa.
8. **Trasporto eventi (DA-A1-03) e destinazione dell'audit prima di A5.** A1 usa `gravya_event_logs`, B2 ha DA-B2-04 (fail-open o fail-closed), B1 "da allineare a `gravya_event_logs` o E1". La decisione sul trasporto è unica e trasversale. Va decisa una volta sola.
9. **Linguaggio dei contratti condivisi.**
   - A1: zod;
   - C1: JSON Schema più zod;
   - C3: DA-C3-03 raccomanda JSON Schema neutro;
   - E2: JSON Schema per `variables_schema`;
   - E3: DA-E3-02 raccomanda un runner TS;
   - B2: DA-B2-02 raccomanda un servizio FastAPI;
   - A3: enforcer Python oppure OPA.

   Manca una decisione trasversale sul formato dei contratti tra Node e Python.
10. **Topologia dell'enforcement.** DA-A3-02 raccomanda un sidecar se si sceglie OPA, altrimenti una libreria in-process. DA-B2-02 raccomanda un gateway come servizio separato e scarta la libreria in-process perché non isola. Le due scelte vanno prese insieme, perché la latenza B2+A3 si somma.
11. **Nome del tenant.** A1, A3 ed E2 usano `tenant_id` (dichiarato uguale a `company_id`), B1 e C3 usano `company_id`, E1 usa `gravya.company_id`. L'equivalenza è dichiarata, quindi non è un errore, ma conviene fissare un solo nome nei contratti v2.
12. **Campo prompt nel `JobSpec` di B1.** E2 dice che B1 risolve il prompt, ma il `JobSpec` non ha `prompt_ref` e non ha una versione del prompt fissata per il run. Va deciso se è B1 a risolvere la versione attiva o se gliela passa C1.
13. **E3 dipende da OTel (DA-E1-01).** Se DA-E1-01 sceglie (C) DB-native, gli span di E3 e gli attributi di E2 vanno ridefiniti come eventi Timeline.
14. **Origine dell'allowlist dei tool** (DA-A1-04 / DA-B2-05): legata a DA-A1-02, la fonte di verità dei mandati.

## 4. Incoerenze tra master plan e stato reale (da segnalare all'utente)

1. **OpenTelemetry.** Il master lo prevede. Il codice lo esclude per decisione esplicita del 15/06 ("NO OpenTelemetry" in `timeline-engine.ts`; `enableOpenTelemetrySetup: false`). Riguarda E1, E2, E3 e B1.
2. **Grafo dei mandati.** Il master prevede Neo4j/Neptune. Nel codice non c'è alcun graph database: ci sono tabelle relazionali con RLS. Le tre tabelle dei permessi (grants, defaults, exceptions) sono separate per scelta. Inoltre il master (§ conclusione e fase 3.1) colloca il grafo dei mandati nella fase "scala", mentre `Prompt e workflow.md` mette A1 in ondata 1: anche i due documenti di riferimento sono incoerenti tra loro.
3. **OPA/Rego assente.** C'è un enforcer Python in-process (`_scope_enforcement.py`) che esclude i councils, più il grant-evaluator TS. I commenti si contraddicono sul fatto che sia attivo: "enforce mode" contro "NOT YET WIRED" (verificato in `run_scope_contract.py`) contro "irraggiungibile" in kloudify.
4. **Isolamento del runtime.** Il master chiede un ambiente effimero per job. Il codice ha container long-lived condivisi tra tenant, con isolamento via GUC/RLS, cioè proprio il "filtro WHERE" che il master giudica insufficiente.
5. **Tool gateway.** Il master lo vuole come confine architetturale. Nel codice i tool sono caricati in-process, l'audit è best-effort e il rate limit è solo per IP.
6. **Motore dei workflow.** Il master indica LangGraph. Il piano registrato in kloudify indica il motore Node β come motore unico dopo la Beta. Oggi i motori sono due.
7. **Versioning dei prompt ed eval harness.** Il master li mette nelle fondamenta. Il piano registrato li colloca post-Beta (#1801; regola del 02/11).
8. **Visione kloudify superata dal codice.** "I tool non vengono mai eseguiti" e "si approva il testo": al commit `349118b11` esistono il ciclo di tool e il parcheggio con replay della chiamata esatta. Resta Non verificato se questi percorsi siano attivi su staging, dove kloudify registra 0 approvazioni.
9. **Errore nella ricognizione `stato/sviluppo.md`.** Cita `ui/src/lib/hitl.ts` come schema Zod: il file non esiste (verificato).
10. **Nessuna fonte collega gravya-app-v2 alla Beta.** In kloudify nessun documento cita v2. Il rapporto tra i due repo non si può ricavare dai file: vedi problema aperto 1.

## Revisione v1.2 (2026-11-03)

Verifica di coerenza dopo l'applicazione di DX-01/PV-03 (ripartenza da zero) e DX-02/PV-01/PV-02 (niente OpenTelemetry, conformità prevalente) ai 9 documenti.

**Esito dei controlli (grep su tutti i 9 documenti):**
- OpenTelemetry/OTel/OTLP/collector: nessun residuo come scelta; le occorrenze rimaste sono esclusioni esplicite, citazioni del sistema precedente in Appendice A o righe di storico.
- Riuso/porting/Beta: nessuna raccomandazione residua basata su riuso di codice o vincoli Beta; DA-A1-05, DA-A3-05, DA-B2-01, DA-C1-02, DA-C1-04, DA-C3-01, DA-E2-05, DA-E3-06 risultano chiuse da DX-01; Appendice A rinominata in tutti i 9 documenti.
- §7 "Sicurezza e conformità": presente in tutti i 9 documenti, con GDPR, NIS2, AI Act e osservabilità AI; retention e basi giuridiche dubbie marcate DA RIPORTARE ALL'UTENTE.
- Tecnologie fuori perimetro: nessuna scelta di default (Neptune, LangSmith/LangGraph Platform, piattaforme eval SaaS, sandbox gestite marcate da riportare).

**Correzioni meccaniche fatte (allineamento al modello E1 §4.1-4.2):**
- B1: `trace_context` usava `span_id` → `parent_segment_id`.
- E3: record `gravya.eval.case` → segmento `kind=eval_case`.
- C1, C3: "tipo `gravya.decision`" → segmento `kind=decision` con `gravya.decision.kind`.
- A3: `gravya.company_id` come attributo → colonna `company_id` del segmento.

**Problemi aperti residui:**
1. A1 è elencato da E1 tra gli emettitori, ma E1 §4.2 non ha un `kind` per le mutazioni del grafo (`graph.mandate.*`): va deciso se sono segmenti di traccia (nuovo `kind`) o solo eventi di audit (A5/tabella propria). Decisione di merito, non corretta.
2. Problemi 7 (convenzione nomi evento, C3 con underscore), 8 (trasporto/audit prima di A5), 9, 10, 12 e 14 della sezione 3 restano aperti; il problema 13 (E3 dipende da OTel) è risolto da DX-02; il problema 11 (nome tenant) è ridotto ma dipende da DX-07.
3. Fail-closed dell'audit: DA-A3-07 e DA-B2-04 vanno decise insieme.
4. Owner del processo di notifica incidenti NIS2 (24 h/72 h) non assegnato in nessun documento dell'ondata 1.
5. DA-E1-05 (GenAI semantic conventions come solo vocabolario, formato header) DA RIPORTARE ALL'UTENTE.

**Matrice dipendenze:** invariata nelle relazioni; cambia solo la natura dell'arco verso E1, che ora è "scrive segmenti nel modello DB-native E1" per A3, B1, B2, C1, C3, E2 (attributi prompt), E3 (`eval_case`) e lettura diretta delle tabelle per E3. Nessuna dipendenza da OTel.

## Revisione v1.3 (2026-11-03)

Verifica di coerenza dei 9 documenti dopo le decisioni dell'utente del 2026-11-03 (DECISIONS.md, DX-09/10/11 e DA decise). Esito: nessun residuo meccanico da correggere.

- **Retention (DX-09):** nessun documento fissa durate proprie; tutti rimandano a DX-09 ed elencano le classi di dati prodotte. E1 cita le durate della v1.2 solo come ritirate.
- **DA decise:** DA-A1-01, DA-C1-01, DA-C1-05, DA-B1-06, DA-E3-09, DA-E1-02, DA-E3-08, DA-B2-07, DA-E1-05, DA-B2-04, DA-A3-07 sono indicate come decise nelle Appendici C e trattate come scelte nel testo; le DA di retention risultano «Assorbita da DX-09».
- **Fail-closed:** coerente tra A3 (allow→deny se il record non si salva, CA9), B2 (`tool.invoked` prima dell'esecuzione, criterio 3), C1 (criterio 8), C3 (AC-10), E2 (transazione unica, test §8.10) ed E3 (record E1 non salvato = exit 2).
- **Segnali verso A5 (DX-10):** dichiarati da A1, A3, B1, B2, C1, C3, E1, E2, E3.
- **AI Act (DX-11):** nessun requisito motivato come obbligo da alto rischio; artt. 12/14/19/26 indicati come buona pratica, art. 50 applicabile.
- **Vocabolario GenAI:** i nomi `gen_ai.*` compaiono solo in E1; gli altri documenti rimandano ai nomi fissati da E1, senza nomi divergenti.

Restano aperti (da non inferire): durate di default DX-09 e relativo responsabile (DX-12); se una coda durevole locale valga come «salvato» e come gestire il fallimento dell'audit di esito dopo l'esecuzione (B2, DA-B2-04); soglia di latenza complessiva di A3 con salvataggio sincrono; DA-A1-08 (base giuridica identificativi admin); campo/etichetta «generato da AI» per l'art. 50 (C1, C3, D1–D4).
