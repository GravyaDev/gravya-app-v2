# Registro delle decisioni

Solo decisioni **in vigore** e **aperte**, nella forma corrente, con il motivo che serve a capirle. La storia (versioni precedenti, precisazioni intermedie, righe chiuse o assorbite, testi dell'utente alla lettera) è in [decisioni-archivio.md](decisioni-archivio.md), che non si legge all'avvio. Quando una decisione cambia, la riga si aggiorna qui e la versione superata va in coda all'archivio, nello stesso commit. Prevalgono i principi vincolanti in [PRINCIPI.md](PRINCIPI.md).

Ultimo aggiornamento: 2026-11-05, registro ristretto alle sole decisioni correnti e due regole di §6 (testi dell'utente in decisioni-archivio.md).

Ogni decisione aperta nasce in un documento di dettaglio (Appendice C), numerata `DA-{ID}-NN`; le trasversali sono `DX-NN`, quelle del catalogo `DA-CV-NN`.

Stati: **Aperta** (manca la scelta); **Escalation** (serve una decisione di business di Daniele); **Decisa** (scelta fatta). «Ipotesi di lavoro» indica una decisione presa per l'implementazione e da rivalutare con dati reali.

---

## 1. Decisioni trasversali (DX)

| ID | Questione | Stato | Decisione | Motivo | Data |
|---|---|---|---|---|---|
| DX-01 | Rapporto tra gravya-app-v2, gravya-app e la Beta | Decisa | Ripartenza da zero (PV-03): pianificazione e codice v2 nuovi; gravya-app è solo riferimento per requisiti, lezioni e soluzioni validate, riportate solo tramite i documenti di dettaglio. | gravya-app nasce da un fork con una visione di prodotto diversa, ha codice e documenti in parte contraddittori e due motori di workflow. | 2026-11-03 |
| DX-02 | Aderenza al master plan o alle scelte esistenti | Decisa in parte | Niente OpenTelemetry (PV-02). La conformità (GDPR, NIS2, AI Act, comunicazioni elettroniche e marketing) e l'osservabilità AI prevalgono sul master plan (PV-01); nel dubbio si riporta all'utente. Le altre divergenze (graph DB, OPA, motore workflow, runtime effimero) si decidono una per una con questo criterio. | Decisione dell'utente: gestione dei dati conforme. | 2026-11-03 |
| DX-03 | Trasporto eventi (Redis Stream, Redis pub/sub o pg NOTIFY); coincide con DA-A1-03 | Aperta | | | |
| DX-04 | Linguaggio del backend e formato dei contratti condivisi | Decisa | Backend tutto in Python (FastAPI, LangGraph, PostgreSQL) in un solo repository; interfaccia in TypeScript più avanti; contratti condivisi in Pydantic. | Un solo linguaggio elimina i contratti tra Node e Python; LangGraph e i job di B1 sono in Python. Competenze del team non verificate. | 2026-11-04 |
| DX-05 | Chi parcheggia la chiamata da approvare e chi chiama `interrupt()` (B2 con `require_approval` secondo A3 e B2; il run secondo C3; nodo esplicito in C1) | Aperta | | | |
| DX-06 | Topologia dell'enforcement (sidecar, libreria o servizio); DA-A3-02 e DA-B2-02 insieme | Aperta | | | |
| DX-07 | Convenzione dei nomi | Decisa | Eventi con nomi puntati (`tool.invoked`, `hitl.requested`); il tenant si chiama `tenant_id` ovunque. I documenti con `hitl_*` o `company_id` si allineano nella loro revisione. | Un solo vocabolario tra documenti e codice. | 2026-11-04 |
| DX-08 | Dipendenze critiche nell'ondata 2: B5 (checkpointer) per C1, C3, B1; A2 (compilatore) per A3 | Aperta | | | |
| DX-09 | Politica di retention | Decisa | Politica unica di default (durate in §5), responsabile F6 (DX-12). Durate di sola lettura finché l'intervallo minimo-massimo del contratto/DPA non è definito (DA-CV-01); poi il superadmin le modifica solo entro l'intervallo (DX-15, DX-16). Override per classe nel modello, attivabile solo con l'intervallo della classe (DA-CV-10); override per agenzia attivo solo con l'intervallo del DPA (DA-C3-09). La scelta restituzione o cancellazione a fine contratto è sempre dell'agenzia (DA-CV-12); se non sceglie, export per tutto il periodo di uscita e poi cancellazione. Retention delle tracce più intervallo di partizione non oltre il massimo delle tracce; finestra di idempotenza con un massimo (valore da definire); sospensione per evidenze di incidente non attivabile finché massimo, riesame e categorie non sono definiti. | Minimizzazione (GDPR art. 5(1)(e)); DX-15 e DX-16 vietano modifiche fuori intervallo; art. 28(3)(g) lascia la scelta al titolare. | 2026-11-03; 2026-11-04 |
| DX-10 | Incidenti e NIS2 | Decisa | Gravya oggi non è soggetto NIS2 (due persone fisiche in regime forfettario); progettazione «NIS2 compliant ready by design». La notifica è di A5 (ondata 2); gli altri sottoprodotti inviano segnali ad A5, senza soglia locale (DA-CV-07). (a) Le misure rilevanti del Reg. (UE) 2024/2690 (log di accessi privilegiati e attività degli amministratori, protezione e backup dei log, orologi sincronizzati, MFA per gli account privilegiati, classificazione degli incidenti art. 7) sono requisiti di progetto per E1, E2, A5, A6. (b) A5 predispone il flusso (preallarme 24 h, notifica 72 h, relazione finale entro un mese, CSIRT Italia, decorrenza dalla conoscenza), presente ma non attivo (`incident.nis2_flow_active`) finché Gravya non è soggetto o un contratto con un'agenzia obbligata non lo richiede. (c) Le soglie «vincolo normativo» degli incidenti seguono il Reg. 2024/2690. I segnali sono sempre prodotti e conservati anche a flusso spento (C2; deroga per l'ondata 1 in §6). Con una variabile `incident.*` non leggibile vale il limite di legge, con segnale ad A5. Spegnimento del flusso: DA-CV-09. Destinatario CSIRT Italia invariante; configurabili solo il canale (elenco chiuso di canali ufficiali, da definire) e il contatto. Variabili GDPR sulle violazioni sempre attive; `incident.recurring_min_count` di tipo fisso; soglie più basse dei criteri del regolamento come scelta di progetto con notifica volontaria. | Scelta dell'utente di progettare già conformi per un possibile futuro assoggettamento; senza segnali conservati la decorrenza dei termini non è ricostruibile; il destinatario è fissato dalla legge. | 2026-11-03; 2026-11-04 |
| DX-11 | Ruolo GDPR e rischio AI Act | Decisa | Gravya è responsabile del trattamento (art. 28 GDPR) per le agenzie. Casi d'uso v2 non ad alto rischio: artt. 12, 14, 19, 26 AI Act non obbligatori, restano buona pratica di osservabilità; art. 50 applicabile. | Decisione dell'utente. | 2026-11-03 |
| DX-12 | Responsabile della retention | Decisa | Nuovo sottoprodotto F6 «Politica di retention e cancellazione» (componente F, ondata 2; ID proposto). | Nessun sottoprodotto del master plan la copriva. | 2026-11-03 |
| DX-13 | Superadmin e variabili di piattaforma | Decisa | Ruolo superadmin di istanza, distinto dagli admin delle agenzie, gestisce le variabili di piattaforma senza rilasci; ogni modifica versionata, auditata, fail-closed. Accesso ai dati dei tenant solo entro le istruzioni del titolare (art. 28), con log (DX-18, DX-19). | Parametri modificabili in piattaforma. | 2026-11-03 |
| DX-14 | Identità, ruoli e configurazione | Decisa | Nuovo sottoprodotto A6 (ondata 2): autenticazione, utenti, ruoli (superadmin, admin agenzia, membro), registro versionato delle variabili, configurazione per tenant. | Il master plan non lo prevedeva. | 2026-11-03 |
| DX-15 | Chi modifica le durate di retention | Decisa | Il superadmin modifica solo i default e solo entro l'intervallo minimo-massimo del contratto/DPA; l'agenzia sceglie solo dentro quell'intervallo. | Limite contrattuale verso le agenzie titolari. | 2026-11-03 |
| DX-16 | Intervallo ammesso per classe di retention | Decisa | Ogni classe ha un intervallo minimo-massimo come variabile protetta; fuori intervallo il valore non è valido. | Come DX-15. | 2026-11-03 |
| DX-17 | Variabile non leggibile o non valida | Decisa | Le azioni si bloccano (fail-closed); le cancellazioni programmate usano l'ultimo valore valido versionato; in entrambi i casi segnale ad A5. Primo avvio senza valore valido: DA-CV-17. | I dati non restano oltre la scadenza nota. | 2026-11-03 |
| DX-18 | Log degli accessi cross-tenant del superadmin | Decisa | Appartiene ad A6, schema unico; E1 e A1 lo usano. | Un solo proprietario. | 2026-11-03 |
| DX-19 | Visibilità del superadmin sui dati dei tenant | Decisa | Di default solo dati aggregati senza identificativi (gruppo minimo `access.aggregate_min_group_size_count`, almeno 2). Lettura di dati di un tenant solo per incidente dichiarato dal superadmin (abilitazione diretta) o su concessione dell'admin agenzia in una richiesta di assistenza; sempre con perimetro, durata (`access.superadmin_trace_access_ttl_hours`) e log (DX-18). Invariante. | Accesso entro le istruzioni del titolare. | 2026-11-03; 2026-11-04 |
| DX-20 | Autenticazione del superadmin | Decisa | Di A6; MFA obbligatoria per superadmin e admin di agenzia (invariante). | Accessi privilegiati. | 2026-11-03 |
| DX-21 | Nomi e responsabilità minori | Decisa | Nome unico `config_version` (nella whitelist del segmento decision di E1); `platform.config.changed` prodotto da A6; le classi senza durata (nodi ed edge del grafo, `outputs_ref`, contatori di rate limit, esiti di idempotenza, token consumati) le assegna F6; l'identità dell'attore la fornisce A6. | Coerenza tra documenti. | 2026-11-03 |
| DX-22 | Nessun valore hardcoded; catalogo delle variabili | Decisa | «TUTTO DEVE ESSERE CONFIGURABILE DA UI SUPERADMIN O ADMIN AGENZIA, NIENTE HARDCODED MAI!» Ogni variabile sta in `docs/catalogo-variabili.md` (unico punto di verità per nome, default, intervallo, chi modifica, pagina); i documenti di dettaglio citano solo il nome della variabile; responsabile del catalogo e del registro versionato (modello, ruoli, pagine) è A6. (a) Vincoli normativi: il limite di legge non è modificabile da UI e cambia solo con una nuova versione del catalogo collegata al registro delle norme; il valore operativo lo imposta il superadmin con motivazione e audit, entro i limiti (fissi non modificabili, minimi solo in aumento, massimi solo in diminuzione; giorni convertiti rispettando i valori legali). (b) Credenziali: pagina dedicata, separata per piattaforma e agenzia; archivio cifrato self-hosted UE; da UI solo inserimento o sostituzione, mai rilettura in chiaro (valori mascherati, con data dell'ultima rotazione); audit di ogni accesso e modifica; il superadmin non inserisce credenziali per un'agenzia (DA-CV-16); segreti di CI solo senza accesso a dati reali, in un account di test separato con inventario e rotazione; chiavi di produzione mai in CI. Eccezione: guardia `API_ENV` (DA-CV-11). | Decisione dell'utente. | 2026-11-03; 2026-11-04 |

---

## 2. Decisioni per documento (DA)

| ID | Titolo | Stato | Decisione o raccomandazione | Data |
|---|---|---|---|---|
| DA-A1-01 | Backend del grafo | Decisa | PostgreSQL con RLS; Neptune escluso; Neo4j solo se servono traversal pesanti | 2026-11-03 |
| DA-A1-02 | Fonte di verità dei mandati | Decisa (ipotesi di lavoro) | Il grafo come unica fonte in v2 | 2026-11-04 |
| DA-A1-03 | Trasporto eventi | Aperta | = DX-03; raccomandazione: Redis Stream | |
| DA-A1-04 | Allowlist dei tool nel grafo | Aperta | Rinviata a B2 (DA-B2-05) | |
| DA-A1-06 | Isolamento | Decisa (ipotesi di lavoro) | Istanza condivisa con RLS; istanza dedicata come opzione | 2026-11-04 |
| DA-A1-08 | Base giuridica degli identificativi degli admin nell'audit | Decisa | Per i dati delle agenzie la base è del titolare; per gli utenti di Gravya (superadmin, operatori) è di Gravya | 2026-11-03 |
| DA-A1-09 | Scritture del superadmin sul grafo | Decisa | Solo nodi di piattaforma, mai nodi di un'agenzia | 2026-11-04 |
| DA-A1-10 | Variabili prima di A6 (= DA-B1-09) | Decisa | Istantanea versionata nel repository, modificabile solo con PR, letta tramite una sola interfaccia (ripiego dichiarato rispetto a DX-22); «proposta da validare» vale come primo valore con segnale; «da definire» ha un valore di sviluppo dichiarato, ammesso solo fuori produzione | 2026-11-04 |
| DA-A1-11 | Integrità dell'audit delle mutazioni di A1 | Decisa | Nell'ondata 1 ruolo solo-inserimento e trigger contro UPDATE e DELETE; catena di hash da valutare con A5 | 2026-11-04 |
| DA-A3-01 | Motore di policy | Aperta | Raccomandazione: valutatore proprio, poi OPA solo locale | |
| DA-A3-02 | Topologia | Aperta | Vedi DX-06; raccomandazione: sidecar se OPA, altrimenti libreria | |
| DA-A3-03 | Granularità del bundle | Aperta | Raccomandazione: un bundle per tenant | |
| DA-A3-04 | Stato dinamico (spesa, token) | Aperta | Raccomandazione: passato da B2 nell'input | |
| DA-A3-07 | Allow se il record di decisione non si salva | Decisa | Fail-closed: l'azione si blocca | 2026-11-03 |
| DA-A3-08 | Propagazione dello stato di uno strumento di trasferimento (= DA-B2-08) | Decisa | A3 valuta sulla policy compilata da A2, come l'opt-in; B2 e l'egress-proxy di B1 applicano lo stesso esito; deny entro un ritardo massimo misurato, variabile del catalogo (da definire con A2 e A6), uguale in A3 e B2 | 2026-11-04 |
| DA-A3-09 | Invii verso terzi nell'ondata 1 (= DA-B2-10) | Decisa | (a) Negati nel bundle nell'ondata 1; (b) da D1-D4 la precondizione (base giuridica, mittente identificato, opposizione) la verifica il connettore; (c) B2 rifiuta argomenti senza `ai_generated` con `model` e `prompt_ref`, anche nel ciclo di tool di B1; (d) `audience` derivata dal catalogo dei tool di B2, un solo vocabolario in B2 e C1, flag per l'interazione diretta con persone (art. 50(1)) | 2026-11-04 |
| DA-B1-01 | Unità di isolamento | Aperta | Raccomandazione: un ambiente per job | |
| DA-B1-02 | Container o VM | Aperta | Raccomandazione: container con profilo di hardening per v2 | |
| DA-B1-03 | Launcher e trasporto | Aperta | Raccomandazione: launcher dedicato chiamato da arq | |
| DA-B1-04 | Rete laterale e DNS | Decisa | Uscita solo verso B2 ed egress-proxy; nessun resolver proprio del job: nomi risolti solo tramite egress-proxy o resolver interno con allowlist | 2026-11-03 |
| DA-B1-06 | Piattaforma di esecuzione | Decisa | Self-hosted su infrastruttura UE; sandbox gestite di terzi solo con approvazione esplicita | 2026-11-03 |
| DA-B1-08 | Superamento della quota di job | Decisa | Oltre la quota il job attende in coda; attesa massima come variabile del catalogo | 2026-11-04 |
| DA-B1-10 | Prompt e input del job senza accesso al DB | Decisa | C1 risolve il prompt da E2 e prepara l'input prima del submit; il job riceve `prompt_ref` e `input_ref` (classe dei payload sensibili temporanei) | 2026-11-04 |
| DA-B2-02 | Forma del confine | Decisa | Servizio HTTP separato con FastAPI (vedi DX-04, DX-06) | 2026-11-04 |
| DA-B2-03 | Contatori di rate limit | Aperta | Raccomandazione: Redis | |
| DA-B2-04 | Audit fail-open o fail-closed | Decisa | Fail-closed: se l'audit non si salva, l'azione si blocca | 2026-11-03 |
| DA-B2-05 | Origine dell'allowlist dei tool | Aperta | Da decidere con DA-A1-02 | |
| DA-B2-07 | Tool che inviano dati a terzi o fuori UE | Decisa | Ogni tool dichiara destinazione, giurisdizione, categorie di dati e sub-responsabile autorizzato (riferimento al DPA), anche UE; senza dichiarazione o autorizzazione deny. Extra-UE solo con opt-in dell'agenzia per destinazione, con strumento di trasferimento valido; lo stato dello strumento lo aggiorna il superadmin con fonte e audit; se cade, segnale ad A5 e disattivazione; riattivazione solo con nuovo opt-in. Vale anche per le chiavi dei provider LLM delle agenzie | 2026-11-03; 2026-11-04 |
| DA-B2-09 | Chiave di idempotenza oltre la finestra | Decisa | Chiave scaduta = errore per le scritture | 2026-11-04 |
| DA-B2-11 | Classi `ALWAYS_HITL` e `MONEY_WRITE` | Decisa | Vocabolario unico (sparisce `REQUIRES_HITL`); le altre azioni seguono `hitl.approval_required_default`; classe assegnata dal superadmin nel catalogo dei tool di B2, versionata e auditata; si può solo aggiungere, toglierla richiede la seconda persona con accesso superadmin; tool senza classe in `require_approval` | 2026-11-04 |
| DA-C1-01 | Motore dei workflow | Decisa | LangGraph come motore unico, libreria self-hosted | 2026-11-03 |
| DA-C1-03 | Condizioni sugli edge | Aperta | Raccomandazione: JSON dichiarativo | |
| DA-C1-05 | Servizi gestiti di LangGraph | Decisa | Solo la libreria open source; niente LangSmith né LangGraph Platform | 2026-11-03 |
| DA-C1-07 | Marcatura leggibile da macchina del testo (art. 50(2)) | Decisa con condizione | Rinviata alla lettura del Codice di buone pratiche, da fare prima del primo rilascio in produzione (art. 50 dal 2.8.2026); vedi §4 | 2026-11-04 |
| DA-C1-08 | Cancellazione di stato e checkpoint | Decisa | Cancellazione delle righe riferite all'interessato nei run chiusi | 2026-11-04 |
| DA-C1-09 | `c1.max_duration_ms` e attese HITL | Decisa | Misura solo l'esecuzione, escluse le attese HITL | 2026-11-04 |
| DA-C3-04 | TTL delle richieste HITL | Decisa | Default 24 h, intervallo 1-168 h fissato dal superadmin; l'admin agenzia sceglie entro l'intervallo | 2026-11-03 |
| DA-C3-06 | Chiamata parcheggiata nelle tracce | Decisa | Solo identificativi e HMAC degli argomenti | 2026-11-03 |
| DA-C3-07 | Modifica del TTL e richieste aperte | Decisa | Una riduzione vale subito, un aumento solo per le nuove richieste | 2026-11-04 |
| DA-C3-08 | Chiusura per TTL | Decisa | Scadenza programmata con l'ultimo valore valido (DX-17) e segnale ad A5; porta solo alla non esecuzione | 2026-11-04 |
| DA-C3-09 | Override della retention per agenzia | Decisa | Nel modello; attivo solo quando l'intervallo del DPA è definito (F6) | 2026-11-04 |
| DA-C3-10 | Chi decide una richiesta HITL | Decisa | Nell'ondata 1 solo l'admin agenzia, senza auto-approvazione; con un solo admin può approvare un proprio run rifacendo la MFA, e l'audit la marca come auto-approvazione | 2026-11-04 |
| DA-C3-11 | Scheduler dello sweeper | Decisa | Job interno al servizio di orchestrazione | 2026-11-04 |
| DA-C3-12 | Hash degli argomenti (= DA-E1-09) | Decisa | HMAC-SHA-256 con chiave per tenant nella pagina credenziali, rotazione a due chiavi (DA-CV-23); la distruzione della chiave rende l'hash non riconducibile; E1 registra solo l'hash del template di E2 | 2026-11-04 |
| DA-E1-02 | Contenuti di prompt e risposte nelle tracce | Decisa | Mai in produzione (invariante); un opt-in futuro richiederebbe DPIA e parere legale | 2026-11-03 |
| DA-E1-03 | Storage delle tracce | Decisa (ipotesi di lavoro) | Lo stesso PostgreSQL di v2, partizionato; niente SaaS né extra-UE | 2026-11-04 |
| DA-E1-04 | Retrieval e decisioni | Decisa (ipotesi di lavoro) | `kind` dedicati (retrieval, decision) | 2026-11-04 |
| DA-E1-05 | GenAI semantic conventions e `traceparent` | Decisa | Solo come vocabolario, senza SDK né export OTel | 2026-11-03 |
| DA-E1-07 | Tracce e audit A5 | Decisa (ipotesi di lavoro) | Tabelle separate, collegate da `trace_id` | 2026-11-04 |
| DA-E1-10 | Scrittura per più tenant | Decisa | Writer senza bypass di RLS, tenant impostato per transazione, `WITH CHECK` | 2026-11-04 |
| DA-E1-11 | Aggregati al superadmin | Decisa | Imposti da viste e ruolo DB senza accesso alle tabelle base | 2026-11-04 |
| DA-E1-12 | Attribuzione di prompt, modello e `config_version` a un'azione irreversibile | Decisa | L'audit fail-closed di B2 e A5 porta solo identificativi e hash; E1 resta fail-open | 2026-11-04 |
| DA-E1-13 | Elenchi chiusi per gli identificativi generici della whitelist di E1 (`opaque_id`, `model_identifier`, `name`, `destination`, `exec_code`) | Decisa | (a) valori dai cataloghi esistenti per modelli, provider, strumenti e agenti (B1, B2) e (b) UUID per gli identificativi generati da Gravya, insieme; il solo controllo di formato è ammesso solo nell'ondata 1 con dati sintetici | 2026-11-05 |
| DA-E2-01 | Modello dati del registry | Aperta | Raccomandazione: tabelle `prompts`, `prompt_versions`, `prompt_activations` | |
| DA-E2-02 | Motore di template | Aperta | Raccomandazione: sostituzione `{{var}}` senza logica | |
| DA-E2-03 | Prompt da migrare | Aperta | Raccomandazione: perimetro del registry v2; preambolo e avvisi art. 50 restano nel codice | |
| DA-E2-04 | Promozione di una versione di prompt | Decisa in parte | Gate E3 obbligatorio: E3 produce in CI un esito registrato (versione, hash, esito, data) che E2 verifica all'attivazione; E2 non chiama E3 a runtime. Aperta: approvazione via C3 per le versioni scritte da umani | 2026-11-04 |
| DA-E2-07 | Versioni proposte dall'AI | Decisa | Candidate, mai attivabili senza un umano: gate E3 e approvazione via C3 | 2026-11-03 |
| DA-E2-08 | Seed dei prompt | Decisa | Testi di gravya-app come bozza, rivisti sui contratti v2 e ripuliti dalla visione precedente | 2026-11-03 |
| DA-E2-09 | Superadmin e template dei tenant | Decisa | Di default solo metadati aggregati; lettura, attivazione e rollback di un prompt di un'agenzia solo come DX-19 (incidente dichiarato o concessione in una richiesta di assistenza), con perimetro, durata e log | 2026-11-04 |
| DA-E2-10 | Cache dei prompt | Decisa | Cache in-process | 2026-11-04 |
| DA-E2-11 | Cancellazione di versioni immutabili | Decisa | Solo dal ruolo di retention di F6, con audit | 2026-11-04 |
| DA-E3-01 | Primo bersaglio del dataset | Aperta | Raccomandazione: gate sul workflow thin-slice C1 | |
| DA-E3-02 | Linguaggio del runner | Decisa | Python (DX-04); posizione nell'ossatura del repository | 2026-11-04 |
| DA-E3-03 | Controlli soggettivi in CI | Aperta | Raccomandazione: nel gate solo controlli deterministici; giudice LLM come segnale | |
| DA-E3-04 | Date relative | Aperta | Raccomandazione: nuovo seed a ogni run | |
| DA-E3-05 | Non determinismo del modello | Aperta | Raccomandazione: un run per iniziare | |
| DA-E3-07 | Soglia del gate | Decisa | Zero fallimenti sui casi bloccanti (invariante); sugli altri solo report (`eval.gate.pass_rate_min_percent` a 0) | 2026-11-04 |
| DA-E3-08 | Dati nei casi di eval | Decisa | Solo dati sintetici | 2026-11-03 |
| DA-E3-09 | Giudice LLM e piattaforme di eval | Decisa | Niente SaaS di eval; giudice LLM solo con elaborazione nell'UE | 2026-11-03 |
| DA-E3-11 | Dove gira la CI di E3 | Decisa | GitHub finché i dati sono sintetici e i segreti sono di un progetto di test separato | 2026-11-04 |

**DA chiuse da altre decisioni** (per ritrovarle dai documenti): DA-E1-01 e DA-B1-05 da DX-02; DA-E2-05, DA-E3-06, DA-A1-05, DA-A3-05 (`_scope_enforcement.py` solo riferimento per i test), DA-B2-01 (gateway nuovo), DA-C1-02 (anche la pipeline agentica è una WorkflowDefinition), DA-C1-04, DA-C3-01 da DX-01; DA-C3-02 da DA-C1-01 (nodo HITL solo in LangGraph); DA-C3-03 da DX-04; DA-E1-08 da DX-19; DA-E1-06, DA-E2-06, DA-E3-10, DA-A1-07, DA-A3-06, DA-B1-07, DA-B2-06, DA-C1-06, DA-C3-05 assorbite da DX-09. **Alias:** DA-B1-09 = DA-A1-10; DA-B2-08 = DA-A3-08; DA-B2-10 = DA-A3-09; DA-E1-09 = DA-C3-12.

---

## 3. Escalation

Nessuna.

---

## 4. Da riportare (punti aperti)

Rilievi e lacune ancora aperti, con i documenti da aggiornare. Fonti nei report in `docs/revisioni/`.

- **Diritto del marketing nei documenti.** PV-01 è esteso a comunicazioni elettroniche e marketing (ePrivacy, Codice privacy artt. 122 e 130); restano da aggiornare D1-D4, C3, A3, B2 e DX-11.
- **Ambito NIS2 non accertato sul piano normativo.** Mancano il confronto del criterio dimensionale con la Raccomandazione 2003/361/CE, la definizione di «incidente significativo di base» (Det. ACN 379907/2025, Allegati 3 e 4) e i termini della coorte. Nei documenti vanno riportati relazione finale entro un mese, destinatario CSIRT Italia, decorrenza dalla conoscenza e valutazione trimestrale degli incidenti ricorrenti. Documenti: DX-10, A5, A3, C1, C3, B1, B2, E2.
- **Data Act.** Qualificazione del SaaS come «servizio di trattamento dei dati», da confermare con un legale. Documenti: §5, F6.
- **Calendario AI Act dopo il Reg. 2026/1744.** Da riportare in DX-11, C3, A1, A3, B1, E1, E2, E3 (art. 50 dal 2.8.2026; artt. 12, 14, 19, 26 per l'alto rischio dal 2.12.2027).
- **Fonte degli obblighi sui log.** Per i log la fonte è il Reg. 2024/2690 (allegati 3.2 e 11.3), valido solo se Gravya è in ambito, non l'art. 21 NIS2; correggere C3, E1, E2 dove citano «NIS2 (art. 21)».
- **Data Privacy Framework.** Copre solo le organizzazioni USA nell'elenco DPF; per le altre serve un altro strumento dell'art. 46. Documenti: DA-B2-07, B2, C3, E1, DPA.
- **Linee guida EDPB 01/2025.** Solo in consultazione: non citarle come requisito (E1, C3).
- **Valori aperti delle variabili.** `_min` e `_max` delle durate (DA-CV-01; anche la vigenza del riferimento di sei mesi per il log cross-tenant); termine verso l'agenzia per le violazioni (DA-CV-08); tempo massimo di valutazione iniziale (`incident.initial_assessment_max_hours`); termine di assistenza del responsabile agli interessati (art. 28(3)(e)); intervalli minimo-massimo di `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms`, `e2.cache.max_ttl_s`, `access.aggregate_min_group_size_count` (minimo 2), tentativi prima del blocco, durata della sessione, durata dell'accesso del superadmin, minimi operativi dei segnali `incident.*`; `retention.pseudonym_map_months` (la cancellazione richiesta dal titolare deve eliminare la riga della mappa entro il termine del DPA). Documenti: A5, A6, F6, catalogo.
- **E1, valori provvisori.** Valori di produzione e intervalli delle variabili `e1.write_*` e di `e1.attributes.max_value_bytes`; chiave HMAC minima e `reviewer_ref` da confermare con A6; campi dei segnali per tipo di evento con A5.
- **E1, chiusura della v1.8.** Rilievi della revisione di E1 v1.8 e catalogo v1.6 e della verifica del giro 4 (`docs/revisioni/e1-v1.8/`, `docs/revisioni/impl-e1/report-code-reviewer-giro4.md`), in chiusura con il giro unico (§6).
- **Cancellazione con una nuova versione non leggibile e durata più lunga.** Da documentare come limite (DX-17). Documenti: F6, catalogo §2.
- **Catalogo, stati da correggere.** Le righe `incident.*` con valori dal regolamento vanno indicate come «vincolo normativo», non «deciso»; le righe con «proposta da validare» senza valore (`a3.*`, `b1.job.*`, `b1.*.max_concurrent_jobs`, `b2.rate_limit.*`, `eval.run.*`, `eval.ingestion.timeout_s`) vanno indicate «da definire».
- **«Legal hold» ancora citato.** Sostituito dalle evidenze di incidente (§5), ma ancora in B1 §7, C3 §7, E2 §7; catalogo §16 da completare.
- **Finestra del rate limit di B2.** `b2.rate_limit.default_calls_per_minute` presuppone il minuto senza dichiararlo (B2, catalogo §7).
- **Metrica del gate E3.** Da verificare che «100% dei casi di fermata» (C3 §10) e «zero casi bloccanti falliti» (E3 AC4) siano la stessa metrica.
- **Registro delle norme.** Da integrare: sub-responsabili (GDPR art. 28(2) e (4)) e Det. ACN 379907/2025, Allegati 3 e 4.
- **Variabili di marketing.** Il catalogo deve dichiarare che consensi, opt-out, liste di soppressione e tracciamento sono rinviati a D1-D4.
- **Incidenti ricorrenti.** Il registro dice «trimestralmente»; il catalogo lo presenta come massimo di legge (89 giorni): tenerlo come scelta di progetto da confermare con un legale o dichiararlo diversamente.
- **Nomi `retention.<classe>.tenant_value`.** Da allineare con `retention.tenant.<classe>` del catalogo e da dire quali classi sono per agenzia (log cross-tenant, evidenze e segnali di incidente in tensione con C2 e C10).
- **Canali CSIRT.** Elenco chiuso dei canali ufficiali da definire; il Portale dei Servizi ACN va riverificato.
- **Sottoprodotto per i dati del miglioramento del servizio (G1, opzione (a)).** Creare o no un sottoprodotto dedicato: non necessario per H1-H3, resta da decidere.
- **`API_ENV` assente.** Oggi il codice di E1 e il catalogo §18 lo trattano come sviluppo, con segnale: comportamento non deciso dall'utente.
- **Partizioni di E1 (E14).** Da confermare in F6.
- **Marcatura del testo (DA-C1-07).** Lettura del Codice di buone pratiche prima del primo rilascio in produzione. Documenti: C1, C3, E2, D1-D4.

---

## 5. Durate di default (DX-09)

Approvate come default il 2026-11-03. Sono variabili di piattaforma di sola lettura finché l'intervallo minimo-massimo del contratto/DPA non è definito (DA-CV-01); poi modificabili solo entro l'intervallo (DX-15, DX-16). Nessuna norma fissa un valore per questi dati: sono scelte di minimizzazione (GDPR art. 5(1)(e)) bilanciate con l'indagine sugli incidenti; i 6 mesi dell'art. 19 AI Act sono solo buona pratica (DX-11). Resta consigliata una verifica legale e sui contratti con le agenzie.

| Classe di dati | Esempi | Durata | Motivo |
|---|---|---|---|
| Tracce operative (metadati) | `gravya_traces`, segmenti (E1) | 90 giorni | Debug e costi; nessun contenuto (DA-E1-02) |
| Eventi di runtime | eventi di B1, `workflow.*` (C1), `graph.*` (A1) | 90 giorni | Come le tracce |
| Audit e decisioni | audit dei tool (B2), decisioni (A3), mutazioni (A1), HITL (C3), attivazioni dei prompt (E2) | 12 mesi | Indagine sugli incidenti e accountability |
| Log di accesso cross-tenant | accessi del superadmin (E1, DX-18) | 12 mesi | Controllo dell'operato del responsabile |
| Payload sensibili temporanei | argomenti delle chiamate parcheggiate (C3), anteprime redatte (B2) | 30 giorni dopo la decisione o l'esecuzione; nell'audit resta solo l'hash | Minimizzazione |
| Stato dei run e checkpoint | stato LangGraph, checkpoint B5 | 30 giorni dopo la chiusura del run | Ripresa e replay |
| Evidenze di incidente | dati collegati a un incidente aperto da A5 | Durata del caso + 12 mesi, con sospensione delle altre scadenze; con massimo, riesame periodico ed elenco chiuso delle categorie (valori in F6); sospensione non attivabile finché non sono definiti; solo per i dati di Gravya, per quelli delle agenzie serve un'istruzione nel DPA e un parere legale (DA-CV-21); meccanismo da definire in F6 e A5 | Relazione finale NIS2 (progettazione ready by design), difesa in giudizio (GDPR art. 17(3)(e)), accountability (art. 5(2)) |
| Artefatti di configurazione | versioni di prompt, bundle, workflow (attore pseudonimo) | Durata del servizio | Riproducibilità, senza dati personali in chiaro |
| Report di eval | report CI, segmenti eval_case | 12 mesi | Storico delle regressioni, dati sintetici |
| Dati dell'agenzia a fine contratto | tutti i dati del tenant | Periodo di recupero di almeno 30 giorni dalla fine del periodo di passaggio, poi cancellazione, salvo obblighi di legge; scelta restituzione o cancellazione dell'agenzia (DA-CV-12) | Data Act art. 25(2)(g)-(h), da confermare la qualificazione del SaaS; GDPR art. 28(3)(g) |

Valori per agenzia: `retention.<classe>.tenant_value` (admin agenzia, entro l'intervallo, con MFA e audit), attivi con l'override per agenzia (DA-C3-09). Da verificare nella validazione: compatibilità con i contratti delle agenzie; obblighi di conservazione di settore dei clienti (a carico del titolare); conflitto tra cancellazione su richiesta e audit di 12 mesi (proposta: pseudonimizzare l'attore e conservare solo l'hash).

---

## 6. Regole trasversali di progetto

| Tema | Documenti | Decisione e motivo | Data |
|---|---|---|---|
| Fail-closed dell'audit delle mutazioni di A1 | A1, A5 | Audit nella stessa transazione, rollback se fallisce | 2026-11-03 |
| Mutazioni del grafo A1 | A1, E1, A5 | Solo eventi di audit (tabella di audit, poi A5), conservazione 12 mesi; se la mutazione avviene dentro un run, collegamento alla traccia tramite `trace_id`. Non diventano segmenti E1 | 2026-11-03 |
| Coda locale e audit dell'esito | B2, A3, C1 | Una coda conta come «salvato» solo se durevole su disco con fsync; se l'audit dell'esito fallisce dopo l'esecuzione, segnale ad A5 e coda di recupero | 2026-11-03 |
| Conferma del salvataggio nell'ondata 1 | A3, B2, E1 | Tabella di audit minima già nell'ondata 1, poi assorbita da A5 (per E1 è la tabella provvisoria dei segnali) | 2026-11-03 |
| Latenza di A3 | A3, B2 | Budget separati, proposte da validare con misura: valutazione p99 ≤ 5 ms, salvataggio sincrono p99 ≤ 20 ms, totale p99 ≤ 25 ms; record di A3 e audit `tool.invoked` di B2 in un'unica transazione eseguita da B2; soglie come variabili per gli alert, non per bloccare | 2026-11-03 |
| Egress-proxy di B1 | B1, B2 | Segue la regola delle destinazioni dichiarate (DA-B2-07) | 2026-11-03 |
| Opt-in extra-UE | B2, A1, A3, A6 | Nella configurazione per tenant di A6, impostata dall'admin dell'agenzia, versionata e auditata, per destinazione dichiarata (DA-B2-07); A2 la compila, A3 la valuta, B2 la applica; il superadmin non la attiva al posto dell'agenzia | 2026-11-03; 2026-11-04 |
| Etichetta «generato da AI» (art. 50) | C1, C3, D1-D4 | Campo obbligatorio `ai_generated` con `model` e `prompt_ref` nell'output dei nodi agent; C3 lo mostra all'approvatore; i connettori applicano disclosure e marcatura per canale, anche leggibile da macchina per il testo (art. 50(2)), nei limiti del canale. Attiva di default e non disattivabile dal tenant per i contenuti verso terzi; eccezioni dell'art. 50 solo dopo verifica legale. Informativa a chi interagisce con un'IA alla prima interazione (art. 50(1)) come invariante | 2026-11-03; 2026-11-04 |
| Dove gira LangGraph | B1, C1 | In B1 solo i nodi agente con il loro ciclo di tool (un job effimero per nodo); il grafo C1 gira nel servizio di orchestrazione con il checkpointer B5. Motivo: attese HITL lunghe, job senza accesso al DB, isolamento dove esegue codice guidato dall'LLM | 2026-11-03 |
| Report CI su GitHub | E3 | Report minimi senza dati personali (dati sintetici), oppure CI self-hosted | 2026-11-03 |
| Catalogo delle variabili nei giri dei documenti | Tutti, catalogo | I doc-writer dei singoli documenti non scrivono nel catalogo: elencano le variabili nella risposta e il coordinator le unisce | 2026-11-04 |
| Valutazione iniziale di un evento sospetto | A5, DX-10 | Variabile di progetto (non di legge) con un tempo massimo; valore da definire (§4). Motivo: la conoscenza che fa decorrere i termini segue la valutazione | 2026-11-04 |
| Cifratura, backup e chiave del provider LLM (E11) | A6, F6, B1, E1, E2 | Cifratura a riposo e in transito e gestione delle chiavi ad A6; backup a F6 (DA-CV-22); la chiave del provider LLM non entra nel job di B1: le chiamate passano dall'egress-proxy, che aggiunge la chiave e non registra corpi né URL completi | 2026-11-04 |
| Sub-responsabili (E12, GDPR art. 28(2)) | B2, A6, F6 | A ogni cambio di destinazione o sub-responsabile parte un'informativa alle agenzie; un'agenzia può opporsi e da allora il tool è negato per lei | 2026-11-04 |
| Partizioni di E1 e retention per agenzia (E14) | E1, F6 | Una partizione si elimina solo quando tutte le sue righe sono scadute per i rispettivi tenant, altrimenti cancellazione per riga; da confermare in F6 (§4) | 2026-11-04 |
| Data Act e trasferimenti (E15) | §5, F6, B2, E1, E2 | Condizionato alla qualificazione del SaaS come «servizio di trattamento dei dati» (da confermare con un legale): termini dell'art. 25 (periodo transitorio fino a 30 giorni, preavviso massimo di due mesi, alternativa fino a sette mesi) nel catalogo come vincoli; costi di passaggio a zero dal 12.1.2027 (art. 29) come invariante. Verifica di uno strumento di trasferimento con data e scadenza (`transfer.instrument_review_interval_days`, massimo 365 giorni): alla scadenza lo stato non è valido, l'opt-in si disattiva, segnale ad A5. Verifica periodica dell'ambito NIS2 (`incident.scope_review_interval_days`, massimo 365 giorni, criteri art. 3 d.lgs. 138/2024) | 2026-11-04 |
| Strumento di esportazione dei dati di un tenant (E15) | F6; dichiarazioni in E1, E2, A1, A3, B1, B2, C1, C3, E3 | Previsto sin da subito, responsabile F6. Formato: archivio ZIP con dati in JSON e JSON Schema per tipo; JSON Lines per volumi grandi; CSV per tabelle semplici; formati di settore (vCard, iCalendar, EML); file originali così come sono; manifest con elenco, schemi e hash. Ogni documento che conserva dati di un tenant dichiara cosa è esportabile | 2026-11-04 |
| Vocabolario degli esiti HITL (F4) | C3, E1 | Stati `requested`, `approved`, `rejected`, `input_provided`, `expired`, `cancelled`, `executed`; risultato di esecuzione `ok`, `refused`, `error`. C3 si allinea | 2026-11-04 |
| Approvazione per l'implementazione | E1, A1 | E1 e A1 approvati come base dell'implementazione; le righe decise di questo registro (per esempio DX-07, DA-A1-11) prevalgono sul testo e si applicano nel codice. Gli altri sette documenti dell'ondata 1 restano in verifica | 2026-11-04 |
| Miglioramento del servizio, H1 | E1, E3, E4, E6 | Da subito solo metadati aggregati senza identificativi dell'agenzia (latenze, errori, costi, tassi di rifiuto HITL, esiti delle valutazioni, già raccolti da E1 senza contenuti) e dati sintetici di E3, senza gate né clausole particolari; collocazione in E6 ed E4 | 2026-11-04 |
| Miglioramento del servizio, H2 | A6, F6, E2, E3, B2, DPA | Livello 1 (ondata 2): opt-in per agenzia; i contenuti migliorano solo i prompt e workflow di quell'agenzia, senza uscire dal tenant. Livello 2 (banca dati tra tenant con gate di anonimizzazione, solo con opt-in): ondata 3, con clausola nel DPA, gate senza chiave anche sugli identificativi indiretti, nessun metadato che leghi il dato all'agenzia, test di re-identificazione, valutazione con legale o DPO. Progettato in v2 da zero (in gravya v1 non esiste un meccanismo di anonimizzazione), senza dichiarare anonimi i dati | 2026-11-04; 2026-11-05 |
| Pseudonimizzazione prima dell'invio a un LLM, H3 | B2, B1, E2, A6 | Ondata 2. Funzione di minimizzazione, non rende conforme un LLM che non lo è: per un LLM extra-UE restano opt-in per destinazione e strumento di trasferimento. Motore locale preferito; Mistral (UE) ammesso come sub-responsabile dichiarato. Tabella di corrispondenza nel tenant con chiave dell'agenzia e durata dei payload sensibili; passo facoltativo per destinazione, attivato dall'admin agenzia, in B2 e nell'egress-proxy di B1. Riferimento tecnico: la pipeline di rilevamento e sostituzione di gravya v1 (`services/pii-redactor`), che produce pseudonimizzazione | 2026-11-04; 2026-11-05 |
| E1: segnali e C2 nell'ondata 1 | E1, A5, catalogo §18 | Deroga solo per l'ondata 1: i segnali sono sempre prodotti; sono conservati nella tabella provvisoria quando è scrivibile, altrimenti nel log locale di ripiego. La conservazione garantita è requisito di A5 (ondata 2). Motivo: temporanea, solo dati sintetici | 2026-11-05 |
| E1: tabella provvisoria dei segnali | E1, A5 | Solo inserimento per il ruolo di scrittura, insieme chiuso unico dei campi (per tipo di evento con A5) | 2026-11-05 |
| E1: identificativi e chiavi | E1, A6, B1, C1 | `run_id` è un UUID canonico generato da Gravya (da recepire in B1 e C1); `gravya.decision.reviewer_ref` è un prefisso fisso più UUID canonico; chiavi HMAC lette da un'interfaccia fino ad A6, lunghezza minima 32 byte come invariante provvisoria (catalogo §18); formati stretti per campo come invarianti della whitelist versionata, fino all'attuazione di DA-E1-13 | 2026-11-05 |
| E1: vocabolari della whitelist | E1, B2, catalogo §18 | `status`, `name` per `kind`, formati di `execution_ticket_id`, `workflow_*`, `retention_class` e dei campi `gen_ai.*` sono provvisori nella whitelist `redaction_version` 1 e descritti in E1; esito del tool in `gravya.tool.outcome` (`ok`, `denied`, `approval_required`, `rate_limited`, `error`), da scrivere anche in B2. Criterio 16 parziale finché E2 non esiste: `gravya.prompt.hash` accettato solo con chiave e versione del prompt | 2026-11-05 |
| E1: scrittura e parametri | E1, catalogo §9 | Scrittura asincrona con coda di `e1.write_buffer_size` segmenti e thread con connessione propria; tempo massimo di collegamento `e1.write_connect_timeout_s` in secondi interi, minimo 2 (libpq legge secondi interi). Valori di sviluppo nell'istantanea: buffer 100, `e1.attributes.max_value_bytes` 2048. Scelte tecniche: `pyproject.toml`, Alembic, psycopg 3, pytest, istantanea JSON, layout `src/gravya_e1` | 2026-11-05 |
| E1: robustezza della scrittura e ruoli del database | E1, A5, A6, catalogo §9 | Timeout lato client sulla connessione di scrittura con `tcp_user_timeout` da `e1.write_tcp_user_timeout_ms` («da definire»); `close()` senza attese illimitate; segnali con coda, thread e connessione propri, con gli stessi limiti di tempo; ruolo di migrazione senza appartenenza al ruolo con `BYPASSRLS` dopo le migrazioni e migrazioni senza errori inghiottiti; funzione di controllo del `trace_id` chiusa (niente oracolo né blocco delle tracce altrui; E1 dichiara il limite residuo: con il tenant della sessione si può ancora sapere se un `trace_id` esiste presso un altro tenant); `production_override` può solo irrigidire la guardia | 2026-11-05 |
| E1: ambiente e avvio | E1, B1, E3, A6, catalogo §18 | `API_ENV` in un insieme chiuso (`production`, `development`, `test`): un valore fuori insieme blocca l'avvio con segnale. Tenant di contesto dell'helper obbligatorio solo con `API_ENV=production` reale; `production_override` da solo non lo attiva; fuori produzione è facoltativo, con segnale. Una variabile «da definire» mancante in produzione impedisce l'avvio, con segnale; il fail-open delle tracce vale solo per i guasti a runtime (PV-01) | 2026-11-05 |
| E1: condizione prima dei dati reali | E1 §9 | Nessun dato reale di un'agenzia prima dell'attuazione di DA-E1-13, dei segnali durevoli di A5 e di una procedura di installazione approvata. Motivo: le deroghe a C2 e a DA-E1-13 valgono solo con dati sintetici | 2026-11-05 |
| E1: chiusura della v1.8 | E1, catalogo | In corso un giro unico: codice (giro 5 su `claude/impl-e1`), E1 v1.9 e catalogo v1.7, poi verifica mirata di code-reviewer, plan-auditor e compliance-auditor | 2026-11-05 |
| Registro delle decisioni: solo correnti | Tutti | In DECISIONS.md solo decisioni in vigore e aperte, nella forma corrente, con il motivo utile sulla riga. Quando una decisione cambia, la versione superata va in coda a [decisioni-archivio.md](decisioni-archivio.md) nello stesso commit. Testi dell'utente: archivio, sezione «2026-11-05 — testi dell'utente» | 2026-11-05 |
| Istruzioni di sessione e memoria | CLAUDE.md, `stato/` | Le istruzioni su avvio, cartella `stato/` e chiusura dei turni stanno solo in `CLAUDE.md`; la memoria della piattaforma sarà eliminata dall'utente dopo la ricopiatura dei prompt | 2026-11-05 |

---

## 7. Catalogo delle variabili (DA-CV)

| ID | Titolo | Decisione e motivo | Stato |
|---|---|---|---|
| DA-CV-01 | Intervalli minimo-massimo delle durate di retention | Durate di sola lettura finché l'intervallo del DPA non è definito; poi modifiche solo entro l'intervallo. Valori `_min` e `_max` aperti (§4) | Decisa (2026-11-04) |
| DA-CV-02 | Intervalli delle variabili non di retention | Per ora validità tecnica (tipo, positivo, minimo ≤ massimo) più regole relazionali: TTL di un token non oltre la vita del run o il TTL HITL; retention delle tracce non inferiore all'intervallo di partizione | Decisa (2026-11-04) |
| DA-CV-03 | Sweeper, code, durata dei token | Valori fissati con misura, con il ritardo massimo tra scadenza e chiusura o cancellazione come criterio; escluse le opzioni (b) e (c), la seconda perché contraddice DX-22 | Decisa (2026-11-04) |
| DA-CV-04 | Soglie e campioni di test | Nel catalogo solo le soglie con metrica a runtime; i campioni dei test restano parametri dei test, con rimando al catalogo | Decisa (2026-11-04) |
| DA-CV-05 | Invarianti di sicurezza e formati | «Configurabile non vuol dire disattivabile»: invarianti (catalogo §18) MFA, fail-closed, deny per destinazione non dichiarata, nessun contenuto nelle tracce in produzione, solo dati sintetici nei test, etichetta «generato da AI» non disattivabile, `approval_token` monouso (il `run_token` vale per tutto il run), destinatario CSIRT Italia, controllo dei dati personali nei template E2 sempre «block», zero fallimenti bloccanti nel gate E3, approvazione sempre obbligatoria per `ALWAYS_HITL` e `MONEY_WRITE`, HMAC-SHA-256 con chiave per tenant, whitelist di E1, header e `traceparent`, exit code di E3, regole di rete 169.254.0.0/16, `synthetic: true` | Decisa (2026-11-04) |
| DA-CV-06 | Rate limit, quota B1, opt-in extra-UE | Limiti indipendenti per agente, tool e tenant, vince il più restrittivo; quota B1 per tenant in job concorrenti; opt-in extra-UE per destinazione (DA-B2-07) | Decisa (2026-11-04) |
| DA-CV-07 | Soglie dei segnali verso A5 | Vivono in A5; i segnali partono senza soglia locale (criteri esaustivi del Reg. 2024/2690) | Decisa (2026-11-04) |
| DA-CV-08 | Termine verso l'agenzia per una violazione di dati personali | Obbligo contrattuale del DPA, non l'art. 33(1); le 72 h valgono solo per i dati di cui Gravya è titolare; righe GDPR attive anche a flusso NIS2 spento. Valore aperto (§4) | Decisa (2026-11-04) |
| DA-CV-09 | Spegnimento di `incident.nis2_flow_active` | Solo con valutazione scritta di un legale o del DPO e approvazione di entrambe le persone con accesso superadmin; variabile non leggibile = flusso attivo, con segnale; variabile di verifica periodica dell'ambito (A5); attivazione anche al contratto con un'agenzia soggetta NIS2; esclusa l'opzione «solo motivazione e audit» (C2) | Decisa (2026-11-04) |
| DA-CV-10 | Attivazione di `retention.class_override_enabled` | Solo con l'intervallo della classe definito | Decisa (2026-11-04) |
| DA-CV-11 | Guardia `API_ENV` | Invariante di deploy, non variabile da UI (una guardia modificabile da UI non protegge la produzione); per E1 vedi §6 | Decisa (2026-11-04) |
| DA-CV-12 | Scelta a fine contratto | Sempre disponibile all'agenzia, indipendentemente dall'override per agenzia; se non sceglie, export per tutto il periodo di uscita, poi cancellazione | Decisa (2026-11-04) |
| DA-CV-13 | `run_token` e `tool_grant_ref` | Un solo token, emesso da B1 e verificato da B2 | Decisa (2026-11-04) |
| DA-CV-14 | Fatturato per `incident.financial_loss_turnover_percent` | Valore versionato con attore e documento di origine; nel dubbio vale il più basso noto | Decisa (2026-11-04) |
| DA-CV-15 | Default di `hitl.approval_required_default` | Default di piattaforma in sola lettura (vero); `ALWAYS_HITL` e `MONEY_WRITE` non declassabili da UI | Decisa (2026-11-04) |
| DA-CV-16 | Credenziali per conto di un'agenzia | Il superadmin non le inserisce mai | Decisa (2026-11-04) |
| DA-CV-17 | Nessun valore valido (primo avvio) | Vale il valore «deciso» del catalogo; segnali, audit e notifiche esclusi dal blocco; classi di retention «da definire» non si scrivono in produzione finché A6 o F6 non fissano un valore | Decisa (2026-11-04) |
| DA-CV-18 | Contenuti verso terzi e `ALWAYS_HITL` | Nell'ondata 1 non sono `ALWAYS_HITL`: decide l'admin agenzia con audit; da riesaminare con D1-D4 | Decisa (2026-11-04) |
| DA-CV-19 | Strumento di trasferimento e sub-responsabile per destinazione | Li imposta il superadmin con fonte e audit; l'agenzia attiva l'opt-in solo su destinazioni con entrambi validi | Decisa (2026-11-04) |
| DA-CV-20 | Classi senza durata | Tetto provvisorio fissato dall'utente prima dell'avvio in produzione; l'ondata 1 non va in produzione | Decisa (2026-11-04) |
| DA-CV-21 | Sospensione per evidenze di incidente | Solo per i dati di Gravya; per quelli delle agenzie istruzione nel DPA e parere legale prima di F6 | Decisa (2026-11-04) |
| DA-CV-22 | Backup e cancellazioni | I backup scadono entro `retention.data_backup_days`, non oltre il massimo delle classi contenute; al ripristino le cancellazioni già eseguite si riapplicano | Decisa (2026-11-04) |
| DA-CV-23 | Sostituzione delle chiavi HMAC e di firma | Due chiavi valide in parallelo, con data di attivazione e disattivazione | Decisa (2026-11-04) |
