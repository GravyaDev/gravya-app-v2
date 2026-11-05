# Task per registrar: togliere il punto «Versione di Python» da §4

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Seguito di `docs/revisioni/e1-runtime/task-registrar.md` (risposta in `risposta-registrar.json`); le sue modifiche sono nel working tree, non committate. Nel lancio precedente hai aggiunto in `docs/DECISIONS.md` §4 il punto «Versione di Python: testo dell'utente da riportare», non richiesto dal task e basato su un fatto falso: il testo dell'utente che fissa Python 3.15 è già in `docs/decisioni-archivio.md` (riga 362, sezione «2026-11-05 — testi dell'utente (branch e versioni di runtime)»: «Ma perché questo postgres? Ti avevo detto il 18... Anche python, metti il 3.15 ma solo se tutti i pacchetti sono compatibili.»). La riga con Python 3.14 nell'archivio è una versione superata, come dice la sezione in cui sta.

## Task
Evento: esito revisione
Cartella: docs/ del repo
Input: questo task
Data: 2026-11-05
Togli da `docs/DECISIONS.md` §4 il punto «Versione di Python: testo dell'utente da riportare», senza lasciarne traccia e senza archiviarlo (non era una decisione né un rilievo). Non toccare nient'altro. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
