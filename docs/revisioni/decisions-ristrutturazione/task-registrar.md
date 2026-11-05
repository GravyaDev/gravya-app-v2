# Task per il registrar: sostituzione di DECISIONS.md e registrazione

Preparato dal coordinator il 2026-11-05 (sessione 8).

Evento: decisione utente ed esito revisione.
Cartella: `docs/` del repository, branch `claude/docs-ondata-1`.

## 1. Sostituzione (eccezione una tantum autorizzata dall'utente)
Il candidato è stato verificato dal plan-auditor (`report-plan-auditor.md` BLOCCA, corretto; `report-plan-auditor-2.md` RIPORTA, nessuna decisione persa).
- `git mv -f docs/revisioni/decisions-ristrutturazione/DECISIONS-candidato.md docs/DECISIONS.md`
- `git mv docs/revisioni/decisions-ristrutturazione/decisioni-archivio-candidato.md docs/decisioni-archivio.md`
Nessuna altra modifica ai due file in questo passo. Non fare commit.

## 2. Registrazione nel nuovo DECISIONS.md, §6 (regole trasversali), testi dell'utente alla lettera
- 2026-11-05: «Decisions deve contenere solo quelle correnti e non anche quelle superate, altrimenti cresce indefinitamente e inoltre una lettura troncata rischia di sbagliare recupero.» e «Fanno eccezione solo regole utili per capire il motivo di una scelta senza dover ricostruire l'intero percorso logico (e in quel caso quando è possibile vanno aggiunti sulla regola corrente)» e «Ok per le decisioni» (alle tre raccomandazioni del coordinator: (1) storico e testi alla lettera in `docs/decisioni-archivio.md`, non letto all'avvio; (2) ristrutturazione una tantum fatta dal coordinator su una copia, verificata dal plan-auditor, sostituita dal registrar; (3) subito). Riga di §6: «Registro delle decisioni: solo correnti» con la regola: in DECISIONS.md solo decisioni in vigore e aperte, nella forma corrente, con il motivo utile sulla riga; quando una decisione cambia, la versione superata va in coda a `docs/decisioni-archivio.md` nello stesso commit.
- 2026-11-05: «Dopo aver ricopiato ti do ok ed elimino la memoria. Istruzioni solo in Claude.md, nessun'altra sessione avrà istruzioni sull'uso della memoria». Riga di §6: «Istruzioni di sessione e memoria» con la regola: le istruzioni su avvio, cartella `stato/` e chiusura dei turni stanno solo in `CLAUDE.md`; la memoria della piattaforma sarà eliminata dall'utente dopo la ricopiatura dei prompt.
Nelle righe metti la regola corrente e la data; le frasi alla lettera vanno **in coda a `docs/decisioni-archivio.md`**, in una sezione nuova «2026-11-05 — testi dell'utente», con il rimando alla riga di §6. Aggiorna la riga «Ultimo aggiornamento» (una riga sola: data e cosa).

## 3. index.md
Riga di DECISIONS: descrizione breve del registro corrente (sezioni §1-§7) senza la lunga cronologia; aggiungi una riga per `decisioni-archivio.md` («storia delle decisioni, non letta all'avvio»). Aggiorna il conteggio delle DA solo se il registro lo cambia (non lo cambia: 120 DA, 22 DX).

## Vincoli
Stati ammessi solo quelli della legenda; un «ok» si registra come «Decisa (2026-11-05, utente)». Nessuna riga nuova fuori da quelle indicate; nessun file fuori da `docs/DECISIONS.md`, `docs/decisioni-archivio.md`, `docs/index.md`; niente commit. Risposta: solo il JSON dello schema del registrar.
