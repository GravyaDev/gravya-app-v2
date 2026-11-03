# B1 — Agent runtime isolato

## 1. Identità

| Campo | Valore |
|---|---|
| ID | B1 |
| Nome | Agent runtime isolato |
| Componente padre | B — Runtime Agenti |
| Versione documento | 1.3 |
| Data | 2026-11-03 |
| Ondata | 1 (walking skeleton) |

> Attenzione al nome: in gravya-app-kloudify esiste una decisione chiamata «B1 (organico agenti)», chiusa il 16/10, che non ha niente a che fare con questo sottoprodotto. Riguarda il numero di supervisori.

## 2. Scopo

**Cosa fa.** Esegue ogni job agente (un run di un executor e le chiamate ai tool che fa) in un ambiente effimero creato per quel job. L'ambiente ha un filesystem temporaneo, che viene distrutto alla fine, e una rete limitata: default-deny, con uscita solo attraverso i canali autorizzati. È legato a un solo tenant (company_id). Il master plan (§2) chiede isolamento «per design» di compute, non filtri `WHERE company_id = ?`.

**Cosa NON fa.**
- Non decide quali tool un agente può usare. Questo spetta ad A3 (enforcement) e a B2 (tool gateway).
- Non conserva lo stato tra un job e l'altro. Memoria e checkpoint sono di B3, B4 e B5.
- Non definisce il workflow. Il grafo è di C1, l'approvazione umana di C3.
- Non sostituisce la RLS di Postgres. La affianca come secondo livello.

**Perché esiste.** Un job agente compromesso, per esempio da prompt injection, non deve poter condividere processo, `/tmp`, segreti o rete con i job di altre agenzie. B1 limita il raggio d'azione al singolo job e al singolo tenant. La lezione viene da gravya-app, dove i container `agents` e `agents-worker` sono processi long-lived condivisi da tutti i tenant (Appendice A): è il difetto da non ripetere, non una base da correggere (PV-03).

## 3. Contesto e dipendenze

**Dipende da:**
- **A3**: la decisione allow/deny si prende prima di avviare il job e prima di ogni azione.
- **B2**: è l'unico canale verso i tool e le API esterne autorizzati.
- **E1**: ogni ciclo di vita del job deve produrre tracce correlate.
- **C1**: è il chiamante che invoca il job. Ospitare il nodo agente è il compito di B1.
- **E2**: il runtime risolve il prompt dell'agente dal registry (dipendenza dichiarata da E2 §3 e §5, aggiunta in revisione v1.1; il `JobSpec` non ha ancora un campo per il riferimento al prompt: vedi problemi aperti in `revisione-ondata-1.md`).
- **B5** (ondata 2): checkpoint per la sospensione HITL e la ripresa (già citato in §12 come dipendenza critica).

**È richiesto da:** C3 (il job si sospende in attesa di HITL, quindi l'ambiente va distrutto e ricreato alla ripresa), B5 (la ripresa da checkpoint avviene in un nuovo ambiente), C4 (retry e DLQ), D1–D5 (i tool girano dentro o dietro B1), E3 (le eval offline devono girare nello stesso runtime).

**Assunzioni (non verificate):**
- La piattaforma di esecuzione è self-hosted su infrastruttura UE (DA-B1-06, decisa); sandbox gestite di terzi solo con approvazione esplicita dell'utente. Quale orchestratore usare (Compose/Coolify come in gravya-app o altro) non è deciso.
- Il run agente può essere serializzato in un payload di input: run_id, company_id, riferimento al checkpoint. Il riferimento al checkpoint dipende da B5.
- I segreti LLM vengono risolti per azienda e iniettati solo nel job del tenant. In gravya-app esiste una soluzione analoga (gravya-app#890), da riprendere come idea e riprogettare sul contratto v2.

## 4. Contratti

**Input: `JobSpec`**

| Campo | Tipo | Note |
|---|---|---|
| job_id | UUID | Idempotenza |
| company_id | UUID | Validato come UUID, come in `tenant_context.py` |
| run_id / execution_ticket_id | UUID | Correlazione con le tracce del modello dati DB-native di E1 |
| agent_id, executor_kind | string | |
| policy_bundle_ref | string, con hash | Prodotto da A2/A3 |
| tool_grant_ref | string | Token di B2 limitato al job |
| limits | {wall_s, mem_mb, pids, tool_turns, cost_usd} | Valori da fissare in v2. Riferimento dal sistema precedente: limiti A6 di kloudify, 10 min e $2 per run, 8 giri di tool |
| trace_context | string | Identificativi di correlazione (trace_id, parent_segment_id) nel formato del modello DB-native di E1. Il formato traceparent è ammesso come formato (DA-E1-05); la scelta spetta a E1. Nessun SDK né export OTel (PV-02) |

**Output: `JobResult`.** Contiene `status` (`succeeded`, `failed`, `timeout`, `killed`, `suspended_hitl`), `outputs_ref` (URI su object storage, mai payload inline), `usage` (token, costo, durata) ed `exit_reason`.

**Eventi emessi:** `runtime.job.started`, `runtime.job.finished`, `runtime.job.killed`, `runtime.egress.denied`. Lo schema e gli attributi (`gravya.*`) sono quelli del vocabolario unificato di E1, sul modello dati DB-native di E1 (DX-02, PV-02). Per gli attributi GenAI (modello, token, costo) E1 può adottare i nomi delle GenAI semantic conventions come vocabolario (DA-E1-05); B1 usa i nomi che E1 fissa. Gli eventi non contengono prompt, output o segreti: solo identificativi, esiti, motivi e misure.

**Eventi consumati:** la richiesta di job, dalla coda arq o da C1, e la cancellazione.

## 5. Interfacce

- **Interna, verso C1 e la coda:** `submit(JobSpec) -> job_id`, `cancel(job_id)`, `status(job_id)`. Il trasporto va scelto tra endpoint FastAPI interno e job arq (DA-B1-03).
- **Verso l'host:** un componente «launcher» crea e distrugge l'ambiente. È l'unico processo con privilegi sul runtime dei container e non è esposto agli agenti.
- **Dentro l'ambiente:** l'entrypoint riceve il `JobSpec` da stdin o da un file montato in sola lettura ed emette il `JobResult` su stdout o su un file.
- **Nessuna UI.** Lo stato è visibile dall'osservabilità DB-native di E1.

## 6. Comportamento

**Flusso principale**
1. C1 o la coda inviano il `JobSpec`.
2. A3 valuta l'avvio e rifiuta se manca un mandato. Se il record di decisione di A3 non si salva, il job non parte (fail-closed, DA-A3-07).
3. Il launcher crea l'ambiente con: rootfs in sola lettura, `/tmp` in tmpfs dedicato, utente non-root, zero capability dopo il setup, rete default-deny verso l'esterno con uscita solo verso B2 e verso egress-proxy, limiti di CPU, memoria e pids, e segreti del solo tenant.
4. Il job esegue l'executor. Le chiamate ai tool passano da B2.
5. Viene emesso il `JobResult` e l'ambiente viene distrutto, compreso tmpfs. Nessun riuso tra tenant.

**Casi limite**
- **Supero di wall-time o memoria:** kill, `status=timeout` o `killed`, evento emesso, poi retry secondo C4.
- **Richiesta HITL (C3):** checkpoint tramite B5, `suspended_hitl`, distruzione dell'ambiente. La ripresa avviene in un ambiente nuovo.
- **Launcher non disponibile:** fail-closed, quindi nessuna esecuzione nei container condivisi come ripiego in produzione. È lo stesso principio di `firewall-entrypoint.sh` con `API_ENV=production`.
- **Connessione raw verso l'esterno:** viene bloccata ed emette `runtime.egress.denied`.
- **Record di decisione o audit non salvato:** se A3 non riesce a salvare il record di decisione (DA-A3-07) o B2 l'audit della chiamata a tool (DA-B2-04), l'azione si blocca: il job non parte o la chiamata a tool fallisce, con `exit_reason` esplicito.
- **Tool con destinazione non dichiarata o extra-UE:** la chiamata è negata da B2 (DA-B2-07); B1 la riceve come errore del tool e non offre canali alternativi.

**Residui da dichiarare:** in gravya-app il tunnelling DNS è accettato come residuo (`firewall-entrypoint.sh`). In v2 va deciso se B1 lo chiude o lo accetta come residuo dichiarato (DA-B1-04); essendo un canale di esfiltrazione, accettarlo è una scelta da riportare all'utente.

## 7. Requisiti non funzionali

- **Sicurezza:** nessuno stato condiviso tra job di tenant diversi (processo, filesystem, segreti). Per l'uscita valgono le regole di §6.
- **Performance:** overhead di avvio p95 sotto i 3 s (proposta da validare).
- **Scalabilità:** concorrenza massima per host configurabile, con una quota per tenant contro il noisy neighbour (valori da definire).
- **Osservabilità:** ogni job ha run_id, company_id e trace_id su tutti gli eventi, registrati nel modello DB-native di E1 (PV-02). Nessun SDK, collector o esportatore OpenTelemetry.
- **Sicurezza e conformità (PV-01):**
  - *GDPR.* Minimizzazione: il runtime non persiste nulla; l'ambiente, tmpfs compreso, è distrutto a fine job; gli eventi portano identificativi e misure, non contenuti; gli output stanno solo in `outputs_ref` sull'object storage del perimetro Gravya. Ruolo: Gravya è responsabile del trattamento (art. 28) per conto delle agenzie (DX-11); la base giuridica del trattamento dei dati dei clienti finali è dell'agenzia e non si decide qui. Retention: si applica la politica unica DX-09 (durate non ancora fissate); B1 non fissa durate proprie. Classi di dati prodotte da B1: eventi di runtime (`runtime.job.*`, `runtime.egress.denied`), `JobResult` con `usage` ed `exit_reason`, artefatti di output referenziati da `outputs_ref` sull'object storage. Prompt e risposte non sono mai catturati in produzione (DA-E1-02). Diritti: poiché il runtime non conserva stato, cancellazione e accesso si esercitano su E1 e sull'object storage tramite company_id/run_id; B1 deve solo garantire che ogni artefatto sia indicizzato per tenant e run.
  - *NIS2 (art. 21).* Misure: isolamento per job e tenant, default-deny di rete, minimo privilegio (non-root, zero capability, rootfs in sola lettura), launcher unico processo privilegiato e non esposto, segreti per tenant iniettati solo nel job, fail-closed. Gestione incidenti: la notifica (allerta 24 h, notifica 72 h) è responsabilità di A5, ondata 2 (DX-10). B1 invia ad A5 come segnali `runtime.egress.denied`, `runtime.job.killed`, i tentativi di escape e i blocchi fail-closed del launcher; il formato del segnale si definisce con A5.
  - *AI Act.* I casi d'uso v2 non sono ad alto rischio (DX-11): log e sorveglianza umana (artt. 12, 14) non sono obblighi ma buona pratica di osservabilità, che B1 mantiene (tracciamento da avvio a fine con esito e motivo, stato `suspended_hitl` esplicito, `cancel(job_id)`). L'art. 50 resta applicabile, ma B1 non produce contenuti per l'utente: la trasparenza si gestisce a monte (C1, E2) e a valle (canali).
  - *Osservabilità AI resa disponibile.* Per ogni job: agente ed executor, riferimento al prompt (quando il `JobSpec` lo avrà), bundle di policy con hash, giri di tool, token, costo, durata, esito ed exit_reason, uscite di rete negate.
  - *Perimetro.* Nessun componente di B1 invia dati fuori dal perimetro controllato; l'unica uscita è attraverso B2 ed egress-proxy. La piattaforma di esecuzione è self-hosted su infrastruttura UE (DA-B1-06); sandbox o VM gestite di terzi solo con approvazione esplicita dell'utente.

## 8. Criteri di accettazione

1. **Isolamento filesystem:** un test di integrazione scrive un file in `/tmp` nel job del tenant X. Il job successivo, del tenant Y, non lo vede. Esito atteso: 0 occorrenze su 100 esecuzioni.
2. **Isolamento processo:** un job del tenant X non vede i processi né le variabili d'ambiente di un job concorrente del tenant Y. Verifica: test che enumera `/proc`, esito 0.
3. **Rete:** dall'interno del job, `socket.connect` verso un IP pubblico e verso 169.254.169.254 falliscono. HTTP via egress-proxy verso un host fuori allowlist viene negato. Esito: 100% negati, con evento `runtime.egress.denied`.
4. **Limiti:** un job che supera wall_s o mem_mb termina con `timeout` o `killed` entro wall_s + 5 s (proposta da validare).
5. **Effimero:** dopo `finished`, il numero di ambienti attivi per quel job_id è 0. Si verifica con un comando sul runtime dei container (dipende da DA-B1-02).
6. **Fail-closed:** con il launcher spento e `API_ENV=production`, il submit restituisce errore e nessun job gira nei container condivisi.
7. **Isolamento dei dati tra tenant:** un test multi-tenant v2 (ispirato a `test_queue_multi_tenant_isolation` di gravya-app, da riscrivere sul contratto nuovo) verifica che job concorrenti di tenant diversi non vedano segreti, eventi né `outputs_ref` l'uno dell'altro. Esito: 0 fughe.
8. **Overhead:** avvio p95 sotto i 3 s su 200 job (proposta da validare).
9. **Fail-closed su decisione e audit:** con lo store dei record di decisione di A3 non scrivibile, il submit fallisce e nessun ambiente viene creato; con lo store di audit di B2 non scrivibile, la chiamata a tool fallisce e nessuna richiesta esce dal job. Esito: 0 azioni eseguite senza record su 100 tentativi.

## 9. Piano di implementazione

**Tecnologie.** Il master indica «Container/VM isolati per tenant». gravya-app ha validato come idee Docker con hardening, iptables e gosu, egress-proxy con HMAC, arq e FastAPI: sono riferimenti, non componenti da portare (PV-03). La scelta tra container e VM resta aperta (DA-B1-02). La piattaforma è self-hosted su infrastruttura UE (DA-B1-06, decisa); l'orchestratore resta da scegliere. Se C1 esegue nodi agente LangGraph, LangGraph è usato solo come libreria open source, senza LangSmith né LangGraph Platform (DA-C1-01, DA-C1-05).

**Fasi (in ordine)**
1. **Definire i contratti.** `JobSpec` e `JobResult`, più un entrypoint «single-job» che esegue un run e termina, in un'immagine nuova e minima per v2 (l'immagine `services/agents/Dockerfile` di gravya-app è solo riferimento).
2. **Launcher con un ambiente per job**, con un profilo di hardening definito per v2 (il compose prod di gravya-app, Appendice A, indica le misure da riprendere).
3. **Rete del job:** default-deny e uscita solo verso B2 ed egress-proxy, riprogettata per v2 senza il traffico laterale aperto che `firewall-entrypoint.sh` di gravya-app ammette.
4. **Integrazione** con la coda e C1 (trasporto da DX-03), gestione della sospensione HITL e ripresa (B5), con fail-closed anche sul mancato salvataggio dei record di A3 e B2.
5. **Test di sicurezza** dei criteri 1–7 e 9, misura dell'overhead e verifica che gli eventi arrivino nel modello DB-native di E1.

**Rischi principali:** il launcher privilegiato (accesso al runtime dei container) diventa il nuovo punto critico. L'executor e il ciclo di tool vanno costruiti in v2: quello di gravya-app è solo riferimento (Appendice A, punto 5).

## 10. Test e valutazione

- **Unit:** validazione del `JobSpec` (UUID, limiti), mappatura degli exit code su `status`.
- **Integration:** ciclo completo submit → started → finished, cancellazione, timeout, sospensione e ripresa HITL.
- **Security:** criteri 1–3, 6 e 9 (fail-closed), tentativi di escape (scrittura sul rootfs, `iptables -F` da utente non-root, lettura dei segreti di altri tenant), injection che tenta l'uscita raw.
- **Eval:** le suite di E3 girano dentro B1 con soli dati sintetici (DA-E3-08), scorer nel perimetro Gravya e giudice LLM solo con elaborazione UE, senza piattaforme SaaS di eval (DA-E3-09), e confrontano l'esito con la baseline definita da E3.

## 11. Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Il launcher con accesso al runtime dei container è una superficie di escalation | Processo separato, API minima, nessuna raggiungibilità dagli agenti (DA-B1-03) |
| L'overhead di avvio rallenta i run brevi | Misurarlo (criterio 8), poi valutare un pool pre-avviato per tenant (DA-B1-01) |
| Il kernel dell'host è condiviso tra i container | Valutare la VM (DA-B1-02) |
| Tunnelling DNS | DA-B1-04 |
| Doppio motore Node/Python (lezione da gravya-app) | In v2 B1 isola ogni esecuzione agente, con LangGraph come motore unico usato come libreria (DA-C1-01); nessun executor deve girare fuori da B1 |
| Tunnelling DNS come canale di esfiltrazione (NIS2, GDPR) | DA-B1-04; accettarlo come residuo va riportato all'utente |

## 12. Stima e priorità

- **Taglia:** L (ricalcolata per una costruzione da zero: in v1.1 la stima contava sul riuso di immagine, hardening e firewall di gravya-app; senza riuso resta L, al limite superiore, perché si aggiungono immagine, profilo di hardening e rete da progettare).
- **Dipendenze critiche:** A3, B2 ed E1 per i contratti. B5 per la ripresa.
- **Thin-slice MVP:** sì, è nell'ondata 1. Per lo skeleton basta la fase 1–3 su un solo executor.

---

## Appendice A — Riferimenti dal sistema precedente

Cosa insegna gravya-app (PV-03): soluzioni da riprendere come idea e difetti da non ripetere. Nulla di quanto segue è codice da portare.

**Soluzioni da riprendere come idea (file letti)**
- `docker/docker-compose.prod.yml`, servizi `agents` e `agents-worker`: hanno già `cap_drop: ALL`, `cap_add` limitato a NET_ADMIN, SETUID e SETGID (usati solo nella fase di setup), `no-new-privileges`, `read_only: true`, tmpfs `/tmp` (512M su agents), limiti di memoria (2G e 1G) e `pids: 512` su agents. È un buon elenco di misure da cui partire per il profilo del singolo job.
- `services/agents/firewall-entrypoint.sh`: imposta OUTPUT DROP, permette solo i peer interni, blocca 169.254.0.0/16, poi `gosu` all'uid 10001. È fail-closed in produzione. Il tunnelling DNS è dichiarato residuo accettato. Il traffico laterale verso i peer interni, db compreso, è lasciato alla RLS.
- `services/agents/src/egress/` (`allowlist.py`, `hmac_signer.py`) e `docker/egress-proxy`: allowlist default-deny per azienda. Ho letto solo i nomi dei file.
- `services/agents/src/job_queue/tenant_context.py`: il worker arq **riusa lo stesso processo per più job e più tenant**. L'isolamento consiste in `set_config('gravya.company_id')` con RESET a fine job.
- `services/agents/src/job_queue/worker.py`: `job_timeout = 300` s.
- `services/agents/src/tools/office/office_tool.py`: esegue un binario esterno con `asyncio.create_subprocess_exec` dentro il container condiviso.

**Difetti da non ripetere e divergenze dal master plan**
1. Il master chiede un ambiente effimero per job, isolato per tenant. Il codice ha container long-lived condivisi da tutti i tenant.
2. Oggi l'isolamento tra tenant nel runtime è RLS via GUC, cioè proprio il modello «filtro per company_id» che il master dice di non bastare.
3. La rete limitata esiste, ma il traffico laterale verso db e server è aperto per scelta (il commento in `firewall-entrypoint.sh` attribuisce la decisione a una sign-off del 2026-07-03).
4. Il timeout arq di 300 s non coincide con il limite A6 di 10 min per run riportato in kloudify (`docs/visione/controlli-e-conformita.md`, tramite la ricognizione).
5. Secondo `docs/stato/kloudify.md` (visione al 16/10), `generic_executor` perde le chiamate ai tool. **Corretto in revisione:** al commit `349118b11` di gravya-app `services/agents/src/executors/generic_executor.py` contiene `_run_tool_loop` (riga 438) con `_MAX_TOOL_CALLS_PER_RESPONSE = 8` (riga 40); le righe 195-211 caricano i tool e separano letture da scritture parcheggiate. Il ciclo di tool quindi esiste nel codice (coerente con B2, Appendice A); resta Non verificato se sia raggiunto in produzione o staging.
6. Il master prevede OpenTelemetry. gravya-app lo escludeva già (Timeline DB-native); in v2 la divergenza è chiusa da DX-02/PV-02: niente OTel.
7. Nessuna sandbox per singola esecuzione e nessun ADR su questo tema in `docs/decisions` (grep senza risultati).

## Appendice B — Non verificato

- Che l'orchestratore self-hosted UE che sarà scelto (DA-B1-06; Coolify è solo quello di gravya-app) permetta a un launcher di creare ambienti per job, e con quali privilegi.
- Il contenuto di `actor_context.py`, `egress/allowlist.py` ed `egress-proxy`.
- Il backend object storage di v2 e la sua collocazione (in gravya-app S3 o Garage, non verificato); deve stare nel perimetro controllato.
- Il valore reale dell'overhead di avvio di un ambiente per job.
- La conformità effettiva delle misure: le valutazioni GDPR/NIS2 di §7 (ruolo e classe di rischio ora decisi da DX-11) sono impostazione di progetto, non verificate con le analisi in `gravya-app/docs/compliance/`, da riverificare.
- I limiti di risorse del servizio `agents-worker` oltre alla memoria di 1G.

## Appendice C — Decisioni aperte

| ID | Titolo | Opzioni | Criterio | Raccomandazione |
|---|---|---|---|---|
| DA-B1-01 | Unità di isolamento | (a) un ambiente per job; (b) un pool long-lived per tenant; (c) pool per tenant con ambiente distrutto a fine job | Isolamento contro overhead misurato | (a) come da master. (c) solo se il criterio 8 fallisce |
| DA-B1-02 | Tecnologia | (a) container con profilo di hardening v2; (b) VM effimera (microVM) | Kernel condiviso accettabile o no, fattibilità sulla piattaforma (DA-B1-06), dati nel perimetro | (a) per lo skeleton, (b) da rivalutare dopo un test di sicurezza |
| DA-B1-03 | Launcher e trasporto | (a) servizio launcher dedicato chiamato dalla coda; (b) worker della coda che crea direttamente gli ambienti (trasporto da DX-03) | Minimizzare chi ha accesso al runtime dei container | (a) |
| DA-B1-04 | Rete laterale e DNS | (a) accesso a tutta la subnet interna (modello gravya-app); (b) uscita solo verso B2 ed egress-proxy, senza db; DNS: chiuso (resolver interno con allowlist) o residuo dichiarato | Raggio d'azione, esfiltrazione (PV-01) | (b): il job non parla con il db direttamente, ma tramite B2 o API. Accettare il DNS come residuo: DA RIPORTARE ALL'UTENTE |
| DA-B1-05 | Telemetria del job | — | — | **Chiusa da DX-02 (PV-02):** telemetria DB-native sul modello dati e sul vocabolario `gravya.*` di E1, niente OTel |
| DA-B1-06 | Piattaforma di esecuzione e deploy | — | — | **Decisa (2026-11-03, utente)**, vedi [DECISIONS.md](DECISIONS.md): self-hosted su infrastruttura UE; sandbox gestite di terzi solo con approvazione esplicita. L'orchestratore resta da scegliere |
| DA-B1-07 | Retention di eventi di runtime e `outputs_ref` | — | — | **Assorbita da DX-09**, vedi [DECISIONS.md](DECISIONS.md): politica di retention unica, durate non ancora fissate |

## Storico modifiche

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | 2026-11-03 | Prima stesura (ondata 1) |
| 1.1 | 2026-11-03 | Revisione incrociata ondata 1: aggiunta la riga Ondata in Identità; corretta l'affermazione "oggi non c'è un ciclo di tool" (Appendice A punto 5 e §9), smentita dalla lettura di `generic_executor.py` al commit 349118b11 e in contraddizione con B2; aggiunte in §3 le dipendenze da E2 (dichiarata da E2) e B5 (già in §12). Motivo: affermazione sullo stato del codice non supportata e dipendenze dichiarate in un solo verso. |
| 1.2 | 2026-11-03 | Applicate DX-01/PV-03 (ripartenza da zero): §2, §3, §9, §10 riformulati senza riuso di immagine, hardening, firewall e test di gravya-app, citati come riferimento; criterio 7 riscritto come test v2; Appendice A rinominata «Riferimenti dal sistema precedente»; taglia in §12 ricalcolata (resta L). Applicate DX-02/PV-01/PV-02 (niente OTel, conformità prioritaria): `trace_context` ed eventi sul modello DB-native di E1; aggiunta in §7 la voce «Sicurezza e conformità» (GDPR, NIS2, AI Act, osservabilità AI); DA-B1-05 chiusa da DX-02; DA-B1-02, 03, 04 riformulate; nuove DA-B1-06 (piattaforma, perimetro dati) e DA-B1-07 (retention), da riportare all'utente. (rev. coerenza) `trace_context`: `span_id` sostituito da `parent_segment_id` (modello E1 §4.1). |
| 1.3 | 2026-11-03 | Applicate le decisioni dell'utente del 2026-11-03. DA-B1-06 decisa (self-hosted UE): §3, §7, §9, Appendici B e C. DA-B1-07 assorbita da DX-09: in §7 nessuna retention propria, elencate le classi di dati prodotte. DX-10: segnali di sicurezza inviati ad A5. DX-11: ruolo art. 28 confermato, artt. 12/14 AI Act ridotti a buona pratica, art. 50 resta (a monte/valle). Fail-closed (DA-A3-07, DA-B2-04): nuovo caso limite in §6, criterio 9, fasi e test aggiornati. DA-B2-07 in §6; DA-E1-05 (traceparent e nomi GenAI semconv come vocabolario, scelta di E1) in §4; DA-E1-02 in §7; DA-C1-01/05 in §9 e §11; DA-E3-08/09 in §10. Taglia invariata (L). Motivo: allineamento a DECISIONS.md. |
