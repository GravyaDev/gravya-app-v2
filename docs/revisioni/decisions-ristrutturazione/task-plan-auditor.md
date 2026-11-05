# Task per il plan-auditor: verifica della ristrutturazione di DECISIONS.md

Preparato dal coordinator il 2026-11-05 (sessione 8). Decisione dell'utente («Ok per le decisioni», 2026-11-05): DECISIONS.md contiene solo le decisioni in vigore e aperte, nella forma corrente, con il motivo utile a capirle; storico e testi alla lettera in un archivio separato; ristrutturazione fatta una tantum dal coordinator su una copia, verificata dal plan-auditor, poi sostituita dal registrar.

File da confrontare (tutti nel repository, branch `claude/docs-ondata-1`):
- Originale: `docs/DECISIONS.md` (329 righe, 127 KB).
- Candidato: `docs/revisioni/decisions-ristrutturazione/DECISIONS-candidato.md`.
- Archivio candidato: `docs/revisioni/decisions-ristrutturazione/decisioni-archivio-candidato.md` (originale integrale, intestazioni abbassate).

Cosa verificare, riga per riga dell'originale:
1. **Nessuna decisione in vigore persa o alterata.** Per ogni riga decisa dell'originale (DX, DA, DA-CV, righe di §6, durate di §5), il candidato riporta il contenuto **in vigore** dopo tutte le precisazioni successive (per esempio DX-09, DX-10, DX-19, DX-22, DA-B2-07 hanno precisazioni del 2026-11-04). Segnala ogni differenza di sostanza: un vincolo, un'eccezione, un valore, una condizione o un responsabile mancante o cambiato.
2. **Nessuna decisione aperta persa:** DA aperte, DX aperte, riserve («Decisa in parte», «con condizione», «ipotesi di lavoro»).
3. **Punti «Da riportare» ancora aperti** dell'originale §4 tutti presenti nel candidato §4; quelli che il candidato omette devono risultare chiusi nell'originale (barrati o con una chiusura scritta). Segnala quelli omessi ma ancora aperti.
4. **Righe tolte:** elenca le righe dell'originale non riportate nel candidato e, per ciascuna, se è davvero superata, chiusa, assorbita o un passo di processo concluso (giri di revisione di E1, regole di processo della v1.5 e del catalogo 1.2, lotti del registro).
5. **Riferimenti:** numeri di sezione mantenuti (§1 DX, §2 DA, §4 Da riportare, §5 durate, §6 regole, §7 DA-CV), perché i documenti citano «DECISIONS §5» ecc.; riferimenti interni coerenti; alias e chiusure delle DA (paragrafo dopo la tabella di §2) corretti.
6. **Archivio:** contiene l'originale integrale.

Non modificare nessun file salvo il report; niente commit; nessun file fuori dalla cartella. Nel JSON solo le chiavi dello schema.

Report: `docs/revisioni/decisions-ristrutturazione/report-plan-auditor.md`. Esito BLOCCA se si perde una decisione in vigore o aperta; RIPORTA per differenze di forma o dubbi.
