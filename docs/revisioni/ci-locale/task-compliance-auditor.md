# Task per compliance-auditor: job della catena di fornitura in locale e CI ridotta

Agente: compliance-auditor
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-locale (worktree `.worktrees/ci-locale`).

## Contesto
Decisione dell'utente del 2026-11-05 (testo alla lettera in `docs/revisioni/ci-locale/task-implementer.md`): job della catena di fornitura in locale, CI di GitHub ridotta per i minuti (DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura»). Task dell'implementer: `docs/revisioni/ci-locale/task-implementer.md`; risposta `docs/revisioni/ci-locale/risposta-implementer.json` (con divergenze e decisioni mancanti dichiarate); report sul branch (`git show impl/ci-locale:docs/revisioni/ci-locale/report-implementer.md`).

## Task
Oggetto: PR main...impl/ci-locale (`git diff main...impl/ci-locale`; file leggibili anche in `.worktrees/ci-locale`)
Motivo: PR
Cartella report: docs/revisioni/ci-locale/ (nel repository principale)

Punti di attenzione: se spostare i controlli in locale lascia scoperto qualcosa rispetto ai rilievi già registrati in DECISIONS §4 «Catena di fornitura e aggiornamenti» e al report `docs/revisioni/ci-fornitura/report-compliance-auditor.md` (per esempio controlli che non girano se la macchina è spenta, credenziali usate dal servizio locale, tracciabilità degli esiti); permessi e credenziali di `gh` usati dal job locale; fail-closed; obblighi pertinenti del registro `docs/norme-di-riferimento.md`. Non modificare nulla nel worktree.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
