# Task per registrar: esito della PR sulla catena di fornitura

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Attuazione dei punti 1 e 2 di DECISIONS §6 «Catena di fornitura» sul branch `impl/ci-fornitura`, unito in `main` con il merge 46659bd (branch e worktree cancellati). Revisioni in `docs/revisioni/ci-fornitura/`: `code-reviewer` BLOCCA al giro 1 (fail-closed di `invia_http` non protetto da test) e al giro 2 (rifiuto degli stati HTTP diversi da 200 non protetto, timeout non verificato), corretti dall'implementer ai giri 2 e 3, **OK** al giro 3 (`report-code-reviewer-giro3.md`); `compliance-auditor` **RIPORTA** (`report-compliance-auditor.md`, risposta `risposta-compliance-auditor.json`). Verifica del coordinator dopo il merge: `tests/` 123 verdi, `scripts/test-non-superuser.sh` riuscito, `scripts/osv-check.py` senza vulnerabilità, workflow «CI» e «Catena di fornitura» verdi su 46659bd. Già corretti nei giri 2 e 3, da non riportare: il rilievo sulla lettura del lockfile fail-open e quello su `IncompleteRead`.

## Task
Evento: esito revisione
Cartella: docs/ del repo
Input: i report e le risposte sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md` §6, riga «Catena di fornitura»: punti 1 e 2 attuati con il merge 46659bd, **salvo Dependabot per i pacchetti Python**, non configurato perché la documentazione di GitHub non garantisce la rigenerazione del lockfile `pip-compile` con hash (implementer, rilievo di entrambi i revisori); controllo OSV in `scripts/osv-check.py` e nel workflow «Catena di fornitura»; `psql` della CI dall'immagine dei servizi; immagine PostgreSQL in un solo punto del workflow. La versione precedente della riga in coda a `docs/decisioni-archivio.md`.
2. `docs/DECISIONS.md` §4, punto «Catena di fornitura e aggiornamenti»: sostituisci «in attuazione» con i punti ancora aperti, ciascuno con il report di provenienza: (a) aggiornamento dei pacchetti Python senza Dependabot (scelta da fare: provare Dependabot con una PR reale o un job che rigenera il lockfile e apre una PR); (b) destinatario dell'avviso quando il job settimanale fallisce, se è un segnale per A5, se «Catena di fornitura» è un controllo obbligatorio per il merge, e la possibile disattivazione dei workflow programmati per inattività (compliance-auditor); (c) elenco versionato di eccezioni con motivo e scadenza per vulnerabilità senza correzione (compliance-auditor, minore); (d) il job del digest rileva il cambio del tag ma non le vulnerabilità dell'immagine fissata, e il ramo «digest cambiato» non è stato provato (compliance-auditor, minore); (e) `ubuntu-24.04` è un'etichetta e non un'immagine fissa: rischio da accettare (compliance-auditor, minore); (f) minori del code-reviewer del giro 1: costanti dello script verificate da test tautologici; Dependabot per le action potrebbe non leggere gli alias YAML dei servizi; esecuzioni doppie con `push` e `pull_request`. Resta il rilievo minore sull'intestazione del lockfile già presente. Documenti: CI, E1. La versione precedente del punto in coda all'archivio.
3. Riga «Ultimo aggiornamento».
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
