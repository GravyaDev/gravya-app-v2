# Registro delle decisioni aperte

Ultimo aggiornamento: 2026-11-03, ondata 1. Prevalgono i principi vincolanti in [PRINCIPI.md](PRINCIPI.md).

Ogni decisione aperta nasce in un documento di dettaglio, nell'Appendice C, ed è numerata `DA-{ID}-NN`. Qui sono raccolte in un unico punto. Quando una decisione viene presa, si compilano le colonne **Scelta**, **Motivo** e **Data**, e si aggiorna il documento di origine con una nuova riga nello Storico modifiche.

Stati possibili:
- **Aperta**: manca la scelta.
- **Escalation**: senza una decisione di business (Daniele) non si procede.
- **Decisa**: la scelta è stata fatta.

---

## 1. Decisioni trasversali, da prendere per prime

Queste decisioni non sono in nessun singolo documento. Ricorrono in più documenti, e a volte i documenti si contraddicono tra loro. La revisione di coerenza le ha raccolte (`revisione-ondata-1.md`). Sono numerate `DX-NN`. Finché non sono prese, molte DA dei singoli documenti restano bloccate.

| ID | Questione | Documenti coinvolti | Stato | Scelta | Motivo | Data |
|---|---|---|---|---|---|---|
| DX-01 | **Rapporto tra gravya-app-v2, gravya-app e la Beta.** | A1, B2, C1, C3, E2, E3 | **Decisa** | **Ripartenza da zero** (PV-03): pianificazione e codice v2 nuovi; gravya-app resta riferimento per requisiti, lezioni apprese e soluzioni validate, da riportare in v2 solo tramite i documenti di dettaglio. | gravya-app nasce come fork di Paperclip (LICENSE, 299 file che lo citano ancora, guardia `check-no-paperclip`), con una visione di prodotto diversa (`doc/GOAL.md`, `doc/PRODUCT.md`: "control plane for autonomous AI companies", organigrammi) e poi riorientata (visione kloudify: Paperclip eliminato, catena senza organigramma). Contiene circa 878k righe in 3.370 file, 421 migrazioni, 509 documenti md su più livelli (doc/, docs/, kloudify docs/visione) in parte contraddittori, e due motori di workflow. I documenti dell'ondata 1 hanno trovato più volte codice e piani in disaccordo tra loro. | 2026-11-03 |
| DX-02 | **Aderenza al master plan o alle scelte esistenti.** | E1, A1, A3, C1, B1 | **Decisa in parte** | Niente OpenTelemetry (PV-02). Regola generale: la conformità a GDPR, NIS2 e AI Act e l'osservabilità AI prevalgono sul master plan (PV-01); nel dubbio si riporta all'utente. Le altre divergenze (graph DB, OPA, motore workflow, runtime effimero) si decidono una per una con questo criterio. | Decisione dell'utente: la gestione dei dati deve essere conforme a NIS2 e GDPR. | 2026-11-03 |
| DX-03 | **Trasporto eventi** (Redis Stream, Redis pub/sub o pg NOTIFY). Coincide con DA-A1-03. | A1, B1, B2, C1, C3, E2 | Aperta | | | |
| DX-04 | **Formato dei contratti condivisi tra Node e Python** (JSON Schema, Zod o Pydantic). Coincide con DA-C3-03. | C3, B2, A3, C1 | Aperta | | | |
| DX-05 | **Chi parcheggia la chiamata da approvare e chi chiama `interrupt()`.** Per A3 e B2 è B2, con l'esito `require_approval` della policy. Per C3 e per il codice attuale è il run/esecutore. C1 modella l'HITL come nodo esplicito. | A3, B2, C1, C3 | Aperta | | | |
| DX-06 | **Topologia dell'enforcement**: sidecar, libreria o servizio. DA-A3-02 e DA-B2-02 vanno decise insieme. | A3, B2, B1 | Aperta | | | |
| DX-07 | **Convenzione dei nomi** per eventi e tenant. Gli eventi usano nomi puntati (`tool.*`) o underscore (`hitl_*`); il tenant si chiama `tenant_id` o `company_id`. | Tutti | Aperta | | | |
| DX-08 | **Dipendenze critiche che stanno nell'ondata 2**. B5 (checkpointer) serve a C1, C3 e B1; A2 (compilatore) serve ad A3. Le alternative sono anticiparli all'ondata 1 o accettare per lo skeleton il checkpointer esistente e un bundle fixture. | B1, C1, C3, A3 | Aperta | | | |
| DX-09 | **Politica di retention unica.** Un'unica politica di default per tutti i dati della piattaforma: tracce, audit, decisioni, HITL, checkpoint, eventi di runtime, report di eval, versioni dei prompt. Va progettata la possibilità di differenziare per classe di dato e per tenant, se servirà. | A1, A3, B1, B2, C1, C3, E1, E2, E3 | **Decisa (struttura)**. Durate da fissare | Politica unica di default, con override per classe e per tenant previsti nel modello ma non attivi. **Le durate di default non sono ancora fissate**: nessuno le ha indicate. Il sottoprodotto responsabile va assegnato (vedi DX-12). | Decisione dell'utente | 2026-11-03 |
| DX-10 | **Notifica incidenti NIS2** (allerta entro 24 h, notifica entro 72 h). | A5 e tutti i produttori di segnali (B1, B2, A3, C3, E2) | **Decisa** | La responsabilità è di A5 (audit trail), ondata 2. Gli altri sottoprodotti inviano segnali ad A5. | Decisione dell'utente | 2026-11-03 |
| DX-11 | **Ruolo GDPR e classe di rischio AI Act.** | Tutti | **Decisa** | Gravya è responsabile del trattamento (art. 28 GDPR) per conto delle agenzie. I casi d'uso v2 non sono ad alto rischio: gli artt. 12, 14, 19 e 26 dell'AI Act non sono obbligatori, e restano come buona pratica di osservabilità. L'art. 50 (trasparenza) resta applicabile. | Decisione dell'utente | 2026-11-03 |
| DX-12 | **Responsabile della politica di retention DX-09.** | — | **Decisa (2026-11-03, utente)** | Componente F (Dati e multi-tenancy). Proposto il nuovo sottoprodotto **F6 — Politica di retention e cancellazione**, non presente nel master plan, da redigere nell'ondata 2. L'ID F6 è una proposta. | Conferma dell'utente della proposta | 2026-11-03 |
---

## 2. Decisioni per documento

| ID | Titolo | Raccomandazione del documento | Stato |
|---|---|---|---|
| DA-E1-01 | OpenTelemetry o Timeline DB-native | Chiusa da DX-02 (PV-02): tracing DB-native | Decisa (2026-11-03) |
| DA-E1-02 | Cattura dei contenuti di prompt e risposte | Mai in produzione; un eventuale opt-in richiede DPIA e parere legale | **Decisa (2026-11-03, utente)** |
| DA-E1-03 | Backend delle tracce | Storage delle tracce: lo stesso PostgreSQL di v2, partizionato; niente SaaS né extra-UE | Aperta |
| DA-E1-04 | Come rappresentare retrieval e decisioni | Kind dedicati (retrieval, decision) nella tabella dei segmenti | Aperta |
| DA-E2-01 | Modello dati del registry | Nuove tabelle prompts/prompt_versions/prompt_activations (senza migrazione) | Aperta |
| DA-E2-02 | Motore di template | Sostituzione `{{var}}` senza logica, in TS e Python | Aperta |
| DA-E2-03 | Quali prompt migrare | Perimetro del registry v2; preambolo fisso e avvisi art. 50 restano nel codice | Aperta |
| DA-E2-04 | Condizione per promuovere una versione | E3 più approvazione umana tramite C3 | Aperta |
| DA-E2-05 | Anticipare il versioning rispetto alla Beta | Chiusa da DX-01 | Decisa (2026-11-03) |
| DA-E3-01 | Primo bersaglio del dataset | Gate sul workflow thin-slice C1; scenari Kloud riscritti come contenuto | Aperta |
| DA-E3-02 | Linguaggio e posizione del runner | Nessuna: dipende dal layout di v2 e da DX-04 | Aperta |
| DA-E3-03 | Controlli soggettivi in CI | Nel gate solo controlli deterministici; giudice LLM come segnale non bloccante | Aperta |
| DA-E3-04 | Date relative (R1) | Nuovo seed a ogni run | Aperta |
| DA-E3-05 | Non determinismo del modello | 1 run per iniziare | Aperta |
| DA-E3-06 | Collocazione rispetto alla Beta | Chiusa da DX-01 | Decisa (2026-11-03) |
| DA-E3-07 | Soglia del gate | 100% sui casi bloccanti, solo report sugli altri | Aperta |
| DA-A1-01 | Backend del grafo | PostgreSQL+RLS. Neptune escluso; Neo4j resta alternativa solo se servono traversal pesanti | **Decisa (2026-11-03, utente)** |
| DA-A1-02 | Fonte di verità dei mandati | Il grafo come unica fonte in v2 | Aperta |
| DA-A1-03 | Trasporto eventi | Redis Stream | Aperta (= DX-03) |
| DA-A1-04 | Allowlist dei tool nel grafo | Rinviata a B2 (vedi DA-B2-05) | Aperta |
| DA-A1-05 | Rapporto con gravya-app e con la Beta | Chiusa da DX-01 | Decisa (2026-11-03) |
| DA-A1-06 | Isolamento | Istanza condivisa, con l'istanza dedicata come opzione | Aperta |
| DA-A3-01 | Motore di policy | Prima un valutatore proprio scritto da zero, poi OPA solo locale | Aperta |
| DA-A3-02 | Topologia | Sidecar se si sceglie OPA, altrimenti libreria | Aperta (vedi DX-06) |
| DA-A3-03 | Granularità del bundle | Un bundle per tenant | Aperta |
| DA-A3-04 | Stato dinamico (spesa, token) | Passato da B2 nell'input | Aperta |
| DA-A3-05 | Destino di `_scope_enforcement.py` | Chiusa da DX-01: non entra in v2, resta un riferimento per i casi di test | Decisa (2026-11-03) |
| DA-B1-01 | Unità di isolamento | Un ambiente per job | Aperta |
| DA-B1-02 | Container o VM | Container con un profilo di hardening da definire per v2 | Aperta (dipende da DA-B1-06) |
| DA-B1-03 | Launcher e trasporto | Launcher dedicato chiamato da arq | Aperta |
| DA-B1-04 | Rete laterale e DNS | Uscita solo verso B2 ed egress-proxy; tunnelling DNS chiuso o accettato? | **Da riportare** |
| DA-B1-05 | Telemetria del job | Chiusa da DX-02: telemetria DB-native sul modello di E1 | Decisa (2026-11-03) |
| DA-B2-01 | Base di partenza del gateway | Chiusa da DX-01: gateway nuovo | Decisa (2026-11-03) |
| DA-B2-02 | Forma del confine | Servizio HTTP separato | Aperta (vedi DX-06) |
| DA-B2-03 | Archivio dei contatori di rate limit | Redis | Aperta |
| DA-B2-04 | Audit fail-open o fail-closed | Fail-closed: se l'audit non si salva, l'azione si blocca | **Decisa (2026-11-03, utente)** |
| DA-B2-05 | Origine dell'allowlist dei tool | Nessuna; da decidere con DA-A1-02 | Aperta |
| DA-C1-01 | Quale motore esegue i workflow | LangGraph come motore unico, usato come libreria self-hosted | **Decisa (2026-11-03, utente)** |
| DA-C1-02 | Grafo Kloud e supervisore: dato o codice | Chiusa da DX-01: anche la pipeline agentica è una WorkflowDefinition | Decisa (2026-11-03) |
| DA-C1-03 | Linguaggio delle condizioni sugli edge | JSON dichiarativo | Aperta |
| DA-C1-04 | Quando farlo rispetto alla Beta | Chiusa da DX-01 | Decisa (2026-11-03) |
| DA-C3-01 | Riuso dei moduli HITL in v2 | Chiusa da DX-01 | Decisa (2026-11-03) |
| DA-C3-02 | Dove vive il nodo HITL | Solo nel motore unico scelto da C1 | Aperta (dipende da DA-C1-01) |
| DA-C3-03 | Fonte del contratto condiviso | JSON Schema neutro | Aperta (= DX-04) |
| DA-C3-04 | TTL delle richieste HITL | 24 h fisse in ondata 1 | Aperta |

## 3. Decisioni aggiunte nella v1.2 (ripartenza da zero e conformità)

| ID | Titolo | Raccomandazione del documento | Stato |
|---|---|---|---|
| DA-E1-05 | GenAI semantic conventions e formato traceparent usati solo come vocabolario, senza SDK OTel | Ammesso il vocabolario (nomi GenAI semconv, formato traceparent) senza SDK né export OTel | **Decisa (2026-11-03, utente)** |
| DA-E1-06 | Retention per classe di traccia | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-E1-07 | Tracce e audit A5: tabelle separate o comuni | Separate, collegate da `trace_id` | Aperta |
| DA-E1-08 | Accesso degli operatori Gravya alle tracce di più tenant | Ruolo di istanza con log degli accessi, solo dati aggregati | **Da riportare** |
| DA-E2-06 | Retention di versioni e attivazioni dei prompt | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-E2-07 | Versioni di prompt proposte dall'AI | Ammesse come candidate, mai attivabili senza un umano | **Da riportare** |
| DA-E2-08 | Seed dei prompt v2: da zero o dai testi di gravya-app rivisti | Testi di gravya-app come bozza da rivedere | **Da riportare** |
| DA-E3-08 | Contenuti di produzione nei casi di eval | Solo dati sintetici, mai dati reali dei clienti | **Decisa (2026-11-03, utente)** |
| DA-E3-09 | Provider del giudice LLM e piattaforme di eval | Niente piattaforme SaaS di eval; giudice LLM solo con elaborazione nell'UE | **Decisa (2026-11-03, utente)** |
| DA-E3-10 | Retention dei report CI e dei segmenti di eval | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-A1-07 | Retention dei mandati scaduti e del loro audit | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-A1-08 | Base giuridica per gli identificativi degli admin nell'audit | Inquadrata da DX-11 (Gravya responsabile del trattamento); base giuridica proposta da confermare nella politica DX-09 | Aperta |
| DA-A3-06 | Retention dei record di decisione | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-A3-07 | Allow quando il record di decisione non viene salvato | Fail-closed: se il record di decisione non si salva, l'azione si blocca | **Decisa (2026-11-03, utente)** |
| DA-B1-06 | Piattaforma di esecuzione e deploy | Self-hosted su infrastruttura UE; sandbox gestite di terzi solo con approvazione esplicita | **Decisa (2026-11-03, utente)** |
| DA-B1-07 | Retention di eventi di runtime e output | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-B2-06 | Retention dell'audit dei tool | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-B2-07 | Tool che inviano dati a terzi o fuori dall'UE | Ogni tool dichiara destinazione, giurisdizione e categorie di dati; deny se manca; opt-in del tenant per l'extra-UE | **Decisa (2026-11-03, utente)** |
| DA-C1-05 | LangGraph senza servizi gestiti (LangSmith, Platform) | Solo la libreria open source; niente LangSmith né LangGraph Platform | **Decisa (2026-11-03, utente)** |
| DA-C1-06 | Retention di stato e checkpoint dei run | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-C3-05 | Retention dei dati HITL | Confluisce nella politica di retention unica DX-09 | Assorbita da DX-09 |
| DA-C3-06 | Cosa della chiamata parcheggiata entra nelle tracce | Solo identificativi e hash | Aperta |

## 4. Lacune trasversali emerse nella v1.2

- ~~Notifica degli incidenti NIS2~~: assegnata ad A5 (DX-10).
- **Mutazioni del grafo A1**: non è deciso se diventano segmenti di traccia E1 (con un nuovo kind) o solo eventi di audit.
- ~~Ruoli GDPR e classificazione di rischio AI Act~~: decisi (DX-11).

## 5. Proposta di durate per DX-09 (da validare)

**Stato: proposta da validare** al termine dell'esame dell'ondata 1, con verifica legale e sui contratti con le agenzie. Le durate non derivano da nessuna norma che fissi un valore preciso per questi dati. Sono scelte di minimizzazione (GDPR art. 5(1)(e)) bilanciate con le esigenze di indagine sugli incidenti (NIS2 art. 21 e 23). Il riferimento di 6 mesi dell'AI Act (art. 19) qui è solo buona pratica (DX-11). Si applicano come unica politica di default; il modello prevede override per classe e per tenant, non attivi.

| Classe di dati | Esempi (documento) | Durata proposta | Motivo |
|---|---|---|---|
| Tracce operative (metadati) | `gravya_traces`, segmenti llm/tool/agent/retrieval (E1) | 90 giorni | Debug e analisi dei costi; nessun contenuto (DA-E1-02) |
| Eventi di runtime | eventi di B1, eventi `workflow.*` (C1), `graph.*` (A1) | 90 giorni | Come le tracce |
| Audit e decisioni | audit dei tool (B2), record di decisione (A3), audit delle mutazioni (A1), decisioni HITL (C3), attivazioni dei prompt (E2) | 12 mesi | Finestra per indagare un incidente e dimostrare l'accountability; supera i 6 mesi dell'art. 19 dell'AI Act, che qui è buona pratica |
| Log di accesso degli operatori cross-tenant | accessi alle tracce (E1, DA-E1-08) | 12 mesi | Controllo dell'operato del responsabile del trattamento |
| Payload sensibili temporanei | argomenti delle chiamate parcheggiate (C3), anteprime redatte (B2) | 30 giorni dopo la decisione o l'esecuzione; nell'audit resta solo l'hash | Minimizzazione |
| Stato dei run e checkpoint | stato LangGraph, checkpoint B5 (C1, C3) | 30 giorni dopo la chiusura del run | Basta per riprendere un run e fare il replay; poi è un dato non necessario |
| Evidenze di incidente | dati collegati a un incidente aperto da A5 | Durata del caso + 12 mesi, sospendendo le altre scadenze per quei dati | Serve un legal hold per NIS2; meccanismo da definire in F6 e A5 |
| Artefatti di configurazione | versioni di prompt, bundle di policy, definizioni di workflow (attore pseudonimo) | Per tutta la durata del servizio | Senza dati personali in chiaro; servono per la riproducibilità |
| Report di eval (dati sintetici) | report CI, segmenti eval_case (E3) | 12 mesi | Storico delle regressioni; nessun dato personale |
| Dati dell'agenzia a fine contratto | tutti i dati del tenant | Restituzione o cancellazione entro 30 giorni dalla fine del contratto, salvo obblighi di legge | GDPR art. 28(3)(g); valore da allineare ai contratti |

**Da verificare nella validazione:** compatibilità con i contratti con le agenzie; obblighi di conservazione di settore dei clienti (per esempio fiscali), che restano a carico del titolare; conflitto tra cancellazione su richiesta dell'interessato e audit di 12 mesi, con proposta di pseudonimizzare l'attore e conservare solo l'hash.

## 6. Punti aperti emersi nella v1.3

| Punto | Documenti | Nota |
|---|---|---|
| Il fail-closed vale anche per l'audit delle mutazioni di A1? | A1, A5 | Proposta: audit nella stessa transazione, rollback se fallisce |
| Fail-closed: una coda durevole locale conta come "salvato"? E cosa fare se fallisce l'audit dell'esito dopo che l'azione è stata eseguita? | B2, A3, C1 | Proposta: la coda conta solo se è durevole su disco con fsync; dopo l'esecuzione, segnale ad A5 e coda di recupero |
| Chi conferma il salvataggio nell'ondata 1, prima che esista A5 | A3, B2 | Tabella di audit minima già in ondata 1, che A5 poi assorbe |
| Soglia di latenza complessiva di A3, compreso il salvataggio sincrono | A3 | Da fissare |
| L'egress-proxy di B1 segue la regola delle destinazioni dichiarate (DA-B2-07)? | B1, B2 | Proposta: sì, oppure il proxy va eliminato |
| Dove si registra l'opt-in del tenant per l'extra-UE | B2, A1, A3 | Da definire |
| Base giuridica degli identificativi degli admin (DA-A1-08) | A1, A3, E2 | Con DX-11 la base giuridica è del titolare (l'agenzia); per i dati degli utenti propri di Gravya è di Gravya. Da riformulare |
| Etichetta "generato da AI" (art. 50) negli output e nelle approvazioni | C1, C3, D1–D4 | Da coordinare nell'ondata 2 |
| Il grafo LangGraph gira tutto dentro il job B1, o solo i nodi agente? | B1, C1 | Da decidere |
| Gli argomenti dei tool rientrano nei "contenuti" esclusi da DA-E1-02? | C3, E1 | Proposta: sì, nelle tracce solo hash (DA-C3-06 (a)) |
| Report CI su GitHub e perimetro UE | E3 | Proposta: report minimi su GitHub senza dati personali, oppure CI self-hosted |
