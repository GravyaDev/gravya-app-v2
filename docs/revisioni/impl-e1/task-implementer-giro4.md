# Task per l'implementer, giro 4: correzioni dopo il RIPORTA della terza revisione

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente: «ok» al punto 1 del coordinator (giro 4 piccolo e mirato, poi verifica del code-reviewer sulle sole modifiche).

Stesso documento (E1 v1.6), perimetro, worktree `/workspace/wt-impl-e1`, branch `claude/impl-e1` (ora `b4f7b44`; `git pull --ff-only`). Valgono i task dei giri precedenti salvo quanto cambia qui. Fonti: `report-code-reviewer-giro3.md` (prove in `code-reviewer-giro3/`, 7 falliti su 13), `report-compliance-auditor-giro3.md`.

## Criterio di fine
1. Passano `tests/` (10 esecuzioni consecutive), le prove dei giri 1 e 2 con gli stessi esiti di oggi (39 + errore di teardown noto; 35 + 12 attesi) e `code-reviewer-giro3/` salvo i falliti attesi elencati sotto; `scripts/test-non-superuser.sh` OK.
2. Nessun file lasciato in `/tmp` dai test o dagli script (controlla prima e dopo una corsa).
3. Report: sottosezione «Giro 4» in coda, rilievo per rilievo con il test che lo prova, e la tabella dei test di `code-reviewer-giro3/` con lo stato.

## Correzioni
1. **Rete bloccata dopo la connessione (CR N2).** Timeout lato client sulla connessione del thread di scrittura: `tcp_user_timeout` di libpq da una nuova variabile `e1.write_tcp_user_timeout_ms` (stato «da definire», valore di sviluppo dichiarato, bloccata in produzione), più eventuale controllo applicativo del tempo massimo di un job. Test N2 deve passare.
2. **`close()` appeso (CR N3).** Nessuna operazione bloccante senza timeout in `close()`; il `timeout` di `close()` vale per tutto lo spegnimento; i job rimasti in coda allo spegnimento sono contati come persi e segnalati (CA minore). Test N3 deve passare.
3. **Segnali non bloccanti (CA G3-01).** I segnali passano da una coda con thread proprio e connessione propria con gli stessi timeout della scrittura (connect, statement, tcp_user_timeout, keepalive); nessuna emissione sul thread del chiamante tocca il database. Coda dei segnali piena: log di ripiego. Test con connessione bloccata: il chiamante non aspetta.
4. **Ruolo con BYPASSRLS (CA G3-02).** Dopo `ALTER FUNCTION ... OWNER TO gravya_e1_so_owner` revoca l'appartenenza del ruolo di migrazione (`REVOKE gravya_e1_so_owner FROM ...`) e il `CREATE` su `public`; nessun `EXCEPTION WHEN OTHERS THEN NULL`: almeno `RAISE WARNING` e, dove l'operazione è necessaria, errore. Se una migrazione futura deve ricreare la funzione, documenta nel report come (concessione temporanea nella migrazione stessa e revoca alla fine). Test: dopo le migrazioni il ruolo di migrazione non può fare `SET ROLE gravya_e1_so_owner`.
5. **Segnali da non superuser (CA G3-03).** Test (e verifica nello script non superuser) con `PostgresSignalSink` da un ruolo non superuser membro di `gravya_writer`: l'INSERT riesce, il SELECT è negato. Policy dei segnali (CR minore): `WITH CHECK` sul tenant del GUC (`tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid`), così il writer non inserisce segnali a nome di un altro tenant; il sink imposta il GUC del tenant del segnale nella propria transazione.
6. **Minori.**
   - Confronto del tenant di contesto su UUID canonici, non su stringhe (CR N9).
   - `e1.write_connect_timeout_ms`: niente arrotondamento silenzioso (CR N11, CA). Valida che il valore sia un multiplo di 1000 (libpq accetta secondi interi) oppure rinomina la variabile in secondi; scegli e dichiara. Nessun `max(1, ...)`.
   - File temporanei (CR N13, CA): `tmp_path` nei test, `TemporaryDirectory` nello script; nessun file in `/tmp` alla fine.
   - Script non superuser: nel cleanup `DROP OWNED BY` e `DROP ROLE` del ruolo di prova (CA).
   - `API_ENV` (CA): valori ammessi in un insieme chiuso (`production`, `development`, `test`); un valore fuori insieme blocca l'avvio con segnale (non diventa «sviluppo»). Assente resta «sviluppo» con segnale, come deciso.
   - `MIGRATION_ROLE` in `migrations/env.py`: identificatore quotato o validato.
   - Nome della chiave scartata nei segnali (CA minore): solo le chiavi note della whitelist; per le altre solo la lunghezza.
   - CI (CA): build senza isolamento o strumenti di build fissati nel lockfile; niente `apt-get` non fissato se il client non serve.

## Falliti attesi ammessi in `code-reviewer-giro3/`
- `test_N4` (oracolo di esistenza del `trace_id` tramite il GUC): limite intrinseco di un controllo di unicità, da dichiarare in E1 v1.7. Correggi nel report l'affermazione del giro 3 che l'oracolo è «chiuso».
- `test_N10` (helper con `production_override` senza contesto scrive due tenant): conseguenza della scelta del coordinator (obbligo solo con `API_ENV=production` reale).
Ogni altro test di `code-reviewer-giro3/` deve passare. Se uno contraddice il task o una decisione, fermati e chiedi. Nessuna modifica ai file di prova dei revisori, salvo l'aggiunta delle variabili nuove alle fixture di istantanea (commit separato, citato nel report).

## Regole
Commit piccoli, push, niente merge. Non modificare `docs/` salvo il report e le fixture di istantanea come sopra. Nessun file fuori dal worktree.
