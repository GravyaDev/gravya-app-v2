# Plan-auditor — docs/catalogo-variabili.md v1.1

Esito: **RIPORTA**. Nessuna violazione di un PV né di una riga decisa che il catalogo applichi male. Nessuna interfaccia rotta con i nove documenti dell'ondata 1 (il catalogo non è citato da nessuno: `DA-CV`/`catalogo-variabili` non compaiono in A1..E3, che sono ancora v1.4). Restano scelte da riportare all'utente e disallineamenti con DECISIONS da sistemare prima che i doc-writer citino i nomi.

Letture: catalogo 1-424 di 424; DECISIONS 1-213 di 213 (compreso §7 e le righe §4/§5/§6 aggiornate); rapporto precedente 1-119 di 119. Registro norme: solo grep (3.4.2(b), «trimestrale», soglie), nessuna lettura. PRINCIPI, template e master plan non riletti: il catalogo non è un documento di dettaglio. I nove documenti: solo grep per `ALWAYS_HITL`, `MONEY_WRITE`, `KLOUD_APPROVAL_DEFAULT`, `DA-E3-11`, `DA-CV`.

## 1. Rilievi della prima revisione: stato

| Rilievo v1.0 | Stato in v1.1 |
|---|---|
| R1 opzioni escluse nelle DA | risolto: DA-CV-01..07 decise e allineate a DECISIONS §7. Ne restano di nuove (vedi sotto) |
| R2 intervalli "da definire" | risolto: regola 8 (validità tecnica + tre regole relazionali), RR per la retention |
| R3 segreti della CI | risolto: C11, §15, §18 |
| R4 "deciso" sovrastimato | risolto: «vincolo derivato da DX-10 (c) e dal registro», «valore del registro» |
| R5 `incident.gdpr.*` | risolto: C5, §13.3 |
| R6 citazioni e «legal hold» | risolto: «E1 §5, CA8, App. B»; righe §16 per B2, C1, C3, E1, E2 |
| R7 variabili implicite | risolto: `b2.idempotency.window_hours`, rate limit a tre, `API_ENV` (ma vedi R5 sotto) |
| R8 legenda | risolto: nessuna riga con default «da definire» e stato «proposta» (unica con valore: `incident.recurring_min_count`) |
| R9 partizioni | risolto: regola 8c |
| R10 override per classe | risolto in parte: DA-CV-10 e riga `retention.tenant.<classe>` |
| R11 `run_token`/`tool_grant_ref` | resta aperto, ora numerato DA-CV-13 |
| R12 | `eval.gate.max_blocking_failures_count` tolta (C7); DA-E3-07 resta Aperta in DECISIONS, dichiarato |

## 2. Rilievi nuovi

**R1 — da_riportare — DA-CV-12 riapre una scelta presa in C6 e raccomanda l'opposto (verificato).**
Catalogo §17.2: «DA-CV-12 | La scelta restituzione/cancellazione ... dipende da `retention.tenant_override_enabled` | (a) ... (come in C6); (b) sempre disponibile ... | Raccomandazione (b)». DECISIONS DX-09 e §5 (C6): «La scelta dell'agenzia a fine contratto ... sono catalogati e attivi con l'override per agenzia (DA-C3-09)»; «Sono attivi con l'override per agenzia». L'opzione (a) è già la decisione. Il dubbio di merito (art. 28(3)(g) lascia la scelta al titolare) è fondato, ma va presentato come richiesta di modifica di C6, non come DA aperta. Inoltre non esiste una riga corrispondente in DECISIONS §4 né §7. Fonte: DX-09/C6.

**R2 — da_riportare — DA-CV-08: stato in contrasto con DECISIONS §7 (verificato).**
Catalogo §17.2 «Aperte»: «DA-CV-08 | Valore del termine ... (la natura contrattuale è decisa, C5)». DECISIONS §7: DA-CV-08 «**Decisa (2026-11-04, utente)**», con il valore rinviato a §4. Stesso ID, stato opposto. Va riallineato: o DA-CV-08 resta Decisa e il valore passa a una riga «Da riportare» (già c'è in §4), o si cambia titolo e numero.

**R3 — da_riportare — DA-CV-09..17 non registrate in DECISIONS; riferimenti incrociati sbagliati (verificato).**
I numeri 09-17 non collidono con DECISIONS §7 (che arriva a 08), ma nessuna è registrata. DECISIONS §4 riferisce il default HITL a «DA-CV-05» («Chi modifica il default di `hitl.approval_required_default` (DA-CV-05)»), il catalogo lo chiama DA-CV-15. Le altre righe di §4 non hanno ID: spegnimento flusso (= DA-CV-09), override per classe (= DA-CV-10), valori non validi e backup (= DA-CV-17), credenziali (= DA-CV-16, parte b), fatturato (= DA-CV-14), run_token (= DA-CV-13). Senza DA-CV-11 e DA-CV-12 in §4 (vedi R1 e R5). Il registrar deve numerare le righe di §4 con gli ID del catalogo, o viceversa.

**R4 — da_riportare — DA-CV-09 (c) offre un'opzione esclusa da C2 (verificato).**
DA-CV-09 (c): «solo motivazione e audit». DX-10 (C2): «Lo spegnimento del flusso richiede una condizione documentata». La riga stessa di §13.1 lo dice. L'opzione (c) è esattamente ciò che C2 vieta; da togliere. Fonte: DX-10 C2.

**R5 — da_riportare — `API_ENV`: DA-CV-11 e C8 (verificato).**
DECISIONS §6 (C8, decisa): variabili da aggiungere al catalogo come «da definire», tra cui «guardia `API_ENV`». Catalogo: §19 la elenca come riga («guardia di ambiente (`API_ENV`) | da definire»), §16 dice «non citare il nome come variabile di catalogo finché DA-CV-11 è aperta», DA-CV-11 raccomanda (a) «invariante di deploy, fuori dal catalogo». Tre trattamenti incompatibili per lo stesso oggetto; l'opzione (a) contraddice la parte di C8 che la mette in catalogo. Da riportare con la richiesta di modificare C8 oppure di tenere la riga.

**R6 — minore — `retention.tenant.<classe>`: nome e perimetro (verificato il nome, dedotto il perimetro).**
- Nome: DECISIONS §5 (C6) dice `retention.<classe>.tenant_value`; il catalogo usa `retention.tenant.<classe>`. I nomi vanno allineati (regola «stessi nomi»).
- Perimetro: la riga dice «una per ogni durata sopra», quindi include `retention.cross_tenant_access_log_months` (controllo sull'operatore Gravya), `retention.incident_evidence_*` (C10: massimo e riesame fissati da F6), `config_audit`, `auth_events`, `credential_access`, `consent_optout`, `incident_signals`, `pseudonym_map`. DX-15 prevede la scelta dell'agenzia «per i dati di una specifica agenzia»; per i log propri di Gravya e per le evidenze di incidente una scelta dell'agenzia è in tensione con C10 e con l'obbligo di conservare i segnali (C2). Va elencato quali classi sono per-agenzia.

**R7 — minore — regola 8(b) usa `_max` e non il TTL effettivo (dedotto).**
«`hitl.approval_token.ttl_s` non supera `hitl.request_ttl_hours_max`». L'admin agenzia può scegliere un TTL HITL di 24 h, con token valido fino a 168 h. DECISIONS DA-CV-02: «il TTL di un token non supera ... il TTL HITL». Il vincolo dovrebbe valere contro il TTL effettivo della richiesta (o essere dichiarato come limite di piattaforma, con l'effetto sul caso per agenzia).

**R8 — minore — testo non aggiornato dopo la registrazione di C1-C14 (verificato).**
Intestazione: «in corso di registrazione in DECISIONS.md»; §17.1 punto 17: «DECISIONS §5 e DX-09 dicono ancora "modificabili dal superadmin"»; punto 10 simile. DECISIONS ora ha le precisazioni (DX-09, §5, DX-22, DA-B2-07, §7). Il punto 17 è obsoleto, tranne la parte su DA-E3-07 (ancora Aperta).

**R9 — minore — retention in sola lettura con default «da definire» (dedotto).**
Per `config_audit_months`, `auth_events_months`, `credential_access_months`, `consent_optout_months`, `log_backup_months`, `data_backup_days`, `pseudonym_map_months`, `incident_signals_months`, `incident_evidence_*`: «sola lettura (RR)» e «da definire». RR dice che valgono i valori di DECISIONS §5, ma per queste classi §5 non ha valori: nessuno può impostarli da UI. DA-CV-17 (a) dice che l'azione si blocca, quindi la cancellazione non parte e il dato è conservato senza termine (GDPR art. 5(1)(e)). Va dichiarato chi imposta il primo valore (F6, con nuova versione del catalogo).

**R10 — minore — `incident.recurring_min_count` (verificato).**
Tipo «massimo: solo in diminuzione», ma «nessuno spazio di configurazione» (unico valore 2): di fatto è un valore fisso, tipo che la regola 6 prevede («fisso») ma che nessuna riga usa. Inoltre nella colonna del valore operativo compare «proposta da validare», mentre lo stato dice «vincolo derivato da DX-10 (c)». Allineare al tipo «fisso» o spiegare perché no.

**R11 — minore — regola 10 e §18 (dedotto).**
Regola 10: punti di contatto con il marketing includono «l'approvazione prima dell'invio verso terzi (§3, §18)». §18/C7(d): l'approvazione per i contenuti verso terzi «la decide l'admin agenzia»; §3 le permette di impostare `hitl.approval_required_default` falso (escluse `ALWAYS_HITL`/`MONEY_WRITE`). Non è detto che l'invio verso terzi ricada nelle due classi chiuse: l'approvazione prima dell'invio non è quindi un invariante. Da chiarire con A3/C3 se i contenuti verso terzi sono `ALWAYS_HITL`.

## 3. Controlli richiesti

1. **Confronto con DECISIONS.** DA-CV-01..07 e le fonti (C6, C12, C7, C9) coincidono. DX-22 C1: il catalogo applica la regola (limite di legge non modificabile; massimo solo in diminuzione; minimo solo in aumento). Nessuna riga «fisso» in §13 (R10). C2, C4, C5, C6, C8, C9, C10, C11: coerenti, salvo R1, R5, R6.
2. **DA-CV-08..17.** Collisione di numeri: nessuna con DECISIONS §7, ma DA-CV-08 ha stato opposto (R2). Aperte davvero (hanno riga «Da riportare» in §4): DA-CV-09, 10, 13, 14, 15, 16, 17. Già decise o con opzioni escluse: DA-CV-12 (R1, C6), DA-CV-09 (c) (R4, C2). DA-CV-15 rispetto a C7: aperta davvero (§4 lo dice), nessuna opzione esclusa da C7. DA-CV-11: R5. DA-CV-10 (c): «a discrezione del superadmin» è in tensione con DX-16 solo se l'intervallo manca; non lo conto come violazione.
3. **Conversioni.** 28 giorni (1 mese, massimo, per difetto): ok. 89 (febbraio-aprile non bisestile 28+31+30): ok per difetto. 184 (luglio-dicembre 31+31+30+31+30+31; anche maggio-ottobre): ok per eccesso, tipo «minimo» corretto (finestra più lunga = più restrittivo). Il catalogo dichiara che l'estensione a 3 e 6 mesi è sua (§17.1, punto 16). La regola 8c (31 giorni per mese, per eccesso) coerente.
4. **Nuove variabili.** §13: `initial_assessment_max_hours` (C3), `csirt_channel`/`csirt_contact` (C4), `*_days` (C1), `gdpr.*` (C5). §2: C8 e C10 coprono le classi nuove; `incident_signals_months` (C2, dedotto, dichiarato), `incident_evidence_*` (C10). §14: C9. §19: C8; `session_max_duration_hours` dedotto (dichiarato), `login_lockout_duration_minutes` è parte del blocco di C8. Nessun valore numerico inventato: tutti i numeri di §13.2 vengono dal registro (3.4.2(b) «trimestrale» verificato con grep) o dalla decisione; §19 solo «da definire».
5. **Invarianti §18.** Elenco coerente con DA-CV-05/C7 (a)-(d), con la riga DA-CV-05 (hash, whitelist, header, exit code, rete, `synthetic`), con C11 e C4. Eccezione `incident.*` al fail-closed coerente con C2. Punto aperto: R11.
6. **Tabelle.** 253 righe che iniziano con `|`: 130 a 7 colonne, 25 a 6, 82 a 4, 16 a 3. La somma dà 253; i conteggi per tabella corrispondono (7 col: tabelle di §2-§14; 6: DA-CV aperte e §19; 4: §15, §16, decise, storico; 3: §18). Nessuna riga con colonne mancanti.

Template e stime: nessuna stima temporale; il catalogo non è soggetto al template.
