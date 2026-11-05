# Task per registrar: chiusura del punto «E1, chiusura definitiva (giro 6)» e worktree per l'implementer

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Due eventi.

**A. Esito della micro-correzione di `API_ENV`.** Il code-reviewer del giro 6 aveva dato BLOCCA su un solo punto (`docs/revisioni/impl-e1/report-code-reviewer-giro6.md` §3). Decisione dell'utente, già in archivio: «(a, micro-correzione)», senza altri giri di revisione e con verifica del coordinator rieseguendo le suite. Correzione fatta dall'implementer con i commit db41169 (codice, test, README) e aa20e20 (`API_ENV` nella CI, arresto di `scripts/test-non-superuser.sh` se manca); task e risposte in `docs/revisioni/impl-e1-chiusura/`. Verifica del coordinator (2026-11-05, Python 3.15, PostgreSQL 18): `tests/` 88 passati in 10 esecuzioni su 10; prove dei revisori con gli stessi esiti del giro 6 (giro 1: 1 fallito e 1 errore di teardown; giro 2: 13 falliti attesi e l'errore intermittente di teardown già noto; giro 3: 3 falliti attesi; giro 4: 3 falliti attesi S1, V1, V2; giro 5: 12 passati), salvo **una** esecuzione su 20 della prova del giro 4 con un fallimento in più, non identificato e non riprodotto in altre 19 esecuzioni (ipotesi non verificata: test sensibile ai tempi); `scripts/test-non-superuser.sh` riuscito in locale; CI di GitHub verde nei due job.

**B. Branch e worktree.** Proposta del coordinator, testo: «Worktree. Con i soli branch in una cartella può esserci un solo branch aperto alla volta, quindi niente implementer in parallelo. Proposta: lo script crea per ogni task un worktree in `.worktrees/<task>` (ignorato da git) sul branch `impl/<task>`, con il suo `.venv` e il suo PostgreSQL in Docker su una porta diversa (il `.venv` principale punterebbe al codice sbagliato e i test usano un nome di database fisso, quindi in parallelo si pesterebbero). Dopo il merge in `main`, un comando cancella worktree, branch locale e remoto e container, e rifiuta se il branch non è unito. All'avvio di ogni sessione l'elenco di quelli rimasti aperti va nell'handoff.» Prima l'utente aveva scritto, alla lettera: «Implementer: per il branch separato a me va benissimo, anzi meglio così ne puoi lanciare più di uno. Però deve essere cancellato al termine del merge e del lavoro, non proliferare all'infinito. Oppure usa worktree, stesso criterio di cancellazione. Valuta e riportami.» Risposta dell'utente alla proposta, alla lettera: «2. confermo».

## Task
Evento: decisione utente ed esito revisione
Cartella: docs/ del repo
Input: i testi alla lettera e gli esiti sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md` §4: togli il punto «E1, chiusura definitiva (giro 6)» (chiuso: il BLOCCA del giro 6 è risolto dalla micro-correzione, commit db41169 e aa20e20); la sua versione va in coda a `docs/decisioni-archivio.md` con il motivo della chiusura. Aggiungi in §4 un punto «E1, residui del giro 6» con: scrittura in volo dopo `close()` con coda profonda; default di `DATABASE_URL` nel README diversi da quelli dei test (fonte: `docs/revisioni/impl-e1/report-code-reviewer-giro6.md`); un fallimento in più non identificato in 1 esecuzione su 20 della prova del giro 4 (ipotesi non verificata: tempi). Documenti: E1.
2. `docs/DECISIONS.md` §6, riga «E1: chiusura definitiva»: aggiungi in fondo che il BLOCCA del giro 6 è risolto dalla micro-correzione (db41169, aa20e20) e che i residui sono in §4. La versione precedente della riga va in coda all'archivio.
3. `docs/DECISIONS.md` §6, riga «Branch di lavoro»: `main` resta il branch di integrazione; ogni implementer lavora in un worktree `.worktrees/<nome>` sul branch `impl/<nome>`, con `.venv` e PostgreSQL in Docker propri (comandi in `scripts/agenti.py`: `worktree-crea`, `worktree-elenco`, `worktree-chiudi`); dopo il merge in `main` worktree, branch locale e remoto e container si cancellano, e la chiusura rifiuta un branch non unito o un worktree con modifiche; i worktree aperti si riportano nell'handoff a ogni sessione. Motivo: implementer in parallelo senza proliferazione di branch. La versione precedente della riga va in coda all'archivio; i due testi dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05.
4. Riga «Ultimo aggiornamento» in testa a `DECISIONS.md`: aggiornala a questi due eventi.
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
