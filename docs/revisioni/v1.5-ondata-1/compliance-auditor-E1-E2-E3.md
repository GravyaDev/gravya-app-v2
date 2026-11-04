# Revisione di conformità: E1, E2, E3 alla v1.5

Revisore: compliance-auditor · Data: 2026-11-04 · Oggetto: docs/E1-tracing-distribuito.md, docs/E2-prompt-registry.md, docs/E3-eval-harness-offline.md (commit 14d2be7) · Norme: registro v1.6 · Catalogo v1.2.

**Esito: RIPORTA.** Nessun BLOCCA: nessuna violazione di una riga decisa, di PV-01 o PV-02. I tre documenti applicano in modo coerente le decisioni (contenuti mai in produzione, solo dati sintetici, nessun SDK OpenTelemetry, accesso del superadmin con log fail-closed, giudice nell'UE, segreti CI separati). I rilievi sono lacune residue. Le DA già segnate «DA RIPORTARE» nei documenti (DA-E1-09, DA-E1-12, DA-E2-09, DA-E2-11, DA-E3-11) non sono riproposte, tranne dove l'estensione del loro perimetro è un problema nuovo (R-03, R-04).

Letture: E1 1-232 di 232; E2 1-228 di 228; E3 1-232 di 232; DECISIONS 1-260 di 260 (letto nella parte sopra e per le righe §4, §7; il resto per grep); PRINCIPI e catalogo v1.2 letti nella sessione precedente (grep solo per i nomi); registro v1.6 letto per intero nella sessione precedente.

## Rilievi

### R-01 · da_riportare · GDPR artt. 4(5), 5(1)(c), 25, 32; considerando 26 (✔): `gravya.prompt.hash` / `content_hash` del testo renderizzato
- **Dove:** E2 §4.3 e §7 («Osservabilità AI»); E1 §4.2 riga `llm`.
- **Testo citato:** E2 §4.3: «`content_hash` è dell'output renderizzato, per correlazione in audit senza testo»; E1 §4.2: `gravya.prompt.key/version/hash` (E2).
- **Problema:** il testo renderizzato contiene i dati dei clienti (variabili). Il suo hash SHA-256 semplice, scritto in tracce e audit, è un derivato di dati personali. Se l'input è breve o a bassa entropia (un nome, un'email) è invertibile per confronto. E1 lo riconosce per `args_hash` (DA-E1-09) ma non per questo hash. E2 usa lo stesso nome `content_hash` anche per l'hash della versione del template (§4.1), quindi non è chiaro quale dei due E1 registri.
- **Proposta:** in E1 e nel segmento `llm` registrare l'hash del solo template (`content_hash` della versione), non del render. Se serve l'hash del render, includerlo nel perimetro di DA-E1-09 (HMAC con chiave per tenant). Usare due nomi distinti.
- **Verifica:** dedotto.

### R-02 · da_riportare · GDPR art. 28(3)(a) e 28(10) ✔; DA-E1-02; DA-E2-07: `learning_proposal` senza fonte dichiarata
- **Dove:** E2 §4.1 (`source`: `learning_proposal`), App. A (`learning-proposal-apply.ts`), DA-E2-07.
- **Testo citato:** «`source` (`seed`/`human`/`learning_proposal`/`rollback`)»; DA-E2-07: «versioni proposte da AI, ammesse come candidate».
- **Problema:** E2 non dice da quali dati nascono le proposte. In gravya-app nascevano dai fallimenti reali. Se in v2 nascono da conversazioni o da contenuti dei tenant, sono un uso dei dati dell'agenzia per migliorare i prompt (anche globali, con effetto su altri tenant), cioè fuori dall'istruzione del titolare. E1 §7 lo segnala per i metadati («addestramento… non coperto senza istruzione, rischio art. 28(10)»), E2 no. DA-E1-02 vieta di catturare contenuti, quindi la fonte non può essere la traccia.
- **Proposta:** E2 dichiari che una `learning_proposal` può partire solo da dati sintetici, da metadati aggregati o da una istruzione scritta del titolare nel DPA, e mai attraversare tenant. Se serve altro, decisione dell'utente.
- **Verifica:** dedotto.

### R-03 · da_riportare · GDPR art. 28(3)(a), DX-13, DX-19: la scrittura del superadmin sui prompt dei tenant non è nel perimetro di DA-E2-09
- **Dove:** E2 §6 («Superadmin»), §8 criterio 12, App. C DA-E2-09.
- **Testo citato:** «Su un prompt di un tenant opera solo entro le istruzioni del titolare … di default vede solo metadati aggregati … il testo del template solo su richiesta dell'agenzia o per un incidente»; criterio 12: «una lettura o un rollback del superadmin su un prompt di tenant produce 1 riga nel log».
- **Problema:** DA-E2-09 è formulata per la sola lettura. Il criterio 12 dà per ammesso un rollback del superadmin su un tenant, quindi una modifica della configurazione del trattamento dell'agenzia (il suo prompt) senza condizione. DX-13 ammette l'accesso ai dati dei tenant solo entro le istruzioni del titolare, e per una scrittura vale a maggior ragione. Il log lo rende tracciabile, non lecito.
- **Proposta:** estendere DA-E2-09 a attivazione e rollback: solo su richiesta dell'agenzia o per un incidente, con riferimento alla richiesta o al caso. Il ripristino del seed vale per i prompt globali.
- **Verifica:** dedotto.

### R-04 · da_riportare · GDPR art. 32(1)(a), (c); NIS2 (Reg. 2024/2690 all. 9, 4.2): nessuna policy di cifratura e backup per le tabelle di E1 ed E2
- **Dove:** E1 §7 («Cifratura e backup: nessuna policy di v2 è definita») e App. B; E2 §7 (assente).
- **Testo citato:** E1: «Cifratura e backup: nessuna policy di v2 è definita (App. B)».
- **Problema:** tracce, prompt dei tenant e pseudonimi stanno in PostgreSQL senza un documento che assegni cifratura a riposo e in transito, gestione delle chiavi e backup. L'art. 32(1) chiede misure adeguate al rischio («as appropriate» per cifratura e pseudonimizzazione e per il ripristino); il Reg. 2024/2690 all. 9 e 4.2 lo chiede per il progetto «NIS2 ready». Il registro dice che le scelte sono di Gravya, da documentare. In DECISIONS §4 non c'è una riga su questo, e E2 non lo dichiara nemmeno come non verificato.
- **Proposta:** assegnare a un sottoprodotto (A6, F1 o F6) la policy di cifratura e backup; in E2 aggiungere la voce. Registrare la lacuna in DECISIONS §4.
- **Verifica:** verificato (il testo di E1; registro per le misure), dedotto che manchi un titolare.

### R-05 · da_riportare · DA-E3-08, GDPR art. 5(1)(c), 44-46: `synthetic: true` è un'etichetta, non un controllo
- **Dove:** E3 §4.1 (`synthetic`), AC11, §5 «Promozione di un fallimento», rischi.
- **Testo citato:** «`synthetic` | bool, sempre `true` | invariante: il validatore rifiuta casi senza questo campo»; AC11: «il validatore rifiuta un caso senza `synthetic: true`»; «input riscritto in forma sintetica e rivisto in PR».
- **Problema:** il validatore verifica che il campo esista, non che i dati lo siano. Un caso promosso da produzione, riscritto da una persona, può contenere un dato reale e finire nel repository (e su GitHub, fornitore USA) e nei log della CI, per tutta la durata del servizio (artefatto di configurazione). Né E3 né E2 hanno un controllo automatico. E2 invece ha un controllo sui pattern email e telefono.
- **Proposta:** il validatore di E3 applichi lo stesso controllo dei dati personali di E2 (pattern base, in blocco) e la revisione in PR abbia una checklist; il dichiarare i limiti del controllo come in E2. La traccia di produzione non ha contenuto (DA-E1-02): E3 dica da dove viene l'input da riscrivere.
- **Verifica:** dedotto.

### R-06 · minore · DX-22; catalogo v1.2: nome di variabile non presente
- **Dove:** E1 §4.2, §5, §7 (`e1.attributes.max_value_bytes`).
- **Testo citato:** «la lunghezza massima di un valore è `e1.attributes.max_value_bytes`»; E1 App. B: «proposte da validare nel catalogo».
- **Problema:** la variabile non è nel catalogo v1.2 (ci sono `e1.write_buffer_size`, `e1.partition_interval_months`, `e1.overhead_p95_ms`). Un valore fisso nel codice sarebbe un hardcoded (DX-22). È il limite che impedisce al testo libero di entrare nei valori.
- **Proposta:** il coordinator la aggiunga al catalogo 1.3 (intervallo richiesto, regola 11, perché limita i contenuti). Gli altri nomi delle tre pagine coincidono col catalogo.
- **Verifica:** verificato.

### R-07 · minore · GDPR art. 5(1)(c), DA-E1-02: il segnale ad A5 per un attributo scartato non deve portare il valore
- **Dove:** E1 §5 («Segnali ad A5»), §6 «Contenuti o valori non conformi».
- **Testo citato:** «in produzione l'attributo è scartato, contato e segnalato ad A5».
- **Problema:** non è detto cosa contiene il segnale. Se riporta chiave e valore, un contenuto di prompt scartato dalla traccia finisce nella tabella di audit (conservata sempre, C2, durata non fissata). Contro DA-E1-02.
- **Proposta:** il segnale contiene solo `kind`, nome della chiave, motivo e conteggio, mai il valore. Aggiungere un test (criterio 4).
- **Verifica:** dedotto.

### R-08 · minore · AI Act art. 50(1), (2) ✔; catalogo §18: i testi di E2 sembrano affidare l'informativa al preambolo del prompt
- **Dove:** E2 §7 («AI Act»), App. C DA-E2-03, rischi.
- **Testo citato:** «sono invarianti … stanno nel codice con il preambolo fisso e il blocco anti-invenzione (DA-E2-03)»; DA-E2-03: «preambolo fisso (anti-invenzione, avvisi art. 50, informativa art. 50(1)) nel codice».
- **Problema:** un avviso che il modello deve scrivere perché è nel preambolo del prompt non è una garanzia: il modello può ometterlo o un contenuto può essere troncato. L'etichetta e la marcatura (C1 `ai_generated`, D1-D4) sono applicate dal sistema; il preambolo è solo un aiuto. E2 non lo distingue. DA-E2-03 è ancora aperta (raccomandazione (b)): se l'utente scegliesse (a) o (c), l'avviso potrebbe finire in un template modificabile.
- **Proposta:** E2 dica che i controlli sono applicati dal codice di C1 e dai connettori e verificati da E3 (AC17), che il preambolo non li sostituisce, e che DA-E2-03 (b) è condizione dell'invariante.
- **Verifica:** dedotto.

### R-09 · minore · GDPR art. 5(1)(c), 17: `change_note` in tabella immutabile
- **Dove:** E2 §4.1 (`change_note`, `prompt_versions` immutabile), §7, App. B.
- **Testo citato:** «`change_note` è testo libero e non è coperto» (App. B).
- **Problema:** il campo è dichiarato non coperto dal controllo, ma sta in una riga che nessuno può modificare né cancellare, con retention «durata del servizio». Un dato personale scritto lì resta fino a DA-E2-11 (non decisa).
- **Proposta:** `change_note` passa lo stesso controllo dei dati personali del template (in blocco) e ha una lunghezza massima; oppure vocabolario chiuso.
- **Verifica:** dedotto.

## Controllato, senza rilievi

- **PV-02:** E1, E2, E3 senza SDK, OTLP, collector o export OpenTelemetry. Solo vocabolario `gen_ai.*` e formato `traceparent` (DA-E1-05); LangSmith escluso; nessuna piattaforma SaaS di eval o tracing (DA-E3-09, DA-C1-05).
- **Contenuti in produzione (DA-E1-02):** E1 ha una whitelist di chiavi e valori, argomenti dei tool solo come hash, test con PII (criteri 4 e 11); contenuti vietati negli audit e nelle tracce. Risulta coerente con E2 (testi renderizzati non conservati) ed E3 (report minimo, AC13).
- **Isolamento tra tenant:** RLS con `WITH CHECK`, writer senza bypass (DA-E1-10), viste aggregate imposte dal DB (DA-E1-11), test sul ruolo; E2 con RLS e prompt globale in sola lettura; E3 con tenant fixture. Non si tratta di filtri solo applicativi.
- **Accesso del superadmin a E1 (DX-13, DX-18, DX-19, DX-20):** aggregati di default, singola traccia su richiesta o incidente, MFA, TTL `access.superadmin_trace_access_ttl_hours`, log di A6 fail-closed, route non esposta finché A6 non esiste.
- **Pseudonimi come dati personali (considerando 26):** E1 §4.3, E2 §7 ed E3 §7 lo dicono; EDPB 01/2025 citate come bozza; mappa non in E1/E2 (`retention.pseudonym_map_months`, F6); cancellazione per riga e per interessato (E1 criterio 14).
- **Retention (DX-09, DX-12, DX-15..17):** tutte le durate sono citate per nome del catalogo; regola `retention.traces_days` più partizione ≤ massimo (D5); DX-17 e primo avvio (DA-CV-17); evidenze di incidente solo per dati di Gravya (DA-CV-21); backup (DA-CV-22); fine contratto come minimo secondo Data Act art. 25(2) con riserva sul SaaS; nessuna durata propria.
- **Fail-closed (DA-B2-04, DA-A3-07):** E1 distingue le tracce (fail-open, perdita contata e segnalata) dal fail-closed di audit e decisioni; E2 transazione unica con A3 e `prompt_activations`; E3 esce con 2 se E1 non scrive. DA-E1-12 (attribuzione a un'azione irreversibile) è già «da riportare» nel documento.
- **AI Act (DX-11):** art. 50 dal 2.8.2026; artt. 12, 14, 19, 26 solo buona pratica e dal 2.12.2027 per l'alto rischio; E3 AC17 verifica `ai_generated`, informativa 50(1), etichetta non disattivabile; marcatura del testo rinviata a DA-C1-07 senza criteri inventati; il Codice non è citato oltre ciò che il registro verifica.
- **E2, controllo PII dei template:** sempre `block`, nessuna variabile, test sulla superficie di configurazione (criterio 14); limiti del controllo dichiarati.
- **E3 segreti CI (C11, D6):** progetto di test separato, inventario e rotazione con `security.credential_rotation_interval_days`, chiavi di produzione mai in CI (AC15); giudice solo UE con endpoint non UE rifiutati (AC16); guardia `API_ENV` come invariante di deploy (AC7); gate senza eccezioni sui bloccanti e `expected_fail_ref` vietato (AC4).
- **Trasferimenti extra-UE:** nessun dato personale in E3; E1 ed E2 riportano la destinazione dichiarata; DPF citato come limitato all'elenco e impugnato (C-703/25 P); sub-responsabile anche in UE (DA-CV-19).
- **NIS2:** citazioni dei log corrette (Reg. 2024/2690 all. 3.2 e 11, non l'art. 21); Gravya non soggetto oggi; flusso non attivo e segnali sempre conservati; nessun termine fisso nel testo.
- **Marketing:** E1, E2, E3 non inviano verso terzi; rinvio a D1-D4 corretto.
- **Nomi del catalogo:** i nomi usati in E2 ed E3 esistono nel catalogo v1.2. In E1 manca solo `e1.attributes.max_value_bytes` (R-06).

## Da aggiungere al registro

Nessuna norma o articolo nuovo. Restano non verificati nel registro, come già dichiarato nei documenti: la marcatura del testo del Codice art. 50 (E2, E3), l'anonimato dei trace (linee guida EDPB 02/2026), la qualificazione del SaaS come servizio di trattamento dei dati (Data Act).
