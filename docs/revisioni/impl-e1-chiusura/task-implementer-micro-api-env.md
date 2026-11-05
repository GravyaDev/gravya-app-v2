# Task per l'implementer: micro-correzione API_ENV (dopo il BLOCCA del giro 6)

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente (2026-11-05): «(a, micro-correzione)».

Branch unico `claude/docs-ondata-1` (il codice di E1 è stato unito con il merge 9311762; non creare branch nuovi). Fonte: `docs/revisioni/impl-e1/report-code-reviewer-giro6.md`, sezione 3.

Correzione (solo questa):
1. `src/gravya_e1/tracing.py`, `TracingHelper.__init__`: togliere la condizione `self._production_override is None and` dal blocco per `API_ENV` non impostata, così il blocco con segnale vale sempre, come per un valore fuori insieme (DECISIONS §6 «E1: ambiente e avvio»; catalogo v1.8 §18).
2. Test: impostare `API_ENV=development` per le suite (variabile esportata nel README e nella CI, oppure fixture autouse in `tests/conftest.py`); aggiornare il test proprio `test_api_env_assente_non_blocca_con_production_override_esplicito`, che deve diventare «blocca anche con production_override». Non toccare i file di prova dei revisori.
3. README: togliere l'eccezione e indicare che `API_ENV` va sempre impostata (anche per le prove dei revisori).

Criterio di fine: `tests/` verde 10 volte; prove dei revisori (giri 1-5, con `PGDATABASE` dove serve e `API_ENV=development`) con gli stessi esiti del giro 6; nessun file in /tmp. Report: sottosezione «Micro-correzione API_ENV» in coda a `report-implementer.md`. Verifica: il coordinator riesegue le suite (decisione dell'utente: nessun altro giro di revisione).
