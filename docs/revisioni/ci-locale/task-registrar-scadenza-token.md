# Task per registrar: scadenza del token del job locale

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Seguito di `docs/revisioni/ci-locale/task-registrar-token.md`: in `docs/DECISIONS.md` §4 hai aggiunto il punto sulla scadenza del token fine-grained del job locale, «da comunicare dall'utente». Il coordinator ha chiesto la data di scadenza; risposta dell'utente, alla lettera: «90 giorni». Il token è stato creato il 2026-11-05, quindi scade il 2027-02-03 (calcolo del coordinator).

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il testo sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza: in `docs/DECISIONS.md` §6, riga «Catena di fornitura», aggiungi al punto del token la durata di 90 giorni e la scadenza 2027-02-03 (rinnovo prima della scadenza, a cura dell'utente). Togli da §4 il punto sulla scadenza ormai nota, senza lasciarne traccia in §4; la sua versione va in coda a `docs/decisioni-archivio.md`, con il testo dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05. Versione precedente della riga di §6 in coda all'archivio. Riga «Ultimo aggiornamento». Le righe di §6 non hanno una colonna di stato. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
