# Task per registrar: DX-22 non si applica agli strumenti di sviluppo

Agente: registrar
Preparato dal coordinator il 2026-11-05. Branch: main.

## Contesto
Domanda del coordinator all'utente (rilievi del code-reviewer, `docs/revisioni/ci-locale/report-code-reviewer.md` rilievo 10, e del compliance-auditor, `report-compliance-auditor.md` rilievo 8; decisione mancante dell'implementer in `risposta-implementer-giro2.json`): «Valori fissi negli script locali: assegnatario delle issue, soglia di ritardo (9 giorni, scelta dell'implementer) e orario del timer stanno scritti negli script, mentre DX-22 vieta i valori fissi. Va bene un'eccezione a DX-22 per gli strumenti di sviluppo?»

Risposta dell'utente, alla lettera: «2. valori fissi: approvo deroga, quelle istruzioni valgono solo sul prodotto e non qui».

## Task
Evento: decisione utente
Cartella: docs/ del repo
Input: il testo sopra
Data: 2026-11-05
Aggiorna i registri di conseguenza:
1. `docs/DECISIONS.md`: accanto a DX-22 (nella sua riga, o come riga nuova di §6 «DX-22: ambito» se la riga di DX-22 non lo consente senza riscriverla) registra che DX-22 (nessun valore fisso nel codice, ogni parametro variabile configurabile e catalogata) vale solo per il prodotto Gravya; non vale per gli strumenti di sviluppo e di CI del repository (per esempio `scripts/agenti.py`, `scripts/fornitura-locale.py`, `scripts/osv-check.py`, unità systemd, workflow), dove i valori stanno come costanti dichiarate in testa ai file con il loro motivo. Se modifichi la riga di DX-22, la versione precedente in coda a `docs/decisioni-archivio.md`.
2. Testo dell'utente alla lettera nella sezione dei testi dell'utente del 2026-11-05 dell'archivio.
3. Riga «Ultimo aggiornamento».
Le righe di §6 non hanno una colonna di stato: non scrivere stati nel testo di §6. Non toccare altre righe. Non fare commit.

## Regole fisse
- Rispondi con il solo JSON dello schema della risposta, con solo le chiavi dello schema.
- Non scrivere nella cartella `stato/` e non creare file fuori dal tuo perimetro e dalla cartella del task (niente copie, backup o file temporanei, nemmeno in `/tmp`).
- Stati ammessi: solo quelli della legenda di `docs/DECISIONS.md`; un «ok» dell'utente = Decisa.
- Non toccare legenda e intestazione dei registri.
- Il testo delle decisioni dell'utente va riportato alla lettera.
