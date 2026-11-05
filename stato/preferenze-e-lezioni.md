# Preferenze dell'utente e lezioni (keywords: preferenze, vincoli, lezioni, errori, stile)

Solo il modo di lavorare, nella forma in vigore. Le decisioni di progetto stanno in `docs/DECISIONS.md` e `docs/PRINCIPI.md`.

## Vincoli dell'utente (keywords: opus, inferire, stime, italiano)
- Solo il coordinator usa Opus; gli altri agenti sono quelli di `.claude/agents/` con il modello indicato nel file. Niente agenti creati al volo.
- Non inferire, non inventare dati: nel dubbio chiedere. Distinguere verificato da dedotto.
- Nessuna stima temporale, solo taglie S/M/L. Italiano.

## Come vuole che si lavori (keywords: punto di verità, sì/no, push, file pronti)
- **Un solo punto di verità.** Un dato in un solo file; se deve stare in due (schema di risposta in descrizione e prompt dello stesso agente), si aggiornano entrambi nello stesso commit. Un aggiornamento a metà lo fa arrabbiare molto.
- **Solo contenuto corrente** nei registri e in `stato/` (DECISIONS.md, memoria, ambiente): ciò che è superato si toglie; la storia sta in git (e, per le decisioni, nell'archivio se deciso). Motivo: i file non devono crescere senza limite e una lettura troncata non deve recuperare una regola vecchia. Eccezione (utente, 2026-11-05): resta ciò che serve a capire il motivo di una scelta senza ricostruire il percorso, scritto quando possibile come motivo sulla regola corrente.
- **Rispondere esattamente alla domanda**: se è sì/no, la prima parola è sì o no.
- Le decisioni dell'utente passano dal registrar con il testo alla lettera; mai modificare a mano DECISIONS.md e index.md (salvo eccezione autorizzata dall'utente).
- Chiedere conferma prima di cancellare o spostare file del repository.
- Dopo ogni commit: push e verifica del remoto; senza token, elencare all'utente i file modificati.
- Azioni ovvie senza che le chieda: commit delle prove nel repository, aggiornamento di `stato/handoff-sessione.md`.
- Se l'utente ha già dichiarato una scelta, applicarla e allineare i file senza ripresentarla come decisione.
- Niente budget di sessione: non proporre di fermare una sessione a metà.
- Configurazioni lean, senza copie superflue; file già pronti da incollare sulla piattaforma.
- Ricopiatura dei prompt degli agenti sulla piattaforma: se ne occupa l'utente se servirà (2026-11-05); non tenerla tra le azioni aperte e non ricordarla.
- Repository di riferimento locali (`gravya-app`, `gravya-app-kloudify`): lavoro in corso dell'utente, mai toccarli, nemmeno con comandi che scrivono di nascosto (`git status`); blocco in `stato/ambiente.md`. Prima di rimuovere strumenti di sistema, controllare che non li usino.
- **Continuità tra ambienti:** tutto deve essere utilizzabile da Claude Code locale (abbonamento) e dalla piattaforma (API): task in file committati, percorsi relativi, niente di necessario solo in /tmp, /mnt o nei thread.
- **File temporanei degli agenti** (/tmp, tmp di pytest, pacchetti scaricati): il coordinator li verifica e li cancella direttamente, **senza segnalarli**. Si segnala solo un file fuori perimetro nel repository, con dati sensibili o non temporaneo. Non cancellare i file di servizio della piattaforma (/tmp/ale-*).

## Thread degli agenti sulla piattaforma (keywords: 25 thread, riuso)
- Massimo 25 thread per sessione e l'utente non può archiviarli singolarmente: riusare con `send_to_agent` i thread inattivi dello stesso tipo («NUOVO INCARICO», dicendo quali file non toccare più); thread nuovo solo per un tipo non ancora lanciato; a limite raggiunto, proporre una sessione nuova.

## Lezioni (keywords: errori, verifiche, risultati negativi)
- **Un solo branch** (utente, 2026-11-05, molto irritato): lavorare sempre su un unico branch di lavoro; niente branch separati per l'implementer, che crea commit avanti e indietro difficili da seguire. Se due agenti lavorano in parallelo, su file diversi dello stesso branch.
- Verificare che un percorso esista prima di scriverlo in un prompt o in un task.
- Modello e strumenti di un agente si verificano nella configurazione, non chiedendoli all'agente.
- I report degli agenti sono indizi: verificarli sui file (attribuzioni del registrar, file:riga del code-reader, «verificato sul codice» del doc-writer, «nessun file in /tmp» dell'implementer).
- Una causa resta un'ipotesi finché un test o una verifica non la conferma.
- Preservare le terminazioni di riga quando si riscrive un file (file CRLF in `docs/fonti/`).
- Prima di indicare un comando di test in un task, verificarne l'esito completo.
- Implementer: tende a codificare come costanti i valori decisi e i minimi/massimi (DX-22) e a piegare il codice ai test di prova forniti come criterio di fine: rileggere il codice nuovo, non solo l'esito dei test; nel task scrivere «se un test contraddice il task o una decisione, fermati e chiedi».
- Doc-writer: tende a riassumere le righe vecchie dello Storico modifiche: salvare lo Storico prima del lancio e confrontarlo dopo.
- Registrar: tende a inventare stati («Decisa con riserva») e a toccare legenda e intestazione: nel task «stati ammessi solo quelli della legenda; un ok = Decisa»; controllare nel diff le righe fuori tabella.
- Auditor: aggiungono chiavi fuori schema al JSON («controlli», «da_aggiungere_al_registro»): nel task «solo le chiavi dello schema».
- Regulatory-researcher: un task con molte norme esaurisce il contesto; una norma per volta, ogni atto letto una sola volta, registro aggiornato subito.
- Azioni dell'utente: appena dice che un'azione è fatta, si aggiorna `stato/azioni-utente.md` nello stesso turno; nel dubbio chiedere se è ancora aperta.
- Controllo dei file non previsti dopo un agente: in locale lo fa `scripts/agenti.py lancia`; con lo strumento Agent o sulla piattaforma, `touch` di un marcatore prima del lancio, poi `find` con `-newer <marcatore> -type f` sul repository e su `/tmp`.
- Le clausole per agente delle lezioni qui sopra (implementer, registrar, auditor, doc-writer, regulatory-researcher) le inserisce `scripts/agenti.py nuovo-task`: se cambia una lezione, si aggiorna anche lo script nello stesso commit.
