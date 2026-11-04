# Catalogo delle variabili di piattaforma

Documento trasversale, unico punto di verità per nome, default, intervallo, chi modifica e pagina di ogni variabile (DX-22). I documenti di dettaglio citano solo il nome. Il modello (registro versionato, ruoli, pagine) è di A6 (DX-14). Le pagine di UI sono provvisorie finché A6 non le fissa. Per i valori con vincolo di legge si aggiungerà il tipo "vincolo normativo" con il riferimento alla norma (nessuno tra quelli di C3).

| Nome | Default | Chi modifica | Intervallo ammesso | Pagina / sezione UI | Documento di origine |
|---|---|---|---|---|---|
| `hitl.request_ttl_hours` | 24 h (DA-C3-04) | superadmin: default e limiti min/max; admin agenzia: valore della propria agenzia entro i limiti | limiti iniziali 1–168 h (DA-C3-04, decisa); estremi assoluti dei limiti non definiti | Piattaforma → HITL (superadmin); Agenzia → Approvazioni (admin agenzia) | C3 |
| `hitl.sweeper_interval_minutes` | 60 min (proposta da validare, dal riferimento) | superadmin | non definito (proposta da validare) | Piattaforma → HITL | C3 |
| `hitl.resume_latency_p95_ms` | 2000 ms (proposta da validare) | superadmin | non definito (proposta da validare) | Piattaforma → HITL | C3 |
| `retention.hitl_payload_days` | 30 giorni dopo decisione o esecuzione (DECISIONS §5) | superadmin (default); override per agenzia: DA-C3-09 | min–max fissato nel contratto/DPA (DX-15, DX-16), non ancora definito | Piattaforma → Retention | C3 (classe DX-09, titolarità F6) |
| `retention.audit_decisions_months` | 12 mesi (DECISIONS §5) | superadmin (default); override per agenzia: DA-C3-09 | min–max da contratto/DPA, non ancora definito | Piattaforma → Retention | C3 (classe DX-09, titolarità F6) |
| `retention.traces_days` | 90 giorni (DECISIONS §5) | superadmin (default); override per agenzia: DA-C3-09 | min–max da contratto/DPA, non ancora definito | Piattaforma → Retention | C3 (classe DX-09, titolarità F6) |
| `retention.run_state_days` | 30 giorni dalla chiusura del run (DECISIONS §5) | superadmin (default); override per agenzia: DA-C3-09 | min–max da contratto/DPA, non ancora definito | Piattaforma → Retention | C3 (classe DX-09, titolarità F6) |
