# Task per registrar: correzione delle righe di §6 e Python 3.15 subito

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Seguito del task `docs/revisioni/decisioni-2026-11-05-locale/task-registrar-runtime-branch.md` (risposta in `risposta-registrar-runtime-branch.json`). Le modifiche di quel task a `docs/DECISIONS.md` e `docs/decisioni-archivio.md` sono nel working tree, non ancora committate: partono da lì.

Nuovo messaggio dell'utente, alla lettera: «Ma perché questo postgres? Ti avevo detto il 18... Anche python, metti il 3.15 ma solo se tutti i pacchetti sono compatibili.»

Verifica del coordinator (2026-11-05): tutti i 17 pacchetti del lockfile, alle versioni fissate, sono installabili su Python 3.15 (pacchetti binari con wheel cp315, gli altri puro Python con `requires_python` compatibile); installati con `pip install --require-hashes` su Python 3.15.2, `pip check` senza errori; `tests/` 87 verdi tre volte su PostgreSQL 18.6 con il codice attuale.

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il messaggio alla lettera sopra
Data: 2026-11-05
Correzioni e aggiornamento in `docs/DECISIONS.md` §6:
1. Righe «Branch di lavoro» e «Versioni di runtime»: togli il prefisso «Decisa (2026-11-05, utente): ». Le righe di §6 non hanno una colonna di stato: nessuna altra riga di §6 porta uno stato nel testo.
2. Riga «Versioni di runtime»: Python 3.15 (non 3.14) e PostgreSQL 18, compatibilità di tutti i pacchetti verificata (sopra). Ordine: l'ambiente di sviluppo passa subito a Python 3.15 e PostgreSQL 18, con verifica dei test sul codice attuale prima di ogni correzione; poi la micro-correzione di `API_ENV`; poi l'aggiornamento di lockfile (con hash), CI e README come lavoro a parte dell'implementer, seguito da `code-reviewer` e `compliance-auditor`. Nel motivo sostituisci la frase ambigua sulle dipendenze con: «dipendenze del lockfile all'ultima versione su PyPI, salvo `pydantic` (fissata 2.14.2, ultima 2.14.3) e `pydantic-core` (fissata 2.50.2, ultima 2.50.4); nessuna vulnerabilità nota su OSV». Date di supporto: Python 3.15 fino al 2031-10-31, PostgreSQL 18 fino al 2030-11-14.
3. La versione della riga «Versioni di runtime» che sostituisci va in coda a `docs/decisioni-archivio.md` (sezione «2026-11-05 — righe superate»), e il messaggio dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05 che hai creato.
4. Riga «Ultimo aggiornamento»: Python 3.15 al posto di 3.14.
Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
