# Report del code-reviewer, giro 2: ci-locale (impl/ci-locale, head 19683a9, base main)

Esito: **BLOCCA**, per un solo motivo, circoscritto. I due bloccanti del giro 1 sono risolti e i rilievi 3-9 sono corretti. Nel codice nuovo della traccia e di `--stato` mancano però test che fallirebbero con mutanti: due dei tre bit di errore e il collegamento di `--prova` al file di traccia non sono provati. Questa traccia è la base del controllo «fornitura recente» di `worktree-unisci`. Il codice è corretto: manca la prova che lo resti.

## Esecuzioni (worktree `.worktrees/ci-locale`, `ci-locale.env`)
- `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` → 301 passed, 1 failed (`test_ci_osv_check.py::test_invia_http_stato_2xx_diverso_da_200…[201]`, timeout del server HTTP locale mentre giravano altri processi). Rieseguito da solo tre volte: 37 passed ogni volta. È instabile sotto carico, non un difetto della PR. Il file è del giro 1.
- `prove-code-reviewer/mutanti.py` (15 mutanti del giro 1): base 103 passed, **15 uccisi su 15** (prima ne sopravvivevano 11).
- `prove-code-reviewer/test_rotture.py`: R1 (eccezione non gestita) e R4 (HEAD del worktree) ora **falliscono**, cioè il difetto non si riproduce (R4 viene rifiutato con «l'HEAD del worktree non coincide…»). R3 (bytes del timeout) ora passa. R2 passa perché il suo assert guarda `cwd`; il rimedio è `-R`, verificato dai mutanti.
- `prove-code-reviewer-giro2/mutanti2.py`: 82 mutanti sul codice nuovo (`fornitura-locale.py`, `agenti.py`), con `test_fornitura_locale.py`, `test_fornitura_strumenti.py` e `test_agenti_unisci.py`. Base 132 passed; 81 valutati (un pattern non univoco, saltato), 67 uccisi, 14 sopravvissuti (13 con l'ambiente pulito: uno dipende da `ci-locale.env` nella shell). Quelli rilevanti sono nei rilievi 1 e 2; gli altri sono equivalenti o di scarso rilievo.
- `prove-code-reviewer-giro2/test_rotture2.py`: 5 prove, tutte passano (difetti minori riprodotti, rilievi 4-6 sotto).
- CI su GitHub: `gh run list -b impl/ci-locale` → «CI» e «Catena di fornitura» success su 19683a9 (confermato).
- Non eseguito: il job senza `--prova`, il timer, `worktree-unisci` reale, un push di tag reale.

## Verifica dei due bloccanti e dei rilievi del giro 1
- **B1 (errori ingoiati): risolto.** Mutanti 15/15 uccisi. `compila_con_pip_tools` ha test propri (non iniettati). `esegui` ha test per timeout e `OSError`.
- **B2 (eccezione che fa perdere le issue): risolto.** `_isola` converte ogni `Exception` in un esito «errore» con la sua issue. `segnala` è in un `try` a parte (codice 32). Uccisi i mutanti `_isola`, `segnala` in `esegui_controlli` e la perdita del codice di `segnala`.
- **3 (HEAD diverso dal branch): corretto.** Controlli di HEAD uguale alla punta e di `main` antenato; mutanti uccisi.
- **4 (base): corretto.** `fetch`, base `origin/main`, commit locali non pubblicati su `pyproject.toml`/lockfile → errore con issue. Mutanti uccisi (base = main locale, commit ignorati, file tolti da `FILE_BASE_LOCKFILE`).
- **5 (`-R`): corretto.** Mutanti «senza -R» uccisi per `issue list|create|comment` e `pr list|create`.
- **6 (bytes del timeout): corretto.** `_testo`; mutanti uccisi.
- **7 (`--digest-attuale`): corretto.** Accettato solo con `--prova`; mutante ucciso.
- **8 (tag): corretto.** `branches: ["**"]` nei due workflow; test dei filtri. Il comportamento reale di GitHub con un push di tag non è provato (dichiarato).
- **9 (timer): corretto.** `daemon-reload` e `restart` se era attivo; test presenti.
- **Nuovo codice**: commenti alle issue (uccisi: commento anche se invariato, mai commento, `ultimo` = corpo, commento fallito ignorato), rimozione delle credenziali (uccisi i tre pattern, il corpo delle issue e `_coda`), `requirements-strumenti.lock.txt` (uccisi `--require-hashes`, file sbagliato, OSV su un solo lockfile), controlli di `worktree-unisci` (uccisi: HEAD, main antenato, fornitura non fresca, forzatura sempre attiva, forzatura non scritta nel messaggio, non-superuser tolto, OSV strumenti tolto, esito dei controlli ignorato, merge non annullato, `--ff`).
- **Fuori perimetro: nessuno.** I 18 file di `main...impl/ci-locale` stanno tutti nel perimetro del task. Nessun testo rivolto a un agente nei file letti.

## Rilievi

1. **Bloccante, verificato.** I test della traccia non provano il comportamento fail-closed di `e_riuscita`/`BIT_ERRORE` per due dei tre bit. Come errore di un controllo è provato solo `ERRORE_CONTROLLO` (4, `test_stato_senza_traccia_o_senza_riuscite_e_errore`). Sopravvivono (132 passed, anche con l'ambiente pulito):
   - `BIT_ERRORE` senza `ERRORE_AGGIORNAMENTO`: un lockfile non rigenerato (pip-compile, git, gh) sarebbe registrato come esecuzione riuscita;
   - `BIT_ERRORE` senza `ERRORE_ISSUE`, e `e_riuscita` che ignora il codice globale: un'esecuzione in cui la segnalazione non è partita (vulnerabilità trovate ma nessuna issue) sarebbe «riuscita»;
   - `main` che registra `prova=False` per `--prova` (nessun test di `main --prova` sulla traccia): un `--prova`, che non apre nulla, soddisferebbe il controllo «fornitura recente» di `worktree-unisci`.
   L'effetto sarebbe che `--stato` e `worktree-unisci` danno via libera con un job che non sta segnalando nulla. Il codice attuale è corretto; mancano i test (un caso per bit, e `main(["--prova"])` seguito da `stato`). Fonte: task giro 2 punti 5 e 3 («fail-closed e coperto da test che fallirebbero con mutanti»); DECISIONS §6 «Catena di fornitura». Prova: `prove-code-reviewer-giro2/mutanti2.py` (nomi `BIT_ERRORE senza ERRORE_ISSUE`, `BIT_ERRORE senza ERRORE_AGGIORNAMENTO`, `e_riuscita: errore globale (issue) ignorato`, `main: registra con prova sempre False`; uso: `python3 mutanti2.py <worktree> <python> "BIT_ERRORE" "registra con prova"`).
2. **Da riportare, verificato.** Altri mutanti sopravvissuti, con effetto minore:
   - `ultima_riuscita` con `min` al posto di `max` (falso allarme «scaduta» con più riuscite);
   - `segnala` che confronta con il primo commento invece dell'ultimo (commenti duplicati);
   - il test `test_nessuna_credenziale_in_issue_commenti_e_pr` dice di coprire la PR, ma il corpo della PR non è ripulito dal test: togliere `ripulisci` dalla PR non lo fa fallire (il corpo ha solo nomi di pacchetti, quindi il rischio è basso);
   - la rimozione del worktree residuo (`sorgente.exists()`) non è provata;
   - `test_variabili_del_file_env_arrivano_ai_controlli`: con le variabili di `ci-locale.env` già nella shell, il test passa anche se `worktree-unisci` non passa l'`.env` ai controlli. Con l'ambiente pulito il mutante è ucciso. Il task stesso chiede di eseguire con `ci-locale.env` caricato, quindi il test non è ermetico.
   - Equivalenti o di scarso rilievo, non rilievi: `repo_github` con l'errore di `git remote get-url` ignorato (la regex rifiuta comunque l'output vuoto); `e_riuscita` senza il controllo per controllo (ridondante con il codice globale, se non per `ERRORE_ISSUE`, già nel rilievo 1); errore di git su `rev-parse` dell'HEAD ignorato (servirebbe che falliscano entrambi i comandi); «già unito» e «principale con modifiche» di `worktree-unisci` (controlli del giro 1, senza test discriminanti).
3. **Minore, verificato (`test_rotture2.py::P1, P2`).** `leggi_esecuzioni` accetta una riga con `data` senza fuso orario o riuscita senza la chiave `esito`: `stato` solleva `TypeError`/`KeyError` (traceback con codice 1). La traccia la scrive solo lo script con data UTC, quindi vale solo per una modifica a mano. Fail-closed comunque (il comando esce con errore), ma con un codice diverso da 64.
4. **Minore, verificato (`P3`).** Una data nel futuro (orologio sbagliato o riga modificata) rende la traccia «fresca» fino a quella data. Nessun controllo di data futura.
5. **Minore, verificato (`P5`).** `ripulisci` copre i pattern chiesti (`ghp_/gho_/ghs_…`, `github_pat_`, URL https con credenziali), non `ssh://utente:segreto@…` né un'intestazione `Authorization: Bearer`. Coerente con il task; l'elenco è esplicito.
6. **Minore, dedotto.** `test_ci_osv_check.py::…[201]` può andare in timeout sotto carico (un'esecuzione su quattro dell'intera suite): rende rossa la suite di `worktree-unisci` senza difetti reali.
7. **Punti che richiedono l'utente (non bloccanti, come da task).** Eccezione a DX-22 per le costanti degli strumenti locali, credenziale `gh` del servizio (PAT classico non presidiato), minuti del Graph Update. L'isolamento della rigenerazione è dichiarato come limite nel README.

## Criteri del task
- Bloccanti 1 e 2: risolti e coperti (mutanti 15/15; `_isola`).
- Traccia/`--stato`: codice corretto; test insufficienti per i bit `ERRORE_AGGIORNAMENTO` e `ERRORE_ISSUE` e per `main --prova` (rilievo 1).
- Commenti alle issue, credenziali, `requirements-strumenti.lock.txt`, controlli di `worktree-unisci`: coperti, con le eccezioni del rilievo 2.
- Fuori perimetro: nessuno.

## Tentativi di rottura
Mutanti del giro 1 (15) e del giro 2 (82); riesecuzione di R1-R4; traccia con data senza fuso, riga senza `esito`, data futura, confine esatto della soglia (9 giorni: fresca, +1 s: scaduta, corretto); `ripulisci` con token corti, `ssh://`, Bearer; rieseguiti i sopravvissuti con ambiente pulito (`env -i`); controllo dei workflow, del timer e del perimetro del diff; lettura dei file per testi rivolti a un agente (nessuno).

Cancellati a fine verifica: `.pytest_basetemp` del worktree, `lavoro/`, `lavoro-mutanti/`, `__pycache__`. Nessuna modifica al worktree (`git status` pulito). Non ho scritto nella cartella `stato/`.

File di prova: `docs/revisioni/ci-locale/prove-code-reviewer-giro2/mutanti2.py` e `test_rotture2.py` (uso nelle intestazioni dei file; `WT=<worktree> <python> -m pytest -q -p no:cacheprovider --basetemp=<cartella> test_rotture2.py`).
