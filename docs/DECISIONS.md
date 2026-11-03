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

---

## 2. Decisioni per documento

| ID | Titolo | Raccomandazione del documento | Stato |
|---|---|---|---|
| DA-E1-01 | OpenTelemetry o Timeline DB-native | Chiusa da DX-02 (PV-02): tracing DB-native | Decisa (2026-11-03) |
| DA-E1-02 | Cattura dei contenuti di prompt e risposte | Mai in produzione; per un eventuale opt-in servono DPIA e parere legale | **Da riportare** |
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
| DA-A1-01 | Backend del grafo | PostgreSQL+RLS; Neptune escluso (fuori perimetro); Neo4j come alternativa | **Da riportare** |
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
| DA-B2-04 | Audit fail-open o fail-closed | Fail-closed (sincrono o coda durevole) per PV-01 | **Da riportare** (insieme a DA-A3-07) |
| DA-B2-05 | Origine dell'allowlist dei tool | Nessuna; da decidere con DA-A1-02 | Aperta |
| DA-C1-01 | Quale motore esegue i workflow | LangGraph come libreria self-hosted, motore unico | **Da riportare** |
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
| DA-E1-05 | GenAI semantic conventions e formato traceparent usati solo come vocabolario, senza SDK OTel | Nessuna; provvisoriamente si usa solo il namespace `gravya.*` | **Da riportare** |
| DA-E1-06 | Retention per classe di traccia | Proposta: 90 giorni per i metadati, almeno 6 mesi per i casi dell'Allegato III; liceità non verificata | **Da riportare** |
| DA-E1-07 | Tracce e audit A5: tabelle separate o comuni | Separate, collegate da `trace_id` | Aperta |
| DA-E1-08 | Accesso degli operatori Gravya alle tracce di più tenant | Ruolo di istanza con log degli accessi, solo dati aggregati | **Da riportare** |
| DA-E2-06 | Retention di versioni e attivazioni dei prompt | Template senza limite, attore pseudonimo | **Da riportare** |
| DA-E2-07 | Versioni di prompt proposte dall'AI | Ammesse come candidate, mai attivabili senza un umano | **Da riportare** |
| DA-E2-08 | Seed dei prompt v2: da zero o dai testi di gravya-app rivisti | Testi di gravya-app come bozza da rivedere | **Da riportare** |
| DA-E3-08 | Contenuti di produzione nei casi di eval | Solo riscrittura sintetica | **Da riportare** |
| DA-E3-09 | Provider del giudice LLM e piattaforme di eval | Piattaforme SaaS escluse; nessun giudice in CI oppure provider con elaborazione nell'UE | **Da riportare** |
| DA-E3-10 | Retention dei report CI e dei segmenti di eval | Nessuna | **Da riportare** |
| DA-A1-07 | Retention dei mandati scaduti e del loro audit | Nessuna | **Da riportare** |
| DA-A1-08 | Base giuridica per gli identificativi degli admin nell'audit | Legittimo interesse e accountability (art. 6.1.f e art. 5.2), da validare | **Da riportare** |
| DA-A3-06 | Retention dei record di decisione | Nessuna | **Da riportare** |
| DA-A3-07 | Allow quando il record di decisione non viene salvato | Fail-closed per scritture e `money_write` | **Da riportare** (insieme a DA-B2-04) |
| DA-B1-06 | Piattaforma di esecuzione e deploy | Self-hosted su infrastruttura UE; sandbox gestite solo con la tua approvazione | **Da riportare** |
| DA-B1-07 | Retention di eventi di runtime e output | Nessuna | **Da riportare** |
| DA-B2-06 | Retention dell'audit dei tool | Differenziata: identificativi più a lungo, anteprime per poco | **Da riportare** |
| DA-B2-07 | Tool che inviano dati a terzi o fuori dall'UE | Campo obbligatorio sulla destinazione, deny se manca, opt-in del tenant per l'extra-UE | **Da riportare** |
| DA-C1-05 | LangGraph senza servizi gestiti (LangSmith, Platform) | Solo la libreria open source | **Da riportare** |
| DA-C1-06 | Retention di stato e checkpoint dei run | Nessuna | **Da riportare** |
| DA-C3-05 | Retention dei dati HITL | Nessuna | **Da riportare** |
| DA-C3-06 | Cosa della chiamata parcheggiata entra nelle tracce | Solo identificativi e hash | Aperta |

## 4. Lacune trasversali emerse nella v1.2

- **Notifica degli incidenti NIS2** (allerta entro 24 h, notifica entro 72 h): nessun sottoprodotto ne è responsabile. Va assegnata, probabilmente con A5 o con un nuovo sottoprodotto.
- **Mutazioni del grafo A1**: non è deciso se diventano segmenti di traccia E1 (con un nuovo kind) o solo eventi di audit.
- **Ruoli GDPR** (titolare o responsabile tra Gravya, agenzia e cliente finale) e **classificazione di rischio AI Act** dei casi d'uso v2: tutti i documenti li assumono senza averli verificati.
