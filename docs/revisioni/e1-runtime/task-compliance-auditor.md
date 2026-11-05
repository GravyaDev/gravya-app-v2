# Task per compliance-auditor: aggiornamento a Python 3.15 e PostgreSQL 18

Agente: compliance-auditor
Preparato dal coordinator il 2026-11-05. Branch: impl/e1-runtime (worktree `.worktrees/e1-runtime`).

## Contesto
Decisione dell'utente in `docs/DECISIONS.md` §6, riga «Versioni di runtime»: Python 3.15 e PostgreSQL 18; aggiornamento di lockfile (con hash, ultime versioni, nessuna vulnerabilità nota), CI e README, poi `code-reviewer` e `compliance-auditor` in parallelo. Task dell'implementer: `docs/revisioni/e1-runtime/task-implementer.md`; risposta: `docs/revisioni/e1-runtime/risposta-implementer.json`; report sul branch (`git show impl/e1-runtime:docs/revisioni/e1-runtime/report-implementer.md`).

## Task
Oggetto: PR main...impl/e1-runtime (`git diff main...impl/e1-runtime`; file leggibili anche in `.worktrees/e1-runtime`)
Motivo: PR
Cartella report: docs/revisioni/e1-runtime/ (nel repository principale, non nel worktree)

Punti di attenzione: sicurezza della catena di fornitura (hash nel lockfile, immagini e action fissate per digest o SHA, origine dei pacchetti, vulnerabilità note), supporto di sicurezza delle versioni scelte (date in DECISIONS §6), effetti sulle garanzie già decise per E1 (RLS, ruoli del database, fail-closed di `API_ENV`, segnali) dovuti al cambio di versione di PostgreSQL o Python, obblighi del registro `docs/norme-di-riferimento.md` pertinenti (per esempio gestione delle vulnerabilità e componenti software). Non modificare nulla nel worktree.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
