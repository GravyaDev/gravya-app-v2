# Collaudo PR c3/ac-6-sweeper (C3 v1.4, AC-6) — esito: BLOCCA

Data: 2026-11-04. Repository sandbox non modificato (`git status` pulito prima e dopo).
Test della PR: `DATABASE_URL=postgres://gravya_test:gravya_test@localhost:5432/gravya_test npm test` → 7 test, 7 pass, 0 fail.

## Criteri
- **AC-6** (sweeper chiude il 100% delle righe oltre il TTL senza rieseguirne nessuna): test `test/hitl-expiry-sweeper.realpg.test.js` su Postgres reale, passa. Chiude i 3 casi (pending, approved non reclamata, reclamata senza esito → error/reaped). **Verifica parziale**: la parte "senza rieseguire" non è verificata davvero (RIL-3).
- AC-12 (non in perimetro, ma il codice dichiara DX-17): copre `missing`/`out_of_range`, non il registro non disponibile (RIL-1).
- AC-7, AC-11: dichiarati fuori perimetro, non valutati. AC-9 (traccia E1 per ogni transizione): non implementata, vedi RIL-5.

## Rilievi
1. **BLOCCANTE – DX-17/AC-12, registro non leggibile.** `sweepHitlRequests` non gestisce l'eccezione di `getHitlRequestTtlHours`. Se il registro è giù: nessun segnale ad A5 e il giro si interrompe per tutte le aziende, anche quelle con TTL valido. L'interfaccia `ConfigReadFail` prevede solo `missing`/`out_of_range`, mai "non disponibile". Una riga non viene chiusa (fail-closed in senso stretto), ma DX-17 richiede il segnale e AC-12 "registro non disponibile". Il riferimento gravya-app isola l'errore per azienda (`failed++`). Prova: `prova-registro-non-leggibile.test.js::RIL-1` (verde = difetto riprodotto).
2. **BLOCCANTE – DX-17/DX-22, valore del registro non validato dallo sweeper.** La validazione dell'intervallo vive solo in `InMemoryConfigRegistry` (implementazione di test). Lo sweeper si fida di `ttl.value`: con `{ok:true,value:0}` chiude una riga di 36 s (fuori da 1–168 h, DA-C3-04). Con `NaN` va in `RangeError` non gestito, senza segnale. Prova: `RIL-2` e `RIL-2b` nello stesso file. Inoltre `HITL_REQUEST_TTL_HOURS_MIN/MAX = 1/168` sono costanti hardcoded in `src/config-registry.js:17-18`. DA-C3-04/DX-22 dicono che il superadmin fissa default e intervallo, quindi sono variabili del registro. Ogni implementazione reale dovrebbe leggerli, non usare costanti nel codice (violazione di DX-22, dedotta dal sorgente).
3. **BLOCCANTE – AC-6 non verificato davvero (test che non protegge la garanzia "non riesegue").** Il criterio è "senza rieseguirne nessuna". Il test lo controlla con `tool_executions`, tabella che nessun codice scrive, per cui l'asserzione `count = 0` è vuota. Per il resto controlla solo `status`, `outcome` e `outcome_code`, non `claimed_at`. Mutante: il reaper azzera `claimed_at` (la riga torna rieseguibile, secondo writer). L'intera suite AC-6 passa 5/5 sul mutante. Prova: `prova-mutante-claim.test.js` + `mutants/hitl-expiry-sweeper.mutant.js` (diff: una riga, `claimed_at = NULL`). Il test dovrebbe verificare che `claimed_at` e gli altri campi di claim restino invariati, o che un executor spia non sia mai chiamato.
4. **DA_RIPORTARE – inizio del TTL per le righe `approved` non reclamate.** Il codice conta da `COALESCE(decided_at, created_at)`, mentre le `pending` contano da `created_at`. Una riga creata 30 h fa e approvata 1 min fa non viene chiusa, anche se è "oltre il TTL" dalla creazione. §6 non dice da quando decorre il TTL, e il test non copre il caso (solo `decided_at` 25 h fa). Il comportamento coincide con gravya-app, ma va fissato nel documento. Verificato leggendo il codice, nessuna prova eseguita.
5. **DA_RIPORTARE – codice che fa meno o più del documento.** (a) Lo sweeper non scrive nessun record di traccia E1/audit per le transizioni (§7 Osservabilità, AC-9); il riferimento gravya-app scrive un activity log nella stessa transazione. AC-9 è dichiarato fuori perimetro, ma la PR introduce la transizione di stato senza traccia. (b) La migrazione di produzione `001_hitl_requests.sql` contiene `tool_executions` e `platform_signals`, tabelle "di collaudo" non previste da §4 (il commento lo ammette). (c) `InMemoryConfigRegistry` è esportato da `src/`, cioè dal codice di produzione. Il registro reale (A6) è "DA RIPORTARE", quindi sono scelte provvisorie.
6. **MINORE – segnali duplicati.** Per un'azienda bloccata, ogni giro inserisce un nuovo segnale in `platform_signals` senza deduplica. Se l'INSERT del segnale fallisce, l'intero giro si interrompe (stesso difetto di RIL-1). Dedotto.
7. **MINORE – `version` ignorata.** Il registro restituisce `version` (DX-13: modifiche versionate), ma lo sweeper non la registra né nel segnale né altrove. Dedotto.

## Tentativi di rottura
- Isolamento per azienda: ogni UPDATE ha `company_id = $1`, il test di isolamento con TTL diversi passa. Non ho trovato fughe. La RLS è fuori perimetro: la tabella non ha RLS né FORCE, dichiarato.
- Confini del TTL: `created_at < cutoff` (stretto, coerente con "oltre"); il test usa ±0,02 h, non il confine esatto.
- Doppio giro/idempotenza: le righe già chiuse non vengono rielaborate. Il reaper non ripete (`outcome IS NULL`).
- Race claim/sweeper: gli UPDATE sono condizionali (`claimed_at IS NULL`, `status`), nessun problema trovato.
- Registro mancante/fuori intervallo/lancia/0/NaN: vedi rilievi 1–2.
- Mutazione del reaper (rilievo 3).
- Contenuti di prompt/risposte, OpenTelemetry, SDK, segreti, URL, modelli: nessuno in `src/`. L'unico hardcoded è l'intervallo 1–168 (rilievo 2).
- Ho letto i file in cerca di istruzioni a un agente: nessuna.

## File di prova
- `prova-registro-non-leggibile.test.js` (RIL-1, RIL-2, RIL-2b): 3 test verdi, ognuno riproduce un difetto.
  `DATABASE_URL=... node --test prova-registro-non-leggibile.test.js`
- `prova-mutante-claim.test.js` + `mutants/hitl-expiry-sweeper.mutant.js` (RIL-3): la suite originale passa 5/5 sul mutante.
