# Report compliance-auditor — C3 Punto HITL e E1 Tracing distribuito (v1.4)

Esito: **BLOCCA**. Verificati contro PRINCIPI.md e DECISIONS.md (sandbox). Le norme sono citate come riferimento tecnico, non come parere legale.

Causa principale: i due documenti sono alla v1.4 e non recepiscono DX-14…DX-22. Quelle decisioni compaiono in DECISIONS.md come **decise**, mentre i documenti le trattano ancora come "DA RIPORTARE" o non le citano.

## Rilievi bloccanti (violazione di decisioni prese)

1. **DX-17 contraddetta: la retention si ferma su variabile non valida** (GDPR 5(1)(e), PV-01, DX-17, DX-09)
   - C3 §8 AC-12: "se il valore è assente o non leggibile, lo sweeper non chiude e la retention non cancella".
   - C3 §7: "se non riesce a leggerle, non cancella (fail-closed DX-13)".
   - E1 §5: "il job di retention non cancella nulla su un valore non valido". E1 §8 criterio 8 dice lo stesso.
   - DX-17 stabilisce che le azioni si bloccano, ma le cancellazioni programmate usano l'ultimo valore valido versionato, "così i dati non restano oltre la scadenza nota", e parte un segnale ad A5.
   - Con i documenti attuali i dati (argomenti, tracce) restano oltre la scadenza se il registro è guasto. E1 §5 è anche incoerente al suo interno: "si mantiene l'ultimo valore valido" e poi "non cancella nulla".
   - Proposta: riscrivere AC-12 e il criterio 8. Valore non leggibile o non valido: si usa l'ultimo valore valido versionato e si invia il segnale ad A5. Il blocco vale per le azioni, non per le cancellazioni.
   - Verificato.

2. **DX-15/DX-16 non applicate: durate e TTL senza intervallo protetto, e solo superadmin** (DX-15, DX-16, DX-22, PV-01)
   - C3 §7: "variabili di piattaforma modificabili dal superadmin (DX-13)". C3 §6: TTL "modificabile dal superadmin". C3 Appendice C DA-C3-04: "Resta aperta".
   - E1 §5: "modificabili solo dal superadmin senza rilasci".
   - Nei documenti non c'è alcun intervallo min/max protetto. Un valore fuori intervallo deve essere non valido (DX-16).
   - Manca la possibilità per l'agenzia di scegliere solo dentro l'intervallo (DX-15).
   - Senza un minimo, la retention dei dati di audit o di incidente può scendere sotto quanto serve a NIS2 art. 21/23, e le durate possono salire oltre il minimo necessario.
   - DA-C3-04 in DECISIONS.md §2 è già "Decisa". I valori min/max non esistono e non vanno inventati: vanno chiesti all'utente (DECISIONS §4).
   - Proposta: citare DX-15/DX-16 per ogni durata e per il TTL (`hitl.request_ttl_hours`). Dichiarare min e max "da fornire". Dire che una modifica fuori intervallo è rifiutata.
   - Verificato.

3. **DX-19 non applicata: il superadmin può leggere singole righe e tracce con il solo log** (GDPR art. 28(3)(a), DX-19, DX-18)
   - E1 §5: "solo il superadmin... tramite route dedicata... registrato (chi, quando, tenant, traccia o filtro, motivo)". E1 Appendice C DA-E1-08 lascia "DA RIPORTARE" il limite agli aggregati.
   - C3 §7 "Accesso cross-tenant": ammesso al superadmin "entro le istruzioni del titolare" con log. Non c'è il default aggregato e senza identificativi.
   - C3 AC-13 verifica solo il log, non la limitazione ad aggregati.
   - DX-19 dice che di default il superadmin vede solo aggregati senza identificativi. La singola traccia (e quindi riga HITL con `arguments`/`context`) è ammessa solo su richiesta dell'agenzia o per un incidente.
   - Le righe HITL in chiaro, con destinatari e contenuti CRM, sarebbero leggibili dal superadmin con una semplice motivazione libera.
   - Proposta: aggiungere la condizione "richiesta dell'agenzia o incidente aperto in A5", con riferimento nel log. Aggiungere un criterio di test. Per C3, escludere `arguments` e `context` dalla vista del superadmin.
   - Verificato.

4. **DX-18 e DX-20 non recepite** (DX-18, DX-20, NIS2 art. 21(2)(j))
   - E1 §4.1 e §5 definiscono schema e retention del log degli accessi come cosa propria. DX-18 dice che il log appartiene ad A6 con schema unico: E1 lo usa e non lo possiede.
   - Né C3 né E1 citano la MFA obbligatoria per superadmin e admin agenzia. Gli admin agenzia sono quelli che approvano in C3.
   - Proposta: E1 e C3 consumano il log A6 e dichiarano la dipendenza da MFA (DX-20).
   - Verificato.

## Rilievi da riportare

5. **Etichetta art. 50 e tracciabilità dell'approvazione** (AI Act art. 50(2), DECISIONS §6)
   - C3 §7 dice che l'etichetta "resta **aperto**" e C3 §4.1 non contiene `ai_generated`, `model`, `prompt_ref`.
   - DECISIONS §6 l'ha decisa (2026-11-03): campo obbligatorio nel contratto di output di C1, che C3 mostra all'approvatore.
   - C3 §4.1/§5 non fa vedere all'approvatore che il contenuto è generato dall'AI, quindi l'approvatore non può verificare la disclosure verso terzi.
   - Proposta: aggiungere i campi al payload `approval_required` e un criterio di accettazione. Eliminare la dicitura "aperto".
   - Verificato.

6. **Argomenti duplicati nel checkpoint non coperti da retention e minimizzazione** (GDPR 5(1)(c) e (e), DA-E1-02, DA-C3-06)
   - C3 §3 e §6 dicono che `interrupt()` richiede lo stato persistito. §7 conserva il checkpoint del run in pausa "30 giorni dopo la chiusura".
   - Il payload di interrupt (§4.1) contiene `preview` e `structured_data`, cioè contenuti. Lo stato LangGraph di norma contiene anche i messaggi LLM.
   - AC-11 cancella `arguments` e `context` dopo 30 giorni dalla decisione. Non è detto che cancelli la copia nel checkpoint. Il 30 giorni parte dalla chiusura del run, che può essere più tardi.
   - DA-E1-02 dice "mai registrati" per i contenuti di prompt e risposta: un checkpoint con messaggi li registrerebbe in produzione.
   - Proposta: dichiarare cosa entra nel checkpoint e la durata effettiva delle copie. Considerare l'inserimento nel checkpoint solo di riferimenti e hash. Estendere AC-11 al checkpoint. Chiedere all'utente se il checkpoint con contenuti è accettato come eccezione a DA-E1-02.
   - Dedotto.

7. **Tracciabilità AI dopo 90 giorni** (PV-01, osservabilità AI; AI Act art. 12 come buona pratica)
   - C3 §7 e E1 §5 collegano decisione, run e prompt "tramite gli identificativi E1".
   - Le tracce durano 90 giorni, mentre decisioni e audit durano 12 mesi (DECISIONS §5).
   - E1 §5/§7 è fail-open: un segmento perso lascia l'evento di audit A5 con `trace_id` che non esiste.
   - Dopo 90 giorni, o con un segmento perso, una decisione HITL o un'azione di tool non è più attribuibile a prompt, versione e modello.
   - Proposta: l'audit A5 o il record di decisione deve portare in proprio `prompt key/version/hash`, `model`, `config_version`. Questa è una scelta da riportare, perché cambia lo schema di A5.
   - Dedotto.

8. **Cancellazione per interessato non realizzabile** (GDPR art. 17 e 25)
   - E1 §6: "i segmenti non contengono dati personali in chiaro, si agisce sugli identificativi pseudonimi". E1 §7 propone "append-only, proposta" e la cancellazione "via drop di partizione".
   - C3 §4.3 conserva `decided_by_user_id` in chiaro e `feedback` per 12 mesi. C3 §7 rimanda a una proposta di pseudonimizzazione "da verificare".
   - Un pseudonimo che si può ricondurre a una persona resta un dato personale. L'append-only e il drop di partizione non permettono di cancellare o pseudonimizzare una singola persona.
   - Manca la gestione della chiave o della mappa di pseudonimizzazione.
   - Il campo libero `feedback` può contenere dati personali: non c'è minimizzazione né limite.
   - Proposta: definire la mappa pseudonimo→utente separata e cancellabile (oppure un pseudonimo per tenant). Definire il comportamento dell'append-only sul diritto di cancellazione. Vincolare o redigere `feedback`.
   - Vale la riserva di DECISIONS §5 sul conflitto tra cancellazione e audit di 12 mesi. Interpretazione da confermare con parere legale.
   - Verificato per l'assenza della procedura, dedotto per l'effetto giuridico.

9. **Retention per partizione mensile contro durate variabili** (GDPR 5(1)(e), DX-09, DX-15)
   - E1 §4.1: "partizionamento per mese... `DROP PARTITION`".
   - Con 90 giorni la partizione contiene fino a circa 30 giorni oltre la scadenza. Se la durata cambia, o con override per tenant/classe previsti da DX-09, il drop di partizione non permette durate diverse per tenant.
   - L'export JSONL verso E3 (§5) e i backup (§7, "backup secondo la policy generale") non rientrano in alcuna classe di retention di DECISIONS §5. Possono restare oltre la scadenza.
   - Proposta: dichiarare la granularità effettiva, ad esempio partizioni settimanali o cancellazione per riga oltre il drop. Aggiungere export e backup alle classi di F6.
   - Dedotto.

10. **Isolamento tenant solo applicativo sul percorso E3 e superadmin** (NIS2 art. 21(2)(i), PV-01)
    - E1 §5 Esportazione verso E3: "con il filtro tenant applicato". È un filtro applicativo, senza RLS dichiarata.
    - E1 §4.1 e §7 dicono "Row-Level Security" ma non FORCE, a differenza di C3. E1 Appendice A cita per il sistema precedente "bypass RLS" per il superadmin.
    - Il ruolo DB con cui la route del superadmin legge cross-tenant non è definito.
    - Proposta: RLS FORCE anche per E1, un ruolo DB dedicato e limitato per la route superadmin, e vista o export per tenant con RLS.
    - Verificato per il testo, dedotto per l'effetto.

11. **HITL aggirabile tramite la policy di approvazione** (AI Act art. 14 come buona pratica, PV-01)
    - C3 §5: "Risolvi la policy di approvazione: task → cliente → azienda → default `true`". C3 §6 passo 1: "la policy risolta restituisce `approvalRequired=true`".
    - C3 AC-1 copre le scritture `REQUIRES_HITL`. Se la policy dell'azienda può restituire `false` per una scrittura irreversibile (in particolare `MONEY_WRITE`), l'HITL viene aggirato con una configurazione e senza traccia.
    - Non è detto chi può impostare `false` né con quale audit. DX-22 vuole la configurazione in UI, ma con versionamento e MFA.
    - Proposta: dichiarare che `MONEY_WRITE` e invii a terzi non possono scendere sotto "approvazione richiesta". Ogni cambio del livello è versionato e auditato. Chiedere all'utente se ammettere un'autonomia graduata.
    - Dedotto.

12. **DX-22: catalogo e valori fissi nei documenti** (DX-22, PV-01)
    - Nessuno dei due documenti rimanda al catalogo delle variabili di A6 o alla pagina UI per categoria.
    - Variabili con nome: solo `hitl.request_ttl_hours` e `hitl.resume_latency_p95_ms`. Le durate di retention di C3 e di E1, la soglia di overhead 5 ms, il buffer e la soglia di perdita non hanno nome né categoria.
    - Parametri di sicurezza nel testo come fissi: whitelist di attributi per `kind` "versionata" (E1 §11), nome dell'header `x-gravya-trace-id`, granularità mensile delle partizioni, "100% di fermate" e altre soglie di test.
    - Le soglie per i test possono restare nei test. Le soglie di sicurezza e conformità (whitelist, perdita, TTL) no.
    - E1 §5 dice "fail-closed... accesso negato" come proposta, ma non dice quale variabile governa i motivi del log.
    - Proposta: tabella delle variabili di C3 e di E1 con nome, categoria della pagina UI, default, min/max, chi può modificare. Decidere se la whitelist di attributi è una variabile (protetta, versionata) o una costante di conformità motivata.
    - Verificato per l'assenza del catalogo, dedotto per le singole costanti.

13. **Segnali verso A5 non verificati** (NIS2 art. 23, DX-10)
    - C3 §7: "Un'esecuzione senza approvazione o una decisione forgiata è un incidente: C3 invia il segnale ad A5". Nessun criterio di accettazione nei §8/§10 lo verifica. Non c'è il formato del segnale. A5 è in ondata 2, senza un ricevitore in ondata 1.
    - E1 §7: "il formato del segnale va concordato con A5".
    - E1 non menziona un segnale per il valore non valido di una variabile (DX-17).
    - Proposta: aggiungere criteri di test per i segnali e un ricevitore minimo in ondata 1, come per la tabella di audit minima di DECISIONS §6.
    - Verificato.

14. **NIS2 art. 21(2)(d),(h): misure generiche** (NIS2 art. 21)
    - E1 §7: "cifratura a riposo e in transito ereditata dal DB". C3 non menziona la cifratura dei payload in `arguments`.
    - Nessun cenno a segreti (la chiave HMAC del resume, §5) né a supply chain: LangGraph, `langgraph-checkpoint-postgres`, helper Node e Python.
    - Proposta: cifratura dei payload sensibili, gestione del segreto HMAC nell'archivio cifrato delle credenziali (DX-22), e voce sulla supply chain delle dipendenze.
    - Dedotto.

15. **LLM: giurisdizione del provider non tracciata** (GDPR capo V, DA-B2-07)
    - E1 §4.2: segmento `llm` ha `gen_ai.provider.name` ma non regione o giurisdizione. Il segmento `tool` ha `gravya.tool.destination`.
    - Non è possibile ricostruire a posteriori se una chiamata LLM è uscita dall'UE.
    - Proposta: aggiungere un attributo di giurisdizione e regione, e dichiarare quale regola impedisce un provider extra-UE senza opt-in.
    - Dedotto.

## Minori

- C3 §4.3: l'hash degli argomenti, se non salato, per email o importi può essere invertito: resta dato pseudonimo. Specificare il sale per tenant. Dedotto.
- C3 AC-8: l'approvazione end-to-end su staging deve usare dati sintetici (DA-E3-08). Non è detto. Verificato.
- E1 §4.2: `name` e `sorgente` dei segmenti non sono vincolati: possono contenere testo libero o titoli di documenti. Verificato.
- E1 §8: numerazione dei criteri disordinata (il 9 viene dopo l'11). C3 e E1 chiamano ancora "da riportare" DX-14, che è decisa (A6). Verificato.
- C3 §6: la scadenza dichiara "TTL... modificabile dal superadmin" mentre DX-15 prevede anche la scelta dell'agenzia dentro l'intervallo. Rientra nel rilievo 2.

## Controllato

- Tutti i riferimenti a PV-01, PV-02, PV-03 e DX-01…DX-22 e le DA citate, in DECISIONS.md.
- Nessun SDK OTel in C3 e E1: ammesso solo il vocabolario (PV-02, DA-E1-05). Conforme.
- Contenuti mai in tracce: conforme per E1 §4.3 e C3 AC-9, salvo il rilievo 6.
- Extra-UE: C3 e E1 rimandano a DA-B2-07 e a PostgreSQL self-hosted in UE. Conforme, salvo il rilievo 15.
- Fail-closed audit e decisione (DA-B2-04, DA-A3-07): presente in C3 e E1. Conforme.
- Il superadmin non decide richieste HITL: conforme. Fail-open limitato alle tracce: coerente.
- Non verificato: i documenti altrove nel set (A1, A3, A5, A6, B2, F6), la analisi in `gravya-app/docs/compliance/` e kloudify (non presenti nella sandbox), la memoria condivisa.

## Collaudo

- Modello: ritengo di essere un modello Claude (dedotto, non verificato: non ho modo di interrogare la mia identità esatta).
- Strumenti disponibili: send_to_parent, bash, read, glob, grep, risposta_compliance_auditor.
- Strumento risposta_*: sì, `risposta_compliance_auditor`; lo uso per consegnare la risposta.
- File letti: `/tmp/test-compliance-auditor/docs/C3-punto-hitl.md`, `E1-tracing-distribuito.md` (parte iniziale via cat, il resto con `cat -n`), `DECISIONS.md`, `PRINCIPI.md`. Elencati con `find` i nomi degli altri file di docs/, non letti. Non ho letto `/workspace/gravya-app-v2`. Ho scritto solo in `/tmp/test-compliance-auditor/report`.
