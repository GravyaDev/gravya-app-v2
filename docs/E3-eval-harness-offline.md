# E3 — Eval harness offline

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E3 |
| Nome | Eval harness offline |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È un runner che gira in CI. Esegue un golden dataset di casi contro il workflow del thin-slice e calcola per ogni caso un esito binario pass/fail. Blocca la PR o il deploy quando fallisce anche un solo caso bloccante (invariante) o quando il pass rate dei casi non bloccanti scende sotto la soglia `eval.gate.pass_rate_min_percent` (master §5 Livello 1, voci 0.3.1–0.3.3; DECISIONS §7, DA-CV-05 (b)).

**Cosa NON fa.**
- Non valuta il traffico di produzione (E4).
- Non assegna voti su scala: ogni controllo è una domanda sì/no (master §2, osservabilità).
- Non sostituisce i test unitari e di integrazione di v2 né il controllo di conformità a runtime (A3).
- Non invia nulla a terzi e non tratta dati reali: solo dati sintetici.

**Perché esiste.** Senza eval non si può concedere autonomia in modo sicuro (master). La visione in kloudify registra il set di valutazione come «assente», primo pezzo da costruire.

## 3. Contesto e dipendenze

**Dipende da:**
- **E2** (Prompt registry): ogni run registra versione di prompt e modello; una PR che cambia un prompt fa scattare E3.
- **E1** (Tracing): gli esiti sono segmenti DB-native (PV-02, niente OpenTelemetry) con vocabolario `gravya.*`; per gli attributi GenAI E1 può adottare i nomi GenAI semconv senza SDK né export (DA-E1-05).
- **B1** (Agent runtime isolato, self-hosted UE, DA-B1-06) e **B2** (Tool gateway): i casi `act` e `refuse` verificano effetto o diniego dei tool. **A3**: i casi di rifiuto verificano i dinieghi.
- **C1** (workflow sotto test; LangGraph come libreria self-hosted, DA-C1-01, DA-C1-05; contratto `ai_generated` e regole art. 50 di C1 §4.4) e **C3** (punto HITL: i casi che vi arrivano hanno esito atteso deterministico).
- **A6** (registro delle variabili e ruoli, DX-14 decisa; ondata 2): fino ad allora un'istantanea nel repository (ripiego di ondata 1, §5). **F6** (DX-12, ondata 2): applica la retention a report e segmenti. **A5**: nessuna dipendenza di segnale (§7).
- **D1–D4**: i casi sulla marcatura per canale dipendono dal loro dettaglio (DA-C1-07).

**È richiesto da:** F6, A6 (variabili di E3), C1 (eval gate prima della pubblicazione di una versione), E2 (promozione di una versione, DA-E2-04), E4 (formato dei controlli binari), rollout con eval gate (master 2.1.2), suite estesa (master 3.3.1), auto-disable su eval cattive (master 0.4.2, ID non assegnato: Non verificato).

**Assunzioni:**
- Il workflow del thin-slice non è ancora scelto (DA-E3-01). Per DX-01 fixture e runner si costruiscono da zero; gli scenari Kloud di gravya-app sono solo contenuto di partenza (Appendice A).
- La CI di v2 gira su GitHub Actions finché i dati sono sintetici e i segreti sono di un progetto di test separato (E13, DA-E3-11 (a), decisa). Se v2 condivida i 2 runner self-hosted di gravya-app non è verificato (DA-E3-02).
- Convenzione dei nomi e formato dei contratti: DX-07, DX-04 (aperte).

## 4. Contratti

### 4.1 Caso del golden dataset (proposta da validare)

| Campo | Tipo | Note |
|---|---|---|
| `id` | string stabile | es. `R1`, `X4` |
| `area` | enum | `read` / `act` / `remember` / `refuse` (le quattro aree esistenti) |
| `persona` | enum | `admin` / `member` / `client` (idea da `EvalPersona`; i ruoli effettivi seguono A6) |
| `input` | string o turni | richiesta sintetica |
| `checks[]` | lista | `check_id`, `type` (`deterministic`/`judge`), `assert`, `blocking` (bool) |
| `origin` | enum | `seed` / `production_failure` / `bug_report` |
| `origin_ref` | string | trace id (E1) o numero di issue; obbligatorio se `origin` ≠ `seed`. È un riferimento, non una copia di dati |
| `synthetic` | bool, sempre `true` | invariante (DA-E3-08, catalogo §18): il validatore rifiuta casi senza questo campo. È un'attestazione, non un controllo: il controllo è quello sotto |
| `expected_fail_ref` | string opzionale | issue che prevede il fallimento; **non ammesso su un caso con un controllo `blocking`** (il gate non ha eccezioni sui bloccanti) |

Vocabolario `deterministic`/`judge` e `block`/`flag` ripreso come idea da `gravya_agent_policies` (migrazione 0375 di gravya-app), da riallineare con A3. Non si usa `hitl`: in CI non c'è un umano (DA-E3-03).

**Controllo dei dati personali (E10).** Il validatore applica a `input`, `assert` e a ogni testo del caso lo stesso controllo dei dati personali dei template di E2: pattern base (email, telefono), sempre in blocco, senza variabili né modalità che lo attenuino. Ha i limiti dichiarati da E2: i pattern base non rilevano altri dati personali (nomi, indirizzi, testo libero). Per questo la PR che aggiunge o modifica un caso ha una checklist obbligatoria per il revisore (nessun nome o dato reale di persone o aziende clienti; destinatari fittizi; input riscritto e non copiato; `origin_ref` come solo riferimento). **Da dove viene l'input da riscrivere:** le tracce di produzione non hanno contenuto (DA-E1-02), quindi l'input non si ricava da una traccia. Si scrive a partire dalla descrizione del difetto (testo di una issue o di una segnalazione) e dalla forma del fallimento nei metadati (nodo, esito, versione), mai da contenuti di clienti.

### 4.2 Output di un run

File JSON: `run_id`, `git_sha`, `prompt_versions` (E2), `model_ref`, `dataset_version`, `platform_config_version` e, per caso, `pass`, `failed_checks[]`, `trace_id`; aggregati `pass_rate` e `blocking_failures`. Il report pubblicato come artefatto CI è **minimo**: solo id, esiti, versioni, aggregati e `trace_id`; niente testo di input o risposta, dati personali o segreti (DECISIONS §6). Exit code (invariante, catalogo §18): 0 gate verde, 1 gate rosso, 2 harness in errore (conta come rosso).

**Esito registrato del gate (E6).** Per ogni versione candidata (versione di prompt, e per analogia versione di workflow) il run produce un esito registrato: oggetto (`prompt_ref` o `workflow_id@version`), hash del contenuto (`content_hash` del template, non del testo renderizzato: E1), esito, `blocking_failures`, `dataset_version`, data. È ciò che E2 verifica all'attivazione di una versione di prompt (il gate è obbligatorio per ogni attivazione) e C1 alla pubblicazione di una versione di workflow (C1 §6): E2 e C1 non chiamano E3 a runtime. Un esito vale solo per l'hash per cui è stato prodotto; un esito mancante o con fallimenti bloccanti impedisce l'attivazione. Come l'esito raggiunga l'ambiente di produzione, dato che la CI non ha credenziali di produzione: DA-E3-12.

### 4.3 Eventi

Per ogni caso un segmento `kind=eval_case` nelle tracce di E1 (`gravya.eval.case_id`, `gravya.eval.pass`). Se la scrittura fallisce il caso non è valutato e il run esce con 2: un esito non registrato non vale come pass. Nessuno span OpenTelemetry, exporter OTLP o collector (PV-02). La forma fisica è di E1. Nessun evento di bus consumato.

## 5. Interfacce

- **CLI**: `eval run --dataset <path> [--cases R1,X4] [--report out.json]` (nome e package: DA-E3-02).
- **CI**: job dedicato sulle PR che toccano prompt, modello, tool od orchestrazione (master §5); filtro per percorso da E2 e B2. **Guardia di produzione**: con `API_ENV=production` l'harness esce ≠ 0 prima di ogni connessione al DB; è un'invariante di deploy, non una variabile di catalogo e non modificabile da UI (DA-CV-11, D2 (b); eccezione a DX-22 scelta dall'utente).
- **Promozione di un fallimento**: comando che crea un caso `origin=production_failure` da un `trace_id`, via PR con revisione umana. Leggere una singola traccia di un tenant è un accesso cross-tenant: di default il superadmin vede solo dati aggregati; la singola traccia solo per un incidente dichiarato dal superadmin, che abilita la lettura con riferimento all'incidente, oppure nell'ambito di una richiesta di assistenza in cui l'admin agenzia concede l'accesso (E8; DX-19). Perimetro e durata sono limitati da `access.superadmin_trace_access_ttl_hours` e ogni accesso va nel log di proprietà di A6 (DX-18; `retention.cross_tenant_access_log_months`). Senza una delle due vie si promuove da `bug_report` o da dati aggregati. L'harness e la CI non hanno credenziali verso le tracce di produzione; nel caso finiscono solo `origin_ref` e un input riscritto in forma sintetica.
- **Variabili di piattaforma lette da E3** (DX-13, DX-22; valori nel catalogo §11): `eval.gate.pass_rate_min_percent`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s`, `eval.run.repetitions_count`. Le modifica il superadmin, con versione e audit. Il job le legge tramite l'interfaccia unica alle variabili (E5): finché A6 non esiste, un'istantanea versionata nel repository, modificabile solo via PR (ripiego di ondata 1 che non soddisfa DX-22, dichiarato nel catalogo). I valori «proposta da validare» valgono come primo valore valido, con segnale; i valori «da definire» hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione (E3 non gira in produzione). **Fail-closed** (DX-17): variabile mancante, fuori dominio o non leggibile = exit 2.
- **Segreti della CI**: stanno fuori dalla pagina credenziali solo se non danno accesso a dati reali. Condizioni (C11, D6): account o progetto del provider di test **separato dalla produzione**; inventario dei segreti con data di inserimento e rotazione con frequenza `security.credential_rotation_interval_days`; chiavi di produzione mai in CI (catalogo §18).

## 6. Comportamento

**Flusso principale.**
1. Fixture isolata con un seed v2 nuovo, idempotente, che rifiuta la produzione e supporta `--clean`.
2. Esegue ogni caso con la persona indicata (ripetuto `eval.run.repetitions_count` volte, DA-E3-05).
3. Valuta i controlli: risposta, stato del DB, oracolo di memoria per i casi `remember`.
4. Scrive il report e applica il gate: rosso se ≥ 1 controllo bloccante fallisce (nessuna eccezione) o se `pass_rate` dei casi non bloccanti è sotto `eval.gate.pass_rate_min_percent`.

**Crescita dai fallimenti reali.** Ogni fallimento osservato (E4, revisione umana, ticket) diventa un caso con `origin_ref`. I casi non si cancellano; si ritirano solo via PR con motivazione.

**Casi limite.**
- *Fallimento atteso* (`expected_fail_ref`): contato e riportato, non incide sul pass rate mentre l'issue è aperta; quando passa, la CI segnala la promozione a bloccante.
- *Scadenza temporale* (R1): re-seed a ogni run o data fissata (DA-E3-04).
- *Ingestione asincrona* (R4, R5): attesa di `ingestion_status = completed` entro `eval.ingestion.timeout_s`; alla scadenza è errore dell'harness, non fail del caso.
- *Non determinismo*: DA-E3-05.
- *Giudice LLM o provider in errore*: esito «non valutato», gate rosso («un controllo che non gira blocca»). Il giudice, se adottato, usa solo elaborazione nell'UE e riceve solo dati sintetici (DA-E3-09, D6).
- *Caso promosso da produzione*: input riscritto in forma sintetica, con il controllo dei dati personali e la checklist di §4.1, rivisto in PR (DA-E3-08, E10).
- *Record E1 non salvabile*, *variabili non valide o non leggibili*, *tetto di spesa raggiunto* (`eval.run.cost_cap_usd`) o *durata oltre* `eval.run.timeout_s`: casi restanti «non valutati», exit 2.

## 7. Requisiti non funzionali

- **Sicurezza e conformità** (PV-01):
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per i dati delle agenzie (DX-11); E3 non ne tratta: dataset, fixture e input sono solo sintetici (invariante, DA-E3-08), tenant fittizio «Kloud Eval SRL» o equivalente. Prompt e risposte non sono mai catturati in produzione (DA-E1-02), quindi non sono fonte per i casi. Gli identificativi pseudonimi nelle tracce sono dati personali (considerando 26; le linee guida EDPB 01/2025 sono solo in consultazione): per questo `origin_ref` è un riferimento e non una copia. Il termine verso le agenzie per le violazioni (art. 33(2), obbligo del DPA, DA-CV-08) non riguarda E3.
  - *Retention (DX-09, F6).* Classi prodotte: (1) report JSON dei run e (2) segmenti `eval_case`: `retention.eval_reports_months`; (3) golden dataset nel repository: artefatto di configurazione, per la durata del servizio, senza dati personali. Le durate sono di sola lettura finché l'intervallo del DPA non è definito (DA-CV-01); le cancellazioni programmate usano l'ultimo valore valido (DX-17). La copia di riferimento è il segmento E1; la scadenza dell'artefatto GitHub va impostata non oltre `retention.eval_reports_months` (limiti GitHub non verificati). Backup di E1 che contengono i segmenti: scadono entro `retention.data_backup_days` e al ripristino le cancellazioni si riapplicano (DA-CV-22, F6). Evidenze di incidente: eventuali dati di E3 legati a un incidente seguono `retention.incident_evidence_months`, con sospensione solo per i dati di Gravya e non attivabile finché limiti e categorie di F6 non sono definiti (DA-CV-21). Fine contratto ed esportazione (E15): E3 non conserva dati di un tenant, solo dati sintetici e riferimenti; non c'è nulla da esportare con lo strumento di F6 (periodo di recupero e scelta dell'agenzia, `retention.tenant_offboarding_choice`, non riguardano E3).
  - *Perimetro dei dati.* Nessuna piattaforma SaaS di eval o tracing (DA-E3-09). La CI gira su GitHub con soli report minimi su dati sintetici (§4.2) e segreti di un progetto di test separato (DECISIONS §6; DA-E3-11 (a), decisa); la CI self-hosted in UE resta l'alternativa se emergono segreti o artefatti non accettabili fuori dall'UE. Giudice LLM, se adottato (DA-E3-03): elaborazione nell'UE, endpoint non UE rifiutati, solo dati sintetici. I segreti CI rispettano §5. Trasferimenti extra-UE: nessun dato personale è trasferito perché i dati sono sintetici; se in futuro un destinatario ricevesse dati reali varrebbero DA-B2-07 e DA-CV-19 (strumento di trasferimento valido e sub-responsabile autorizzato, anche in UE; il Data Privacy Framework copre solo le organizzazioni USA dell'elenco ed è impugnato, C-703/25 P).
  - *Accessi cross-tenant.* L'unico accesso previsto è la lettura di una singola traccia per promuovere un fallimento, solo per incidente dichiarato o su richiesta di assistenza dell'admin agenzia, con perimetro, durata e log (§5; DX-19, DX-18, E8). Le modifiche alle variabili sono versionate e auditate (DX-13).
  - *NIS2.* Gravya oggi non è soggetto NIS2; per scelta «NIS2 compliant ready by design» (DX-10) valgono come requisiti di progetto le misure del Reg. di esecuzione (UE) 2024/2690, non l'art. 21 della direttiva per log e conservazione. In E3: guardia di produzione (invariante di deploy), nessun bypass RLS, nessuna credenziale nel report, segreti CI separati dalla produzione con inventario e rotazione. Quale sezione del regolamento copra lo sviluppo sicuro non è verificato (Appendice B). E3 non gira in produzione e non è tra i produttori di segnali verso A5 (DX-10); i segnali di incidente restano sempre prodotti e conservati dagli altri sottoprodotti, e il flusso di notifica (preallarme 24 h, notifica 72 h, relazione finale entro un mese, CSIRT Italia, decorrenza dalla conoscenza) è di A5, presente ma non attivo (`incident.nis2_flow_active`). Un fallimento dei casi `refuse` (fuga cross-tenant) in CI blocca il rilascio ed è trattato come vulnerabilità.
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 solo buona pratica, comunque per l'alto rischio dal 2.12.2027 (Reg. 2026/1744). L'art. 50 si applica dal 2.8.2026. L'harness ha casi bloccanti sulle invarianti: (i) ogni output verso terzi porta `ai_generated` con `model` e `prompt_ref` (C1 §4.4); (ii) l'informativa art. 50(1) a chi interagisce con un'IA, alla prima interazione (D6); (iii) l'etichetta «generato da AI» non disattivabile dal tenant. (iv) per il ciclo di tool di un nodo agente, la chiamata a un tool verso terzi senza `ai_generated` negli argomenti è rifiutata da B2 (C1 §4.4 punto 6). Il caso sulla marcatura leggibile da macchina del testo (art. 50(2), D7) si scrive solo quando DA-C1-07 (c) fissa livelli e tecniche dopo la lettura del Codice, **prima del primo rilascio in produzione**: oggi non sono verificati (registro N-AIACT-COM) e non si inventano criteri. Questi casi sono controlli applicati dal codice e dai connettori e verificati da E3: un preambolo del prompt non li sostituisce (rilievo compliance R-08, riguarda E2).
  - *Marketing (PV-01, ePrivacy, Codice privacy artt. 122 e 130).* E3 non invia comunicazioni: i destinatari dei casi sono fittizi. Consensi, opt-out e tracciamento sono di D1–D4 e i loro casi si aggiungono con quei documenti.
  - *Osservabilità AI.* Per ogni run: `git_sha`, `dataset_version`, versioni prompt, `model_ref`, esito per caso e controllo, costo, tutto nel DB di E1 e collegato a `trace_id`.
- **Isolamento**: tenant fixture dedicato; i casi `refuse` verificano l'assenza di dati di altri tenant.
- **Costo**: tetto per run `eval.run.cost_cap_usd`. Il limite di gravya-app ($2, 10 minuti per run agente) è solo riferimento.
- **Riproducibilità**: il report contiene `git_sha`, `dataset_version` e versioni dei prompt.

## 8. Criteri di accettazione

Le soglie citano il catalogo; i campioni dei test sono parametri dei test (DA-CV-04 (b)).

| # | Criterio | Verifica |
|---|---|---|
| AC1 | Il golden dataset iniziale ha la dimensione richiesta dal master (0.3.1) | conteggio dei casi nell'intervallo, parametro del test |
| AC2 | Ogni controllo è binario | il validatore rifiuta campi con punteggio numerico |
| AC3 | Il gate blocca | una PR di prova che degrada un prompt fa uscire il job con 1 |
| AC4 | Gate senza eccezioni sui bloccanti | un solo controllo bloccante fallito dà exit 1 con qualunque valore di `eval.gate.pass_rate_min_percent`; il validatore rifiuta `expected_fail_ref` su un caso con controlli bloccanti; per i non bloccanti, due valori della variabile cambiano l'esito senza modifiche al codice |
| AC5 | Determinismo | 2 run consecutivi sullo stesso SHA danno gli stessi esiti sui controlli `deterministic` (100%) |
| AC6 | Crescita dai fallimenti | il validatore rifiuta `origin=production_failure` senza `origin_ref` |
| AC7 | Guardia di produzione (invariante di deploy) | con `API_ENV=production` exit ≠ 0 prima di qualunque connessione al DB (test unitario); nessuna variabile o pagina UI la modifica |
| AC8 | Tracciabilità | ogni caso del report ha un `trace_id` nel backend E1 |
| AC9 | Errore ≠ pass | con il provider LLM non raggiungibile il job esce con 2 |
| AC10 | Fail-closed sulla registrazione | con E1 non scrivibile, exit 2 e nessun caso pass |
| AC11 | Solo dati sintetici | il validatore rifiuta un caso senza `synthetic: true` |
| AC12 | Variabili fail-closed | con una variabile assente o fuori dominio exit 2 prima di eseguire casi; il report contiene `platform_config_version` |
| AC13 | Report minimo | l'artefatto CI contiene solo i campi di §4.2: nessun testo di input/risposta, dato personale o segreto |
| AC14 | Nessun accesso cross-tenant dalla CI | le credenziali del job non leggono tracce di produzione (test di configurazione); la promozione da `trace_id` richiede il ruolo superadmin e una delle due vie di §5 (incidente dichiarato o richiesta di assistenza), non supera `access.superadmin_trace_access_ttl_hours` e genera 1 riga nel log degli accessi (test d'integrazione quando esistono E1 e A6) |
| AC15 | Segreti CI | test di configurazione: nessuna chiave di produzione nella CI; il provider usato è un progetto di test separato; l'inventario dei segreti ha data di rotazione non oltre `security.credential_rotation_interval_days` |
| AC16 | Giudice nell'UE | la configurazione del giudice rifiuta un endpoint fuori dall'UE (test unitario) |
| AC17 | Art. 50 | casi bloccanti nel dataset che falliscono (exit 1) se un output verso terzi manca di `ai_generated` con `model` e `prompt_ref`, se manca l'informativa art. 50(1) alla prima interazione, o se B2 non rifiuta la chiamata dell'agente a un tool verso terzi senza `ai_generated` |
| AC19 | Controllo dei dati personali (E10) | il validatore rifiuta in blocco un caso con un indirizzo email o un numero di telefono nell'`input` o nell'`assert`; nessuna variabile o opzione lo attenua (test unitario); la checklist è nel template della PR (test di configurazione) |
| AC20 | Esito registrato del gate (E6) | per una versione candidata il run produce l'esito registrato con oggetto, hash del template, esito, `blocking_failures`, `dataset_version` e data; un esito per un hash diverso non è accettato; con fallimenti bloccanti l'esito è negativo (test d'integrazione con lo stub di E2) |
| AC18 | Scadenza dell'artefatto | la scadenza dell'artefatto GitHub impostata nel workflow è non oltre `retention.eval_reports_months` (test di configurazione) |

## 9. Piano di implementazione

**Fasi.**
1. Sciogliere DA-E3-01 e DA-E3-12 (DA-E3-02 e DA-E3-11 sono decise). Riscrivere i 20 scenari di `gravya-app/docs/testing/kloud-eval-scenarios.md` nel formato di §4.1.
2. Costruire seed, fixture, runner e oracolo di memoria (specifica: seed di gravya-app e `kloud_memory_oracle.py`, riferimento, DX-01).
3. Controlli `deterministic`; poi `judge` secondo DA-E3-03.
4. Job CI con gate: per ora i casi non bloccanti sono solo report (DA-E3-07 (b)), i bloccanti bloccano sempre.
5. Aggancio a E1 ed E2, esito registrato del gate, istantanea delle variabili, segreti CI alle condizioni di §5; infine promozione dei fallimenti, casi art. 50 e controllo dei dati personali del validatore.

**Tecnologie.** Python (E16, DA-E3-02 (b): backend tutto in Python; contratti in Pydantic), pytest, GitHub Actions (DA-E3-11 (a)), persistenza nel modello DB-native di E1. Nessun SDK né export OpenTelemetry (PV-02); nessuna piattaforma SaaS di eval (DA-E3-09).

**Rischi.** In §11.

## 10. Test e valutazione

- **Unit**: validatore dei casi, gate e soglia, guardia `API_ENV`, redazione delle credenziali, exit 2 su E1 non scrivibile (AC10) o variabili non valide (AC12).
- **Integration**: run completo su DB effimero (idea da `kloud-eval-seed.realpg.test.ts`).
- **Conformità**: report e record E1 senza testo di risposta né dati personali; AC11, AC13, AC15, AC16, AC17, AC18, AC19, AC20.
- **Eval dell'harness**: mutation test del gate, un prompt rotto produce il rosso (AC3).
- **Security**: i casi X1–X5 sono test di isolamento; nel report non compare alcun segreto.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Esiti instabili, gate ignorato | Controlli deterministici; DA-E3-05 |
| Il giudice LLM sbaglia | Domande binarie strette; campione rivisto a mano (Livello 3 del master); segnale non bloccante |
| Costo della CI | Filtro per percorso; `eval.run.cost_cap_usd` |
| Dataset vecchio | `origin` obbligatorio; crescita dai fallimenti |
| Dati personali reali nei casi promossi | `synthetic` obbligatorio (AC11), controllo dei dati personali in blocco come E2 e checklist in PR (AC19), input scritto dalla descrizione del difetto e non da contenuti |
| Esito del gate non verificabile in produzione da E2 e C1 | Esito registrato per hash (AC20); trasporto dalla CI alla produzione: DA-E3-12 |
| Dati verso provider o piattaforme fuori perimetro | Nessun SaaS; giudice solo UE (AC16) |
| Report CI su GitHub con dati personali | Report minimo (AC13); alternativa: CI self-hosted UE |
| Segreti CI che danno accesso alla produzione | Progetto di test separato, inventario e rotazione (AC15) |
| Eccezioni al gate sui bloccanti | Invariante; `expected_fail_ref` vietato sui bloccanti (AC4) |
| Soglie modificate senza tracciamento | Variabili versionate e auditate, fail-closed (AC12) |
| Accesso improprio alle tracce nella promozione | Condizione DX-19, log, nessuna credenziale di produzione in CI (AC14) |
| Marcatura del testo non verificata | Nessun criterio inventato; caso scritto dopo DA-C1-07 (c), prima del primo rilascio in produzione |
| Runner CI saturi (se condivisi, Non verificato) | Job serializzato o notturno (DA-E3-02) |

## 12. Stima e priorità

- **Taglia**: L. Seed, fixture, oracolo, runner, controlli, gate, agganci E1/E2 e controlli di conformità, tutto da zero (DX-01); le decisioni del 2026-11-04 non la cambiano.
- **Dipendenze critiche**: B1 ed E2 (senza B1 i casi `act` non sono eseguibili; E2 verifica l'esito registrato); C1 per il workflow sotto test; A6 per le variabili (ripiego di ondata 1).
- **Thin-slice MVP**: sì (master 0.3).

---

## Appendice A — Riferimenti dal sistema precedente

Per DX-01/PV-03 nulla di quanto segue entra in v2 come codice. Il contenuto è quello della v1.4, non riletto in v1.5.

**Soluzioni da riprendere come idea:**
- `gravya-app/server/scripts/kloud-eval-seed.ts` e `kloud-eval-fixture.ts`: seed idempotente di un tenant fittizio che passa per le route reali, con guardia `API_ENV` e `--clean`.
- `gravya-app/docs/testing/kloud-eval-scenarios.md`: 20 scenari pass/fail con esito atteso (Read R1–R6, Act A1–A5, Remember M1–M4, Refuse X1–X5) e fallimenti previsti (#2069, #2507, #1685, #2489): requisiti già binari, da riscrivere in §4.1.
- `0375_gravya_agent_policies.sql`: vocabolario `deterministic|judge|hitl`, `block|flag`. `describeDbTarget`: nessuna credenziale nei log.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` §2.10: set di valutazione «manca».

**Difetti da non ripetere:** scenari solo in prosa; nessun workflow di eval in CI; test di integrazione della fixture rimasto rosso (409 `record_archived`, riportato da kloudify); benchmark di memoria a metrica (Recall@k) non binario; scenari centrati sull'assistente Kloud e non su un workflow C1.

## Appendice B — Non verificato

- Stato delle issue #2523, #2489, #2069, #2507, #1685, #892 e del rosso di `kloud-eval-seed.realpg.test.ts`; contenuto di `kloud_memory_oracle.py`, `prompt_improvement_job.py` e dei validatori in `services/agents/src/compliance/`.
- Il workflow del thin-slice; l'ID del sottoprodotto di auto-disable (master 0.4.2); i runner CI condivisi; i valori «master 0.3.1» (non riletti nel master).
- Regione e limiti di conservazione degli artefatti GitHub; dove stiano i segreti della CI se la CI è su GitHub (secret store di un fornitore USA: da valutare in DA-E3-11).
- Quale sezione del Reg. di esecuzione (UE) 2024/2690 copra lo sviluppo e la CI sicuri: non letta per questo documento. Se una fuga di segreti CI sia un segnale verso A5: non deciso (E3 non è produttore in DX-10).
- Marcatura leggibile da macchina del testo (art. 50(2)): numero di strati, tecniche, soglie non verificati (registro N-AIACT-COM, testo del Codice non letto); eccezione per funzione assistiva non valutata. Marketing: artt. 122 e 130 non letti per questo documento (D1–D4).
- Che E3 non conservi dati di un tenant (quindi nulla da esportare con lo strumento di F6, E15): dedotto dalla regola «solo dati sintetici»; da confermare con F6. Il formato dello strumento di esportazione non è fissato (proposta del coordinator in attesa di conferma dell'utente).
- Soglie in stato «proposta da validare» o «da definire» del catalogo (`eval.run.repetitions_count`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s`, e il valore di `eval.gate.pass_rate_min_percent` se il catalogo non è ancora allineato a DA-E3-07 (b)); la corrispondenza tra «zero fallimenti bloccanti» di E3 e «100% di fermate» di C3 (catalogo §16).
- Dove e come si registra l'esito del gate (E6) e se l'estensione alle versioni di workflow di C1 sia voluta (E6 parla di prompt): deduzione. Limiti del controllo dei dati personali: quelli di E2 (pattern base, E2 letto in questo task solo per ricerca).
- Nome e forma del registro delle variabili (A6, non ancora documentato).

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-E3-01 | Primo bersaglio del dataset | (a) scenari Kloud riscritti; (b) workflow thin-slice di C1; (c) entrambi | aderenza al master, requisiti disponibili | (b) come bersaglio del gate; (a) come contenuto per i casi `refuse`/`remember` |
| DA-E3-02 | Linguaggio e posizione del runner | (a) TypeScript accanto alle API v2; (b) Python accanto agli agenti v2 | accesso ad API e runtime, formato contratti (DX-04) | **Decisa (b) (2026-11-04, utente, E16)**: backend tutto in Python. Resta da confermare se la CI di v2 condivide i runner self-hosted di gravya-app |
| DA-E3-03 | Controlli soggettivi in CI | (a) giudice LLM binario (solo UE, DA-E3-09); (b) solo deterministici | affidabilità, costo | (b) per il gate, (a) come segnale non bloccante |
| DA-E3-04 | Date relative (R1) | (a) re-seed a ogni run; (b) data fissata | determinismo | (a) |
| DA-E3-05 | Non determinismo | (a) 1 run; (b) N run e maggioranza; (c) pass solo se N/N | costo contro instabilità | (a) per iniziare; `eval.run.repetitions_count` |
| DA-E3-06 | ~~Collocazione rispetto alla Beta~~ | — | — | **Chiusa da DX-01** |
| DA-E3-07 | Valore di default di `eval.gate.pass_rate_min_percent`. La regola dei bloccanti è decisa: zero fallimenti, invariante (C7 (b)) | (a) valore alto sui non bloccanti più zero bloccanti; (b) solo report sui non bloccanti (valore 0, intervallo 0-100) | il master non fissa un valore; dataset piccolo | **Decisa (b) (2026-11-04, utente, E13)**: per ora solo report sui casi non bloccanti; default 0 nel catalogo (v1.3, al posto di 90) |
| DA-E3-08 | Contenuti di produzione nei casi promossi | — | — | **Decisa (2026-11-03, utente)**: solo dati sintetici; invariante |
| DA-E3-09 | Provider del giudice LLM e piattaforme di eval | — | — | **Decisa (2026-11-03, utente)**: niente SaaS di eval; giudice con elaborazione UE; confermata in D6 |
| DA-E3-10 | ~~Retention di report e segmenti~~ | — | — | **Assorbita da DX-09** |
| DA-E3-11 | Dove gira la CI di E3 | (a) GitHub Actions con report minimi su dati sintetici; (b) CI self-hosted in UE | perimetro UE dei segreti CI e degli artefatti; costo | **Decisa (a) (2026-11-04, utente, E13)** finché i dati sono sintetici e i segreti sono di un progetto di test separato (C11, D6) |
| DA-E3-12 | Come l'esito registrato del gate (E6) arriva all'ambiente di produzione, dove E2 e C1 lo verificano, senza dare alla CI credenziali di produzione (invariante: chiavi di produzione mai in CI). **DA RIPORTARE ALL'UTENTE** (confine CI-produzione, credenziali) | (a) la CI pubblica l'esito come artefatto e un passo di rilascio, fuori dalla CI e con credenziali di produzione, lo importa verificando l'hash; (b) importazione manuale del superadmin con audit; (c) la CI firma l'esito con una chiave dedicata alla firma degli esiti (chiave nella pagina credenziali, due chiavi in parallelo, DA-CV-23) | nessuna credenziale di produzione in CI; non aggirabilità del gate; semplicità | (a); (c) solo se la chiave di firma non dà accesso a dati reali (da valutare con l'utente) |
| DA-C1-07 (di C1) | Marcatura del testo (art. 50(2)) | vedi C1 | — | **Decisa (c) in C1 (E13)**: rinvio alla lettura del Codice, scadenza prima del primo rilascio in produzione; il caso di eval si scrive dopo |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span allineati a E1 (`gravya.eval.*`); dipendenza da E1/OTel resa condizionata a DA-E1-01; aggiunti C1 ed E2 in "È richiesto da"; annotata la citazione kloudify superata dal codice. Motivo: interfacce non combacianti e coerenza con B1/B2. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): fixture, seed, runner e oracolo si costruiscono in v2, gravya-app solo riferimento; Appendice A rinominata "Riferimenti dal sistema precedente" (idee da riprendere, difetti da non ripetere); taglia M→L; DA-E3-06 chiusa da DX-01; DA-E3-01/02/03 riformulate; rimosso il rischio Beta. Applicate DX-02/PV-01/PV-02: rimossi span OTel e OpenTelemetry dalle tecnologie, esiti come record DB-native di E1 con vocabolario `gravya.*`; aggiunta in §7 la voce "Sicurezza e conformità" (GDPR, NIS2, AI Act, osservabilità AI); nessuna piattaforma SaaS di eval di default; nuove DA-E3-08/09/10 da riportare all'utente. (rev. coerenza) record `gravya.eval.case` rinominato segmento `kind=eval_case` (E1 §4.2) in §4, §7, DA-E3-10. |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-E3-08 (solo dati sintetici) e DA-E3-09 (niente SaaS di eval, giudice solo UE) decise: diventano scelte in §4, §6, §7, §9, §10, §11 e nell'Appendice C; aggiunto il campo `synthetic` e AC11. DA-E3-10 assorbita da DX-09: tolta la retention specifica, elencate in §7 le classi di dati prodotte. §7 allineata a DX-10 (notifica incidenti di A5) e DX-11 (Gravya responsabile ex art. 28; non alto rischio: artt. 12/19 solo buona pratica, art. 50 resta); tolta dalla §7 la questione del ruolo titolare/responsabile. Recepito il fail-closed (DA-B2-04/DA-A3-07) come principio anche per gli esiti: record E1 non salvato = exit 2, AC10 e test unitario. DA-E1-05: E1 può adottare i nomi GenAI semconv come vocabolario. Citati DA-B1-06, DA-C1-01/05, DA-E1-02. Taglia L invariata. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09: report e segmenti `eval_case` con default 12 mesi, dataset come artefatto di configurazione (DECISIONS.md §5), applicati da F6. DX-13: soglia del gate, tetto di spesa e timeout diventano variabili di piattaforma gestite dal superadmin, versionate, auditate, fail-closed (§5, §6, AC4, AC12); la promozione di fallimenti da tracce di produzione è un accesso cross-tenant del superadmin con log (DA-E1-08, AC14). DX-14 (A6) citata come dipendenza proposta, da riportare. Decisione §6 "Report CI su GitHub e perimetro UE" resa scelta in §4.2, §7, AC13, test, rischi e Appendice C (registrata come DA-E3-11, ID proposto). Taglia L invariata. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo v1.2 e al registro v1.6. Gate senza eccezioni sui bloccanti (C7 (b)): `expected_fail_ref` vietato sui bloccanti, soglia solo sui non bloccanti (AC4); guardia `API_ENV` come invariante di deploy (DA-CV-11, AC7); variabili rinominate come nel catalogo (`eval.gate.pass_rate_min_percent`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s`, `eval.run.repetitions_count`), valori tolti dal testo; campioni di test come parametri (DA-CV-04); segreti CI in progetto di test separato con inventario e rotazione (C11, D6, AC15); giudice nell'UE (AC16); casi art. 50 (AC17) con la marcatura del testo rinviata a DA-C1-07; promozione di una singola traccia solo su richiesta dell'agenzia o per incidente (DX-19; prima bastava il superadmin); correzioni normative (Reg. 2024/2690 al posto di «NIS2 (art. 21)», flusso NIS2 non attivo, DPF, EDPB 01/2025, calendario AI Act, marketing rinviato a D1–D4); DA-E3-07 e DA-E3-11 riformulate; dipendenze A6 (DX-14 decisa), C1. Motivo: unico giro di revisione prima dell'approvazione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 (2026-11-04) e revisione unica della v1.5. Validatore con controllo dei dati personali come E2, in blocco, checklist in PR e origine dell'input da riscrivere (E10, rilievo compliance R-05, AC19); esito registrato del gate che E2 e C1 verificano all'attivazione (E6, AC20, nuova DA-E3-12 sul trasporto CI-produzione); DA-E3-11 (a), DA-E3-07 (b) solo report con default 0, DA-E3-02 (b) Python (E13, E16); due vie di accesso del superadmin a una singola traccia, incidente dichiarato o assistenza (E8); riferimento corretto al catalogo §11 per `eval.*`; istantanea delle variabili con le regole di E5; dichiarazione che E3 non conserva dati di tenant da esportare (E15); caso art. 50 sul ciclo di tool dei nodi agente (C1 §4.4) e scadenza della marcatura del testo prima del primo rilascio in produzione; tolte le note «non ancora in DECISIONS». Motivo: chiudere la v1.5 prima dell'approvazione dell'utente. |
