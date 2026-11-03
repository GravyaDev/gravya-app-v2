# E3 — Eval harness offline

## 1. Identità

| Campo | Valore |
|---|---|
| ID | E3 |
| Nome | Eval harness offline |
| Componente padre | E — Osservabilità e Valutazione |
| Versione documento | 1.1 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

## 2. Scopo

**Cosa fa.** È un runner che gira in CI. Esegue un golden dataset di casi contro il workflow del thin-slice e calcola per ogni caso un esito binario pass/fail. Blocca la PR o il deploy quando il pass rate scende sotto la soglia o quando un caso marcato come bloccante fallisce (master §5 Livello 1, voci 0.3.1–0.3.3).

**Cosa NON fa.**
- Non valuta il traffico di produzione: quello è E4 (Eval online).
- Non assegna voti su scala tipo 1–5 o "la risposta era buona?". Ogni controllo è una domanda specifica con risposta sì/no (master §2, osservabilità).
- Non sostituisce i test unitari e di integrazione esistenti, né il gate di conformità sull'output a runtime (`gravya_agent_policies`, slice 1 di #892).

**Perché esiste.** Il master dice che senza eval non si può concedere autonomia in modo sicuro. La visione in kloudify, invece, registra il set di valutazione come "assente" e afferma che "il set è il primo pezzo da costruire".

## 3. Contesto e dipendenze

**Dipende da:**
- **E2** (Prompt registry): ogni run deve registrare la versione del prompt e del modello usati, e una PR che cambia un prompt deve far scattare E3.
- **E1** (Tracing distribuito): gli esiti vengono attaccati agli span OTel (condizionato a DA-E1-01: il codice esistente esclude OTel). Questo lascia aperta la via verso E4 senza lock-in di vendor.
- **B1** (Agent runtime isolato): l'harness esegue il caso dentro il runtime reale e non su un mock.
- **B2** (Tool gateway): i casi di tipo "Act" e "Refuse" si verificano sull'effetto o sul diniego dei tool.
- **A3** (Runtime enforcement): i casi di rifiuto verificano i dinieghi.
- **C1** e **C3**: il workflow sotto test e il punto HITL. I casi che arrivano all'HITL devono avere un esito atteso deterministico.

**È richiesto da:** C1 (eval gate prima della pubblicazione di una versione), E2 (hook di promozione, secondo DA-E2-04), E4 (riusa il formato dei controlli binari), il rollout con eval gate attive (master 2.1.2, ondate successive), la suite estesa (master 3.3.1) e il trigger di auto-disable su eval cattive (master 0.4.2, ID non assegnato nel master: Non verificato).

**Assunzioni:**
- Il workflow del thin-slice non è ancora scelto in modo formale. Questo documento assume come primo bersaglio Kloud, perché in gravya-app esiste già una fixture dedicata (vedi Appendice A). Lo sciolgo in DA-E3-01.
- La CI resta GitHub Actions sui runner self-hosted esistenti. Regola kloudify (15/10): non proporre runner aggiuntivi su quella macchina.

## 4. Contratti

### 4.1 Caso del golden dataset (proposta da validare)

| Campo | Tipo | Note |
|---|---|---|
| `id` | string stabile | es. `R1`, `X4` (convenzione di `kloud-eval-scenarios.md`) |
| `area` | enum | `read` / `act` / `remember` / `refuse` (dalle 4 aree esistenti) |
| `persona` | enum | `admin` / `member` / `client` (`EvalPersona` in `kloud-eval-fixture.ts`) |
| `input` | string o turni | richiesta dell'utente |
| `checks[]` | lista | ogni controllo: `check_id`, `type` (`deterministic`/`judge`), `assert`, `blocking` (bool) |
| `origin` | enum | `seed` / `production_failure` / `bug_report` |
| `origin_ref` | string | trace id (E1) o numero di issue, obbligatorio se `origin` ≠ `seed` |
| `expected_fail_ref` | string opzionale | issue che prevede il fallimento (es. #2489 per X4–X5) |

I valori `deterministic`/`judge` e `block`/`flag` riprendono il vocabolario di `gravya_agent_policies` (migrazione 0375). Non riuso `hitl`, perché in CI non c'è un umano. Lo tratto in DA-E3-03.

### 4.2 Output di un run

È un file JSON con questi campi: `run_id`, `git_sha`, `prompt_versions` (da E2), `model_ref`, `dataset_version` e, per ogni caso, `pass` (bool), `failed_checks[]` e `trace_id`. A questi si aggiungono gli aggregati `pass_rate` e `blocking_failures`. Exit code: 0 = gate verde, 1 = gate rosso, 2 = harness in errore (che conta comunque come rosso).

### 4.3 Eventi

L'harness emette uno span `gravya.eval.case` per caso con gli attributi `gravya.eval.case_id` e `gravya.eval.pass` (nomi allineati a E1 §4.1). Non consuma eventi di bus.

## 5. Interfacce

- **CLI**: `eval run --dataset <path> [--cases R1,X4] [--report out.json]`. Il nome del comando e il package sono da decidere in DA-E3-02.
- **CI**: un job dedicato, eseguito sulle PR che toccano prompt, modello, tool od orchestrazione (master §5). Il filtro per percorso va derivato da E2 e B2.
- **Promozione di un fallimento**: un comando o template che crea un caso con `origin=production_failure` a partire da un `trace_id`. Il caso entra nel dataset tramite PR con revisione umana.

## 6. Comportamento

**Flusso principale.**
1. Prepara la fixture isolata. Il seed esistente è idempotente, rifiuta la produzione e usa `--clean`.
2. Esegue ogni caso con la persona indicata.
3. Valuta i controlli: risposta, stato del DB e oracolo di memoria per i casi `remember`.
4. Scrive il report e applica il gate.

**Crescita dai fallimenti reali.** Ogni fallimento osservato in produzione (da E4, dalla revisione umana o da un ticket) diventa un caso con `origin_ref`. I casi non si cancellano. Un caso si ritira solo tramite PR con motivazione.

**Casi limite.**
- *Fallimento atteso* (`expected_fail_ref`): il caso viene contato e riportato, ma non blocca finché l'issue è aperta. Quando passa, la CI segnala che il caso va promosso a bloccante.
- *Scadenza temporale*: R1 vale circa 20 giorni dopo il seed. L'harness rifà il seed a ogni run, oppure fissa la data (DA-E3-04).
- *Ingestione asincrona dei documenti* (R4, R5): l'harness attende `ingestion_status = completed`. Se scade il timeout, l'esito è errore dell'harness e non fail del caso.
- *Non determinismo del modello*: vedi DA-E3-05.
- *Errore del giudice LLM o del provider*: l'esito è "non valutato" e il gate è rosso. Il master non lo dice; segue il principio kloudify "un controllo che non gira blocca".

## 7. Requisiti non funzionali

- **Sicurezza**: si esegue solo su un DB non di produzione. Si riusa la guardia `API_ENV` del seed, e nel report non compaiono credenziali (come in `describeDbTarget`). Nessun bypass RLS aggiunto.
- **Isolamento**: la fixture è un tenant dedicato ("Kloud Eval SRL"). I casi `refuse` verificano che nessun dato di un altro tenant compaia.
- **Costo**: è previsto un tetto di spesa per run (valore: proposta da validare). Va rispettato il limite A6 di $2 e 10 minuti per run agente registrato in kloudify.
- **Osservabilità**: ogni caso ha un `trace_id` E1 navigabile.
- **Riproducibilità**: il report contiene `git_sha`, `dataset_version` e le versioni dei prompt E2.

## 8. Criteri di accettazione

| # | Criterio | Verifica |
|---|---|---|
| AC1 | Il golden dataset iniziale ha 10–30 casi (master 0.3.1) | conteggio dei casi nel dataset ≥ 10 e ≤ 30 |
| AC2 | Ogni controllo è binario | test di validazione dello schema: rifiuta campi con punteggio numerico |
| AC3 | Il gate blocca | una PR di prova che degrada un prompt fa fallire il job CI (exit 1) |
| AC4 | Soglia | gate rosso se `pass_rate` < 90% sui casi non attesi-falliti, oppure se ≥ 1 caso bloccante fallisce (**90%: proposta da validare**) |
| AC5 | Determinismo dell'harness | 2 run consecutivi sullo stesso SHA danno gli stessi esiti sui controlli `deterministic` (100%) |
| AC6 | Crescita dai fallimenti | il validatore rifiuta un caso con `origin=production_failure` privo di `origin_ref` |
| AC7 | Guardia produzione | con `API_ENV=production` l'harness esce ≠ 0 prima di qualunque connessione al DB (test unitario) |
| AC8 | Tracciabilità | ogni caso del report ha un `trace_id` presente nel backend E1 |
| AC9 | Errore ≠ pass | con il provider LLM non raggiungibile il job è rosso (exit 2) |

## 9. Piano di implementazione

**Fasi ordinate.**
1. Sciogliere DA-E3-01 e DA-E3-02. Convertire i 20 scenari di `docs/testing/kloud-eval-scenarios.md` nel formato di §4.1, con i controlli DB già scritti nel file.
2. Scrivere il runner via API che `kloud-eval-scenarios.md` dichiara come "later PRs", riusando seed, fixture e `kloud_memory_oracle.py`.
3. Implementare i controlli `deterministic` (stato del DB, presenza o assenza di nomi). Poi i controlli `judge` secondo DA-E3-03.
4. Aggiungere il job CI con il gate, inizialmente in modalità report-only fino alla soglia di AC4, poi bloccante.
5. Aggiungere l'aggancio a E1 (span) ed E2 (versioni). Infine il flusso di promozione dei fallimenti.

**Tecnologie.** Sono quelle già nel codice: TypeScript/tsx (seed), Python (oracolo, benchmark), vitest/pytest, GitHub Actions self-hosted, OpenTelemetry (master). Il master cita solo una "piattaforma eval" generica: nessun vendor è scelto, ed è coerente con il no lock-in.

**Rischi.** Sono elencati in §11.

## 10. Test e valutazione

- **Unit**: validatore dello schema dei casi, calcolo di gate e soglia, guardia `API_ENV`, redazione delle credenziali.
- **Integration**: run completo su DB effimero (modello realpg esistente: `kloud-eval-seed.realpg.test.ts`).
- **Eval dell'harness**: "mutation test" del gate, cioè un prompt volutamente rotto deve produrre il rosso (AC3).
- **Security**: i casi X1–X5 sono essi stessi test di isolamento. In più, nel report non compare alcun segreto.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Esiti instabili (modello non deterministico) → gate ignorato | Controlli deterministici dove possibile; DA-E3-05 |
| Il giudice LLM sbaglia | Il giudice è limitato a domande binarie strette; campione rivisto a mano (Livello 3 del master) |
| Costo della CI | Il gate scatta solo su PR rilevanti (filtro per percorso); tetto di spesa |
| Il dataset diventa vecchio | `origin` obbligatorio; crescita dai fallimenti; scadenza di R1 gestita |
| Conflitto con la priorità Beta | DA-E3-06 |
| Runner CI saturi (2 self-hosted) | Nessun runner nuovo; job serializzato o notturno da decidere in DA-E3-02 |

## 12. Stima e priorità

- **Taglia**: M. La fixture e gli scenari esistono già. Mancano il runner, i controlli, il gate e gli agganci E1/E2.
- **Dipendenze critiche**: B1 (eseguire davvero gli agenti) ed E2 (versioni). Senza B1 i casi `act` non sono eseguibili. Kloudify registra che l'enforcement è "irraggiungibile finché gli agenti non eseguono i tool"; nota di revisione: il codice al commit `349118b11` ha un ciclo di tool (`_run_tool_loop` in `generic_executor.py`), quindi la frase di kloudify è superata sul codice, mentre resta Non verificato se il percorso sia raggiunto in staging.
- **Thin-slice MVP**: sì (master 0.3).

---

## Appendice A — Allineamento con lo stato attuale

**Esiste (letto):**
- `gravya-app/server/scripts/kloud-eval-seed.ts` e `kloud-eval-fixture.ts` (#2523, PR 1): seed idempotente del tenant fittizio "Kloud Eval SRL" (17 clienti, 22 note, 6 documenti KB, 3 persone) passando per le route reali. Ha guardia `API_ENV` e `--clean`. Riusabile così com'è.
- `gravya-app/docs/testing/kloud-eval-scenarios.md`: 20 scenari pass/fail con esito atteso scritto prima del run (Read R1–R6, Act A1–A5, Remember M1–M4, Refuse X1–X5) e fallimenti previsti (#2069, #2507, #1685, #2489). È già un golden dataset nel senso del master, ma in prosa: manca il formato macchina. Dichiara che il runner via API è una PR successiva.
- `gravya-app/server/src/__tests__/kloud-eval-db-target.test.ts` e `kloud-eval-seed.realpg.test.ts`. Il secondo è tra i "rossi" dell'onda 4t (409 `record_archived`) secondo `gravya-app-kloudify/.claude/memory.md`, come riportato in `docs/stato/kloudify.md`.
- `gravya-app/services/agents/src/benchmarks/` (`golden_set.json` con 5 casi, `memory_recall.py` Recall@k/Precision@k) e l'handler `c2_memory_benchmark.py`: benchmark del solo retrieval, a metrica e non binario.
- `gravya-app/packages/db/src/migrations/0375_gravya_agent_policies.sql`: criteri per agente `deterministic|judge|hitl`, `block|flag`. Riusabile come vocabolario dei controlli.
- `gravya-app-kloudify/docs/visione/architettura-agenti.md` §2.10: il set di valutazione e il controllo periodico sono marcati "manca".
- `gravya-app/.github/workflows/`: nessun workflow di eval.

**Divergenze dal master:**
1. Il master mette l'eval harness nelle fondamenta (fase 0). La visione kloudify lo vuole come "primo pezzo", ma la regola del 02/11 sposta a post-Beta ciò che non tocca sicurezza o primo cliente, e secondo la ricognizione l'eval è già classificata post-Beta.
2. Il master prevede un gate CI che blocca il deploy. Oggi non c'è alcun runner automatico, ma solo esecuzione manuale da tester. La CI ha 2 runner self-hosted e la regola vieta di aggiungerne.
3. Il master prevede eval binarie. Il benchmark di memoria esistente è a metrica (Recall@k): non va usato come gate senza convertirlo.
4. Il master parla di un golden dataset "per il workflow" del thin-slice. Gli scenari esistenti coprono Kloud (assistente), non un workflow C1 ad alto volume.

## Appendice B — Non verificato

- Se esista già, in un branch o PR aperta, il runner via API di #2523 (cercato solo su questa copia di gravya-app).
- Lo stato attuale delle issue #2523, #2489, #2069, #2507, #1685, #892.
- Lo stato reale del rosso `kloud-eval-seed.realpg.test.ts` nell'onda 4t (riportato da kloudify, non riprodotto).
- Il contenuto completo di `kloud_memory_oracle.py`, `prompt_improvement_job.py` (REPLAY) e dei validatori in `services/agents/src/compliance/` (non letti per intero).
- Quale sia il workflow del thin-slice per v2.
- L'ID del sottoprodotto che implementa l'auto-disable (master 0.4.2).
- La classificazione post-Beta dell'eval in `docs/visione/`, ripresa dalla ricognizione kloudify e non riletta riga per riga.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-E3-01 | Primo bersaglio del dataset | (a) scenari Kloud esistenti; (b) workflow thin-slice di C1; (c) entrambi | riuso contro aderenza al master | (a) subito, (b) appena C1 sceglie il workflow |
| DA-E3-02 | Linguaggio e posizione del runner | (a) TS in `server/scripts` accanto al seed; (b) Python in `services/agents` accanto all'oracolo | riuso, accesso alle route e agli agenti | (a): il seed importa già le route |
| DA-E3-03 | Controlli soggettivi in CI | (a) giudice LLM binario; (b) solo deterministici, i soggettivi vanno a revisione umana fuori CI; (c) giudice = supervisore esistente | affidabilità e costo | (b) per il gate, (a) come segnale non bloccante |
| DA-E3-04 | Date relative (R1) | (a) re-seed a ogni run; (b) data di riferimento fissata | determinismo e durata | (a) |
| DA-E3-05 | Non determinismo | (a) 1 run, temperatura minima; (b) N run e maggioranza; (c) pass solo se N/N | costo contro instabilità | (a) per iniziare; N da validare |
| DA-E3-06 | Collocazione rispetto alla Beta del 30/11 | (a) anticipare in v2 come da master; (b) post-Beta come da kloudify | la decide Daniele | escalation; nessuna raccomandazione tecnica |
| DA-E3-07 | Soglia del gate | (a) 90% + zero bloccanti; (b) 100% sui bloccanti, solo report sul resto | il master non fissa un valore | (b) finché il dataset è piccolo |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: attributi dello span allineati a E1 (`gravya.eval.*`); dipendenza da E1/OTel resa condizionata a DA-E1-01; aggiunti C1 ed E2 in "È richiesto da"; annotata la citazione kloudify superata dal codice. Motivo: interfacce non combacianti e coerenza con B1/B2. |
