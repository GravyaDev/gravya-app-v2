# Report compliance-auditor — PR main...impl/ci-fornitura

Esito: **RIPORTA** (nessun bloccante).

## Letture
- PRINCIPI.md 1-15 di 15; DECISIONS.md: righe «Catena di fornitura» (§4 r. 155, §6 r. 218), il resto solo grep.
- Diff completo del branch (escluso report-implementer, letto a parte), tutti i file: ci.yml, fornitura.yml, dependabot.yml, osv-check.py, test-non-superuser.sh, test_ci_osv_check.py, README.
- Report e1-runtime del compliance-auditor, intero; report-implementer, intero.
- norme-di-riferimento.md: solo grep e righe 436-442 (NIS2 art. 21, Reg. 2024/2690).
- Verificato con `gh api`: i due SHA delle action coincidono con i tag v7.0.1 e v7.1.0. Lockfile: 18 pacchetti, tutti nel formato `nome==versione` che il parser legge; nessuna riga fuori formato. Non ho eseguito i test né le CI.

## Risposta ai rilievi a e b di e1-runtime
- **a (scansione e aggiornamenti):** scansione OSV coperta (push, PR, settimanale). Aggiornamenti coperti solo per le action: manca Dependabot per pip, che la decisione prevedeva. Parziale.
- **b (runner, psql, action):** coperto. `ubuntu-24.04`, `psql` dall'immagine del servizio con digest (controllata con `case`), action su Node 24 fissate per SHA. Resta il rischio accettato dell'immagine del runner (etichetta di versione, non fissa), da registrare.

## Cosa risulta a posto
- Permessi: `contents: read` a livello di workflow e di job in tutti i job; nessun segreto né token con scrittura. I trigger `pull_request` non danno accesso a segreti.
- Fail-closed di `osv-check.py`: exit 2 se OSV non risponde, se la risposta non è valida (lunghezza di `results`, `id` mancante), se il lockfile è vuoto o illeggibile; exit 1 se ci sono vulnerabilità. Paginazione e blocchi gestiti. I test coprono questi casi.
- Job `digest-postgres`: fallisce se in `ci.yml` non c'è esattamente una immagine con digest, se il digest attuale è vuoto o diverso.
- Nessun dato personale né di tenant coinvolto. A OSV vanno solo nomi e versioni dei pacchetti.
- Il digest di PostgreSQL sta in un solo punto (ancora YAML).

## Rilievi
1. **da_riportare, NIS2 art. 21(2)(d), Reg. 2024/2690 (dedotto: applicabilità a Gravya da accertare).** Dependabot per pip non configurato, mentre DECISIONS §6 «Catena di fornitura» (1) dice «Dependabot settimanale per i pacchetti Python e per le action». Il report dell'implementer dice che la documentazione non garantisce la rigenerazione del lockfile con hash. Il rischio resta limitato: OSV settimanale segnala le vulnerabilità sul lockfile (rilevazione sì, proposta di aggiornamento no). Restano scoperti: nessuna PR di aggiornamento, quindi la correzione dipende da un intervento manuale; versioni obsolete ma senza CVE non si vedono; le dipendenze di build sono nel lockfile (`--all-build-deps`) e quindi guardate da OSV. Proposta: far scegliere all'utente tra provare Dependabot pip con una PR reale, o un'altra via (job settimanale che rigenera il lockfile e apre una PR). Intanto registrare in DECISIONS che il punto 1 è attuato solo in parte.
2. **da_riportare, NIS2 art. 21(2)(d) (dedotto).** Nessuna notifica garantita sul fallimento del job settimanale. Una esecuzione `schedule` fallita è visibile solo nella scheda Actions e agli utenti che GitHub avvisa di default (chi ha modificato per ultimo il cron). Non c'è un destinatario di Gravya né un segnale verso A5. Per i `schedule` GitHub può inoltre disattivare il workflow dopo un periodo di inattività del repository (da verificare nella documentazione GitHub, non nel registro). Se il controllo fallisce in silenzio, il monitoraggio è solo apparente. Proposta: indicare chi riceve l'avviso (notifiche GitHub, issue automatica al fallimento) e se il fallimento va trattato come segnale ad A5; decidere se il workflow `fornitura` deve essere un controllo richiesto per il merge.
3. **minore, NIS2 art. 21(2)(d) (dedotto).** `osv-check.py` fa fallire ogni push su qualsiasi vulnerabilità, anche senza correzione disponibile, senza severità e senza un'eccezione tracciata (ad esempio un elenco di ID accettati con motivo e scadenza). Rischio pratico: il controllo viene ignorato o disattivato, il che peggiora la copertura. Proposta: prevedere un meccanismo di eccezione versionato, con motivo e scadenza, prima che serva.
4. **minore (dedotto).** Il parser ignora in silenzio le righe di pacchetto in formato diverso da `nome==versione` (ad esempio `nome[extra]==v` o `nome @ url`): sarebbe un caso fail-open. Oggi tutti i 18 pacchetti sono letti. Proposta: far fallire il controllo se una riga non vuota, non commento e non di continuazione non corrisponde, oppure se il numero di voci non coincide con quello dei blocchi `--hash`.
5. **minore, NIS2 art. 21(2)(d) (dedotto).** Il job `digest-postgres` segnala solo che il tag è cambiato; non scansiona l'immagine fissata (livello Debian e librerie) né il runner. Una vulnerabilità nel digest fissato non viene vista finché il tag non si muove. Per la CI con dati sintetici il rischio è basso; vale di più per l'immagine di produzione del primo deploy. Proposta: registrarlo come residuo e riprenderlo quando si definisce l'immagine di produzione (DECISIONS §6 «Catena di fornitura» (3)).
6. **minore (dedotto).** Il ramo «digest cambiato → fallisce» non è stato provato (lo dichiara l'implementer). Il ramo vuoto e il caso di più immagini sono codice leggibile ma non provato. Proposta: una prova con un digest diverso, anche con `workflow_dispatch`.
7. **minore (dedotto).** In `test-non-superuser.sh` la password casuale del ruolo di prova finisce negli argomenti di `docker run` (DSN) e quindi nell'elenco dei processi del runner. Il runner è effimero, i dati sono sintetici e la password vale solo per il database usa e getta. Nessuna azione richiesta; da non estendere a credenziali reali.
8. **minore (dedotto).** Il runner `ubuntu-24.04` è una etichetta di versione e non un'immagine fissa; il sostituto futuro di 24.04 non è monitorato. Proposta: registrare come rischio accettato, come già suggerito in e1-runtime rilievo 2.

## Da aggiungere al registro
Nessuna norma nuova. NIS2 art. 21 e Reg. 2024/2690 sono già nel registro; l'applicabilità a Gravya resta aperta. Il comportamento delle esecuzioni `schedule` di GitHub (disattivazione per inattività, destinatario degli avvisi) non è nel registro e non è una norma: va letto nella documentazione di GitHub dall'implementer o dal coordinator.
