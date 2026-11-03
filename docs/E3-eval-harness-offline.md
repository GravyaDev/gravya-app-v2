# E3 — Eval harness offline

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E3 |
| Nome | Eval harness offline |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.4 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È un runner che gira in CI. Esegue un golden dataset di casi contro il workflow del thin-slice e calcola per ogni caso un esito binario pass/fail. Blocca la PR o il deploy quando il pass rate scende sotto la soglia o quando un caso marcato come bloccante fallisce (master §5 Livello 1, voci 0.3.1–0.3.3).

**Cosa NON fa.**
- Non valuta il traffico di produzione: quello è E4 (Eval online).
- Non assegna voti su scala tipo 1–5 o "la risposta era buona?". Ogni controllo è una domanda specifica con risposta sì/no (master §2, osservabilità).
- Non sostituisce i test unitari e di integrazione di v2, né il controllo di conformità sull'output a runtime (competenza di A3; in gravya-app era `gravya_agent_policies`, slice 1 di #892, citato solo come riferimento).

**Perché esiste.** Il master dice che senza eval non si può concedere autonomia in modo sicuro. La visione in kloudify, invece, registra il set di valutazione come "assente" e afferma che "il set è il primo pezzo da costruire".

## 3. Contesto e dipendenze

**Dipende da:**
- **E2** (Prompt registry): ogni run deve registrare la versione del prompt e del modello usati, e una PR che cambia un prompt deve far scattare E3.
- **E1** (Tracing distribuito): gli esiti di ogni caso vengono registrati nel modello di tracce DB-native definito da E1 (PV-02: niente OpenTelemetry), con il vocabolario unificato `gravya.*`; per gli attributi GenAI (modello, token, operazione) E1 può adottare come vocabolario i nomi delle GenAI semantic conventions, senza SDK né export OTel (DA-E1-05). I dati restano sotto il controllo diretto di Gravya e la via verso E4 resta aperta senza lock-in di vendor.
- **B1** (Agent runtime isolato): l'harness esegue il caso dentro il runtime reale e non su un mock, self-hosted su infrastruttura UE (DA-B1-06).
- **B2** (Tool gateway): i casi di tipo "Act" e "Refuse" si verificano sull'effetto o sul diniego dei tool.
- **A3** (Runtime enforcement): i casi di rifiuto verificano i dinieghi.
- **DX-13** (superadmin e variabili di piattaforma, deciso): soglia del gate, tetto di spesa, timeout e durate di retention sono variabili di piattaforma. Il registro delle variabili e i ruoli sono proposti in **A6 — Identità, ruoli e configurazione di piattaforma** (DX-14, **DA RIPORTARE**, non deciso; alternativa: ruoli in A1 e variabili in F6): dipendenza proposta.
- **F6** (Politica di retention e cancellazione, DX-12, ondata 2): applica le durate DX-09 ai report e ai segmenti di E3.
- **C1** e **C3**: il workflow sotto test (LangGraph come libreria self-hosted, senza LangSmith né LangGraph Platform: DA-C1-01, DA-C1-05) e il punto HITL. I casi che arrivano all'HITL devono avere un esito atteso deterministico.

**È richiesto da:** F6 (per le classi di dati da conservare), A6 se istituito (variabili di E3 da registrare, DX-14), C1 (eval gate prima della pubblicazione di una versione), E2 (hook di promozione, secondo DA-E2-04), E4 (riusa il formato dei controlli binari), il rollout con eval gate attive (master 2.1.2, ondate successive), la suite estesa (master 3.3.1) e il trigger di auto-disable su eval cattive (master 0.4.2, ID non assegnato nel master: Non verificato).

**Assunzioni:**
- Il workflow del thin-slice non è ancora scelto in modo formale. Per DX-01 la fixture e il runner si costruiscono da zero in v2; gli scenari Kloud di gravya-app (Appendice A) sono usati come contenuto di partenza dei requisiti, non come codice. Il bersaglio si scioglie in DA-E3-01.
- La CI di v2 si assume su GitHub Actions; per la decisione §6 di DECISIONS.md su GitHub vanno solo report minimi senza dati personali, in alternativa CI self-hosted (§7). Se v2 condivida i 2 runner self-hosted di gravya-app (e quindi la regola kloudify del 15/10 di non aggiungerne) **non è verificato**: va confermato dall'utente (vedi dubbi in DA-E3-02).

## 4. Contratti

### 4.1 Caso del golden dataset (proposta da validare)

| Campo | Tipo | Note |
|---|---|---|
| `id` | string stabile | es. `R1`, `X4` (convenzione di `kloud-eval-scenarios.md`) |
| `area` | enum | `read` / `act` / `remember` / `refuse` (dalle 4 aree esistenti) |
| `persona` | enum | `admin` / `member` / `client` (idea ripresa da `EvalPersona` in gravya-app; i ruoli effettivi seguono il modello permessi di v2) |
| `input` | string o turni | richiesta dell'utente |
| `checks[]` | lista | ogni controllo: `check_id`, `type` (`deterministic`/`judge`), `assert`, `blocking` (bool) |
| `origin` | enum | `seed` / `production_failure` / `bug_report` |
| `origin_ref` | string | trace id (E1) o numero di issue, obbligatorio se `origin` ≠ `seed`. È un riferimento, non una copia dei dati della traccia (vedi §7) |
| `synthetic` | bool, sempre `true` | attestazione che l'input è interamente sintetico (DA-E3-08); il validatore rifiuta casi senza questo campo |
| `expected_fail_ref` | string opzionale | issue che prevede il fallimento (es. #2489 per X4–X5) |

I valori `deterministic`/`judge` e `block`/`flag` riprendono come idea il vocabolario di `gravya_agent_policies` di gravya-app (migrazione 0375), da riallineare con A3. Non si usa `hitl`, perché in CI non c'è un umano. Lo tratto in DA-E3-03.

### 4.2 Output di un run

È un file JSON con questi campi: `run_id`, `git_sha`, `prompt_versions` (da E2), `model_ref`, `dataset_version` e, per ogni caso, `pass` (bool), `failed_checks[]` e `trace_id`. A questi si aggiungono gli aggregati `pass_rate` e `blocking_failures`. Il report pubblicato come artefatto CI su GitHub è **minimo**: contiene solo id, esiti, versioni, aggregati e `trace_id`; niente testo di input o risposta, niente dati personali, niente segreti (decisione §6 di DECISIONS.md). Contiene anche `platform_config_version`, la versione delle variabili di piattaforma usate (soglia, tetto di spesa, timeout). Exit code: 0 = gate verde, 1 = gate rosso, 2 = harness in errore (che conta comunque come rosso).

### 4.3 Eventi

L'harness scrive per ogni caso un segmento `kind=eval_case` nel modello di tracce DB-native di E1, con gli attributi `gravya.eval.case_id` e `gravya.eval.pass` (nomi allineati a E1 §4.1). Gli attributi relativi al modello seguono il vocabolario scelto da E1, che può usare i nomi GenAI semantic conventions (DA-E1-05). Se la scrittura del segmento fallisce, il caso non è considerato valutato e il run termina con exit 2 (gate rosso): un esito non registrato non vale come pass. Nessuno span OpenTelemetry, nessun exporter OTLP o collector (PV-02). La forma fisica del record (tabella, colonne) la definisce E1. Non consuma eventi di bus.

## 5. Interfacce

- **CLI**: `eval run --dataset <path> [--cases R1,X4] [--report out.json]`. Il nome del comando e il package sono da decidere in DA-E3-02.
- **CI**: un job dedicato, eseguito sulle PR che toccano prompt, modello, tool od orchestrazione (master §5). Il filtro per percorso va derivato da E2 e B2.
- **Promozione di un fallimento**: un comando o template che crea un caso con `origin=production_failure` a partire da un `trace_id`. Il caso entra nel dataset tramite PR con revisione umana. Leggere una traccia di produzione di un tenant è un accesso cross-tenant: lo fa solo un utente con ruolo superadmin (DX-13), entro le istruzioni del titolare (art. 28) e con l'accesso registrato nel log degli accessi di E1 (DA-E1-08, conservato 12 mesi per DX-09 §5). L'harness e la CI non hanno credenziali verso le tracce di produzione: nel caso finisce solo `origin_ref` e l'input riscritto in forma sintetica.
- **Variabili di piattaforma lette da E3** (DX-13): `eval.gate.pass_rate_min`, `eval.run.cost_cap`, `eval.run.timeout`, `eval.ingestion.timeout` (nomi proposti da validare, da allineare a DX-07). Le modifica solo il superadmin, senza rilasci; ogni modifica è versionata e auditata dal registro (A6 proposto, DX-14). Il job CI legge un'istantanea versionata delle variabili; finché il registro non esiste, l'istantanea è un file versionato nel repository modificabile solo tramite PR. **Fail-closed**: variabile mancante, fuori dominio o non leggibile = exit 2 (gate rosso), mai un default implicito nel codice.

## 6. Comportamento

**Flusso principale.**
1. Prepara la fixture isolata con un seed v2 nuovo, idempotente, che rifiuta la produzione e supporta `--clean` (requisiti ripresi dal seed di gravya-app, che li aveva già validati).
2. Esegue ogni caso con la persona indicata.
3. Valuta i controlli: risposta, stato del DB e oracolo di memoria per i casi `remember`.
4. Scrive il report e applica il gate.

**Crescita dai fallimenti reali.** Ogni fallimento osservato in produzione (da E4, dalla revisione umana o da un ticket) diventa un caso con `origin_ref`. I casi non si cancellano. Un caso si ritira solo tramite PR con motivazione.

**Casi limite.**
- *Fallimento atteso* (`expected_fail_ref`): il caso viene contato e riportato, ma non blocca finché l'issue è aperta. Quando passa, la CI segnala che il caso va promosso a bloccante.
- *Scadenza temporale*: R1 vale circa 20 giorni dopo il seed. L'harness rifà il seed a ogni run, oppure fissa la data (DA-E3-04).
- *Ingestione asincrona dei documenti* (R4, R5): l'harness attende `ingestion_status = completed`. Il timeout è la variabile `eval.ingestion.timeout` (DX-13). Se scade, l'esito è errore dell'harness e non fail del caso.
- *Non determinismo del modello*: vedi DA-E3-05.
- *Errore del giudice LLM o del provider*: il giudice, se adottato, usa solo provider con elaborazione nell'UE (DA-E3-09). L'esito è "non valutato" e il gate è rosso. Il master non lo dice; segue il principio kloudify "un controllo che non gira blocca".
- *Caso promosso da produzione*: l'input viene riscritto interamente in forma sintetica, senza dati reali dei clienti (DA-E3-08), e rivisto in PR; del fallimento reale si conserva solo `origin_ref`.
- *Record E1 non salvabile*: il caso è "non valutato" e il job esce con 2 (rosso).
- *Variabili di piattaforma non valide o non leggibili*: il run non parte ed esce con 2 (rosso).
- *Tetto di spesa raggiunto* (`eval.run.cost_cap`): i casi restanti sono "non valutati" e il job esce con 2 (rosso).

## 7. Requisiti non funzionali

- **Sicurezza e conformità** (PV-01):
  - *GDPR – ruolo e minimizzazione*: Gravya agisce come responsabile del trattamento (art. 28) per conto delle agenzie (DX-11). Il dataset seed e la fixture contengono solo dati fittizi (tenant "Kloud Eval SRL" o equivalente del thin-slice). Nei casi di eval si usano **solo dati sintetici, mai dati reali dei clienti** (DA-E3-08): i casi promossi da fallimenti reali (`production_failure`, `bug_report`) si riscrivono in forma sintetica e conservano solo `origin_ref`. I contenuti di prompt e risposte non vengono mai catturati in produzione (DA-E1-02), quindi non sono una fonte per i casi.
  - *GDPR – retention e diritti*: la conservazione segue la politica di retention unica DX-09 con i default approvati (DECISIONS.md §5), modificabili dal superadmin come variabili di piattaforma (DX-13) e applicati da F6. Classi di dati prodotte da E3: (1) report JSON dei run (artefatti CI) e (2) segmenti `kind=eval_case` nel modello di tracce E1: classe "Report di eval (dati sintetici)", default **12 mesi**; (3) golden dataset versionato nel repository: classe "Artefatti di configurazione", per tutta la durata del servizio (casi sintetici, nessun dato personale). Gli artefatti su GitHub hanno una conservazione governata da GitHub e non dal registro delle variabili (Appendice B): la copia di riferimento per i 12 mesi è il segmento E1; la scadenza dell'artefatto GitHub va impostata a un valore non superiore al default DX-09. Report e segmenti contengono solo id, esiti, versioni e `trace_id`, non il testo delle risposte. Se un `origin_ref` punta a una traccia soggetta a cancellazione (art. 17), il caso resta valido perché non dipende dai dati della traccia.
  - *Perimetro dei dati*: nessuna piattaforma SaaS di eval o tracing (DA-E3-09). Il giudice LLM, se adottato (DA-E3-03), usa solo provider con elaborazione nell'UE (DA-E3-09) e riceve solo dati sintetici. Report CI su GitHub e perimetro UE (decisione §6 di DECISIONS.md): su GitHub vanno solo report minimi senza dati personali, prodotti su dati sintetici (§4.2); in alternativa la CI è self-hosted su infrastruttura UE. Quale delle due resta legato a DA-E3-02.
  - *Accessi cross-tenant*: l'unico accesso ai dati di un tenant previsto da E3 è la lettura di una traccia per promuovere un fallimento, fatta dal superadmin con log degli accessi (DX-13, DA-E1-08). Le modifiche alle variabili di E3 sono versionate e auditate (DX-13).
  - *NIS2 (art. 21)*: l'harness gira solo su DB non di produzione (guardia di ambiente, AC7), nessun bypass RLS, nessuna credenziale nel report (requisito ripreso da `describeDbTarget` di gravya-app); i segreti CI stanno nel secret store e i runner sono soggetti alle stesse misure di gestione accessi e patching del resto della CI. Il gate è una misura di sicurezza dello sviluppo (art. 21.2.e). L'harness non tratta dati di produzione e non notifica incidenti: la notifica NIS2 è di A5 (DX-10). Un fallimento dei casi `refuse` (fuga cross-tenant) scoperto in CI blocca il rilascio ed è trattato come vulnerabilità; E3 non è tra i produttori di segnali verso A5 indicati in DX-10.
  - *AI Act*: i casi v2 non sono ad alto rischio (DX-11). L'art. 50 resta applicabile: l'harness verifica prima del rilascio, con casi dedicati, che l'agente si dichiari AI dove richiesto, oltre ai rifiuti. La conservazione per ogni run di versioni di prompt e modello è buona pratica di osservabilità, non adempimento degli artt. 12/19. Non sostituisce la sorveglianza umana a runtime (C3).
  - *Osservabilità AI resa disponibile*: per ogni run `git_sha`, `dataset_version`, versioni prompt (E2), `model_ref`, esito per caso e per controllo, costo del run, tutto interrogabile nel DB di E1 e collegato a `trace_id`.
- **Isolamento**: la fixture è un tenant dedicato ("Kloud Eval SRL"). I casi `refuse` verificano che nessun dato di un altro tenant compaia.
- **Costo**: è previsto un tetto di spesa per run, variabile di piattaforma `eval.run.cost_cap` gestita dal superadmin (DX-13) (valore di default: proposta da validare). Come riferimento, kloudify registra per gravya-app un limite A6 di $2 e 10 minuti per run agente; in v2 il valore va riconfermato.
- **Osservabilità**: ogni caso ha un `trace_id` E1 navigabile.
- **Riproducibilità**: il report contiene `git_sha`, `dataset_version` e le versioni dei prompt E2.

## 8. Criteri di accettazione

| # | Criterio | Verifica |
|---|---|---|
| AC1 | Il golden dataset iniziale ha 10–30 casi (master 0.3.1) | conteggio dei casi nel dataset ≥ 10 e ≤ 30 |
| AC2 | Ogni controllo è binario | test di validazione dello schema: rifiuta campi con punteggio numerico |
| AC3 | Il gate blocca | una PR di prova che degrada un prompt fa fallire il job CI (exit 1) |
| AC4 | Soglia | gate rosso se `pass_rate` < `eval.gate.pass_rate_min` sui casi non attesi-falliti, oppure se ≥ 1 caso bloccante fallisce. Default della variabile 90% (**proposta da validare**, DA-E3-07); test con due valori diversi della variabile che cambiano l'esito senza modifiche al codice |
| AC5 | Determinismo dell'harness | 2 run consecutivi sullo stesso SHA danno gli stessi esiti sui controlli `deterministic` (100%) |
| AC6 | Crescita dai fallimenti | il validatore rifiuta un caso con `origin=production_failure` privo di `origin_ref` |
| AC7 | Guardia produzione | con `API_ENV=production` l'harness esce ≠ 0 prima di qualunque connessione al DB (test unitario) |
| AC8 | Tracciabilità | ogni caso del report ha un `trace_id` presente nel backend E1 |
| AC9 | Errore ≠ pass | con il provider LLM non raggiungibile il job è rosso (exit 2) |
| AC10 | Fail-closed sulla registrazione | con il backend E1 non scrivibile il job è rosso (exit 2) e nessun caso risulta pass |
| AC11 | Solo dati sintetici | il validatore rifiuta un caso privo di `synthetic: true` (DA-E3-08) |
| AC12 | Variabili fail-closed (DX-13) | con una variabile di E3 assente o fuori dominio il job esce con 2 prima di eseguire casi (test unitario); il report contiene `platform_config_version` |
| AC13 | Report minimo su GitHub | test che l'artefatto CI contiene solo i campi di §4.2: nessun testo di input/risposta, nessun dato personale, nessun segreto |
| AC14 | Nessun accesso cross-tenant dalla CI | le credenziali del job CI non consentono la lettura di tracce di produzione (test di configurazione); la promozione da `trace_id` richiede il ruolo superadmin e genera una riga nel log degli accessi (test d'integrazione quando esistono E1 e A6/DX-14) |

## 9. Piano di implementazione

**Fasi ordinate.**
1. Sciogliere DA-E3-01 e DA-E3-02. Riscrivere i 20 scenari di `gravya-app/docs/testing/kloud-eval-scenarios.md` nel formato di §4.1, adattando i controlli DB allo schema v2.
2. Costruire da zero in v2 seed, fixture, runner e oracolo di memoria, prendendo come specifica il seed di gravya-app e `kloud_memory_oracle.py` (riferimento, non codice da portare, DX-01).
3. Implementare i controlli `deterministic` (stato del DB, presenza o assenza di nomi). Poi i controlli `judge` secondo DA-E3-03.
4. Aggiungere il job CI con il gate, inizialmente in modalità report-only fino alla soglia di AC4, poi bloccante.
5. Aggiungere l'aggancio a E1 (record DB-native) ed E2 (versioni). Infine il flusso di promozione dei fallimenti.

**Tecnologie.** TypeScript o Python secondo DA-E3-02 (e DX-04), vitest/pytest, GitHub Actions, persistenza degli esiti nel modello DB-native di E1. Nessun SDK né export OpenTelemetry (PV-02); ammesso solo il vocabolario GenAI semconv tramite E1 (DA-E1-05). Il master cita una "piattaforma eval" generica: nessuna piattaforma SaaS di eval (DA-E3-09).

**Rischi.** Sono elencati in §11.

## 10. Test e valutazione

- **Unit**: validatore dello schema dei casi, calcolo di gate e soglia, guardia `API_ENV`, redazione delle credenziali, exit 2 quando la scrittura su E1 fallisce (AC10), exit 2 con variabili di piattaforma mancanti o fuori dominio (AC12), gate con soglia letta dalla variabile (AC4).
- **Integration**: run completo su DB effimero (idea ripresa da `kloud-eval-seed.realpg.test.ts` di gravya-app).
- **Conformità**: test che il report e i record E1 non contengano testo di risposta né dati personali; validatore che rifiuta casi senza `synthetic: true` (DA-E3-08, AC11); configurazione del giudice che rifiuta endpoint non UE (DA-E3-09); controllo dei campi dell'artefatto GitHub (AC13); scadenza dell'artefatto non superiore al default DX-09.
- **Eval dell'harness**: "mutation test" del gate, cioè un prompt volutamente rotto deve produrre il rosso (AC3).
- **Security**: i casi X1–X5 sono essi stessi test di isolamento. In più, nel report non compare alcun segreto.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Esiti instabili (modello non deterministico) → gate ignorato | Controlli deterministici dove possibile; DA-E3-05 |
| Il giudice LLM sbaglia | Il giudice è limitato a domande binarie strette; campione rivisto a mano (Livello 3 del master) |
| Costo della CI | Il gate scatta solo su PR rilevanti (filtro per percorso); tetto di spesa |
| Il dataset diventa vecchio | `origin` obbligatorio; crescita dai fallimenti; scadenza di R1 gestita |
| Dati personali reali entrano nel dataset tramite i casi promossi | Solo dati sintetici (DA-E3-08): campo `synthetic` obbligatorio, revisione in PR |
| Dati inviati a provider o piattaforme fuori perimetro | Nessuna piattaforma SaaS; giudice solo con elaborazione UE (DA-E3-09) |
| Report CI su GitHub con dati personali o fuori perimetro UE | Report minimo su dati sintetici (AC13), oppure CI self-hosted UE |
| Soglie modificate in modo errato o non tracciato | Variabili di piattaforma versionate e auditate, solo superadmin, fail-closed (DX-13, AC12) |
| Accesso improprio alle tracce dei tenant nella promozione dei fallimenti | Solo superadmin, con log degli accessi; nessuna credenziale di produzione nella CI (AC14) |
| Runner CI saturi (se v2 condivide i 2 self-hosted, Non verificato) | Job serializzato o notturno da decidere in DA-E3-02 |

## 12. Stima e priorità

- **Taglia**: L (era M in v1.1). Con la costruzione da zero (DX-01) vanno scritti anche seed, fixture e oracolo di memoria, oltre a runner, controlli, gate e agganci E1/E2, più i controlli di conformità di §7. Le decisioni del 2026-11-03 (DA-E3-08/09, fail-closed, DX-09) semplificano i controlli ma non cambiano la taglia. Resta riutilizzabile come contenuto il testo dei 20 scenari.
- **Dipendenze critiche**: B1 (eseguire davvero gli agenti) ed E2 (versioni). Senza B1 i casi `act` non sono eseguibili. In v2 i casi `act` dipendono dal ciclo di tool di B1/B2 costruito da zero (in gravya-app esisteva `_run_tool_loop` in `generic_executor.py`, solo riferimento).
- **Thin-slice MVP**: sì (master 0.3).

---

## Appendice A — Riferimenti dal sistema precedente

Per DX-01/PV-03 nulla di quanto segue entra in v2 come codice: è materiale di riferimento.

**Soluzioni da riprendere come idea (lette):**
- `gravya-app/server/scripts/kloud-eval-seed.ts` e `kloud-eval-fixture.ts` (#2523, PR 1): seed idempotente di un tenant fittizio ("Kloud Eval SRL": 17 clienti, 22 note, 6 documenti KB, 3 persone) che passa per le route reali, con guardia `API_ENV` e `--clean`. Da riprendere: dati solo fittizi, passaggio dalle API reali, guardia di produzione, idempotenza.
- `gravya-app/docs/testing/kloud-eval-scenarios.md`: 20 scenari pass/fail con esito atteso scritto prima del run (Read R1–R6, Act A1–A5, Remember M1–M4, Refuse X1–X5) e fallimenti previsti (#2069, #2507, #1685, #2489). È il contenuto più prezioso: requisiti già formulati in forma binaria, da riscrivere nel formato di §4.1.
- `gravya-app/packages/db/src/migrations/0375_gravya_agent_policies.sql`: vocabolario `deterministic|judge|hitl`, `block|flag`.
- `describeDbTarget`: nessuna credenziale nei log.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` §2.10: il set di valutazione è marcato "manca" e indicato come primo pezzo da costruire.

**Difetti da non ripetere:**
- Scenari solo in prosa, senza formato macchina e senza runner automatico: in v2 il formato di §4.1 e il runner nascono insieme.
- Nessun workflow di eval in `.github/workflows/`: esecuzione solo manuale da tester. In v2 il gate CI è parte del deliverable.
- Test di integrazione della fixture rimasto rosso (`kloud-eval-seed.realpg.test.ts`, 409 `record_archived`, riportato da kloudify): la fixture deve avere un test verde come criterio d'ingresso.
- Benchmark di memoria a metrica (`services/agents/src/benchmarks/`, Recall@k): non è un gate binario; in v2 i controlli sono solo sì/no.
- Scenari centrati sull'assistente Kloud e non su un workflow C1: in v2 il dataset segue il thin-slice (DA-E3-01).

## Appendice B — Non verificato

- Lo stato attuale delle issue #2523, #2489, #2069, #2507, #1685, #892.
- Lo stato reale del rosso `kloud-eval-seed.realpg.test.ts` (riportato da kloudify, non riprodotto; rilevante solo come lezione).
- Il contenuto completo di `kloud_memory_oracle.py`, `prompt_improvement_job.py` (REPLAY) e dei validatori in `services/agents/src/compliance/` (non letti per intero).
- Quale sia il workflow del thin-slice per v2.
- L'ID del sottoprodotto che implementa l'auto-disable (master 0.4.2).
- Se la CI di v2 userà gli stessi runner self-hosted di gravya-app.
- Dove risiedono fisicamente gli artefatti CI su GitHub (regione) e se la loro scadenza si può allineare ai 12 mesi DX-09 (i limiti di conservazione degli artefatti GitHub non sono stati verificati).
- Il nome e la forma del registro delle variabili di piattaforma (dipende da DX-14, da riportare).

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-E3-01 | Primo bersaglio del dataset | (a) scenari Kloud riscritti per v2; (b) workflow thin-slice di C1; (c) entrambi | aderenza al master e disponibilità dei requisiti (non più riuso di codice, DX-01) | (b) come bersaglio del gate; (a) come contenuto di partenza per i casi `refuse`/`remember` trasversali |
| DA-E3-02 | Linguaggio e posizione del runner, uso dei runner CI | (a) TypeScript accanto alle API v2; (b) Python accanto agli agenti v2 | accesso alle API e al runtime agenti v2, formato contratti (DX-04); capacità CI non verificata | dipende dal layout v2 e da DX-04; nessuna raccomandazione finché non sono decisi. Se la CI v2 condivida i runner di gravya-app: da confermare con l'utente |
| DA-E3-03 | Controlli soggettivi in CI | (a) giudice LLM binario (solo provider UE, DA-E3-09); (b) solo deterministici, i soggettivi vanno a revisione umana fuori CI | affidabilità, costo | (b) per il gate, (a) come segnale non bloccante |
| DA-E3-04 | Date relative (R1) | (a) re-seed a ogni run; (b) data di riferimento fissata | determinismo e durata | (a) |
| DA-E3-05 | Non determinismo | (a) 1 run, temperatura minima; (b) N run e maggioranza; (c) pass solo se N/N | costo contro instabilità | (a) per iniziare; N da validare |
| DA-E3-06 | Collocazione rispetto alla Beta del 30/11 | — | — | **Chiusa da DX-01**: la Beta di gravya-app non vincola v2; E3 resta nelle fondamenta (master fase 0, ondata 1) |
| DA-E3-07 | Valore di default della soglia del gate (la soglia è comunque variabile di piattaforma, DX-13) | (a) 90% + zero bloccanti; (b) 100% sui bloccanti, solo report sul resto | il master non fissa un valore | (b) finché il dataset è piccolo |
| DA-E3-11 | Report CI su GitHub e perimetro UE | — | — | **Decisa** (2026-11-03, utente, DECISIONS.md §6): report minimi su GitHub senza dati personali (dati sintetici), oppure CI self-hosted |
| DA-E3-08 | Uso di contenuti di produzione nei casi promossi | — | — | **Decisa** (2026-11-03, utente, vedi [DECISIONS.md](DECISIONS.md)): solo dati sintetici, mai dati reali dei clienti |
| DA-E3-09 | Provider del giudice LLM e piattaforma eval | — | — | **Decisa** (2026-11-03, utente, vedi [DECISIONS.md](DECISIONS.md)): niente piattaforme SaaS di eval; giudice LLM solo con elaborazione nell'UE |
| DA-E3-10 | Retention di report CI e segmenti `kind=eval_case` | — | — | **Assorbita da DX-09** (vedi [DECISIONS.md](DECISIONS.md)): politica di retention unica; default approvato 12 mesi per report e segmenti (DECISIONS.md §5), variabile di piattaforma (DX-13); classi in §7 |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span allineati a E1 (`gravya.eval.*`); dipendenza da E1/OTel resa condizionata a DA-E1-01; aggiunti C1 ed E2 in "È richiesto da"; annotata la citazione kloudify superata dal codice. Motivo: interfacce non combacianti e coerenza con B1/B2. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): fixture, seed, runner e oracolo si costruiscono in v2, gravya-app solo riferimento; Appendice A rinominata "Riferimenti dal sistema precedente" (idee da riprendere, difetti da non ripetere); taglia M→L; DA-E3-06 chiusa da DX-01; DA-E3-01/02/03 riformulate; rimosso il rischio Beta. Applicate DX-02/PV-01/PV-02: rimossi span OTel e OpenTelemetry dalle tecnologie, esiti come record DB-native di E1 con vocabolario `gravya.*`; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); nessuna piattaforma SaaS di eval di default; nuove DA-E3-08/09/10 da riportare all'utente. (rev. coerenza) record `gravya.eval.case` rinominato segmento `kind=eval_case` (E1 §4.2) in §4, §7, DA-E3-10. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-E3-08 (solo dati sintetici) e DA-E3-09 (niente SaaS di eval, giudice solo UE) decise: diventano scelte in §4, §6, §7, §9, §10, §11 e nell'Appendice C; aggiunto il campo `synthetic` e AC11. DA-E3-10 assorbita da DX-09: tolta la retention specifica, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica incidenti di A5) e DX-11 (Gravya responsabile ex art. 28; non alto rischio: artt. 12/19 solo buona pratica, art. 50 resta); tolta dalla §7 la questione del ruolo titolare/responsabile. Recepito il fail-closed (DA-B2-04/DA-A3-07) come principio anche per gli esiti: record E1 non salvato = exit 2, AC10 e test unitario. DA-E1-05: E1 può adottare i nomi GenAI semconv come vocabolario. Citati DA-B1-06, DA-C1-01/05, DA-E1-02. Taglia L invariata. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: report e segmenti `eval_case` con default 12 mesi, dataset come artefatto di configurazione (DECISIONS.md §5), applicati da F6. DX-13: soglia del gate, tetto di spesa e timeout diventano variabili di piattaforma gestite dal superadmin, versionate, auditate, fail-closed (§5, §6, AC4, AC12); la promozione di fallimenti da tracce di produzione è un accesso cross-tenant del superadmin con log (DA-E1-08, AC14). DX-14 (A6) citata come dipendenza proposta, da riportare. Decisione §6 "Report CI su GitHub e perimetro UE" resa scelta in §4.2, §7, AC13, test, rischi e Appendice C (registrata come DA-E3-11, ID proposto). Taglia L invariata. |
