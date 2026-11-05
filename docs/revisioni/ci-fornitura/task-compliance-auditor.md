# Task per compliance-auditor: catena di fornitura della CI

Agente: compliance-auditor
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura (worktree `.worktrees/ci-fornitura`).

## Contesto
Decisione dell'utente in `docs/DECISIONS.md` §6, riga «Catena di fornitura» (punti 1 e 2), con il punto aperto in §4 «Catena di fornitura e aggiornamenti». Task dell'implementer: `docs/revisioni/ci-fornitura/task-implementer.md`; la sua risposta: `docs/revisioni/ci-fornitura/risposta-implementer.json` (con due divergenze dichiarate: Dependabot per pip non configurato perché la documentazione non garantisce la rigenerazione del lockfile con hash, e un file di test nuovo `tests/test_ci_osv_check.py`); il suo report è sul branch (`git show impl/ci-fornitura:docs/revisioni/ci-fornitura/report-implementer.md`).

## Task
Oggetto: PR main...impl/ci-fornitura (`git diff main...impl/ci-fornitura`; file leggibili anche in `.worktrees/ci-fornitura`)
Motivo: PR
Cartella report: docs/revisioni/ci-fornitura/ (nel repository principale, non nel worktree)

Punti di attenzione: se i controlli rispondono ai rilievi a e b del report `docs/revisioni/e1-runtime/report-compliance-auditor.md` (scansione delle vulnerabilità e aggiornamenti; runner, `psql`, action); permessi minimi dei workflow (`permissions`); fail-closed dei controlli; cosa resta scoperto senza Dependabot per i pacchetti Python; obblighi pertinenti del registro `docs/norme-di-riferimento.md`. Non modificare nulla nel worktree.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
