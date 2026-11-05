# Task per registrar: decisione dell'utente sulla catena di fornitura

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
`docs/DECISIONS.md` §4, punto «Catena di fornitura e aggiornamenti» (rilievi a, b, c, d del compliance-auditor e rilievo minore del code-reviewer sull'intestazione del lockfile). Il coordinator ha presentato all'utente queste decisioni con raccomandazione:

1. Controllo delle vulnerabilità e aggiornamenti (rilievo a). Raccomandazione: un controllo OSV del lockfile nella CI, a ogni push e ogni settimana; Dependabot settimanale per i pacchetti Python e per le action. Il digest di PostgreSQL lo controlla lo stesso job settimanale. In alternativa: solo il controllo nella CI, senza aggiornamenti automatici.
2. Componenti della CI non fissati (rilievo b). Raccomandazione: runner fissato a `ubuntu-24.04`, `psql` dalla stessa immagine `postgres:18` della CI invece che da apt, action aggiornate a versioni su Node 24, sempre fissate per SHA.
3. Lockfile unico per esecuzione e sviluppo (rilievo c). Raccomandazione: rimandare la separazione al primo deploy, quando servirà un'immagine di produzione.
4. Limite superiore di versione per Python, `requires-python` (rilievo d). Raccomandazione: non metterlo; gli hash del lockfile proteggono già, e un limite superiore di solito crea più problemi di quanti ne eviti.

Con l'«ok», l'1 e il 2 li fa l'implementer in un nuovo worktree (task `docs/revisioni/ci-fornitura/task-implementer.md`), con le revisioni e il merge.

Risposta dell'utente, alla lettera: «ok».

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il testo sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md` §6: riga nuova «Catena di fornitura» (documenti: CI, E1) con le quattro decisioni nella forma corrente (1 e 2 da attuare con il task dell'implementer indicato; 3 rimandata al primo deploy; 4 nessun limite superiore) e il motivo in breve dalle raccomandazioni.
2. `docs/DECISIONS.md` §4, punto «Catena di fornitura e aggiornamenti»: restano aperti solo ciò che non è deciso o non è attuato. Tieni il punto con: attuazione di 1 e 2 in corso (task sopra); il rilievo minore del code-reviewer sull'intestazione del lockfile (non deciso). Togli i rilievi c e d, ora decisi in §6. La versione precedente del punto va in coda a `docs/decisioni-archivio.md`; il testo dell'utente («ok», con il riferimento alle quattro raccomandazioni) nella sezione dei testi dell'utente del 2026-11-05.
3. Riga «Ultimo aggiornamento» in testa a `DECISIONS.md`.
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
