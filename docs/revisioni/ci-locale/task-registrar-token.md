# Task per registrar: token dedicato per il job locale

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Rilievo 2 del compliance-auditor (`docs/revisioni/ci-locale/report-compliance-auditor.md`): il job locale usa il PAT classico di `kloud-ai` (scope `repo`, `workflow`, `read:org`, senza scadenza), lo stesso di tutte le sessioni della macchina. Il coordinator ha proposto all'utente un token fine-grained solo per `gravya-app-v2` (contents, pull requests, issues; niente workflow), con scadenza, letto dal servizio systemd da un file leggibile solo dall'utente e tolto dall'ambiente del passo pip-tools; il login di `gh` resta invariato; in alternativa, rischio accettato e registrato. Risposta dell'utente, alla lettera: «Token creato, dimmi dove metterlo». Il coordinator ha indicato `~/.config/gravya-fornitura/env` (permessi 600); l'attuazione nel servizio è nel task `docs/revisioni/ci-locale/task-implementer-giro3.md`, punto 4.

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il testo sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza: in `docs/DECISIONS.md` §6, riga «Catena di fornitura», aggiungi che il job locale usa un token fine-grained dedicato a `gravya-app-v2` (contents, pull requests, issues; senza workflow; con scadenza), caricato dal servizio da `~/.config/gravya-fornitura/env` e assente dal passo pip-tools; attuazione con il task indicato. Mai il valore del token. Versione precedente della riga in coda a `docs/decisioni-archivio.md`; testo dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05; riga «Ultimo aggiornamento». Le righe di §6 non hanno una colonna di stato. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
