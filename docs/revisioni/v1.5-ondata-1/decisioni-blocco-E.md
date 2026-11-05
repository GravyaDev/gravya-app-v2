# Blocco di decisioni E: chiusura della v1.5 dell'ondata 1

Preparato dal coordinator il 2026-11-04 (sessione 7), dopo la revisione unica della v1.5: plan-auditor sull'ondata intera e compliance-auditor su A1-A3-B1, B2-C1-C3, E1-E2-E3 (tutti RIPORTA, nessun BLOCCA; report in questa cartella) e le revisioni del catalogo 1.2. Ogni voce ha la raccomandazione del coordinator; con "ok" l'utente le conferma tutte. Le correzioni senza scelta (parte 2) le applicano i doc-writer senza decisione.

## Parte 1. Decisioni

**E1. Hash degli argomenti e dei contenuti (DA-C3-12 = DA-E1-09; anche B2 e il `content_hash` del testo renderizzato di E2).** Un SHA-256 semplice di un dato breve è riconducibile al dato e resta un dato personale dopo la cancellazione. *Raccomandazione:* HMAC-SHA-256 con chiave per tenant, nella pagina credenziali, rotazione a due chiavi (DA-CV-23); la distruzione della chiave rende l'hash non riconducibile. Modifica l'invariante "SHA-256" di DA-CV-05. E2 usa due nomi distinti per l'hash del template e per quello del render; E1 registra solo l'hash del template.

**E2. Chi valuta strumento di trasferimento e sub-responsabile (DA-A3-08 = DA-B2-08).** *Raccomandazione:* A3, sulla policy compilata da A2 (come l'opt-in, DECISIONS §6); B2 e l'egress-proxy di B1 applicano lo stesso esito. Un solo criterio: il deny arriva entro un ritardo massimo misurato, variabile del catalogo (da definire con A2 e A6), uguale in A3 e B2.

**E3. Invii verso terzi (DA-A3-09, DA-B2-10, C1 `audience`).** *Raccomandazione:* (a) nell'ondata 1 i tool di invio verso terzi sono negati nel bundle (l'ondata 1 non va in produzione); (b) da D1-D4 la precondizione (base giuridica registrata, mittente identificato, meccanismo di opposizione) la verifica il connettore; (c) B2 rifiuta una chiamata a un tool di invio verso terzi se gli argomenti non portano `ai_generated` con `model` e `prompt_ref` (vale anche per il ciclo di tool dei nodi agente in B1); (d) il destinatario del contenuto (`audience`) si deriva dal catalogo dei tool di B2 e non lo dichiara l'autore del workflow; un solo vocabolario in B2 e C1, con un flag per l'interazione diretta con persone (art. 50(1)).

**E4. Classi di approvazione (DA-B2-11; A1, A3, C3).** *Raccomandazione:* vocabolario unico `ALWAYS_HITL` e `MONEY_WRITE` (sparisce `REQUIRES_HITL`); le altre azioni seguono `hitl.approval_required_default`. La classe la assegna il superadmin nel catalogo dei tool di B2, versionata e auditata; si può solo aggiungere, toglierla richiede la conferma della seconda persona con accesso superadmin. Un tool senza classe dichiarata va in `require_approval`.

**E5. Variabili prima di A6 e primo avvio (DA-A1-10 = DA-B1-09; punto del plan-auditor sul catalogo 1.2).** *Raccomandazione:* un'istantanea versionata delle variabili nel repository, modificabile solo con una PR, letta da tutti i documenti tramite una sola interfaccia (ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste). I valori "proposta da validare" valgono come primo valore valido, con segnale; i valori "da definire" hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione.

**E6. Prompt e input del job, gate E3 (DA-B1-10, DA-E2-04).** *Raccomandazione:* C1 risolve il prompt da E2 e passa al job il testo renderizzato e l'input tramite `input_ref`, che segue la classe dei payload sensibili temporanei; il job non accede al DB. Il gate E3 è obbligatorio per attivare ogni versione di prompt: E3 produce in CI un esito registrato (versione, hash, esito, data) che E2 verifica all'attivazione; E2 non chiama E3 a runtime.

**E7. Token di approvazione.** *Raccomandazione:* l'`approval_token` è legato a tenant, tool e hash degli argomenti approvati; lo consuma solo B2 (registro dei token consumati), A3 ne verifica firma e legame. Il `run_token` non è monouso (vale per tutto il run): si corregge l'invariante del catalogo §18.

**E8. Superadmin sui prompt delle agenzie (DA-E2-09 esteso).** *Raccomandazione:* come DX-19: di default solo metadati aggregati; lettura del testo, attivazione e rollback di un prompt di un'agenzia solo su richiesta dell'agenzia o per un incidente, con riferimento e log.

**E9. Proposte automatiche di prompt (E2, `learning_proposal`).** *Raccomandazione:* nascono solo da dati sintetici, metadati aggregati o istruzione scritta nel DPA; mai attraversando i tenant.

**E10. Dati sintetici di E3.** *Raccomandazione:* il validatore di E3 applica lo stesso controllo dei dati personali dei template di E2, in blocco, più una checklist nella PR; il documento dice da dove viene l'input da riscrivere.

**E11. Cifratura, backup e chiave del provider LLM.** Lacuna trasversale (nessun documento la assegna). *Raccomandazione:* cifratura a riposo e in transito e gestione delle chiavi assegnate ad A6; backup a F6 (con DA-CV-22); registrata in DECISIONS §4. La chiave del provider LLM non entra nel job di B1: le chiamate LLM passano dall'egress-proxy, che aggiunge la chiave e non registra corpi né URL completi.

**E12. Sub-responsabili e opposizione delle agenzie (GDPR art. 28(2)).** *Raccomandazione:* quando una destinazione o un sub-responsabile cambia, parte un'informativa alle agenzie; un'agenzia può registrare un'opposizione, e da quel momento il tool è negato per lei.

**E13. Decisioni dei documenti, con la raccomandazione del doc-writer o del coordinator:**
- DA-C3-10: nell'ondata 1 decide solo l'admin agenzia, con divieto di auto-approvazione (chi ha avviato il run non decide la propria richiesta).
- DA-C3-07 (c): una riduzione del TTL vale subito, un aumento solo per le nuove richieste. DA-C3-11 (a): sweeper come job interno al servizio di orchestrazione.
- DA-C1-07 (c): marcatura del testo rinviata alla lettura del Codice di buone pratiche, con scadenza prima del primo rilascio in produzione (l'art. 50 vale dal 2.8.2026). DA-C1-08 (a): cancellazione delle righe riferite all'interessato nei run chiusi. DA-C1-09 (a): `c1.max_duration_ms` misura solo l'esecuzione, escluse le attese HITL.
- DA-E1-10 (a), DA-E1-11 (a), DA-E1-12 (a): writer senza bypass di RLS; aggregati imposti da viste e ruolo DB; l'audit fail-closed porta solo identificativi e hash di prompt, modello e `config_version`.
- DA-E2-10 (a): cache in-process. DA-E2-11 (a): cancellazione delle versioni solo dal ruolo di retention di F6, con audit.
- DA-E3-11 (a): CI su GitHub finché i dati sono sintetici e i segreti sono di un progetto di test separato. DA-E3-07 (b): per ora solo report sui casi non bloccanti (default 0 nel catalogo al posto di 90).
- DA-A1-09 (a): il superadmin scrive solo nodi di piattaforma, mai nodi di un'agenzia.
- DA-B1-08 (a): oltre la quota il job attende in coda (attesa massima come variabile). DA-B2-09 (b): chiave di idempotenza scaduta = errore per le scritture.
- Ipotesi di lavoro per l'implementazione di E1 e A1, già raccomandate nei documenti: DA-E1-03 (tracce nello stesso PostgreSQL, partizionato), DA-E1-04 (kind dedicati), DA-E1-07 (tabelle separate dall'audit), DA-A1-02 (il grafo come unica fonte), DA-A1-06 (istanza condivisa con RLS). DA-A1-03 (= DX-03, trasporto eventi) resta aperta: il primo perimetro di A1 non la usa.

**E14. Retention per agenzia e partizioni di E1 (plan-auditor sul catalogo 1.2).** *Raccomandazione:* come scritto in E1 v1.5: una partizione si elimina solo quando tutte le sue righe sono scadute per i rispettivi tenant; negli altri casi cancellazione per riga. Da confermare in F6.

**E15. Data Act e trasferimenti (compliance-auditor sul catalogo 1.2).** *Raccomandazione:* (a) i termini del Data Act art. 25 (periodo transitorio fino a 30 giorni, preavviso massimo di due mesi, alternativa fino a 7 mesi) entrano nel catalogo come vincoli condizionati alla qualificazione del SaaS; (b) costi di passaggio a zero dal 12.1.2027 (art. 29) come invariante condizionata, con la stessa riserva; (c) la verifica di uno strumento di trasferimento ha una data e una scadenza (`transfer.instrument_review_interval_days`, massimo 365 giorni): alla scadenza lo stato diventa non valido, l'opt-in si disattiva e parte un segnale ad A5; (d) `incident.scope_review_interval_days` con massimo 365 giorni e con i criteri dell'art. 3 d.lgs. 138/2024 (individuazione dell'ACN, imprese collegate, dati consolidati).

**E16. Linguaggio del backend, per l'ossatura del repository (DX-04, DA-B2-02, DA-E3-02 aperte).** *Raccomandazione (deduzione del coordinator):* (a) backend tutto in Python (FastAPI, LangGraph, PostgreSQL) in un solo repository, interfaccia in TypeScript più avanti: LangGraph e i job di B1 sono in Python e un solo linguaggio elimina i contratti tra Node e Python (DX-04 diventa Pydantic). Alternativa (b): server Node/TypeScript e orchestratore Python, come gravya-app. Le competenze del team non sono note al coordinator.

## Parte 2. Correzioni senza scelta (applicate dai doc-writer)

- Transazione unica A3 + B2: un solo esito per il record non salvato (`deny` con `record_not_persisted`); la transazione copre ogni esito (allow, deny, require_approval, rate_limited); B2 passa ad A3 tutti i campi richiesti da A3 §4; B2 §5 elenca `a3.record.persist_timeout_ms`.
- Idempotenza di B2: chiave composta da tenant, tool e hash degli argomenti; stessa chiave con argomenti diversi = errore; si conserva solo stato e riferimento redatto; criterio di test con due tenant.
- Vocabolario degli esiti HITL in E1 allineato a C3 (esito di esecuzione, `rejected`, significato di `gravya.decision.id` per C3).
- Il segnale di E1 per un attributo scartato porta solo kind, chiave, motivo e conteggio, mai il valore.
- Feedback del revisore in C3: motivo codificato nell'audit; il testo libero segue `retention.sensitive_payload_days`. `change_note` di E2 con lo stesso controllo dei dati personali dei template.
- Dati dei clienti delle agenzie in A1 e A3 (`client_ids`, `record_ids`, vincoli): dichiararli, con classe di retention e cancellazione; A1 non dice più "non dati di clienti finali".
- Firma del bundle di A2 verificata da A3 (chiave nella pagina credenziali, catalogo §15); scadenza e revoca dei mandati propagate entro un ritardo massimo misurato.
- B1 dichiara che il runtime con container condivisi non va in produzione con dati reali finché DA-B1-02 è aperta; `outputs_ref` con classe di retention.
- Testi superati: note "non ancora in DECISIONS" su DA-CV-18..23 e fine contratto; rimandi al catalogo (§11 per `eval.*`); `retention.tenant_offboarding_choice` citata in B2 e C1; DA-CV-17 con il testo deciso in B2 e C3.
- Variabili proposte nei documenti da aggiungere al catalogo 1.4: attesa massima in coda di B1, ritardo di propagazione delle policy (E2 sopra), eventuali variabili delle opzioni scelte.
