# Principi vincolanti di Gravya v2

Questo documento raccoglie i principi che valgono sopra il master plan ("Piano generale"). Quando un documento di dettaglio, il master plan o il codice esistente sono in conflitto con uno di questi principi, prevale il principio. Il conflitto va segnalato, e **nel dubbio si riporta all'utente prima di decidere**.

| ID | Principio | Origine | Data |
|---|---|---|---|
| PV-01 | **Priorità alla conformità.** Gestione dei dati conforme a GDPR e NIS2, rispetto dell'AI Act e osservabilità AI sono la priorità di progetto. Prevalgono su aderenza al master plan, comodità tecnica e velocità. | Utente (DX-02) | 2026-11-03 |
| PV-02 | **Niente OpenTelemetry.** Il tracing e l'osservabilità AI sono DB-native, con dati sotto il controllo diretto di Gravya. La scelta è motivata da gestione dei dati, NIS2 e GDPR, ed è confermata dall'utente. Sostituisce il requisito del master plan "OpenTelemetry + GenAI semantic conventions". | Utente (DX-02); già presente in gravya-app (`timeline-engine.ts`, 2026-06-15) | 2026-11-03 |
| PV-03 | **Ripartenza pulita.** v2 si pianifica e si costruisce da zero, a partire dai documenti di dettaglio. `gravya-app` è materiale di riferimento (requisiti, lezioni apprese, soluzioni già validate), non una base di codice da estendere. Un componente esistente entra in v2 solo se un documento di dettaglio lo prevede esplicitamente, e in quel caso viene rivisto contro il nuovo contratto. | DX-01 | 2026-11-03 |

## Come si applicano

- Ogni documento di dettaglio dichiara come rispetta PV-01 nella §7 (Requisiti non funzionali), nella voce "Sicurezza e conformità".
- Una tecnologia del master plan che sposta dati fuori dal perimetro controllato (servizi gestiti extra-UE, piattaforme SaaS di eval o di tracing) è **una decisione da riportare all'utente**, non una scelta di default.
- Gli obblighi normativi già analizzati in `gravya-app/docs/compliance/` (ai-act, gdpr, nis2) e in `gravya-app-kloudify/docs/visione/controlli-e-conformita.md` sono requisiti di riferimento. In v2 vanno riverificati, non dati per scontati.
