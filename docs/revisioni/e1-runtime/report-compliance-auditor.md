# Report compliance-auditor — PR main...impl/e1-runtime (Python 3.15, PostgreSQL 18)

Esito: **RIPORTA** (nessun bloccante).

## Letture
- PRINCIPI.md 1-15 di 15; DECISIONS.md: riga «Versioni di runtime» (§6 r. 215) e righe correlate (r. 211, 214, 18-20, 46, 91), il resto solo grep.
- Diff completo del branch: ci.yml, README.md, pyproject.toml, report-implementer.md; requirements.lock.txt solo l'inizio del diff (120 righe), più controlli con grep/awk sull'intero file.
- norme-di-riferimento.md: solo grep (NIS2 art. 21, Reg. 2024/2690 §5-6, CRA).
- Non eseguiti: OSV, verifica del digest dell'immagine, esecuzione dei test.

## Cosa risulta a posto
- Lockfile: ogni pacchetto ha almeno un hash (nessuna voce senza hash; 457 righe `--hash`). Nessun `--index-url`, `--find-links`, URL o `git+`: origine PyPI predefinita. Installazione in CI con `--require-hashes`.
- Immagine `postgres:18` in CI fissata per digest, due job. Action fissate per SHA. Permessi `contents: read`.
- Date di supporto (Python 3.15 al 2031-10-31, PostgreSQL 18 al 2030-11-14) coincidono con DECISIONS §6; non le ho riverificate. Python 3.11 e PostgreSQL 16 uscivano prima.
- RLS, ruoli, `API_ENV`: il diff non tocca migrazioni né codice. Il report dell'implementer dichiara 88 test passati e `test-non-superuser.sh` riuscito su PG 18. Le garanzie E1 non risultano indebolite dal cambio di versione, ma lo so solo dal report: non ho rieseguito nulla. Nel codice di migrazione e negli script non ho trovato `md5`, `password_encryption` o `pg_hba`, quindi nessun effetto evidente delle deprecazioni di PG 18 sull'autenticazione. Il resto (CI con `trust`, password casuale nello script) è invariato.
- Nessun dato personale né extra-UE introdotto. Le immagini si scaricano da Docker Hub a build time, senza dati di tenant.

## Rilievi
1. **da_riportare, NIS2 art. 21(2)(d)(e), art. 21(3); Reg. 2024/2690 all. 5.1, 6.10 (dedotto, solo se Gravya è in ambito).** Le «nessuna vulnerabilità nota» poggia su una verifica OSV manuale dell'implementer, il 2026-11-05. In `.github/workflows/ci.yml` non c'è alcuna scansione automatica (pip-audit/OSV) né Dependabot/Renovate. Il lockfile fissato senza monitoraggio continuo invecchia in silenzio. L'allegato non fissa frequenza né termini di correzione (registro §N-NIS2-REG): sono scelte di Gravya da documentare. Proposta: decidere processo e frequenza di scansione e dell'aggiornamento di lockfile e digest (anche solo una voce di catalogo/DECISIONS), poi implementarlo.
2. **da_riportare, NIS2 art. 21(2)(d) (dedotto).** Residui di catena di fornitura non fissati: `ubuntu-latest` (il runner passerà a Ubuntu 26, come segnalato dall'implementer), `apt-get install postgresql-client` non fissato nel job `test-non-superuser` (`ci.yml` r. 104-105; l'implementer lo dichiara residuo) e il client `psql` che con PG 18 può non coincidere con la versione del server. Le action fissate per SHA girano su Node 20, deprecato: sono v4/v5, da aggiornare per restare supportate. Proposta: aggiornare le action a SHA di versioni su Node 24 e fissare o documentare il client psql; l'immagine del runner resta un rischio accettato, da registrare.
3. **minore, DX-22 / PV-01 (dedotto).** `scripts/agenti.py` r. 52: `postgres:18` come tag mobile (sovrascrivibile con `GRAVYA_PG_IMMAGINE`). È solo sviluppo locale, con dati sintetici, ma non è fissato per digest come in CI. L'immagine di default sta nel codice invece che in una variabile del catalogo. Proposta: fissare il digest o dichiarare lo script fuori ambito.
4. **minore (verificato).** DECISIONS §6 r. 215 dice «`pydantic` fissata 2.14.2 … `pydantic-core` 2.50.2», ma il lockfile ha ora 2.14.3 e 2.50.4. Il lockfile segue la regola «ultima versione», mentre il testo è superato. Proposta: far correggere la riga al `registrar` (è una nota di stato, non una decisione nuova).
5. **minore (dedotto).** `--extra=dev` mette pytest, pluggy, pygments, iniconfig e simili nello stesso lockfile del runtime. Se il lockfile servisse a un'immagine di produzione, la superficie d'attacco sarebbe più ampia del necessario (NIS2 art. 21(2)(e)). Proposta: lockfile separati per runtime e dev, quando si arriverà al deploy.
6. **minore (dedotto).** `requires-python = ">=3.15"` senza limite superiore, mentre il lockfile è compilato e verificato solo su 3.15.2. Il rischio è modesto, perché l'installazione usa il lockfile con hash. Una versione maggiore futura non verificata resterebbe ammessa. Proposta: limite superiore, o lasciare com'è.
7. **minore (dedotto).** Il digest `postgres:18@sha256:bd5dfa49…` non l'ho potuto verificare contro il registry (nessun accesso di rete richiesto dal task). Se il digest è di un'immagine multi-arch, il fissaggio vale. Il CI ha passato (run 42084513531, da report). L'immagine non viene riesaminata alla ricezione di patch di sicurezza di PG 18.x finché il digest non cambia: rientra nel rilievo 1.

## Da aggiungere al registro
Nessuna norma nuova. NIS2 art. 21 e Reg. 2024/2690 sono già presenti e letti, come indicato nel registro. L'applicabilità a Gravya resta aperta («plausibile ma da accertare»). Il CRA (N-CRA) non vale per il SaaS puro.
