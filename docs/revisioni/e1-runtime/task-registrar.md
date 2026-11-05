# Task per registrar: esito della PR sulle versioni di runtime

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Aggiornamento a Python 3.15 e PostgreSQL 18 (DECISIONS §6 «Versioni di runtime») fatto dall'implementer sul branch `impl/e1-runtime`, unito in `main` con il merge 3bf8969 (branch e worktree cancellati). Revisioni: `code-reviewer` **OK** (`docs/revisioni/e1-runtime/report-code-reviewer.md`, risposta `risposta-code-reviewer.json`), `compliance-auditor` **RIPORTA** (`report-compliance-auditor.md`, risposta `risposta-compliance-auditor.json`). Verifica del coordinator dopo il merge: `tests/` 88 verdi 10 volte, `scripts/test-non-superuser.sh` riuscito, prove dei revisori con gli esiti del giro 6. Il rilievo minore del compliance-auditor su `scripts/agenti.py` (immagine PostgreSQL con tag mobile) è già risolto dal coordinator: lo script legge l'immagine fissata per digest dalla CI. Regola di blocco di `docs/agenti/README.md`: un esito `RIPORTA` non ferma la sequenza, ma il punto va in `DECISIONS.md` come punto da riportare.

## Task
Evento: esito revisione
Cartella: docs/ del repo
Input: le due risposte JSON e i due report sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md` §6, riga «Versioni di runtime»: aggiornala allo stato attuale (attuata con il merge 3bf8969; dipendenze del lockfile tutte all'ultima versione su PyPI, nessuna vulnerabilità nota su OSV al 2026-11-05). Togli il riferimento a `pydantic` 2.14.2 e `pydantic-core` 2.50.2, ormai superato (rilievo di entrambi i revisori). La versione precedente della riga va in coda a `docs/decisioni-archivio.md`.
2. `docs/DECISIONS.md` §4: un punto nuovo «Catena di fornitura e aggiornamenti» con i rilievi del compliance-auditor ancora aperti, con la norma che ciascuno cita: processo e frequenza della scansione delle vulnerabilità e dell'aggiornamento di lockfile e digest, oggi solo manuale; runner `ubuntu-latest` non fissato, client `psql` installato con apt senza versione, action fissate per SHA ma su Node 20 deprecato; lockfile unico per runtime e sviluppo, da separare al deploy; nessun limite superiore in `requires-python`. Aggiungi il rilievo minore del code-reviewer: l'intestazione del lockfile non dice che il comando va eseguito senza un `requirements.lock.txt` esistente, o con `--upgrade`, per ottenere le ultime versioni. Documenti: E1, CI. Non aggiungere il rilievo su `scripts/agenti.py`, già risolto.
3. Riga «Ultimo aggiornamento» in testa a `DECISIONS.md`: aggiornala a questo evento.
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
