# Passaggio di consegne (keywords: handoff, ripresa, stato, prossimi passi, implementazione, E1)

Riscritto il 2026-11-05 (sessione 9, prima in Claude Code locale). Si riscrive, non si accoda. Vale per la piattaforma e per Claude Code locale (`CLAUDE.md`). La memoria di sessione è tutta in questa cartella `stato/` (da `docs/stato/`, che descrive i repository di riferimento, è distinta).

## Leggere prima
1. Questo file, poi `preferenze-e-lezioni.md`, `ambiente.md` (sezione «Claude Code locale»), `azioni-utente.md`.
2. **Branch:** `main` per documenti e codice; ogni implementer in un worktree `.worktrees/<nome>` sul branch `impl/<nome>`, cancellato dopo il merge (DECISIONS §6 «Branch di lavoro», comandi in `CLAUDE.md`). **Worktree aperti: `ci-locale`** (branch `impl/ci-locale`, pushato, non unito; PostgreSQL del worktree sulla porta 5433, variabili in `.worktrees/ci-locale.env`).
3. `docs/DECISIONS.md` (solo decisioni correnti: §4 punti aperti, §6 regole incluse quelle di E1), `docs/agenti/README.md`, `docs/catalogo-variabili.md`.

## Stato (2026-11-05, fine sessione 9 in Claude Code locale, chiusa su richiesta dell'utente)
- Ondata 1: E1 alla v1.10, gli altri 8 documenti alla v1.6. Approvati come base dell'implementazione: E1 e A1. Da approvare: A3, B1, B2, C1, C3, E2, E3.
- **E1 (passi 0, 2, 3) chiuso** (micro-correzione `API_ENV`). Residui in DECISIONS §4 «E1, residui del giro 6».
- **Runtime** Python 3.15 e PostgreSQL 18 (merge 3bf8969). **Catena di fornitura della CI** (merge 46659bd). Ultimo merge di lavoro in `main`: 46659bd; `tests/` 123 verdi su `main`.
- **In corso: job della catena di fornitura in locale e CI di GitHub ridotta** (decisione dell'utente, DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura»; §4 «Catena di fornitura e aggiornamenti»). Worktree `ci-locale`: giro 1 implementer, code-reviewer BLOCCA, compliance-auditor RIPORTA; giro 2 implementer (302 test, CI verde su 19683a9), code-reviewer **BLOCCA** al giro 2 (test della traccia delle esecuzioni che non uccidono alcuni mutanti; `report-code-reviewer-giro2.md`). Task del giro 3 pronto: `docs/revisioni/ci-locale/task-implementer-giro3.md`. Su `main` la CI di GitHub parte ancora per ogni push, anche di soli documenti, finché `ci-locale` non è unito: **pochi push**.

## Prossimi passi, in ordine
1. `python3 scripts/agenti.py lancia docs/revisioni/ci-locale/task-implementer-giro3.md`; poi code-reviewer di verifica (giro 3, sul modello di `task-code-reviewer-giro2.md`). Con OK: `python3 scripts/agenti.py worktree-unisci ci-locale` (comando nuovo del branch: dopo il merge è in `main`; per questo primo merge usarlo dal worktree o fare il merge a mano con gli stessi controlli: OSV, `tests/`, `test-non-superuser.sh`), push, `worktree-chiudi ci-locale`.
2. Dopo il merge: installare il timer (`bash scripts/installa-timer-fornitura.sh`, istruzioni nel README), eseguire una volta il job vero, aggiungere a `CLAUDE.md` (Avvio) `python3 scripts/fornitura-locale.py --stato`; registrar: attuazione dei punti di §6 «Catena di fornitura», rilievi residui RIPORTA del compliance-auditor (`docs/revisioni/ci-locale/report-compliance-auditor.md`) in §4, e le decisioni dell'utente sotto.
3. **Nuova fase, sessione nuova:** A1 passi 3-4 sull'ossatura.
4. Alla prossima revisione di A1: App. C r.251 cita «DECISIONS §4» per «Mutazioni del grafo», ora in §6.
5. Poi: allineamento degli altri documenti dell'ondata 1; approvazione dei sette documenti; ondata 2 (A5, A6, F6). Con il plan-auditor: `security.vulnerability_scan_interval_days` del catalogo e la cadenza settimanale del job.

## In attesa di risposta dall'utente (da presentare in un blocco)
1. Credenziale del job locale: oggi il PAT classico di `kloud-ai` (scope `repo`, `workflow`, `read:org`, 17 repository in scrittura, senza scadenza), lo stesso di tutte le sessioni della macchina. Raccomandazione del coordinator (spiegata all'utente il 2026-11-05): token fine-grained solo per `gravya-app-v2` (contents, pull requests, issues; niente workflow), con scadenza, letto dal servizio systemd da un file leggibile solo dall'utente e tolto dall'ambiente del passo pip-tools; il login di `gh` resta invariato. Alternativa: rischio accettato e registrato. Scelta dell'utente non ancora data.
