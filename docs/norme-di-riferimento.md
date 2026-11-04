# Registro delle norme di riferimento di Gravya v2

**Versione:** 1.2 · **Data:** 2026-11-04 · **Curatore:** regulatory-researcher · **Stato:** v1.2 = v1.1 + lotto 2 (N-GDPR letto sul testo ufficiale integrale in GU, nuove schede N-DPF e N-EDPB); da portare nel repository dopo la verifica del coordinator.

Questo documento è l'unico punto di verità sulle norme che Gravya v2 deve rispettare (PV-01). Il `compliance-auditor` e gli altri agenti citano le norme da qui, non a memoria. Non è un parere legale e non sostituisce il DPO.

## 0. Come leggere il registro

**Separazione tra norma e interpretazione.** In ogni scheda la parte «Contenuto della norma» riporta ciò che la fonte dice (sintesi in parole mie, citazioni testuali solo brevi). La parte «Applicazione a Gravya» è interpretazione, sempre marcata **[INTERPRETAZIONE — da confermare con un legale]**. Un'interpretazione non è un requisito finché un legale o il DPO non la conferma e il coordinator non la registra come decisione.

**Segni di verifica sugli articoli** (valgono per il testo della norma, non per le interpretazioni):

| Segno | Significato |
|---|---|
| ✔ | Testo letto in questa sessione su una fonte ufficiale (EUR-Lex, Normattiva, Gazzetta Ufficiale, Garante, Commissione UE, ACN, MIMIT, EDPB, sito del Parlamento). |
| ◐ | Letto solo in un estratto di una pagina ufficiale (la pagina completa non si apriva), oppure letto su una copia non ufficiale del testo ufficiale. Da riverificare sulla fonte prima di farne un requisito. |
| ○ | Non riletto: noto da conoscenza, non verificato in questa sessione. Non va citato come verificato. |
| non_verificata | Non ho potuto aprire la fonte ufficiale: la voce non è utilizzabile come requisito. |

**Fonti.** Studi legali, blog e riassunti sono serviti solo a trovare la fonte ufficiale. Dove un dato (una data, un numero di provvedimento) l'ho visto solo su una fonte non ufficiale lo scrivo con «fonte non ufficiale» e la voce resta ◐ o non_verificata.

**Limite tecnico di questa sessione.** Le pagine di acn.gov.it non si aprivano con lo strumento di lettura («url_not_accessible»): ho letto gli estratti di quelle pagine mostrati dalla ricerca. Il testo integrale di EUR-Lex per il consolidato dell'AI Act e per alcuni altri atti si apriva solo in parte.

## 1. Indice

| ID | Norma | Verifica | Applicabile a Gravya (interpretazione) |
|---|---|---|---|
| N-GDPR | Reg. (UE) 2016/679 | ✔ per gli articoli del perimetro (4(5), 4(7), 4(8), 5, 17, 25, 28, 32-34, 44-49, 99: testo originale GU, rettifica 2018 non confrontata); ✔ considerando; ◐ art. 19; ○ altri articoli | Sì, come responsabile (DX-11) e come titolare per i propri dati |
| N-DPF | Decisione di esecuzione (UE) 2023/1795 (adeguatezza UE-USA, Data Privacy Framework) | ✔ testo; ◐ stato giudiziario (impugnazione C-703/25 P pendente secondo le fonti viste); «in vigore oggi» non_verificato | Solo se il provider USA è nell'elenco DPF; altrimenti art. 46 |
| N-EDPB | Linee guida 01/2025 (pseudonimizzazione, **bozza**), 4/2019 v2.0 (art. 25), Raccomandazioni 01/2020 v2.0 (misure supplementari) | ◐ (estratti ufficiali EDPB) | Orientamenti non vincolanti per trace, minimizzazione e trasferimenti verso LLM |
| N-PRIV-IT | d.lgs. 196/2003 (Codice privacy), artt. 122 e 130 | ◐ | Sì, per cookie, email/SMS di marketing e tracking pixel |
| N-EPRIVACY | Dir. 2002/58/CE (artt. 5(3), 13) | ◐ | Sì, tramite il Codice privacy |
| N-RPO | Registro pubblico delle opposizioni (l. 5/2018, DPR 26/2022) | ◐ | Solo per telefono e posta cartacea, non per email/SMS |
| N-GAR-COOKIE | Linee guida del Garante su cookie e strumenti di tracciamento (2021) | ✔ | Sì, per sito/app di Gravya e script serviti alle agenzie |
| N-GAR-PIXEL | Linee guida del Garante sui tracking pixel nelle email (2026) | ◐ | Sì, direttamente (piattaforme di invio massivo di email) |
| N-ECOMM | Dir. 2000/31/CE e d.lgs. 70/2003 (artt. 8, 9) | ◐ | Sì, per le comunicazioni commerciali inviate per conto delle agenzie |
| N-NIS2 | Dir. (UE) 2022/2555 | ◐ | Probabile, da accertare (SaaS come servizio di cloud computing, soglia dimensionale) |
| N-NIS2-IT | d.lgs. 138/2024 e determinazioni ACN | ◐ | Come sopra |
| N-AIACT | Reg. (UE) 2024/1689 | ✔ per art. 50, 6; ○ altri | Sì: art. 50 e art. 4; non alto rischio (DX-11) |
| N-AIACT-OMN | Reg. (UE) 2026/1744 (Digital Omnibus sull'IA) | ✔ | Sì, cambia il calendario |
| N-AIACT-COM | Documenti della Commissione che attuano l'AI Act | ✔/◐ | Sì |
| N-AIACT-IT | l. 132/2025 e d.lgs. 179/2026 | ◐ | Sì, per autorità e sanzioni |
| N-CRA | Reg. (UE) 2024/2847 | ◐ (dati ufficiali Commissione) | Il SaaS puro no; i componenti software distribuiti agli utenti sì |
| N-DATAACT | Reg. (UE) 2023/2854 | ◐ | Sì, Cap. VI (cambio fornitore) |
| N-DSA | Reg. (UE) 2022/2065 | ◐ | Possibile, solo come servizio di hosting |
| N-OMNIBUS-DATI | COM(2025) 837, Digital Omnibus su GDPR/ePrivacy/Data Act/NIS | ◐ | **Solo proposta, non adottata** |

## 2. Calendario consolidato (solo date verificate o marcate)

| Data | Evento | Norma | Verifica |
|---|---|---|---|
| 2025-02-02 | Si applicano i Capi I e II dell'AI Act (art. 4 alfabetizzazione, art. 5 pratiche vietate) | N-AIACT | ✔ (art. 113, terzo comma, lett. a, come riscritto dall'Omnibus) |
| 2025-08-02 | Si applicano gli obblighi dei fornitori di modelli GPAI | N-AIACT | ✔ (pagina Commissione) |
| 2025-09-12 | Si applica il Data Act | N-DATAACT | ◐ (metadato EUR-Lex) |
| 2026-01-15 | Si applica la Determinazione ACN 379907/2025 (specifiche di base NIS) | N-NIS2-IT | ◐ (FAQ ACN) |
| 2026-07-27 | Entra in vigore il Digital Omnibus sull'IA | N-AIACT-OMN | ✔ |
| 2026-08-02 | Data generale di applicazione dell'AI Act: si applica l'art. 50; la Commissione ottiene i poteri di enforcement sui modelli GPAI | N-AIACT | ✔ |
| 2026-09-11 | Segnalazioni dell'art. 14 CRA per i prodotti con elementi digitali | N-CRA | ✔ (pagina Commissione) |
| 2026-10-23 | Entra in vigore il d.lgs. 179/2026 | N-AIACT-IT | ✔ (Normattiva) |
| 2026-10-29 | Scade il termine di 6 mesi per adeguarsi alle linee guida sui tracking pixel (GU 29.4.2026) | N-GAR-PIXEL | ◐: il termine è «sei mesi dalla pubblicazione in GU», la data è un calcolo. **Già scaduto alla data di questo registro.** |
| 2026-12-02 | Si applicano i nuovi divieti dell'art. 5(1)(ba), (bb); termine dell'art. 50(2) per i sistemi generativi già sul mercato prima del 2.8.2026 | N-AIACT-OMN | ✔ |
| 2026-12-31 | Termine per designare il referente CSIRT per i soggetti NIS inseriti per la prima volta nel 2026 | N-NIS2-IT | fonte non ufficiale: non verificato |
| 2027-01-01 | Notifica degli incidenti significativi di base per i soggetti inseriti nell'elenco NIS nel 2026 | N-NIS2-IT | ◐ (news e FAQ ACN) |
| 2027-01-12 | Costi di passaggio a zero (art. 29 Data Act) | N-DATAACT | ✔ (art. 29(1), estratto EUR-Lex) |
| 2027-07-31 | Misure di sicurezza di base per i soggetti inseriti nell'elenco NIS nel 2026 | N-NIS2-IT | ◐ (FAQ ACN) |
| 2027-08-02 | Sandbox nazionali dell'AI Act; termine per i modelli GPAI già sul mercato prima del 2.8.2025 | N-AIACT | ✔ |
| 2027-12-02 | Si applicano gli obblighi per i sistemi ad alto rischio dell'Allegato III (Cap. III, sez. 1-3) | N-AIACT-OMN | ✔ |
| 2027-12-11 | Applicazione piena del CRA | N-CRA | ✔ |
| 2028-08-02 | Si applicano gli obblighi per i sistemi ad alto rischio dell'Allegato I | N-AIACT-OMN | ✔ |
| 2030-08-02 | Termine per i sistemi ad alto rischio destinati alle PA già sul mercato | N-AIACT-OMN | ✔ (art. 111(2)) |

---

## 3. Protezione dei dati e comunicazioni elettroniche

### N-GDPR — Regolamento generale sulla protezione dei dati

- **Estremi:** Regolamento (UE) 2016/679 del 27 aprile 2016, GU L 119 del 4.5.2016 (rettifica GU L 127 del 23.5.2018).
- **Fonte ufficiale:** https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng
- **Date:** in vigore dal 24 maggio 2016 ✔ (metadato EUR-Lex: prima entrata in vigore 2016-05-24; pubblicazione 2016-05-04); applicabile dal 25 maggio 2018 ✔ (art. 99: entrata in vigore il ventesimo giorno dopo la pubblicazione in GU; «si applica a decorrere da 25 maggio 2018»; GU L 119 del 4.5.2016, testo originale, Cellar).
- **Verificata il:** 2026-11-04 (v1.0, lotto 1 in v1.1, lotto 2 in v1.2) · **Stato:** ✔ per gli articoli segnati ✔ in tabella. **Fonte del lotto 2:** testo italiano originale pubblicato in GU L 119 del 4.5.2016, letto dal Cellar dell'Ufficio delle pubblicazioni (https://publications.europa.eu/resource/celex/32016R0679), cioè l'archivio da cui EUR-Lex serve i testi. **Limite:** non è la versione consolidata e non incorpora la rettifica GU L 127 del 23.5.2018, che non ho confrontato. Le sintesi del lotto 1 (nate da estratti EUR-Lex in inglese e da copie non ufficiali) sono state riviste sul testo italiano e confermate. I **considerando** 26, 28-30, 39, 65, 78, 81, 83, 85 sono ✔ (letti per intero nel lotto 1). Gli articoli non elencati in tabella restano ○.

**Contenuto della norma (sintesi):**

| Articolo | Sintesi | Verifica |
|---|---|---|
| 4(7), 4(8) | **4(7)** titolare: chi, da solo o insieme ad altri, determina finalità e mezzi del trattamento (se finalità e mezzi sono fissati dal diritto UE o nazionale, questo può designare il titolare o i criteri per designarlo). **4(8)** responsabile: chi tratta dati personali per conto del titolare. | ✔ (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata) |
| 4(5) e considerando 26, 28, 30 | **Art. 4(5)** (definizione di pseudonimizzazione: trattamento che impedisce di attribuire i dati a una persona senza informazioni aggiuntive, tenute separate): trattamento dei dati personali in modo che non possano più essere attribuiti a un interessato specifico senza informazioni aggiuntive, a condizione che queste siano conservate separatamente e soggette a misure tecniche e organizzative che impediscano di attribuire i dati a una persona identificata o identificabile (✔ testo letto). **Considerando 26 ✔ (letto per intero):** i dati pseudonimizzati, attribuibili a una persona con informazioni aggiuntive, «should be considered to be information on an identifiable natural person», cioè restano dati personali. Per stabilire se una persona è identificabile si considerano tutti i mezzi ragionevolmente prevedibili (anche da parte di terzi, per esempio l'individuazione/singling out), con fattori oggettivi come costi, tempo e tecnologia disponibile. I principi non si applicano alle informazioni anonime, cioè non riferite a una persona identificata o identificabile o rese anonime in modo che l'interessato non sia più identificabile. Considerando 28: la pseudonimizzazione può ridurre i rischi e aiutare a rispettare gli obblighi, ma non è un'esenzione. Considerando 30: identificativi online (indirizzi IP, cookie, altri identificatori) possono lasciare tracce che, combinate con identificatori univoci, servono a creare profili e a identificare le persone. | ✔ considerando 26, 28, 30; ✔ art. 4(5) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata) |
| 5(1)(c), (e), 5(2) | **5(1)(c)** minimizzazione: dati adeguati, pertinenti e limitati a quanto necessario rispetto alle finalità. **5(1)(e)** limitazione della conservazione: identificabilità degli interessati non oltre il tempo necessario per le finalità (periodi più lunghi solo per archiviazione nel pubblico interesse, ricerca o statistica, con le garanzie dell'art. 89(1)); la Corte di giustizia (C-77/21, Digi) lo applica anche a una copia di dati creata per test e correzione errori. **5(2)** il titolare è responsabile del rispetto del par. 1 e deve poter dimostrarlo («accountability»). **5(1)(f)** integrità e riservatezza: dati trattati in modo da garantirne un'adeguata sicurezza, compresa la protezione da trattamenti non autorizzati o illeciti e da perdita, distruzione o danno accidentali, con misure tecniche e organizzative adeguate. | ✔ 5(1)(c), (e), (f), 5(2) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata). Nota: il testo italiano di 5(2) dice che il titolare «è competente per il rispetto» del par. 1 e «in grado di comprovarlo». |
| 17 | **17(1)** l'interessato ha diritto alla cancellazione senza ingiustificato ritardo e il titolare ha l'obbligo di cancellare quando ricorre uno dei motivi (dati non più necessari alle finalità; revoca del consenso senza altra base giuridica; opposizione ex art. 21 senza motivi legittimi prevalenti, o opposizione al marketing diretto; trattamento illecito; obbligo di legge di cancellare; dati di minori raccolti per servizi della società dell'informazione). **17(2)** se il titolare ha reso pubblici i dati, adotta misure ragionevoli (tecnologia disponibile, costi) per informare gli altri titolari della richiesta. **17(3)** i par. 1 e 2 non si applicano nella misura in cui il trattamento è necessario: (a) per la libertà di espressione e informazione; (b) per un obbligo di legge che richiede il trattamento o per un compito di interesse pubblico o pubblici poteri; (c) per motivi di sanità pubblica (art. 9(2)(h), (i) e 9(3)); (d) per archiviazione nel pubblico interesse, ricerca o statistica (art. 89(1)), se la cancellazione rischia di rendere impossibile o pregiudicare gravemente tali obiettivi; (e) per accertare, esercitare o difendere un diritto in sede giudiziaria. Il considerando 65 ✔ (letto) elenca le stesse categorie di conservazione lecita. Nota di lettura: il motivo 17(1)(c) comprende l'opposizione al marketing diretto (art. 21(2)); il motivo (f) rinvia ai servizi della società dell'informazione offerti direttamente ai minori (art. 8(1)). L'art. 19 (comunicazione ai destinatari della cancellazione, salvo impossibilità o sforzo sproporzionato) l'ho visto in estratto EUR-Lex. | ✔ art. 17 intero, par. 1 (a)-(f), 2, 3 (a)-(e) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata); ✔ considerando 65; ◐ art. 19 |
| 25 | **25(1)** *privacy by design*: tenuto conto dello stato dell'arte, dei costi e di natura, ambito, contesto e finalità, nonché dei rischi per i diritti e le libertà, il titolare adotta, sia al momento di determinare i mezzi del trattamento sia durante il trattamento, misure tecniche e organizzative adeguate, «such as pseudonymisation», pensate per attuare in modo efficace i principi (per esempio la minimizzazione) e integrare le garanzie necessarie. **25(2)** *by default*: misure per garantire che siano trattati per impostazione predefinita solo i dati necessari per ogni specifica finalità; l'obbligo riguarda quantità di dati raccolti, portata del trattamento, periodo di conservazione e accessibilità; in particolare i dati non devono essere accessibili senza l'intervento della persona a un numero indefinito di persone fisiche. **25(3)** una certificazione approvata (art. 42) può servire come elemento per dimostrare la conformità ai par. 1 e 2. Obbligo del **titolare**: il considerando 78 ✔ invita i produttori di prodotti e servizi a tenere conto della protezione dei dati, senza imporre loro un obbligo diretto. | ✔ par. 1-3 (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata); ✔ considerando 78. La sintesi del lotto 1 era corretta; la versione italiana dice «misure tecniche e organizzative adeguate, quali la pseudonimizzazione». |
| 6, 7 | Basi giuridiche e condizioni del consenso. | ○ (6(1)(a)-(f) viste di passaggio nel testo locale, non sintetizzate) |
| 12-22 | Informativa e diritti dell'interessato (accesso, cancellazione, opposizione, portabilità). | ○ (salvo art. 17, sopra) |
| 28 | Il titolare usa solo responsabili che offrono garanzie sufficienti; il trattamento è regolato da contratto. Il responsabile: assiste il titolare nei diritti degli interessati; assiste per gli artt. 32-36; a scelta del titolare cancella o restituisce i dati a fine servizio, salvo obblighi di legge; mette a disposizione le informazioni e consente audit; avvisa subito se un'istruzione viola la norma. Per ricorrere a un altro responsabile servono le condizioni dei par. 2 e 4. | ✔ art. 28(1)-(10) letto per intero nel testo locale (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata). Dettagli letti: 28(2) autorizzazione scritta, specifica o generale, per altri responsabili, con informazione delle modifiche e possibilità di opposizione; 28(3)(a) trattamento solo su istruzione documentata, anche per i trasferimenti verso paesi terzi; 28(4) stessi obblighi a catena e piena responsabilità del responsabile iniziale verso il titolare; 28(9) contratto in forma scritta, anche elettronica. |
| 28(10) | **Contenuto preciso:** «Without prejudice to Articles 82, 83 and 84», se un responsabile **viola il regolamento determinando finalità e mezzi** del trattamento, è considerato titolare **rispetto a quel trattamento**. Quindi: (1) la riqualificazione scatta quando il responsabile *determina finalità e mezzi* e con ciò *viola* il regolamento (la condizione è letta nel testo; l'articolo non dice che ogni scelta sui mezzi lo renda titolare); (2) vale solo per quel trattamento, non per tutti quelli svolti per il titolare; (3) restano ferme la responsabilità civile (art. 82), le sanzioni amministrative (art. 83) e le altre sanzioni (art. 84), cioè la riqualificazione non le sostituisce. Il considerando 81 ✔ (letto) dice che il trattamento del responsabile è retto da contratto con oggetto, durata, natura, finalità, tipo di dati e categorie di interessati, e che a scelta del titolare il responsabile restituisce o cancella i dati salvo obblighi di legge. | ✔ (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata). Il testo italiano è «Fatti salvi gli articoli 82, 83 e 84, se un responsabile del trattamento viola il presente regolamento, determinando le finalità e i mezzi del trattamento, è considerato un titolare del trattamento in questione»: la sintesi del lotto 1 è confermata; «in questione» equivale a «rispetto a quel trattamento». |
| 30(2) | Il responsabile tiene un registro delle categorie di trattamenti svolti per conto del titolare. | ✔ |
| 32 | **32(1)** titolare **e** responsabile adottano misure tecniche e organizzative adeguate al rischio, tenuto conto di stato dell'arte, costi, natura, ambito, contesto e finalità e dei rischi per i diritti e le libertà, comprese, «as appropriate»: pseudonimizzazione e cifratura; capacità di assicurare riservatezza, integrità, disponibilità e resilienza di sistemi e servizi; capacità di ripristinare tempestivamente disponibilità e accesso ai dati dopo un incidente fisico o tecnico; procedura per provare, verificare e valutare regolarmente l'efficacia delle misure. **32(2)** il livello di sicurezza si valuta guardando ai rischi del trattamento (distruzione, perdita, modifica, divulgazione o accesso non autorizzati, accidentali o illeciti). **32(3)** codici di condotta (art. 40) o certificazioni (art. 42) approvati possono servire a dimostrare la conformità. **32(4)** chi agisce sotto l'autorità del titolare o del responsabile e ha accesso ai dati li tratta solo su istruzione del titolare, salvo obbligo di legge. Il considerando 83 ✔ cita la cifratura come esempio. | ✔ art. 32(1)-(4) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata); ✔ considerando 83. Sintesi del lotto 1 confermata. |
| 33(1), 33(2) | **33(1)** in caso di violazione di dati personali il **titolare** notifica all'autorità di controllo competente (art. 55) senza ingiustificato ritardo e, ove possibile, **entro 72 ore** da quando ne è venuto a conoscenza, salvo che sia improbabile un rischio per i diritti e le libertà delle persone; oltre le 72 ore la notifica indica i motivi del ritardo. **33(2)** il **responsabile** notifica al titolare «without undue delay» dopo aver preso conoscenza della violazione: **il GDPR non fissa un numero di ore per il responsabile**; le 72 ore sono un termine del titolare. Il considerando 85 ✔ ripete le 72 ore e ammette informazioni a fasi. Par. 3-5 (contenuto minimo, informazioni a fasi, documentazione di tutte le violazioni da parte del titolare) visti in estratto. | ✔ art. 33(1)-(5) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata); ✔ considerando 85. Conferma: il testo italiano del par. 2 dice «senza ingiustificato ritardo», senza ore. |
| 34 | Se la violazione presenta probabilmente un rischio elevato, il titolare la comunica agli interessati senza ingiustificato ritardo, con linguaggio semplice e chiaro. La comunicazione non serve se ricorre una delle condizioni del par. 3, tra cui misure di protezione già applicate che rendono i dati incomprensibili a chi non è autorizzato (per esempio la cifratura); le altre condizioni del par. 3 sono: (b) il titolare ha adottato successivamente misure che scongiurano il sopraggiungere del rischio elevato; (c) la comunicazione richiederebbe sforzi sproporzionati e allora si procede con una comunicazione pubblica o misura simile di pari efficacia. Se il titolare non ha comunicato, l'autorità, valutata la probabilità di rischio elevato, può imporlo o ritenere soddisfatte le condizioni del par. 3 (34(4)). | ✔ art. 34(1)-(4) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata) |
| 35 | Valutazione d'impatto quando il trattamento, specie con nuove tecnologie, presenta rischio elevato. | ✔ (35(1) letto) |
| 44-49 (Cap. V) | **44** principio generale: un trasferimento a un paese terzo o a un'organizzazione internazionale è ammesso solo se rispettate le condizioni del Cap. V, anche per i trasferimenti successivi; lo scopo è che il livello di protezione garantito dal GDPR non sia pregiudicato (✔). **45 (adeguatezza):** se la Commissione ha deciso che il paese terzo, un territorio o settori specifici, o l'organizzazione garantiscono un livello adeguato, il trasferimento è ammesso senza autorizzazioni specifiche (45(1)); la Commissione la può decidere con atto di esecuzione per un paese, un territorio o settori specifici, o un'organizzazione, garantiscono un livello adeguato; l'atto prevede un riesame periodico almeno ogni quattro anni e specifica ambito territoriale e settoriale (45(3)); le decisioni non escludono i trasferimenti con i meccanismi degli artt. 46-49 (45(7)); la Commissione pubblica nella GU e sul suo sito l'elenco dei paesi per cui l'adeguatezza è o non è più garantita (45(8)); le decisioni adottate sotto la direttiva 95/46/CE restano in vigore finché non modificate, sostituite o abrogate (45(9)). **Criteri (45(2)):** stato di diritto, diritti umani, legislazione generale e settoriale (anche su sicurezza pubblica, difesa, sicurezza nazionale, diritto penale e accesso delle autorità pubbliche ai dati) e sua attuazione, norme sui trasferimenti successivi, diritti azionabili e ricorso effettivo; esistenza e funzionamento di autorità di controllo indipendenti; impegni internazionali. **45(4)** la Commissione monitora in continuo gli sviluppi che possono incidere sulle decisioni. **Revoca (45(5)):** se risulta che il livello adeguato non è più garantito, la Commissione revoca, modifica o sospende la decisione nella misura necessaria con atto di esecuzione, **senza effetto retroattivo**, anche con procedura d'urgenza (art. 93(3)); **45(6)** poi avvia consultazioni con il paese terzo. **46 (garanzie adeguate):** in assenza di decisione di adeguatezza, titolare o responsabile possono trasferire solo se hanno fornito garanzie adeguate e a condizione che siano disponibili diritti azionabili e mezzi di ricorso effettivi per gli interessati (46(1)); **46(2)** garanzie adeguate senza autorizzazione specifica del Garante: strumento vincolante tra autorità pubbliche; norme vincolanti d'impresa (art. 47); clausole tipo adottate dalla Commissione (art. 93(2)); clausole tipo di un'autorità di controllo approvate dalla Commissione; codice di condotta approvato (art. 40) con impegno vincolante del destinatario; certificazione approvata (art. 42) con impegno vincolante. **46(3)** previa autorizzazione dell'autorità di controllo: clausole contrattuali ad hoc o disposizioni in accordi amministrativi tra autorità pubbliche. (Il testo del GDPR non menziona le «misure supplementari»: derivano dalla giurisprudenza e dalle raccomandazioni EDPB, vedi sotto.) **49 (deroghe):** in assenza di adeguatezza o garanzie (art. 45(3), art. 46 comprese le norme vincolanti d'impresa), un trasferimento o un insieme di trasferimenti può avvenire solo in una delle condizioni elencate (49(1), primo comma, elenco chiuso: (a) consenso esplicito dell'interessato dopo l'informazione sui rischi dovuti alla mancanza di adeguatezza e garanzie; (b) necessità per eseguire un contratto con l'interessato o misure precontrattuali su sua richiesta; (c) necessità per concludere o eseguire un contratto tra il titolare e un'altra persona a favore dell'interessato; (d) importanti motivi di interesse pubblico, riconosciuti dal diritto UE o dello Stato del titolare (49(4)); (e) accertare, esercitare o difendere un diritto in sede giudiziaria; (f) interessi vitali dell'interessato o di altri se non può consentire; (g) trasferimento da un registro pubblico, senza la totalità dei dati né intere categorie (49(2)); le lettere (a)-(c) e il secondo comma non valgono per le autorità pubbliche nell'esercizio dei pubblici poteri (49(3))); se non si può basare su 45 o 46 e nessuna deroga si applica, è ammesso solo se non ripetitivo, riguarda un numero limitato di interessati, è necessario per interessi legittimi cogenti del titolare non prevalenti sui diritti dell'interessato, e il titolare ha valutato tutte le circostanze (49(1), secondo comma; il titolare fornisce garanzie adeguate sulla base di tale valutazione, informa del trasferimento l'autorità di controllo e, oltre agli artt. 13-14, l'interessato del trasferimento e degli interessi legittimi perseguiti). In assenza di adeguatezza, il diritto dell'Unione o degli Stati membri può porre limiti al trasferimento di categorie specifiche di dati per importanti motivi di interesse pubblico (49(5)); il titolare o responsabile documenta la valutazione e le garanzie nel registro dell'art. 30 (49(6)). **48** (trasferimento o comunicazione non autorizzati dal diritto dell'Unione): sentenze di un giudice e decisioni di un'autorità amministrativa di un paese terzo che dispongono il trasferimento o la comunicazione di dati possono essere riconosciute o rese esecutive solo se basate su un accordo internazionale in vigore tra il paese richiedente e l'Unione o uno Stato membro (per esempio un trattato di mutua assistenza giudiziaria), fatti salvi gli altri presupposti del Cap. V. **47** (norme vincolanti d'impresa): l'autorità di controllo competente le approva con il meccanismo di coerenza (art. 63) se sono vincolanti per i membri del gruppo, conferiscono diritti azionabili agli interessati e hanno il contenuto minimo del par. 2; non le approfondisco (solo esistenza e oggetto). | ✔ art. 44, 45(1)-(9), 46(1)-(5), 47 (esistenza e oggetto), 48, 49(1)-(6) (GU L 119 del 4.5.2016, testo originale, Cellar; rettifica 2018 non confrontata). Il Data Privacy Framework è trattato nella scheda N-DPF. |
| 83 | Sanzioni amministrative. | ○ |

**Orientamenti:** EDPB, Linee guida 07/2020 sui concetti di titolare e responsabile (ruoli funzionali, determinati dalle attività concrete, non dal nome dato nel contratto). Fonte: https://www.edpb.europa.eu/system/files/documents/2023-10/EDPB_guidelines_202007_controllerprocessor_final_en.pdf · ◐ (aperto solo l'estratto; la versione 2.1 del 20.9.2022 è da fonte non ufficiale).

**Atti italiani:** d.lgs. 196/2003 modificato dal d.lgs. 101/2018 (vedi N-PRIV-IT). Autorità: Garante per la protezione dei dati personali.

**Collegamenti al progetto:** DX-11 (ruolo di responsabile, art. 28); DX-09 e DECISIONS §5 (art. 5(1)(e); art. 28(3)(g) citato per la restituzione o cancellazione a fine contratto: citazione corretta, la norma non fissa una durata); DX-13 e DX-19 (accesso del superadmin entro le istruzioni del titolare, art. 28); DA-B2-07 (trasferimenti extra-UE, Cap. V); DA-E1-02 e DA-C3-06 (minimizzazione); DA-A1-08; E1 §10 (art. 17); tutti i sottoprodotti che trattano dati delle agenzie (A1, A3, B1, B2, C1, C3, E1, E2, E3, F6, A5, A6).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- DX-11 (responsabile per i dati dei clienti delle agenzie) è coerente con l'art. 28. Gravya resta titolare dei dati dei propri utenti (superadmin, operatori, account delle agenzie), della fatturazione e dei propri siti (DA-A1-08 lo dice già).
- Il ruolo si decide sui fatti (EDPB 07/2020). Se Gravya decide finalità o mezzi propri (per esempio analisi dei tracking pixel per proprie finalità, addestramento o miglioramento di modelli con dati delle agenzie, profilazione per conto proprio), per quel trattamento rischia di diventare titolare o contitolare. Da chiarire nel contratto con le agenzie e nel DPA.
- I fornitori di modelli (LLM) sono sub-responsabili; servono l'autorizzazione del titolare, il contratto a catena e la verifica dei trasferimenti (DA-B2-07).
- **Identificativi pseudonimi in trace e payload (lotto 1).** Secondo il considerando 26 un identificativo pseudonimo (per esempio un ID interno del contatto o dell'utente) resta dato personale se, con informazioni aggiuntive in mano a Gravya, all'agenzia o a un terzo, la persona è identificabile con mezzi ragionevolmente prevedibili. Per i trace è quindi prudente trattarli come dati personali (con minimizzazione, conservazione limitata, cancellazione coerente con l'art. 17 e sicurezza dell'art. 32), a meno di una valutazione documentata che li dimostri anonimi (anche per l'agenzia che tiene la tabella di corrispondenza). La pseudonimizzazione è una misura di sicurezza e di *design* (artt. 25 e 32), non un'esenzione.
- **Art. 28(10).** Il rischio di riqualificazione come titolare riguarda i trattamenti in cui Gravya determina finalità e mezzi violando il regolamento (per esempio usare dati delle agenzie per finalità proprie senza istruzione o base giuridica). L'articolo non dice che una scelta tecnica sui mezzi, presa entro le istruzioni del titolare, renda Gravya titolare; per le decisioni di architettura e le istruzioni quadro nel DPA vedi EDPB 07/2020 (◐). Se Gravya è responsabile, le 72 ore dell'art. 33(1) non sono un suo termine: nei documenti un termine di notifica alle agenzie va fissato nel DPA (il GDPR dice solo «senza ingiustificato ritardo»), mentre le 24/72 ore di DX-10 derivano dalla NIS2.
- **Trace, LLM extra-UE e Cap. V (lotto 1).** Se un provider LLM fuori dallo SEE riceve payload con dati personali, il trasferimento richiede una base del Cap. V: decisione di adeguatezza (art. 45) per quel paese o settore, altrimenti garanzie adeguate (art. 46), e le deroghe dell'art. 49 sono l'ultima risorsa, non una base ordinaria per flussi sistematici. Quali decisioni di adeguatezza siano in vigore: per gli USA vedi la scheda N-DPF (lotto 2); le linee guida EDPB sulle misure supplementari sono nella sezione «Linee guida EDPB» (lotto 2).

---

### N-DPF — Decisione di adeguatezza UE-USA (Data Privacy Framework)

- **Estremi:** decisione di esecuzione (UE) 2023/1795 della Commissione del 10 luglio 2023, a norma del Reg. (UE) 2016/679, sul livello di protezione adeguato nel quadro UE-USA per la protezione dei dati personali; notificata con il numero C(2023)4745; GU L 231 del 20.9.2023, pag. 118. Destinatari: gli Stati membri (art. 4).
- **Fonte ufficiale:** testo letto dal Cellar dell'Ufficio delle pubblicazioni, versione italiana della GU: https://publications.europa.eu/resource/celex/32023D1795 (l'indirizzo ELI di EUR-Lex non è stato aperto).
- **Verificata il:** 2026-11-04 · **Stato:** ✔ per il testo della decisione (art. 1-4 e considerando 209-220 letti; GU, testo originale: non ho confrontato eventuali modifiche successive); ✔ per i fatti giudiziari e i riesami elencati sotto (fonti curia.europa.eu, EUR-Lex, commission.europa.eu, edpb.europa.eu); stato «in vigore oggi»: vedi sotto.

**Contenuto della norma (sintesi):**

| Articolo | Sintesi | Verifica |
|---|---|---|
| 1 | Ai fini dell'art. 45 GDPR, gli Stati Uniti garantiscono un livello di protezione adeguato **solo** per i dati personali trasferiti dall'Unione a **organizzazioni statunitensi che figurano nell'elenco degli aderenti al quadro (Data Privacy Framework List)**, tenuto e pubblicato dal Dipartimento del Commercio (allegato I, parte I, punto 3). Non copre trasferimenti verso organizzazioni statunitensi non incluse nell'elenco. | ✔ |
| 2 | Quando le autorità degli Stati membri esercitano i poteri dell'art. 58 GDPR sui trasferimenti coperti, ne informano senza ritardo la Commissione. | ✔ |
| 3 | La Commissione monitora in continuo il quadro statunitense (3(1)); Stati membri e Commissione si informano reciprocamente su carenze di vigilanza (3(2)) e su ingerenze eccessive delle autorità pubbliche USA (3(3)). **Riesame (3(4)):** un anno dopo la notifica della decisione agli Stati membri, poi con cadenza decisa in stretta consultazione con il comitato dell'art. 93 e con l'EDPB. Se l'adeguatezza non è più garantita la Commissione può sospendere, modificare o abrogare la decisione o limitarne l'ambito, secondo l'art. 45(5) GDPR (3(5)). | ✔ |
| 4 | Destinatari: gli Stati membri. Data di adozione: 10 luglio 2023 (formula di chiusura). La data di notifica non è nel testo letto. | ✔ |
| Considerando 211-214, 215-220 | Il primo riesame entro un anno; poi la frequenza dei riesami successivi dopo l'esito del primo; la Commissione presenta una relazione pubblica a Parlamento europeo e Consiglio. Ipotesi di avvio della procedura di sospensione o revoca: inadempienza delle organizzazioni aderenti non affrontata dagli organismi di vigilanza; mancato rispetto dei limiti all'accesso delle autorità USA; mancata risposta ai reclami degli interessati UE. Procedura d'urgenza dell'art. 93(3) GDPR possibile. | ✔ |

**Stato alla data del registro (2026-11-04), solo da fonti ufficiali:**

| Fatto | Fonte ufficiale | Verifica |
|---|---|---|
| Sentenza del Tribunale (Decima Sezione ampliata) del 3 settembre 2025, causa T-553/23, *Latombe c. Commissione*: ricorso di annullamento della decisione 2023/1795 respinto nel merito, senza decidere prima sulla ricevibilità; la causa T-553/23 R (sospensione) era stata respinta con ordinanza del 12.10.2023 per mancanza di urgenza. Il Tribunale ha valutato la decisione alla situazione di fatto e di diritto al momento dell'adozione (così la sintesi non ufficiale; il testo ufficiale del punto non è stato riletto). | EUR-Lex: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62023TJ0553 (titolo e sommario letti; motivi della sentenza non riletti per intero); InfoCuria per l'ordinanza | ◐ |
| **Impugnazione pendente:** causa **C-703/25 P**, *Latombe c. Commissione*, impugnazione proposta il 31 ottobre 2025 contro la sentenza T-553/23 (ECLI:EU:T:2025:831); lingua della causa: francese; parti: Latombe, Commissione, Irlanda, Stati Uniti. Quattro motivi: (1) indipendenza e imparzialità del Data Protection Review Court (DPRC) e regole di nomina e revoca dei giudici; (2) il DPRC non è un tribunale «precostituito per legge» (istituito con atto del Procuratore generale); (3) la raccolta di massa senza autorizzazione preventiva di un'autorità indipendente; (4) il potere del Presidente USA di aggiornare gli obiettivi della raccolta di massa (decreto presidenziale 14086). Chiede l'annullamento della decisione 2023/1795 o, in subordine, il rinvio al Tribunale. | Avviso dell'impugnazione, InfoCuria (docid 307389) e GUUE C/2025/6610 del 22.12.2025: https://eur-lex.europa.eu/eli/C/2025/6610/oj/eng | ✔ per l'esistenza, i motivi e la data; ◐ per «ancora pendente»: la scheda InfoCuria vista in ricerca (aggiornata al 4.6.2026) elencava solo il ricorso, ma non ho potuto aprirla; **nessuna sentenza né conclusioni dell'avvocato generale viste** |
| **Primo riesame periodico:** relazione della Commissione COM(2024) 451 final del 9 ottobre 2024 al Parlamento europeo e al Consiglio. Conclude che le autorità USA hanno messo in atto le strutture e le procedure necessarie al funzionamento effettivo del quadro; la Commissione consulterà EDPB e comitato dell'art. 93 sulla periodicità dei riesami futuri (art. 3(4) della decisione). La cadenza di tre anni (prossimo riesame circa 2027) la dice solo la stampa specializzata: **fonte non ufficiale, non verificata**. | EUR-Lex: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:52024DC0451 ; Commissione: https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en | ✔ per esistenza, data e conclusione (estratti ufficiali); ○ per la periodicità successiva |
| **Relazione EDPB** sul primo riesame, 4 novembre 2024. Lettera dell'EDPB alla Commissione sulla sentenza della Corte suprema USA *Trump v. Slaughter*, 31 luglio 2026 (titolo e data letti sul sito EDPB; **contenuto non letto**). Altre lettere EDPB alla Commissione sul tema adeguatezza: 21.4.2026 (requisiti di registrazione delle INGO) e 12.3.2026 (condizioni di ingresso negli USA per cittadini SEE) (solo titoli). | https://www.edpb.europa.eu/documents/reports-statements-and-letters/edpb-report-on-the-first-review-of-the-european-commission_en ; https://www.edpb.europa.eu/documents/edpb-correspondence/edpb-letter-to-the-european-commission-on-us-supreme-court-judgment_en | ✔ per esistenza e titoli; ○ per il contenuto |
| **Revoca, sospensione o modifica della decisione:** non ho trovato su fonti ufficiali alcun atto della Commissione che revochi, sospenda o modifichi la decisione 2023/1795, né un atto della Corte di giustizia che la annulli. Ma non ho verificato il consolidato EUR-Lex né un elenco ufficiale aggiornato: l'assenza di un atto «visto» non prova che non esista. | — | **non_verificato** («in vigore oggi» non è dimostrato positivamente) |
| Notizie su un nuovo ricorso di noyb e sugli effetti di *Trump v. Slaughter* sull'indipendenza della FTC compaiono solo in articoli di siti non ufficiali (secureprivacy.ai e simili, luglio 2026): non le riporto come fatti. | — | fonte non ufficiale: non verificato |

**Collegamenti al progetto:** DA-B2-07 (trasferimenti extra-UE verso provider LLM); N-GDPR Cap. V (artt. 44-49); tutti i sottoprodotti che inviano dati personali a provider con sede o sub-processori negli USA (B2, C3, E1).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- Un trasferimento verso un provider LLM statunitense può appoggiarsi alla decisione 2023/1795 solo se quel provider è **nell'elenco DPF per i dati del tipo trasferito** (la decisione copre solo le organizzazioni elencate, art. 1): va verificato l'elenco del Dipartimento del Commercio (non consultato in questo registro) e va controllato che l'adesione sia attiva e copra i dati in questione (per esempio dati non HR). Un provider non elencato richiede garanzie dell'art. 46 (per esempio clausole tipo) con valutazione del trasferimento.
- La decisione è revocabile con effetto non retroattivo (art. 45(5) GDPR) e l'impugnazione C-703/25 P è pendente: prudente prevedere un meccanismo alternativo (clausole tipo) già nel DPA e un'architettura che consenta di cambiare provider o regione (opzione di residenza UE, pseudonimizzazione, minimizzazione del payload). Non è un obbligo di legge: è una scelta di gestione del rischio.
- Gravya come responsabile trasferisce su istruzione documentata del titolare (art. 28(3)(a)): il DPA con le agenzie deve indicare quali trasferimenti e su quale base.

---

### N-EDPB — Linee guida e raccomandazioni EDPB su pseudonimizzazione, art. 25 e trasferimenti (lotto 2)

Atti non vincolanti (soft law) del Comitato europeo per la protezione dei dati: indicano come le autorità di controllo leggono il GDPR, non sono norme. Letti solo sulle pagine e sui PDF EDPB mostrati dalla ricerca (estratti), non per intero: ◐.

| Documento | Estremi, stato, link | Punti utili per log/trace, minimizzazione, trasferimenti verso provider LLM (sintesi mia) | Verifica |
|---|---|---|---|
| **Linee guida 01/2025 sulla pseudonimizzazione** | Adottate il 16 gennaio 2025 come **versione per consultazione pubblica** (v1); consultazione 17.1-14.3.2025 (la notizia EDPB parlava di scadenza al 28.2.2025, la pagina della consultazione indica il 14.3.2025). **Nessuna versione definitiva vista** sulla pagina EDPB aperta (mostra solo la v1 e un riepilogo «at a glance»): stato = bozza in consultazione, definitiva non trovata. Pagina: https://www.edpb.europa.eu/public-consultations/guidelines-012025-on-pseudonymisation_en ; testo v1: https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf | (1) I dati pseudonimizzati che si possono attribuire a una persona con informazioni aggiuntive restano dati personali (rinvio al considerando 26): vale anche se dati e informazioni aggiuntive non sono nelle stesse mani. (2) La pseudonimizzazione serve come misura di *data protection by design* (art. 25) e di sicurezza (art. 32); non c'è un obbligo generale di usarla; la sua efficacia dipende dal «dominio di pseudonimizzazione» e dall'isolamento delle informazioni aggiuntive. (3) Prima di trasmettere dati pseudonimizzati, valutare secondo la minimizzazione se servono davvero i pseudonimi (servono per riunire record nel tempo o per un canale di ritorno; altrimenti no); inoltre il responsabile che inverte la pseudonimizzazione contro l'istruzione del titolare agisce illecitamente (art. 29). Il documento tratta anche la pseudonimizzazione come misura supplementare nei trasferimenti. | ◐ (estratti ufficiali EDPB: pagina consultazione letta; PDF visto solo in estratti della ricerca) |
| **Linee guida 02/2026 sull'anonimizzazione** (segnalate perché collegate: non richieste) | Adottate il 7 luglio 2026 come versione 1.0 per consultazione, **consultazione fino al 30 ottobre 2026** (già chiusa alla data del registro); la notizia EDPB dice che tengono conto della sentenza della Corte di giustizia C-413/23 P, *EDPS c. SRB*, del 4 settembre 2025. Pagina: https://www.edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en | Non ho letto il testo. Dal titolo, dalla data e dalla notizia EDPB (letta in estratto): rilevante per decidere se i trace siano «anonimi». Che l'anonimato sia valutato «dalla prospettiva di ciascun soggetto» e che il responsabile non sfugga agli obblighi sono sintesi di studi legali: **fonte non ufficiale, non verificato**. | ◐ solo esistenza, data, stato |
| **Linee guida 4/2019 sull'art. 25 (protezione dei dati fin dalla progettazione e per impostazione predefinita)** | **Versione 2.0 adottata il 20 ottobre 2020** dopo consultazione pubblica (v1.0 del 13 novembre 2019). Adottate in via definitiva. Pagina: https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-42019-article-25-data-protection-design-and_en ; PDF: https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf | (1) L'obbligo dell'art. 25 è del titolare e si estende ai trattamenti svolti tramite responsabili, che il titolare deve verificare con regolarità; responsabili e produttori non sono destinatari diretti ma le linee guida suggeriscono loro di usarle per costruire prodotti adeguati (rilevante per Gravya come fornitore di una piattaforma usata dalle agenzie). (2) L'obbligo di mantenere, riesaminare e aggiornare vale anche per i sistemi preesistenti. (3) Gli elementi chiave e gli esempi sono indicativi, non esaustivi né vincolanti; il titolare valuta caso per caso. | ◐ (estratti del PDF ufficiale EDPB mostrati dalla ricerca; versione e data ✔ dal frontespizio) |
| **Raccomandazioni 01/2020 sulle misure che integrano gli strumenti di trasferimento** | **Versione 2.0, versione finale, 18 giugno 2021** (versione per consultazione: novembre 2020). Pagina: https://www.edpb.europa.eu/documents/recommendation/recommendations-012020-on-measures-that-supplement-transfer-tools-to_en ; PDF: https://www.edpb.europa.eu/system/files/documents/2021-06/edpb_recommendations_202001vo.2.0_supplementarymeasurestransferstools_en.pdf | (1) Percorso in sei passi per l'esportatore (mappare i trasferimenti, individuare lo strumento, valutare l'efficacia dello strumento dell'art. 46 alla luce di legge e prassi del paese terzo, adottare misure supplementari, procedure formali, riesaminare nel tempo); la valutazione va documentata e la responsabilità primaria è dell'esportatore. (2) Già al primo passo si deve verificare che i dati trasferiti siano adeguati, pertinenti e limitati a quanto necessario (minimizzazione del payload verso il provider). (3) Le deroghe dell'art. 49 sono eccezionali e non possono diventare la regola. Le raccomandazioni riguardano le garanzie dell'art. 46; per un'adeguatezza vedi N-DPF. | ✔ per estremi, data e stato (pagina EDPB letta); ◐ per i punti (estratti del PDF) |

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- Le linee guida 01/2025 sono una bozza: citarle come «versione per consultazione» e non come posizione definitiva dell'EDPB. Confermano la prudenza già scritta nel registro (ID pseudonimi in trace = dati personali). La sentenza C-413/23 P (4.9.2025) e le linee guida 02/2026 sull'anonimizzazione, non lette qui, possono cambiare il modo di valutare l'anonimato per un destinatario che non può reidentificare: prima di dichiarare «anonimi» i trace verso un provider LLM serve una valutazione documentata con il DPO.
- Le raccomandazioni 01/2020 descrivono come motivare e documentare un trasferimento basato sull'art. 46 (per esempio clausole tipo) verso un provider fuori dallo SEE; non sono richieste per un trasferimento coperto da adeguatezza (DPF), dove il provider sia nell'elenco.

---

### N-PRIV-IT — Codice in materia di protezione dei dati personali (artt. 122 e 130)

- **Estremi:** decreto legislativo 30 giugno 2003, n. 196, modificato dal d.lgs. 28 maggio 2012, n. 69 (recepimento della dir. 2009/136/CE) e dal d.lgs. 10 agosto 2018, n. 101.
- **Fonte ufficiale:** Normattiva (testo vigente): https://www.normattiva.it/ — l'indirizzo esatto dell'atto non l'ho aperto; art. 122 letto nel testo citato dalle linee guida del Garante; art. 130 letto su copie non ufficiali.
- **Verificata il:** 2026-11-04 · **Stato:** ◐.

**Contenuto della norma (sintesi):**

| Articolo | Sintesi | Verifica |
|---|---|---|
| 122, c. 1 | Archiviare informazioni nel terminale dell'utente o accedere a quelle già archiviate è consentito solo con il consenso dell'utente, informato con modalità semplificate. Non serve per l'archiviazione tecnica strettamente necessaria a trasmettere una comunicazione o a erogare il servizio richiesto dall'utente. | ✔ (testo riportato nelle linee guida del Garante 2021) |
| 122, c. 2-bis | Fuori dal c. 1 è vietato usare una rete di comunicazione elettronica per accedere a informazioni nel terminale, archiviarne o monitorare le operazioni dell'utente. | ✔ (idem) |
| 130, c. 1-2 | Per inviare pubblicità o vendita diretta con sistemi automatizzati senza operatore, email, fax, SMS, MMS o messaggi «di altro tipo» serve il consenso del contraente o utente. | ◐ |
| 130, c. 3, 3-bis | Per i mezzi diversi (telefono con operatore, posta cartacea) si applicano le regole generali e, per telefono e posta cartacea, il Registro pubblico delle opposizioni (vedi N-RPO). | ◐ |
| 130, c. 4 | «Soft spam»: per vendere propri prodotti o servizi analoghi si può usare, senza consenso, l'indirizzo email fornito dall'interessato in occasione della vendita, se l'interessato è informato e non rifiuta, all'inizio e in ogni comunicazione. | ◐ |
| 130, c. 5 | È sempre vietato inviare comunicazioni promozionali camuffando l'identità del mittente, violando l'art. 8 d.lgs. 70/2003, senza un recapito idoneo per esercitare i diritti degli artt. 15-22 GDPR, o invitando a visitare siti che violano lo stesso art. 8. | ◐ |
| 130, c. 6 | In caso di violazioni reiterate il Garante può prescrivere ai fornitori di servizi di comunicazione elettronica filtri o altre misure sugli indirizzi di invio. | ◐ |

**Provvedimenti delle autorità:** Garante, linee guida cookie (N-GAR-COOKIE) e tracking pixel (N-GAR-PIXEL). Le «Linee guida in materia di attività promozionale e contrasto allo spam» del Garante (2013) non le ho aperte: **non_verificata**. Un'ordinanza della Cassazione (n. 15881/2025) che limiterebbe il soft spam a rapporti di vendita effettivi e onerosi: visto solo su fonti non ufficiali, **non_verificata**.

**Collegamenti al progetto:** nessun documento dell'ondata 1 cita l'art. 130, l'art. 122 o il d.lgs. 70/2003 (vedi cambiamenti rilevanti). Sottoprodotti interessati: D1-D4 (connettori di canale), C3 (approvazioni prima dell'invio), A3 (policy), B2 (tool di invio).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- Il consenso e la prova del consenso spettano di regola all'agenzia (mittente e titolare). Gravya, come piattaforma che invia per conto loro, dovrebbe poter rifiutare o bloccare un invio senza base giuridica registrata, senza identificazione del mittente o senza meccanismo di opposizione. Se questo è un requisito di prodotto va deciso dall'utente (nessuna DX lo copre oggi).
- Il soft spam vale solo per l'email e solo verso propri clienti; non per SMS o altri canali.

---

### N-EPRIVACY — Direttiva ePrivacy

- **Estremi:** Direttiva 2002/58/CE del 12 luglio 2002, GU L 201 del 31.7.2002, modificata dalla dir. 2009/136/CE del 25 novembre 2009 (testo consolidato del 19.12.2009).
- **Fonte ufficiale:** https://eur-lex.europa.eu/eli/dir/2002/58/oj/eng (consolidato: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02002L0058-20091219)
- **Verificata il:** 2026-11-04 · **Stato:** ◐.

**Contenuto della norma (sintesi):**
- **Art. 13(1):** chiamate automatiche, fax ed email per marketing diretto solo con il consenso preventivo dell'interessato. ◐ (testo su copia di EUR-Lex)
- **Art. 13(2):** eccezione per i clienti: stessa impresa, propri prodotti simili, possibilità gratuita e agevole di opporsi. ○
- **Art. 13(3):** per le altre comunicazioni di marketing gli Stati scelgono tra consenso (opt-in) e diritto di opporsi (opt-out), gratuiti. ✔ (letto nel consolidato EUR-Lex)
- **Art. 13(4):** è sempre vietato inviare email di marketing nascondendo l'identità del mittente per conto del quale si scrive o senza un indirizzo valido per chiedere di smettere. ◐ (testo su copia di EUR-Lex)
- **Art. 5(3):** consenso per archiviare o accedere a informazioni nel terminale dell'utente, salvo l'esenzione tecnica. ○ (recepito dall'art. 122 Codice, letto)
- Il considerando 41 prevede che l'uso di contatti elettronici di clienti per prodotti simili spetti solo alla stessa impresa che li ha ottenuti. ✔ (considerando letto sulla pagina EUR-Lex)

**Atti italiani:** artt. 122 e 130 del Codice (N-PRIV-IT).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** il soft spam non si trasferisce da un'agenzia a un'altra né a Gravya: se Gravya o le agenzie riusano contatti raccolti da altri, serve il consenso. Il regolamento ePrivacy (2017) è stato ritirato nel 2025 secondo fonti non ufficiali: **non_verificato**. Le modifiche proposte alla direttiva sono in N-OMNIBUS-DATI.

---

### N-RPO — Registro pubblico delle opposizioni

- **Estremi:** art. 130, commi 3-bis e seguenti, Codice privacy; legge 11 gennaio 2018, n. 5, art. 1; DPR 27 gennaio 2022, n. 26 (regolamento sul registro esteso a tutte le numerazioni nazionali fisse e mobili); DPR 178/2010 e DPR 149/2018 (versioni precedenti, da fonte non ufficiale).
- **Fonti ufficiali:** https://registrodelleopposizioni.it/ (sito del servizio, che ospita il testo del DPR 26/2022) · https://www.mimit.gov.it/it/comunicazioni/telefonia/registro-pubblico-delle-opposizioni
- **Verificata il:** 2026-11-04 · **Stato:** ◐ (estratti dei siti ufficiali).

**Contenuto della norma (sintesi):**
- Il registro vale per le telefonate (con operatore o automatizzate, per l'art. 1 l. 5/2018) e per la posta cartacea con finalità pubblicitaria o di ricerche di mercato. ✔ (DPR 26/2022, art. 2, letto in estratto)
- Chi si iscrive non può più essere contattato dall'operatore di telemarketing, salvo consenso dato dopo l'iscrizione o contratto in essere o cessato da non più di 30 giorni. ✔ (pagina MIMIT)
- L'operatore deve registrarsi e far verificare le liste dei numeri prima delle campagne; le liste restituite valgono 15 giorni (telemarketing) o 30 giorni (marketing postale). ✔ (pagina MIMIT). L'obbligo di consultazione mensile e prima di ogni campagna (art. 8 DPR 26/2022) l'ho letto solo su una copia non ufficiale: ◐.
- Per il servizio, «cittadino» include anche persone giuridiche, enti e associazioni titolari di un contratto telefonico. ✔ (sito del registro)
- L'iscrizione non riguarda email e SMS: per questi canali vale l'art. 130, c. 1-2, Codice. ◐

**Collegamenti al progetto:** nessuno oggi. Interessa D1-D4 solo se Gravya supporta campagne telefoniche o postali.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** il registro non si applica a email e SMS. Diventa rilevante se Gravya offre o abilita il telemarketing o la posta cartacea per le agenzie: chi fa la consultazione (l'operatore, cioè l'agenzia titolare) e come Gravya lo supporta sono scelte da decidere.

---

### N-GAR-COOKIE — Linee guida del Garante su cookie e altri strumenti di tracciamento

- **Estremi:** provvedimento n. 231 del 10 giugno 2021, doc. web 9677876, GU n. 163 del 9 luglio 2021. Termine di adeguamento: 6 mesi dalla pubblicazione in GU (già trascorso).
- **Fonte ufficiale:** https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9677876
- **Verificata il:** 2026-11-04 · **Stato:** ✔ (testo letto sul sito del Garante).

**Contenuto (sintesi):**
- Cookie e altri strumenti (anche «passivi», come il fingerprinting) per finalità non tecniche richiedono il consenso preventivo ai sensi dell'art. 122; il legittimo interesse non può giustificarli.
- Per impostazione predefinita, al primo accesso non deve essere installato nulla di diverso dai cookie tecnici. Il banner deve consentire di proseguire senza consenso (per esempio chiudendolo) con evidenza pari a quella dell'accettazione.
- Lo scroll da solo non è consenso. Il cookie wall è illecito, salvo che si offra un accesso equivalente senza consenso (verifica caso per caso).
- La scelta dell'utente va registrata e non richiesta di nuovo prima che passino almeno 6 mesi, salvo mutamento significativo delle condizioni o impossibilità di sapere se il cookie è già memorizzato.
- I cookie analytics sono equiparati ai tecnici solo se minimizzati (per esempio IP mascherato) e limitati a statistiche aggregate su un solo sito o app.
- L'informativa deve dichiarare i criteri con cui il titolare classifica i propri cookie.

**Collegamenti al progetto:** nessuno oggi (nessun documento della v2 tratta sito o app web con cookie).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** vale per il sito e l'applicazione web di Gravya; per i moduli, le landing page o gli script che Gravya mette a disposizione delle agenzie vanno chiariti ruoli (titolare: agenzia o Gravya) e chi gestisce il consenso.

---

### N-GAR-PIXEL — Linee guida del Garante sui tracking pixel nelle email

- **Estremi:** provvedimento n. 284 del 17 aprile 2026, doc. web 10241943, GU Serie Generale n. 98 del 29 aprile 2026. Termine: 6 mesi dalla pubblicazione in GU, cioè 29 ottobre 2026 (data calcolata, vedi calendario).
- **Fonti ufficiali:** https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10241943 · comunicato https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10241977 · pagina tematica https://www.garanteprivacy.it/temi/tracking-pixel · vademecum https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/10303585
- **Verificata il:** 2026-11-04 · **Stato:** ◐ (estratti delle pagine del Garante; il testo integrale del provvedimento non l'ho letto per intero).

**Contenuto (sintesi):**
- I tracking pixel nelle email rientrano nell'art. 122 Codice: l'inserimento del pixel è archiviazione nel terminale e la lettura è accesso a informazioni già archiviate. In generale sono vietati salvo che ricorra una condizione prevista, di norma il consenso preventivo. ✔ (pagina tematica)
- Il consenso serve, per esempio, quando il pixel misura il comportamento del singolo destinatario per adattare comunicazioni o frequenza, o per creare profili commerciali. Può non servire per statistiche aggregate, deliverability e contrasto allo spam, nei limiti delle deroghe. ✔ (pagina tematica)
- Il consenso ai pixel può essere compreso nel consenso alle comunicazioni promozionali se chiesto in modo neutro. La revoca deve essere facile e anche granulare: il destinatario può scegliere di continuare a ricevere le email senza pixel. Il rifiuto non deve limitare il servizio. ✔
- Le linee guida si rivolgono, tra gli altri, ai «gestori di piattaforme per l'invio massivo di email». ✔ (comunicato)
- Il Garante ha chiesto privacy by design e by default e di individuare con cura i ruoli (mittente, fornitore del servizio di invio, fornitore della tecnologia). ◐
- La verifica dell'applicazione rientra nell'attività ispettiva del Garante per il secondo semestre 2026. ✔ (vademecum, estratto)

**Collegamenti al progetto:** nessuno oggi (vedi cambiamenti rilevanti).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** come piattaforma che invia email per conto delle agenzie, Gravya è un destinatario diretto delle linee guida. Aperture, click tracking e report di campagna vanno progettati con consenso registrato, revoca granulare e minimizzazione. Il termine è già scaduto.

---

### N-ECOMM — Commercio elettronico (Dir. 2000/31/CE, d.lgs. 70/2003)

- **Estremi:** Direttiva 2000/31/CE dell'8 giugno 2000 (GU L 178 del 17.7.2000) e decreto legislativo 9 aprile 2003, n. 70 (GU n. 87 del 14 aprile 2003, S.O. n. 61). Per la responsabilità degli intermediari la direttiva è stata in parte sostituita dal DSA (vedi N-DSA).
- **Fonti:** testo del d.lgs. 70/2003 sul sito del Parlamento https://www.parlamento.it/parlam/leggi/deleghe/03070dl.htm (lo cito come testo di legge pubblicato; non è Normattiva). Direttiva: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32000L0031 — **non aperta**.
- **Verificata il:** 2026-11-04 · **Stato:** ◐ per il d.lgs. 70/2003; non_verificata per la direttiva.

**Contenuto (sintesi):**
- **Art. 8 d.lgs. 70/2003:** le comunicazioni commerciali che sono un servizio della società dell'informazione devono indicare, sin dal primo invio e in modo chiaro, che sono comunicazioni commerciali, la persona per conto della quale sono fatte, e le condizioni di offerte e concorsi. ✔ (testo sul sito del Parlamento)
- **Art. 9:** le comunicazioni commerciali non sollecitate per posta elettronica devono essere identificabili come tali fin dalla ricezione e indicare che il destinatario può opporsi in futuro; la prova che la comunicazione era sollecitata spetta al prestatore. ✔

**Collegamenti al progetto:** nessuno oggi. Il d.lgs. 70/2003 art. 8 è richiamato dall'art. 130, c. 5, del Codice.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** l'identificazione «per conto di chi» è un requisito dei messaggi inviati dalla piattaforma per le agenzie: la piattaforma dovrebbe garantire che mittente, natura commerciale e opposizione siano sempre presenti. Il prestatore tenuto a provare il consenso è l'agenzia; Gravya dovrebbe conservare la prova.

---

## 4. Cybersicurezza

### N-NIS2 — Direttiva NIS2

- **Estremi:** Direttiva (UE) 2022/2555 del 14 dicembre 2022, GU L 333 del 27.12.2022. Recepimento entro il 17 ottobre 2024; si applica dal 18 ottobre 2024.
- **Fonte ufficiale:** https://eur-lex.europa.eu/eli/dir/2022/2555/oj/eng
- **Verificata il:** 2026-11-04 · **Stato:** ◐ (estratti EUR-Lex e scheda di sintesi EUR-Lex).

**Contenuto (sintesi):**
- **Art. 2:** si applica a soggetti pubblici o privati di tipo indicato negli Allegati I o II che sono almeno medie imprese. ✔ (estratto). I settori dell'Allegato I includono le infrastrutture digitali e la gestione dei servizi ICT B2B; non ho riletto l'allegato (○).
- **Art. 21:** misure di gestione del rischio proporzionate, con approccio multirischio. ○ (articolo non riletto; richiamato in estratti)
- **Art. 23:** obbligo di notificare gli incidenti significativi al CSIRT o all'autorità. ◐ (richiamato negli estratti; i termini 24 ore / 72 ore / relazione finale entro un mese li ho letti solo su fonti italiane, vedi N-NIS2-IT).
- **Art. 34 (sanzioni, numero ○):** per violazioni degli artt. 21 e 23 i soggetti essenziali rischiano almeno fino a 10 milioni di euro o il 2% del fatturato mondiale; i soggetti importanti almeno fino a 7 milioni o l'1,4%. ✔ (testo letto, numero dell'articolo non riletto)
- Le autorità informano il Garante quando una violazione di artt. 21 o 23 può comportare un data breach da notificare ai sensi del GDPR. ✔ (estratto)

**Collegamenti al progetto:** DX-10 (notifica incidenti 24/72 ore a carico di A5); DX-22(a) (valori con vincolo di legge); PV-01; documenti con «NIS2 (art. 21)» in §7 (A3, C1, C3 e altri); DECISIONS §5 (NIS2 art. 21 e 23). Le citazioni degli artt. 21 e 23 sono coerenti con la norma.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- Un SaaS può rientrare tra i «fornitori di servizi di cloud computing» (infrastrutture digitali) se è un servizio che consente l'amministrazione su richiesta di un pool scalabile di risorse condivisibili. La definizione dell'art. 2(bbb) d.lgs. 138/2024 l'ho letta solo su una copia non ufficiale ◐. Se il SaaS di Gravya sia o no un «servizio di cloud computing» e se Gravya superi la soglia di dimensione sono **questioni aperte**; DX-10 oggi le presuppone risolte. Serve anche stabilire se è «soggetto importante» o «essenziale».
- Anche se Gravya non fosse soggetto NIS, le agenzie clienti potrebbero esserlo; allora Gravya può comparire come fornitore (vedi ACN, elenco dei fornitori rilevanti).

---

### N-NIS2-IT — Recepimento italiano e atti dell'ACN

- **Atto:** decreto legislativo 4 settembre 2024, n. 138, GU Serie Generale n. 230 del 1° ottobre 2024; in vigore dal 16 ottobre 2024 e applicato dal 18 ottobre 2024 (date da fonti non ufficiali; la pagina ufficiale ACN conferma il recepimento con d.lgs. 138 del 4 settembre 2024).
- **Fonti ufficiali:** Normattiva https://www.normattiva.it/eli/id/2024/10/01/24G00155/CONSOLIDATED (trovato nella ricerca, non letto per intero) · ACN https://www.acn.gov.it/portale/en/nis/la-normativa · https://www.acn.gov.it/portale/en/nis/modalita-specifiche-base · https://www.acn.gov.it/portale/en/faq/nis/misure-di-sicurezza-e-notifica-di-incidenti (tutte non apribili, solo estratti).
- **Autorità:** ACN (Autorità nazionale competente NIS e punto di contatto unico); CSIRT Italia riceve le notifiche.
- **Verificata il:** 2026-11-04 · **Stato:** ◐.

**Articoli del d.lgs. 138/2024 rilevanti (sintesi):**

| Articolo | Sintesi | Verifica |
|---|---|---|
| 3, 6 | Ambito di applicazione per Allegati e dimensione; distinzione tra soggetti essenziali e importanti. | ◐ |
| 7 | Registrazione e aggiornamento annuale sulla piattaforma ACN (dal 1° gennaio al 28 febbraio di ogni anno). | ◐ (copia non ufficiale) |
| 23 | Gli organi di amministrazione approvano le misure, ne sovrintendono l'attuazione, si formano e rispondono delle violazioni. | ◐ (fonte secondaria) |
| 24, 25 | Misure di sicurezza e notifica degli incidenti significativi; modalità e tempi demandati all'ACN (artt. 30, 31, 32). | ◐ |
| 30 | Elenco e categorizzazione di attività e servizi. | ◐ |
| 42 | Fase di prima applicazione fino al 31 dicembre 2025: 9 mesi per la notifica, 18 mesi per le misure, dalla comunicazione di inserimento in elenco. | ◐ |

**Atti dell'ACN (determinazioni del Direttore generale):**

| Atto | Contenuto | Verifica |
|---|---|---|
| Determinazione 379907 del 19.12.2025, applicabile dal 15.1.2026 (sostituisce la 164179 del 14.4.2025) | Specifiche di base: misure di sicurezza (Allegato 1 per i soggetti importanti, Allegato 2 per gli essenziali) e incidenti significativi di base da notificare (Allegato 3 importanti, Allegato 4 essenziali). Termine delle misure: 18 mesi dalla comunicazione di inserimento nell'elenco, per chi è stato inserito nel 2025 (ottobre 2026 per la prima coorte). Pre-notifica entro 24 ore da quando il soggetto ha gli elementi oggettivi. | ◐ (FAQ e pagina ACN, estratti). Il numero di misure (37/87 e 43/116) è da fonte non ufficiale. |
| Determinazione 127434/2026 del 13.4.2026, applicabile dal 30.4.2026 | Termini per i soggetti inseriti per la prima volta nel 2026: notifica degli incidenti di base dal 1° gennaio 2027; misure di base entro il 31 luglio 2027. | ◐ (news e FAQ ACN) |
| Determinazione 127437/2026 | Piattaforma digitale e nuovo elenco dei fornitori rilevanti (art. 18). | ◐ (news ACN) |
| Determinazione 379887/2025 | Portale ACN e servizi NIS, applicabile dal 31.12.2025. | fonte non ufficiale: non verificato |
| Determinazioni 155238/2026 (modello di categorizzazione) e 314287/2026 (piattaforma, applicabile dal 25.10.2026) | Non le ho trovate su fonte ufficiale. | **non_verificata** |
| Linee guida NIS «Specifiche di base» e «Definizione del processo di gestione degli incidenti» | Esistono (pagina ACN). | ◐ |

La relazione finale entro un mese e la notifica entro 72 ore le ho viste solo in fonti non ufficiali: ◐/non verificato sulla fonte ACN.

**Collegamenti al progetto:** DX-10; A5; DX-22(a) e le soglie «vincolo normativo» (vanno agganciate agli Allegati 3 e 4 della Det. 379907/2025, che definiscono quando un incidente è «significativo di base»); A3, B1, B2, C1, C3, E2 (segnali ad A5).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** se Gravya è un soggetto NIS deve essere in elenco ACN, aver svolto la registrazione annuale e rispettare i termini della propria coorte; il termine delle misure (18 mesi o 31 luglio 2027) dipende dalla data di inserimento. Nessun documento del progetto indica se e quando Gravya si è registrata.

---

## 5. Intelligenza artificiale

### N-AIACT — Regolamento sull'intelligenza artificiale

- **Estremi:** Regolamento (UE) 2024/1689 del 13 giugno 2024, GU L 2024/1689 del 12.7.2024; in vigore dal 1° agosto 2024 ✔ (considerando 1 del Reg. 2026/1744).
- **Fonti ufficiali:** testo originale https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng · consolidato al 27.7.2026 https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng (si apriva solo in testata) · Esploratore ufficiale della Commissione, basato sul consolidato: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50
- **Verificata il:** 2026-11-04 · **Stato:** ✔ per gli articoli segnati; ○ per gli altri.

**Articoli rilevanti per Gravya (sintesi):**

| Articolo | Sintesi | Verifica |
|---|---|---|
| 4 | **Come riscritto dall'Omnibus:** fornitori e deployer adottano misure per sostenere lo sviluppo dell'alfabetizzazione in materia di IA del proprio personale e di chi opera per loro; non devono garantire un livello specifico a ogni singola persona. | ✔ (testo Reg. 2026/1744 art. 1(5)) |
| 5 | Pratiche vietate. Dal 2.12.2026 si aggiungono i divieti di sistemi che generano o manipolano immagini, video, audio realistici di parti intime di una persona identificabile senza consenso o materiale pedopornografico; per i fornitori valgono gli «ragionevoli e adeguati» presìdi tecnici (par. 1a). I divieti già in vigore dell'art. 5(1)(a)-(h) (tra cui le tecniche manipolative) non li ho riletti. | ✔ per (ba), (bb), 1a, 1b; ○ per gli altri |
| 6 | Un sistema è ad alto rischio se rientra nell'Allegato I (componente di sicurezza di prodotti) o nell'Allegato III. L'Omnibus precisa che i sistemi usati solo per assistenza all'utente, ottimizzazione, efficienza o automazione non sono «componenti di sicurezza» (par. 1a). Un sistema dell'Allegato III che esegue profilazione di persone fisiche è sempre ad alto rischio (par. 3). Il fornitore che ritiene un sistema dell'Allegato III non ad alto rischio documenta la valutazione prima dell'immissione sul mercato (par. 4). | ✔ |
| 12, 14, 19, 26 | Requisiti dei sistemi ad alto rischio (registrazione, sorveglianza umana, conservazione dei log, obblighi dei deployer). Applicabili solo ai sistemi ad alto rischio, dal 2.12.2027 (Allegato III) e dal 2.8.2028 (Allegato I). | ○ per i contenuti; ✔ per le date |
| 25 | Responsabilità lungo la catena del valore. Come modificato: il fornitore iniziale coopera con il nuovo fornitore; fornitore di un sistema ad alto rischio e terzo che fornisce modello o componenti specificano per iscritto le informazioni e l'assistenza necessarie. | ✔ (testo Reg. 2026/1744 art. 1(12)) |
| 50 | **Trasparenza.** (1) I fornitori progettano i sistemi che interagiscono direttamente con persone in modo che queste siano informate che parlano con un'IA, salvo ovvietà. (2) I fornitori di sistemi, anche GPAI, che generano audio, immagini, video **o testo** sintetici garantiscono che gli output siano marcati in formato leggibile da macchina e rilevabili; la soluzione deve essere efficace, interoperabile, robusta e affidabile per quanto tecnicamente possibile. L'obbligo non vale nella misura in cui il sistema svolge una funzione assistiva di editing standard o non altera in modo sostanziale i dati o la semantica forniti dal deployer. (3) Riconoscimento delle emozioni e categorizzazione biometrica. (4) I deployer di sistemi che generano o manipolano immagini, audio o video costituenti deep fake lo dichiarano; i deployer di sistemi che generano o manipolano testo pubblicato per informare il pubblico su questioni di interesse pubblico lo dichiarano, salvo revisione umana o controllo editoriale con responsabilità editoriale di una persona. (5) Informazioni chiare e distinguibili al più tardi alla prima interazione o esposizione, conformi ai requisiti di accessibilità. (7) La Commissione facilita codici di buone pratiche e ne valuta l'adeguatezza; se inadeguato può adottare un atto di esecuzione. | ✔ (testo consolidato letto sul portale ufficiale della Commissione) |
| 51-55 | Modelli GPAI: i fornitori del modello documentano e mettono a disposizione dei fornitori a valle le informazioni sul modello (art. 53(1)(b)), hanno una politica sul diritto d'autore e pubblicano la sintesi dei dati di addestramento; obblighi aggiuntivi per i modelli con rischio sistemico. | ◐ (sintesi dalle pagine ufficiali della Commissione sulle linee guida GPAI; articoli non riletti) |
| 99 | Sanzioni, fissate dagli Stati. Importi massimi: non riletti (○). | ○ |
| 111(2), (4), 113 | Disposizioni transitorie e date di applicazione, come riscritte dall'Omnibus. | ✔ (testo Reg. 2026/1744) |

**Calendario di applicazione dopo l'Omnibus:** vedi sezione 2 e N-AIACT-OMN. In sintesi: art. 4 e art. 5 dal 2.2.2025; GPAI dal 2.8.2025; art. 50 dal 2.8.2026 (il solo art. 50(2) per i sistemi generativi già sul mercato prima del 2.8.2026 entro il 2.12.2026); alto rischio Allegato III dal 2.12.2027; Allegato I dal 2.8.2028.

**Collegamenti al progetto:** DX-11 (non alto rischio; artt. 12, 14, 19 e 26 non obbligatori e usati come buona pratica; art. 50 applicabile); PV-01; DECISIONS §6 (riga «Etichetta "generato da AI" (art. 50)»: campo `ai_generated`, `model`, `prompt_ref`); DECISIONS §5 (art. 19, 6 mesi, buona pratica); documenti A1, A3, B1, C1, C3, E1, E2, E3 §7 (sezione «AI Act»); DA-E2-03 (preambolo con avvisi art. 50 nel codice); E3 (casi di test sull'art. 50); C1, C3, D1-D4 (etichettatura per canale).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- **Ruolo.** Gravya integra modelli di terzi tramite API: è fornitore di un sistema di IA, non fornitore di un modello GPAI, a meno di modifiche o fine-tuning oltre la soglia indicata dalla Commissione (vedi N-AIACT-COM). Le agenzie sono deployer. Gravya è anche deployer per i propri usi interni.
- **Art. 50(2) riguarda anche il testo.** DECISIONS §6 prevede la marcatura leggibile da macchina solo per le immagini e «metadati e testo» per email e post. Se gli output testuali di Gravya sono «testo sintetico», la marcatura leggibile da macchina del testo e l'eventuale esenzione per funzione assistiva vanno valutate: il Codice di buone pratiche (N-AIACT-COM) prevede almeno due livelli di marcatura quando serve. Per un sistema nuovo, non già sul mercato prima del 2.8.2026, il termine del 2.12.2026 non è una proroga.
- **Art. 50(1).** Se un agente di Gravya parla direttamente con persone (chat, risposte automatiche), l'informazione «sei con un'IA» spetta al fornitore al più tardi alla prima interazione.
- **Art. 50(4).** Spetta ai deployer (agenzie) per deep fake e testi di interesse pubblico; Gravya può aiutarli con l'etichetta (DECISIONS §6).
- **Alto rischio.** Il CRM e il marketing non compaiono tra i casi dell'Allegato III che ho letto in questa sessione (non ho riletto l'allegato, ○). DX-11 è plausibile, ma la classificazione dipende dalla finalità prevista dichiarata da Gravya: se un'agenzia usa la piattaforma per usi dell'Allegato III (per esempio selezione del personale o valutazione del credito) la finalità prevista e le condizioni d'uso vanno definite per escluderli. Le linee guida sulla classificazione sono ancora in bozza (N-AIACT-COM).
- **Art. 5.** Per un sistema che genera immagini, i nuovi divieti dal 2.12.2026 richiedono presìdi adeguati contro la generazione di materiale intimo non consensuale. Le tecniche manipolative (art. 5(1)(a)) non le ho riletti: ○.

---

### N-AIACT-OMN — Digital Omnibus sull'IA (adottato)

- **Estremi:** Regolamento (UE) 2026/1744 dell'8 luglio 2026, che modifica i Regg. (UE) 2024/1689, 2018/1139 e 2023/1230. Pubblicato in GU L del 24.7.2026; in vigore il terzo giorno dopo (27.7.2026). **È diritto in vigore, non più una proposta.**
- **Fonte ufficiale:** https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng (testo letto per intero in PDF: https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ%3AL_202601744)
- **Verificata il:** 2026-11-04 · **Stato:** ✔

**Contenuto (sintesi):**
- Art. 113: i Cap. III, sezioni 1-3 (requisiti e obblighi dei sistemi ad alto rischio) si applicano dal 2.12.2027 per i sistemi dell'Allegato III e dal 2.8.2028 per quelli dell'Allegato I; i nuovi divieti dell'art. 5(1)(ba), (bb), (1a), (1b) dal 2.12.2026; gli artt. 102-110 dal 27.7.2026.
- Art. 111(4): i fornitori di sistemi che generano audio, immagini, video o testo sintetici già sul mercato prima del 2.8.2026 adottano le misure per l'art. 50(2) entro il 2.12.2026.
- Art. 4 riscritto (vedi N-AIACT). Nuovo art. 4a (dati particolari per rilevare e correggere distorsioni, a condizioni rigorose). Art. 50(7) e art. 56(6) modificati: l'approvazione dei codici con atto di esecuzione non c'è più; la Commissione valuta l'adeguatezza dei codici.
- Art. 111(2): il periodo transitorio per i sistemi ad alto rischio già sul mercato si applica solo se non subiscono modifiche significative; per le PA entro il 2.8.2030.
- Nuovi poteri esclusivi dell'AI Office su sistemi basati su modelli GPAI quando modello e sistema sono dello stesso fornitore o gruppo (art. 75).
- Il Reg. 2023/1230 sulle macchine passa dalla sezione A alla sezione B dell'Allegato I.

**Collegamenti al progetto:** nessun documento cita le date dell'Omnibus. Le date di applicazione citate dai documenti (se ve ne sono) vanno riverificate; PV-01 e DX-11 non sono toccati dal rinvio perché DX-11 considera i casi d'uso non ad alto rischio.

---

### N-AIACT-COM — Documenti della Commissione che attuano l'AI Act

| Documento | Estremi | Fonte ufficiale | Verifica |
|---|---|---|---|
| Codice di buone pratiche sulla trasparenza dei contenuti generati da IA | Versione finale pubblicata il 10.6.2026. La Commissione e l'AI Board hanno confermato che è uno strumento volontario adeguato a dimostrare la conformità all'art. 50, par. 2, 4 e 5. Due sezioni: fornitori (marcatura e rilevamento), deployer (etichettatura di deep fake e testi). La Commissione ha creato anche un insieme di icone UE per l'etichettatura. | https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content | ✔ (pagina letta; ultimo aggiornamento 19.10.2026). Le date dell'adeguatezza (8 e 9.7.2026) e il termine del 2.2.2027 per l'interoperabilità del rilevamento li ho letti solo su fonti non ufficiali: non verificati. |
| Linee guida sugli obblighi di trasparenza dell'art. 50 | Pubblicate dalla Commissione (pagina aggiornata il 6.8.2026): chiariscono ruoli di fornitore e deployer, definizioni (sistemi interattivi, contenuto sintetico, deep fake, testo di interesse pubblico) ed eccezioni; spiegano come dimostrare la conformità, anche aderendo al Codice. Non vincolanti. | https://digital-strategy.ec.europa.eu/en/policies/guidelines-transparency-ai-generated-content (rinvia a https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-transparency-obligations) | ✔ (pagina letta). La data di pubblicazione del testo (20.7.2026) è da fonte non ufficiale. |
| Linee guida sull'ambito degli obblighi dei fornitori di modelli GPAI | C(2025) 5045 del 18.7.2025. Un modello è GPAI di norma se addestrato con calcolo superiore a 10^23 FLOP e capace di generare linguaggio, immagini o video. Chi modifica o affina un modello diventa fornitore del modello modificato solo in casi eccezionali, indicativamente se il calcolo della modifica supera un terzo di quello del modello originale. Un attore che integra un modello in un sistema e lo immette sul mercato è fornitore del sistema. Non vincolanti. | https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers · https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers | ✔ (estratti delle pagine ufficiali) |
| Codice di buone pratiche per i modelli GPAI | Consegnato alla Commissione il 10.7.2025. Il suo contenuto non l'ho letto. | https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai | ○ (pagina collegata, non aperta) |
| Linee guida sulla classificazione dei sistemi ad alto rischio (art. 6(5)) | **Solo bozza.** Dovute entro il 2.2.2026, la bozza è stata pubblicata il 19.5.2026 (data da fonte non ufficiale; la pagina della Commissione esiste). Non risulta adottata la versione finale (fonte non ufficiale). Chiariscono la «finalità prevista» e i casi d'uso dell'Allegato III. | https://digital-strategy.ec.europa.eu/en/library/draft-commission-guidelines-classification-high-risk-ai-systems | ◐ |

**Poteri di enforcement:** la Commissione può far valere gli obblighi GPAI dal 2.8.2026; per i modelli già sul mercato prima del 2.8.2025 il termine è il 2.8.2027. ✔ (pagina Commissione)

---

### N-AIACT-IT — Attuazione italiana dell'AI Act

- **Legge 23 settembre 2025, n. 132** («Disposizioni e deleghe al Governo in materia di intelligenza artificiale»), GU n. 223 del 25 settembre 2025, in vigore dal 10 ottobre 2025. Fonte: https://www.gazzettaufficiale.it/eli/id/2025/09/25/25G00143/sg · ✔ per gli estremi di pubblicazione; la data di entrata in vigore la ho letta su fonti non ufficiali (◐).
  - Art. 20: AgID e ACN sono le Autorità nazionali per l'IA. AgID è autorità di notifica; ACN è autorità di vigilanza del mercato e punto di contatto unico; Banca d'Italia, CONSOB e IVASS restano autorità di vigilanza per il loro settore; restano ferme le competenze del Garante e di AGCOM come Coordinatore dei servizi digitali. ✔ (testo riportato nelle note del d.lgs. 179/2026 su Normattiva)
  - Art. 24: delega al Governo per adeguare la normativa nazionale all'AI Act, con attribuzione alle autorità dei poteri di vigilanza, ispettivi e sanzionatori e adeguamento delle sanzioni. ✔ (idem)
  - Art. 26: introduce l'art. 612-quater del codice penale (diffusione illecita di contenuti falsificati con IA). ◐ (fonti non ufficiali)
- **Decreto legislativo 7 ottobre 2026, n. 179**, GU n. 234 dell'8 ottobre 2026, in vigore dal 23 ottobre 2026. Fonte: https://www.normattiva.it/eli/id/2026/10/08/26G00200/ORIGINAL · ✔ (titolo, data, entrata in vigore, definizioni e note letti su Normattiva). Titolo: adeguamento della normativa nazionale all'AI Act «in materia di poteri delle Autorità nazionali e di utilizzo dell'intelligenza artificiale nella formazione». Struttura letta: Capo II sui poteri delle Autorità (autorità, notifica, vigilanza del mercato artt. 14-18, sanzioni artt. 19-25, spazi di sperimentazione artt. 26-31), Capo III su formazione, professioni, lavoro, sanità e PA. Il contenuto degli articoli (importi delle sanzioni, ruolo del Garante, obblighi sul lavoro) lo conosco solo da fonti non ufficiali: ◐/non verificato.
- Atti attuativi ancora da adottare (decreto ACN sulla registrazione dei sistemi ad alto rischio, DPCM sui poteri ispettivi, regolamento AgID sulle sanzioni, decreti sulle sandbox): fonte non ufficiale, non verificati.

**Collegamenti al progetto:** nessuno. Chi vigila sull'art. 50 per Gravya in Italia: ACN (interpretazione).

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** l'interlocutore per l'AI Act in Italia è ACN; per i profili di dati personali resta il Garante. Gli importi massimi delle sanzioni per l'art. 50 vanno letti sul testo del d.lgs. 179/2026 e dell'art. 99 del regolamento.

---

## 6. Prodotti, dati e servizi digitali

### N-CRA — Cyber Resilience Act

- **Estremi:** Regolamento (UE) 2024/2847 del 23 ottobre 2024, GU L del 20.11.2024. Entrato in vigore il 10 dicembre 2024.
- **Fonti ufficiali:** testo https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R2847 (non aperto) · riassunto della Commissione https://digital-strategy.ec.europa.eu/en/policies/cra-summary (✔ letto) · pagina https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act
- **Verificata il:** 2026-11-04 · **Stato:** ◐: i dati vengono dal riassunto della Commissione, che precisa di non essere la posizione ufficiale della Commissione e rinvia al testo in GU.

**Contenuto (sintesi, dalla pagina della Commissione):**
- Si applica ai prodotti con elementi digitali (hardware e software, compresi componenti messi sul mercato separatamente) la cui finalità o uso ragionevolmente prevedibile include una connessione dati diretta o indiretta, quando sono messi a disposizione sul mercato dell'Unione.
- Il prodotto include le soluzioni di trattamento dei dati a distanza: elaborazione a distanza il cui software è progettato dal fabbricante o sotto la sua responsabilità e la cui assenza impedirebbe al prodotto di svolgere una delle sue funzioni.
- Il fabbricante (art. 13) esegue una valutazione del rischio, rispetta i requisiti essenziali dell'Allegato I, gestisce le vulnerabilità per un periodo di supporto e verifica la diligenza sui componenti di terzi.
- Art. 14: il fabbricante notifica alla CSIRT dello Stato della sede principale e all'ENISA le vulnerabilità sfruttate attivamente e gli incidenti gravi: allerta entro 24 ore, notifica entro 72 ore, relazione finale entro 14 giorni dalla disponibilità di una correzione (vulnerabilità) o entro un mese dalla notifica a 72 ore (incidenti). Vale anche per i prodotti già sul mercato prima dell'11.12.2027.
- Date: in vigore 10.12.2024; Cap. IV (organismi notificati) dall'11.6.2026; art. 14 dall'11.9.2026; applicazione piena dall'11.12.2027. I prodotti già sul mercato prima di tale data rientrano solo se subiscono una modifica sostanziale, eccetto le segnalazioni.
- Il 27.7.2026 la Commissione ha pubblicato orientamenti sull'applicazione (C(2026) 5252), non vincolanti: ✔ che esistono (pagina ufficiale); il loro contenuto sulla portata (SaaS, applicazioni web) lo conosco solo da fonti non ufficiali: **non_verificato**.
- Atti attuativi: Reg. delegato (UE) 2025/1535 e Reg. di esecuzione (UE) 2025/2392 del 28.11.2025 (descrizione tecnica delle categorie importanti e critiche). ✔ (elencati dalla pagina della Commissione)

**Atti italiani:** uno schema di decreto legislativo di attuazione, approvato in esame preliminare il 2.10.2026, è citato solo da una fonte non ufficiale: **non_verificato**.

**Collegamenti al progetto:** nessuno.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:**
- Un SaaS usato solo da browser non è di per sé un prodotto con elementi digitali (lettura coerente con la definizione di «trattamento dei dati a distanza», che copre solo il servizio da cui dipende un prodotto).
- Se Gravya distribuisce software eseguito sui dispositivi di agenzie o utenti (app mobile, estensione del browser, SDK, plugin, connettori installati in locale, agent o runtime installati presso il cliente) quel software è un prodotto e Gravya ne è fabbricante: dall'11.9.2026 valgono le segnalazioni dell'art. 14 e dall'11.12.2027 i requisiti essenziali. Il progetto non dice se esiste software distribuito: da chiarire, anche per B1 (runtime) e per eventuali connettori.

---

### N-DATAACT — Data Act

- **Estremi:** Regolamento (UE) 2023/2854 del 13 dicembre 2023, GU L del 22.12.2023; in vigore dall'11 gennaio 2024; si applica dal 12 settembre 2025.
- **Fonte ufficiale:** https://eur-lex.europa.eu/eli/reg/2023/2854/oj/eng (pagina aperta, testo letto solo in estratto)
- **Verificata il:** 2026-11-04 · **Stato:** ◐.

**Contenuto (sintesi):**
- **Cap. VI (artt. 23-31):** regole sul passaggio tra servizi di trattamento dei dati (che comprendono il cloud e, secondo le fonti, anche i SaaS) o verso infrastrutture ICT del cliente. Non ho riletto la definizione del servizio (○).
- **Art. 25:** i diritti del cliente e gli obblighi del fornitore sul passaggio sono definiti in un contratto scritto. Contenuto minimo, secondo fonti non ufficiali: preavviso massimo di due mesi, periodo di transizione massimo di 30 giorni, periodo di recupero dei dati di almeno 30 giorni. ◐/non verificato sul testo
- **Art. 29:** dal 12 gennaio 2027 i fornitori non possono imporre costi di passaggio; fino ad allora solo costi ridotti, non superiori ai costi direttamente collegati al passaggio. Prima del contratto il fornitore informa su costi standard, penali di recesso anticipato e costi ridotti. ✔ (art. 29(1)-(4) letti in estratto EUR-Lex)
- **Art. 31:** regime attenuato per servizi su misura di un solo cliente e per versioni di prova. ○ (fonte non ufficiale)
- Non c'è una soglia dimensionale per i fornitori del Cap. VI (fonte non ufficiale). ○

**Atti attuativi:** modelli di clausole contrattuali per il cloud, volontari (Commissione, novembre 2025): fonte non ufficiale.

**Collegamenti al progetto:** DX-09 §5, riga «Dati dell'agenzia a fine contratto» (restituzione o cancellazione entro 30 giorni dalla fine del contratto, valore «da allineare ai contratti») e F6.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** se il SaaS di Gravya è un «servizio di trattamento dei dati» per le agenzie, il Cap. VI si applica ai contratti con le agenzie (anche a quelli già in corso, secondo fonti non ufficiali): vanno previsti l'esportazione dei dati e delle risorse digitali, i termini dell'art. 25 e l'azzeramento dei costi di passaggio dal 12.1.2027. Il termine di «30 giorni dalla fine del contratto» per la cancellazione (DX-09 §5) può **entrare in tensione** con un periodo di recupero dei dati di almeno 30 giorni dopo la transizione: va verificato sul testo dell'art. 25(2).

---

### N-DSA — Digital Services Act

- **Estremi:** Regolamento (UE) 2022/2065 del 19 ottobre 2022, GU L 277 del 27.10.2022.
- **Fonte ufficiale:** https://eur-lex.europa.eu/legal-content/en/TXT/?uri=CELEX:32022R2065 (estratti)
- **Verificata il:** 2026-11-04 · **Stato:** ◐.

**Contenuto (sintesi):**
- Disciplina i fornitori di servizi intermediari («mere conduit», «caching», «hosting»). I considerando indicano come esempi di servizi di hosting il cloud computing, l'hosting web e i servizi di condivisione di file (◐: letto su un sito che riproduce il testo; fonte non ufficiale).
- I fornitori di servizi di hosting devono predisporre meccanismi di segnalazione dei contenuti illegali (art. 16) ✔ (estratto EUR-Lex) e rispettare gli altri obblighi per l'hosting; per le piattaforme online esistono obblighi ulteriori con esenzione per micro e piccole imprese (art. 19). ◐
- Coordinatore dei servizi digitali in Italia: AGCOM (art. 15, d.l. 15 settembre 2023, n. 123, conv. l. 159/2023). ✔ (richiamato nel testo dell'art. 20 l. 132/2025 su Normattiva)

**Collegamenti al progetto:** nessuno.

**Applicazione a Gravya — [INTERPRETAZIONE — da confermare con un legale]:** il DSA si applica a Gravya solo se è un fornitore di servizi intermediari. La memorizzazione di dati privati di CRM per conto dell'agenzia non è l'obiettivo tipico del DSA; potrebbe diventare rilevante se Gravya ospita contenuti pubblici delle agenzie (landing page, pagine, post): in quel caso ricadrebbe come servizio di hosting. Non sembra una piattaforma online ai sensi dell'art. 3, salvo diffusione al pubblico per conto dei destinatari del servizio. La conclusione è da accertare.

---

## 7. Proposte e norme in evoluzione (non diritto vigente)

### N-OMNIBUS-DATI — Digital Omnibus su GDPR, ePrivacy, Data Act, NIS2

- **Estremi:** proposta COM(2025) 837 del 19 novembre 2025, procedura 2025/0360(COD). **Non adottata.**
- **Stato (fonti non ufficiali, ◐):** al 12.10.2026 il Parlamento non aveva una posizione e il Consiglio non aveva un mandato. Una fonte non ufficiale riferisce che il 21.10.2026 il Coreper ha concordato il mandato del Consiglio (testo di 179 pagine, doc. 14756/26): cookie che restano nella direttiva ePrivacy con sei esenzioni, attesa di quattro mesi prima di richiedere di nuovo il consenso dopo un rifiuto, definizione relativa di dato personale, legittimo interesse per lo sviluppo di IA, termine di 96 ore per le violazioni ad alto rischio. **Non l'ho verificato sul sito del Consiglio: non_verificato.**
- **Fonte ufficiale (non aperta):** scheda del Parlamento https://www.europarl.europa.eu/legislative-train/theme-a-new-plan-for-europe-s-sustainable-prosperity-and-competitiveness/file-digital-package
- **Effetto oggi:** nessuno. Si applicano GDPR, direttiva ePrivacy e Data Act come in vigore. Le modifiche, se adottate, richiederebbero recepimento nazionale per la parte ePrivacy.

---

## 8. Norme valutate e ritenute non applicabili o non verificate

- **DSA:** vedi N-DSA (possibile solo in parte).
- **Direttiva ePrivacy, regolamento ePrivacy:** la proposta di regolamento è stata ritirata nel 2025 secondo fonti non ufficiali (non verificato); resta la direttiva.
- **Non verificate, fuori dal perimetro iniziale ma da valutare:** Codice del consumo (d.lgs. 206/2005) e disciplina delle pratiche commerciali scorrette (AGCM) per i messaggi di marketing; direttiva (UE) 2019/882 sull'accessibilità (richiamata dall'art. 50(5) AI Act per le informazioni di trasparenza); le Linee guida del Garante «Attività promozionale e contrasto allo spam» (2013). Non le ho aperte: **non_verificate**.

## 9. Cambiamenti rilevanti per i documenti esistenti

Non ho modificato nessun documento. Segnalo dove una decisione o un documento poggia su una norma citata in modo incompleto, scaduta o modificata.

1. **AI Act, art. 50(2) e il testo generato.** DECISIONS §6 (riga etichetta art. 50) prevede la marcatura leggibile da macchina per le immagini e metadati/testo per email e post. L'art. 50(2) copre anche il testo sintetico e il Codice di buone pratiche (adeguato per la Commissione) indica almeno due livelli di marcatura. Documenti toccati: DECISIONS §6, C1 (§4.1 `ai_generated`), C3 (§7 e payload), E2 (DA-E2-03), E3, D1-D4.
2. **Diritto del marketing assente.** Nessun documento dell'ondata 1, né PRINCIPI (PV-01 cita solo GDPR, NIS2 e AI Act), cita art. 130 Codice, art. 122, direttiva ePrivacy, d.lgs. 70/2003, RPO o le linee guida del Garante su cookie e tracking pixel. Il termine di adeguamento alle linee guida sui pixel è scaduto il 29.10.2026. Documenti toccati: PRINCIPI (PV-01), DX-11, D1-D4, C3, A3, B2.
3. **NIS2, ambito e termini.** DX-10 assegna ad A5 la notifica 24 h / 72 h presumendo che Gravya sia soggetto NIS; l'ambito non è accertato. Mancano la relazione finale entro un mese, le definizioni di «incidente significativo di base» (Det. ACN 379907/2025, Allegati 3 e 4) e i termini della coorte di Gravya. Documenti toccati: DX-10, DX-22(a), A5, A3, C1, C3, B1, B2, E2.
4. **Data Act, art. 25 e art. 29.** DX-09 §5 (restituzione o cancellazione entro 30 giorni dalla fine del contratto) va riverificato contro il periodo di recupero dei dati e il divieto di costi di passaggio dal 12.1.2027. Documenti toccati: DX-09 §5, F6.
5. **AI Act, calendario.** Nessuna norma citata nei documenti è errata, ma DX-11, C3, A1, A3, B1, E1, E2, E3 non riportano il calendario dopo l'Omnibus: gli artt. 12, 14, 19, 26 sarebbero comunque applicabili ai sistemi ad alto rischio solo dal 2.12.2027; l'art. 50 vale dal 2.8.2026; l'art. 4 è stato ridotto a obbligo di misure di sostegno.

## 10. Elementi non verificati in questo registro

- Pagine ACN (acn.gov.it) non apribili: contenuto letto solo in estratto.
- Determinazioni ACN 155238/2026 e 314287/2026; Determinazione 379887/2025 e numero di misure e requisiti: non su fonte ufficiale.
- Mandato del Consiglio sul Digital Omnibus dati (21.10.2026): fonte non ufficiale.
- Contenuto della guida CRA C(2026) 5252; schema di decreto italiano di attuazione del CRA.
- Date dell'adeguatezza del Codice art. 50 (8-9.7.2026), del termine del 2.2.2027 e della pubblicazione delle linee guida art. 50 (20.7.2026); data della bozza delle linee guida sull'alto rischio (19.5.2026) e assenza della versione finale.
- Contenuto degli articoli del d.lgs. 179/2026 oltre le definizioni; atti attuativi.
- GDPR (aggiornato v1.2): articoli letti sul testo originale in GU (Cellar), ✔: 4(5), 4(7), 4(8), 5(1)(c), (e), (f), 5(2), 17, 25, 28, 32, 33, 34, 44-49 (47 solo esistenza e oggetto), 99; la rettifica GU L 127 del 23.5.2018 e i consolidamenti non sono stati confrontati. Restano ○: articoli non riletti (6, 7, 12-16, 18-22, 83 e altri); ◐ art. 19 (estratto EUR-Lex). Considerando ✔: 26, 28-30, 39, 65, 78, 81, 83, 85.
- Data Privacy Framework: non verificato che la decisione 2023/1795 sia in vigore oggi (nessun atto di revoca visto, ma nessun consolidato o elenco ufficiale aggiornato aperto); stato della causa C-703/25 P (nessuna sentenza vista, scheda InfoCuria non aperta); elenco DPF del Dipartimento del Commercio non consultato; contenuto della lettera EDPB del 31.7.2026 (*Trump v. Slaughter*); periodicità dei riesami successivi al primo (solo fonte non ufficiale); motivi della sentenza T-553/23 non riletti per intero.
- Linee guida EDPB: nessuna versione definitiva delle linee guida 01/2025 trovata (bozza); PDF di 01/2025, 4/2019 e 01/2020 letti solo in estratti; linee guida 02/2026 sull'anonimizzazione e sentenza C-413/23 P non lette.
- Direttiva 2000/31/CE; Allegati I e II della NIS2; Allegato III dell'AI Act; art. 5(1)(a)-(h) dell'AI Act; art. 99 AI Act; art. 25 Data Act (contenuto minimo).
- Linee guida del Garante sullo spam (2013); ordinanza Cassazione 15881/2025; Joint Opinion EDPB-EDPS 2/2026.

## 11. Testi trovati nei materiali che si rivolgevano a un agente

Nelle pagine e nei file letti non ho trovato istruzioni rivolte a un agente.

## Storico modifiche

| Versione | Data | Cosa | Perché |
|---|---|---|---|
| 1.0 | 2026-11-04 | Creazione del registro: GDPR, Codice privacy (artt. 122 e 130), ePrivacy, RPO, linee guida del Garante su cookie e tracking pixel, e-commerce, NIS2 e recepimento italiano con atti ACN, AI Act con Omnibus, documenti della Commissione e attuazione italiana, CRA, Data Act, DSA, proposta Omnibus dati. | Primo registro richiesto dal coordinator; prima della v1.5 dei documenti dell'ondata 1. |
| 1.1 | 2026-11-04 | Lotto 1, solo N-GDPR: aggiunte o completate le sintesi di art. 4(5) e considerando 26, 28, 30; 5(1)(c), (e), 5(2); 17 con 17(3); 25; 28(10); 32; 33(1)-(2) e 34; Cap. V (44-49). Nota sul limite di lettura; §10 aggiornato; aggiunte tre interpretazioni (pseudonimi nei trace, art. 28(10) e termine di notifica del responsabile, trasferimenti verso LLM extra-UE). | Richiesta del compliance-auditor (rilievi su C3 e E1). La pagina EUR-Lex dell'atto si è aperta solo fino al considerando 87: i considerando sono ✔, gli articoli ◐ da estratti EUR-Lex e copie non ufficiali (nessun articolo portato a ✔). §9 non modificato: nessun articolo letto cambia il senso di una decisione. |
| 1.2 | 2026-11-04 | Lotto 2: N-GDPR portato a ✔ sul testo italiano originale in GU (4(5), 4(7), 4(8), 5(1)(c), (e), (f), 5(2), 17 intero, 25, 28 intero, 32, 33, 34, 44-49, 99); sintesi del lotto 1 confermate (nessuna differenza sostanziale), integrati 17(1)(e)-(f), le condizioni 34(3)(b)-(c), i criteri e la revoca di 45(2)-(6), le deroghe di 49(1)-(4), gli artt. 47 e 48; tolta la riga duplicata dell'art. 25 con ○; nuova scheda N-DPF (decisione 2023/1795, T-553/23, impugnazione C-703/25 P, riesame 2024) e nuova scheda N-EDPB (linee guida 01/2025 bozza, 4/2019 v2.0, raccomandazioni 01/2020 v2.0); §1 e §10 aggiornati. | Richiesta del coordinator (norme «da aggiungere» dal compliance-auditor su C3 e E1) e testo ufficiale integrale disponibile. §9 non modificato: nessuna decisione o documento poggia su una citazione errata alla luce degli articoli letti; la rettifica del 2018 non è stata confrontata. |
