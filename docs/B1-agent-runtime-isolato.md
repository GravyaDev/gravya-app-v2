# B1 — Agent runtime isolato

## 1. Identità

| Campo | Valore |
|---|---|
| ID | B1 |
| Nome | Agent runtime isolato |
| Componente padre | B — Runtime Agenti |
| Versione documento | 1.6 |
| Data | 2026-11-04 |
| Ondata | 1 (walking skeleton) |

> Attenzione al nome: in gravya-app-kloudify esiste una decisione chiamata «B1 (organico agenti)», chiusa il 16/10, che non ha niente a che fare con questo sottoprodotto. Riguarda il numero di supervisori.

## 2. Scopo

**Cosa fa.** Esegue ogni job agente in un ambiente effimero creato per quel job. Un job è un solo nodo agente del grafo C1, con il suo ciclo di chiamate ai tool (DECISIONS §6: dentro B1 girano solo i nodi agente). L'ambiente ha un filesystem temporaneo, distrutto alla fine, e una rete default-deny con uscita solo verso B2 ed egress-proxy. È legato a un solo tenant (company_id). Il master plan (§2) chiede isolamento «per design» di compute, non filtri `WHERE company_id = ?`.

**Cosa NON fa.**
- Non esegue il grafo C1: gira nel servizio di orchestrazione, con il checkpointer B5, perché workflow di giorni e attese HITL non stanno in ambienti effimeri (DECISIONS §6).
- Non decide quali tool un agente può usare: A3 (enforcement) e B2 (tool gateway).
- Non conserva stato tra job. Memoria e checkpoint sono di B3, B4, B5.
- Non accede al database: il job parla solo con B2 ed egress-proxy (DA-B1-04).
- Non sostituisce la RLS di Postgres: la affianca.
- Il runtime a container condivisi non va in produzione con dati reali finché DA-B1-02 è aperta: l'ondata 1 non va in produzione.

**Perché esiste.** Un job compromesso, per esempio da prompt injection, non deve condividere processo, `/tmp`, segreti o rete con i job di altre agenzie. La lezione viene da gravya-app, dove i container `agents` e `agents-worker` sono long-lived e condivisi da tutti i tenant (Appendice A): è il difetto da non ripetere (PV-03).

## 3. Contesto e dipendenze

**Dipende da:**
- **A3**: allow/deny prima dell'avvio e prima di ogni azione.
- **B2**: unico canale verso i tool; verifica il `run_token` emesso da B1.
- **E1**: tracce correlate per ogni ciclo di vita del job.
- **C1**: chiamante, un job per nodo agente.
- **E2**: il prompt è risolto da C1, non dal job (E6).
- **A5** (ondata 2): riceve i segnali di incidente; in ondata 1 vanno nella tabella di audit minima (DECISIONS §6).
- **A6** (ondata 2, DX-14): registro versionato delle variabili (DX-13, DX-22), ruoli superadmin e admin agenzia, pagina credenziali, configurazione per tenant con l'opt-in extra-UE. Non esiste in ondata 1: la lettura passa da un'istantanea nel repository (DA-B1-09, E5). Ad A6 vanno anche cifratura a riposo e in transito e gestione delle chiavi (E11).
- **F6** (ondata 2, DX-12): applica la retention DX-09 alle classi di B1, i backup (DA-CV-22) e lo strumento di esportazione dei dati di un tenant (E15).
- **B5** (ondata 2): il checkpoint sta nel servizio di orchestrazione, non in B1.
- **DX-03** (trasporto eventi): aperta. **DX-04** (formato dei contratti): con il backend in Python (E16) `JobSpec` e `JobResult` sono modelli Pydantic. **DX-05** (chi parcheggia la chiamata da approvare): aperta, condiziona lo stato `suspended_hitl`.

**È richiesto da:** C1 (chiama i job), C3 (attese HITL tra nodi), B5, C4 (retry e DLQ), D1–D5 (i tool girano dietro B1), E3 (eval nello stesso runtime), B2 (verifica il token), A3 (valutazione all'avvio), A5 (segnali).

**Assunzioni (non verificate):** piattaforma self-hosted su infrastruttura UE (DA-B1-06, decisa); l'orchestratore non è scelto. Le chiavi dei provider LLM sono per tenant, nella pagina credenziali di agenzia, e non entrano mai nel job: le legge l'egress-proxy (E11).

## 4. Contratti

**Input: `JobSpec`**

| Campo | Tipo | Note |
|---|---|---|
| job_id | UUID | Idempotenza |
| company_id | UUID | Validato come UUID |
| run_id / execution_ticket_id | UUID | Correlazione con le tracce DB-native di E1 |
| agent_id, executor_kind | string | |
| policy_bundle_ref | string, con hash | Da A2/A3 |
| prompt_ref | string | Chiave e versione di E2: serve alla traccia e ad `ai_generated`; formato esatto da E2 (Appendice B) |
| input_ref | string | Oggetto su object storage con il testo renderizzato del prompt (risolto da C1 da E2) e l'input del nodo secondo il data contract di C1 (E6). Segue la classe dei payload sensibili temporanei (`retention.sensitive_payload_days`). Il contenuto non va nelle tracce (DA-E1-02) |
| limits | {wall_s, memory_mb, pids, tool_turns, cost_usd} | Tetti e default sono `b1.job.wall_s_*`, `b1.job.memory_mb_*`, `b1.job.pids_*`, `b1.job.tool_turns_*`, `b1.job.cost_usd_*` (`_default`, `_max`), letti dal registro a ogni submit; il `JobSpec` può solo restringerli. Valori del sistema precedente (300 s, 10 min, $2, 8 giri) sono riferimenti, non default |
| trace_context | string | `trace_id`, `parent_segment_id` nel formato E1; `traceparent` ammesso come formato (DA-E1-05). Nessun SDK né export OTel (PV-02) |

**Token del job (DA-CV-13).** Il campo `tool_grant_ref` della v1.4 è eliminato: non esiste un secondo token. Dopo il via libera di A3, il launcher emette un solo `run_token`, firmato, e lo inietta nel job; B2 lo verifica e ne ricava `agent_id`, `tenant_id`, `run_id` (B2 §4). Scadenza: `b1.run_token.ttl_s`. Il token non è monouso: vale per tutto il run, e B2 lo verifica a ogni chiamata (E7; la voce «token monouso» del catalogo §18 vale solo per l'`approval_token`). La chiave di firma sta nella pagina credenziali di piattaforma e si sostituisce con due chiavi valide in parallelo, con date di attivazione e disattivazione (DA-CV-23; Reg. 2024/2690 all. 9.2(c)). Lo stesso vale per la chiave HMAC dell'egress-proxy.

**Output: `JobResult`.** `status` (`succeeded`, `failed`, `timeout`, `killed`, `suspended_hitl`), `outputs_ref` (URI su object storage, mai payload inline), `usage` (modello, token, costo, durata), `exit_reason`, `ai_generated` (`model`, `prompt_ref`), `config_version` (DX-21). `ai_generated` è nel `JobResult` e dentro ogni oggetto di `outputs_ref` secondo il contratto di output dei nodi agente di C1 (DECISIONS §6); B1 imposta modello e prompt effettivi e non li altera. Una chiamata a un tool di invio verso terzi dal ciclo di tool porta `ai_generated` negli argomenti: senza, B2 la rifiuta (E3).

**Eventi emessi:** `runtime.job.started`, `runtime.job.finished`, `runtime.job.killed`, `runtime.egress.denied`. Schema e attributi `gravya.*` sono quelli di E1 (DX-02, PV-02). Gli eventi non contengono prompt, output o segreti: solo identificativi, esiti, motivi e misure.

**Eventi consumati:** richiesta di job (da C1 o dalla coda) e cancellazione.

## 5. Interfacce

- **Verso C1 e la coda:** `submit(JobSpec) -> job_id`, `cancel(job_id)`, `status(job_id)`. Trasporto: DA-B1-03.
- **Verso l'host:** il «launcher» crea e distrugge gli ambienti; è l'unico processo privilegiato e non è raggiungibile dagli agenti.
- **Dentro l'ambiente:** l'entrypoint riceve il `JobSpec` da stdin o da file in sola lettura ed emette il `JobResult`.
- **Credenziali:** nessun valore nel documento. Chiavi del `run_token` e HMAC dell'egress-proxy: pagina credenziali di piattaforma (superadmin). Chiavi dei provider LLM: pagina credenziali di agenzia (admin agenzia); il superadmin non le inserisce mai per conto dell'agenzia (DA-CV-16). Solo inserimento o sostituzione, mai rilettura in chiaro. Le chiavi dei provider non entrano nel job: le chiamate LLM escono dall'egress-proxy, che aggiunge la chiave, non registra corpi né URL completi e ne risponde con i soli esiti (E11).
- **Nessuna UI propria.** Lo stato è nell'osservabilità di E1.

## 6. Comportamento

**Flusso principale**
1. C1 invia il `JobSpec` per un nodo agente.
2. Il submit legge le variabili dall'interfaccia di lettura (in ondata 1 un'istantanea nel repository, E5). Se non sono leggibili o non valide, il submit fallisce (DX-17) con segnale ad A5.
3. A3 valuta l'avvio. Se il record di decisione non si salva, il job non parte (DA-A3-07).
4. Il launcher verifica le quote `b1.tenant.max_concurrent_jobs` e `b1.host.max_concurrent_jobs`: oltre la quota il job attende in coda, al massimo `b1.queue.max_wait_s`, poi il submit termina con errore esplicito (`exit_reason` `queue_wait_exceeded`, retry di C4; DA-B1-08). Emette il `run_token` e crea l'ambiente: rootfs in sola lettura, `/tmp` tmpfs dedicato, utente non-root, zero capability dopo il setup, rete default-deny con uscita solo verso B2 ed egress-proxy, limiti di CPU, memoria e pids, nessuna chiave di provider LLM.
5. Il job esegue il nodo con il testo e l'input ricevuti; non accede al database (E6). Le chiamate ai tool passano da B2, quelle al provider LLM dall'egress-proxy.
6. Il launcher emette il `JobResult` e distrugge l'ambiente, tmpfs compreso. Nessun riuso tra tenant.

**Casi limite**
- **Supero di wall-time, memoria, pids, giri di tool o costo:** kill o chiusura con `status` `timeout` o `killed`, `exit_reason` esplicito, evento e segnale; entro `b1.job.kill_grace_s` oltre il limite di tempo. Il retry è di C4.
- **Richiesta di approvazione durante il ciclo di tool:** il job si chiude con `suspended_hitl` e l'ambiente è distrutto; la ripresa avviene in un job nuovo. Chi parcheggia la chiamata è DX-05 (aperta). Il nodo HITL e il checkpoint stanno in C1 e B5.
- **Launcher non disponibile:** fail-closed, nessuna esecuzione nei container condivisi. La guardia `API_ENV=production` è un'invariante di deploy, non una variabile di catalogo e non modificabile da UI (DA-CV-11, D2(b)); è un'eccezione a DX-22 scelta dall'utente.
- **Record di decisione (A3) o audit di B2 non salvato:** l'azione si blocca (DA-A3-07, DA-B2-04). Una coda locale conta come «salvato» solo se durevole su disco con fsync. Se l'audit dell'esito fallisce dopo l'esecuzione, B2 invia un segnale ad A5 e mette l'esito in una coda di recupero; B1 non ritenta la chiamata e chiude con `exit_reason` esplicito. In ondata 1 la conferma viene dalla tabella di audit minima.
- **Egress-proxy e destinazioni dichiarate (DECISIONS §6, DA-B2-07):** una destinazione passa solo se dichiarata con giurisdizione e categorie di dati **e** con sub-responsabile autorizzato (riferimento al DPA e data, GDPR art. 28(2), D7); altrimenti deny. Una destinazione extra-UE passa solo con `tenant.extra_eu_optin.<destination_id>.enabled` attivo, che richiede strumento di trasferimento e stato validi (D5). Lo strumento e l'autorizzazione li imposta il superadmin con fonte e audit, l'opt-in l'admin agenzia (DA-CV-19); il superadmin non lo attiva. Se lo strumento cade, parte un segnale ad A5 e la destinazione si disattiva; la riattivazione richiede un nuovo opt-in. Vale anche per le chiavi dei provider LLM delle agenzie. Ogni rifiuto emette `runtime.egress.denied` con il motivo (`undeclared`, `subprocessor_not_authorized`, `extra_eu_no_optin`, `not_allowlisted`; nomi definitivi da E1). Lo stato di una destinazione non leggibile equivale a deny. L'egress-proxy non valuta in proprio: applica lo stesso esito di A3 sulla policy compilata da A2 (come B2); il deny arriva entro il ritardo massimo di propagazione, variabile di catalogo da definire con A2 e A6, uguale in A3, B2 e B1 (E2).
- **DNS e rete laterale (DA-B1-04, decisa):** il job non ha un resolver proprio; i nomi si risolvono solo tramite egress-proxy o resolver interno con allowlist; nessun accesso al db. 169.254.0.0/16 è sempre bloccato (invariante di rete).
- **Invio verso terzi (E3):** nell'ondata 1 i tool di invio verso terzi sono negati nel bundle. Dopo, B2 rifiuta la chiamata se gli argomenti non portano `ai_generated` con `model` e `prompt_ref`, anche dentro il ciclo di tool; la precondizione di base giuridica, mittente e opposizione la verifica il connettore (D1-D4).
- **Variabili di sviluppo (E5):** i valori «da definire» hanno nell'istantanea un valore di sviluppo dichiarato, ammesso solo fuori produzione; i valori «proposta da validare» valgono come primo valore valido, con segnale.
- **Segnali di incidente:** B1 invia ad A5, senza soglia locale (DA-CV-07), `runtime.egress.denied`, `runtime.job.killed`, i tentativi di escape, i blocchi fail-closed del launcher e le variabili non leggibili. I segnali si producono e si conservano sempre, anche con `incident.nis2_flow_active` falso (C2, D6); il formato si definisce con A5.

## 7. Requisiti non funzionali

- **Sicurezza:** nessuno stato condiviso tra job di tenant diversi (processo, filesystem, token). Cifratura a riposo e in transito (job↔B2, egress-proxy, object storage) e gestione delle chiavi: A6; backup: F6 (E11, GDPR art. 32(1)(a)). Chiavi di produzione mai in CI; i test usano un account di test separato dalla produzione, con dati sintetici, inventario e rotazione dei segreti (C11, D6, DA-E3-08).
- **Performance:** avvio entro `b1.job.start_overhead_p95_ms` (proposta da validare nel catalogo).
- **Scalabilità:** concorrenza per host e quota per tenant in job concorrenti (`b1.host.max_concurrent_jobs`, `b1.tenant.max_concurrent_jobs`, DA-CV-06); modifiche versionate e auditate, `config_version` negli eventi.
- **Osservabilità:** ogni evento ha run_id, company_id e trace_id, nel modello DB-native di E1 (PV-02).
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Gravya è responsabile del trattamento (art. 28) per i dati delle agenzie (DX-11); la base giuridica è dell'agenzia. Minimizzazione: il runtime non persiste nulla, gli eventi portano identificativi e misure, non contenuti; prompt e risposte non sono mai catturati in produzione (DA-E1-02). Gli identificativi (company_id, run_id, agent_id) sono pseudonimi e restano dati personali (considerando 26): vanno trattati con minimizzazione e cancellazione coerente; le linee guida EDPB 01/2025 sono solo in consultazione e non si citano come requisito. Diritti: B1 indicizza ogni artefatto per tenant e run; cancellazione e accesso si esercitano su E1 e sull'object storage. Accesso cross-tenant: B1 non lo offre; il superadmin vede di default solo dati aggregati; l'accesso ai dati di un tenant passa da due vie, entrambe con perimetro, durata (`access.superadmin_trace_access_ttl_hours`) e log di A6 (DX-18, DX-19, `retention.cross_tenant_access_log_months`): (a) incidente dichiarato dal superadmin, con riferimento all'incidente; (b) richiesta di assistenza, in cui l'admin agenzia concede l'accesso (E8). Per una violazione di dati delle agenzie il termine di avviso è un obbligo del DPA (art. 33(2) senza ore; DA-CV-08, valore aperto).
  - *Retention (DX-09, F6).* B1 non fissa durate. Classi prodotte: eventi di runtime (`retention.runtime_events_days`); `JobResult` con `usage` ed `exit_reason` (classe da confermare con F6, proposta: eventi di runtime); artefatti in `outputs_ref` e oggetti `input_ref` (dati del tenant: classe proposta `retention.sensitive_payload_days`, proposta da validare, conferma di F6, DX-21); segnali di incidente (`retention.incident_signals_months`, durata provvisoria: DA-CV-20); evidenze di incidente (`retention.incident_evidence_months`). Le durate sono di sola lettura finché non esiste l'intervallo del DPA (DA-CV-01). Esportazione (E15): i dati di B1 di un tenant sono esportabili con lo strumento di F6, senza fissarne il formato: oggetti di `outputs_ref` e `input_ref` (indicizzati per tenant e run), `JobResult` e eventi di runtime. A fine contratto vale `retention.tenant_offboarding_days` come minimo (Data Act art. 25(2); applicabilità da confermare con un legale); i backup scadono entro `retention.data_backup_days` e al ripristino le cancellazioni già eseguite si riapplicano (DA-CV-22).
  - *Evidenze di incidente (non «legal hold»).* La sospensione delle scadenze per i dati di un incidente non è attivabile finché massimo, riesame e categorie non sono definiti (D5). Vale solo per i dati propri di Gravya; per i dati delle agenzie servono istruzione nel DPA e parere legale prima di F6 (DA-CV-21). La base giuridica resta da scegliere con un legale (DECISIONS §4).
  - *NIS2.* Gravya oggi non è soggetto NIS2; si progetta «NIS2 compliant ready by design» (DX-10). Misure: isolamento per job e tenant, default-deny, minimo privilegio, launcher unico processo privilegiato, nessuna chiave di provider nel job, fail-closed. Per log e accessi privilegiati il riferimento è il Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11, come requisito di progetto, non l'art. 21 della direttiva (che non nomina i log): registrare gli accessi privilegiati all'host e al launcher e le attività degli account amministrativi. Notifica: `incident.nis2_flow_active` (flusso presente, non attivo; segnali sempre prodotti); preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, dalla conoscenza dell'incidente; la responsabilità è di A5 (DX-10).
  - *AI Act.* Casi d'uso non ad alto rischio (DX-11): artt. 12, 14, 19, 26 sono buona pratica (comunque dal 2.12.2027 per l'alto rischio). L'art. 50 si applica dal 2.8.2026: l'etichetta «generato da AI», l'informativa a chi interagisce con un'IA (50(1)) e la marcatura leggibile da macchina anche del testo (50(2)) sono invarianti, con dettaglio in C1 e D1-D4; B1 non produce contenuti per l'utente finale, ma l'executor genera testo: `ai_generated` è nel `JobResult` e negli invii verso terzi (§4, E3).
  - *Marketing.* B1 non invia comunicazioni né traccia utenti; ePrivacy e Codice privacy artt. 122 e 130 sono di D1-D4. L'egress-proxy non apre canali verso terzi oltre la regola delle destinazioni.
  - *Osservabilità AI.* Per ogni job: agente, executor, `prompt_ref`, bundle di policy con hash, giri di tool, token, costo, durata, esito, `exit_reason`, uscite di rete negate, `config_version`.
  - *Perimetro.* Nessun dato lascia il perimetro; l'unica uscita è B2 ed egress-proxy. Piattaforma self-hosted UE (DA-B1-06); sandbox di terzi solo con approvazione dell'utente.

## 8. Criteri di accettazione

I campioni (100 esecuzioni, 200 job) sono parametri del test (DA-CV-04).

1. **Filesystem:** un file scritto in `/tmp` dal tenant X non è visibile al job successivo del tenant Y. 0 occorrenze su 100 esecuzioni.
2. **Processi:** un job non vede processi né variabili d'ambiente di un job concorrente di altro tenant (test su `/proc`): 0.
3. **Rete:** `socket.connect` verso un IP pubblico e verso 169.254.169.254 falliscono; una richiesta via egress-proxy fuori allowlist è negata; nessuna risoluzione DNS dal job fuori dal percorso consentito. 100% negati, con `runtime.egress.denied`.
4. **Limiti:** un job che supera `wall_s` o `memory_mb` termina entro il limite più `b1.job.kill_grace_s`. Un job che supera `pids`, `tool_turns` o `cost_usd` termina con `exit_reason` corrispondente. Esito: 5 su 5.
5. **Effimero:** dopo `finished`, gli ambienti attivi per quel job_id sono 0 (comando sul runtime dei container; DA-B1-02).
6. **Fail-closed:** con il launcher spento e guardia di produzione attiva, il submit dà errore e nessun job gira nei container condivisi.
7. **Isolamento tra tenant:** job concorrenti di tenant diversi non vedono segreti, eventi, token né `outputs_ref` l'uno dell'altro: 0 fughe.
8. **Overhead:** avvio p95 ≤ `b1.job.start_overhead_p95_ms` su 200 job.
9. **Fail-closed su decisione e audit:** con lo store di A3 non scrivibile il submit fallisce e nessun ambiente nasce; con l'audit di B2 non scrivibile la chiamata a tool fallisce. 0 azioni senza record su 100 tentativi.
10. **Destinazioni dichiarate:** destinazione non dichiarata, senza sub-responsabile autorizzato, extra-UE senza opt-in e extra-UE con strumento non valido sono negate al 100%, con il motivo corretto e con lo stesso esito di A3. Dopo la caduta dello strumento il deny arriva entro il ritardo massimo di propagazione, il segnale ad A5 esiste e la riattivazione richiede un nuovo opt-in.
11. **Variabili:** il superadmin abbassa `b1.job.wall_s_default`; il job successivo, senza rilascio, termina entro il nuovo limite e l'evento riporta la nuova `config_version`. Con il registro non leggibile il submit fallisce, con segnale. L'admin agenzia riceve un rifiuto. Esito 3 su 3. Fino ad A6 il test usa l'interfaccia di lettura con un registro simulato (E5).
12. **Token unico:** B2 accetta il `run_token` del job per più chiamate dello stesso run e rifiuta quello di un altro run o scaduto (`b1.run_token.ttl_s`); nel `JobSpec` non esiste `tool_grant_ref`.
13. **Rotazione chiavi:** durante la finestra con due chiavi valide, token firmati con la vecchia e con la nuova chiave sono accettati; dopo la data di disattivazione la vecchia è rifiutata; nessun job fallisce per la sostituzione. Vale per la chiave del token e per l'HMAC dell'egress-proxy.
14. **Quota:** con `b1.tenant.max_concurrent_jobs` raggiunto dal tenant X, i job del tenant Y partono entro `b1.job.start_overhead_p95_ms`; il job in eccesso di X attende e, oltre `b1.queue.max_wait_s`, termina con `queue_wait_exceeded`.
15. **Segnali:** ogni caso di §6 con segnale produce una riga nella tabella di audit minima, anche con `incident.nis2_flow_active` falso.
16. **Chiave LLM fuori dal job:** nell'ambiente, nel filesystem e nei processi del job la chiave del provider non compare (0 occorrenze); una chiamata LLM di prova passa dall'egress-proxy e i suoi log non contengono corpi né URL completi (0 occorrenze).
17. **Invii verso terzi:** dal ciclo di tool, una chiamata a un tool di invio verso terzi senza `ai_generated` è rifiutata da B2 (100% su 100 tentativi); con `ai_generated`, nell'ondata 1 è negata dal bundle.

## 9. Piano di implementazione

**Tecnologie.** Il master indica «Container/VM isolati per tenant». Da gravya-app si riprendono solo idee validate (Docker con hardening, egress-proxy con HMAC, arq, FastAPI), da riprogettare (PV-03). Container o VM: DA-B1-02. Backend in Python (FastAPI, LangGraph, PostgreSQL; E16): il job e il launcher sono in Python, i contratti sono modelli Pydantic. LangGraph è solo la libreria open source (DA-C1-01, DA-C1-05).

**Fasi**
1. Contratti `JobSpec` e `JobResult` (formato: DX-04) e un entrypoint «single-job» in un'immagine minima nuova.
2. Launcher, emissione del `run_token`, profilo di hardening v2.
3. Rete del job: default-deny, uscita solo verso B2 ed egress-proxy con la regola delle destinazioni, DNS chiuso.
4. Integrazione con C1 e la coda, fail-closed su A3 e B2, lettura dei limiti dal registro, segnali ad A5, rotazione a due chiavi.
5. Test di sicurezza (criteri 1–15) e misura dell'overhead.

**Prerequisito:** i valori di `b1.job.*`, `b1.host.max_concurrent_jobs`, `b1.tenant.max_concurrent_jobs` e `b1.queue.max_wait_s` sono «da definire» nel catalogo: in produzione il submit fallisce finché non sono fissati (catalogo §1, regola 4); fuori produzione valgono i valori di sviluppo dell'istantanea (E5).

**Rischi:** il launcher privilegiato è il nuovo punto critico. Executor e ciclo di tool vanno costruiti in v2 (Appendice A, punto 5).

## 10. Test e valutazione

- **Unit:** validazione del `JobSpec`, mappatura exit code → `status`, verifica e scadenza del token.
- **Integration:** submit → started → finished, cancellazione, timeout, sospensione e ripresa, quota per tenant, modifica dei limiti, registro non disponibile, rotazione delle chiavi.
- **Security:** criteri 1–3, 6, 9, 10, 12, 16, 17; tentativi di escape (scrittura sul rootfs, `iptables -F` da non-root, lettura di segreti di altri tenant), injection verso uscita raw o DNS, tentativi di leggere la chiave del provider.
- **Eval:** le suite di E3 girano in B1 con soli dati sintetici (DA-E3-08); giudice LLM solo con elaborazione UE, senza piattaforme SaaS di eval (DA-E3-09). I segreti della CI stanno in un account di test, mai di produzione (C11, D6).

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Il launcher è una superficie di escalation | Processo separato, API minima, non raggiungibile dagli agenti (DA-B1-03); accessi privilegiati registrati |
| Overhead di avvio sui run brevi | Misura (criterio 8); poi pool pre-avviato (DA-B1-01) |
| Kernel dell'host condiviso | Valutare la VM (DA-B1-02) |
| Esfiltrazione via DNS | Chiusa da DA-B1-04: resolver solo via egress-proxy o interno con allowlist |
| Doppio motore Node/Python (lezione da gravya-app) | Un solo motore, LangGraph come libreria (DA-C1-01); nessun executor fuori da B1 |
| Un superadmin alza limiti o quota oltre il sicuro | Modifiche versionate, auditate, fail-closed; il `JobSpec` non supera i tetti |
| Un solo token compromesso dà accesso a B2 | Scadenza `b1.run_token.ttl_s` non oltre `b1.job.wall_s_max`; chiavi sostituibili senza fermo |
| Registro delle variabili assente in ondata 1 | Istantanea nel repository dietro una sola interfaccia, ripiego dichiarato che non soddisfa DX-22 (DA-B1-09) |
| Runtime a container condivisi in produzione con dati reali | Non ammesso finché DA-B1-02 è aperta |

## 12. Stima e priorità

- **Taglia:** L (costruzione da zero: immagine, hardening, rete, launcher, token).
- **Dipendenze critiche:** A3, B2, E1 per i contratti; C1 per il nodo; A6 e A5 (ondata 2) per registro, ruoli e segnali.
- **Thin-slice MVP:** sì, ondata 1. Per lo skeleton bastano le fasi 1–3 su un solo executor.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (PV-03). Letto nelle versioni precedenti, non ricontrollato nella v1.5. Nulla è codice da portare; i valori numerici sono riferimenti, non default di v2.

**Da riprendere come idea**
- `docker/docker-compose.prod.yml`, servizi `agents` e `agents-worker`: `cap_drop: ALL` con `cap_add` limitato al setup, `no-new-privileges`, `read_only: true`, tmpfs `/tmp`, limiti di memoria e pids.
- `services/agents/firewall-entrypoint.sh`: OUTPUT DROP, blocco 169.254.0.0/16, poi `gosu` a un uid non privilegiato; fail-closed in produzione. Il tunnelling DNS era un residuo accettato e il traffico laterale verso db e server era lasciato alla RLS: in v2 sono chiusi (DA-B1-04).
- `services/agents/src/egress/` e `docker/egress-proxy`: allowlist default-deny per azienda con firma HMAC. Letti solo i nomi dei file.
- `services/agents/src/job_queue/tenant_context.py`: il worker arq riusa lo stesso processo per più job e tenant; l'isolamento è `set_config('gravya.company_id')` con RESET.
- `services/agents/src/job_queue/worker.py`: `job_timeout = 300` s. `office_tool.py` esegue un binario esterno nel container condiviso.

**Difetti da non ripetere**
1. Container long-lived condivisi da tutti i tenant, contro l'ambiente effimero del master.
2. Isolamento per RLS via GUC: il modello «filtro per company_id» che il master dice non bastare.
3. Traffico laterale verso db e server aperto per scelta (sign-off del 2026-07-03 nel commento dello script).
4. Timeout arq di 300 s diverso dal limite «A6» di kloudify (10 min per run): «A6» è un'etichetta di kloudify, non il sottoprodotto A6.
5. `generic_executor.py` (commit `349118b11`) contiene `_run_tool_loop`: il ciclo di tool esiste; se sia raggiunto in produzione è non verificato.
6. Il master prevede OpenTelemetry; in v2 è escluso (PV-02).
7. Nessuna sandbox per singola esecuzione e nessun ADR in `docs/decisions`.

## Appendice B — Non verificato

- Che l'orchestratore self-hosted UE (DA-B1-06) permetta a un launcher di creare ambienti per job, e con quali privilegi.
- Contenuto di `actor_context.py`, `egress/allowlist.py`, `egress-proxy`; valori reali di overhead; risorse di `agents-worker` oltre la memoria.
- Backend e collocazione dell'object storage di v2 (nel perimetro controllato).
- Classe di retention di `outputs_ref`, `input_ref` e `JobResult`: proposte in §7, da confermare con F6 (DX-21).
- Interfaccia del registro delle variabili e pagine di UI: A6, non redatto. Nomi delle variabili sotto DX-07 (aperta).
- Il catalogo §18 elenca ancora B1 tra i documenti del «token monouso»: va corretto dal coordinator (E7); non ricontrollato nel catalogo 1.3.
- Formato di `prompt_ref` (E2) e struttura dell'oggetto `input_ref` (C1, non ricontrollata nel suo documento); nome e valore della variabile per il ritardo massimo di propagazione del deny (A3, E2): non ricontrollati.
- Comportamento fuori produzione (esecuzione senza launcher per lo sviluppo): la guardia riguarda la produzione, il resto non è deciso.
- Formato dell'esportazione dei dati di un tenant: proposta del coordinator in attesa di conferma dell'utente (E15).
- Qualificazione di Gravya come fornitore cloud e dimensione (NIS2); SaaS come «servizio di trattamento dei dati» (Data Act); stato giudiziario del DPF (C-703/25 P); testo del Codice art. 50 sulla marcatura del testo: tutti ◐ o aperti nel registro.
- Se B1 o i connettori includono software distribuito ai clienti (Cyber Resilience Act): da chiarire (registro, N-CRA).
- La conformità effettiva delle misure di §7: impostazione di progetto, non verificata con `gravya-app/docs/compliance/`.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-B1-01 | Unità di isolamento | (a) un ambiente per job; (b) pool long-lived per tenant; (c) pool per tenant con ambiente distrutto a fine job | Isolamento contro overhead misurato | **Aperta.** (a) come da master; (c) solo se il criterio 8 fallisce |
| DA-B1-02 | Tecnologia | (a) container con profilo di hardening v2; (b) microVM effimera | Kernel condiviso accettabile, fattibilità su DA-B1-06 | **Aperta.** (a) per lo skeleton, (b) dopo un test di sicurezza. Finché è aperta, il runtime a container condivisi non va in produzione con dati reali |
| DA-B1-03 | Launcher e trasporto | (a) servizio launcher dedicato chiamato dalla coda; (b) worker che crea direttamente gli ambienti (DX-03) | Minimizzare chi accede al runtime dei container | **Aperta.** (a) |
| DA-B1-04 | Rete laterale e DNS | — | — | **Decisa (2026-11-03, utente):** uscita solo verso B2 ed egress-proxy; DNS chiuso, nomi solo via egress-proxy o resolver interno con allowlist |
| DA-B1-05 | Telemetria del job | — | — | Chiusa da DX-02 (PV-02) |
| DA-B1-06 | Piattaforma | — | — | **Decisa (2026-11-03, utente):** self-hosted UE; sandbox di terzi solo con approvazione |
| DA-B1-07 | Retention | — | — | Assorbita da DX-09 (classi in §7) |
| — | Grafo C1 nel job B1 o solo i nodi agente | — | — | **Decisa (2026-11-03, utente, DECISIONS §6):** solo i nodi agente, un job per nodo; il grafo C1 gira nel servizio di orchestrazione |
| DA-B1-08 | Comportamento oltre la quota | (a) attesa in coda; (b) rifiuto | Vicino rumoroso (DA-CV-06) | **Decisa (E13, 2026-11-04, utente):** (a); attesa massima `b1.queue.max_wait_s` |
| DA-B1-09 | Lettura delle variabili in ondata 1 | — | — | **Decisa (E5, 2026-11-04, utente):** istantanea versionata nel repository, modificabile solo con una PR, dietro una sola interfaccia; ripiego dichiarato che non soddisfa DX-22 finché A6 non esiste. «Proposta da validare» = primo valore valido con segnale; «da definire» = valore di sviluppo, solo fuori produzione |
| DA-B1-10 | Prompt e input del job | — | — | **Decisa (E6, 2026-11-04, utente):** C1 risolve il prompt da E2 e passa testo renderizzato e input con `input_ref` (classe dei payload sensibili temporanei); il job non accede al DB |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunta la riga Ondata in Identità; corretta l'affermazione "oggi non c'è un ciclo di tool" (Appendice A punto 5 e §9), smentita dalla lettura di `generic_executor.py` al commit 349118b11 e in contraddizione con B2; aggiunte in §3 le dipendenze da E2 (dichiarata da E2) e B5 (già in §12). Motivo: affermazione sullo stato del codice non supportata e dipendenze dichiarate in un solo verso. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): §2, §3, §9, §10 riformulati senza riuso di immagine, hardening, firewall e test di gravya-app, citati come riferimento; criterio 7 riscritto come test v2; Appendice A rinominata «Riferimenti dal sistema precedente»; taglia in §12 ricalcolata (resta L). Applicate DX-02/PV-01/PV-02 (niente OTel, conformità prioritaria): `trace_context` ed eventi sul modello DB-native di E1; aggiunta in §7 la voce «Sicurezza e conformità» (GDPR, NIS2, AI Act, osservabilità AI); DA-B1-05 chiusa da DX-02; DA-B1-02, 03, 04 riformulate; nuove DA-B1-06 (piattaforma, perimetro dati) e DA-B1-07 (retention), da riportare all'utente. (rev. coerenza) `trace_context`: `span_id` sostituito da `parent_segment_id` (modello E1 §4.1). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-B1-06 decisa (self-hosted UE): §3, §7, §9, Appendici B e C. DA-B1-07 assorbita da DX-09: in §7 nessuna retention propria, elencate le classi di dati prodotte. DX-10: segnali di sicurezza inviati ad A5. DX-11: ruolo art. 28 confermato, artt. 12/14 AI Act ridotti a buona pratica, art. 50 resta (a monte/valle). Fail-closed (DA-A3-07, DA-B2-04): nuovo caso limite in §6, criterio 9, fasi e test aggiornati. DA-B2-07 in §6; DA-E1-05 (traceparent e nomi GenAI semconv come vocabolario, scelta di E1) in §4; DA-E1-02 in §7; DA-C1-01/05 in §9 e §11; DA-E3-08/09 in §10. Taglia invariata (L). Motivo: allineamento a DECISIONS.md. |
| 1.4 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DX-09 §5: durate di default in §7 (eventi di runtime 90 giorni, checkpoint 30 giorni, legal hold incidenti) e in Appendice C (DA-B1-07). DX-13: limiti di default dei job, concorrenza per host e quota per tenant come variabili di piattaforma gestite dal superadmin (§3, §4, §6, §7), accesso cross-tenant solo come superadmin con log (§7); nuovi criteri 10-11, test e rischi; DX-14 citata come dipendenza proposta (A6, da riportare). Righe decise di DECISIONS §6: egress-proxy con regola delle destinazioni dichiarate (§6, criterio 10); coda durevole con fsync e audit fallito dopo l'esecuzione (§6). La riga aperta su LangGraph nel job B1 è riportata in Appendice C. Motivo: allineamento a DECISIONS.md. |
| 1.5 | 2026-11-04 | Allineamento alle decisioni del 2026-11-03/04, al catalogo 1.2 e al registro delle norme 1.6. Un solo token `run_token` emesso da B1 e verificato da B2, `tool_grant_ref` eliminato (DA-CV-13); rotazione delle chiavi con due chiavi in parallelo (DA-CV-23); guardia `API_ENV` come invariante di deploy (DA-CV-11); limiti e quote con i nomi del catalogo, quota in job concorrenti (DA-CV-06); dentro B1 solo i nodi agente (DECISIONS §6); egress-proxy con sub-responsabile autorizzato, opt-in per destinazione e strumento di trasferimento (DA-B2-07, D5, D7, DA-CV-19); DA-B1-04 registrata come decisa (DNS chiuso); «legal hold» sostituito da evidenze di incidente (DA-CV-21); log NIS2 riferiti al Reg. 2024/2690, flusso presente ma non attivo, segnali sempre prodotti (DX-10, C2, D6); AI Act art. 50 e calendario; segreti CI in account di test (C11, D6); retention con i nomi del catalogo (DA-CV-20, DA-CV-22); nuovi criteri 12-15; nuove DA-B1-08, 09, 10; taglio dei valori fissi (DX-22). Motivo: un solo giro di revisione prima dell'approvazione. |
| 1.6 | 2026-11-04 | Decisioni E1-E16 del 2026-11-04 (utente, con E8 ed E15 integrate) e revisione unica della v1.5 (plan-auditor, compliance-auditor A1-A3-B1). Prompt e input: C1 li risolve e li passa con `input_ref`, il job non accede al DB (E6); chiave del provider LLM fuori dal job, chiamate LLM dall'egress-proxy senza registrare corpi né URL (E11, R-07, R-08); egress-proxy con lo stesso esito di A3 sui trasferimenti (E2); invii verso terzi senza `ai_generated` rifiutati da B2 anche nel ciclo di tool, `ai_generated` nel `JobResult` (E3); `run_token` non monouso (E7); istantanea delle variabili in ondata 1 (E5); attesa in coda con `b1.queue.max_wait_s` (E13); backend Python (E16); accesso del superadmin per incidente o per richiesta di assistenza (E8); esportazione dei dati del tenant con lo strumento di F6 (E15); cifratura a A6 e backup a F6 (E11, R-10); classe di retention di `outputs_ref` e `input_ref` (R-09); dichiarazione sul runtime a container condivisi (DA-B1-02); nuovi criteri 16-17; DA-B1-08, 09, 10 decise; tolte le note «non ancora in DECISIONS». Ripristinate le righe 1.1-1.4 nel testo originale. Motivo: un solo giro di correzioni prima dell'approvazione. |
