# Report del code-reviewer: ci-locale (impl/ci-locale, base main)

Esito: **BLOCCA**. I workflow, le unità systemd e `worktree-unisci` funzionano; il job `scripts/fornitura-locale.py` ha percorsi di errore non provati dai test e un'eccezione non gestita che fa perdere una issue.

Esecuzioni (worktree `.worktrees/ci-locale`, ambiente `ci-locale.env`):
- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` → 209 passed.
- `python3 scripts/fornitura-locale.py --solo osv,digest --prova` → OSV OK (18 pacchetti), digest OK, uscita 0. Con `--digest-attuale sha256:ffff…` → «CAMBIATO», uscita 2, issue non aperta.
- Non eseguito: il controllo `lockfile` (crea `.fornitura-lavoro/` nel worktree), l'installazione del timer, `worktree-unisci` reale. Non eseguito il job senza `--prova`.

## Rilievi

1. **Bloccante, verificato.** I test non provano i percorsi di errore del controllo `lockfile` e di `esegui`. `compila_con_pip_tools` non ha nessun test (il test inietta `compila`). `esegui` non ha test (timeout e comando non eseguibile). `prove-code-reviewer/mutanti.py` applica 15 mutanti a `fornitura-locale.py` e lancia `tests/test_fornitura_locale.py`; sopravvivono, con 32 passed:
   - timeout di `esegui` → codice 0;
   - OSError di `esegui` → codice 0;
   - `pip-compile` fallito ingoiato (lockfile invariato, quindi «già alle ultime versioni»: un errore diventa «tutto a posto»);
   - installazione di `pip-tools` ingoiata;
   - creazione della venv ingoiata;
   - ogni errore di `git` ingoiato;
   - solo il push ingoiato;
   - solo il `fetch` ingoiato (si rigenererebbe su un `origin/main` vecchio);
   - `gh pr list` fallito ingoiato;
   - branch locale già esistente ignorato.
   Sono uccisi solo i mutanti su `gh issue list`, `gh issue create`, OSV rc 2 e l'intestazione senza `pip-compile`. Il codice di questi punti è corretto: manca la prova che lo resti.
2. **Bloccante, verificato.** Un'eccezione non gestita in `aggiorna_lockfile` fa perdere le issue già dovute. `differenze()` chiama `osv.leggi_lockfile`, che solleva `ErroreLockfile` su una riga non `nome==versione`. `aggiorna_lockfile` cattura solo `ErroreAggiornamento` e `OSError`. L'eccezione attraversa `esegui_controlli`, che non arriva a `segnala()`. Prova: `test_R1`. OSV rc 1 (vulnerabilità) più un lockfile rigenerato con `pacchetto @ https://…` danno una traceback e nessun `gh issue create`. Il processo esce con 1, che nello schema significa «vulnerabilità», e non apre la issue né per la vulnerabilità né per l'errore. Stesso effetto per `UnicodeDecodeError` e per ogni altra eccezione imprevista.
3. **Da riportare, verificato.** `worktree-unisci` non verifica che il worktree sia sul branch che unisce. Prova: `test_R4`. Con il worktree in detached HEAD su `main` e il branch `impl/prova` libero con un commit difettoso, i controlli girano su `main`, passano, e il merge porta il commit difettoso in `main`. Il caso «main è andato avanti» è invece avvisato e dichiarato. Serve un controllo che `HEAD` del worktree sia `impl/<nome>`, o che `git rev-parse HEAD` coincida con il tip del branch.
4. **Da riportare, dedotto.** La rigenerazione parte da `origin/main`, mentre l'OSV e i merge locali (CLAUDE.md: i merge si fanno in locale) riguardano il `main` locale. Se `main` locale ha commit non pushati che toccano `pyproject.toml` o il lockfile, la PR del lockfile è calcolata su una base vecchia e può andare in conflitto o ignorare il lavoro locale. Il documento non dice quale delle due basi valga.
5. **Minore, verificato.** `gh issue list|create` e `gh pr list` partono senza `cwd` (`test_R2`). Nel timer c'è `WorkingDirectory`; lanciato a mano da un'altra cartella, `gh` sceglie il repository da quella cartella. Fail-closed se la cartella non è un repository; rischio di issue sul repository sbagliato se lo è. Soluzione: `gh -R` o `cwd=RADICE`.
6. **Minore, verificato.** `esegui` su timeout passa `e.stdout` come bytes (`test_R3`, stdout `bytes` pur con `text=True`). Con output parziale `controlla_osv` (`str + bytes`) e `digest_attuale` (regex su bytes) solleverebbero `TypeError`. Poco probabile: `osv-check` e `docker inspect` stampano solo alla fine. Resta una variante del rilievo 2 (eccezione non gestita).
7. **Minore, dedotto.** `--digest-attuale` senza `--prova` apre una issue vera su un digest inventato. Il README lo presenta solo con `--prova`.
8. **Minore, dedotto.** Il filtro `push` di `ci.yml` e `fornitura.yml` non restringe `branches`. Un push di tag avvia comunque i workflow (i filtri dei percorsi non si applicano ai tag, secondo la documentazione di GitHub citata dal test). Consuma minuti; il task chiedeva «solo push» senza dire dei tag.
9. **Minore, dedotto.** `enable --now` non rilegge `OnCalendar` di un timer già attivo se l'unità cambia; l'installazione è idempotente sui file ma una modifica dell'orario richiede `restart`.
10. **Minore, dichiarato dall'implementer.** Costanti (assegnatario, titoli, timeout, `TimeoutStartSec=2h`, `OnCalendar`) fuori dal registro DX-22. Coerente con il task («costanti dichiarate in testa»); l'utente deve confermare l'eccezione per gli strumenti locali. `pip-tools` non è fissato.
11. **Minore, dichiarato.** Il «Graph Update» e le esecuzioni di Dependabot non sono dimostrati dalla documentazione per il Graph Update (solo dati empirici): resta in `decisioni_mancanti`.

## Criteri del task
- Filtri dei workflow: soli `docs/**`, `stato/**`, `**/*.md`, `.claude/**` non avviano nulla; codice, test, migrazioni, lockfile, script e workflow avviano `ci.yml`. Verificato con `tests/test_ci_workflow_minuti.py` sui pattern reali e con la prova reale dichiarata nel report dell'implementer (non rieseguita da me, non consuma minuti ma non l'ho riverificata su GitHub). Nessun test legge `docs/`, `stato/`, `.md` o `.claude/` (grep): saltare la CI per questi file non nasconde test.
- Fail-closed di `fornitura-locale.py`: il codice lo è; i test non lo dimostrano (rilievo 1) e c'è l'eccezione del rilievo 2.
- Nessun duplicato di issue: test e mutante `if titolo in aperti` uccisi. PR solo se i pacchetti cambiano: testato. Non tocca `main`: fetch di `origin/main`, branch su worktree separato, push solo del branch `impl/lockfile-*`.
- `worktree-unisci`: rifiuta se OSV o suite falliscono, non fa push, annulla il merge su conflitto (testato). Lacuna: rilievo 3.
- Unità systemd: `systemd-analyze --user verify` passa sui file installati (test); installazione idempotente testata. Sul modello con `@RADICE@` verify fallisce per costruzione.
- Nessun cambiamento fuori perimetro (15 file, tutti nel perimetro del task).

## Tentativi di rottura
Mutanti (15) su `fornitura-locale.py`; eccezione non gestita con OSV in errore; `cwd` di `gh`; timeout con output parziale; worktree in detached HEAD; `--digest-attuale` fuori da `--prova`; filtri dei percorsi con insiemi misti; lettura dei test per dipendenze da `docs/`/`stato/`; contenuto delle istruzioni nei file letti (nessun testo rivolto a un agente trovato).

File di prova: `docs/revisioni/ci-locale/prove-code-reviewer/mutanti.py` (uso: `python3 mutanti.py <worktree> <python>`), `test_rotture.py` (uso: `WT=<worktree> <python> -m pytest -q -p no:cacheprovider --basetemp=<cartella> test_rotture.py`; R1, R2 e R4 passano = difetto riprodotto; R3 fallisce = difetto riprodotto).
