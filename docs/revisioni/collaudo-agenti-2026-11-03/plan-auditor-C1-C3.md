# Report plan-auditor — C1 e C3 (sandbox collaudo)
Esito: BLOCCA

## Bloccanti
1. C1 App. B (l.195) e C3 §7 AI Act (art. 50): trattano `ai_generated` come aperto ("Non verificato se serva un campo `ai_generated`", "resta aperto"). DECISIONS §6 lo dà Decisa (2026-11-03, utente): campo obbligatorio nel contratto di output dei nodi agent (C1) con `model` e `prompt_ref`, mostrato da C3 all'approvatore. Il campo manca in C1 §4.1 e nel payload C3 §4.1: interfaccia C1->C3 rotta. [verificato]
2. C1 App. B: "Se il grafo LangGraph gira tutto dentro il job B1 o solo i nodi agente (§6, aperta)". DECISIONS §6: Decisa, solo i nodi agente dentro B1, grafo nel servizio di orchestrazione. [verificato]
3. C3 App. C DA-C3-04: "Resta aperta in DECISIONS.md"; opzione (b) "override per azienda" presentata come alternativa, e §6/§7 dicono solo "modificabile dal superadmin". DECISIONS: DA-C3-04 Decisa (utente): default 24 h, il superadmin fissa default e intervallo min/max, l'admin agenzia sceglie nell'intervallo. L'intervallo e il ruolo admin agenzia mancano. [verificato]
4. C3 §7 e AC-12: "se non riesce a leggerle, non cancella", "la retention non cancella". DX-17 (Decisa): per le cancellazioni programmate si usa l'ultimo valore valido versionato; si blocca solo l'azione. Contraddizione diretta. Anche per lo sweeper TTL non è chiaro quale ramo valga. [verificato]
5. DX-22 violata:
   - C1 §7 Performance: "È una soglia di test, non una variabile di piattaforma" (valore fisso dichiarato).
   - C1 §3 e C3 §6, §7: le variabili `c1.max_steps`, `c1.max_duration_ms`, `hitl.request_ttl_hours`, `hitl.resume_latency_p95_ms` hanno solo il superadmin. Mancano per tutte: default, chi modifica (admin agenzia dove applicabile) e intervallo ammesso (DX-13/15/16).
   - C1 criterio 10 vieta all'admin agenzia ogni modifica, in contrasto con DA-C3-04/DX-22.
   - Nessuno dei due documenti cita DX-22 né il catalogo delle variabili in A6 (grep: 0 occorrenze). [verificato]

## Da riportare
6. DX-05 aperta, interfaccia C1/B2/C3 non coerente: C1 §6 il nodo `tool` invoca B2 e conosce solo `denied`; il nodo `hitl` chiama `interrupt()`. C3 §6: "l'esecutore propone... A3 restituisce approvalRequired... parcheggia". B2/A3 dicono: `require_approval` -> `approval_required` + richiesta a C3. Non è definito chi parcheggia, né come un `require_approval` in un nodo `tool` passi al nodo `hitl`. [dedotto]
7. Eventi: C1 emette `workflow.run.interrupted` "verso C3"; C3 non consuma eventi e usa `hitl_*` (DX-07 aperta). Manca un evento di ripresa in C1. [verificato]
8. Dati C3 §4.3: `tool_key` vs `tool_id` (B2 catalogo) e `tool_ref` (C1); `company_id` senza richiamo a DX-07. [verificato sui nomi]
9. C1 `hitl` node: la WorkflowDefinition §4.1 non dichiara i campi del nodo hitl (TTL, riferimento alla chiamata) richiesti da C3 §4. [dedotto]
10. Intervallo min/max del TTL, valori con vincolo di legge e credenziali: le note "Da riportare" di DECISIONS §4 non compaiono in nessuno dei due documenti (C3 non segnala che min/max non è definito). [verificato]

## Minori
11. Stato obsoleto su DX-14: C1 §3/§9/§12 e C3 §3/§11 scrivono "DA RIPORTARE / proposta A6"; DX-14 è Decisa. F6 (DX-12) è decisa, solo l'ID è proposto. [verificato]
12. C1 §7 GDPR: "Non verificato come v2 la registri" la base giuridica, già decisa (DA-A1-08, §6). [verificato]
13. C3 stati: `pending -> approved/rejected/cancelled`, ma §6 usa `rejected:human_denied` ed evento `hitl_expired` senza stato `expired`. [dedotto]
14. Dipendenze: C1 elenca E3 e C3 elenca E3 in modo coerente; B5 dichiarato in ondata 2 (DX-08) in entrambi. Nessuna asimmetria trovata su C1<->C3. Template: 12 sezioni in ordine in entrambi; taglie L; nessuna stima temporale.

## Controllato
PRINCIPI (PV-01/02/03): nessuna violazione (nessun OTel come SDK, nessun servizio extra-UE). Righe DX-01..22, DA-C1-01/05, DA-C3-04/06, DA-E1-02/05, DA-B2-04, DA-A3-07, §4 e §6 di DECISIONS. Retention: C1/C3 rimandano a DX-09 con i default di §5, coerenti. Confronto con A3, B2, E1 per interfacce.

## Collaudo
- Modello: non so dichiararlo in modo verificato; dedotto: un modello Claude (versione non nota).
- Strumenti: bash, read, glob, grep, send_to_parent, risposta_plan_auditor.
- Strumento risposta_*: sì, `risposta_plan_auditor` presente. Lo uso per la risposta JSON, poi send_to_parent.
- Fonti lette: /tmp/test-plan-auditor/docs/{PRINCIPI.md, DECISIONS.md, C1-grafo-workflow.md, C3-punto-hitl.md}, docs/fonti/"Prompt e workflow.md" (righe 1-70), docs/fonti/"Piano generale.md" (solo grep), estratti di A3, B2, E1 (grep). Nessun file in /workspace/gravya-app-v2.
