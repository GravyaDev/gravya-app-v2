# Report dell'implementer: job della catena di fornitura in locale e CI ridotta

Documento: `docs/E1-tracing-distribuito.md` v1.10 (parte di CI); DECISIONS §4 «Catena di fornitura e aggiornamenti» (decisione del 2026-11-05) e §6 «Catena di fornitura». Branch `impl/ci-locale`. Nessun cambiamento a codice applicativo, migrazioni, lockfile.

## Cosa è stato fatto (un commit per punto)

| Punto | Commit | Contenuto |
|---|---|---|
| 1 | CI: solo push e avvio manuale… | `ci.yml` e `fornitura.yml`: solo `push` e `workflow_dispatch`; `ci.yml` con `paths-ignore` (`docs/**`, `stato/**`, `**/*.md`, `.claude/**`); `fornitura.yml` con `paths` (lockfile, `scripts/osv-check.py`, il workflow); `concurrency` con `cancel-in-progress` per branch; tolti `schedule`, `pull_request` e il job del digest. Test: `tests/test_ci_workflow_minuti.py`. |
| 5 | Test delle costanti di osv-check… | Valori letterali documentati (URL, `PyPI`, blocco da 1000, HTTP 200, timeout) e controllo del corpo della richiesta. `tests/test_ci_osv_check.py`. |
| 2 | Job settimanale locale… | `scripts/fornitura-locale.py`, `.gitignore` (`.fornitura-lavoro/`), `tests/test_fornitura_locale.py`. |
| 3 | Timer systemd utente… | `systemd/gravya-fornitura.{service,timer}`, `scripts/installa-timer-fornitura.sh`, `tests/test_timer_fornitura.py`. **Non installato.** |
| 4 | agenti.py worktree-unisci… | Comando `worktree-unisci <nome> -m <messaggio>`; `tests/test_agenti_unisci.py`. |
| — | README… | Sezione «Catena di fornitura (CI e controlli in locale)»: installazione, controllo, esecuzione a mano. |

## Minuti di Actions: Dependabot e «Graph Update»

Domanda: in un repository privato le esecuzioni di Dependabot e del dependency graph consumano minuti?
- **Dependabot (aggiornamenti delle action)**: no. La pagina «About billing for GitHub Actions» (docs.github.com, `billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions`, consultata il 2026-11-05) elenca tra i casi in cui «the use of standard GitHub-hosted runners is free»: repository pubblici, GitHub Pages e **Dependabot**.
- **«Graph Update: pip»**: non ho trovato una frase esplicita nella documentazione sul dependency graph. Verifica empirica sul repository (`gh api repos/GravyaDev/gravya-app-v2/actions/runs/<id>/timing`): le 4 esecuzioni con evento `dynamic` (3 «Graph Update: pip in /.», 1 «github_actions in /. - Update») hanno `billable` vuoto (`{}`), mentre un'esecuzione di «CI» ha `UBUNTU … job_runs` con durata contata. Conclusione: non risultano fatturate; **non dimostrato dalla documentazione**, solo dai dati.
- Impostazioni del repository non toccate. Su 64 esecuzioni del 2026-11-05: 53 «CI», 8 «Catena di fornitura», 1 CI da `pull_request`, 4 `dynamic`.

## Dimostrazione: un commit di soli documenti non avvia workflow

Senza consumare minuti: (a) la documentazione di GitHub («Workflow syntax for GitHub Actions», `on.<push>.paths-ignore`) dice che il workflow non parte quando **tutti** i file modificati corrispondono a un pattern di `paths-ignore`, e che con `paths` non parte se nessun file corrisponde; `*` non attraversa `/`, `**` sì; (b) `tests/test_ci_workflow_minuti.py` riproduce questa regola (`corrisponde`, `avvia`) e la applica ai pattern **letti dai file reali**: 7 insiemi di soli documenti (`docs/…`, `stato/…`, `README.md`, `src/LEGGIMI.md`, `.claude/…`, misti) non avviano né `ci.yml` né `fornitura.yml`; insiemi con codice, test, lockfile, workflow o un solo file non ignorato avviano `ci.yml`; `fornitura.yml` parte solo per lockfile/script OSV/workflow stesso. Limite: il matcher è una riproduzione, non il motore di GitHub; la prova definitiva è il primo push di soli documenti dopo il merge (nessuna esecuzione attesa).

## Risultati dei comandi (nel worktree, ambiente di `.worktrees/ci-locale.env`)

- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` → **209 passed** (suite intera, anche le 33+2+32+6+13 prove nuove).
- Mutazioni provate a mano e poi ripristinate: `ora != fissato` → `==` (4 test falliscono); `if titolo in aperti` → `if False` (1 test fallisce); `returncode != 0` → `== 0` nel comando di unione (5 test falliscono).
- `scripts/fornitura-locale.py --prova` (reale: OSV su api.osv.dev, docker, pip-compile `--upgrade` su `origin/main`): `osv: OK 18 pacchetti`, `digest: OK postgres:18 è ancora sha256:bd5dfa49…`, `lockfile: già alle ultime versioni`, **uscita 0**; nessuna issue, branch, push o PR. Con `--solo digest --prova --digest-attuale sha256:ffff…`: «CAMBIATO», uscita **2**, issue non aperta (prova).
- `systemd-analyze --user verify` sui file generati dall'installatore: **codice 0, nessun messaggio**.
- CI su GitHub dopo il push: vedi «Esito CI» in fondo.

## Scelte e limiti (da leggere)

- **Codici di uscita**: bit sommabili (1 vulnerabilità, 2 digest, 4 controllo non riuscito, 8 aggiornamento non riuscito, 16 PR aperta, 32 issue non aperta). Il 16 è un esito normale: nell'unità `SuccessExitStatus=16`.
- **Rigenerazione**: usa `origin/main` (dopo `git fetch`) in un worktree temporaneo di `.fornitura-lavoro/`, non il checkout principale; il comando è letto dall'intestazione del lockfile (non copiato nel codice) con `--upgrade`. L'intestazione sola non conta come cambiamento: si confrontano i pacchetti. Se è già aperta una PR con branch `impl/lockfile-*` non ne apre un'altra.
- **`pip-tools` non è fissato** (versione più recente in una venv di lavoro nella cartella ignorata): non è nel lockfile e il lockfile non può cambiare in questo task. Il risultato passa da OSV e CI.
- **Costanti** (assegnatario, titoli, prefisso del branch, timeout, identità dei commit del branch del lockfile `noreply@gravya.invalid`) dichiarate in testa agli script con il motivo, non nel registro DX-13: sono costanti di uno strumento locale, non variabili applicative; segnalato in `divergenze`.
- **Issue**: non si chiudono da sole quando il problema rientra; nessun segnale ad A5 (non richiesto).
- **`worktree-unisci`** prova il branch, non il risultato del merge: se `main` ha commit che il branch non contiene, avvisa ma procede (il task non prevede il blocco). Rifiuta anche se il worktree o il principale hanno modifiche non committate, se il principale non è su `main`, se il branch è già unito; in caso di conflitto annulla il merge.
- Il push del branch `impl/lockfile-*` farà partire, una volta alla settimana e solo se il lockfile cambia, `ci.yml` e `fornitura.yml` su GitHub: è voluto (CI e OSV sul lockfile nuovo prima del merge).
- Il test `systemd-analyze verify` si salta su GitHub (`GITHUB_ACTIONS`): lì non c'è una sessione utente systemd; in locale gira.

## Esito CI
Push di `impl/ci-locale` (commit 2a314d5): «CI» **success** (job `test` e `test-non-superuser`) e «Catena di fornitura» **success** (partita perché il push cambia `fornitura.yml`). Un solo push con codice. Subito dopo, il commit con questo solo aggiornamento del report (solo `docs/`) è stato pushato: esito: **nessuna esecuzione avviata** (dopo 25 s le esecuzioni del branch restavano 2, entrambe sul commit 2a314d5): prova reale, non solo dei pattern.
