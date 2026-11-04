# Compliance-auditor — C3 (Punto HITL) ed E1 (Tracing distribuito), v1.4, ondata 1
Data: 2026-11-04. Esito: **BLOCCA**. Registro norme usato: docs/norme-di-riferimento.md v1.0.

## Rilievi bloccanti (violano una decisione già presa)
1. **DX-17 violata (E1 §5, E1 criterio 8, C3 §6/§7, C3 AC-12).** Con valore non valido o non leggibile i documenti scrivono «il job di retention non cancella nulla» (E1) e «la retention non cancella» (C3). DX-17 dice l'opposto: le cancellazioni programmate usano l'ultimo valore valido versionato. Così i dati restano oltre la scadenza (GDPR art. 5(1)(e)). C3 aggiunge che lo sweeper TTL «non chiude»: le richieste scadute restano approvabili. E1 non prevede il segnale ad A5 per variabile non valida, richiesto da DX-17.
2. **DX-19, DX-18, DA-E1-08 non applicate (E1 §5, §4.1(3), App. C DA-E1-08, §9 fase 0; C3 §7 «Accesso cross-tenant», AC-13).** La route superadmin ha il solo log di accesso. Manca il default aggregato senza identificativi. E1 dice ancora «DA RIPORTARE». Il log è descritto come classe di E1, ma DX-18 lo assegna ad A6. Per C3 il superadmin può accedere a righe con `arguments` e `context`, cioè dati personali in chiaro. Proposta: accesso di default solo tramite viste aggregate senza identificativi, imposte dall'architettura (view o ruolo DB dedicato) e non da un filtro applicativo. La singola traccia o riga solo su richiesta dell'agenzia o per un incidente, con log di A6 e fail-closed.
3. **DX-21 non applicata (E1 §4.2, riga `decision`).** `config_version` non è nella whitelist, quindi una decisione di policy o HITL non è attribuibile alla versione di configurazione in vigore (osservabilità AI, PV-01).
4. **DECISIONS §6 (etichetta art. 50) non applicata in C3 (§4.1, §7 «AI Act»).** C3 scrive che l'etichetta «resta **aperto**». La decisione è presa: `ai_generated` con `model` e `prompt_ref`, e C3 lo mostra all'approvatore. Il payload `approval_required` non ha il campo. L'approvatore può quindi autorizzare l'invio a terzi di contenuto AI senza vederne l'origine. AI Act art. 50 è ✔ nel registro.

## Da riportare
5. **Intervallo min/max protetto non dichiarato (DX-15, DX-16, DA-C3-04; C3 §6, §7, App. C; E1 §4.1, §5, §7).** Le durate e il TTL sono «modificabili dal superadmin» senza intervallo né test di valore fuori intervallo. L'App. C di C3 dice che DA-C3-04 «resta aperta», ma è decisa (1–168 h, default 24 h). Il catalogo `docs/catalogo-variabili.md` (DX-22) non è citato e i nomi (`hitl.request_ttl_hours` ecc.) sono «proposte». Manca la classificazione «vincolo normativo». Un valore troppo basso cancella audit o tracce prima del dovuto (NIS2 art. 21/23, solo dedotto).
6. **Pseudonimi, hash e cancellazione (GDPR artt. 4(5), 17, 25, 32; E1 §6 «Richiesta di cancellazione», §7 NIS2 «append-only»; C3 §4.3 e AC-5).**
   - L'identificativo del revisore è «pseudonimo» e le tracce sono append-only. Non è definito chi tiene la mappa pseudonimo→persona né come si cancella. E1 App. B ammette «Non verificato che basti».
   - `args_hash` è un hash semplice di argomenti a bassa entropia (email, testo breve): è reversibile per tentativi e resta nell'audit 12 mesi dopo la cancellazione degli argomenti, quindi resta dato personale. Proposta: HMAC con chiave per tenant, la cui distruzione rende l'hash non più riconducibile all'argomento. Il confronto di AC-5 resta possibile.
7. **Partizioni mensili condivise tra tenant (E1 §4.1).** Si cancella con `DROP PARTITION`, ma la cancellazione di un singolo tenant a fine contratto entro 30 giorni (art. 28(3)(g)) e la cancellazione per interessato richiedono cancellazioni riga per riga, non descritte. Il rischio è doppio: tempi non rispettati e incoerenza con il Data Act art. 25/29 (§9 punto 4 del registro).
8. **Copie dei dati personali fuori dalla retention di C3 (C3 §4.1, §4.3, §6, §7).**
   - `preview` e `structured_data` del payload `interrupt` e `input_data` della ripresa finiscono nel checkpoint (B5), con regole diverse da quelle della riga di scrittura parcheggiata: si cancellano 30 giorni dopo la *chiusura del run*, non dopo la decisione.
   - Alla scadenza TTL la richiesta diventa `cancelled`, ma non è detto che il run si chiuda. Se non si chiude, il checkpoint con dati personali non scade mai.
   - `feedback` è testo libero conservato 12 mesi.
   Proposta: chiudere forzatamente il run alla scadenza e includere tutte le copie nella classe «payload sensibili temporanei».
9. **Esiti post-esecuzione (C3 §6; DECISIONS §6).** C3 tratta solo il fallimento dell'audit *prima* dell'esecuzione. Manca il caso deciso: audit dell'esito non salvato dopo l'esecuzione, con segnale ad A5 e coda di recupero. Se l'esito non arriva, lo sweeper scrive `error/reaped` per un'azione in realtà eseguita (audit falsato). Mancano anche i segnali ad A5 per claim senza esito, tentativi di doppio resume e decisione forgiata: «C3 invia il segnale» non ha un criterio di accettazione.
10. **HITL aggirabile / DX-05 aperta (C3 §3, §5, §6 punto 5, AC-1).**
    - Il parcheggio, il claim e l'esito sono chiamati dal «run» (esecutore). Il replay del run «emette il token monouso, chiamata unica», mentre §3 dice che esegue B2. Non si garantisce che l'esecuzione passi solo da B2.
    - L'esito è autodichiarato dal run, quindi falsificabile.
    - Non è definito chi può decidere (ruolo, separazione tra chi richiede e chi approva, MFA).
    - AC-1 è un test campionario («0 su 100 run»); serve anche un vincolo strutturale: B2 rifiuta un tool `REQUIRES_HITL` senza un token firmato e collegato all'hash.
11. **DX-20 (MFA) assente (C3 §7 NIS2, E1 §7 NIS2).** Nessun documento cita l'MFA per superadmin e admin agenzia, che sono chi decide le richieste HITL e legge le tracce (NIS2 art. 21(2)(j) ○ nel registro). Il segreto HMAC del resume (`kloud-resume.ts`) non ha un percorso di gestione e rotazione (DX-22(b), NIS2 21(2)(h)).
12. **Attribuzione di prompt, versione e modello affidata a un buffer fail-open (E1 §5, §7; C3 §7 «Cosa rende osservabile»; C3 AC-9).** Un'azione irreversibile può essere eseguita e auditata (fail-closed) mentre il segmento `llm` o `decision` è andato perso. Il `trace_id` nell'audit A5 punterebbe a nulla. In più AC-9 di C3 pretende un record per *ogni* transizione, in contrasto con il fail-open. Proposta: l'audit fail-closed di B2/A5 porta `prompt key/version/hash`, modello e `config_version` (solo identificativi e hash, mai contenuti). In alternativa, i segmenti `decision` e `hitl` sono fail-closed.
13. **Finalità «qualità» dei metadati e export verso E3 (E1 §7 GDPR, §5 «Esportazione verso E3»; GDPR art. 28(3)(a), 28(10)).** E1 elenca come finalità «sicurezza, qualità, fatturazione» e non verifica che il contratto le copra. L'export JSONL delle tracce verso E3, insieme alla promozione dei prompt (DA-E2-07), è un riuso dei dati delle agenzie per il miglioramento del prodotto. Se la finalità è di Gravya, Gravya rischia il ruolo di titolare (EDPB 07/2020, registro N-GDPR). L'export non ha classe di retention: i file JSONL sfuggono ai 90 giorni. E1 non limita l'export a `root_kind=eval` (dati sintetici, DA-E3-08).
14. **Whitelist solo sulle chiavi (E1 §4.1, §4.2, §6).** Non è prevista una validazione dei valori: tipo, enum, pattern dell'hash, lunghezza. Restano a testo libero `name`, `retrieval.sorgente`, i codici di errore e `gen_ai.tool.call.id`. Questi campi possono portare contenuto o dati personali in produzione (DA-E1-02). Un tentativo di scrittura di contenuto viene solo contato in produzione, senza segnale ad A5.
15. **RLS e scrittura asincrona (E1 §5, §7; E1 App. A su `superadmin-observability.ts`).** Il writer bufferizzato che scrive per più tenant richiede un ruolo con bypass di RLS oppure un GUC per riga. Il meccanismo non è dichiarato, come non lo è quello della route superadmin (in gravya-app era un bypass di RLS). Serve `WITH CHECK` e un test di scrittura con tenant errato. Rischio di isolamento solo applicativo (dedotto).
16. **Trasferimenti e supply chain (E1 §4.2 `llm`; C3 §5 e §7).**
    - Il segmento `llm` registra il provider ma non giurisdizione o regione di elaborazione, quindi non si può provare l'assenza di trasferimenti extra-UE impliciti verso provider LLM.
    - C3 non dichiara che la card di approvazione mostra all'approvatore destinazione e giurisdizione del tool (DA-B2-07).
    - E1 §7 dichiara «cifratura a riposo e in transito ereditata dal DB» e «backup secondo la policy generale», ma nessun documento di v2 definisce quella policy né la cifratura, e i backup non rientrano in DX-09.
17. **Art. 50(2) sul testo (DECISIONS §4 «Da riportare», registro §9 punto 1).** La marcatura leggibile da macchina del testo sintetico non è coperta da C3 (payload `preview`) né da E1. E1 §7 afferma che E1 «registra a supporto della marcatura», ma la traccia è fail-open e a 90 giorni: non può essere la prova di marcatura. È già in DECISIONS §4 come punto aperto, qui lo si richiama soltanto.

## Minori
18. DX-14 (A6) è decisa ma in C3 §3, §11, App. B e in E1 §3, §11, §12, App. B è ancora «proposta, DA RIPORTARE». DA-C3-04, DA-C3-05 e DA-E1-08 sono descritte come aperte pur essendo decise.
19. C3 AC-8 (staging) e le prove di integrazione di C3 §10 non dichiarano dati sintetici (DA-E3-08). E1 §10 lo dichiara.
20. C3 §11 ammette il default «approvazione richiesta» come requisito, ma `KLOUD_APPROVAL_DEFAULT = true` ripreso da gravya-app va configurabile dalla UI (DX-22); soglie e parametri di C3 e E1 sono «proposte» non catalogate.
21. E1 §8: numerazione dei criteri fuori ordine (9 dopo 11).

## Controllato e senza rilievo
- Niente OTel come SDK o export in E1 e C3; il vocabolario GenAI e `traceparent` sono usati nei limiti di DA-E1-05 (PV-02).
- Contenuti e argomenti mai nelle tracce, solo hash (DA-E1-02, DA-C3-06). Nessun servizio extra-UE o SaaS di tracing o eval; PostgreSQL self-hosted in UE.
- Fail-closed su audit e decisione prima dell'esecuzione (DA-B2-04, DA-A3-07). Fail-open limitato alle tracce con distinzione esplicita. Notifica NIS2 delegata ad A5 (DX-10).
- RLS FORCE e `company_id` su entrambe le tabelle E1 e sulla tabella HITL, con test di isolamento (AC-7, criterio 3).
- Durate di default coerenti con DECISIONS §5. Il TTL di C3 è la variabile `hitl.request_ttl_hours`, coerente con DA-C3-04.
- Idempotenza, claim e token monouso; assenza di checkpointer = errore (AC-2); superadmin che non decide le richieste HITL.
- Le analisi di riferimento (gravya-app NIS2 `measures.md`, kloudify `controlli-e-conformita.md`) sono state lette e confrontate. Non ho letto per intero i file in docs/compliance/gdpr e ai-act: solo grep.

## Da aggiungere al registro (verificare con il regulatory-researcher)
- GDPR art. 4(5) (pseudonimizzazione) e considerando 26: sono ○ o assenti; richiesti dai rilievi 6 e 8.
- GDPR art. 5(1)(c), (e), art. 17 (con 17(3)), art. 25, art. 32, art. 28(10): sono ○. Il rilievo 13 dipende dal testo dell'art. 28(10).
- Linee guida EDPB sulla pseudonimizzazione (esistenza e contenuto da accertare) e sulla protezione dei dati fin dalla progettazione (art. 25). Non le ho verificate: da accertare.
- GDPR artt. 44-49 per i provider LLM (la verifica è ◐); decisione di adeguatezza UE-USA se rilevante.
- NIS2 art. 21(2) lettere (d), (h), (i), (j) e art. 23 nel testo: sono ○. d.lgs. 138/2024 artt. 24-25 sulle misure.
- Segnalo, senza proporre una fonte, se esistano obblighi di conservazione o integrità dei log di accesso del responsabile.

## Letture
- C3-punto-hitl.md 1-234 di 234
- E1-tracing-distribuito.md 1-196 di 196 (riga 196 letta quasi interamente)
- PRINCIPI.md 1-15 di 15
- DECISIONS.md 1-172 di 172
- norme-di-riferimento.md 1-489 di 489
- gravya-app-kloudify/docs/visione/controlli-e-conformita.md 1-71 di 71
- gravya-app/docs/compliance/nis2/measures.md 1-80 di 219
- gravya-app/docs/compliance/gdpr/art32-security-of-processing.md solo grep
- gravya-app/docs/compliance/README.md, ai-act/system-register.md: solo elenco (non letti)
- A1-grafo-mandati.md: solo grep ("backup")
