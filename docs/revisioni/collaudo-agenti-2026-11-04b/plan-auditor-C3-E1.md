# Plan-auditor — C3 v1.4 ed E1 v1.4 (2026-11-04)

Esito: **BLOCCA**

Letture integrali: PRINCIPI.md (15), DECISIONS.md (172), C3 (235), E1 (196), Prompt e workflow.md (113).
Solo grep, senza lettura: Piano generale.md (righe C3/E1/HITL/Tracing), A1, A3, B1, B2, C1, E2, E3 (righe con hitl/approval/gravya./segment/E1).
`docs/catalogo-variabili.md` non esiste nella sandbox. Di conseguenza nessuna variabile di C3 o E1 può essere verificata contro il catalogo (nomi, default, intervallo, chi modifica, pagina). Questo è un rilievo in sé (R-18).

## Bloccanti

**R-01. C3 §6, Appendice C (DA-C3-04) e §3: TTL con solo superadmin e DA "aperta".**
- Testo C3: «(a) 24 h come default di piattaforma, modificabile dal superadmin (DX-13); (b) anche override per azienda … (a) in ondata 1. Resta aperta in DECISIONS.md».
- DECISIONS DA-C3-04 è **Decisa**: 24 h default, il superadmin fissa default e intervallo min/max, l'admin agenzia sceglie entro l'intervallo (DX-22); min 1 h, max 168 h.
- C3 tratta come opzione una scelta già presa e rinvia l'override per azienda. Non riporta l'intervallo 1–168 h né chi può modificare la variabile (DX-15, DX-22).
- Verificato.

**R-02. C3 §7 e AC-12, E1 §5 e criterio 8: valore non leggibile o non valido.**
- Testo C3: «se non riesce a leggerle, non cancella (fail-closed DX-13)». AC-12: «lo sweeper non chiude e la retention non cancella».
- Testo E1: «il job di retention non cancella nulla su un valore non valido». Criterio 8: «con un valore non valido il job non cancella nulla».
- DX-17: azioni bloccate (fail-closed), ma le **cancellazioni programmate usano l'ultimo valore valido versionato**, e parte un segnale ad A5.
- C3 ed E1 contraddicono DX-17. E1 §5 si contraddice anche da solo: «si mantiene l'ultimo valore valido» e subito dopo «non cancella nulla».
- Il segnale ad A5 è nominato in C3 AC-12 ma non in E1 criterio 8.
- Verificato.

**R-03. E1 §4.1 (classi prodotte, punto 3) e §5 (accesso cross-tenant): proprietà del log degli accessi.**
- Testo E1: «Classi di dati prodotte da E1: … (3) log degli accessi cross-tenant del superadmin (§5)».
- Testo E1 §5: la route dedicata registra «chi, quando, tenant, traccia o filtro, motivo» e il log è di E1.
- DX-18: il log appartiene ad A6, con schema unico. E1 e A1 lo usano e non lo possiedono.
- E1 lo tratta come proprio (classe prodotta, schema proprio). C3 AC-13 lo tratta correttamente come log da usare, ma non cita A6.
- Verificato.

**R-04. E1 §5 e §7, C3 §6: «modificabili solo dal superadmin».**
- Testo E1: «modificabili solo dal superadmin senza rilasci».
- DX-22: configurabile «da UI superadmin o admin agenzia». DX-15: per i dati di una specifica agenzia, l'agenzia sceglie dentro l'intervallo. DX-16: ogni classe ha un intervallo min/max come variabile protetta.
- Né E1 né C3 dichiarano intervalli o il ruolo dell'admin agenzia. Il testo «solo superadmin» è in conflitto con DX-15/DX-22.
- Verificato.

**R-05. C3 §7 AI Act, riga «etichetta art. 50»: presentata come aperta.**
- Testo C3: «se C3 debba mostrare all'approvatore o allegare un'etichetta "generato da AI" resta **aperto** (DECISIONS.md §6, da coordinare nell'ondata 2)».
- DECISIONS §6 è **Decisa** (2026-11-03): contratto di output C1 con `ai_generated` (`model`, `prompt_ref`), «C3 lo mostra all'approvatore».
- Il payload di §4.1 (`approval_required`/`input_required`) non ha il campo `ai_generated`. Si tratta come aperta una scelta già presa e il contratto non combacia con C1.
- Resta aperto solo l'art. 50(2) per il testo sintetico (DECISIONS §4, «Da riportare»), che C3 non cita.
- Verificato.

**R-06. C3 §4.1/AC-9 contro E1 §4.2: i campi del segmento `decision` non combaciano.**
- Testo C3 §7: «segmento `kind=decision` con `gravya.decision.kind=hitl` … nella traccia entrano solo identificativi e hash degli argomenti». AC-9: «ogni transizione … record di traccia E1 … solo identificativi e hash».
- E1 §4.2, `decision`: `gravya.decision.kind`, `gravya.decision.outcome`, `gravya.policy.bundle_*` se policy, «l'identificativo del revisore (pseudonimo)» se hitl.
- `gravya.tool.args_hash` esiste solo per `kind=tool`. Per `decision` non c'è un attributo hash né `request_id`/`approval_id`.
- E1 non definisce un nome per l'attributo del revisore né i valori ammessi di `gravya.decision.outcome`. C3 ha sei transizioni (`requested`, `approved`, `denied`, `input_provided`, `expired`, `outcome`) che non sono mappate sugli outcome.
- AC-9 di C3 non è soddisfacibile con la whitelist E1, che scarta gli attributi fuori whitelist.
- Verificato.

**R-07. E1 §4.2 non ha l'attributo `config_version` (DX-21).**
- DX-21: nome unico `config_version`, «aggiunto alla whitelist del segmento decision di E1».
- E1 §4.2 non lo contiene. Nel testo di E1 e C3 non compaiono `config_version` né l'evento `platform.config.changed` (produttore A6).
- Verificato (grep nei due file e lettura integrale).

## Da riportare

**R-08. C3 §6 passi 1-2 e §5, contro A3 e B2: chi parcheggia e chi riceve `require_approval` (DX-05 aperta).**
- C3: «L'esecutore propone una scrittura … la policy risolta restituisce `approvalRequired=true` … La chiamata viene parcheggiata». Operazione «Parcheggia una chiamata — run (solo il servizio)».
- A3: «A3 restituisce solo `require_approval`». B2: «`require_approval`: risposta `approval_required` e richiesta a C3». Flusso A3: «B2 sospende e passa a C3».
- DX-05 è **Aperta** e C3 la tratta come risolta a favore del run.
- C3 non ha nella §5 l'operazione «ricevi richiesta da B2» né «emetti token monouso», che A3 e B2 si aspettano da C3. Il token compare solo come passo del replay in §6.
- Il campo `approvalRequired=true` non esiste in A3, che ha `result=require_approval`.
- Il campo `permission_key` ha nome diverso (`tool_class`/`permission_key`). C3 §3 dice che A3 «classifica il tool come REQUIRES_HITL/MONEY_WRITE», ma in A3 `tool_class` è un input fornito da B2 dal catalogo.
- Verificato (A3/B2 solo con grep).

**R-09. E1 §5 e §9 Fase 0, Appendici B e C (DA-E1-08): residuo «DA RIPORTARE» già deciso.**
- DX-19 è **Decisa**: aggregati senza identificativi di default, singola traccia solo su richiesta dell'agenzia o per incidente, con log.
- E1 App. C: «Resta aperto il solo residuo … DA RIPORTARE ALL'UTENTE». E1 §9 Fase 0 ripete lo stesso residuo.
- DECISIONS §2 riga DA-E1-08: Decisa.
- Né E1 né C3 §7 «Accesso cross-tenant» descrivono la regola degli aggregati.
- Verificato.

**R-10. C3 e E1: DX-14 «DA RIPORTARE / non ancora decisa» è superata.**
- Passi: C3 §3, §11 (rischio 7), App. B; E1 §3, §9, §11, §12, App. B.
- DX-14 è Decisa (A6, ondata 2). DX-12 (F6) è decisa.
- A6 (e A5 in C3 §3) sono dipendenze di ondata 2 per documenti di ondata 1. C3 §3 «A5» non è marcata come ondata 2; E1 non marca F6/A6.
- Dipendenza da un'ondata successiva non dichiarata. A3 prevede una tabella di audit minima in ondata 1, che C3 non cita.
- Verificato.

**R-11. C3 App. C (DA-C3-02) e DA-C3-04: righe «da registrare/aperta» superate.**
- DA-C3-02: «la chiusura formale resta da registrare in DECISIONS.md». DECISIONS la riporta già **Chiusa**.
- Stato nel registro e testo del documento divergono.
- Verificato.

**R-12. E1 §4.1/§4.2 e App. C: DA-E1-04 e DA-E1-07 sono Aperte ma usate come scelte.**
- Il testo dice «Tabelle **separate** dall'audit legale» e usa `kind` dedicati (retrieval, decision).
- DECISIONS le riporta Aperte. Per DA-E1-03 il testo lo dice («resta formalmente aperta»), per le altre due no.
- Verificato.

**R-13. E1 §4.1 (partizioni per mese) contro le durate configurabili.**
- Testo: «Partizionamento per tempo (per mese) per applicare la politica di retention DX-09 con una `DROP PARTITION`».
- Le durate sono configurabili da UI (DX-13, DX-15, DX-22), quindi un valore non multiplo del mese, ad esempio 45 giorni, non è applicabile con un drop di partizione.
- Anche la granularità «mensile» è un parametro fisso (DX-22).
- Dedotto.

**R-14. E1 §4.2 e §3 contro C1/A1: interfacce verso E1 senza kind né attributi.**
- C1 criterio 6 (dedotto da grep) richiede `gravya.workflow.id`, `gravya.workflow.version`, `gravya.workflow.node_id` per il 100% dei nodi, e C1 §3 chiede record «per run, nodo ed edge».
- E1 definisce solo `gravya.workflow.node_id` (id e versione sono colonne di `gravya_traces`) e nessun kind per nodo/edge.
- A1 dichiara «eventi `graph.*` nel modello DB-native di E1», ma E1 non ha un kind `graph` e DECISIONS §4 dice che le mutazioni A1 «non diventano segmenti E1». E1 §3 elenca A1 tra gli emittenti.
- B2 emette `decision_id` (A3), che non ha un attributo nel segmento `tool` o `decision` di E1.
- A3 usa un attributo `gravya.company_id`, mentre E1 ha la colonna `company_id` (DX-07 aperta).
- Dedotto (grep sugli altri documenti).

**R-15. DECISIONS §4 «Da riportare» non applicate o non richiamate in C3 ed E1.**
- Ambito NIS2 non accertato: C3 §7 (NIS2) ed E1 §7 trattano la notifica 24 h/72 h come certa e non richiamano la riserva.
- Calendario AI Act dopo l'Omnibus: C3 §7 ed E1 §7 non lo riportano.
- Diritto del marketing assente (PV-01), art. 50(2) marcatura del testo: non richiamati in C3.
- Data Act art. 25/29 su E1 §4.1 («restituzione o cancellazione entro 30 giorni»): non segnalato come da riverificare.
- Verificato (assenza rispetto al registro).

**R-16. E1 §5 e C3 §7: log degli accessi con «retention 12 mesi» ripetuta nel testo.**
- Il default di 12 mesi è citato in più punti (E1 §4.1, §5, §7, §11, criterio 8; C3 §7).
- DX-22(c): i documenti di dettaglio citano solo il nome della variabile. Il catalogo non esiste, quindi i nomi non sono verificabili.
- Dedotto.

**R-17. E1 §7, §5 e C3 §7 e App. B: soglie e parametri senza nome di variabile, senza intervallo, senza «chi modifica».**
- E1: «soglia di overhead p95 (default 5 ms, proposta da validare)», buffer e soglia di perdita «non fissati», nessun nome di variabile.
- C3: `hitl.request_ttl_hours` e `hitl.resume_latency_p95_ms` marcati «proposte» (App. B), senza intervallo né pagina.
- Valori fissi: nome dell'header di correlazione (E1 §5, «da fissare»), granularità mensile delle partizioni (R-13), HMAC e firma del resume (C3 §5), durata «24 h» riportata come costante gravya-app.
- Le credenziali (chiave HMAC di resume e del token monouso) richiedono la pagina dedicata di DX-22(b), che C3 non cita.
- Verificato per C3 ed E1; non verificabile contro il catalogo (assente).

**R-18. Assenza di `docs/catalogo-variabili.md` (DX-22(c)).**
- Con il catalogo assente non si può verificare nessuna variabile. Il catalogo deve nascere prima della v1.5, oppure la v1.5 deve elencare le variabili in un'appendice provvisoria con nome, default, intervallo, chi modifica, pagina.
- Variabili da catalogare:
  - C3: TTL, soglia di latenza di ripresa, durate payload 30 giorni, checkpoint 30 giorni, decisioni 12 mesi.
  - E1: durate tracce 90 giorni, log accessi 12 mesi, report eval 12 mesi, overhead 5 ms, buffer, soglia di perdita.
- Verificato (il file manca).

## Minori

**R-19. E1 §8: numerazione dei criteri fuori ordine.** L'ordine è 8, 10, 11, 9. Nessun problema di testabilità, ma i rimandi in §10 («criteri 1-5, 7-11») sono confusi.

**R-20. C3 §4.4: nomi evento `hitl_*`.** Diversi dalla convenzione puntata degli altri documenti (DX-07 aperta). C3 lo dichiara, quindi nessuna violazione. Per C1 `workflow.run.interrupted` «verso C3» non è consumato da C3: interfaccia dichiarata ma non chiusa.

**R-21. DX-21: identità dell'attore e `decided_by_user_id`.** C3 §4.3 (`decided_by_user_id`) ed E1 (revisore pseudonimo) non dicono che l'identità è fornita da A6. Le classi senza durata che F6 assegna (es. checkpoint in pausa, contatori) non sono citate come tali.

**R-22. Template.** Le 12 sezioni sono in ordine in entrambi i documenti. Nessuna stima temporale, taglie S/M/L (C3 L, E1 M). Le soglie numeriche sono quasi tutte marcate «proposta da validare». Fanno eccezione E1 criteri 8 («90 giorni», derivato da DX-09 §5, accettabile) e C3 AC-11 («30 giorni», derivato).
