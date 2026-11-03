# Report plan-auditor — 2026-11-03

Perimetro: ondata 1 completa (E1, E2, E3, A1, A3, B1, B2, C1, C3, tutti v1.4), DECISIONS.md, PRINCIPI.md.
Motivo: recepimento delle decisioni utente del 2026-11-03 (default di retention DX-09 §5, DX-13 superadmin, conferma delle righe Decisa in §6; DX-14 da riportare).

**Esito: RIPORTA.** Non ho trovato violazioni di PV-01/02/03 né di righe Decisa, e nessuna interfaccia rotta in modo bloccante. Restano incoerenze nel registro e tra documenti che richiedono una scelta dell'utente o una correzione del registrar.

## Rilievi

### R1 — da_riportare — DECISIONS.md, incoerenze interne di stato (verificato)
- §1 DX-09: "**Le durate di default non sono ancora fissate**: nessuno le ha indicate", mentre §5 dice "approvate dall'utente (2026-11-03)".
- §3 DA-A1-08: stato "Aperta", mentre §6 la dà "**Decisa**" e A1 v1.4 (App. C), A3, C1, C3, E2 la trattano come decisa.
- §3 DA-C3-06: stato "Aperta", mentre §6 decide "nelle tracce solo hash (DA-C3-06 (a))"; C3 §7 la cita come "decisa", ma C3 App. C (riga DA-C3-06) va ricontrollata.
- §3 DA-E1-08: "**Da riportare**", mentre DX-13 decide l'impianto (superadmin + log); E1 §App.C la indica come "decisa nell'impianto" con un residuo aperto.
Fonte: regola comune 1 (le righe Decisa prevalgono): il registro deve essere univoco. Azione: aggiornamento del registrar.

### R2 — da_riportare — Residuo di DA-E1-08 in contrasto con E3 ed E2 (verificato il testo, conflitto dedotto)
E1 App. C: "Resta aperto il solo residuo dell'opzione C, cioè se limitare il superadmin ai dati aggregati senza identificativi ... Raccomandazione: sì". Invece E3 §4 e §7 prevedono che il superadmin legga una singola traccia di produzione per promuovere un fallimento ("lettura di una traccia per promuovere un fallimento, fatta dal superadmin"); E2 §5 e B2 §7 prevedono letture puntuali cross-tenant. Se l'utente accetta la raccomandazione di E1, il flusso di promozione di E3 e il supporto di B2 ed E2 cambiano. Va deciso prima di chiudere l'ondata.

### R3 — da_riportare — Semantica del fail-closed sulle variabili di piattaforma diversa da documento a documento (verificato)
DX-13 dice solo "soggetta a fail-closed". Le applicazioni sono diverse:
- E1 §5: "si mantiene l'ultimo valore valido versionato" (fallback, non blocco);
- A3 §4: valore più restrittivo e, se la configurazione non è verificabile, `deny`;
- B1 §6: il submit fallisce;
- B2 §5: nessuna esecuzione (`error`);
- A1 §6: `503`;
- C3 AC-12: lo sweeper non chiude (quindi le richieste HITL restano aperte oltre il TTL);
- E3: exit 2.
L'"ultimo valore valido" di E1 è di fatto un ripiego (B1 lo vieta esplicitamente: "nessun ripiego su valori hardcoded"). Serve una regola comune, da fissare nel sottoprodotto di DX-14 o in DX-13.

### R4 — da_riportare — Proprietà del log degli accessi cross-tenant (verificato, lacuna dedotta)
E1 §4.1 elenca il "log degli accessi cross-tenant del superadmin" tra le proprie classi di dati, e A1 §7 lo elenca tra le classi prodotte da A1. A3, B2, C1, C3 ed E2 scrivono nel "log degli accessi" citando DA-E1-08, e nessun documento ne definisce uno schema unico. B2 App. B lo conferma: "il formato del log degli accessi cross-tenant (DA-E1-08)" non è verificato. Non è chiaro chi lo possiede (E1, A5 o il futuro A6): c'è il rischio di più tabelle. Da collegare a DX-14.

### R5 — minore — Nome del campo con la versione della configurazione (verificato)
A3 §4 usa `config_version` nel record `Decision`, E3 §4 usa `platform_config_version` nel report, B1 §7 parla di "versione delle variabili applicata" senza un nome. E1 §4.2 non mette nessuno dei due nella whitelist del segmento `decision`; se A3 lo scrivesse anche nella traccia, la validazione lo rifiuterebbe (dedotto). Da allineare con DX-07.

### R6 — minore — Evento `platform.config.changed` senza produttore (verificato)
A3 §4 lo consuma ("nome proposto, dipende da DX-07 e dal proprietario del registro, DX-14"). Nessun documento dell'ondata lo emette. È dichiarato come dipendenza da DX-14, quindi è accettabile, ma va inserito nel documento che nascerà da DX-14.

### R7 — minore — Classi di retention non coperte da §5 (verificato)
Per queste classi nessun documento assegna una durata, e i documenti lo dichiarano in App. B:
- A1: nodi ed edge del grafo, che potrebbero rientrare in "Artefatti di configurazione";
- B1: gli `outputs_ref`;
- B2: contatori di rate limit, esiti `idempotency_key`, token consumati.
È coerente con DX-09, ma servirà un'assegnazione in F6.

### R8 — minore — E2 §3: "identità di attore ... fornita da A3" (verificato)
A3 non dichiara di fornire identità: valuta decisioni. È una formulazione da riallineare a DX-14, che resta da riportare.

## Verifiche con esito positivo
- DX-14 è citata come proposta o da riportare, e mai come decisa, in A1, A3, B1, B2, C3, E1, E2 ed E3 (E3: "A6 se istituito").
- I default di retention di §5 sono riportati correttamente: 90 giorni, 12 mesi, 30 giorni, caso + 12 mesi, 30 giorni a fine contratto. Nessuna durata propria in contrasto.
- OpenTelemetry compare solo come vocabolario (DA-E1-05); non ci sono SDK, export, LangSmith o servizi extra-UE.
- Le righe Decisa di §6 sono recepite: coda fsync, tabella di audit minima in ondata 1, audit A1 nella stessa transazione, egress-proxy con destinazioni dichiarate, hash degli argomenti, report CI minimi. Le righe Aperta (latenza A3, opt-in extra-UE, art. 50, LangGraph in B1) sono rimaste aperte nei documenti.
- Nomi E1 §4.2 confrontati con E2 (`gravya.prompt.*`), E3 (`gravya.eval.case_id/pass`), A3/C1/C3 (`gravya.decision.kind` policy/router/hitl), B2 (`gravya.tool.args_hash`): combaciano.
- Taglie solo S/M/L; non ho trovato stime temporali.
