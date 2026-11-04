# Catalogo delle variabili di piattaforma

**Versione:** 1.3 · **Data:** 2026-11-04 · **Registro delle norme:** v1.6 (`norme-di-riferimento.md`) · **Stato:** applica le decisioni dell'utente del 2026-11-04 sul catalogo (C1-C14, D1-D8, DA-CV-18..23 e fine contratto secondo il Data Act, dettaglio in §17.2), le variabili nuove dei documenti v1.5 dell'ondata 1 e le correzioni delle revisioni sulla v1.2; da validare con A5, A6 e F6. La versione 1.3 è redatta dal coordinator (unione delle variabili, regola di processo di DECISIONS §6).

## 1. Scopo e regole

Questo documento è l'unico punto di verità per nome, default, intervallo ammesso, chi modifica e pagina di UI di ogni durata, soglia, limite o parametro dei documenti dell'ondata 1 (A1, A3, B1, B2, C1, C3, E1, E2, E3). Lo prevede DX-22(c). La regola di fondo è quella dell'utente (DX-22): «TUTTO DEVE ESSERE CONFIGURABILE DA UI SUPERADMIN O ADMIN AGENZIA, NIENTE HARDCODED MAI». Ha un limite, deciso il 2026-11-04 (C7): **configurabile non vuol dire disattivabile**. I controlli di sicurezza e di conformità sono invarianti e stanno nel §18, non nelle tabelle delle variabili.

Indice: §2-§14 variabili per pagina di UI; §15 credenziali; §16 valori fissi trovati nei documenti; §17 non verificato e decisioni; §18 invarianti (comprese le invarianti di deploy); §19 sicurezza operativa e accessi.

Regole d'uso:

1. **I documenti di dettaglio citano solo il nome** della variabile, senza ripetere default e intervalli.
2. **Minimo, massimo e valori decisi stanno qui**, non solo i default. Il codice li legge dal registro e non li replica come costanti.
3. **Il modello** (registro versionato, ruoli, pagine di UI) è di A6 (DX-14, decisa il 2026-11-03). A6 non è ancora documentato (ondata 2): le pagine indicate sono **provvisorie** finché A6 non le fissa.
4. **Variabile non leggibile o non valida (DX-17).** Le azioni si bloccano (fail-closed). Le cancellazioni programmate usano l'ultimo valore valido versionato. In entrambi i casi parte un segnale ad A5. Per la chiusura per TTL di una richiesta HITL vale DA-C3-08 (a). Eccezione per le variabili `incident.*`: vale il limite di legge, con segnale (regola 6); per `incident.nis2_flow_active` non leggibile il flusso è trattato come attivo, con segnale (D1). Una nuova versione non leggibile con una durata più lunga non allunga la conservazione: le cancellazioni usano l'ultima versione valida (DX-17; lettura del redattore). Finché A5 non esiste (ondata 1), i segnali vanno nella tabella di audit minima (DECISIONS §6) e il blocco non è mai silenzioso.

   **Nessun valore valido (primo avvio, versioni tutte non valide; D3, DA-CV-17 (a)).** (1) Per le righe con stato «deciso» il primo valore valido è il default di questo catalogo. (2) Per le righe «da definire» l'azione che dipende dalla variabile si blocca. (3) Sono **esclusi dal blocco** la produzione e la conservazione dei segnali, l'audit e le notifiche. (4) Una classe di retention «da definire» **non viene scritta in produzione** finché A6 o F6 non fissano un valore, con una nuova versione del catalogo. Il punto (3) e il punto (4) si incrociano sulle classi di audit e sui segnali «da definire»: la durata provvisoria è aperta (DA-CV-20).
5. **Ogni modifica** è versionata e auditata (DX-13). Il superadmin gestisce le variabili di piattaforma; l'admin agenzia solo quelle indicate come tali.
6. **Vincoli normativi (DX-22(a), C1).** Ogni vincolo ha due elementi. (1) Il **limite di legge**: non modificabile da UI; cambia solo con una nuova versione di questo catalogo collegata a una versione del registro `norme-di-riferimento.md` (questa versione: v1.5). (2) Il **valore operativo**, impostato dal superadmin con motivazione e audit, che deve restare nei parametri di legge. Per ogni riga di §13 si indica il tipo di limite: **fisso** (il valore operativo non è modificabile), **minimo** (modificabile solo in aumento) o **massimo** (modificabile solo in diminuzione). Con una variabile `incident.*` non leggibile vale il limite di legge, con segnale ad A5 (C2).
7. **Conversione dei termini in mesi (C1).** I termini sono in giorni, con mese di calendario. Per un limite massimo («entro N mesi») il valore in giorni è la durata minima possibile di N mesi consecutivi (arrotondamento per difetto). Per un limite minimo («almeno N mesi») è la durata massima possibile di N mesi consecutivi (per eccesso). Valori usati: 1 mese massimo = 28 giorni; 3 mesi massimo = 89 giorni (febbraio-aprile, anno non bisestile); 6 mesi minimo = 184 giorni (luglio-dicembre). Le conversioni sono confermate aritmeticamente dal Reg. (CEE, Euratom) 1182/71 (registro v1.6, N-TERMINI: giorno dell'evento escluso, mese di calendario); per lettera quel regolamento vale per gli atti di Consiglio e Commissione, quindi applicarlo a GDPR, NIS2 e d.lgs. 138/2024 è un'interpretazione da confermare con un legale. I termini in ore (24 h, 72 h) decorrono dal momento della conoscenza, senza slittamento per festivi.
8. **Intervalli (DA-CV-02 (a), C12; D4, D5).** Finché un intervallo non è fissato da una decisione, vale la sola **validità tecnica**: tipo corretto, numero intero positivo (salvo indicazione diversa, per esempio 0-100 per le percentuali), unità coerente con il nome, minimo ≤ massimo, `_default` ≤ `_max`. In tabella si scrive «validità tecnica». Fanno eccezione le variabili della regola 11. In più valgono quattro **regole relazionali**: (a) il TTL di `b1.run_token.ttl_s` non supera la vita del run (`b1.job.wall_s_max`); (b) il TTL di un token di approvazione non supera il **TTL effettivo della richiesta HITL**, cioè il valore di `hitl.request_ttl_hours` in vigore per l'agenzia (in secondi), e non il massimo di piattaforma `hitl.request_ttl_hours_max` (D5); (c) `retention.traces_days` non è inferiore a `e1.partition_interval_months` (per eccesso, 31 giorni per mese), perché E1 cancella per partizione (E1 §4.1); (d) `retention.traces_days` più `e1.partition_interval_months` (per eccesso, 31 giorni per mese) non supera `retention.traces_days_max` (D5): la durata effettiva delle tracce, partizione compresa, resta dentro il massimo di retention. Per la finestra degli esiti di idempotenza vale il massimo `b2.idempotency.window_hours_max` (§7).
9. **Credenziali (DX-22(b)).** Non sono nel catalogo come valori: §15.
10. **Marketing.** Le variabili del diritto delle comunicazioni elettroniche e del marketing (direttiva ePrivacy, Codice privacy artt. 122 e 130, PV-01 esteso) sono rinviate a D1-D4: l'ondata 1 non ne introduce. I punti di contatto sono la disclosure art. 50 (§18), la classe di retention di consensi e opt-out (§2) e l'approvazione dei contenuti verso terzi, che non è un'invariante finché non è deciso se tali contenuti ricadono in una classe `ALWAYS_HITL` (DA-CV-18).
11. **Variabili con intervallo richiesto (D4).** Nessuna variabile di sicurezza e accessi di §19, né `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` e `e2.cache.max_ttl_s`, è attivabile in produzione senza un intervallo minimo-massimo **deciso**. I valori li fissano A5 e A6, con una nuova versione del catalogo. Dove oggi è scritto «validità tecnica» per queste variabili, non basta: la riga resta non attiva. `access.aggregate_min_group_size_count` ha già un minimo deciso (2).
12. **Sospensione per evidenze di incidente (D5).** La sospensione delle scadenze per i dati collegati a un incidente non è attivabile finché `retention.incident_evidence_max_total_months`, `retention.incident_evidence_review_interval_days` e `retention.incident_evidence_categories` sono «da definire». Per i dati delle agenzie vale in più l'istruzione del titolare nel DPA (C10).
13. **Destinazioni extra-UE (D5).** L'opt-in è attivabile solo con uno strumento di trasferimento e uno stato validi (§14). Lo stato lo aggiorna il superadmin con indicazione della fonte e audit, mai l'agenzia. Dopo la disattivazione per strumento caduto, la riattivazione richiede un nuovo opt-in dell'agenzia.

**Assunzione sui nomi.** La convenzione dei nomi (DX-07) è ancora aperta. Qui si assume la notazione puntata in minuscolo con l'unità nel nome. Suffissi: `_ms`, `_s`, `_minutes`, `_hours`, `_days`, `_months`, `_bytes`, `_mb`, `_usd`, `_eur`, `_percent`, `_count`. Se DX-07 cambia, si rinominano le righe qui e i documenti che le citano.

**Legenda delle colonne.** *Tipo*: `ordinaria`; `vincolo normativo` con la norma; `vincolo di progetto` (non di legge); `obbligo contrattuale (DPA)`. *Stato del valore*: `deciso` con riferimento; `proposta da validare` (esiste un valore che non deriva da una decisione); `da definire` (nessun valore: nessun documento né decisione lo fissa). *Intervallo*: minimo e massimo, oppure «validità tecnica» (regola 8).

**Regola retention (RR, C6).** Le durate di §2 sono **di sola lettura** finché l'intervallo minimo-massimo del contratto/DPA con le agenzie (DX-15, DX-16) non è definito (F6): valgono i valori di DECISIONS §5. Quando `<nome>_min` e `<nome>_max` sono valorizzati dal DPA, il superadmin può cambiare il default solo dentro l'intervallo, con motivazione e audit. Con `retention.tenant_override_enabled` (DA-C3-09) l'admin agenzia sceglie il valore per la propria agenzia, per le sole classi che sono dati dell'agenzia (riga `retention.<classe>.tenant_value`), dentro lo stesso intervallo. Un valore fuori intervallo non è valido (DX-16). La scelta di restituzione o cancellazione a fine contratto non dipende dall'override (D2). **Nuove classi senza valore (D3, D8):** il primo valore lo fissano F6 o A6, con una nuova versione del catalogo; finché manca, la classe non è scritta in produzione (regola 4), salvo segnali, audit e notifiche (DA-CV-20).

## 2. Retention (Piattaforma → Retention; Agenzia → Retention, pagina provvisoria)

Politica unica di default (DX-09). Durate approvate dall'utente il 2026-11-03 (DECISIONS §5); la verifica legale e sui contratti con le agenzie resta consigliata. Nessuna norma letta fissa un valore per queste classi: sono scelte di minimizzazione (GDPR art. 5(1)(e)). L'applicazione è di F6 (DX-12). Per la retention dei dati collegati a un incidente si usa «evidenze di incidente»: «legal hold» non ha base nell'art. 23 né nel Reg. 2024/2690 letto (registro §9, punto 4).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `retention.traces_days` | 90 giorni | sola lettura (RR) | `_min`/`_max` da definire (DPA, F6); ≥ `e1.partition_interval_months` (regola 8c); più `e1.partition_interval_months` non oltre `_max` (regola 8d) | ordinaria | deciso (DECISIONS §5, DX-09) | E1 (tracce e segmenti), C1, B2, C3 (tracce delle transizioni HITL). Contatori di perdita dei segmenti di E1 assegnati a questa classe: proposta da validare |
| `retention.runtime_events_days` | 90 giorni | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09) | A1 (`graph.*`), A3 (`policy.bundle.*`), B1 (`runtime.*`), C1 (`workflow.*`), E2 (`prompt.version.*`: assegnazione alla classe proposta da validare) |
| `retention.audit_decisions_months` | 12 mesi | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09; audit delle mutazioni A1: DECISIONS §4) | A1 (audit mutazioni), A3 (record di decisione), B2 (audit dei tool), C3 (decisioni e feedback), E2 (attivazioni) |
| `retention.cross_tenant_access_log_months` | 12 mesi | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09). Il log appartiene ad A6 (DX-18) | A1, A3, B1, B2, C1, C3, E1, E2, E3 |
| `retention.sensitive_payload_days` | 30 giorni dopo la decisione o l'esecuzione; poi resta l'hash | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09) | C3 (`arguments`, `context`), B2 (anteprime redatte) |
| `retention.run_state_days` | 30 giorni dopo la chiusura del run | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09) | C1 (stato), C3 (checkpoint in pausa), B1 (checkpoint via B5) |
| `retention.incident_evidence_months` | durata del caso + 12 mesi, sospendendo le altre scadenze per quei dati | sola lettura (RR) | `_min`/`_max` da definire; limiti complessivi nelle tre righe seguenti | ordinaria | deciso (DECISIONS §5, riga modificata il 2026-11-04: art. 23(4) direttiva, GDPR artt. 17(3)(e) e 5(2)). La sospensione non è attivabile finché le tre righe seguenti sono «da definire» (D5, regola 12). La base giuridica della conservazione è da confermare con un legale: l'art. 5(2) GDPR è accountability e non una base (registro, N-GDPR), l'art. 23(4) vale solo con Gravya in ambito NIS2 (DA-CV-21) | B1, B2, C1, C3, E1, E2 |
| `retention.incident_evidence_max_total_months` | da definire | sola lettura (RR) | validità tecnica; valore da F6 (C10). Senza valore la sospensione non è attivabile (regola 12) | ordinaria | da definire (F6). È il massimo della sospensione, durata del caso inclusa | A5, F6 e i documenti della riga precedente |
| `retention.incident_evidence_review_interval_days` | da definire | sola lettura (RR) | validità tecnica; valore da F6 (C10). Senza valore la sospensione non è attivabile (regola 12) | ordinaria | da definire (F6). Riesame periodico della sospensione | A5, F6 |
| `retention.incident_evidence_categories` | elenco chiuso di categorie di dati: contenuto da definire in F6 | da definire (F6) | elenco chiuso (C10); per i dati delle agenzie la categoria e la conservazione sono istruzione del titolare nel DPA. Senza elenco la sospensione non è attivabile (regola 12) | obbligo contrattuale (DPA) per i dati delle agenzie; ordinaria per i dati propri di Gravya | da definire (F6; C10) | A5, F6 |
| `retention.incident_signals_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (F6 o A6; A5 indica l'esigenza). I segnali di incidente si conservano sempre, anche a flusso spento (C2) e sono esclusi dal blocco della regola 4 (D3); nessuna classe è assegnata (dedotto); durata provvisoria: DA-CV-20 | A5 (tabella di audit minima in ondata 1), tutti i produttori di segnali |
| `retention.eval_reports_months` | 12 mesi | sola lettura (RR) | `_min`/`_max` da definire | ordinaria | deciso (DECISIONS §5, DX-09) | E3 (report e segmenti `eval_case`), E1 |
| `retention.tenant_offboarding_days` | 30 giorni di periodo di recupero dei dati, contati dalla fine del periodo di passaggio; poi cancellazione, salvo obblighi di legge | sola lettura (RR) | **minimo 30 giorni, solo in aumento** (limite di legge, non modificabile da UI); `_max` da definire in F6, non inferiore a 60 giorni dall'avvio del passaggio (registro v1.6 §9) | vincolo normativo condizionato: Data Act art. 25(2) (periodo transitorio fino a 30 giorni, periodo di recupero di almeno 30 giorni, cancellazione solo dopo), se il SaaS di Gravya è un «servizio di trattamento dei dati» (art. 2(8), da confermare con un legale) | deciso (DECISIONS §5, riga corretta il 2026-11-04). È il «periodo di uscita» di `retention.tenant_offboarding_choice`. L'art. 29 (costi di passaggio dal 12.1.2027) resta da riportare (DECISIONS §4) | A1, B2, C1, C3, E1, E2 |
| `retention.config_audit_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (A6 o F6). Audit delle modifiche alle variabili (`platform.config.changed`, DX-21); classe di audit, esclusa dal blocco della regola 4 (D3); durata provvisoria: DA-CV-20 | A6, tutti |
| `retention.auth_events_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (A6 o F6). Autenticazione e gestione utenti (Reg. 2024/2690 all. 3.2.3(b), (d): «se opportuno»); classe di audit, esclusa dal blocco della regola 4 (D3); durata provvisoria: DA-CV-20 | A6 |
| `retention.credential_access_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (A6 o F6). Accessi e modifiche alle credenziali (§15); classe di audit, esclusa dal blocco della regola 4 (D3); durata provvisoria: DA-CV-20 | A6 |
| `retention.consent_optout_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (F6, con D1-D4). Consensi, opt-out e liste di soppressione (GDPR art. 17(1)(c); Codice privacy art. 130, ◐). Non scritta in produzione finché manca il valore (regola 4) | F6, D1-D4 |
| `retention.log_backup_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (F6 o A6; A5 indica l'esigenza). Copie di backup dei log «per un periodo predefinito» (Reg. 2024/2690 all. 3.2.5, che non indica la durata) | A5, E1 |
| `retention.data_backup_days` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (F6). Il Reg. 2024/2690 rimanda i periodi di conservazione dei backup agli «obblighi commerciali e normativi» del soggetto (all. 4.2.2(f), letto) e non fissa nessun numero: non è un vincolo normativo. Vale l'art. 5(1)(e) GDPR; propagazione delle cancellazioni ai backup: DA-CV-22 | F6 |
| `retention.pseudonym_map_months` | da definire | sola lettura (RR) | validità tecnica | ordinaria | da definire (F6). Mappa di re-identificazione degli pseudonimi (GDPR art. 4(5), considerando 26; DECISIONS §5 «da verificare»). Non scritta in produzione finché manca il valore (regola 4) | F6, E1, A1 |
| `retention.class_override_enabled` | falso | superadmin | solo falso/vero. Vero solo quando l'intervallo `_min`/`_max` della classe è definito, come per l'agenzia (D3, DA-CV-10 (a)) | ordinaria | deciso (DX-09 per il default falso; D3 per la condizione) | E1 (`retention_class`), tutti |
| `retention.tenant_override_enabled` | falso | superadmin | vero solo quando l'intervallo del contratto/DPA è definito (F6). Non governa `retention.tenant_offboarding_choice` (D2) | ordinaria | deciso (DA-C3-09, DX-15) | tutti |
| `retention.<classe>.tenant_value` (nome come in DECISIONS §5; `<classe>` è il nome della durata senza il prefisso `retention.`, per esempio `retention.traces_days.tenant_value`). **Perimetro:** le sole classi che sono dati dell'agenzia: `traces_days`, `runtime_events_days`, `audit_decisions_months`, `sensitive_payload_days`, `run_state_days` (dedotto dalla natura dei dati di DECISIONS §5; F6 conferma). Non hanno la variabile per agenzia: i log e gli audit propri di Gravya (`cross_tenant_access_log_months`, `config_audit_months`, `auth_events_months`, `credential_access_months`), le evidenze e i segnali di incidente (C2, C10), `eval_reports_months` (dati sintetici), `tenant_offboarding_days`, `consent_optout_months`, `log_backup_months`, `data_backup_days`, `pseudonym_map_months`; una di queste classi può averla solo per decisione di F6 con una nuova versione del catalogo | il valore di piattaforma della classe | admin agenzia, per la propria agenzia | tra `<classe>_min` e `<classe>_max`; attiva solo con `retention.tenant_override_enabled` | ordinaria (istruzione del titolare, GDPR art. 28(3)(a)) | deciso (C6, DX-15) per l'esistenza; perimetro dedotto; intervalli da definire (DPA, F6). Attore, MFA (DX-20), `config_version` e riferimento alla versione del DPA in audit: dettaglio di A6/F6 | tutti |
| `retention.tenant_offboarding_choice` | esportazione disponibile per tutto il periodo di uscita (`retention.tenant_offboarding_days`), poi cancellazione | admin agenzia | restituzione oppure cancellazione (GDPR art. 28(3)(g)). **Sempre disponibile all'agenzia, indipendente da `retention.tenant_override_enabled`** (D2 (a), DA-CV-12, opzione (b)) | ordinaria (scelta del titolare). Il default è da riverificare sul Data Act (artt. 25 e 29, registro ◐) | deciso (D2) per la disponibilità e il default; D2 modifica la riga di C6 che la legava all'override | A1, C1, E1, E2, F6 |

**Famiglia protetta (DX-16).** Ogni variabile `retention.*_days` o `retention.*_months` ha due variabili gemelle di intervallo, `<nome>_min` e `<nome>_max`, con lo stesso suffisso di unità. Default: da definire (DPA, F6). Le modifica il superadmin con motivazione e audit, solo per riportare i valori definiti dal DPA. Tipo: ordinaria. Stato: da definire.

**Classi senza durata variabile** (DX-21: le assegna F6 e i documenti le citano come tali): artefatti di configurazione (versioni di prompt, bundle di policy, definizioni di workflow, catalogo tool: «per tutta la durata del servizio», DECISIONS §5); nodi ed edge del grafo A1 (classe non assegnata: A1 App. B); `outputs_ref` di B1; contatori di rate limit e token di approvazione consumati di B2; token consumati. Gli esiti per `idempotency_key` hanno ora la finestra `b2.idempotency.window_hours` (§7). Per le altre categorie nessuna durata è fissata in DECISIONS §5.

## 3. HITL (Piattaforma → HITL; Agenzia → Approvazioni)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `hitl.request_ttl_hours` | 24 h | superadmin: default e limiti; admin agenzia: valore della propria agenzia entro i limiti (DA-C3-04) | tra `hitl.request_ttl_hours_min` e `hitl.request_ttl_hours_max` | ordinaria | deciso (DA-C3-04, 2026-11-03) | C3 (§6, sweeper) |
| `hitl.request_ttl_hours_min` | 1 h | superadmin | intero positivo e ≤ `hitl.request_ttl_hours_max` (validità tecnica) | ordinaria | deciso (DA-C3-04) | C3 |
| `hitl.request_ttl_hours_max` | 168 h | superadmin | intero ≥ `hitl.request_ttl_hours_min` (validità tecnica) | ordinaria | deciso (DA-C3-04) | C3 |
| `hitl.sweeper_interval_minutes` | da definire | superadmin | validità tecnica; da fissare con misura, con il ritardo massimo tra scadenza e chiusura come criterio (DA-CV-03 (a)) | ordinaria | da definire | C3 (§6, AC-6) |
| `hitl.resume_latency_p95_ms` | 2000 ms | superadmin | validità tecnica | ordinaria | proposta da validare | C3 (§7) |
| `hitl.approval_required_default` | vero | admin agenzia, per azienda, cliente e task, **escluse** le classi `ALWAYS_HITL` e `MONEY_WRITE`, che richiedono sempre approvazione umana (§18). Per i contenuti verso terzi l'approvazione la decide l'admin agenzia, con audit dell'attore (C7). **Default di piattaforma: sola lettura, vero** (D3, DA-CV-15 (a)); nessuno lo modifica da UI. La classificazione `ALWAYS_HITL` e `MONEY_WRITE` non è declassabile da UI (§18) | vero/falso (per agenzia, azienda, cliente e task) | ordinaria | requisito ripreso da C3 §3; limiti dalle decisioni C7 e D3 | C3, A3 |

Chiusura per TTL (DA-C3-08 (a)): scadenza programmata che usa l'ultimo valore valido versionato; la chiusura porta solo alla non esecuzione. Se il valore letto è fuori da `hitl.request_ttl_hours_min`/`_max`, non è valido (DX-16, DX-17).

## 4. Enforcement e latenze (Piattaforma → Enforcement e latenze)

Le tre soglie di latenza sono budget separati, usati per gli alert e non per bloccare (DECISIONS §6, decisa il 2026-11-03: «tutti proposte da validare con misura»). Per evitare la doppia scrittura, record di decisione di A3 e audit `tool.invoked` di B2 stanno in un'unica transazione eseguita da B2.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a3.latency.eval_p99_ms` | 5 ms (valutazione, escluso il trasporto) | superadmin | validità tecnica | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3 (§7, CA5) |
| `a3.latency.persist_p99_ms` | 20 ms (salvataggio sincrono del record) | superadmin | validità tecnica | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3, B2 |
| `a3.latency.total_p99_ms` | 25 ms (totale per azione) | superadmin | validità tecnica. Con i default proposti vale 5 + 20 = 25 ms; il legame tra i tre valori non è fissato da DECISIONS §6 | ordinaria | budget deciso (DECISIONS §6); valore proposta da validare con misura | A3, B2 |
| `a3.bundle.max_age_s` | da definire | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11, D4; valori con A5 e A6). A3 richiede un valore minimo valido per il ripiego fail-closed (A3 §4) | ordinaria | da definire | A3 (§4, §6) |
| `a3.eval.timeout_ms` | da definire | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11, D4) | ordinaria | da definire | A3 (§4, §6, CA11) |
| `a3.record.persist_timeout_ms` | da definire | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11, D4) | ordinaria | da definire | A3 (§4, §6), B2 (transazione unica) |

## 5. Grafo dei mandati (Piattaforma → Grafo mandati)

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a1.delegation.max_depth` | 3 | superadmin | validità tecnica, minimo 1. Si applica alle nuove deleghe, non retroattivamente | ordinaria | proposta da validare (A1 §4.5) | A1 (§4.2, CA5, CA11) |
| `a1.artifact.max_properties_bytes` | 4 KB (A1 non dice se 4.000 o 4.096 byte) | superadmin | validità tecnica | ordinaria | proposta da validare (A1 §4.5) | A1 (CA7) |
| `a1.sweeper.interval_minutes` | da definire | superadmin | validità tecnica; da fissare con misura, con il ritardo massimo tra `valid_until` e lo stato `expired` come criterio (DA-CV-03 (a)) | ordinaria | da definire (A1 §4.5) | A1 (§6, CA4) |

## 6. Runtime agenti (Piattaforma → Runtime agenti)

Per i limiti del job B1 §4 parla di «tetti e valori di default» come variabili di piattaforma; il `JobSpec` può solo restringerli. Si assumono due variabili per limite, `_default` e `_max` (non verificato: B1 non dice se siano distinte). I valori del sistema precedente (300 s di timeout arq in gravya-app; 10 minuti, $2 e 8 giri di tool per run, riferiti da kloudify) sono riferimenti e non default di v2.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `b1.job.wall_s_default` | da definire | superadmin | validità tecnica; ≤ `b1.job.wall_s_max` | ordinaria | da definire (B1 §4, senza valore) | B1 (§4, CA11) |
| `b1.job.wall_s_max` | da definire | superadmin | validità tecnica | ordinaria | da definire | B1 |
| `b1.job.memory_mb_default` | da definire | superadmin | validità tecnica; ≤ `b1.job.memory_mb_max` | ordinaria | da definire | B1 (§4) |
| `b1.job.memory_mb_max` | da definire | superadmin | validità tecnica | ordinaria | da definire | B1 |
| `b1.job.pids_default` | da definire | superadmin | validità tecnica; ≤ `b1.job.pids_max` | ordinaria | da definire | B1 (§4) |
| `b1.job.pids_max` | da definire | superadmin | validità tecnica | ordinaria | da definire | B1 |
| `b1.job.tool_turns_default` | da definire | superadmin | validità tecnica; ≤ `b1.job.tool_turns_max` | ordinaria | da definire | B1 (§4) |
| `b1.job.tool_turns_max` | da definire | superadmin | validità tecnica | ordinaria | da definire | B1 |
| `b1.job.cost_usd_default` | da definire | superadmin | validità tecnica; ≤ `b1.job.cost_usd_max` | ordinaria | da definire | B1 (§4) |
| `b1.job.cost_usd_max` | da definire | superadmin | validità tecnica | ordinaria | da definire | B1 |
| `b1.job.kill_grace_s` | 5 s oltre `wall_s` | superadmin | validità tecnica | ordinaria | proposta da validare (B1 CA4) | B1 (CA4) |
| `b1.host.max_concurrent_jobs` | da definire | superadmin | validità tecnica | ordinaria | da definire (B1 §7, senza valore) | B1 (§7) |
| `b1.tenant.max_concurrent_jobs` | da definire | superadmin | validità tecnica. Unità: job concorrenti (DA-CV-06 (a)) | ordinaria | da definire (B1 §7, senza valore) | B1 (§7) |

## 7. Tool gateway (Piattaforma → Tool gateway)

Il catalogo dei tool (B2 §4) contiene anche «limiti di default» per tool, gestiti dall'interfaccia amministrativa del catalogo del superadmin (B2 §5). Il rate limit ha tre limiti indipendenti, per agente, per tool e per tenant, e vince il più restrittivo (DA-CV-06 (a)). La finestra di misura è quella del nome (al minuto): se B2 la rende configurabile serve un'altra variabile (§17.1, punto 11). Gli ultimi quattro parametri sono **impliciti**: nessun documento li fissa, ma servono al comportamento descritto (token monouso, coda di recupero «fino a riuscirci», «restituisce il primo esito» per `idempotency_key`).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `b2.rate_limit.agent_calls_per_minute` | da definire | superadmin | validità tecnica | ordinaria | da definire (B2 §5, senza valore) | B2 (§5, CA4) |
| `b2.rate_limit.tool_calls_per_minute` | da definire (è il «limite di default» del tool nel catalogo, B2 §4) | superadmin | validità tecnica | ordinaria | da definire (B2 §5, senza valore) | B2 (§5, CA4) |
| `b2.rate_limit.tenant_calls_per_minute` | da definire | superadmin | validità tecnica | ordinaria | da definire (B2 §5, senza valore) | B2 (§5, CA4) |
| `b2.recovery_queue.retry_interval_s` | da definire | superadmin | validità tecnica; da fissare con misura (DA-CV-03 (a)) | ordinaria | da definire (parametro implicito, B2 §6) | B2 (§6, CA10) |
| `b2.idempotency.window_hours` | da definire | superadmin | validità tecnica; ≤ `b2.idempotency.window_hours_max` (D5) | ordinaria | da definire (parametro implicito, B2 §6; classe di retention da F6, C8) | B2 (§6) |
| `b2.idempotency.window_hours_max` | da definire | superadmin | validità tecnica; valore da F6 (D5). Gli esiti possono contenere dati dell'esito (dedotto): il massimo evita una conservazione fuori dalla retention | ordinaria | da definire (D5) | B2 (§6), F6 |
| `b1.run_token.ttl_s` | da definire | superadmin | validità tecnica; ≤ `b1.job.wall_s_max` (regola 8a). Il token è uno solo, emesso da B1 e verificato da B2 (D3, DA-CV-13 (a)): `tool_grant_ref` e `run_token` sono lo stesso oggetto e non serve un'altra variabile | ordinaria | da definire (parametro implicito, B2 §3-§4) | B1, B2 |
| `hitl.approval_token.ttl_s` | da definire | superadmin | validità tecnica; non oltre il TTL effettivo della richiesta HITL in secondi (regola 8b, D5) | ordinaria | da definire (parametro implicito, C3 §6, B2 §6) | C3, B2, A3 |

## 8. Workflow (Piattaforma → Workflow)

Il campo `max_steps`/`max_duration_ms` di una definizione può solo restringere i tetti di piattaforma (C1 §4.1).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `c1.max_steps` | 500 | superadmin | validità tecnica, minimo 1 | ordinaria | proposta da validare (C1 §4.1) | C1 (§4.1, §6, CA10) |
| `c1.max_duration_ms` | 300000 ms (5 min) | superadmin | validità tecnica | ordinaria | proposta da validare (C1 §4.1) | C1 (§4.1, §6, CA10) |

## 9. Tracing (Piattaforma → Tracing)

La soglia di allarme sulla perdita di segmenti non è una variabile di E1: E1 invia ogni perdita ad A5 senza soglia locale, e la soglia vive in A5 (DA-CV-07 (b), C12).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `e1.write_buffer_size` | da definire (unità non specificata da E1: segmenti o byte) | superadmin | validità tecnica | ordinaria | da definire (E1 §5, «non fissati») | E1 (§5, §6) |
| `e1.partition_interval_months` | 1 (partizioni mensili) | superadmin | validità tecnica; `retention.traces_days` non inferiore a questo valore (regola 8c) e, sommato a `retention.traces_days`, non oltre `retention.traces_days_max` (regola 8d). Effetto sulle partizioni esistenti non descritto | ordinaria | proposta da validare (E1 §4.1) | E1 (§4.1) |
| `e1.attributes.max_value_bytes` | da definire | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11): è il limite che impedisce al testo libero di entrare nei valori degli attributi | ordinaria | da definire (proposta di E1 v1.5) | E1 (§4.2, §5, §7) |

## 10. Prompt (Piattaforma → Prompt)

Il controllo anti-PII dei template (`e2.template.pii_check_mode`) non è una variabile: è sempre `block` (§18).

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `e2.cache.max_ttl_s` | 60 s | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11, D4; valori con A5 e A6); il default è una proposta da validare | ordinaria | proposta da validare (E2 §7) | E2 (§7) |
| `e2.rollback.propagation_max_s` | 60 s | superadmin | intervallo minimo-massimo richiesto prima dell'attivazione in produzione (regola 11: è un'età massima di E2, come `e2.cache.max_ttl_s`) | ordinaria | proposta da validare (E2 §7) | E2 (§7, CA2, CA13) |

## 11. Eval (Piattaforma → Eval)

Il job CI legge un'istantanea versionata delle variabili (E3 §5). Finché il registro non esiste l'istantanea è un file nel repository modificabile solo tramite PR: è un ripiego dell'ondata 1, non soddisfa DX-22 (§17.1, punto 9). Il gate ha **zero fallimenti bloccanti** come invariante (§18); `eval.gate.pass_rate_min_percent` riguarda solo i casi non bloccanti.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `eval.gate.pass_rate_min_percent` | 90 | superadmin | validità tecnica, 0-100; solo per i casi non bloccanti | ordinaria | proposta da validare. Il default è oggetto di DA-E3-07 (aperta in DECISIONS: E3 AC4 propone 90 % più zero bloccanti; DA-E3-07 raccomanda solo report sui casi non bloccanti) | E3 (§5, AC4) |
| `eval.run.cost_cap_usd` | da definire | superadmin | validità tecnica | ordinaria | da definire (E3 §7, senza valore) | E3 (§5, §6, §7) |
| `eval.run.timeout_s` | da definire | superadmin | validità tecnica | ordinaria | da definire (E3 §5, senza valore) | E3 (§5) |
| `eval.ingestion.timeout_s` | da definire | superadmin | validità tecnica | ordinaria | da definire (E3 §6, senza valore) | E3 (§6, R4 e R5) |
| `eval.run.repetitions_count` | 1 | superadmin | validità tecnica | ordinaria | proposta da validare; DA-E3-05 aperta | E3 (DA-E3-05) |

## 12. Soglie di prestazione (Piattaforma → Soglie di prestazione)

Obiettivi misurabili con metrica a runtime: servono sia per gli alert sia come soglia dei criteri di accettazione, così il test legge lo stesso valore. Nel catalogo stanno le sole soglie con metrica a runtime; i campioni dei test (100 esecuzioni, 10.000 decisioni, 30 casi, 1.000 chiamate, N=10, dimensioni dei dataset) restano parametri dei test e citano il catalogo (DA-CV-04 (b), C12). Le tre soglie di A3 sono in §4.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `a1.read_batch_p99_ms` | 100 ms (≤ 1.000 mandati per tenant) | superadmin | validità tecnica | ordinaria | proposta da validare (A1 §7) | A1 (§7, CA9) |
| `a1.write_p99_ms` | 50 ms | superadmin | validità tecnica | ordinaria | proposta da validare (A1 §7) | A1 (§7, CA9) |
| `b1.job.start_overhead_p95_ms` | 3000 ms | superadmin | validità tecnica | ordinaria | proposta da validare (B1 §7, CA8) | B1 (§7, CA8, DA-B1-01) |
| `b2.overhead_p95_ms` | 50 ms (escluso il tool) | superadmin | validità tecnica | ordinaria | proposta da validare (B2 §7, CA8) | B2 (§7, CA8) |
| `c1.node_overhead_p95_ms` | 50 ms (per nodo, esclusi LLM e tool) | superadmin | validità tecnica | ordinaria | proposta da validare (C1 §7) | C1 (§7) |
| `e1.overhead_p95_ms` | 5 ms per segmento | superadmin | validità tecnica | ordinaria | proposta da validare (E1 §5, §7) | E1 (§5, §7, CA6) |
| `e2.resolve_render_p99_ms` | 5 ms (da cache) | superadmin | validità tecnica | ordinaria | proposta da validare (E2 §7) | E2 (§7) |

## 13. Incidenti e conformità (Piattaforma → Incidenti e conformità)

**Contesto (DX-10, decisa).** Oggi Gravya non è soggetto NIS2. La progettazione è «NIS2 compliant ready by design» (proposte (a)-(c) confermate il 2026-11-04). A5 predispone il flusso di notifica come funzione presente ma non attiva finché Gravya non diventa soggetto NIS2 o un contratto con un'agenzia obbligata non lo richiede. Qualificazione di Gravya come fornitore di cloud computing e dimensione non sono accertate (registro, N-NIS2): le righe `incident.cloud.*` e `incident.financial_*` si applicano solo se Gravya è fornitore cloud in ambito. I criteri del Reg. (UE) 2024/2690 sono «esaustivi» (considerando 30): una soglia interna più alta di quella del regolamento non è ammessa. Una soglia più bassa è invece una **scelta di progetto** (D6): fa classificare come significativi anche incidenti che il regolamento non considera tali, e la notifica per la parte oltre i criteri è volontaria (art. 26 d.lgs. 138/2024, N-NIS2-IT ✔; interpretazione da confermare con un legale).

**Regole (C1, C2, C4, C5).**
- **Segnali sempre prodotti.** Anche a flusso spento i segnali di incidente si producono e si conservano sempre (ondata 1: tabella di audit minima, DECISIONS §6, finché A5 non esiste). A flusso spento non parte solo la notifica verso l'esterno. Classe di retention dei segnali: `retention.incident_signals_months` (§2).
- **Limite di legge e valore operativo.** Per ogni riga di §13.2: il limite di legge non è modificabile da UI (regola 6); il valore operativo lo imposta il superadmin con motivazione e audit, solo nel verso ammesso. Il minimo (o massimo) operativo, cioè quanto lontano dal limite si può spingere il valore, non è fissato da alcuna norma né decisione: da definire in A5, prima dell'attivazione del flusso. Con valore non leggibile: limite di legge, con segnale.
- **Più restrittivo.** Per i termini di notifica significa più breve; per le soglie di significatività, che qualifichino più incidenti (soglie più basse, finestra più lunga).
- **Variabili GDPR sempre attive** (13.3), indipendenti da `incident.nis2_flow_active`: invariante (§18).
- **Valore non leggibile.** Per le righe con un limite di legge vale il limite di legge, con segnale. Per `incident.nis2_flow_active` vale «flusso attivo», con segnale. Per le righe senza limite di legge (`incident.nis2.csirt_channel`, `incident.nis2.csirt_contact`, `incident.initial_assessment_max_hours`, `incident.scope_review_interval_days`) le notifiche non sono bloccate (D3, regola 4); quale valore usare è da definire in A5 (non verificato, §17.1 punto 20).

### 13.1 Flusso, destinatario e valutazione iniziale

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `incident.nis2_flow_active` | falso | superadmin, con motivazione e audit. **Accensione:** obbligatoria quando Gravya diventa soggetto NIS2 e al contratto con un'agenzia soggetta NIS2 che la richiede (DX-10 (b), D1); l'accertamento è umano. **Spegnimento** (da vero a falso): solo con la valutazione scritta di un legale o del DPO e l'approvazione di entrambe le persone con accesso superadmin (D1, DA-CV-09) | falso/vero. Se non leggibile: flusso trattato come attivo, con segnale ad A5 (D1) | interruttore di una funzione normativa, con condizione di spegnimento | deciso (DX-10 (b), C2, D1) | A5, A1, A3, B1, B2, C1, C3, E1, E2 (segnali) |
| `incident.scope_review_interval_days` | da definire | superadmin, con motivazione e audit | validità tecnica; valore da A5 | vincolo di progetto (non di legge) | da definire (D1). Riesame periodico dell'ambito NIS2 di Gravya (qualificazione come fornitore cloud, dimensione, contratti con agenzie soggette NIS2): il registro non accerta l'ambito (N-NIS2) | A5 |
| `incident.nis2.csirt_channel` | da definire | superadmin, con motivazione e audit | **elenco chiuso di canali ufficiali ACN** (D6). Candidati nel registro v1.5, letti solo in estratti (◐): Portale dei Servizi ACN (maschera NIS) e Portale segnalazioni CSIRT Italia; da riverificare sulla pagina ACN prima di usarli. Il destinatario non è una variabile: CSIRT Italia è invariante (§18, C4) | ordinaria | da definire (contenuto dell'elenco; registro v1.5 ◐) | A5 |
| `incident.nis2.csirt_contact` | da definire | superadmin, con motivazione e audit | validità tecnica | ordinaria | da definire (il registro v1.5 non ha letto i contatti di emergenza del CSIRT Italia né la designazione del referente: non verificati). Eventuali credenziali del canale: §15 | A5 |
| `incident.initial_assessment_max_hours` | da definire | superadmin, con motivazione e audit | validità tecnica. Massimo operativo da fissare in A5 | vincolo di progetto (non di legge) | da definire (C3). Limita il tempo di valutazione di un evento sospetto, da cui dipende la «conoscenza» che fa decorrere i termini (N-NIS2-REG considerando 31; art. 23(4) direttiva) | A5 e produttori di segnali |

### 13.2 Termini e soglie dei vincoli normativi (NIS2)

Chi modifica il valore operativo: superadmin, con motivazione e audit. Nei termini «dalla conoscenza» il limite decorre dalla conoscenza, non dal preallarme. Per i prestatori di servizi fiduciari il termine di 24 h della notifica non è pertinente a Gravya.

| Nome | Limite di legge (non modificabile da UI) | Tipo del limite e verso ammesso | Valore operativo (default; minimo/massimo operativo) | Norma | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `incident.nis2.early_warning_hours` | 24 h dalla conoscenza | massimo: solo in diminuzione | 24; minimo operativo da definire (A5) | N-NIS2 art. 23(4)(a); N-NIS2-IT art. 25(5) | deciso (DX-10 (b)) | A5 e tutti i produttori di segnali |
| `incident.nis2.notification_hours` | 72 h dalla conoscenza (non dal preallarme) | massimo: solo in diminuzione | 72; minimo operativo da definire (A5) | N-NIS2 art. 23(4)(b); N-NIS2-IT art. 25(5) | deciso (DX-10 (b)) | A5 |
| `incident.nis2.final_report_days` | 1 mese dalla trasmissione della notifica | massimo: solo in diminuzione. Conversione: 28 giorni | 28; minimo operativo da definire (A5) | N-NIS2 art. 23(4)(d); N-NIS2-IT art. 25(5) | termine deciso (DX-10 (b): relazione finale entro un mese); valore in giorni derivato dalla regola 7 | A5 |
| `incident.nis2.progress_report_interval_days` | 1 mese (incidente ancora in corso) | massimo: solo in diminuzione. Conversione: 28 giorni | 28; minimo operativo da definire (A5) | N-NIS2-IT art. 25(5)(e) («mensile»; la direttiva dice «relazione sui progressi» senza cadenza) | valore del registro; la riga di DECISIONS §4 è «Da riportare», non una riga decisa | A5 |
| `incident.nis2.final_report_after_closure_days` | 1 mese dalla conclusione della gestione (incidente in corso alla scadenza della relazione finale) | massimo: solo in diminuzione. Conversione: 28 giorni | 28; minimo operativo da definire (A5) | N-NIS2 art. 23(4)(e); N-NIS2-IT art. 25(5)(e) | valore del registro (DECISIONS §4, «Da riportare») | A5 |
| `incident.cloud.outage_total_minutes` | 30 min: indisponibilità completa di un servizio cloud oltre questa durata | massimo: solo in diminuzione | 30; minimo operativo da definire (A5) | N-NIS2-REG art. 7(a) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.cloud.outage_partial_hours` | 1 h: disponibilità limitata oltre questa durata | massimo: solo in diminuzione | 1; minimo operativo da definire (A5) | N-NIS2-REG art. 7(b) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.cloud.users_affected_percent` | 5 % degli utenti del servizio nell'Unione (si applica il più basso fra questo e `incident.cloud.users_affected_count`) | massimo: solo in diminuzione | 5; minimo operativo da definire (A5) | N-NIS2-REG art. 7(b) e (d) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.cloud.users_affected_count` | 1000000 utenti | massimo: solo in diminuzione | 1000000; minimo operativo da definire (A5) | N-NIS2-REG art. 7(b) e (d) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.financial_loss_eur` | 500000 EUR di perdita finanziaria diretta (si applica il più basso fra questo e la percentuale di fatturato) | massimo: solo in diminuzione | 500000; minimo operativo da definire (A5) | N-NIS2-REG art. 3(1)(a) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.financial_loss_turnover_percent` | 5 % del fatturato totale annuo dell'esercizio precedente | massimo: solo in diminuzione | 5; minimo operativo da definire (A5). Il dato di fatturato è `incident.annual_turnover_eur` (sotto) | N-NIS2-REG art. 3(1)(a) | vincolo derivato da DX-10 (c) e dal registro | A5 |
| `incident.annual_turnover_eur` | nessun limite di legge: è il dato di base della riga precedente | dato di input, non soglia: il valore errato verso l'alto alza la soglia effettiva, quindi vale la regola del più basso noto | da definire. Valore versionato, con attore e documento di origine; **nel dubbio vale il più basso valore noto** (D3, DA-CV-14). Modifica: superadmin, con motivazione e audit | N-NIS2-REG art. 3(1)(a): fatturato totale annuo dell'esercizio precedente | da definire (valore); regola decisa (D3). Nome assegnato dal redattore (§17.1, punto 11) | A5 |
| `incident.recurring_min_count` | 2 incidenti con la stessa causa apparente | **fisso** (D6): il valore operativo non è modificabile. Il valore 1 renderebbe ricorrente ogni incidente | 2 (non modificabile) | N-NIS2-REG art. 4 | vincolo derivato da DX-10 (c) e dal registro; tipo «fisso» deciso (D6) | A5 |
| `incident.recurring_window_days` | 6 mesi | minimo: solo in aumento. Conversione: 184 giorni | 184; massimo operativo da definire (A5) | N-NIS2-REG art. 4 | vincolo derivato da DX-10 (c) e dal registro; conversione dalla regola 7 | A5 |
| `incident.recurring_review_interval_days` | cadenza **trimestrale fissata dalla norma** (valutazione degli incidenti ricorrenti): il testo non dice né «almeno» né «al massimo» | massimo di 89 giorni = **scelta prudente del progetto**, non limite di legge: solo in diminuzione. Conversione: 89 giorni | 89; minimo operativo da definire (A5) | N-NIS2-REG, allegato 3.4.2(b) (✔ nel registro v1.5; registro §9, punto 9(a)) | valore del registro; il massimo di 89 giorni è da confermare con un legale (DECISIONS §4, nota del 2026-11-04, «Da riportare») | A5 |

Senza soglia (nessuna variabile): art. 7(c) del Reg. 2024/2690 (compromissione di integrità, riservatezza o autenticità dei dati per azione sospettata malevola, senza soglia di utenti); art. 3(1)(b) (esfiltrazione di segreti commerciali) ed (e) (accesso non autorizzato sospettato malevolo con rischio di grave perturbazione).

### 13.3 Violazioni di dati personali (GDPR, sempre attive)

Le due righe valgono sempre, a flusso NIS2 acceso o spento (C5). Il termine di 72 h dell'art. 33(1) vale solo per i dati di cui Gravya è titolare (i propri utenti, DA-A1-08); per i dati delle agenzie Gravya è responsabile (DX-11) e vale l'art. 33(2). Il termine di risposta agli interessati (art. 12(3): un mese, prorogabile di due) è del titolare e non è un vincolo per Gravya; per l'assistenza del responsabile (art. 28(3)(e), «nella misura in cui ciò sia possibile») la legge non fissa un termine: la riga sotto è un obbligo del DPA (D7). Non esiste una variabile per la comunicazione agli interessati (art. 34, a carico del titolare). «Un mese» non va riscritto come «30 giorni» in un vincolo normativo (registro §9, punto 9(c)).

| Nome | Limite di legge (non modificabile da UI) | Tipo del limite e verso ammesso | Valore operativo (default; minimo/massimo operativo) | Norma | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `incident.gdpr.controller_notification_hours` | 72 h dalla conoscenza, ove possibile (oltre, motivazione del ritardo) | massimo: solo in diminuzione | 72; minimo operativo da definire (A5) | N-GDPR art. 33(1) | termine di legge; uso per i soli dati di cui Gravya è titolare (C5) | A5 |
| `incident.gdpr.processor_notice_hours` | nessun numero: l'art. 33(2) dice «senza ingiustificato ritardo» | obbligo contrattuale (DPA): il termine è quello concordato con l'agenzia | da definire dopo verifica legale; nessun numero proposto (DA-CV-08). Modificabile dal superadmin solo come attuazione di una modifica del DPA, con riferimento alla versione e audit (regola da confermare in A6/F6) | N-GDPR art. 33(2), qualitativo; art. 28(3) | da definire (C5; la natura contrattuale è decisa, il valore è aperto: DECISIONS §4 e §7, DA-CV-08) | A5, DPA con le agenzie |
| `dsar.assist_max_days` | nessun numero: l'art. 28(3)(e) non fissa un termine al responsabile; il mese dell'art. 12(3) è del titolare | obbligo contrattuale (DPA): termine entro cui Gravya assiste l'agenzia titolare su una richiesta di un interessato | da definire; deve lasciare al titolare il tempo per rispondere entro il suo termine (registro, N-GDPR, interpretazione). Modificabile dal superadmin solo come attuazione di una modifica del DPA, con riferimento alla versione e audit (regola da confermare in A6/F6) Massimo da fissare in F6 prima dell'attivazione (regola 11), con riferimento al mese dell'agenzia (28 giorni, regola 7). **Se non leggibile non blocca l'assistenza**: vale l'ultimo valore valido, con segnale ad A5 | N-GDPR art. 28(3)(e); art. 12(3) (del titolare) | da definire (D7). Non è un vincolo normativo. Nome e unità assegnati dal redattore (§17.1, punto 11) | A5, F6, DPA con le agenzie |

## 14. Destinazioni extra-UE (Agenzia → Impostazioni → Destinazioni dei dati)

L'opt-in è per **destinazione dichiarata** (DA-B2-07, C9), non un booleano unico. `<destination_id>` è l'identificativo della destinazione dichiarata dal tool nel catalogo (B2). Il superadmin non può attivare l'opt-in al posto dell'agenzia (DECISIONS §6). L'opt-in è registrato nella configurazione per tenant di A6, versionato e auditato (MFA, DX-20; `config_version`, DX-21). Vale anche per le chiavi dei provider LLM inserite dalle agenzie (§15): una chiave verso un provider extra-UE è usabile solo se la sua destinazione è dichiarata e l'opt-in è attivo; senza destinazione dichiarata vale il deny (§18). La decisione di adeguatezza del DPF copre solo i provider nell'elenco DPF, e il suo stato giudiziario è ◐ (registro, N-DPF); l'elenco DPF non è stato consultato dal registro (non verificato).

**Regole (D5, D7).** (1) L'opt-in è attivabile solo con strumento di trasferimento e stato validi; altrimenti vale il deny. (2) Lo stato lo aggiorna il superadmin, con la fonte e l'audit; mai l'agenzia. (3) Se lo strumento cade, parte un segnale ad A5, l'opt-in si disattiva (C9) e la riattivazione richiede un nuovo opt-in dell'agenzia. (4) Ogni destinazione, anche nell'UE, porta il campo «sub-responsabile autorizzato (riferimento al DPA, data)» (GDPR art. 28(2) e (4)); senza di esso il tool resta negato, anche per una destinazione UE, che non passa dall'opt-in.

| Nome | Default | Chi modifica | Intervallo ammesso | Tipo | Stato del valore | Documenti che la usano |
|---|---|---|---|---|---|---|
| `tenant.extra_eu_optin.<destination_id>.enabled` | falso (extra-UE negato senza opt-in) | admin agenzia. Il superadmin non può attivarlo | falso/vero; vero solo con strumento e stato validi (regola 13, D5) | ordinaria (istruzione documentata del titolare, GDPR art. 28(3)(a)) | deciso (DECISIONS §6; C9; D5) | A1, A3, B1 (egress-proxy), B2 (DA-B2-07) |
| `tenant.extra_eu_optin.<destination_id>.transfer_instrument` | da definire | **superadmin**, con fonte, riferimento al DPA e audit; mai l'agenzia (DA-CV-19) | elenco chiuso di strumenti del GDPR Cap. V (adeguatezza art. 45, garanzie art. 46); valori da definire con verifica legale | ordinaria | da definire (C9) | B2, A6, DPA con le agenzie |
| `tenant.extra_eu_optin.<destination_id>.transfer_instrument_status` | da definire | **superadmin**, con indicazione della fonte e audit; mai l'agenzia (D5) | stato dello strumento (per esempio valido o non valido): valori da definire. Se lo strumento cade (per esempio decisione di adeguatezza sospesa o revocata, art. 45(5)), parte un segnale ad A5 e l'opt-in si disattiva (C9) | ordinaria | chi modifica deciso (D5); valori da definire (C9) | A5, B2, A6 |
| `destination.<destination_id>.subprocessor_authorization` (riferimento al DPA e data) | da definire. Senza valore il tool resta negato (D7) | **superadmin**, con fonte, riferimento al DPA e audit; mai l'agenzia (DA-CV-19) | riferimento a una versione del DPA e data; autorizzazione scritta, specifica o generale, e informazione delle modifiche (art. 28(2): il testo non fissa un preavviso) | obbligo contrattuale (DPA) | campo deciso (D7); valori da definire. Nome assegnato dal redattore (§17.1, punto 11) | B2, A6, DPA con le agenzie |

## 15. Credenziali (Piattaforma → Credenziali; Agenzia → Credenziali)

Nessun valore è nel catalogo (DX-22(b)). Le credenziali stanno nella pagina dedicata di A6, separata tra credenziali di piattaforma (superadmin) e di agenzia (admin agenzia). I valori sono in un archivio cifrato self-hosted nell'UE; da UI solo inserimento o sostituzione, mai rilettura in chiaro (mascherate, con data dell'ultima rotazione); ogni accesso e modifica è in audit (classe `retention.credential_access_months`). La frequenza di rotazione è `security.credential_rotation_interval_days` (§19).

Le credenziali non si rileggono mai in chiaro (invariante, §18). La sostituzione delle chiavi HMAC e di firma senza interruzione di servizio non è definita: DA-CV-23.

**Segreti della CI (C11, D6).** Sono ammessi fuori dalla pagina credenziali solo se non danno accesso a dati reali (test con dati sintetici, DA-E3-08). Le chiavi di produzione non stanno mai in CI (§18). Condizioni aggiunte da D6: (1) l'account o il progetto del provider usato in CI è **separato da quello di produzione**, dedicato ai test; (2) esiste un inventario dei segreti della CI con la data di inserimento e la rotazione, con frequenza `security.credential_rotation_interval_days` (§19); (3) il giudice LLM di E3 elabora i dati nell'UE (DA-E3-09).

| Voce | Pagina | Chi inserisce o sostituisce | Documenti |
|---|---|---|---|
| Chiave di firma del `run_token` | credenziali di piattaforma | superadmin | B1, B2 |
| Chiave HMAC di resume e firma del token monouso | credenziali di piattaforma | superadmin | C3, A3, B2 |
| Chiave HMAC dell'egress-proxy | credenziali di piattaforma | superadmin | B1 |
| Chiavi dei provider LLM per tenant | credenziali di agenzia | admin agenzia (destinazione extra-UE: §14) | B1 |
| Credenziali dei sistemi esterni dietro i tool | credenziali di agenzia; di piattaforma se il tool è di piattaforma | admin agenzia; superadmin solo per i tool di piattaforma. Il superadmin **non inserisce mai** credenziali per conto di un'agenzia (D3, DA-CV-16 (a)) | B2 |
| Eventuali credenziali del canale di notifica verso CSIRT Italia | credenziali di piattaforma | superadmin | A5 (esistenza non verificata) |
| Segreti della CI (inclusa la chiave del provider del giudice LLM di E3, se il giudice gira in CI) | secret store della CI, solo alle condizioni di C11 e D6 (account o progetto di test separato dalla produzione, inventario e rotazione, giudice nell'UE) | non da UI di piattaforma | E3 (DA-E3-09, DA-E3-11 aperta) |

## 16. Valori fissi trovati nei documenti

Elenco documento §sezione → variabile, per chi aggiorna i documenti. Sostituire il valore con il nome della variabile. I valori del sistema precedente citati come riferimento non sono default di v2.

| Documento §sezione | Valore fisso trovato | Variabile o trattamento | Correzione richiesta |
|---|---|---|---|
| A1 §4.2, §4.5, CA5, CA11 | profondità 3 | `a1.delegation.max_depth` | citare solo il nome; CA11 usa il nome e un valore di prova |
| A1 §4.5, CA7 | 4 KB | `a1.artifact.max_properties_bytes` | citare il nome |
| A1 §4.5 | `a1.sweeper.interval` | `a1.sweeper.interval_minutes` | rinominare |
| A1 §4.5, §7, CA13 | 90 giorni, 12 mesi | `retention.runtime_events_days`, `retention.audit_decisions_months`, `retention.cross_tenant_access_log_months` | il test CA13 confronta con il catalogo; le durate sono di sola lettura (RR) |
| A1 §7 | 30 giorni (fine contratto) | `retention.tenant_offboarding_days` | citare il nome |
| A1 §7 | p99 < 100 ms (≤ 1.000 mandati), p99 < 50 ms | `a1.read_batch_p99_ms`, `a1.write_p99_ms` | 1.000 mandati è condizione di test (DA-CV-04 (b)) |
| A1 §7 | 10.000 `Agent`, 100.000 `Artifact` per tenant | dimensione del dataset di test | parametro del test (DA-CV-04 (b)) |
| A1, B1, B2, C1, C3, E1, E2, E3, A3 §7 | 12 mesi del log di accesso | `retention.cross_tenant_access_log_months` | citare il nome |
| A3 §4 | `a3.bundle.max_age` | `a3.bundle.max_age_s` | rinominare; aggiungere il minimo valido |
| A3 §4 | `retention.audit_decisions`, `retention.runtime_events` | `retention.audit_decisions_months`, `retention.runtime_events_days` | rinominare |
| A3 §4 («ripiego sul valore più restrittivo») | regola implicita | DX-17: azioni bloccate, segnale ad A5 | allineare il testo a DX-17 |
| A3 §7, CA5 | p99 ≤ 5 ms; soglia complessiva «aperta» | `a3.latency.eval_p99_ms`, `a3.latency.persist_p99_ms`, `a3.latency.total_p99_ms` | la soglia complessiva è decisa (DECISIONS §6) |
| A3 CA1, CA5 | ≥ 30 casi; 10.000 decisioni | campioni di test | parametri del test (DA-CV-04 (b)) |
| B1 §4 | `limits` senza valori; «10 min e $2 per run, 8 giri» | `b1.job.*_default`, `b1.job.*_max` | i valori citati sono riferimento, non default |
| B1 §7, CA8 | p95 sotto 3 s; 200 job | `b1.job.start_overhead_p95_ms` | 200 job è campione di test |
| B1 CA4 | wall_s + 5 s | `b1.job.kill_grace_s` | citare il nome |
| B1 §7 | concorrenza per host, quota per tenant | `b1.host.max_concurrent_jobs`, `b1.tenant.max_concurrent_jobs` | la quota è in job concorrenti (DA-CV-06 (a)) |
| B1 §7 | 90 giorni, 30 giorni, 12 mesi, «legal hold» | `retention.runtime_events_days`, `retention.run_state_days`, `retention.incident_evidence_months`, `retention.cross_tenant_access_log_months` | usare «evidenze di incidente» al posto di «legal hold» (registro §9, punto 4) |
| B1 §6, CA6, §6 «fail-closed»; E3 AC7 | guardia `API_ENV=production` | invariante di deploy (§18, D2, DA-CV-11 (b)): non è una variabile di catalogo | citare la guardia come invariante di deploy e non come variabile; non è modificabile da UI |
| B1 App. A | 300 s, 512M, 2G e 1G, pids 512, uid 10001 | riferimenti del sistema precedente | non default; il profilo di hardening v2 è da definire (DA-B1-02) |
| B1 CA3 | 169.254.169.254, 169.254.0.0/16 | invariante di rete (§18) | non variabile |
| B2 §5, CA4 | «N = 10», limiti di default | `b2.rate_limit.agent_calls_per_minute`, `.tool_calls_per_minute`, `.tenant_calls_per_minute` | N=10 è il valore di prova; sostituisce `b2.rate_limit.default_calls_per_minute` |
| B2 §7, CA8 | p95 < 50 ms; 1.000 chiamate | `b2.overhead_p95_ms` | 1.000 è campione di test |
| B2 §7 | 12 mesi, 30 giorni, 90 giorni | `retention.audit_decisions_months`, `retention.sensitive_payload_days`, `retention.traces_days` | citare i nomi |
| B2 App. A | 16.000 caratteri, 8 chiamate per risposta, `RATE_LIMIT_RPM` | riferimenti del sistema precedente | non default |
| B2 §6 | coda di recupero «fino a riuscirci» | `b2.recovery_queue.retry_interval_s` | aggiungere l'intervallo |
| B2 §6 | `idempotency_key`: «restituisce il primo esito» senza finestra | `b2.idempotency.window_hours` | aggiungere la finestra, con il massimo `b2.idempotency.window_hours_max` (D5) |
| B2 §4, C3 §6 | token monouso senza durata | `b1.run_token.ttl_s`, `hitl.approval_token.ttl_s` | definire, con le regole 8a e 8b (il limite del token di approvazione è il TTL effettivo della richiesta, D5) |
| B1 §4 (`tool_grant_ref`), B2 §4 (`run_token`) | due nomi per un token «emesso da B1» / «di B2 limitato al job» | `b1.run_token.ttl_s` (D3, DA-CV-13 (a)) | un solo token, emesso da B1 e verificato da B2: B1 e B2 usano lo stesso nome nei documenti e B1 corregge «Token di B2» |
| B2 App. B, C1 (riferimento alle retention), C3 §7, E1 §4.1, E2 §7 | «legal hold» | `retention.incident_evidence_months` | usare «evidenze di incidente» (registro §9, punto 4) |
| C1 §4.1, §6, CA10 | 500 step e 5 min | `c1.max_steps`, `c1.max_duration_ms` | citare i nomi |
| C1 §4.3, §7 | 30, 90 giorni, 12 mesi | `retention.run_state_days`, `retention.runtime_events_days`, `retention.traces_days` | citare i nomi |
| C1 §7 | p95 < 50 ms «non variabile» | `c1.node_overhead_p95_ms` | DA-CV-04 (b): soglia con metrica a runtime, quindi variabile |
| C3 §3, §5 | `KLOUD_APPROVAL_DEFAULT = true` | `hitl.approval_required_default` | escluse le classi `ALWAYS_HITL` e `MONEY_WRITE` (§18); il default di piattaforma è in sola lettura, vero (D3, DA-CV-15 (a)) |
| C3 §4.3, §7, AC-11 | 30 giorni, 12 mesi, 90 giorni | `retention.sensitive_payload_days`, `retention.audit_decisions_months`, `retention.traces_days`, `retention.run_state_days` | citare i nomi |
| C3 §6, App. C | 24 h, «DA-C3-04 resta aperta» | `hitl.request_ttl_hours` con `_min` e `_max` | DA-C3-04 è decisa; 24 h di gravya-app è solo riferimento |
| C3 §6, §7, AC-12 | sweeper che «non chiude» e retention che «non cancella» con valore non leggibile | DX-17, DA-C3-08 (a) | riscrivere: ultimo valore valido versionato e segnale ad A5 |
| C3 §7, §10 | 2 s al p95; 100 % di fermate | `hitl.resume_latency_p95_ms`; invariante «zero fallimenti bloccanti» del gate (§18) | citare il nome e l'invariante. «100 % di fermate» (C3) e «zero fallimenti bloccanti» (E3) sono metriche diverse: la corrispondenza non è detta nei documenti |
| C3 §5 | HMAC e firma del resume | credenziali (§15) | rimandare alla pagina credenziali |
| E1 §4.1, §7, CA8 | 90 giorni, 12 mesi; «oltre 90 giorni» | `retention.traces_days`, `retention.cross_tenant_access_log_months`, `retention.eval_reports_months` | il test legge il valore dal registro |
| E1 §4.1, §5 | partizioni «per mese» | `e1.partition_interval_months` | citare il nome; regola 8c |
| E1 §5 | `x-gravya-trace-id`, `x-gravya-parent-segment-id`, 32 cifre esadecimali | nomi e formato: invarianti (§18) | non variabili |
| E1 §5 | «soglia di overhead p95 (default 5 ms)», buffer | `e1.overhead_p95_ms`, `e1.write_buffer_size` | citare i nomi |
| E1 §5 | soglia di perdita dei segmenti | nessuna variabile locale | la soglia vive in A5 (DA-CV-07 (b)); E1 invia ogni perdita ad A5 |
| E1 §5, CA8, App. B | «ultimo valore valido; non cancella nulla su valore non valido» | DX-17 | il job di retention usa l'ultimo valore valido versionato |
| E2 §7, CA2, CA13 | `e2.cache.max_ttl_s` 60, `e2.rollback.propagation_max_s` 60 | stessi nomi | ripetere solo i nomi |
| E2 §7, CA13 | `e2.template.pii_check_mode` | invariante: sempre `block` (§18) | togliere la variabile |
| E2 §7 | p99 < 5 ms «non variabile» | `e2.resolve_render_p99_ms` | DA-CV-04 (b): soglia con metrica a runtime, quindi variabile |
| E2 §4.3 | lunghezza dell'hash «da fissare con E1» | formato: invariante (§18) | fissare con E1 |
| E3 §5, AC4 | `eval.gate.pass_rate_min`, `eval.run.cost_cap`, `eval.run.timeout`, `eval.ingestion.timeout`; 90 % | `eval.gate.pass_rate_min_percent`, `eval.run.cost_cap_usd`, `eval.run.timeout_s`, `eval.ingestion.timeout_s` | rinominare; DA-E3-07 aperta |
| E3 AC4 | `eval.gate.max_blocking_failures_count` | invariante: zero fallimenti bloccanti (§18) | togliere la variabile |
| E3 AC1 | 10–30 casi (master 0.3.1) | dimensione del dataset iniziale | parametro del test (DA-CV-04 (b)) |
| E3 §6 | R1 vale circa 20 giorni dal seed | dato della fixture | non è una variabile; scompare con il re-seed (DA-E3-04) |
| E3 §7 | $2 e 10 minuti per run agente (kloudify) | riferimento | non default di `eval.run.cost_cap_usd` |
| E3 §7 | 12 mesi; scadenza dell'artefatto GitHub non superiore al default | `retention.eval_reports_months` | la scadenza GitHub è ≤ questo valore; limiti GitHub non verificati |
| E3 §4.2 | exit code 0, 1, 2 | formato: invariante (§18) | non variabile |
| A1, B1, B2 App. C | opt-in extra-UE «aperto» | `tenant.extra_eu_optin.<destination_id>.enabled` | decisa (DECISIONS §6; per destinazione, C9) |
| A1, A3, B1, B2, C1, C3, E1, E2, E3 §3 | DX-14 «da riportare» | A6 | DX-14 è decisa (2026-11-03) |

## 17. Non verificato / da decidere

### 17.1 Non verificato

1. **Nomi e pagine.** I nomi dipendono da DX-07 (aperta in DECISIONS §1); le pagine da A6 (non documentato).
2. **Valori del sistema precedente** (300 s, 512M, 2G, pids 512, 16.000 caratteri, 8 chiamate, `MAX_CASCADE_DEPTH = 3`, 24 h, 10 minuti e $2 per run): ripresi dai documenti dell'ondata 1, non riletti nel codice. I valori di kloudify arrivano da una ricognizione (B1 App. A).
3. **Master plan.** I valori «master 0.3.1» (10–30 casi) sono citati da E3, non riletti nel master.
4. **Incidenti «di base».** I casi degli Allegati 3 e 4 della Det. ACN 379907/2025 non sono nel registro (non letti): non catalogati. Restano aperti i termini della coorte di Gravya (DECISIONS §4).
5. **Ambito NIS2.** La qualificazione di Gravya come fornitore cloud e il criterio dimensionale non sono accertati (registro, N-NIS2). L'interruttore `incident.nis2_flow_active` ha default falso; si accende quando Gravya diventa soggetto NIS2 o al contratto con un'agenzia soggetta NIS2 che lo richiede (D1); l'ambito si riesamina con `incident.scope_review_interval_days`.
6. **Durata dei log.** Nessuna norma letta fissa una durata per i log di un responsabile: il Reg. 2024/2690 (allegato 3.2.5) non indica una durata; le sei mensilità del Garante (N-GAR-ADS) sono un riferimento, non un vincolo per il responsabile, e la vigenza dopo il GDPR non è verificata. Il valore di 12 mesi di `retention.cross_tenant_access_log_months` resta una scelta di DECISIONS §5.
7. **Parametri «pianificati» del Reg. 2024/2690** (riesame dei registri 3.2.4 e 3.2.7, riesame dei diritti 11.2.3 e 11.3.3, blocco dopo tentativi falliti e sessioni inattive 11.6, orologi 3.2.6; continuità e backup 4.1-4.2, patch 6.6, vulnerabilità 6.10, fornitori 5.1.6-5.1.7, crittografia 9.2(c) e 9.3): il regolamento, nelle sezioni lette dal registro v1.5, non dà valori; sono catalogati in §19 come «da definire» e non sono vincoli normativi (registro §9, punto 9(b)). Fanno eccezione i due riesami almeno annuali (1.1.2 e 2.1.4), catalogati in §19.2. Per la rotazione delle credenziali il punto 9.2(c) chiede che la politica del soggetto definisca le tempistiche di modifica delle chiavi, senza una periodicità fissa. Restano non lette le sezioni 7, 8, 10, 12, 13 e parti di 1-3 dell'allegato (○): potrebbero contenere altri intervalli (non verificato).
8. **Data Act.** Il valore di `retention.tenant_offboarding_days` e il default di `retention.tenant_offboarding_choice` (esportazione per tutto il periodo di uscita, poi cancellazione) vanno riverificati contro gli artt. 25 e 29 (registro ◐, art. 25(2) non letto sul testo; DECISIONS §4).
9. **Fixture dell'ondata 1.** I valori di default versionati nel repository (A3 F5b, E3 §5) e la tabella minima di C1 non soddisfano DX-22 finché A6 non esiste: sono ripieghi dichiarati dai documenti.
10. **Documenti non aggiornati.** I nove documenti (v1.4) descrivono ancora come aperte o proposte decisioni ora prese: DX-14, DX-17-DX-22, DA-C3-04, DA-C3-08, DA-C3-09, DECISIONS §6 e le decisioni C1-C14 e D1-D8.
11. **Unità e semantica incerte:** `e1.write_buffer_size`, «4 KB» (A1), esistenza distinta di `_default` e `_max` per i limiti B1, finestra del rate limit di B2 (assunta al minuto dal nome). **Nomi e unità assegnati dal redattore** (D1, D3, D5, D7: le decisioni non li danno): `incident.scope_review_interval_days`, `incident.annual_turnover_eur`, `dsar.assist_max_days`, `destination.<destination_id>.subprocessor_authorization`, `b2.idempotency.window_hours_max`, `security.policy_review_interval_days`, `security.risk_assessment_review_interval_days`, `continuity.rto_hours`, `continuity.rpo_minutes`, `continuity.restore_test_interval_days`, `security.patch_deadline_days`, `security.vulnerability_scan_interval_days`, `security.supplier_review_interval_days`, `security.crypto_policy_review_interval_days`. I nomi dei documenti B1 e B2 per il token unico (`run_token` o `tool_grant_ref`) sono da allineare.
12. **Altri parametri senza valore:** A1 DA-A1-06 (soglia dell'istanza dedicata «da validare»). Le soglie dei segnali verso A5 (picchi di `deny`, `tool.denied` ripetuti, mutazioni anomale, perdita di segmenti) vivono in A5 e non sono fissate da nessun documento (DA-CV-07 (b)).
13. **Etichetta usata in B1:** «limiti A6 di kloudify» indica un'etichetta di kloudify e non il sottoprodotto A6.
14. **`run_token` e `tool_grant_ref`.** Risolto da D3 (DA-CV-13 (a)): un solo token, emesso da B1 e verificato da B2. Resta da allineare il nome nei documenti B1 e B2 (punto 11).
15. **Registro delle norme (v1.5).** Sono ✔ nel registro: GDPR 12(3)-(6), 28(2), 28(3)(e), 28(4); Reg. 2024/2690 allegato 3.4.2(b) e sezioni 4, 5, 6, 9; canale di notifica verso il CSIRT Italia, solo estratti (◐). Non sono verificati nel registro: il computo del «mese» (reg. 1182/71, ○) per le conversioni; GDPR artt. 15-16, 18-22 (○); sezioni 7, 8, 10, 12, 13 dell'allegato; Allegati 3 e 4 della Det. ACN 379907/2025; la raccomandazione 2003/361/CE (soglie dimensionali); i contatti di emergenza del CSIRT Italia e la designazione del referente; elenco DPF e stato di singoli provider; N-PRIV-IT art. 130 (◐).
16. **Conversione mesi-giorni.** I valori 28, 89 e 184 giorni sono un calcolo del redattore sul calendario; la regola 7 estende a 3 e 6 mesi l'indicazione dell'utente (che per un massimo di un mese dà 28 giorni). Da confermare con un legale.
17. **Allineamento con DECISIONS.md.** DECISIONS contiene C1-C14 (§4-§7); le decisioni D1-D8 sono qui applicate come comunicate dall'utente e vanno registrate. Differenze note da sistemare in DECISIONS: (a) C8 (§6) elenca la guardia `API_ENV` tra le variabili da catalogare, mentre D2 (b) la porta tra le invarianti di deploy; (b) DX-09 e §5 (C6) legano la scelta di fine contratto all'override per agenzia, mentre D2 (a) la rende indipendente; (c) §4 numera «DA-CV-05» il default HITL, che qui è DA-CV-15; (d) le righe §4 senza ID (spegnimento del flusso, override per classe, valori non validi e backup, credenziali, fatturato, `run_token`) corrispondono a DA-CV-09, 10, 17, 22 e 23, 14, 13; (e) il nome della variabile per agenzia segue §5 (`retention.<classe>.tenant_value`); (f) DA-E3-07 risulta «Aperta», mentre C7 fissa a zero i fallimenti bloccanti; (g) la marcatura leggibile da macchina del testo (art. 50(2)) è «Da riportare» in §4, mentre D7 la rende un'invariante di principio con il dettaglio in C1 e D1-D4. DA-CV-05 elenca come invarianti anche hash, whitelist E1, header, exit code, regole di rete e `synthetic: true`: dall'opzione (a) di DA-CV-05, non da una riga di C7.
18. **Struttura dei segnali.** La tabella di audit minima che riceve i segnali in ondata 1 non è ancora definita (DECISIONS §6).
19. **Perimetro per agenzia.** L'elenco delle classi di retention che sono dati dell'agenzia (§2, `retention.<classe>.tenant_value`) è dedotto dalla natura dei dati di DECISIONS §5; `consent_optout_months` è escluso perché una durata più corta per agenzia potrebbe far perdere un opt-out (dedotto). F6 conferma. Il significato di `<classe>` (nome della durata senza il prefisso) è un'assunzione del redattore.
20. **Valore delle variabili `incident.*` senza limite di legge se non leggibili.** D3 esclude le notifiche dal blocco, ma non dice quale canale, contatto o tempo di valutazione usare se la variabile non è leggibile (probabile ultimo valore valido versionato: dedotto). Da definire in A5.
21. **Estensione di D4.** D4 cita «i timeout e le età massime di A3 ed E2»: la regola 11 elenca `a3.bundle.max_age_s`, `a3.eval.timeout_ms`, `a3.record.persist_timeout_ms` ed `e2.cache.max_ttl_s`. Non è chiaro se rientri anche `e2.rollback.propagation_max_s`: qui non è inclusa. Anche la classificazione iniziale di un tool come `ALWAYS_HITL` o `MONEY_WRITE` (chi la assegna) non è descritta.
22. **Base dei valori «proposti dal progetto».** I due riesami annuali (§19.2) valgono solo se Gravya è in ambito NIS2 come fornitore cloud (registro, N-NIS2-REG); l'ambito non è accertato (punto 5). Il valore 365 è la conversione per difetto di «almeno annualmente» secondo la regola 7, estesa a un anno: calcolo del redattore, da confermare con un legale.

### 17.2 Decisioni

**Decise (non più aperte).**

| ID | Titolo | Scelta | Fonte |
|---|---|---|---|
| DA-CV-01 | Intervalli minimo-massimo delle durate di retention | (a): durate di sola lettura finché l'intervallo del contratto/DPA non è definito; poi variabili per agenzia e scelta a fine contratto (§2) | C6 |
| DA-CV-02 | Intervalli delle variabili non di retention | (a): sola validità tecnica, più regole relazionali (regola 8) | C12 |
| DA-CV-03 | Intervalli di sweeper e code, durata dei token | (a): da fissare con misura, con il ritardo massimo tra scadenza e chiusura come criterio. Le regole relazionali dei token sono nella regola 8 | C12 |
| DA-CV-04 | Soglie «non variabili» e campioni di test | (b): in catalogo le sole soglie con metrica a runtime (§12); i campioni di test restano parametri dei test | C12 |
| DA-CV-05 | Invarianti di sicurezza e formati | (a): elenco di invarianti non variabili (§18) | C7 |
| DA-CV-06 | Granularità del rate limit, quota B1, opt-in extra-UE | (a): tre limiti indipendenti, vince il più restrittivo; quota B1 in job concorrenti; opt-in per destinazione (§7, §6, §14) | C12, C9 |
| DA-CV-07 | Soglie dei segnali verso A5 | (b): ogni evento rilevante va ad A5 senza soglia locale; le soglie vivono in A5 | C12 |
| DA-CV-08 | Natura del termine di Gravya verso l'agenzia titolare per segnalare una violazione | Obbligo contrattuale del DPA, non l'art. 33(1); le 72 h valgono solo per i dati di cui Gravya è titolare. **Il valore è aperto**: nessun numero proposto, da definire dopo verifica legale (riga «Da riportare» di DECISIONS §4; `incident.gdpr.processor_notice_hours`) | C5; DECISIONS §7 |
| DA-CV-09 | Condizione di spegnimento di `incident.nis2_flow_active` | Spegnimento solo con valutazione scritta di un legale o del DPO e approvazione di entrambe le persone con accesso superadmin; non leggibile = flusso attivo, con segnale; nuova variabile `incident.scope_review_interval_days` (valore da definire, A5); accensione anche al contratto con un'agenzia soggetta NIS2. Opzione (c) tolta (solo motivazione e audit contraddice C2) | D1 |
| DA-CV-10 | Condizione di attivazione di `retention.class_override_enabled` | (a): vero solo con l'intervallo di classe definito, come per l'agenzia | D3 |
| DA-CV-11 | Guardia di ambiente (`API_ENV=production`) di B1 CA6 e E3 AC7 | (a): invariante di deploy, fuori dal catalogo come variabile (§18); §16 e §19 corretti | D2 (b) |
| DA-CV-12 | Scelta restituzione/cancellazione a fine contratto e override per agenzia | Opzione (b), D2 (a): `retention.tenant_offboarding_choice` sempre disponibile all'agenzia, indipendente dall'override; se non sceglie, esportazione per tutto il periodo di uscita, poi cancellazione (da riverificare sul Data Act) | D2 |
| DA-CV-13 | `run_token` e `tool_grant_ref` | (a): un solo token, emesso da B1 e verificato da B2 | D3 |
| DA-CV-14 | Fonte del dato di fatturato | Valore versionato con attore e documento di origine (`incident.annual_turnover_eur`); nel dubbio vale il più basso noto | D3 |
| DA-CV-15 | Default di piattaforma di `hitl.approval_required_default` | (a): sola lettura, vero; la classificazione `ALWAYS_HITL` e `MONEY_WRITE` non è declassabile da UI (invariante, §18) | D3 |
| DA-CV-16 | Credenziali di sistemi esterni inserite dal superadmin per un'agenzia | (a): mai, solo l'admin agenzia | D3 |
| DA-CV-17 | Nessun valore valido di una variabile esiste | I valori «deciso» valgono come primo valore valido; segnali, audit e notifiche esclusi dal blocco; le classi di retention «da definire» non si scrivono in produzione finché A6 o F6 non fissano un valore (regola 4). Resta aperta la durata provvisoria di segnali e audit: DA-CV-20 | D3 |
| DA-CV-18 | Contenuti verso terzi e classe `ALWAYS_HITL` | (b): nell'ondata 1 non sono `ALWAYS_HITL`, decide l'admin agenzia con audit; da riesaminare con D1-D4 | utente 2026-11-04 («Ok») |
| DA-CV-19 | Chi imposta strumento di trasferimento e autorizzazione del sub-responsabile | (a): il superadmin, con fonte, riferimento al DPA e audit; l'agenzia attiva l'opt-in solo su destinazioni con entrambi validi | utente 2026-11-04 («Ok») |
| DA-CV-20 | Durata provvisoria di segnali e audit nelle classi senza valore | (b): tetto provvisorio fissato dall'utente prima dell'avvio in produzione (valore aperto) | utente 2026-11-04 («Ok») |
| DA-CV-21 | Base e perimetro della sospensione per evidenze di incidente | (a): solo dati di Gravya; per le agenzie istruzione nel DPA e parere legale prima di F6 | utente 2026-11-04 («Ok») |
| DA-CV-22 | Cancellazioni e backup | (a): backup entro `retention.data_backup_days`, non oltre il massimo delle classi contenute; al ripristino le cancellazioni si riapplicano. Il registro delle cancellazioni da riapplicare contiene solo hash o pseudonimi tecnici e dura non oltre `retention.data_backup_days` (classe assegnata da F6) | utente 2026-11-04 («Ok»); precisazione del coordinator dalla revisione di conformità sulla v1.2 |
| DA-CV-23 | Sostituzione delle chiavi HMAC e di firma | (a): due chiavi valide in parallelo, con data di attivazione e disattivazione | utente 2026-11-04 («Ok») |

**Aperte.** Nessuna decisione DA-CV aperta (v1.3). I valori ancora da fissare e i punti residui delle revisioni stanno in DECISIONS §4 («Da riportare») e nei documenti responsabili (A5, A6, F6).

## 18. Invarianti (non variabili)

Non sono variabili e non hanno interruttori. Qualunque `*_enabled` per attenuarle è fuori catalogo. Principio: **configurabile non vuol dire disattivabile** (C7).

| Invariante | Riferimento | Documenti |
|---|---|---|
| MFA obbligatoria per superadmin e admin di agenzia (più alta del «se opportuno» di Reg. 2024/2690 11.7.1) | DX-20 | A6 e tutti |
| Fail-closed: azioni bloccate con variabile non leggibile o non valida; audit e record di decisione non salvati bloccano l'azione. Unica eccezione di segno opposto: variabili `incident.*` (limite di legge, §1 regola 6) | DX-17, DA-B2-04, DA-A3-07 | A3, B2, tutti |
| Deny per tool senza destinazione, giurisdizione e categorie di dati dichiarate | DA-B2-07 | B2, A3 |
| Extra-UE negato senza opt-in dell'agenzia; il superadmin non lo attiva | DECISIONS §6; C9 | B2, A1, A3, B1 |
| Nessun contenuto di prompt e risposte nelle tracce in produzione (un eventuale opt-in richiederebbe DPIA e parere legale: nessuna variabile lo consente); argomenti dei tool solo come hash | DA-E1-02; DA-C3-06 | E1, C3, B2 |
| Solo dati sintetici nei test e nei casi di eval | DA-E3-08 | E3, A1, A3, B1, B2, C1, C3 |
| Etichetta «generato da AI» sui contenuti verso terzi, attiva di default e non disattivabile dal tenant | DECISIONS §6 (riga etichetta, art. 50) | C1, C3, E2, D1-D4 |
| Marcatura leggibile da macchina anche del testo generato (AI Act art. 50(2)): invariante di principio. Modalità e livelli di marcatura sono nel dettaglio di C1 e D1-D4; l'eccezione per la funzione assistiva di editing non è valutata qui | D7; registro N-AIACT (art. 50(2) ✔, in vigore dal 2.8.2026 per i sistemi nuovi); DECISIONS §4 | C1, C3, E2, E3, D1-D4 |
| Informativa a chi interagisce direttamente con un'IA (per esempio chat e risposte automatiche) al più tardi alla prima interazione | D6; AI Act art. 50(1) (registro N-AIACT ✔) | C1, C3, D1-D4 |
| Token monouso | C7 | B1, B2, C3, A3 |
| Destinatario delle notifiche NIS2: CSIRT Italia (configurabili solo canale e contatto, §13.1) | C4; N-NIS2-IT art. 25 ✔ | A5 |
| `e2.template.pii_check_mode` sempre `block` | C7; GDPR art. 25 e 5(1)(c) | E2 |
| Gate E3: zero fallimenti bloccanti (`eval.gate.pass_rate_min_percent` solo per i casi non bloccanti) | C7; DA-E3-07 | E3, C3, E2 |
| Approvazione umana sempre obbligatoria per le classi `ALWAYS_HITL` e `MONEY_WRITE` (vocabolario chiuso). Per i contenuti verso terzi l'approvazione la decide l'admin agenzia, con audit (se tali contenuti siano `ALWAYS_HITL` è aperto: DA-CV-18) | C7 | C3, A3, B2 |
| La classificazione `ALWAYS_HITL` e `MONEY_WRITE` non è declassabile da UI; il default di piattaforma di `hitl.approval_required_default` è vero e in sola lettura | D3 (DA-CV-15 (a)) | C3, A3, B2 |
| Chiavi di produzione mai in CI; segreti della CI solo senza accesso a dati reali, con account o progetto di test separato dalla produzione, inventario e rotazione; giudice LLM di E3 con elaborazione nell'UE | C11; D6; DA-E3-09 | E3 |
| I segnali di incidente sono sempre prodotti e conservati, anche a `incident.nis2_flow_active` falso | C2 | A5 e tutti i produttori di segnali |
| Le variabili GDPR sulle violazioni (`incident.gdpr.*`, §13.3) sono sempre attive, indipendenti da `incident.nis2_flow_active` | C5 | A5 |
| Le credenziali non si rileggono mai in chiaro: da UI solo inserimento o sostituzione, con valore mascherato | DX-22 (b) | A6, B1, B2 |
| Il superadmin vede di default solo dati aggregati senza identificativi; una singola traccia solo su richiesta dell'agenzia o per un incidente, con log degli accessi | DX-19, DX-18 | A6, E1, A1 |
| Guardia di ambiente di produzione (`API_ENV=production`, B1 CA6, E3 AC7): invariante di deploy, non una variabile di catalogo né modificabile da UI. Eccezione a DX-22 «niente hardcoded mai» scelta dall'utente (D2 (b)) | D2 (b), DA-CV-11 | B1, E3, A6 |
| SHA-256 e lunghezza dell'hash, whitelist degli attributi E1, nomi degli header di correlazione e formato `traceparent`, exit code di E3, regole di rete 169.254.0.0/16, `synthetic: true` | DA-CV-05 (a) | E1, E2, E3, B1 |

## 19. Sicurezza operativa e accessi (Piattaforma → Sicurezza e accessi)

Parametri richiesti dalle misure del Reg. (UE) 2024/2690 che DX-10 (a) rende requisiti di progetto («se opportuno» o «nella misura del possibile»: l'eventuale deroga si documenta, art. 2(2) del regolamento). Il regolamento, nelle sezioni lette dal registro v1.5, non dà valori per queste righe: tutti **da definire**. Il documento indicato è quello che li fissa (ondata 2). Tipo: ordinaria, non vincolo normativo (registro §9, punto 9(b)). **Nessuna riga di §19 è attivabile in produzione senza un intervallo minimo-massimo deciso (regola 11, D4); i valori li fissano A5 e A6.** Dove la colonna «Intervallo» dice «richiesto», vale la regola 11.

### 19.1 Parametri da definire

| Nome | Default | Chi modifica | Intervallo ammesso | Stato del valore | Documento responsabile; punto della norma |
|---|---|---|---|---|---|
| `security.log_review_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire | A5; Reg. 2024/2690 all. 3.2.4 e 3.2.7 (riesame di registri ed elenco delle risorse registrate) |
| `security.access_review_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 11.2.3 e 11.3.3 (riesame dei diritti e degli account privilegiati) |
| `security.clock_skew_max_ms` | da definire | superadmin | richiesto (regola 11) | da definire | A5; all. 3.2.6 (origini dell'ora sincronizzate) |
| `security.login_lockout_attempts_count` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 11.6 (blocco dopo tentativi falliti) |
| `security.login_lockout_duration_minutes` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 11.6 |
| `security.session_idle_timeout_minutes` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 11.6 (terminazione delle sessioni inattive) |
| `security.session_max_duration_hours` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 11.6 (la durata massima non è nominata nel testo letto: dedotto) |
| `security.credential_rotation_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire | A6; all. 9.2(c) (la politica definisce le tempistiche di modifica delle chiavi; nessuna periodicità fissa). Vale anche per l'inventario dei segreti della CI (§15) |
| `access.superadmin_trace_access_ttl_hours` | da definire | superadmin | richiesto (regola 11) | da definire | A6; DX-19 (accesso a una singola traccia su richiesta dell'agenzia o per incidente); all. 11.2.2 («limitato in portata e durata» per i terzi) |
| `access.aggregate_min_group_size_count` | da definire | superadmin | minimo **2** (deciso, D4); massimo richiesto (regola 11) | minimo deciso (D4); default da definire | A6 e E1; DX-19 (dati aggregati senza identificativi: dimensione minima del gruppo) |
| `continuity.rto_hours` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (F6, A5 o A6); all. 4.1.2(e)-(f) e considerando 13: il regolamento non fissa valori |
| `continuity.rpo_minutes` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (F6, A5 o A6); all. 4.1 e 4.2.2: nessun valore fissato |
| `continuity.restore_test_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (F6, A5 o A6); all. 4.2.6 («periodico», senza valore) |
| `security.patch_deadline_days` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (A5 o A6); all. 6.6.2 («termine ragionevole», senza numero di giorni) |
| `security.vulnerability_scan_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (A5 o A6); all. 6.10.2 («intervalli pianificati», senza valore) |
| `security.supplier_review_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (A5, A6 o F6); all. 5.1.6-5.1.7 («intervalli pianificati») |
| `security.crypto_policy_review_interval_days` | da definire | superadmin | richiesto (regola 11) | da definire (D7) | da assegnare (A6); all. 9.3 («intervalli pianificati») |

La guardia di ambiente `API_ENV` non è in questa tabella: è un'invariante di deploy (§18, D2).

### 19.2 Vincoli normativi di sicurezza (solo se Gravya è in ambito NIS2 come fornitore cloud)

Tre valori numerici fissati dall'allegato del Reg. 2024/2690 (registro v1.6 §9: 1.1.2, 2.1.4, 10.1.3). Il limite di legge non è modificabile da UI (regola 6); il valore operativo lo imposta il superadmin con motivazione e audit, solo verso valori più restrittivi, e resta senza attivazione finché il suo intervallo non è deciso (regola 11). Documento responsabile: da assegnare (A5 o A6).

| Nome | Limite di legge (non modificabile da UI) | Tipo del limite e verso ammesso | Valore operativo | Norma | Stato del valore |
|---|---|---|---|---|---|
| `security.policy_review_interval_days` | riesame della politica di sicurezza almeno annualmente (e dopo incidenti o cambiamenti significativi) | massimo: solo in diminuzione. Conversione: 365 giorni (regola 7, estesa a un anno) | da definire; minimo operativo da definire | N-NIS2-REG allegato 1.1.2 | limite dal registro v1.6; valore da definire (D7) |
| `security.risk_assessment_review_interval_days` | riesame della valutazione dei rischi e del piano di trattamento a intervalli pianificati e almeno con cadenza annuale (e dopo incidenti o cambiamenti significativi) | massimo: solo in diminuzione. Conversione: 365 giorni (regola 7, estesa a un anno) | da definire; minimo operativo da definire | N-NIS2-REG allegato 2.1.4 | limite dal registro v1.6; valore da definire (D7) |
| `security.role_assignment_review_interval_days` | riesame dell'assegnazione del personale ai ruoli quanto meno una volta l'anno | massimo: solo in diminuzione. Conversione: 365 giorni (regola 7, estesa a un anno) | da definire; minimo operativo da definire | N-NIS2-REG allegato 10.1.3 | limite dal registro v1.6; valore da definire. Nome assegnato dal coordinator (revisione di conformità sulla v1.2) |

## Storico modifiche

| Versione | Data | Cosa | Perché |
|---|---|---|---|
| 1.0 | 2026-11-04 | Creazione del catalogo: retention (DX-09, DX-15, DX-16), HITL, enforcement e latenze, grafo, runtime, gateway, workflow, tracing, prompt, eval, soglie di prestazione, incidenti e conformità con i vincoli normativi di DX-10 e DX-22(a), opt-in extra-UE, rimando alle credenziali, valori fissi per documento, non verificato e decisioni aperte DA-CV-01..08. | DX-22(c): documento trasversale unico per le variabili, prima dell'aggiornamento dei documenti dell'ondata 1. |
| 1.1 | 2026-11-04 | Regole di §1 (limite di legge e valore operativo con tipo fisso/minimo/massimo, conversione mesi-giorni, validità tecnica e regole relazionali, segnali in ondata 1, marketing rinviato a D1-D4). §2: durate di sola lettura (C6), variabili per agenzia e scelta a fine contratto, nuove classi (audit delle configurazioni, autenticazione, accessi alle credenziali, consensi e opt-out, backup, mappa degli pseudonimi, segnali di incidente), limiti delle evidenze di incidente (C10). §3, §13: termini degli incidenti rinominati in giorni (`incident.nis2.final_report_days`, `progress_report_interval_days`, `final_report_after_closure_days`, `incident.recurring_window_days`, `recurring_review_interval_days`) con limite di legge, tipo e verso; destinatario CSIRT Italia reso invariante con `csirt_channel` e `csirt_contact`; valutazione iniziale (C3); variabili GDPR sempre attive e `processor_notice_hours` come obbligo contrattuale (C5); stati «deciso» corretti per i valori del registro. §7: tre limiti di rate limit al posto di `b2.rate_limit.default_calls_per_minute`, finestra di `idempotency_key`. §9: tolta `e1.segment_loss_alert_threshold` (soglia in A5). §10, §11: tolte `e2.template.pii_check_mode` e `eval.gate.max_blocking_failures_count` (ora invarianti). §14: opt-in per destinazione con strumento di trasferimento e stato (C9). §15: segreti della CI (C11) e attori delle credenziali. §16: citazione di E1 corretta, «legal hold» in B2, C1, C3, E1, E2, nuove righe. §17: DA-CV-01..07 decise, DA-CV-08 con natura contrattuale decisa, nuove DA-CV-09..17. Nuovi §18 (invarianti, C7) e §19 (sicurezza operativa e accessi, C8). Stato «proposta da validare» senza valore cambiato in «da definire». | Applicazione delle decisioni dell'utente C1-C14 del 2026-11-04 e dei rilievi di revisione sulla v1.0 (conformità e piano). |
| 1.2 | 2026-11-04 | Testata con registro delle norme v1.5. §1: regola 4 (primo avvio secondo D3, segnali, audit e notifiche esclusi dal blocco, nuova versione non leggibile), regola 8 (token di approvazione limitato dal TTL effettivo, regola 8d sulle tracce, massimo per l'idempotenza), regola 10 (approvazione verso terzi non più invariante), nuove regole 11 (intervallo richiesto, D4), 12 (sospensione delle evidenze, D5), 13 (opt-in extra-UE, D5). §2: perimetro e nome delle variabili per agenzia (`retention.<classe>.tenant_value`), scelta di fine contratto sempre disponibile con default (D2), override per classe (D3), primo valore delle nuove classi (F6 o A6), backup (all. 4.2.2(f)). §3: default di piattaforma di `hitl.approval_required_default` in sola lettura. §4, §10: intervallo richiesto per `a3.*` ed `e2.cache.max_ttl_s`. §7: token unico, `b2.idempotency.window_hours_max`. §13: interruttore NIS2 (D1), `incident.scope_review_interval_days`, `incident.annual_turnover_eur`, `incident.recurring_min_count` fisso, `incident.recurring_review_interval_days` come cadenza della norma con massimo prudente, elenco chiuso per `csirt_channel`, soglie più basse come scelta di progetto, `dsar.assist_max_days`. §14: stato dello strumento aggiornato dal superadmin, campo del sub-responsabile (D5, D7). §15: segreti della CI (D6), superadmin mai per conto dell'agenzia. §16: `API_ENV`, token unico, default HITL. §17: DA-CV-08..17 decise, tolta l'opzione (c) di DA-CV-09, nuove DA-CV-18..23, punti non verificati riscritti sul registro v1.5. §18: nuove invarianti (D2, D3, D6, D7). §19: `API_ENV` tolta, nuove righe RTO, RPO, test di ripristino, patch, scansioni, fornitori, crittografia, intervallo richiesto, §19.2 con i due riesami annuali (max 365 giorni). | Applicazione delle decisioni D1-D8 dell'utente del 2026-11-04 e dei rilievi della seconda revisione di plan-auditor e compliance-auditor sulla v1.1. |
| 1.3 | 2026-11-04 | Redatta dal coordinator. Testata con registro delle norme v1.6. Regola 7: conferma delle conversioni dal Reg. 1182/71 con l'avvertenza sulla sua applicabilità e i termini in ore. §2: `retention.tenant_offboarding_days` come minimo di 30 giorni dalla fine del periodo di passaggio (Data Act art. 25(2), condizionato). §4: B2 tra gli utilizzatori di `a3.record.persist_timeout_ms`. §9: nuova `e1.attributes.max_value_bytes` (E1 v1.5). §10: `e2.rollback.propagation_max_s` con intervallo richiesto. §13: `dsar.assist_max_days` con massimo da F6 e non bloccante se illeggibile. §14: strumento di trasferimento e sub-responsabile impostati dal superadmin (DA-CV-19). §17.2: DA-CV-18..23 decise, nessuna DA-CV aperta; precisazione su DA-CV-22 (registro delle cancellazioni solo hash). §19.2: terzo riesame annuale (all. 10.1.3). | Decisioni dell'utente del 2026-11-04 (DA-CV-18..23, fine contratto), variabili nuove dei documenti v1.5 (regola di processo: le unisce il coordinator) e correzioni delle revisioni di plan-auditor e compliance-auditor sulla v1.2. |
