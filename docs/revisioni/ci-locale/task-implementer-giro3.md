# Task per implementer: correzione del secondo BLOCCA sul job locale (giro 3)

Agente: implementer
Worktree: ci-locale
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-locale.

## Contesto
Seguito di `docs/revisioni/ci-locale/task-implementer-giro2.md` (risposta `risposta-implementer-giro2.json`, ultimo commit 19683a9). Verifica del `code-reviewer` sul giro 2: **BLOCCA** (`docs/revisioni/ci-locale/report-code-reviewer-giro2.md`, risposta `risposta-code-reviewer-giro2.json`, prove in `prove-code-reviewer-giro2/`). Leggi per intero il report: i numeri sotto rimandano ai suoi rilievi.

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10), parte di CI; DECISIONS §6 «Minuti di GitHub Actions» e «Catena di fornitura».
Perimetro: `scripts/fornitura-locale.py`, `scripts/agenti.py` (solo `worktree-unisci`), i loro test, report. Niente altro.
Repository: .worktrees/ci-locale; branch di lavoro: impl/ci-locale
Push: sì (solo `impl/ci-locale`, un solo push alla fine)
Vincoli specifici:
1. **Bloccante.** Test che falliscono con i mutanti del code-reviewer sulla traccia delle esecuzioni: `ERRORE_AGGIORNAMENTO` ed `ERRORE_ISSUE` rendono l'esecuzione non riuscita; `e_riuscita` considera il codice globale; `main` registra `prova` secondo l'opzione `--prova`. Dimostralo eseguendo le prove del code-reviewer (`../../docs/revisioni/ci-locale/prove-code-reviewer-giro2/` dalla radice del worktree), senza modificarle.
2. **Da riportare.** Test anche per gli altri mutanti sopravvissuti elencati nel report: `ultima_riuscita` con `min` al posto di `max`; confronto con l'ultimo commento della issue, non il primo; corpo della PR ripulito dalle credenziali; rimozione del worktree residuo; passaggio delle variabili d'ambiente in `worktree-unisci`.
3. **Minori.** `leggi_esecuzioni` fail-closed su righe malformate (data senza fuso orario, chiave `esito` mancante, data nel futuro): codice di errore del comando, senza traceback; `ripulisci` copre anche `ssh://utente:segreto@` e `Authorization: Bearer`; il test dello stato HTTP 201 di `tests/test_ci_osv_check.py` non deve dipendere dal carico (timeout del test più largo o server pronto prima della richiesta).
4. **Token dedicato** (compliance-auditor 2; decisione dell'utente del 2026-11-05: token fine-grained solo per `gravya-app-v2`, già creato). Il servizio systemd carica `GH_TOKEN` da `EnvironmentFile=%h/.config/gravya-fornitura/env` (obbligatorio: se il file manca il servizio non parte; percorso come costante dichiarata e nel README, con permessi 600 e cartella 700). `gh` e il push di git (credential helper `gh auth git-credential`) usano quel `GH_TOKEN`: verificalo nella documentazione di `gh` e dichiaralo nel report. Il passo che installa ed esegue pip-tools gira **senza** `GH_TOKEN`, `GITHUB_TOKEN` e `GH_HOST` nell'ambiente, con test che lo prova. Lo script, lanciato a mano, avvisa se `GH_TOKEN` non è impostato (userebbe il login generale di `gh`). Non leggere né stampare mai il contenuto del file del token, nemmeno nei test (usa file finti).
5. Ogni test nuovo deve fallire su un mutante corrispondente: per ciascuno, nel report, il mutante provato e l'esito (cartella di lavoro dentro `docs/revisioni/ci-locale/`, poi cancellata).
6. Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde 3 volte nel worktree con `set -a; . ../ci-locale.env; set +a`; prove del code-reviewer del giro 2 con tutti i mutanti uccisi; CI verde sul branch dopo l'unico push. Commit piccoli. Sezione «Giro 3» in coda al report.
Cartella report: docs/revisioni/ci-locale/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
