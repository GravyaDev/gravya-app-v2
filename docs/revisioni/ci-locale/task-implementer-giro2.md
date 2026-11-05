# Task per implementer: correzione del BLOCCA sul job locale e rilievi tecnici (giro 2)

Agente: implementer
Worktree: ci-locale
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-locale.

## Contesto
Seguito di `docs/revisioni/ci-locale/task-implementer.md` (tuoi commit 505ff88…65c4b12). Revisioni in `docs/revisioni/ci-locale/`: `code-reviewer` **BLOCCA** (`report-code-reviewer.md`, `risposta-code-reviewer.json`, prove in `prove-code-reviewer/`), `compliance-auditor` **RIPORTA** (`report-compliance-auditor.md`, `risposta-compliance-auditor.json`). Leggi per intero i due report: i numeri sotto rimandano ai loro rilievi.

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10), parte di CI; DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura».
Perimetro: `scripts/fornitura-locale.py`, `scripts/agenti.py` (solo `worktree-unisci` e ciò che gli serve), `scripts/installa-timer-fornitura.sh`, `systemd/`, i due workflow (solo il punto 9), i test relativi, README, report. Nessun cambiamento al codice applicativo, alle migrazioni, a `requirements.lock.txt`.
Repository: .worktrees/ci-locale; branch di lavoro: impl/ci-locale
Push: sì (solo `impl/ci-locale`, **un solo push alla fine**)
Vincoli specifici:
1. **Bloccante 1 (code-reviewer).** Percorsi di errore fail-closed e coperti da test reali: timeout e `OSError` di `esegui`, `pip-compile` fallito, pip-tools non installabile, venv non creabile, errori di git e di `gh`: ognuno deve dare un codice di errore e una issue, mai «già alle ultime versioni» o codice 0. `compila_con_pip_tools` deve avere test propri (non iniettati). Dimostra con i mutanti delle prove del code-reviewer (`prove-code-reviewer/`, dalla radice del worktree con `../../docs/...`) che ora la suite fallisce su ciascuno; non modificare le prove.
2. **Bloccante 2 (code-reviewer).** Un'eccezione inattesa in un controllo non deve far perdere le issue degli altri: ogni controllo è isolato, un'eccezione non prevista diventa a sua volta un esito «errore» con la sua issue, e `segnala()` viene sempre eseguita per tutti gli esiti. Test che lo provano (OSV con vulnerabilità e lockfile rigenerato non conforme: issue di entrambi).
3. **`worktree-unisci`** (code-reviewer da riportare 3; compliance-auditor 5): rifiuta se l'HEAD del worktree non coincide con il tip di `impl/<nome>`; rifiuta se `main` non è antenato di `impl/<nome>` (main andato avanti: prima si aggiorna il branch); esegue anche `scripts/test-non-superuser.sh` con le variabili del worktree, oltre a OSV e `tests/`; rifiuta (salvo un'opzione esplicita di forzatura che lo scrive nel messaggio di merge) se l'ultima esecuzione riuscita del job settimanale è più vecchia della soglia del punto 5.
4. **Base della rigenerazione** (code-reviewer 4): `git fetch` e base `origin/main`; se `main` locale ha commit non pushati che toccano `pyproject.toml` o `requirements.lock.txt`, nessuna PR: esito «errore» con issue che lo spiega.
5. **Traccia delle esecuzioni** (compliance-auditor 1, 6, 7): a ogni esecuzione, anche fallita, una riga JSON (data, esito per controllo, versioni) in coda a un file locale fuori dal repository (per esempio `~/.local/state/gravya-fornitura/esiti.jsonl`, percorso come costante in testa), e un comando `--stato` che stampa l'ultima esecuzione riuscita ed esce con errore se è più vecchia di una soglia (costante dichiarata, con motivo: margine sul timer settimanale). Nel README: il coordinator lo esegue a ogni avvio di sessione (lo aggiungo io a `CLAUDE.md` dopo il merge).
6. **Issue** (compliance-auditor 4, 9): se una issue dello stesso tipo è già aperta e il contenuto è cambiato, aggiungi un commento con il nuovo contenuto (niente commento se invariato); prima di scrivere in una issue o in una PR, togli dal testo i pattern di credenziali (token `ghp_`/`github_pat_`/`gho_`, URL con credenziali `https://…@`), con test.
7. **pip-tools fissato** (compliance-auditor 3): versione di pip-tools e delle sue dipendenze con hash in un file di requisiti separato e versionato (per esempio `requirements-strumenti.lock.txt`), installato con `--require-hashes`, con il comando di rigenerazione nell'intestazione; il job settimanale controlla con OSV anche quel file. Non serve isolare la rigenerazione in un contenitore: dichiaralo come limite nel README.
8. **Minori del code-reviewer**: `gh` sempre con `-R <owner>/<repo>` ricavato dal remoto `origin` (5); output di timeout trattato come testo (6); `--digest-attuale` accettato solo con `--prova` (7); installazione del timer che dopo la copia esegue `daemon-reload` e `restart` del timer se era già attivo (9).
9. **Tag** (code-reviewer 8): i due workflow non partono per i push di tag (`branches: ["**"]` o `tags-ignore`), con il test dei filtri aggiornato.
10. Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde nel worktree con `set -a; . ../ci-locale.env; set +a`; prove del code-reviewer con i mutanti uccisi; `python3 scripts/fornitura-locale.py --prova` con esito; `--stato` provato; `systemd-analyze --user verify`; CI verde sul branch dopo l'unico push. Commit piccoli, uno per punto. Sezione «Giro 2» in coda al report.
Cartella report: docs/revisioni/ci-locale/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
