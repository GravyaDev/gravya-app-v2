# Task per code-reviewer: verifica del giro 3 (secondo BLOCCA sul controllo OSV)

Agente: code-reviewer
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura (worktree `.worktrees/ci-fornitura`).

## Contesto
Il tuo BLOCCA del giro 2 (`docs/revisioni/ci-fornitura/report-code-reviewer-giro2.md`, risposta `risposta-code-reviewer-giro2.json`): rifiuto degli stati HTTP diversi da 200 non protetto da test; test del timeout che non verifica il timeout; frase inesatta del report sul caso 204. Correzione dell'implementer: task `task-implementer-giro3.md`, risposta `risposta-implementer-giro3.json`, commit 796a096. Verifica del coordinator: la tua `prova-sopravvissuti.sh` ora dà la suite del branch in errore su s1 (6 falliti), s2 (1) e s3 (7); sul branch la tua prova dà 4 passati; CI e «Catena di fornitura» verdi su 796a096.

## Task
PR: branch impl/ci-fornitura, base main, head impl/ci-fornitura (solo il giro 3: `git diff 3f64f3d..impl/ci-fornitura`)
Documento di dettaglio dichiarato: E1 (v1.10), parte di CI; DECISIONS §6 «Catena di fornitura» punto 1.
Cartella report: docs/revisioni/ci-fornitura/ (nel repository principale; report `report-code-reviewer-giro3.md`)

Verifica solo che i tre rilievi del giro 2 siano risolti e che il giro 3 non abbia cambiamenti fuori perimetro. Dai l'esito sull'insieme del branch (`main...impl/ci-fornitura`) considerando chiusi i rilievi già verificati nei giri 1 e 2; gli altri rilievi non bloccanti del giro 1 restano come riportati, non riesaminarli. Le prove si eseguono dalla radice del worktree con `. .venv/bin/activate`. Non modificare nulla nel worktree e non fare commit; cartelle di lavoro solo dentro `docs/revisioni/ci-fornitura/`, cancellate a fine verifica.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
