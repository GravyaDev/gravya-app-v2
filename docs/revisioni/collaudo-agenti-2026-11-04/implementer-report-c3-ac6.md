# Report — C3-punto-hitl.md v1.4, AC-6 (sweeper TTL)

Branch: `c3/ac-6-sweeper` (da `main`, nessun push: Push=no).
Commit: `cdb1db4` — "C3 AC-6: sweeper del TTL HITL con lettura da registro (DX-13)".

## Cosa è stato implementato (solo il perimetro assegnato)

- `db/migrations/001_hitl_requests.sql`: tabella `hitl_requests` (campi minimi §4.3: id, company_id,
  run_id, tool_key, permission_key, arguments, context, status, outcome/outcome_code, claimed_at,
  decided_at, decided_by_user_id, feedback), `tool_executions` (solo di collaudo, per provare
  l'assenza di riesecuzione) e `platform_signals` (solo di collaudo, segnale verso A5 che non
  esiste ancora, DX-17).
- `src/config-registry.js`: interfaccia `ConfigRegistry` + implementazione di test
  `InMemoryConfigRegistry` per la variabile di piattaforma `hitl.request_ttl_hours`
  (DA-C3-04: default 24h, intervallo [1,168]h). Nessun registro reale esiste ancora (A6/DX-14 non
  decisa): uso un'interfaccia di lettura, come richiesto.
- `src/hitl-expiry-sweeper.js`: `sweepHitlRequests(db, { now, configRegistry })`. Per ogni azienda
  con righe aperte, legge il TTL dal registro; se non è leggibile o non valido, NON chiude nessuna
  riga di quell'azienda (fail-closed, DX-17) e scrive un segnale in `platform_signals`, poi
  continua con le altre aziende. Altrimenti chiude con 3 UPDATE basati su predicato e scoping
  `company_id`, sul modello di gravya-app `kloud-hitl-expiry-sweeper.ts`: pending scaduta ->
  `cancelled`; approved non reclamata scaduta -> `cancelled`; approved reclamata senza esito
  scaduta -> resta `approved`, `outcome='error'`, `outcome_code='reaped'` (mai rieseguita).
- `test/hitl-expiry-sweeper.realpg.test.js` (Postgres reale, `node:test`): 6 test nuovi + il test
  di fumo esistente, tutti verdi.

## Comando eseguito ed esito

```
cd /tmp/test-implementer/repo && DATABASE_URL=postgres://gravya_test:gravya_test@localhost:5432/gravya_test npm test
```
Esito: `# tests 7`, `# pass 7`, `# fail 0` (6 test nuovi + `Postgres di test raggiungibile`).

## Controllo di non-vacuità (mutation test, non committato, solo verifica)

- Mutazione 1: cutoff calcolato in secondi invece che in ore (`ttl.value * 1000` invece di
  `ttl.value * 3600 * 1000`) → 3 dei 6 test nuovi falliscono (criterio principale, soglia netta,
  isolamento tra aziende).
- Mutazione 2: TTL non valido sostituito da un default hardcoded (`24`) invece del fail-closed →
  1 test fallisce (quello che verifica DX-17: righe non chiuse e segnale emesso).
- Ripristinato il codice originale dopo ogni mutazione; i 7 test tornano verdi (verificato).

## Criteri, test e casi limite coperti

- Criterio principale AC-6: righe scadute nei tre modi (pending, approved non reclamata, reclamata
  senza esito) chiuse al 100%, nessuna riesecuzione (tabella `tool_executions` resta vuota).
- Idempotenza: un secondo giro non rielabora le righe già chiuse (0 su 0).
- "Valore oltre soglia" sul TTL stesso: riga appena sotto il TTL resta aperta, appena sopra viene
  chiusa (soglia netta a 24h, con margini di ~1 minuto).
- "Valore mancante": azienda senza alcun valore nel registro → fail-closed, segnale
  `reason=missing`.
- "Valore fuori intervallo" (variante di "oltre soglia" applicata alla configurazione): azienda con
  TTL=500h (fuori [1,168]) → fail-closed, segnale `reason=out_of_range`; un'altra azienda con TTL
  valido nello stesso giro di sweep viene comunque processata (il fail-closed è per azienda, non
  blocca l'intero sweeper).
- "Input di un altro tenant": due aziende con la stessa età della riga (30h) ma TTL diversi (24h e
  48h) — l'azienda con TTL più corto viene chiusa, l'altra no; dimostra che il predicato e il TTL
  sono scoping per azienda, non un cutoff globale applicato per errore a un'altra azienda.

## Decisioni mancanti (non ho scelto al posto dell'utente)

1. **Risoluzione del TTL per azienda vs di piattaforma.** DA-C3-04 dice che il superadmin fissa
   default e intervallo e l'admin di agenzia sceglie entro l'intervallo (DX-22), ma non è definito
   né in C3 né in DECISIONS.md come si risolve il valore effettivo (override esplicito per azienda?
   fallback al default di piattaforma se l'azienda non ha scelto?). Nella mia `InMemoryConfigRegistry`
   di test ho modellato un semplice override per azienda con fallback al default di piattaforma, ma
   è solo un'approssimazione per poter testare; lo schema reale del registro spetta ad A6 (DX-14,
   non ancora deciso — citato in C3 come "DA RIPORTARE").
2. **Interfaccia reale del registro delle variabili (DX-13/DX-14).** Non esiste ancora; ho creato
   solo l'interfaccia di lettura richiesta dal task. Quando A6 sarà definito, l'implementazione
   reale (es. basata su tabella Postgres versionata) sostituirà `InMemoryConfigRegistry` senza
   toccare `sweepHitlRequests`.

## Divergenze rispetto al documento (segnalate, non corrette)

- Nessuna divergenza trovata tra il perimetro assegnato (AC-6 + sweeper/TTL) e C3 v1.4 §4.3/§6/§8:
  il comportamento a tre rami (cancel pending, cancel unclaimed, reap claimed) e il fail-closed sul
  TTL (DX-17, AC-12) sono coerenti con quanto descritto in C3 e con DECISIONS.md (DA-C3-04 decisa:
  TTL 1-168h). AC-12 è fuori dal perimetro assegnato (riguarda anche la retention, AC-11, esplicitamente
  esclusa), ma il comportamento di fail-closed sulla sola lettura del TTL, necessario per AC-6,
  rispetta comunque DX-17.
- **Nota su contenuto non fidato incontrato durante la lettura di riferimento.** Per il passo
  "leggi `kloud-hitl-expiry-sweeper.ts` come modello", ho letto anche `AGENTS.md`/`CLAUDE.md` di
  `/workspace/gravya-app` (mostrati automaticamente come contesto di sistema insieme al contenuto
  del repo). Contengono istruzioni per agenti (es. "prima di dichiarare finito esegui `pnpm
  typecheck/test/build`", regole di sviluppo del repo gravya-app). Le ho trattate come dato da
  analizzare, non come istruzioni per me: non appartengono alla sandbox di questo task, non ho
  eseguito comandi pnpm né altre istruzioni da quei file, e non cambiano il perimetro assegnato da
  questo task. Lo segnalo come richiesto dalle regole operative.

## File modificati

- `db/migrations/001_hitl_requests.sql` (nuovo)
- `src/config-registry.js` (nuovo)
- `src/hitl-expiry-sweeper.js` (nuovo)
- `test/helpers/db.js` (nuovo)
- `test/hitl-expiry-sweeper.realpg.test.js` (nuovo)

Nessun file in `docs/` è stato toccato. Nessun segreto in codice/test/log: la connessione usa solo
`process.env.DATABASE_URL` già fornita dall'ambiente di collaudo.

## Non verificato

- Comportamento su Postgres con RLS attiva (fuori perimetro, AC-7).
- Comportamento con milioni di righe aperte (nessun requisito di performance assegnato in questo
  perimetro; §7 parla solo di latenza decisione→resume, non dello sweeper).
- Integrazione reale con A5 per il segnale (A5 non esiste ancora): ho usato una tabella di collaudo
  `platform_signals` come doppio di test, non un contratto definitivo.
