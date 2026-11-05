# Revisione di conformità: B2, C1, C3 alla v1.5

Revisore: compliance-auditor · Data: 2026-11-04 · Commit c010ae8 · Registro norme: v1.6 · Esito: **RIPORTA** (nessuna violazione reale di una norma del registro, di PV-01/PV-02 o di una riga decisa di DECISIONS; 6 rilievi da riportare, 5 minori).

*verificato* = riscontrato sul testo dei documenti, di DECISIONS o del registro. *dedotto* = ragionamento mio. Non riproposti: i punti già «Da riportare» in DECISIONS §4 (intervalli min/max, TTL dei token, canali CSIRT, ambito NIS2, mappa degli pseudonimi, DA-CV-08, ecc.).

## 1. Rilievi

### R1 · da_riportare · AI Act art. 50(2) e (4), DA-CV-18, PV-01: l'etichetta e l'approvazione sono imposte solo dal validatore statico sui nodi `tool`
- **Dove:** C1 §4.4 punti 2 e 5; B2 §4 (catalogo) e §6; C1 §2 (nodi agente con ciclo di tool in B1).
- **Testo:** C1 «se il contenuto di un nodo `agent` raggiunge un nodo `tool` con `audience` `person` o `third_party`, anche l'`input_schema` di quel nodo richiede `ai_generated`»; B2 «Un tool `outbound_to_third_parties` senza `ai_generated_output` dichiarato non si registra nel catalogo» e «Non verifica consensi di marketing né applica etichette art. 50».
- **Problema:** DECISIONS §6 decide che dentro B1 girano i nodi agente «con il loro ciclo di tool». Un agente che nel suo ciclo chiama un tool verso terzi passa da B2 ma non da un nodo `tool` di C1: le regole di §4.4 (propagazione di `ai_generated`, `hitl` a monte di `ALWAYS_HITL`/`MONEY_WRITE`) non lo vedono. B2 controlla solo la dichiarazione del flag in catalogo, non che l'argomento della chiamata porti `ai_generated` o la marcatura. Per `ALWAYS_HITL`/`MONEY_WRITE` regge l'approvazione di A3/B2 (token monouso). Per i contenuti verso terzi, dove l'approvazione la decide l'admin agenzia (DA-CV-18) e può essere falsa, l'etichetta «non disattivabile» (invariante) non ha alcun punto di controllo a runtime: il contenuto AI può arrivare a un terzo senza etichetta. Dove si imponga l'approvazione dipende da DX-05, aperta.
- **Proposta:** B2 rifiuta a runtime (`denied`) una chiamata a un tool `outbound_to_third_parties` o `ai_generated_output` se `args` non porta `ai_generated` con `model` e `prompt_ref`; C1 dichiara che le regole di §4.4 valgono anche per il ciclo di tool dei nodi agente, imposte da B2.
- **Verifica:** dedotto (dal testo dei documenti).

### R2 · da_riportare · AI Act art. 50(1)-(2); DECISIONS §6 («non disattivabile dal tenant»): `nodes[].audience` è dichiarato nella definizione del workflow
- **Dove:** C1 §4.1 (`nodes[].audience`), §4.4 punti 2 e 4; B2 §4 (flag `outbound_to_third_parties`).
- **Testo:** «`nodes[].audience` | se `tool` | `internal` | `person` | `third_party`: chi riceve l'output del nodo; ... (nome e vocabolario *proposta*, da allineare con B2 e D1–D4)».
- **Problema:** l'autore del workflow sceglie `audience`. Dichiarare `internal` per un nodo che in realtà invia a una persona o a un terzo toglie le regole di §4.4 (etichetta e informativa 50(1)). La fonte sicura è il catalogo B2 (impostato dal superadmin). Inoltre B2 ha il flag `outbound_to_third_parties` ma nessun flag per l'interazione conversazionale con una persona (art. 50(1)): `person` e `third_party` non sono definiti in modo comune. Se gli autori sono i tenant, l'invariante è aggirabile dal tenant.
- **Proposta:** il validatore deriva `audience` dal catalogo B2 (campo del tool) e rifiuta una dichiarazione meno restrittiva; B2 aggiunge un flag di interazione diretta con persone; un solo vocabolario in B2 e C1.
- **Verifica:** dedotto.

### R3 · da_riportare · GDPR art. 28(2) e (4), considerando 81; DA-CV-19: autorizzazione del sub-responsabile impostata dal superadmin per tutte le agenzie
- **Dove:** B2 §4 («Fatti sulla destinazione, impostati dal superadmin con fonte e audit») e §6 punto 2.
- **Testo:** «sub-responsabile autorizzato con riferimento al DPA e data»; «Senza autorizzazione valida del sub-responsabile (riferimento al DPA e data): `denied`, anche per una destinazione UE, che non passa dall'opt-in».
- **Problema:** l'art. 28(2) richiede l'autorizzazione scritta, specifica o generale, **del titolare**. Con un'autorizzazione generale il responsabile informa delle modifiche e dà al titolare la possibilità di opporsi (registro, riga 28(2); il seguito dell'opposizione è materia del contratto). Il campo è per destinazione, non per agenzia, e una destinazione UE non ha opt-in: un'agenzia che si è opposta a un nuovo sub-responsabile continua a vedere i suoi dati inviati a quella destinazione. Il documento non prevede né l'informativa alle agenzie alla modifica del catalogo né un blocco per agenzia. Il superadmin attesta il riferimento al DPA ma non verifica che il DPA di ogni agenzia lo copra.
- **Proposta:** evento di informativa alle agenzie quando una destinazione o un sub-responsabile è aggiunto o cambiato (con riferimento al DPA); controllo `denied` per agenzia se il tenant ha registrato un'opposizione; DA da portare all'utente insieme a DA-B2-08.
- **Verifica:** dedotto (testo del registro e dei documenti).

### R4 · da_riportare · GDPR artt. 25 e 32; isolamento tra tenant (PV-01): chiave di idempotenza senza ambito dichiarato, esito conservato
- **Dove:** B2 §6 («Idempotenza»), §4 (`idempotency_key`), criterio 15 e 6; DA-B2-03 (Redis).
- **Testo:** «retry con la stessa `idempotency_key` entro `b2.idempotency.window_hours` restituisce il primo esito senza rieseguire».
- **Problema:** non è detto che la chiave sia confinata a tenant, agente e tool, né che l'esito sia restituito solo con gli stessi `args` (stesso hash). Se lo spazio delle chiavi è globale, la chiave di un tenant restituisce a un altro l'esito (cioè dati) del primo: isolamento solo applicativo. Il criterio 6 prova l'isolamento dei record, non delle chiavi. Il §7 dice che l'audit non conserva il risultato, ma per restituire «il primo esito» il risultato (o un suo riferimento) va conservato per la finestra: cosa e dove (Redis non ha RLS, DA-B2-03) non è detto.
- **Proposta:** la chiave si compone con `tenant_id`, `tool_id` e hash degli `args`; con `args` diversi la stessa chiave è `error`; si conserva solo stato e riferimento redatto; criterio di test con due tenant e la stessa chiave.
- **Verifica:** dedotto.

### R5 · da_riportare · GDPR art. 4(5), considerando 26, art. 5(1)(e), art. 17; DA-C3-12: «poi resta l'hash» in B2 non allineato a DA-C3-12
- **Dove:** B2 §7 («anteprime redatte, `retention.sensitive_payload_days` (poi resta l'hash)»; «argomenti compaiono solo come hash»); C3 Appendice C DA-C3-12 (aperta, da riportare).
- **Testo:** C3 «un hash di argomenti a bassa entropia (email, testo breve) resta dato personale (GDPR considerando 26) e sopravvive alla cancellazione degli argomenti».
- **Problema:** DECISIONS §5 e §6 decidono «resta solo l'hash» come minimizzazione, ma un SHA-256 semplice di un indirizzo email o di una frase breve è invertibile per tentativi: dopo la cancellazione degli argomenti l'hash è un dato pseudonimo che resta per `retention.audit_decisions_months` e `retention.traces_days`, e non si cancella su richiesta dell'interessato. B2 genera gli stessi hash (audit, tracce) e non richiama DA-C3-12: la scelta (b), HMAC con chiave per tenant, vale per B2, A3 ed E1, non solo per C3. L'invariante di formato SHA-256 (DA-CV-05) non è in contrasto con HMAC-SHA-256 ma va detto.
- **Proposta:** portare DA-C3-12 all'utente come decisione comune a B2, C3, E1, A3; B2 rimanda a DA-C3-12 e dichiara l'hash dei suoi argomenti nella stessa forma.
- **Verifica:** verificato (C3 lo dice; B2 non lo riprende); dedotto (estensione a B2).

### R6 · da_riportare · DA-CV-15, DA-CV-05 (c), DA-B2-11: classificazione `ALWAYS_HITL`/`MONEY_WRITE` in catalogo e tool senza classe
- **Dove:** B2 §6 («non sono declassabili da UI (DA-CV-15)»), §5 (catalogo gestito dal superadmin), DA-B2-11 (a); C1 §4.4 punto 5.
- **Testo:** B2 DA-B2-11 «(a) il superadmin in catalogo, versionato e auditato».
- **Problema:** DA-B2-11 raccomanda che sia il superadmin ad assegnare la classe tramite l'interfaccia del catalogo. Chi assegna una classe può non assegnarla: la «non declassabilità da UI» (DA-CV-15) non regge se la classificazione è un campo di UI. Il documento non dice cosa vale per un tool senza classe di approvazione o senza `money_write` dichiarato: nel sistema di riferimento era default-deny per i tool senza tassonomia (B2 App. A), in v2 non è scritto.
- **Proposta:** un tool senza classe di approvazione esplicita è `denied` o `require_approval`; la classe è dichiarata alla registrazione e può solo essere aggiunta, non tolta, con audit e conferma di un secondo soggetto; DA-B2-11 va all'utente con questa regola.
- **Verifica:** dedotto.

### R7 · minore · DA-CV-15, DA-CV-05 (c): C3 usa `REQUIRES_HITL`, il resto del progetto `ALWAYS_HITL`
- **Dove:** C3 §6 punto 1, §7 «Sicurezza tecnica», AC-1; C3 §3 (`ALWAYS_HITL`); B2 §4; C1 §4.4.
- **Testo:** C3 «Un tool classificato `REQUIRES_HITL` o `MONEY_WRITE` nel catalogo di B2».
- **Problema:** il vocabolario chiuso della decisione è `ALWAYS_HITL`/`MONEY_WRITE`; `REQUIRES_HITL` è il nome di gravya-app. Chi implementa AC-1 dal testo di C3 testa una classe che nel catalogo non esiste, e l'invariante resta senza test.
- **Proposta:** sostituire `REQUIRES_HITL` con `ALWAYS_HITL` in §6, §7 e AC-1.
- **Verifica:** verificato.

### R8 · minore · AI Act art. 50(2) (✔); registro N-AIACT-COM; D7: marcatura applicata dopo l'approvazione e tempistica di DA-C1-07
- **Dove:** C3 §4.1 e AC-5 («marcatura compresa»); C1 §4.4 punto 3, DA-C1-07.
- **Testo:** C3 «C3 non la altera, perché gli argomenti eseguiti sono quelli approvati»; C1 «`ai_generated` ... è l'unico input da cui i connettori D1–D4 derivano la marcatura per canale».
- **Problema:** C1 dice che la marcatura la deriva il connettore dal metadato, C3 che è negli argomenti approvati e confrontata byte per byte. Se il connettore la aggiunge dopo, l'approvatore non vede il contenuto marcato e AC-5 è ambiguo. In più, il registro dice che l'art. 50 vale dal 2.8.2026 e che il 2.12.2026 non è una proroga per un sistema nuovo: DA-C1-07 (c) rinvia la scelta finché il testo del Codice non è letto, ma non indica una scadenza prima del primo rilascio in produzione.
- **Proposta:** dire dove si applica la marcatura (negli argomenti approvati o dal connettore, con hash del contenuto marcato); portare DA-C1-07 con una scadenza legata al primo rilascio in produzione.
- **Verifica:** verificato (testi); dedotto (rischio).

### R9 · minore · GDPR art. 5(1)(c) e (e), art. 25: `feedback` di C3 in classe di 12 mesi
- **Dove:** C3 §4.3 (ultimo capoverso).
- **Testo:** «`feedback` è testo libero e segue `retention.audit_decisions_months`: la card avverte di non inserirvi dati personali non necessari».
- **Problema:** gli argomenti si cancellano dopo `retention.sensitive_payload_days` (30 giorni), ma il testo libero del revisore, che può citare nomi e contenuti, resta in una classe di 12 mesi. L'avviso nella card non è una misura per impostazione predefinita (art. 25(2)).
- **Proposta:** nell'audit si conserva un motivo codificato (elenco chiuso); il testo libero segue la classe `retention.sensitive_payload_days`.
- **Verifica:** dedotto.

### R10 · minore · DA-CV-17 (testo deciso): regola del «nessun valore valido» incompleta in B2 e C3
- **Dove:** B2 §5 (ultima frase delle variabili lette); C3 §6 («Variabile non leggibile o non valida»), AC-12(d).
- **Testo:** B2 «senza alcun valore valido, per le righe 'da definire' l'azione si blocca»; DECISIONS §7 DA-CV-17: «segnali, audit e notifiche sono esclusi dal blocco; le classi di retention 'da definire' non si scrivono in produzione».
- **Problema:** i due documenti riportano la forma iniziale della regola. Senza l'esclusione, un valore mancante potrebbe bloccare la produzione dei segnali o dell'audit, contro C2. Manca anche il richiamo alla regola per le classi di retention «da definire» (segnali, audit delle configurazioni, accessi alle credenziali: DA-CV-20).
- **Proposta:** riscrivere con il testo deciso in DA-CV-17.
- **Verifica:** verificato.

### R11 · minore · GDPR art. 28(3)(g); DA-CV-12; Data Act art. 25(2): fine contratto e testi superati
- **Dove:** B2 §7 (ultima frase della voce Retention), App. B e App. C («DECISIONS e il catalogo 1.2 le registrano ancora come aperte»); C1 §7 Retention.
- **Testo:** B2 «`retention.tenant_offboarding_days` è un minimo»; C1 «periodo di recupero dei dati di almeno 30 giorni dalla fine del passaggio, poi cancellazione».
- **Problema:** B2 e C1 non citano la scelta dell'agenzia tra restituzione e cancellazione (`retention.tenant_offboarding_choice`, sempre disponibile per DA-CV-12) né il default (export per tutto il periodo di uscita), che C3 invece riporta. B2 App. B e C dicono che DA-CV-18..23 non sono in DECISIONS: ora lo sono.
- **Proposta:** aggiungere la scelta dell'agenzia e il default in B2 e C1; togliere le note superate.
- **Verifica:** verificato.

## 2. Da aggiungere al registro

1. **Codice privacy art. 130** (commi 1-5): sul testo ufficiale Normattiva (oggi ◐ su copie non ufficiali). Serve a B2 e C1 per DA-B2-10 (invii verso terzi).
2. **EDPB, Linee guida 07/2020**, parti su sub-responsabili e opposizione del titolare (oggi ◐ in estratto). Serve a R3.
3. **Codice di buone pratiche art. 50, testo** (il registro lo dà non_verificata per il numero di strati sul testo): serve a R8 e DA-C1-07.

## 3. Controllato, senza rilievi

- **Decisioni recepite in B2:** transazione unica A3+audit, coda con fsync, audit di esito fallito (coda di recupero e segnale), DA-CV-13 (token unico), DA-CV-16 (superadmin senza credenziali di agenzia), DA-CV-19 (strumento e sub-responsabile dal superadmin con fonte), strumento caduto → disattivazione e nuovo opt-in (C9, D5), DA-CV-22 e DA-CV-23 (due chiavi in parallelo), rate limit a tre livelli, segnali senza soglia locale anche con flusso NIS2 falso (C2).
- **Citazioni normative:** nessun «NIS2 (art. 21)» per i log (Reg. 2024/2690 all. 3.2 e 11), nessun «legal hold», DPF limitato all'elenco e impugnato, EDPB 01/2025 come consultazione, art. 33(2) senza ore, art. 50 dal 2.8.2026, artt. 12/14/19/26 solo buona pratica con il calendario del Reg. 2026/1744, Data Act art. 25(2) con 30 giorni come minimo: tutte coerenti con il registro v1.6.
- **PV-02 e perimetro UE:** nessun SDK o export OpenTelemetry, LangGraph senza LangSmith né Platform, esecuzione self-hosted in UE; nessun contenuto di prompt e risposte nelle tracce; argomenti solo come hash (salvo R5).
- **Marketing (PV-01 esteso):** B2 cita ePrivacy art. 13, Codice privacy artt. 122 e 130, d.lgs. 70/2003 artt. 8-9 e le linee guida sui pixel; consenso e opt-out rinviati a D1-D4 e DA-B2-10 portata all'utente; C1 e C3 dichiarano di non verificare base giuridica né consenso. Coerente con catalogo §1 regola 10.
- **C3:** HITL non aggirabile per `MONEY_WRITE`/`ALWAYS_HITL` (token monouso legato all'hash, claim esclusivo, B2 rifiuta senza token); chiusura per TTL solo verso la non esecuzione; il superadmin non decide richieste di un tenant; decisioni solo con actor `human` e MFA; fail-closed senza checkpointer; segnale al doppio resume. DA-C3-10 (chi decide) e DA-C3-12 sono segnate «da riportare all'utente».
- **C1:** `ai_generated` obbligatorio per nodo agente, informativa 50(1) come invariante, rifiuto del nodo agente senza `ai_generated`, fail-closed per tetti e per variabili, nessuno `state` nelle tracce, RLS FORCE sulle tabelle, run legato alla versione.
- **Isolamento tra tenant:** tenant solo dal token in B2, RLS sulle tabelle di C1 e C3, criteri di test di isolamento in tutti e tre (salvo R4).
- **Nomi di variabile** confrontati con il catalogo v1.2: coincidono (`dsar.assist_max_days`, `destination.<id>.subprocessor_authorization`, `b2.idempotency.window_hours_max`, `hitl.*`, `c1.*`, `retention.*`). Resta la differenza `retention.<classe>.tenant_value` (B2, C3) contro `retention.tenant.<classe>` (catalogo), già in DECISIONS §4.

## 4. Letture

- docs/B2-tool-gateway.md: 1-250 di 250
- docs/C1-grafo-workflow.md: 1-225 di 225
- docs/C3-punto-hitl.md: 1-266 di 266
- docs/revisioni/v1.5-ondata-1/brief-doc-writer-v1.5.md: 1-47 di 47
- docs/PRINCIPI.md: letto in sessione precedente, 1-15 di 15
- docs/DECISIONS.md: 1-260 di 260 salvo righe 1-123 (§1-§3, già lette in sessione precedente nella versione di 224 righe; qui rilette §4-§7 per intero, 124-260, con righe lunghe troncate a 2.500 caratteri in alcuni passaggi di §4 e §5)
- docs/norme-di-riferimento.md v1.6: 1-5, 215-262, 302-336, 597-622, 782-796 di 828; per 90-132 e 338-543 e 665-695 gli stessi blocchi letti nella sessione precedente sulla v1.5 (righe spostate di circa 8-17); non letti N-TERMINI e N-PMI (righe 713-764)
- docs/catalogo-variabili.md v1.2: solo grep dei nomi di variabile e di `audience`, `ALWAYS_HITL`, `REQUIRES_HITL`
