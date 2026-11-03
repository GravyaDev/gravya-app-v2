# Ricognizione del repo di stato gravya-app-kloudify (2026-11-03)

Legenda: **[L]** = letto nel file citato · **[D]** = mia deduzione · **[NV]** = non verificato.
Commit di testa del repo: `e43f15e3` (2026-11-02 21:37, «record the 2026-11-03 order…»). Ho letto: `README.md`, `CLAUDE.md` (solo l'inizio), `Task Board.md`, `Scratchpad.md`, `.claude/memory.md`, `Daily Notes/2026-11-02.md` (la fine), `docs/visione/README.md`, `docs/visione/architettura-agenti.md`, `docs/visione/controlli-e-conformita.md`, e con grep `docs/codebase-summary.md`. **Non** ho letto: `.claude/kloudify/CLAUDE.core.md` (payload gitignored, non presente nel clone), la KB `.claude/knowledge-base*`, i piani `.claude/plans/`, `docs/Meta references/`.

## 1. Cos'è Kloudify e come governa lo sviluppo

- [L] `README.md`: il repo è «the machine layer for the Gravya product»: stato, piani, KB, daily notes. **Non contiene codice applicativo**: server/ui/services/docker/scripts e la documentazione di prodotto stanno in `GravyaDev/gravya-app`. Qui: `.claude/`, `Daily Notes/`, `Task Board.md`, `Scratchpad.md`, `docs/`.
- [L] Kloudify è un «payload» (hook, comandi, agenti, skill) prodotto dal repo `GravyaDev/Kloudify`, installato per macchina in `.claude/kloudify/` (gitignored), modalità `downstream-self-state`. Gli upgrade sono «automatici e obbligatori» a `/start`, solo tag stabili. Versione in uso: v5.26.0, v5.30.0 da installare (`.claude/memory.md`).
- [L] `CLAUDE.md` impone di leggere `.claude/memory.md` prima di agire e include `CLAUDE.core.md` (regole Kloudify, non leggibili qui).
- [L] Modello operativo (da `.claude/memory.md` e `Daily Notes/2026-11-02.md`): un coordinatore AI («XO», account `kloud-ai`) con peer/sotto-agenti esecutori, uno «scriba» e un «tester»; lavoro in **onde** di PR (4r, 4s, 4t, 4u) con PR d'onda, giri di revisione (verdetto `DRAIN-VERDICT`, `SCRIBE-ACK`), CI su 2 runner self-hosted, script `land-wave.sh`, `wave-ci-delta.sh`, `wave-verify.sh`. Molti gate/hook (122 dinieghi registrati il 02/11).
- [L] Governance umana: **Daniele decide la coda direttamente** (banner in `Task Board.md`: il «Director» non esiste dal 2026-08-13; le righe che lo citano sono storiche).
- [L] **Unico punto di lettura del pianificato: issue `GravyaDev/gravya-app#1508`** (label `roadmap`); file locali di roadmap non autorevoli (`Task Board.md`, sezione Plans, 2026-09-30). La roadmap è generata da `.claude/roadmaps/gravya-app.json` con `bin/roadmap.py` [L in memory/daily note; file non aperto].

## 2. Stato attuale

**Task Board** [L]: è soprattutto un registro storico. Sezione Plans vuota per scelta; voci aperte residue (cron delle automazioni editabile — marcata pre-Beta; rigenerazione Graphify; follow-up UX Boards; suite docker-pg sul runner); upstream monitorati (Coolify #10676, Kloudify, claude-peers-mcp); log di flotte concluse (22/10, 24/10). Nessuna voce riguarda i 9 temi dell'ondata 1.

**Scratchpad** [L]: vuoto (svuotato il 2026-08-24).

**Ultime Daily Notes** [L]: l'ultima è `Daily Notes/2026-11-02.md`; **non esiste una nota 2026-11-03**. Il 02/11: fuse le onde 4r (PR gravya-app#3049, 56 membri) e 4s; onda 4t aperta (PR #3102, 19 membri) con 3 rossi in CI; riordino issue (38 chiuse/accorpate, roadmap ricostruita con fasi Beta e post-Beta); scansione sicurezza 0 CRITICAL/0 HIGH; flotta ridotta allo scriba.

**`.claude/memory.md`** [L]: **Beta entro il 30/11/2026**. Roadmap al 02/11 sera: «Beta 15/160, post-Beta 0/130»; 126 voci Beta «vere» aperte. DeepSeek acceso per agenti singoli con verificatore Sonnet.

## 3. Regole Beta e ordine dei lavori per il 2026-11-03

[L] `.claude/memory.md`, ordine di Daniele (verbatim citato lì: «Domani priorità Kloudify v5.30.0, poi Rossi della 4t, CI, etichette, tester e 4u.»):
1. upgrade Kloudify v5.30.0 (solo tag stabile);
2. **taglio della Beta** sulla roadmap #1508: ciò che rallenta va post-Beta con una propria issue; sicurezza e permessi restano; poi sync/render/post e numero di voci Beta + data stimata a Daniele;
3. fix dei tre rossi della 4t (realpg `kloud-eval-seed.realpg.test.ts` per 409 `record_archived`; `verify` sul gate read-audit CRM; `e2e` `mobile-editors.spec.ts`); 4) delta CI e merge 4t; 5) etichette tester e post-land; 6) tester; 7) onda 4u.

**Regole in vigore dal 02/11 sera** [L]:
- i rilievi delle revisioni diventano issue Beta **solo** se toccano sicurezza, isolamento fra agenzie, perdita di dati o il percorso del primo cliente; il resto è post-Beta;
- prima della CI di un'onda si eseguono in locale i controlli `policy` (no-paperclip, agents-lock-hashes, tenant-rls, i18n-gate + smoke, writing-routes);
- ogni sera una riga a Daniele: voci Beta aperte/chiuse/nuove e ritmo necessario per il 30/11.
Altre regole vive: mai proporre runner CI aggiuntivi su quella macchina (15/10); domande per openapi.it accumulate in `.claude/reports/domande-per-openapi-it.md`.

[D] Tutto l'ordine del 03/11 riguarda gravya-app (Beta su v1); **nessun punto menziona gravya-app-v2** né i temi dell'ondata 1.

## 4. Decisioni e vincoli in docs/ rilevanti per i 9 temi

Fonte principale: `docs/visione/` (versione 2026-10-16, gravya-app#1801; «ciò che non è scritto qui non è visione»). Lo stato «oggi» è riferito a `origin/staging @ c547bcaa6` di gravya-app al 16/10 [L], quindi **può essere superato** dalle onde successive [D].

Principi trasversali [L, `README.md` §3]: catena Kloud → supervisore → agenti specialisti → tool (P2); chi coordina non esegue, chi esegue non giudica (P3); permessi come dati, una chiave per azione, tabella per azienda (P6); autonomia graduata con partenza «approvazione richiesta» (P7); barriere senza umani: tetto di spesa fail-closed, contratto di esecuzione dei tool, audit (P8); niente scatola nera (P10); preambolo anti-invenzione fisso nel codice (P11); **prompt nel DB, seed nel repo, prompt in inglese** (P12); agenti non scrivono in memoria (P13); colonne HSAR scritte solo da umani, es. `hitl_level`, `system_prompt` (P16); Paperclip eliminato (P15).

**E1 Tracing distribuito** [L, `architettura-agenti.md` §3 A1]: Phoenix (Arize) adottato il 13/04 e **scartato il 15/06 per multi-tenancy debole** (#266). Al suo posto una timeline nel DB (console superadmin) con modello, token, costo, latenza, esito di ogni chiamata, **non prompt e risultati**. Audit: `tools/_audit.py` → `gravya_tool_invocations`, `gravya_event_logs`; le letture del router Kloud non passano dall'audit (manca). Raccolta di prompt/risultati dei clienti: va prima documentata legalmente (gravya-app#1925). AI Act art. 12/19: log ≥6 mesi solo se uso ad alto rischio (`controlli-e-conformita.md` §5). [D] Un tracing con contenuti di prompt diverge dalla decisione «non prompt e risultati»: va segnalato come divergenza da decidere.

**E2 Prompt registry** [L]: P12 (prompt nel DB, seed = versione 0 ripristinabile). A2: criteri di qualità nel DB accanto al prompt, **solo superadmin**, versionati **insieme al prompt**; l'agenzia non li modifica. Versioning prompt = punto 5 dell'epic #1801, **post-Beta**. Oggi esiste solo lo storico prompt dei supervisori modificati dal ciclo di miglioramento (migrazione 0322); cache prompt 60 s [L parziale, §2.8].

**E3 Eval harness offline** [L, §2.10 e `controlli-e-conformita.md` §6]: set di valutazione **assente**; «il set è il primo pezzo da costruire»; i limiti A6 «si ricalibrano con i run misurati dal set». Esiste lo script `scripts/kloud-eval-seed.ts` in gravya-app (citato nei rossi 4t in memory) [L il nome; contenuto NV]. Criteri = righe `agent_policy` (#892): tipo controllo deterministico/giudice/umano, gravità blocca/segnala; un controllo che non gira blocca o va all'umano.

**A1 Grafo mandati / A3 Runtime enforcement** [L, `controlli-e-conformita.md` §1-3]: classi Admin, Membro, Kloud, Supervisore (solo sui propri agenti), Agente (solo su sé); «Kloud può tutto» come autorità sui permessi ma con eccezioni D4/D7/D11; modello permessi in costruzione in gravya-app#998 (pezzi 1-4), **pezzo 4 da riscrivere sulla catena senza organigramma** (domanda aperta B3: identità di Kloud sul server). Enforcement esistente: `tools/_scope_enforcement.py:229-298` (contratto, `REQUIRES_HITL`, `MONEY_WRITE`, token monouso, tetto spesa) — «c'è, irraggiungibile finché gli agenti non eseguono i tool». Vocabolario chiuso `ALWAYS_HITL`/`MONEY_WRITE` (migrazione 0218): mai automatici (A5). Limiti A6: 8 giri tool/agente, $2 e 10 min per run, $10/giorno per agente e azienda; `MAX_CASCADE_DEPTH`=3 fisso nel codice. Isolamento RLS nel percorso agentico (`api/runtime.py`) c'è. Valori interni: superadmin a livello istanza, invisibili alle aziende.

**B1 Agent runtime isolato** [L, §2.3, §2.9]: difetto chiave — `generic_executor` usa `llm_invoke` che perde le chiamate ai tool (`executors/generic_executor.py:195-211`); esiste `llm_invoke_with_tools`. Nessun ciclo di tool, nessun limite di giri, nessun costo/tempo per run. Chiavi LLM: scelta esplicita azienda/piattaforma, senza ripiego (gravya-app#890). PII redaction spenta di default; motore Presidio+NER approvato il 15/10. Injection detector solo log. B1 (organico agenti) chiusa il 16/10: 7 supervisori; «un agente per tipo di uscita, non per canale». [NV] Nessun documento letto parla di isolamento a livello di processo/sandbox.

**B2 Tool gateway** [L, §2.4]: tool registrati in `gravya_tools`, legati agli esecutori via `gravya_executor_tools` + whitelist moduli `src.tools.`; audit per chiamata; 36 processi deterministici `c2_*` che «dove serve diventano tool». MCP Meta Ads rivalutato: per la Beta restano i tool interni, rivalutazione dell'MCP **dopo la Beta, dietro i nostri blocchi**; Manus: no.

**C1 Grafo workflow** [L, §3 B2]: **un solo modello**: un'automazione è un workflow del motore su Node (β), che non ha mai avuto interfaccia. Per la Beta girano le **automazioni Python** attuali; dopo la Beta β diventa motore unico (roadmap `workflow-beta-engine`) con tela γ (`workflow-gamma-canvas`, assorbe #1497). La catena è il blocco «chiama un supervisore». Override dei rifacimenti per passo nel workflow Gamma **eliminato**. Oggi il supervisore è un grafo LangGraph lineare senza rifacimenti (`generic_supervisor.py:616-627`) [L il grafo; «LangGraph» è [D] dal nome dei file `graph.py`].

**C3 Punto HITL** [L, §2.5 e `controlli-e-conformita.md` §2]: si approva **l'azione (il tool), non il testo**; oggi è il contrario (interrupt a fine catena che approva un testo e poi non esegue nulla, `graph.py:863-867, 948-953`) — difetto. Livello come dato per azienda/cliente/task (#998). 0 eventi di approvazione su staging. A3: rifacimenti 2 (supervisore→agente) e 1 (Kloud→supervisore); al fallimento finale risultato marcato non conforme e domanda all'umano, mai successo finto. A5: soglie per proporre l'automatico (20 run, 95%, nessun rifiuto negli ultimi 10), approva l'admin dell'agenzia, ritorno automatico all'HITL al primo rifiuto. Council solo con flag, prima (non al posto) dell'approvazione umana.

## 5. Rapporto gravya-app ↔ gravya-app-v2

- [L, grep su tutto il repo per `app-v2`, `gravya-app v2`, «riscrittura», «rewrite»]: **nessuna menzione di gravya-app-v2** né di una migrazione o riscrittura della piattaforma. Le occorrenze di «v2» sono solo sul layout del repo di stato (`docs/codebase-summary.md:63`, migrazione v1→v2→v3 sibling) e su piani interni non correlati.
- [L] Tutta la pianificazione registrata punta a chiudere la **Beta su gravya-app entro il 30/11/2026**.
- [D] Quindi cosa si porta in v2 e cosa no **non è documentato** nel repo di stato: va trattato come «Non verificato» / decisione aperta per l'utente. I documenti dell'ondata 1 non possono appoggiarsi a una strategia di migrazione registrata qui.
- [D] Possibile tensione da segnalare: la regola del 02/11 sposta a post-Beta tutto ciò che non tocca sicurezza/isolamento/dati/primo cliente; diversi temi dell'ondata 1 (prompt versioning, motore workflow β, eval) sono già classificati **post-Beta** in `docs/visione/`. Se v2 li anticipa, è una divergenza col piano registrato da far decidere a Daniele.

## 6. Avvertenze per gli agenti

- Lo stato «oggi» di `docs/visione/` è al 16/10; le onde 4o-4s (fuse fino al 02/11) possono aver cambiato il codice: verificare in `/workspace/gravya-app` prima di citare un difetto come attuale.
- Numeri di issue (#998, #1801, #892, #1925, #266, #890, #894) sono citati nei documenti; il loro stato attuale su GitHub è [NV].
