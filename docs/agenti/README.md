# Agenti di governance del progetto

Versione 1.8, 2026-11-03.

Questi agenti mantengono allineati piano, registri e codice di Gravya v2. Ognuno ha un compito solo, un perimetro di scrittura definito e un formato di risposta fisso, così il loro esito si può leggere in modo automatico. Il prompt di ciascun agente è in un unico file, in `.claude/agents/` alla radice del repository: è la sola fonte. Questa cartella contiene questo README e, in `schemi/`, lo schema JSON dello strumento di risposta di ogni agente sulla piattaforma.

## Catalogo

| Agente | File | Compito | Scrive | Modalità |
|---|---|---|---|---|
| `coordinator` | [coordinator.md](../../.claude/agents/coordinator.md) | Pianifica, redige e mantiene i documenti di progetto; orchestra gli altri agenti secondo le sequenze sotto e riporta all'utente | Documenti di progetto e memoria di sessione (`/mnt/memory/gravya/`); i registri solo tramite il `registrar` | Orchestratore |
| `registrar` | [registrar.md](../../.claude/agents/registrar.md) | Aggiorna `DECISIONS.md`, `index.md`, lo Storico modifiche dei documenti dopo ogni decisione o modifica | `docs/DECISIONS.md`, `docs/index.md`, righe dello Storico | Collaborativa |
| `plan-auditor` | [plan-auditor.md](../../.claude/agents/plan-auditor.md) | Verifica la coerenza tra principi, decisioni, documenti di dettaglio e master plan | Solo il proprio report | Avversariale |
| `code-reviewer` | [code-reviewer.md](../../.claude/agents/code-reviewer.md) | Verifica che il codice di una PR implementi il documento di dettaglio, rispetti i criteri di accettazione e i principi | Solo il proprio report | Avversariale |
| `compliance-auditor` | [compliance-auditor.md](../../.claude/agents/compliance-auditor.md) | Cerca violazioni di GDPR, NIS2, AI Act e osservabilità AI (PV-01) in documenti e codice | Solo il proprio report | Avversariale |
| `doc-writer` | [doc-writer.md](../../.claude/agents/doc-writer.md) | Redige o aggiorna un documento di dettaglio secondo il template | Solo il file del documento assegnato | Collaborativa |
| `code-reader` | [code-reader.md](../../.claude/agents/code-reader.md) | Risponde a domande precise sul codice, con citazioni: ambito "storico" (gravya-app, kloudify, solo riferimento) o "v2" (stato reale rispetto ai documenti) | Solo il proprio report | Ricognizione, sola lettura |
| `implementer` | [implementer.md](../../.claude/agents/implementer.md) | Implementa codice e test di un documento approvato, un perimetro alla volta, su un branch dedicato; non fa merge | Codice e test sul proprio branch, il proprio report | Collaborativa |

## Quando si attivano

L'attivazione è deterministica: a ogni evento corrisponde una sequenza fissa, e l'ordine non dipende dal giudizio del momento.

| Evento | Sequenza |
|---|---|
| L'utente prende una decisione | `registrar` |
| Un documento di dettaglio viene creato o modificato | `plan-auditor` e `compliance-auditor` in parallelo, poi `registrar` |
| Una nuova ondata di documenti | `code-reader` con ambito "storico" (un dossier per documento, in parallelo), poi `doc-writer` (uno per documento, in parallelo, con il dossier), poi `plan-auditor` e `compliance-auditor`, poi `registrar` |
| Implementazione di un documento approvato | `implementer` sul perimetro deciso, poi la sequenza "Una PR di codice" |
| Una PR di codice | `code-reviewer` e `compliance-auditor` in parallelo, poi `registrar` se emergono divergenze dal piano |
| Un punto "non verificato" da chiarire, o lo stato reale dello sviluppo | `code-reader` (ambito "storico" o "v2") |
| Chiusura di un'ondata o di una milestone | `plan-auditor` sull'insieme completo, poi `registrar` |

**Regola di blocco.** Un esito `BLOCCA` di un agente avversariale ferma la sequenza. Il `registrar` registra il blocco e i rilievi, l'orchestratore li riporta all'utente, e si procede solo dopo una correzione o una decisione esplicita dell'utente. Un esito `RIPORTA` non ferma la sequenza, ma il punto finisce in `DECISIONS.md` come "Da riportare".

## Modello

Per decisione dell'utente (2026-11-03) gli agenti di governance **non usano Opus**. Unica eccezione: il `coordinator`, che orchestra e verifica gli altri, usa Opus (decisione dell'utente).

Modello e impegno di ogni agente stanno **solo** nell'intestazione del suo file in `.claude/agents/` (campi `model:` ed `effort:`). Questo README non li ripete: a ogni modifica si aggiorna il file dell'agente e, a mano, l'agente sulla piattaforma.

Nel file di ogni agente lo schema della risposta compare due volte: nella `description:` (la legge il coordinatore, che non vede il prompt) e nella sezione "Risposta (JSON)" del corpo (la legge l'agente, che non vede la descrizione). La duplicazione è necessaria: le due copie si modificano sempre insieme, nello stesso commit.

Quelle due copie sono **esempi** di risposta, leggibili da chi scrive o legge il task. Lo strumento di risposta sulla piattaforma (`risposta_{agente}`) richiede invece un JSON Schema vero (`properties`, `required`, `enum`): sta in `schemi/risposta_{agente}.json` e si incolla così com'è. Ogni modifica allo schema di un agente tocca, nello stesso commit, la descrizione, il corpo e il file in `schemi/`.

Il modello è indicato nel campo `model:` dell'intestazione di ogni file, che Claude Code rispetta quando l'agente sta in `.claude/agents/`. **Agenti configurati sulla piattaforma** (es. l'agente Registrar della sessione di pianificazione): sono una copia fuori dal repository. A ogni modifica di un file in `.claude/agents/` vanno aggiornati a mano (prompt e strumenti).

**Limite noto:** una sessione che gira su Opus e lancia agenti inline (workflow) non può scegliere Sonnet o Haiku: gli agenti ereditano il modello della sessione. Per rispettare questa regola, le sequenze vanno eseguite da una sessione Claude Code aperta nel repository, che usi gli agenti di `.claude/agents/`, oppure da una sessione impostata su Sonnet.

## Come si invocano

- **In Claude Code (consigliato):** gli agenti si trovano in `.claude/agents/` e vengono invocati per nome; il campo `model:` assicura Sonnet o Haiku.
- **In una sessione di pianificazione:** solo gli agenti predefiniti (sulla piattaforma o in `.claude/agents/`), che girano con il proprio modello. Mai agenti creati al volo da una sessione su Opus.
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
| 1.2 | 2026-11-03 | Aggiunta la colonna Impegno: tutti medio, code-reviewer alto (decisione dell'utente). |
| 1.3 | 2026-11-03 | Modello e impegno spostati solo nell'intestazione dei file degli agenti (`model:`, `effort:`), tolta la tabella dal README: un solo punto di verità. |
| 1.4 | 2026-11-03 | Lo schema della risposta è anche nella descrizione degli agenti; regola di aggiornamento congiunto delle due copie. |
| 1.5 | 2026-11-03 | Aggiunto l'agente `coordinator` (prompt dell'agente di pianificazione, invocabile). |
| 1.6 | 2026-11-03 | Agente rinominato `coordinator` (strumento `risposta_coordinator`), modello Opus: unica eccezione alla regola "niente Opus" (decisione dell'utente). |
| 1.7 | 2026-11-03 | Il `registrar` non scrive più nella memoria di sessione (evita doppioni di `DECISIONS.md`); la memoria è curata solo dal `coordinator`. |
| 1.8 | 2026-11-03 | Esito del collaudo degli agenti (decisioni dell'utente): nuovi agenti `code-reader` (Haiku) e `implementer` (Sonnet) con le loro sequenze; JSON Schema degli strumenti di risposta in `schemi/`; correzioni ai prompt: `doc-writer` (lettura completa delle fonti, niente metadati del task nel documento, i punti "da confermare" restano aperti, campo Dossier nel template), `plan-auditor` (lettura completa delle fonti), `registrar` (niente copie o backup, terminazioni di riga conservate). |
