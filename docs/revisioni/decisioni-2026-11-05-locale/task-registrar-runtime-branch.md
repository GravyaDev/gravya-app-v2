# Task per registrar: versioni di runtime e branch di lavoro `main`

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Sessione 9, la prima in Claude Code locale. Il coordinator ha posto all'utente queste domande, numerate, e l'utente ha risposto.

Domanda sul branch: «Su GitHub esiste solo `main`: la PR #1 ha unito `claude/docs-ondata-1`, che non c'è più. […] Da ora il branch unico di lavoro è `main`?». Risposta dell'utente, alla lettera: «Sì, main».

Domande sulle versioni (testo del coordinator):
1. Versioni di runtime: a) PostgreSQL 18 (in Docker) e Python 3.14; b) PostgreSQL 18 e Python 3.15; c) restare come ora (Python 3.11 e PostgreSQL 16, che venivano dal container della piattaforma, non da una decisione).
2. Ordine: a) prima la micro-correzione di `API_ENV` con le versioni attuali (PostgreSQL 16 in Docker), poi l'aggiornamento come lavoro a parte; b) tutto insieme.
3. Esecuzione dell'aggiornamento: l'implementer aggiorna lockfile (con hash), CI e README e riesegue i test sulla nuova versione; poi `code-reviewer` e `compliance-auditor`, come per ogni PR di codice.

Risposta dell'utente, alla lettera: «1a, 2a, 3 ok».

Verifica del coordinator (2026-11-05), da riportare come motivo: le dipendenze Python del lockfile sono all'ultima versione su PyPI salvo `pydantic` 2.14.3 e `pydantic-core` 2.50.4, nessuna vulnerabilità nota su OSV; Python 3.11 è supportato fino al 2027-10-31, PostgreSQL 16 fino al 2028-11-09; Python 3.14 fino al 2030-10-31, PostgreSQL 18 fino al 2030-11-14.

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: le due risposte alla lettera sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
- `docs/DECISIONS.md` §6, riga «Branch di lavoro»: il branch unico di lavoro è `main` (dopo la PR #1 che ha unito `claude/docs-ondata-1`). La versione superata della riga va in coda a `docs/decisioni-archivio.md`, con il testo alla lettera.
- `docs/DECISIONS.md` §6, riga nuova «Versioni di runtime» (documenti: E1 e tutto il codice): Python 3.14 e PostgreSQL 18; prima la micro-correzione di `API_ENV` sulle versioni attuali, poi l'aggiornamento come lavoro a parte dell'implementer (lockfile con hash, CI, README, test sulla nuova versione), seguito da `code-reviewer` e `compliance-auditor`; motivo in breve dalla verifica del coordinator. Testo alla lettera dell'utente in coda a `docs/decisioni-archivio.md`.
- Puoi aggiornare la riga «Ultimo aggiornamento» in testa a `DECISIONS.md`; nient'altro dell'intestazione.
- Non toccare §4 e le altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
