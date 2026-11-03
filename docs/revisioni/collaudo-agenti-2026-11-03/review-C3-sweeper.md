# Report revisione PR feature/c3-hitl-sweeper (base main) — documento C3 v1.4

Esito: **BLOCCA**

## Esecuzione test
- `node --test test/` (comando indicato dal task): **fallisce** con `Cannot find module '/tmp/test-code-reviewer/repo/test'` (Node v22.22.0 tratta `test/` come modulo). Problema di invocazione, non del codice.
- `node --test` (senza argomento) e `node --test test/sweeper.test.js`: 1 test, 1 pass, 0 fail.
- Prove aggiuntive: script `node --input-type=module -e` con casi limite sullo sweeper (nessun file scritto nel repo).

## Criteri di accettazione interessati (la PR dichiara AC-6 e AC-12)
| ID | Test | Verifica reale | Esito |
|---|---|---|---|
| AC-6 (100% righe oltre TTL chiuse, senza rieseguirne, Postgres reale) | `test/sweeper.test.js::lo sweeper restituisce tutte le richieste` | **No.** Controlla solo `out.length === 2`. Le righe del test hanno createdAt = now-1000 ms, quindi nessuna è oltre il TTL: il test passerebbe anche con uno sweeper che non fa nulla. Nessun Postgres, nessun controllo sui `status`. | non soddisfatto |
| AC-12 (TTL dal registro DX-13; valore assente/illeggibile → non chiude e segnale) | assente | n/a | non soddisfatto: nessuna lettura dal registro, nessun segnale |
| AC-1..5, 7..11, 13 | assenti | — | fuori dalla PR (non dichiarati), nessun rilievo |

## Rilievi
1. **BLOCCANTE — DX-22 / DX-13 / AC-12 / DX-17.** `src/hitl/sweeper.js:2` `const REQUEST_TTL_HOURS = 24;` è hardcoded. Il documento §6/§7 impone la variabile di piattaforma `hitl.request_ttl_hours` letta dal registro; DX-22 vieta valori hardcoded. Non esiste né lettura del registro né ramo per valore assente/non valido (nessun blocco, nessun segnale ad A5). Verificato.
2. **BLOCCANTE — AC-6 testato solo in apparenza.** Il test non verifica nessuna transizione (vedi tabella). Il commit message dichiara "AC-6, AC-12" ma nessuno dei due è coperto. Verificato.
3. **BLOCCANTE — §6 Scadenza: righe `approved` non reclamate non vengono chiuse.** Il doc dice: "pending o approvata ma non reclamata diventa cancelled". Prova: `{status:'approved', createdAt: now-48h}` senza `claimedAt` resta `approved` per sempre (riga id 2 nella prova). Il codice cancella solo `pending`. Una riga approvata e mai reclamata resta eseguibile oltre il TTL (rischio per AC-1/AC-6: "100% delle righe oltre TTL"). Verificato.
4. **BLOCCANTE — input malformato o incompleto resta aperto in silenzio, senza segnale.** Righe senza `createdAt` o con `createdAt:'abc'` danno confronto NaN → restano `pending` per sempre (prove id 7 e 8). Non è fail-closed con segnale (DX-17, AC-12). `sweep(null)` solleva `requests is not iterable` senza segnalazione. Verificato.
5. **DA RIPORTARE — il TTL conta da `createdAt`, anche per le righe approvate.** Il doc non precisa la base temporale (creazione o decisione/claim). Per un claim fresco su richiesta vecchia, `error/reaped` scatta subito. Da chiarire nel doc.
6. **DA RIPORTARE — contratto dei campi.** §4.3 definisce `status`, `claimed_at`, `outcome` (`ok/refused/error` + codice), snake_case. Il codice usa `createdAt`, `claimedAt` (camelCase), `status:'error'` (non previsto: lo stato è `pending→approved/rejected/cancelled`) e `reason:'reaped'` al posto di `outcome=error` con codice `reaped`. Il doc cita `error/reaped` come outcome, non come status. Il campo è rinominato/spostato. Verificato.
7. **MINORE/DA RIPORTARE — operazione solo in memoria.** La funzione è pura sugli array: nessun UPDATE condizionale sulla riga (§7 Idempotenza: "si applica alla riga attraverso un UPDATE condizionale"), nessun filtro `company_id`/RLS, nessun record di traccia E1 per transizione (AC-9, §7), nessun evento `hitl_expired`, nessun collegamento a C4. Non esiste persistenza, quindi AC-6 su Postgres reale non può essere soddisfatto da questa PR. Il sweeper non esegue mai i tool (corretto, "non riesegue") ma il vincolo non è garantito da test. Dedotto.
8. **Nota.** Il comando di test del task (`node --test test/`) non funziona su Node 22; `package.json` ha `node --test` senza argomento. Verificato.

## Tentativi di rottura
- Riga pending > TTL: chiusa `cancelled` (ok). Riga a esattamente 24h: resta pending (confine `>`, ok ma non testato).
- Approvata non reclamata oltre TTL: NON chiusa (rilievo 3).
- Approvata con claim senza outcome: `status:'error', reason:'reaped'`, non rieseguita (ok, ma non testato).
- Approvata con outcome ok: invariata (ok).
- Input di altro tenant (`companyId:'B'`): trattato come qualsiasi altra riga, nessun filtro tenant (nessuna nozione di tenant nel codice; rilievo 7).
- TTL: nessuna variabile/registro, nessun fail-closed né segnale (rilievi 1, 4).
- Input malformato (createdAt mancante/non numerico, null): resta aperto o lancia, senza segnale.
- Segreti/OpenTelemetry/contenuti di prompt/log: nessuno nel codice (30 righe totali).
- Codice che fa più del documento: nessuna funzionalità extra, tranne il campo `reason:'reaped'` e lo status `error` non previsti da §4.3.

## Collaudo
- Modello: ritengo di essere Claude (Anthropic), famiglia/versione non determinabile con certezza — **dedotto**, non verificato (nessuno strumento di introspezione).
- Strumenti: bash, read, glob, grep, send_to_parent, risposta_code_reviewer (di schema), più accesso alla memoria in /mnt/memory (non usato: ricerca non necessaria in sandbox; in `/mnt/memory/gravya` ho solo listato i nomi dei file, non li ho letti).
- Strumento `risposta_code_reviewer`: presente; l'ho usato per la risposta finale se l'invocazione va a buon fine (vedi messaggio al coordinatore).
