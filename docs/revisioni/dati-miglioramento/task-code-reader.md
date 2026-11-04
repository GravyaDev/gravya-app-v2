# Task per il code-reader: meccanismo di anonimizzazione di gravya v1 (G1 (b))

Preparato dal coordinator il 2026-11-04 (sessione 7). Non ancora lanciato: limite di 25 thread raggiunto, in attesa che l'utente archivi i thread finiti.

Ambito: storico. Repository: gravya-app (/workspace/gravya-app; riportare il commit con git rev-parse), se serve gravya-app-kloudify. Solo riferimento (PV-03).

Scopo: pianificare in v2 un meccanismo di "dati per il miglioramento del servizio" (prestazioni degli LLM e della piattaforma, analisi statistica). L'utente dice che in v1 esisteva un meccanismo non terminato che anonimizzava i dati a fini di miglioramento del servizio, basato su un motore locale e non su Presidio. Verificare se services/pii-redactor è quello giusto, senza darlo per scontato.

Perimetro: intero repository (server/, services/, ui/, docs/, migrazioni, test; escluso node_modules), anche storia e branch non unite (git log --all -S "anonymi", -S "anonimizz").

Domande:
1. Dove si trova il meccanismo (file, servizi, tabelle, job, branch o PR) e che motore usa (libreria o implementazione locale, modelli, regole, dizionari)?
2. Dati in ingresso, trasformazioni applicate, reversibilità (tabella di corrispondenza, chiavi).
3. Dove finiscono i dati trasformati, chi li usa e per cosa, con quale retention.
4. Isolamento tra tenant, consenso o opt-in dell'agenzia.
5. Cosa era incompleto (TODO, issue, test mancanti), cosa concludono i documenti di docs/compliance/.
6. Rapporto con il ciclo learning proposals (learning-proposal-apply.ts, prompt_improvement_job.py) e con services/pii-redactor.

Report: docs/revisioni/dati-miglioramento/code-reader-meccanismo-v1.md. Citazioni file:riga o commit, verificato distinto da dedotto; se non trovato, dirlo con le ricerche fatte.
