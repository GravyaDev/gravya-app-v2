# Brief comune ai doc-writer della v1.5 dell'ondata 1

Scritto dal coordinator il 2026-11-04 (sessione 7). Vale per i nove aggiornamenti A1, A3, B1, B2, C1, C3, E1, E2, E3 dalla v1.4 alla v1.5. Ogni doc-writer riceve nel task il proprio documento e i punti specifici; qui ci sono le regole comuni.

## Obiettivo

Portare ogni documento allo stato delle decisioni prese dall'utente tra il 2026-11-03 e il 2026-11-04, in un solo passaggio: dopo la v1.5 c'è un solo giro di revisione (plan-auditor e compliance-auditor), poi l'utente approva il documento e l'implementer può partire. Un documento che resta con decisioni superate o valori fissi blocca l'implementazione: questo è il criterio di "fatto".

## Fonti (in ordine di prevalenza)

1. `docs/PRINCIPI.md` (PV-01 esteso il 2026-11-04 a comunicazioni elettroniche, marketing e norme del registro).
2. Righe decise di `docs/DECISIONS.md`, per intero, compresi §4 (righe "Da riportare", alcune barrate perché chiuse), §5 (durate e precisazioni), §6 (punti e regole di processo), §7 (DA-CV-01..17). Il registrar sta aggiungendo in parallelo le decisioni del 2026-11-04 riportate sotto (DA-CV-18..23 e fine contratto): vale il testo di questo brief; se trovi differenze, segnalale in `non_verificato`.
3. `docs/catalogo-variabili.md` v1.2: unico punto di verità per le variabili. Nel documento citi solo il nome della variabile, mai default, minimi o massimi. La §16 del catalogo elenca, documento per documento, i valori fissi da sostituire: applicala. La §18 elenca le invarianti (non variabili): citale come invarianti con la decisione di riferimento.
4. `docs/norme-di-riferimento.md` v1.6: articoli e date si prendono da qui, non a memoria. Leggi almeno l'indice, il calendario, §9 e le schede che il documento cita.
5. Template e modello: `docs/fonti/Prompt e workflow.md`, `docs/fonti/Esempio A1 - completo.md`; master plan `docs/fonti/Piano generale.md`.

## Regole comuni

- **Catalogo: non lo modifichi.** È una regola di processo decisa dall'utente (DECISIONS §6, README agenti 1.17): le variabili nuove o cambiate le elenchi nel campo `variabili` della risposta, con nome, default, chi modifica, intervallo e pagina; il coordinator le unisce nel catalogo. Se ti serve una variabile che il catalogo non ha, proponila lì con un nome nello stile del catalogo (notazione puntata, unità nel nome).
- **Nessun valore fisso (DX-22).** Ogni durata, soglia, limite o parametro è una variabile del catalogo o un'invariante della §18. Le soglie dei criteri di accettazione citano la variabile; se un valore è una proposta senza decisione, resta "proposta da validare" nel catalogo, non nel testo.
- **Citazioni normative da correggere** (registro §9 e DECISIONS §4):
  - log, conservazione e integrità dei log: non "NIS2 (art. 21)", ma Reg. di esecuzione (UE) 2024/2690, allegato 3.2 e 11 (requisiti di progetto per la scelta "NIS2 compliant ready by design", DX-10; Gravya oggi non è soggetto NIS2);
  - "legal hold": non esiste più; si parla di "evidenze di incidente" (DECISIONS §5, con le basi e i limiti di C10 e D5);
  - notifica incidenti: preallarme 24 h, notifica 72 h, relazione finale entro un mese, destinatario CSIRT Italia, decorrenza dalla conoscenza; flusso presente ma non attivo (`incident.nis2_flow_active`), segnali sempre prodotti e conservati (DX-10, C2, D1, D6);
  - GDPR: Gravya responsabile (art. 28) per i dati delle agenzie; art. 33(2) senza ore per il responsabile, il termine verso le agenzie è un obbligo del DPA (DA-CV-08);
  - trasferimenti extra-UE: il Data Privacy Framework copre solo le organizzazioni USA dell'elenco DPF ed è impugnato (C-703/25 P); opt-in per destinazione dichiarata con strumento di trasferimento valido e sub-responsabile autorizzato, anche in UE (DA-B2-07, C9, D5, D7);
  - pseudonimizzazione: le linee guida EDPB 01/2025 sono solo in consultazione; gli identificativi pseudonimi nei trace sono dati personali (considerando 26);
  - AI Act: art. 50 applicabile dal 2.8.2026; etichetta "generato da AI" invariante; informativa a chi interagisce con un'IA (50(1)) invariante; marcatura leggibile da macchina anche del testo (50(2)), dettaglio in C1 e D1-D4; artt. 12, 14, 19, 26 solo buona pratica (DX-11) e comunque per l'alto rischio dal 2.12.2027 (calendario dopo il Reg. 2026/1744);
  - marketing (PV-01 esteso): ePrivacy, Codice privacy artt. 122 e 130 dove il documento tocca invii verso terzi o tracciamento; il dettaglio è di D1-D4.
- **Decisioni già prese:** le decisioni aperte del documento che DECISIONS ha chiuso vanno segnate come decise in Appendice C con la scelta; le scelte superate (per esempio C6 modificata da D2(a), C8 modificata da D2(b)) vanno corrette nel testo.
- **Dipendenze dell'ondata 2:** dove un valore o un meccanismo spetta ad A5, A6 o F6 (non ancora redatti), scrivi il rimando e lascia il punto aperto, senza inventarlo.
- **Lunghezza:** il template indica 1.200-2.000 parole; i documenti v1.4 sono intorno alle 4.000. Non allungare: sostituisci e taglia ciò che è superato.
- **Verificato e dedotto:** non dichiarare "verificato sul codice" ciò che non hai ricontrollato tu (lezione del collaudo, README 1.16). Per la v1.5 non ci sono dossier nuovi del code-reader (decisione dell'utente).
- **Storico:** versione 1.5 e una riga nello Storico modifiche con cosa è cambiato e perché.
- **Perimetro di scrittura:** solo il tuo file `docs/{ID}-*.md`. Nessun altro file, nessuna copia, nessun file in /tmp o in /mnt/memory, niente shell. Niente commit né push.
- Niente stime temporali (solo taglie S/M/L), niente OpenTelemetry come SDK o export (PV-02), italiano.

## Decisioni del 2026-11-04 non ancora in DECISIONS (raccomandazioni del coordinator confermate dall'utente con "Ok")

- **DA-CV-18:** i contenuti verso terzi (email, post, messaggi per conto delle agenzie) non sono una classe ALWAYS_HITL nell'ondata 1: decide l'admin agenzia, con audit (C7 (d)); da riesaminare con D1-D4. ALWAYS_HITL e MONEY_WRITE restano sempre con approvazione e non declassabili da UI (DA-CV-15).
- **DA-CV-19:** strumento di trasferimento e autorizzazione del sub-responsabile (riferimento al DPA, data) di ogni destinazione li imposta il superadmin, con fonte e audit; l'agenzia attiva l'opt-in solo su destinazioni con entrambi validi.
- **DA-CV-20:** le classi di segnali e audit ancora senza durata (segnali di incidente, audit delle configurazioni, autenticazioni, accessi alle credenziali) avranno un tetto provvisorio fissato dall'utente prima dell'avvio in produzione; l'ondata 1 non va in produzione.
- **DA-CV-21:** la sospensione delle scadenze per le evidenze di incidente vale solo per i dati di Gravya; per i dati delle agenzie serve un'istruzione nel DPA e un parere legale prima di F6.
- **DA-CV-22:** i backup scadono entro `retention.data_backup_days`, non oltre il massimo delle classi che contengono; al ripristino di un backup le cancellazioni già eseguite si riapplicano.
- **DA-CV-23:** sostituzione delle chiavi HMAC e di firma senza interruzione: due chiavi valide in parallelo durante il passaggio, con data di attivazione e disattivazione.
- **Fine contratto (Data Act art. 25(2), registro 1.6):** non più "restituzione o cancellazione entro 30 giorni", ma periodo di recupero dei dati di almeno 30 giorni dalla fine del periodo di passaggio, poi cancellazione; `retention.tenant_offboarding_days` diventa un minimo; qualificazione del SaaS come "servizio di trattamento dei dati" da confermare con un legale.
- **Processo (proposta (a) dell'utente):** un solo giro di revisione per documento; un esito RIPORTA va in DECISIONS senza secondo giro; solo un BLOCCA ferma il documento. Dopo l'approvazione dell'utente l'implementer parte (prima E1 e A1).
