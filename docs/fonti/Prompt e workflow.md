> **Nota di allineamento (v1.1, 2026-11-03).** Documento sorgente dell'utente. Le decisioni prese durante la pianificazione prevalgono sul testo originale (ordine: `docs/PRINCIPI.md`, `docs/DECISIONS.md`, documenti di dettaglio, questo file). Dove il testo è superato, una nota **[→ …]** rimanda alla decisione, senza ripeterne il contenuto: la fonte resta `DECISIONS.md`. 

## 1. Meta-prompt (da incollare una volta, all'inizio di ogni sessione)

```
Sei un architetto tecnico senior. Scrivi documenti operativi di implementazione
per una piattaforma di gestione per un'agenzia di marketing basata su agenti AI.
Il documento è destinato a un team di implementazione (umano o AI) che deve
costruire quel sottoprodotto senza ambiguità.

REGOLE:
- Non inventare tecnologie non presenti nel piano master. Se serve una scelta,
  dichiarala come "decisione aperta" con 2-3 opzioni e un criterio.
- Ogni dipendenza da altri sottoprodotti va citata con ID esplicito (es. "dipende
  da A1, B2").
- Ogni criterio di accettazione deve essere testabile (un comando, un test, una
  metrica con soglia).
- Se qualcosa non è verificabile, dichiaralo in "Non verificato".
- Lunghezza target: 800-1.500 parole. Markdown. **[→ la lunghezza in uso è nel prompt di `.claude/agents/doc-writer.md`]**

TEMPLATE OBBLIGATORIO (12 sezioni, in quest'ordine): **[→ in uso anche Appendici A, B, C e Storico modifiche: vedi `.claude/agents/doc-writer.md`]**
1. Identità — ID, nome, componente padre, versione del documento
2. Scopo — cosa fa, cosa NON fa, perché esiste
3. Contesto e dipendenze — sottoprodotti da cui dipende, assunzioni
4. Contratti — input, output, eventi emessi/consumati, schema dati (se applicabile)
5. Interfacce — API, comandi, UI, formati
6. Comportamento — flussi principali, casi limite, gestione errori
7. Requisiti non funzionali — performance, sicurezza, scalabilità, osservabilità
8. Criteri di accettazione — testabili, con soglia
9. Piano di implementazione — fasi, tecnologie (dal master), rischi
10. Test e valutazione — unit, integration, eval, security
11. Rischi e mitigazioni
12. Stima e priorità — S/M/L, dipendenze critiche, se è nel thin-slice MVP
```

---

## 2. Prompt per componente (riutilizzabile per A–G)

Sostituisci `{COMPONENTE}`, `{SOTTOPRODOTTI}`, `{CONTESTO}`. Un prompt per componente, un messaggio per volta.

```
Scrivi i documenti operativi per il Componente {COMPONENTE} della piattaforma.
Un documento per ogni sottoprodotto elencato, seguendo il template del
meta-prompt (12 sezioni). Restituisci un blocco markdown per documento,
separati da `---` e con nome file suggerito (es. `A1-grafo-mandati.md`).

CONTESTO (dal master plan):
{CONTESTO — incolla qui la sezione 2 e 6 del piano master relative a questo componente}

SOTTOPRODOTTI DA DOCUMENTARE:
{SOTTOPRODOTTI — es.:
A1. Modello del grafo dei mandati
A2. Compilatore policy
A3. Runtime di enforcement
A4. Validatore round-trip
A5. Audit trail dei mandati}

VINCOLI SPECIFICI PER QUESTO COMPONENTE:
- {es. per A: "il grafo è la mappa, non il magazzino: i payload grandi vanno
  in object storage, referenziati da nodi-àncora"}
- {es. per E: "OpenTelemetry GenAI semantic conventions, nessun lock-in vendor"} **[→ PV-02, DA-E1-05]**
- {es. per B: "isolamento architetturale, non solo filtri WHERE"}

Alla fine, produci una tabella di dipendenze incrociate: per ogni sottoprodotto,
quali altri sottoprodotti (anche di altri componenti) devono esistere prima.
```

---

## 3. Ordine di priorità (cosa generare prima)

Non tutti i 28 documenti servono per il thin-slice. L'ordine consigliato:

**Ondata 1 — Walking skeleton (9 documenti)**
- `E1` Tracing distribuito
- `E2` Prompt registry
- `E3` Eval harness offline
- `A1` Modello del grafo dei mandati
- `A3` Runtime di enforcement
- `B1` Agent runtime isolato
- `B2` Tool gateway
- `C1` Grafo di workflow
- `C3` Punto HITL

Sono il minimo per avere **un workflow governato e osservabile**. Se questi nove non stanno in piedi, il resto è prematuro.

**Ondata 2 — MVP completo (10 documenti)**
- `A2`, `A4`, `A5`, `B3`, `B4`, `B5`, `C2`, `C4`, `D1`, `G2` **[→ più F6 e A6 (DX-12, DX-14); elenco in uso in `docs/index.md`]**

**Ondata 3 — Scala (9 documenti)**
- `C5`, `D2`, `D3`, `D4`, `D5`, `E4`, `E5`, `E6`, `F1`–`F5`, `G1`, `G3`, `G4`

Le ondate 2 e 3 si possono generare dopo aver **testato** l'ondata 1 sul campo: i prompt restano gli stessi, ma i documenti dell'ondata 2 beneficeranno di ciò che hai imparato.

---

## 4. Workflow pratico

1. **[→ il flusso in uso è in `docs/agenti/README.md`]** **Apri una sessione/agente/tmux per componente** (o per sottoprodotto, se preferisci più controllo). Incolla il **meta-prompt**, poi il **prompt componente**.
2. **Salva ogni output** come file `.md` con la naming `{ID}-{slug}.md` (es. `A1-grafo-mandati.md`). Tieni un `index.md` che linka tutti.
3. **Non rigenerare** un documento senza motivo: se cambia il master plan, aggiorna il documento con un diff esplicito, non con una riscrittura.
4. **Testa i criteri di accettazione** dell'ondata 1 prima di generare l'ondata 2. Se un criterio non è testabile, il documento è da correggere.
5. **Tieni un registro delle decisioni aperte**: ogni "decisione aperta" dai documenti va in un file `DECISIONS.md` con data, opzioni, scelta, motivo. Altrimenti si perde.

---

## Storico modifiche

| Versione | Data | Cosa è cambiato e perché |
|---|---|---|
| 1.0 | 2026-11-03 | Versione originale caricata dall'utente. |
| 1.1 | 2026-11-03 | Note di allineamento: lunghezza e template in uso nel doc-writer, PV-02, ondata 2 con F6 e A6, flusso con gli agenti di governance. |
