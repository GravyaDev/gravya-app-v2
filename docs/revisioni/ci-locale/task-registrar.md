# Task per registrar: decisioni dell'utente sui punti aperti della catena di fornitura e job in locale

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
`docs/DECISIONS.md` §4, punto «Catena di fornitura e aggiornamenti», punti (a)-(f). Il coordinator ha presentato all'utente:
- a) Aggiornamento dei pacchetti Python. Raccomandazione: un job settimanale che rigenera il lockfile alle ultime versioni e, se cambia, apre una PR, che passa poi dalla CI e dalle revisioni come ogni altra. In alternativa: provare Dependabot con una PR reale.
- b) Chi viene avvisato se il controllo settimanale fallisce. Raccomandazione: il job apre automaticamente una issue su GitHub assegnata all'utente; il controllo OSV diventa obbligatorio per fare merge in `main`; il segnale verso A5 arriverà quando A5 esisterà.
- c) Eccezioni per vulnerabilità senza correzione disponibile. Raccomandazione: rimandare al primo caso reale, e allora creare un elenco versionato con motivo e scadenza.
- e) `ubuntu-24.04` è un nome di versione, non un'immagine fissa. Raccomandazione: accettarlo come rischio registrato.
- d e f) Minori (controllo del digest mai provato su un digest diverso; costanti verificate solo da test tautologici; esecuzioni doppie a ogni PR). Raccomandazione: sistemarli alla prossima modifica della CI.

Risposta dell'utente, alla lettera: «Ok a tutto. Per quanto riguarda i job, devi configurare tutto quello che puoi sulla macchina locale e non su github per le actions mensili sono 3000 minuti ed è successo più volte di sforare e bloccare tutto.»

Dati del coordinator (2026-11-05): il 2026-11-05 il repository ha avuto 64 esecuzioni di GitHub Actions (53 del workflow «CI», quasi tutte per commit di soli documenti o di `stato/`); sulla macchina locale c'è systemd con timer utente persistenti. L'attuazione è nel task `docs/revisioni/ci-locale/task-implementer.md` (worktree `ci-locale`): job settimanali su un timer locale, CI di GitHub solo per i cambiamenti di codice, controllo obbligatorio prima del merge eseguito in locale.

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il testo sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md` §6, riga nuova «Minuti di GitHub Actions» (documenti: CI, tutti): i job programmati e i controlli che possono girare in locale girano sulla macchina locale e non su GitHub Actions; su GitHub restano solo i controlli che servono, avviati solo da cambiamenti di codice. Motivo: il limite di 3000 minuti al mese è stato superato più volte, bloccando tutto (dalle parole dell'utente).
2. `docs/DECISIONS.md` §6, riga «Catena di fornitura»: aggiungi le decisioni a, b, c, e (nella forma raccomandata, con l'esecuzione in locale secondo la riga nuova: job settimanale locale per OSV, digest e rigenerazione del lockfile con PR se cambia; issue assegnata all'utente quando un controllo fallisce; controllo OSV obbligatorio prima del merge in `main`, eseguito in locale; eccezioni rimandate al primo caso reale; `ubuntu-24.04` rischio accettato) e la decisione su d e f (alla prossima modifica della CI, cioè ora, nello stesso task). Attuazione in corso con il task sopra. Versione precedente in coda all'archivio.
3. `docs/DECISIONS.md` §4, punto «Catena di fornitura e aggiornamenti»: tutti i punti (a)-(f) sono decisi; il punto resta solo per l'attuazione in corso (task sopra) e per il rilievo minore già presente sull'intestazione del lockfile. Versione precedente in coda all'archivio; testo dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05.
4. Riga «Ultimo aggiornamento».
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
