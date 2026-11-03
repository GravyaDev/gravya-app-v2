# Revisione compliance — ondata 1 v1.4 (2026-11-03)

Esito: **RIPORTA**. Nessuna violazione di decisioni o PV trovata. Ci sono tre rilievi da riportare all'utente e uno minore.

Perimetro controllato: E1, E2, E3, A1, A3, B1, B2, C1, C3 (v1.4), DECISIONS.md (DX-13, DX-14, §5, §6), PRINCIPI.md. Ho controllato in modo mirato come i documenti recepiscono DX-09 §5, DX-13 (superadmin, variabili versionate/auditate/fail-closed, accesso cross-tenant entro art. 28 con log) e DX-14. Ho verificato che in tutti e nove i documenti DX-14 compaia come "da riportare/proposta", mai come decisa.

## Rilievi

1. **da_riportare — GDPR art. 28(3)(a), art. 5(1)(e).** In DECISIONS.md §5 ("Si possono modificare in piattaforma dal superadmin (DX-13)") e nei §7 di E1, B2, C1 e C3, le durate di retention dei dati dei tenant sono variabili che il superadmin di Gravya, cioè il responsabile, può modificare in modo unilaterale. La durata di conservazione dei dati del titolare fa parte delle istruzioni del titolare. Se il superadmin allunga una durata senza un'istruzione dell'agenzia o una clausola contrattuale (DPA), Gravya rischia di trattare i dati oltre le istruzioni. Proposta: collegare le modifiche di retention ai contratti o DPA, oppure fissare per ogni classe un intervallo ammesso tra un minimo e un massimo. Interpretazione legale da confermare. (dedotto)
2. **da_riportare — GDPR art. 5(1)(e), NIS2 art. 21.** Non ho trovato intervalli ammessi per le durate di retention: esistono solo per le soglie di A3 (A3 §4). Di conseguenza il fail-closed "valore non valido" non ha un criterio per le durate. Un valore molto basso cancella evidenze di audit o di incidente; uno molto alto viola la minimizzazione. E1 §10 riconosce il rischio di cancellazione prematura, ma non definisce limiti. (verificato: grep di "intervall" in DECISIONS.md senza risultati)
3. **da_riportare — GDPR art. 5(1)(e) contro fail-closed.** C3 AC-12 stabilisce che con il registro non leggibile "la retention non cancella". Il fail-closed in questo caso porta a conservare dati personali oltre la scadenza, senza un limite di tempo. È una scelta di merito ragionevole, ma va resa esplicita: serve un segnale ad A5 o F6 e un limite all'arretrato. Va anche verificata la coerenza con E1 e B2. (verificato C3 riga 125; dedotto per gli altri)
4. **minore — NIS2 art. 21(2)(i), DX-14.** L'autenticazione del superadmin (MFA, gestione delle credenziali) non ha ancora un responsabile finché DX-14 è aperta. A1 §5 lo dichiara correttamente. Va risolta prima dell'implementazione. (verificato A1 riga 35)

## Controlli con esito positivo
- In tutti i documenti, l'accesso cross-tenant è riservato al superadmin, con log fail-closed e retention di 12 mesi, entro le istruzioni del titolare.
- In tutti i documenti, la modifica delle variabili è versionata, auditata e fail-closed.
- DX-14 compare come proposta (A6) in tutti e nove i documenti.
- C3: il superadmin non decide le richieste HITL dei tenant (C3 §7).
- Le durate di retention corrispondono a DECISIONS.md §5.
