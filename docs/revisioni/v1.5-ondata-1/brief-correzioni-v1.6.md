# Brief per le correzioni v1.6 dell'ondata 1

Scritto dal coordinator il 2026-11-04 (sessione 7). Vale per i doc-writer che portano A1, A3, B1, B2, C1, C3, E1, E2, E3 dalla v1.5 alla v1.6. Restano valide tutte le regole del brief della v1.5 (`brief-doc-writer-v1.5.md`): solo il proprio file, niente shell né file in /tmp, catalogo non modificato (variabili nuove nel campo `variabili` della risposta), nessun valore fisso, verificato e dedotto distinti, **righe precedenti dello Storico intatte**.

## Cosa applicare

1. Le decisioni E1-E16 di `docs/revisioni/v1.5-ondata-1/decisioni-blocco-E.md`, **tutte approvate dall'utente il 2026-11-04** con le raccomandazioni del coordinator, più le due aggiunte dell'utente riportate sotto.
2. Le correzioni della parte 2 dello stesso file.
3. I rilievi dei report della revisione unica che riguardano il tuo documento: `plan-auditor-ondata-1-v1.5.md` e il `compliance-auditor-*.md` del tuo gruppo, nella stessa cartella. Un rilievo che chiede una scelta non coperta da E1-E16 non lo risolvi: lo metti in Appendice C come decisione aperta con raccomandazione.
4. DECISIONS.md: il registrar sta registrando E1-E16 in parallelo; vale il testo del blocco E e delle aggiunte qui sotto.
5. Catalogo: il coordinator l'ha portato alla v1.3 (DA-CV-18..23 decise, `retention.tenant_offboarding_days` come minimo, `e1.attributes.max_value_bytes`). Le note "non ancora in DECISIONS" sono superate: toglile.

## Aggiunte dell'utente (testo alla lettera)

- **E8:** "in aggiunta, la lettura può essere abilitata direttamente da Superadmin in caso di incidente dichiarato (va loggato, ovviamente). In caso di richiesta assistenza, l'admin di agenzia può concedere l'accesso ai dati come parte della richiesta di assistenza."
  Come applicarla (coordinator): vale per tracce (E1), prompt (E2) e ogni dato di tenant visibile al superadmin (A1, A3). Due vie di accesso a dati di un tenant: (a) incidente dichiarato dal superadmin, che abilita la lettura direttamente, con log (DX-18) e riferimento all'incidente; (b) richiesta di assistenza dell'agenzia, in cui l'admin agenzia concede l'accesso come parte della richiesta. In entrambi i casi l'accesso ha perimetro e durata (`access.superadmin_trace_access_ttl_hours`) ed è registrato.
- **E15:** "in aggiunta, per quanto riguarda il trasferimento dobbiamo prevedere sin da subito uno strumento di conversione dei dati in formato strutturato accettato universalmente."
  Come applicarla (coordinator): uno strumento di esportazione dei dati di un tenant è previsto sin da subito; il responsabile è F6 (ondata 2). Ogni documento dell'ondata 1 che conserva dati di un tenant dichiara in §4 o §7 che i suoi dati sono esportabili con lo strumento di F6 e indica quali (tabelle, campi, artefatti), senza fissare il formato: il formato è una proposta del coordinator in attesa di conferma dell'utente.

## Versione

Versione 1.6, riga dello Storico con cosa e perché (decisioni E1-E16 del 2026-11-04 e revisione unica della v1.5). Rispondi con il solo JSON dello schema del doc-writer.
