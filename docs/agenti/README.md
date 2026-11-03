# Agenti di governance del progetto

Versione 1.1, 2026-11-03.

Questi agenti mantengono allineati piano, registri e codice di Gravya v2. Ognuno ha un compito solo, un perimetro di scrittura definito e un formato di risposta fisso, così il loro esito si può leggere in modo automatico. Il prompt di ciascun agente è in un unico file, in `.claude/agents/` alla radice del repository: è la sola fonte. Questa cartella contiene solo questo README.

## Catalogo

| Agente | File | Compito | Scrive | Modalità |
|---|---|---|---|---|
| `registrar` | [registrar.md](../../.claude/agents/registrar.md) | Aggiorna `DECISIONS.md`, `index.md`, lo Storico modifiche dei documenti e la memoria di progetto dopo ogni decisione o modifica | `docs/DECISIONS.md`, `docs/index.md`, righe dello Storico, `/mnt/memory/gravya/` | Collaborativa |
| `plan-auditor` | [plan-auditor.md](../../.claude/agents/plan-auditor.md) | Verifica la coerenza tra principi, decisioni, documenti di dettaglio e master plan | Solo il proprio report | Avversariale |
| `code-reviewer` | [code-reviewer.md](../../.claude/agents/code-reviewer.md) | Verifica che il codice di una PR implementi il documento di dettaglio, rispetti i criteri di accettazione e i principi | Solo il proprio report | Avversariale |
| `compliance-auditor` | [compliance-auditor.md](../../.claude/agents/compliance-auditor.md) | Cerca violazioni di GDPR, NIS2, AI Act e osservabilità AI (PV-01) in documenti e codice | Solo il proprio report | Avversariale |
| `doc-writer` | [doc-writer.md](../../.claude/agents/doc-writer.md) | Redige o aggiorna un documento di dettaglio secondo il template | Solo il file del documento assegnato | Collaborativa |

## Quando si attivano

L'attivazione è deterministica: a ogni evento corrisponde una sequenza fissa, e l'ordine non dipende dal giudizio del momento.

| Evento | Sequenza |
|---|---|
| L'utente prende una decisione | `registrar` |
| Un documento di dettaglio viene creato o modificato | `plan-auditor` e `compliance-auditor` in parallelo, poi `registrar` |
| Una nuova ondata di documenti | `doc-writer` (uno per documento, in parallelo), poi `plan-auditor` e `compliance-auditor`, poi `registrar` |
| Una PR di codice | `code-reviewer` e `compliance-auditor` in parallelo, poi `registrar` se emergono divergenze dal piano |
| Chiusura di un'ondata o di una milestone | `plan-auditor` sull'insieme completo, poi `registrar` |

**Regola di blocco.** Un esito `BLOCCA` di un agente avversariale ferma la sequenza. Il `registrar` registra il blocco e i rilievi, l'orchestratore li riporta all'utente, e si procede solo dopo una correzione o una decisione esplicita dell'utente. Un esito `RIPORTA` non ferma la sequenza, ma il punto finisce in `DECISIONS.md` come "Da riportare".

## Modello

Per decisione dell'utente (2026-11-03) gli agenti di governance **non usano Opus**:

| Agente | Modello | Motivo |
|---|---|---|
| `registrar` | `haiku` | Compito meccanico: aggiorna i registri da input già decisi |
| `doc-writer` | `sonnet` | Redazione strutturata con ragionamento sulle dipendenze |
| `plan-auditor`, `compliance-auditor`, `code-reviewer` | `sonnet` | Revisione avversariale |

Il modello è indicato nel campo `model:` dell'intestazione di ogni file, che Claude Code rispetta quando l'agente sta in `.claude/agents/`. **Agenti configurati sulla piattaforma** (es. l'agente Registrar della sessione di pianificazione): sono una copia fuori dal repository. A ogni modifica di un file in `.claude/agents/` vanno aggiornati a mano (prompt e strumenti).

**Limite noto:** una sessione che gira su Opus e lancia agenti inline (workflow) non può scegliere Sonnet o Haiku: gli agenti ereditano il modello della sessione. Per rispettare questa regola, le sequenze vanno eseguite da una sessione Claude Code aperta nel repository, che usi gli agenti di `.claude/agents/`, oppure da una sessione impostata su Sonnet.

## Come si invocano

- **In Claude Code (consigliato):** gli agenti si trovano in `.claude/agents/` e vengono invocati per nome; il campo `model:` assicura Sonnet o Haiku.
- **In una sessione di pianificazione:** solo se la sessione non è su Opus, oppure se l'utente lo autorizza esplicitamente.
- **Nel repository:** quando esisterà la CI di v2, `code-reviewer` e `compliance-auditor` diventano controlli obbligatori sulle PR. Il loro esito `BLOCCA` fa fallire il controllo.

## Regole comuni a tutti gli agenti

1. In caso di conflitto prevalgono, in quest'ordine: `PRINCIPI.md`, poi `DECISIONS.md` (righe decise), poi il documento di dettaglio, poi il master plan.
2. Non inferire. Ogni rilievo distingue ciò che è stato **verificato** (con file e riga) da ciò che è **dedotto**.
3. Nessun agente decide al posto dell'utente. Una scelta di merito va riportata, non risolta.
4. Ogni agente scrive solo nel proprio perimetro. Gli agenti avversariali non modificano mai i file che esaminano.
5. Si scrive in italiano. Non si salvano segreti o credenziali da nessuna parte.

## Storico modifiche

| Versione | Data | Cosa è cambiato e perché |
|---|---|---|
| 1.0 | 2026-11-03 | Prima versione. |
| 1.1 | 2026-11-03 | Eliminate le copie dei prompt in `docs/agenti/`: fonte unica in `.claude/agents/`, per evitare disallineamenti (decisione dell'utente). Aggiunta la regola di riallineamento degli agenti configurati sulla piattaforma. |
