# Task per implementer: correzione del BLOCCA sul controllo OSV (giro 2)

Agente: implementer
Worktree: ci-fornitura
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura.

## Contesto
Seguito di `docs/revisioni/ci-fornitura/task-implementer.md` (tuoi commit d3d1fb0, a0f238c). Il `code-reviewer` ha dato **BLOCCA** (`docs/revisioni/ci-fornitura/report-code-reviewer.md`, risposta `risposta-code-reviewer.json`): il percorso di rete reale di `scripts/osv-check.py` (`invia_http`, «OSV non raggiungibile → errore») non è coperto dai test; il test della rete giù solleva `ErroreOsv` e aggira `invia_http`, quindi un mutante in cui `invia_http` ingoia l'errore lascia la suite verde. Prova: `docs/revisioni/ci-fornitura/prove-code-reviewer/` (`prova-mutante.sh`, `test_invia_http_fail_closed.py`). Il code-reviewer riporta anche, verificato: una risposta troncata (`http.client.IncompleteRead`) esce con traceback e codice 1 (quello delle vulnerabilità) invece del codice 2 degli errori di OSV. Il `compliance-auditor` (`report-compliance-auditor.md`) riporta come minore: righe del lockfile in formato diverso da `nome==versione` (es. `nome[extra]==v`, `nome @ url`) ignorate in silenzio (fail-open).

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10), parte di CI; decisione DECISIONS §6 «Catena di fornitura» punto 1.
Perimetro: solo `scripts/osv-check.py` e `tests/test_ci_osv_check.py`, più il report.
Repository: .worktrees/ci-fornitura; branch di lavoro: impl/ci-fornitura
Push: sì (solo `impl/ci-fornitura`)
Vincoli specifici:
1. Test reali di `invia_http` (senza rete esterna: per esempio un server HTTP locale su `127.0.0.1` avviato nel test, o un'eccezione della libreria standard al livello del socket/`urlopen`) che falliscono se `invia_http` ingoia l'errore: rete non raggiungibile, timeout, stato HTTP diverso da 200, corpo non JSON, risposta troncata. Ogni caso deve dare il codice di uscita degli errori di OSV (2), distinto da quello delle vulnerabilità (1). Verifica che i tuoi test falliscano sul mutante del code-reviewer (`prova-mutante.sh` descrive come lo costruisce; non modificare i file in `prove-code-reviewer/`; eseguili per controllo).
2. `http.client.IncompleteRead` e gli altri errori di `http.client` gestiti come errore di OSV (codice 2, messaggio chiaro, senza traceback).
3. Lettura del lockfile fail-closed: ogni riga di pacchetto che non corrisponde al formato atteso fa fallire il controllo (codice 2), e il numero di pacchetti letti deve coincidere con il numero di blocchi di pacchetto del lockfile; test per entrambi i casi.
4. Nessun altro cambiamento (non toccare workflow, Dependabot, README salvo che il comportamento documentato cambi).
5. Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde nel worktree (ambiente come nel task precedente: `. .venv/bin/activate`, `PGHOST=127.0.0.1 PGPORT=5433 PGUSER=root GRAVYA_E1_TEST_DSN="host=127.0.0.1 port=5433 user=root" API_ENV=development`); le prove del code-reviewer passano sul codice corretto (stanno solo nel repository principale: dalla radice del worktree, con il `.venv` attivo, `bash ../../docs/revisioni/ci-fornitura/prove-code-reviewer/prova-mutante.sh` e `OSV_SCRIPT=scripts/osv-check.py python -I -m pytest -q -p no:cacheprovider ../../docs/revisioni/ci-fornitura/prove-code-reviewer/test_invia_http_fail_closed.py`; il mutante dello script si basa su una riga precisa di `invia_http`: se la tua correzione la cambia, dichiaralo nel report e dimostra con un mutante equivalente che i tuoi test lo rilevano); `python3 scripts/osv-check.py requirements.lock.txt` con esito 0 sul lockfile attuale; CI verde sul branch dopo il push. Commit piccoli, uno per punto. Aggiungi una sezione «Giro 2» in coda a `docs/revisioni/ci-fornitura/report-implementer.md`.
Cartella report: docs/revisioni/ci-fornitura/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
