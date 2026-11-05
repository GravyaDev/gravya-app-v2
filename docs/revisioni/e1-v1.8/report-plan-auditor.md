# Report plan-auditor: E1 v1.8 e catalogo v1.6 (branch claude/docs-ondata-1)

Esito: **RIPORTA**. Nessuna violazione di un PV o di una riga «Decisa». Sono chiusi quasi tutti i rilievi di v1.7. Restano 2 punti che richiedono una scelta o una registrazione, più incoerenze minori tra E1, catalogo e codice.

## Letture
- docs/E1-tracing-distribuito.md v1.8: 1-292 di 292.
- docs/revisioni/e1-v1.8/task-auditor.md: 1-17 di 17.
- docs/revisioni/e1-v1.7/report-compliance-auditor.md: 1-62 di 62. Il mio report v1.7 non è stato riletto; ho usato la sintesi nel task.
- docs/catalogo-variabili.md v1.6: 1-30, 154-172, 338-348, 381-382, 440-457, 494-502 di 502 (grep sul resto per E1, `e1.`, HMAC, API_ENV, deroga, DX-07). Non letti §2-§8, §10-§15, §17.2, §19: **lettura parziale**.
- docs/DECISIONS.md: 1-120 (letto prima), 210-214, 288-296 di ~320 (grep per DA-E1-13 e righe del 2026-11-05 su E1). Non letti §3 e §5: **lettura parziale**.
- docs/PRINCIPI.md: 1-15 di 15.
- /workspace/wt-impl-e1 (sola lettura): `migrations/versions/0006_giro4_fixes.py` 1-100 di 100; `config/variables.py` 1-230; `tracing.py` 85-100 e 360-420; `scripts/test-non-superuser.sh` solo grep; `report-implementer.md` 868-925 e grep. Non ho rieseguito i test. `git diff` non eseguibile (nessuno strumento shell): i confronti con v1.7 sono sul testo letto nella revisione precedente.
- Master plan non letto (il template è quello già usato).

## 1. Rilievi v1.7: stato

### Chiusi
- **R1 e CA D-01 (segnali e C2).** Chiuso: E1 §3, §4.1, §5 (deroga ondata 1), §7 e catalogo §18 r.442 coincidono con DECISIONS r.290.
- **R2 (timeout lato server/client).** Chiuso: E1 §5 e §11 distinguono il server (`e1.write_statement_timeout_ms`) dal client; il catalogo dice «lato server»; il codice conferma.
- **R3 («vocabolario chiuso»).** Chiuso in §4.2, §4.3, §8 criterio 4, §11. §7 mantiene una frase attenuata che rimanda al limite, accettabile.
- **R4 (DA-E1-13).** Chiuso: E1 App. C r.277 corrisponde a DECISIONS r.118 (opzioni (a)+(b), (c) solo ondata 1).
- **R7 (variabile «da definire» mancante).** Chiuso: E1 §5, §6, criterio 17 coincidono con DECISIONS r.292.
- **R8, R9 (testi obsoleti SHA-256 e credenziali, criterio 9).** Chiusi. Il criterio 9 ora è testabile.
- **CA D-02 (ruolo di migrazione e `BYPASSRLS`), D-03 (policy segnali permissiva), D-04 (regola 11), D-05, D-06, D-07, D-08.** Chiusi nel testo: E1 §5 e App. B, catalogo regola 11 (r.25), §18 r.451.
- **Storico di E1:** righe 1.0-1.7 invariate nel contenuto (confrontate con /tmp/s8/E1-storico-v16.txt e con il testo v1.7 letto prima); una sola riga nuova (1.8). Verificato per lettura, non per diff.

### Ancora aperti o chiusi solo in parte
- **R5 (valori fissi): chiuso nel catalogo, ma E1 non è aggiornato.** Vedi N1.
- **R6 (tenant di contesto, `API_ENV`): registrato in DECISIONS r.291 e citato da E1, ma il catalogo non è allineato.** Vedi N2 e N3.
- **R11 (catalogo obsoleto): aperto.** Vedi N4.
- **R10 (contratto e implementazione mescolati): attenuato, residuo in N5.**

## 2. Rilievi nuovi

### N1 (da_riportare, verificato). E1 App. B dice ancora che formati e chiave non sono nel catalogo
- E1 App. B (r.243): «La lunghezza minima di 32 byte è provvisoria fino ad A6 ed è nel codice, non nel catalogo». App. B (r.253): «Valori fissi nel codice. I formati numerici ... e la lunghezza minima della chiave HMAC ... non sono nel catalogo §16-§18 con una riga propria: se siano invarianti o variabili (DX-22) è da decidere con A6».
- Catalogo §18 r.451 (v1.6) ora contiene i formati della whitelist e «lunghezza minima della chiave HMAC di 32 byte (provvisoria fino ad A6, DECISIONS §6)» come invarianti.
- Problema: E1 e catalogo si contraddicono. Il catalogo classifica come invarianti valori che E1 dichiara non classificati. Per la chiave minima non c'è nessuna riga DECISIONS che la dichiari invariante (r.284: «provvisoria fino ad A6»). Va scelta una versione: o E1 recepisce la classificazione provvisoria del catalogo, o il catalogo marca la riga come «da decidere con A6». §16 non ha righe.

### N2 (da_riportare, verificato). Insieme chiuso di `API_ENV` e segnale `e5.environment_invalid`: scelta del coordinator non registrata, effetto sulla sicurezza
- E1 §5: «un valore di `API_ENV` impostato ma fuori dall'insieme chiuso (`production`, `development`, `test`) non blocca l'avvio, è trattato come sviluppo e produce il segnale `e5.environment_invalid`». Stesso testo in criterio 17 e App. B r.257: «un valore scritto male in produzione disattiva le garanzie legate alla produzione senza bloccare l'avvio».
- DECISIONS r.291 registra solo «tenant di contesto obbligatorio solo con `API_ENV=production` reale». L'insieme chiuso e il segnale non sono in nessuna riga decisa. Il report dell'implementer r.905 li attribuisce a «decisione del coordinator» presa per non rompere un test bloccato dal giro 1.
- Catalogo §18 r.446: guardia `API_ENV=production` per «B1, E3, A6». Non cita E1, il tenant di contesto né l'insieme chiuso.
- Problema: una guardia di deploy (invariante, DX-22 D2 (b)) che, scritta male, si spegne silenziosamente tocca PV-01 (priorità alla conformità). La scelta tra «segnala e prosegue» e «blocca» spetta all'utente, non al coordinator. E1 dichiara il limite in App. B, ma la scelta di non bloccare non ha una riga decisa.

### N3 (minore, verificato). Il catalogo non cita E1 né il tenant di contesto nella guardia di ambiente
- Vedi N2: catalogo §18 r.446 e §16 r.320 elencano solo B1 ed E3. E1 §5 e criterio 17 rimandano a «catalogo §18» come fonte dell'invariante. DECISIONS r.291 indica «E1, catalogo §18» come documenti da aggiornare. Il catalogo non è stato aggiornato in questo punto.

### N4 (minore, verificato). Residui obsoleti nel catalogo v1.6
- Catalogo r.29 («Assunzione sui nomi»): «La convenzione dei nomi (DX-07) è ancora aperta»; §17.1 punto 1 (r.365): «I nomi dipendono da DX-07 (aperta in DECISIONS §1)». DX-07 è **Decisa** (F2, 2026-11-04).
- Regola 6 (r.20): «(questa versione: v1.5)» riferita al registro delle norme, mentre la testata dice registro v1.6.
- Storico 1.6: «tolti i riferimenti alle fasi di lavoro». Le righe di §9 (r.163-168) citano ancora «implementazione su `claude/impl-e1`»; r.162: «proposta di E1 v1.5».
- Regola 4 (r.16-18): «i segnali vanno nella tabella di audit minima ... il blocco non è mai silenzioso» e punto (3) «esclusi dal blocco la produzione e la conservazione dei segnali». Non richiamano la deroga dell'ondata 1 di §18. Nessun testo falso, ma la regola 4 non rimanda alla deroga.

### N5 (minore, verificato). Residui nel contratto E1 e nel codice (non errori di E1)
- **Migrazione 0006 (punto 3 del task).** E1 §5 e il report dell'implementer (r.912, «Scoperta durante la verifica») sono coerenti con `scripts/test-non-superuser.sh` (r.93-94 e r.124-126: la concessione `CREATE` su `public` al proprietario esiste durante la migrazione ed è revocata dal deploy). Sono incoerenti: il docstring di `0006_giro4_fixes.py` (r.22-26: «Rimosso anche il GRANT CREATE ... non serve») e l'intestazione dello script (r.13-15: «non gli serve»). Il docstring è sbagliato rispetto al codice e a PostgreSQL. E1 è corretto. Va corretto il docstring, non E1.
- **Revoca best-effort.** `0006` fa `REVOKE gravya_e1_so_owner FROM gravya_migrator` dentro `EXCEPTION WHEN OTHERS ... RAISE WARNING`: solo l'appartenenza, non `CREATE` su `public`. E1 §5 dice «la migrazione tenta la revoca dell'appartenenza e, se non ha i privilegi, emette un avviso visibile»: corretto. Non dice però che la revoca di `CREATE` non è mai tentata dalla migrazione, né che la pulizia è reale solo nello script di prova (non in una procedura di deploy). App. B r.256 dichiara la procedura «proposta, non approvata»: sufficiente, ma una frase esplicita eviterebbe l'equivoco. Le formule di §5 «entrambe le concessioni vanno revocate» sono un requisito, non un fatto implementato.
- **`e1.write_tcp_user_timeout_ms` non è in `_EXPECTED_INT_VARIABLES`** (`config/variables.py` r.58-70). Il catalogo promette «validità tecnica (intero ≥ 1)» per questa variabile; il codice non impone intero e minimo 1 come per le altre. Va segnalato al code-reviewer.
- **`e1.write_connect_timeout_ms`.** Catalogo r.164: «il valore è passato al driver senza arrotondamento» (float in secondi, ad esempio 0.4). Dedotto, non verificato: libpq documenta `connect_timeout` in secondi interi; che un valore frazionario sia accettato e rispettato dal driver non è provato. La regola di conversione che la revisione di conformità aveva chiesto è stata sostituita da questa affermazione. Va marcato come non verificato in E1 App. B o nel catalogo.
- **Due nomi per la stessa destinazione dei segnali.** E1 §2 e §8 criterio 7 parlano di «tabella di audit minima», §3, §4.1, §5 e criterio 4 di «tabella provvisoria dei segnali». DECISIONS §6 la chiama «tabella di audit minima». Va chiarito se sono la stessa tabella (dedotto che lo siano).

### N6 (minore, dedotto). Dipendenza di DA-E1-13 dai cataloghi di B1 e B2 non dichiarata in E1 §3 e §12
- DA-E1-13 (a) richiede «valori dai cataloghi esistenti per modelli, provider, strumenti e agenti (B1, B2)». E1 §3 non elenca questa dipendenza e §12 «Dipendenze critiche» non la cita. E1 App. B r.252 dice «I cataloghi ... non sono ancora redatti come elenchi chiusi». Il passo 1 di §9 non prevede il lavoro con B1 e B2.
- Inoltre la parte (b) (UUID per gli identificativi generati da Gravya) richiede che B1, B2 e C1 li emettano come UUID: nella tabella provvisoria `execution_ticket_id`, `workflow_id`, `gen_ai.agent.id` e altri sono ancora «prefisso_corpo» e la colonna «Da confermare con» non menziona il passaggio a UUID.

## 3. Coerenza E1-catalogo (punto 2 del task)
- **Timeout lato server/client:** coerente (E1 §5, §11; catalogo r.163-168).
- **Regola 11:** coerente: il catalogo r.25 elenca `e1.write_buffer_size` e le `e1.write_*`; E1 §5 e App. B r.249 le dicono «da definire» con valore di sviluppo ammesso solo fuori produzione. Le nove variabili `e1.*` di E1 §5 hanno tutte una riga in catalogo §9 e §12.
- **Formati e chiave minima in §18:** presenti nel catalogo, E1 non aggiornato (N1).
- **Deroga C2:** coerente (E1 §5, §7; catalogo §18 r.442; DECISIONS r.290).
- **Altre dipendenze tra documenti dell'ondata 1** (A1, B1, B2, C1, C3, E2, E3 alla v1.6, non allineati a F2): confermo le divergenze del report v1.7 (C3 `company_id` e `hitl_expired`, B2 senza `gravya.tool.outcome`). Sono lavoro da fare, non errori di E1.

## 4. Controllato
- Nessun OpenTelemetry come SDK o export; nessun servizio extra-UE; retention solo per rimando a `retention.*`; nessuna stima temporale (solo taglia M); sezioni 1-12, Appendici A-C e Storico in ordine.
- DA-E1-13: testo E1 App. C coerente con DECISIONS r.118. Le righe del 2026-11-05 (r.290-292) sono recepite in E1 nel contenuto, con le formule di §5, §6, §7 coerenti con la deroga, il tenant di contesto e l'avvio senza variabile.
- Il testo di E1 non dichiara come implementato ciò che App. B definisce non verificato: «implementati in revisione e non uniti» (§9), «controllati sul codice solo formati, segnali, avvio, `close()`, migrazione 0006» (App. B r.261).
- Il codice conferma: tenant di contesto obbligatorio solo con `API_ENV=production` esatto (`tracing.py` r.371-377); `e5.environment_invalid` solo con `production_override` assente (r.397-410); `da_definire` in produzione blocca la lettura e emette un segnale (`variables.py` r.156-164); insieme chiuso `production`, `development`, `test` (`config/env.py` r.18).

## Domande per l'utente
1. N2: un valore di `API_ENV` scritto male (per esempio «prod») deve bloccare l'avvio, o resta «segnala e prosegue come sviluppo»? Va registrato in DECISIONS in ogni caso.
2. N1: formati numerici della whitelist e chiave HMAC minima: invarianti provvisorie (come ora nel catalogo §18), o da riclassificare con A6?
