# Revisione di conformità: A1, A3, B1 v1.5

Revisore: compliance-auditor · Data: 2026-11-04 · Repository c010ae8 · Registro norme v1.6 · Catalogo v1.2 (solo incoerenze di nome)

**Esito: RIPORTA.** Nessun BLOCCA: non ho trovato violazioni di una norma del registro, di PV-01/PV-02 o di una riga decisa di DECISIONS. Sono 13 rilievi da riportare e minori, riassunti qui sotto e dettagliati nel JSON di risposta.

## Rilievi

| ID | Doc | Gravità | Tema |
|---|---|---|---|
| R-01 | A1, A3 | da_riportare | Dati personali dei clienti finali dell'agenzia (`client_ids`, `record_ids`, `constraints`, nomi di dominio) in nodi, audit e decisioni append-only: A1 dice «non dati di clienti finali» |
| R-02 | A1, A3 | da_riportare | Scadenza e revoca di un mandato non arrivano ad A3 entro un termine misurabile («ultimo bundle valido») |
| R-03 | A3 | da_riportare | Il token di approvazione non è legato a tenant, tool e hash degli argomenti: HITL aggirabile per riuso su un'altra chiamata |
| R-04 | A3, A1 | da_riportare | Tool senza classe: nessun default-deny dichiarato; due fonti della classificazione (A1 `permission_key`, B2 `tool_class`) |
| R-05 | A3 | da_riportare | Invii verso terzi: nessuna classe nel vocabolario di `tool_class` che li identifichi, quindi DA-A3-09 e CA16 non sono realizzabili e PV-01 (marketing, art. 50) resta scoperto |
| R-06 | A3 | da_riportare | Il bundle è verificato solo con l'hash; la firma è «eventuale» e la chiave non è nel catalogo §15 |
| R-07 | B1 | da_riportare | Chiave del provider LLM iniettata dentro il job, dove gira codice guidato dall'LLM |
| R-08 | B1 | da_riportare | Il percorso delle chiamate LLM non è fissato; l'egress-proxy non dice che non registra corpi e URL |
| R-09 | B1 | da_riportare | `outputs_ref` senza durata (DX-21) con contenuti generati da dati delle agenzie |
| R-10 | A1, A3, B1 | da_riportare | Nessuna misura di cifratura (art. 32(1)(a) GDPR; NIS2 art. 21(2)(h); Reg. 2024/2690 all. 9) nei tre documenti |
| R-11 | A1, A3 | minore | Audit append-only protetto solo da permessi del database, senza verifica di integrità; A1 dice «protetto da modifiche» |
| R-12 | A3 | minore | `incident.nis2_flow_active` tra le variabili lette da A3: se illeggibile, per la regola di A3 il risultato è `deny`, contro DX-10 D1 |
| R-13 | A1 | minore | Percorso di lettura cross-tenant del superadmin sotto RLS FORCE non descritto; il log è garantito solo dall'applicazione |

Altre note non rilievi:
- B1 non dichiara che il runtime con container condivisi non va in produzione con dati reali finché DA-B1-02 è aperta (A3 dichiara che l'ondata 1 non va in produzione).
- Il «token monouso» (catalogo §18) per il `run_token` è già in B1 App. B.
- Il catalogo §15 non ha la riga della chiave di firma del bundle (R-06).

## Letture

- docs/A1-grafo-mandati.md: 1-251 di 251
- docs/A3-runtime-enforcement.md: 1-247 di 247
- docs/B1-agent-runtime-isolato.md: 1-238 di 238
- docs/DECISIONS.md: 1-260 di 260
- docs/PRINCIPI.md: 1-15 di 15 (letto nel giro precedente, non riletto)
- docs/revisioni/v1.5-ondata-1/brief-doc-writer-v1.5.md: 1-47 di 47
- docs/catalogo-variabili.md v1.2: 405-470 di 477 (§18, §19), più verifica automatica che ogni nome di variabile citato nei tre documenti compaia nel catalogo (tutti presenti)
- docs/norme-di-riferimento.md v1.6: righe 22, 28-50 (indice), 79-80, 483, 665-690 (N-DATAACT), più ricerche per parola chiave. Letture integrali del giro precedente: N-GDPR, N-DPF, N-NIS2, N-NIS2-IT, N-NIS2-REG, N-GAR-ADS (v1.4)
