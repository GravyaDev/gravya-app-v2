# Code reader: meccanismo di anonimizzazione "per il miglioramento del servizio" in gravya-app v1

- Repository: gravya-app @ `6ac6443c` (HEAD detached; refs locali: `staging`; remote: `origin/staging`; nessuno stash; `git log --all` = 2477 commit raggiungibili da questi due ref, nessun branch non unito trovato).
- Ambito: solo riferimento (PV-03). Nessuna proposta di riuso.
- Gravya-app-kloudify @ `efe366c`: letto solo per tre riferimenti (vedi §Kloudify).

## Sintesi

Non ho trovato in v1 un meccanismo che anonimizzi dati per il miglioramento del servizio (prestazioni LLM, analisi statistica). Non esiste nel codice, nella storia git, nelle migrazioni né nei documenti di compliance di gravya-app.

`services/pii-redactor` esiste ed è un motore locale, ma non è quel meccanismo: è un redattore PII in uscita verso i provider LLM/embeddings (#1504 fase 2), in modalità passthrough di default. Contrariamente a quanto affermato nello scopo ("NON su Presidio"), il suo motore usa Presidio (`presidio_analyzer.AnalyzerEngine` su `spacy.blank("it")`). Il sidecar non persiste nulla e non restituisce mai la corrispondenza placeholder→valore.

Il meccanismo più vicino per "dati dei clienti usati per migliorare" è il ciclo dei learning proposals (`learning_proposals`): raccoglie feedback per company, genera una bozza di prompt di supervisore e richiede approvazione umana. Non anonimizza, non esce dal tenant e non ha retention implementata.

## Risposte

### D1. Dove si trova il meccanismo e che motore usa

**Verificato:** non trovato un meccanismo per il miglioramento del servizio.

Ricerche fatte:
- `git log --all -S "anonimizz"`: 0 commit. `-S "anonymiz"`: 68 commit, tutti con testo di documentazione (Tor "anonymized" in `infra/agent-search/README.md`, descrizione di `presidio-anonymizer` nei doc del redattore, `DeanonymizeEngine` in `docs/compliance/audits/2026-07-24-pii-engine-selection-gdpr.md:209-211`). `-S "anonim"`: 68 commit, tutti con "anonimo"/"anonimità"/"anonimato" (glossario `docs/compliance/glossary.md:60`, "Rule 2: nessun contesto = anonimo = bloccato"). Nessun match nel codice applicativo.
- `git log --all -i --grep="anonim\|pseudonim"`: solo commit che citano il redattore o il contesto Tor.
- `git log --all --diff-filter=D --name-only`: nessun file cancellato con nome riconducibile ad anonimizzazione, analytics, statistiche, telemetria o miglioramento.
- Grep working tree (esclusi node_modules, .git, fixture, corpus): `anonim|anonymi|pseudonim|de-identif` trovano solo commenti del redattore (`services/pii-redactor/pii_redactor/replace.py:1`, `requirements.txt:5`), documenti di compliance, `infra/agent-search`, e `server/src/services/crm-erasure.ts:1479` ("rows are DELETEd, never anonymised", erasure GDPR).
- Grep `miglioramento|improvement|service improvement|analytics|dataset|fine-tun|messa a punto` in `docs`, `server/src`, `services/agents/src`, `packages`: nessun uso che descriva un trattamento per il miglioramento del servizio. Trovato solo il ciclo learning (`docs/compliance/ai-act/system-register.md:81`, "S2 — Self-learning prompt loop") e una nota "Confirm no fine-tuning makes Gravya a GPAI provider" (`docs/compliance/ai-act/system-register.md:259` (📌 non confermata)).

Motore del redattore (`services/pii-redactor`), verificato:
- `services/pii-redactor/pii_redactor/engine.py:1-2`: `"""Presidio AnalyzerEngine (own span replacement) on spacy.blank("it"): no model weights, no network."""`
- `engine.py:14-22`: import di `AnalyzerEngine, RecognizerRegistry`, `SpacyNlpEngine`, `ItFiscalCodeRecognizer`, `IbanRecognizer`, `EmailRecognizer`, `PhoneRecognizer`.
- `services/pii-redactor/requirements.txt:3-5`: `presidio-analyzer>=2.2.364`, `spacy>=3.8.16`; `# presidio-anonymizer is deliberately not used`.
- Riconoscitori locali: liste Wikidata/gazzetteer in `services/pii-redactor/lists/` (`given_names_it.txt`, `surnames_it.txt`, `comuni_it.tsv`, `common_words_it.txt`, `SOURCES.md`); regole regex in `pii_redactor/recognizers.py` e belt deterministico in `pii_redactor/belt.py`.
- Stesso motore dichiarato in `docs/security/pii-redaction.md:3-4`: "a redaction **sidecar** (`services/pii-redactor`: Presidio on `spacy.blank("it")`, no model weights)".

### D2. Dati in ingresso, trasformazioni, reversibilità

**Verificato (redattore):**
- Ingresso: `POST /redact` con `{"text", "session_id"}` (`docs/security/pii-redaction.md:23`; `server.py:26` `REDACT_PATH = "/redact"`). Chiamato solo da `llm_client.py:478` (`kwargs = await redact_litellm_kwargs(kwargs)`, prima della chiamata al provider) e da `embeddings_client.py:164-294` (`redact_outbound`). Il testo è in uscita verso LLM/embeddings, non è un flusso verso una base di dati.
- Trasformazione: span PII → placeholder `[LABEL_n]` numerati per session (`pii_redactor/sessions.py:29-39`, `Session.get`). Chunk di 8000 caratteri (`docs/security/pii-redaction.md:25`).
- Reversibilità: **nessuna**. Il contratto dichiara: `services/agents/src/tools/pii_redaction.py:6`: "`redact(text) -> text` (no mapping returned)". Le rotte del sidecar sono solo `/redact` e `/healthz` (`server.py:26-27`, `:131`, `:136`). Nessun endpoint di ripristino.
- La mappa valore→placeholder esiste solo in memoria: `sessions.py:20` (`self.seen: dict[tuple[str, str], str]`), scartata dopo `PII_REDACTOR_SESSION_TTL_S` (default 600, `server.py:74`) e al massimo `PII_REDACTOR_MAX_SESSIONS` (default 1000, `server.py:75`). Lo stato è pulito in `_purge` solo alla chiamata successiva (`sessions.py:49-53`), quindi può restare in RAM più a lungo del TTL se non arrivano richieste.
- Nessuna tabella di corrispondenza, nessuna chiave di pseudonimizzazione: il token HMAC (`pii_redactor/token.py`) serve solo ad autenticare il chiamante, non a pseudonimizzare.
- Il redattore è spento di default: `docs/security/pii-redaction.md:15` ("`off` (default; also unset, empty, `false`, `0`, `no`, `disabled`) = passthrough"). `docs/compliance/gdpr/ropa.md:1296` dice "outbound PII redaction sidecar ..., not yet switched on".

**Verificato (learning proposals):**
- Ingresso: feedback di un utente su un run del supervisore, via `POST /companies/:companyId/learning-proposals/capture` (`server/src/routes/learning-proposals.ts:138`), con `supervisorId`, `runId`, `feedbackText`.
- Il job `prompt_improvement` (`services/agents/src/job_queue/prompt_improvement_job.py:1-30`) legge il `system_prompt` del supervisore, riproduce la classificazione dei passi con il prompt attuale e con il candidato, e scrive in `learning_proposals` (`evidence`, `candidate`, `diagnosis`). Il testo del feedback è neutralizzato con `kloud.sanitise` (`prompt_improvement_job.py:58-62`). Nessuna anonimizzazione né pseudonimizzazione (non c'è passo di trasformazione per scopo di miglioramento).
- Chiamata LLM della bozza: `_draft_prompt_via_kloud` → `llm_invoke` (`prompt_improvement_job.py:139-208`), quindi passa dal redattore outbound se `enforce` è attivo (`llm_client.py:474-478`).

### D3. Dove finiscono i dati trasformati, chi li usa, retention

**Verificato:**
- Redattore: il testo redatto va al provider LLM o embeddings che l'ha richiesto. Il sidecar non scrive su disco o DB (`server.py` solo `log.info` con metodo, path e status; `server.py:6` "the log line has the method, the path and the status only"). Il testo non viene loggato (`server.py:6`).
- Learning proposals: la tabella `learning_proposals` (`packages/db/src/migrations/0209_learning_proposals.sql`) contiene `candidate.before_content/after_content`, `evidence.input/output_old/output_new`, `reviewed_by_user_id`. Chi li usa: la company admin in review (`ui/src/components/LearningProposalsTab.tsx`), e il save del prompt in `gravya_supervisors` alla approvazione (`server/src/services/learning-proposal-apply.ts:1-30`, passo 4c-4d).
- Retention: **non implementata**. `0209_learning_proposals.sql:34-40`: "DATA RETENTION (GDPR Art 5(1)(e), storage-limitation) ... the TTL/expiry mechanism is DEFERRED to slice-2 (slice-1 has no auto-trigger ...). No expires_at column is added". `docs/compliance/gdpr/ropa.md:127-140` (D4, 🕓 "no TTL/expiry exists in Slice-1") e `ropa.md:1270` (🕓 "learning_proposals retention/TTL (Art.5(1)(e)) deferred to Slice-2"). Grep `expires_at|retention|ttl` in migrazioni/route/job learning: solo il commento di 0209.
- Erasure: `docs/compliance/audits/2026-10-21-scribe-wave-3d.md:340` — `nullLearningProposalsOfClient` (`server/src/services/crm-erasure.ts:437`) azzera i dati del cliente nella erasure per soggetto (#2108/#2129). Verificato solo dal record di audit, non ho riletto `crm-erasure.ts:437`.
- Nessun job di miglioramento o analisi che legga `learning_proposals` fra tenant. Non ho trovato query cross-tenant su quella tabella (ricerca `grep learning_proposals` su `server`, `services`, `packages`: solo i file citati sopra; non ho aperto tutti i risultati).

### D4. Isolamento tra tenant, consenso o opt-in dell'agenzia

**Verificato (isolamento):**
- `learning_proposals` è `FORCE ROW LEVEL SECURITY` con policy `_tenant_isolation` per `company_id` (`0209_learning_proposals.sql` header; `packages/db/src/schema/learning_proposals.ts:1-30`: "company-scoped (F30/F31 model)").
- Il capture verifica che il supervisore appartenga alla company (`learning-proposals.ts:150-164`), e rifiuta i seed globali (`seed_immutable`).

**Non trovato (consenso/opt-in):** nessun consenso, opt-in o toggle per "miglioramento del servizio" nel codice o nei documenti di compliance (ricerche in D1). La base del trattamento dei learning proposals è il ciclo HITL con approvazione dell'admin (`system-register.md:81-90`), non un consenso. Il redattore non ha opt-in: è un controllo di minimizzazione, attivo con una variabile d'ambiente.

### D5. Incompleto (TODO, issue, test mancanti) e documenti di compliance

**Verificato:**
- Retention dei learning proposals: non implementata, rinviata a "slice-2" (`0209_learning_proposals.sql:34-40`; `ropa.md:127-140`, `ropa.md:1270`).
- Redattore: `docs/security/pii-redaction.md:115-118` ("Not covered here": egress diversi da LLM/embeddings e qualità del retrieval su embedding redatti "tracked separately"). Sezione "SIGTERM (r4, observed, not changed)" con residuo "Both are follow-ups on #2501" (`docs/security/pii-redaction.md:78-87`).
- Redattore, provider Mistral (fuori domanda, citato perché tocca i dati vocali): `docs/compliance/gdpr/ropa.md:1094`: "No code enforces this condition" (nessun controllo nel codice sul piano del provider).
- Documenti di compliance su anonimizzazione o pseudonimizzazione: `docs/compliance/audits/2026-07-24-pii-engine-selection-gdpr.md:50-56`: "it **REDUCES** identifiers ... The scrubbed output remains **personal data** (GDPR Recital 26) ... the technique is **pseudonymisation, not anonymisation** (EDPB)." Stessa conclusione in `docs/compliance/audits/2026-10-24-scribe-wave-4k.md:23` (Presidio su `spacy.blank("it")`). Non esistono `docs/compliance/*` sul miglioramento del servizio.
- Il record `ai-act/system-register.md:81-197` documenta S2 (ciclo di auto-apprendimento) senza nessuna finalità di miglioramento del servizio. La finalità dei learning proposals è il prompt del singolo supervisore, dello stesso tenant.

**Non trovato:** issue o test che descrivano un meccanismo di anonimizzazione per il miglioramento del servizio. Gli unici test di redazione sono di log/errore/feedback e del redattore (`services/agents/tests/unit/test_1504_pii_redaction.py`, `services/pii-redactor/tests/`).

### D6. Rapporto con learning-proposal-apply.ts, prompt_improvement_job.py e services/pii-redactor

**Verificato:**
- `learning-proposal-apply.ts`: è il saga di approvazione (`:1-30`). Scrive `gravya_supervisors.system_prompt` (passo 4c) e `gravya_supervisor_prompt_revisions` (passo 4d). Non chiama il redattore. Non tocca dati di altri tenant (passo 4a: refused se company diversa).
- `prompt_improvement_job.py`: genera bozze e replay, dipende dal redattore solo indirettamente, tramite `llm_invoke` → `redact_litellm_kwargs` (`llm_client.py:478`) quando `GRAVYA_PII_REDACTION=enforce`.
- `services/pii-redactor`: indipendente dal ciclo learning, non lo chiama e non ne riceve dati direttamente. Il rapporto è solo "stessa catena di chiamate LLM".
- Conclusione: i due non sono lo stesso meccanismo né si passano dati di miglioramento. Il redattore minimizza il testo inviato all'LLM; il ciclo learning salva feedback e bozze nel tenant.

## Kloudify (riferimento, perimetro ridotto)

- `docs/visione/architettura-agenti.md:227-230` (gravya-app-kloudify@`efe366c`): "**Uso dei dati dei clienti per la messa a punto:** la messa a punto è nostra, ma oggi nulla raccoglie prompt e risultati dei clienti. Prima di raccoglierli, anche ripuliti, va documentato legalmente (ruolo, base giuridica, clausola del contratto, anonimizzazione, conservazione): appunti in gravya-app#1925." Questo contraddice l'affermazione dello scopo che esista già un meccanismo in v1. Il rimando a "gravya-app#1925" non compare nella storia di gravya-app (`git log --all | grep 1925`: nessun risultato).
- `.claude/reports/2026-07-04-presidio-decision-brief.md:17, 67, 88`: la brief del 2026-07-04 diceva "Presidio (self-hosted): not a dependency today" e proponeva un regex-port per v1. Poi Presidio è stato adottato (`docs/compliance/audits/2026-07-24-pii-engine-selection-gdpr.md:1-11`).

## Contraddizioni

1. `services/pii-redactor/pii_redactor/engine.py:1-2` (Presidio) | `docs/security/pii-redaction.md:3-4` (Presidio) | scopo del coordinatore ("motore locale e NON su Presidio"): il codice dice Presidio; la domanda dell'utente parte da un'ipotesi diversa.
2. `gravya-app-kloudify/docs/visione/architettura-agenti.md:227-230` ("oggi nulla raccoglie prompt e risultati dei clienti") | scopo del task (utente: "in v1 esisteva un meccanismo non terminato che anonimizzava i dati a fini di miglioramento del servizio"): la documentazione dice che non esiste.
3. `.claude/reports/2026-07-04-presidio-decision-brief.md:67` ("Presidio (self-hosted): not a dependency today") | `services/pii-redactor/requirements.txt:3` (`presidio-analyzer`): data diversa, il codice è cambiato. Non è una contraddizione grave ma va datata.
4. `docs/compliance/gdpr/ropa.md:127-140` (D4: `learning_proposals` è "per-customer", finalità di prompt improvement) | `docs/compliance/ai-act/system-register.md:85-90` (finalità: "proposes prompt/config improvements"): coerenti fra loro; nessuna contraddizione interna trovata.

## Non trovato

- Un meccanismo di anonimizzazione o pseudonimizzazione per il miglioramento del servizio (prestazioni LLM, analisi statistica) in gravya-app @ `6ac6443c`: nessun file, tabella, job, rotta, branch, PR o documento di compliance. Ricerche: `git log --all -S` (anonimizz, anonymiz, anonim), `git log --all --grep` (anonim, pseudonim, improv, analytic, dataset, fine-tun, tuning), `--diff-filter=D`, grep working tree su `anonim|anonymi|pseudonim|miglior|improv|analytic|statistic|aggregat|dataset|fine-tun|opt-in|consent|consens`.
- Consenso o opt-in dell'agenzia per usare i dati a fini di miglioramento: non trovato.
- Tabella di corrispondenza persistente o chiave di reversibilità: non trovata. La mappa del redattore è solo in RAM (`sessions.py`).
- Retention del redattore: non applicabile (nessun dato persistito). Retention dei learning proposals: non implementata (0209, ropa D4).
- Cosa "non terminato" l'utente intende: non trovato. Il TODO più vicino è la retention dei learning proposals (0209 e ropa D4), ma non è un meccanismo di anonimizzazione.
- Issue #1925 citata in Kloudify: non nella storia di gravya-app (non letta su GitHub).
- Ho solo verificato con grep la riga `crm-erasure.ts:437` (`nullLearningProposalsOfClient`), oltre alla citazione nel record di audit `2026-10-21-scribe-wave-3d.md:340`.

## Fuori perimetro

- `docs/compliance/gdpr/ropa.md:1076-1094` e `privacy-notice-draft-sources.md:115`: il trasferimento di audio vocale a Mistral dipende da un controllo non implementato nel codice ("No code enforces this condition", `ropa.md:1094`). Non è domanda di questo task.
- Nessun segreto o credenziale trovato in questa lettura. Il test vector (valore non riportato) in `docs/security/pii-redaction.md:40` è un test vector dichiarato come tale (secret `test-internal-secret`), non un segreto reale.
- Nessuna istruzione diretta a un agente trovata nei file letti.

## Letture

| File | Righe lette |
| --- | --- |
| services/pii-redactor/pii_redactor/engine.py | 1-80 di 106 (grep sul resto) |
| services/pii-redactor/pii_redactor/sessions.py | 1-73 di 73 |
| services/pii-redactor/pii_redactor/token.py | 1-23 di 23 |
| services/pii-redactor/pii_redactor/server.py | 20-30, 74-86 (grep sul resto) |
| services/pii-redactor/requirements.txt | grep |
| docs/security/pii-redaction.md | 1-118 di 118 |
| docs/compliance/audits/2026-07-24-pii-engine-selection-gdpr.md | 1-60 di 344 |
| server/src/services/learning-proposal-apply.ts | 1-60 di 386 |
| server/src/routes/learning-proposals.ts | 120-175 di 494 |
| services/agents/src/job_queue/prompt_improvement_job.py | 1-120 di 549 |
| services/agents/src/tools/llm_client.py | 474-482 di ~2000 |
| services/agents/src/tools/pii_redaction.py | solo grep |
| packages/db/src/migrations/0209_learning_proposals.sql | 1-40 di ? |
| packages/db/src/schema/learning_proposals.ts | 1-40 di 95 |
| server/src/services/feedback-redaction.ts | 1-50 di 193 |
| docs/compliance/gdpr/ropa.md | 127-140 e 1270, 1296 (grep sul resto) |
| docs/compliance/ai-act/system-register.md | 81-90, 242-243 (grep sul resto) |
| docs/compliance/audits/2026-10-21-scribe-wave-3d.md | solo grep riga 340 |
| gravya-app-kloudify/docs/visione/architettura-agenti.md | 222-236 di ? |
| gravya-app-kloudify/.claude/reports/2026-07-04-presidio-decision-brief.md | solo grep |
| Storia git gravya-app | `git log --all -S`, `--grep`, `--diff-filter=D`, `for-each-ref` |

Commit letti: gravya-app `6ac6443c`; gravya-app-kloudify `efe366c`.
