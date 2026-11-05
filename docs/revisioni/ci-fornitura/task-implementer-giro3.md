# Task per implementer: correzione del secondo BLOCCA sul controllo OSV (giro 3)

Agente: implementer
Worktree: ci-fornitura
Preparato dal coordinator il 2026-11-05. Branch: impl/ci-fornitura.

## Contesto
Seguito di `docs/revisioni/ci-fornitura/task-implementer-giro2.md` (tuoi commit e3759ef, c11fa33, 3f64f3d). Verifica del `code-reviewer` sul giro 2: **BLOCCA** (`docs/revisioni/ci-fornitura/report-code-reviewer-giro2.md`, risposta `risposta-code-reviewer-giro2.json`, prove in `prove-code-reviewer-giro2/`):
- bloccante, verificato: il rifiuto di uno stato HTTP diverso da 200 in `invia_http` non è protetto da test; togliendo il controllo, o riducendolo a `>= 400`, la suite resta verde; un 201, 203 o 206 con corpo `{"results":[{}]}` verrebbe accettato come «nessuna vulnerabilità» (codice 0);
- da riportare, verificato: il test del timeout non verifica il timeout (la risposta tardiva `{}` viene rifiutata per il formato, quindi passa anche senza timeout); serve una risposta tardiva ma valida;
- minore, verificato: il report del giro 2 dice che il caso 204 è coperto da un test; il test passa con e senza il controllo dello stato, quindi l'affermazione è inesatta.

## Task
Documento: docs/E1-tracing-distribuito.md (versione 1.10), parte di CI; DECISIONS §6 «Catena di fornitura» punto 1.
Perimetro: solo `tests/test_ci_osv_check.py` (e `scripts/osv-check.py` solo se un test nuovo rivela un difetto), più il report.
Repository: .worktrees/ci-fornitura; branch di lavoro: impl/ci-fornitura
Push: sì (solo `impl/ci-fornitura`)
Vincoli specifici:
1. Test con risposta 2xx diversa da 200 (almeno 201, 203 e 206) con corpo valido `{"results":[{}]}` (o con un risultato per ogni query): codice 2. Il test deve fallire se il controllo dello stato viene tolto o ridotto a `>= 400`: dimostralo con questi due mutanti, costruiti in una cartella di lavoro dentro `docs/revisioni/ci-fornitura/` e poi cancellata.
2. Test del timeout con una risposta tardiva ma **valida**: codice 2. Deve fallire con il mutante senza timeout (`timeout=None`), dimostrato come sopra. Il test non deve durare molto: usa il timeout configurabile dello script, se c'è un modo di passarlo nel test senza cambiare il valore di default.
3. Correggi nel report la frase inesatta sul caso 204, nella sezione «Giro 2», e aggiungi una sezione «Giro 3» con i mutanti provati e i loro esiti.
4. Le prove del code-reviewer (`docs/revisioni/ci-fornitura/prove-code-reviewer-giro2/`, nel repository principale: dalla radice del worktree con `../../docs/...`) devono dare esito coerente con la correzione; non modificarle.
5. Criterio di fine: `pytest -q -p no:cacheprovider --basetemp=.pytest_basetemp` verde nel worktree (ambiente come nei task precedenti); CI verde sul branch dopo il push. Commit piccoli.
Cartella report: docs/revisioni/ci-fornitura/

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Se un test contraddice il task o una decisione, fermati e chiedi (riporta il punto in `decisioni_mancanti` o `divergenze`).
- Nessun valore nel codice, nemmeno minimi, massimi o valori decisi (DX-22): vanno nel registro delle variabili.
- Lavora sul branch indicato; non creare branch nuovi.
