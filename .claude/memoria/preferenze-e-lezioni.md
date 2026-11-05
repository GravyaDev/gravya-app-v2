# Preferenze dell'utente e lezioni (keywords: preferenze, vincoli, lezioni, errori, stile)

Solo il modo di lavorare. Le decisioni di progetto stanno in `docs/DECISIONS.md` e `docs/PRINCIPI.md`, non qui.

## Vincoli dell'utente (keywords: opus, inferire, stime, italiano)
- Subagenti mai su Opus e niente agenti creati al volo: solo agenti predefiniti della piattaforma. Unica eccezione: il coordinator (sessione principale) è Opus, effort medium.
- Non inferire, non inventare dati: nel dubbio chiedere. Distinguere verificato da dedotto.
- Nessuna stima temporale, solo taglie S/M/L. Scrivere in italiano.
- Conformità prima di tutto; principi e decisioni: vedi PRINCIPI.md / DECISIONS.md.

## Come vuole che si lavori (keywords: punto di verità, sì/no, aggiornamenti, push)
- **Un solo punto di verità.** Un dato in un solo file; se deve stare in due (es. schema di risposta in descrizione e prompt dello stesso agente), si aggiornano entrambi nello stesso commit. Un aggiornamento fatto a metà lo fa arrabbiare molto (successo con l'impegno degli agenti messo solo nel README).
- **Rispondere esattamente alla domanda**: se è sì/no, la prima parola è sì o no. Errore commesso: alla domanda "vedi la nuova descrizione?" ho risposto con spiegazioni invece di "No".
- Le decisioni dell'utente passano dal Registrar con il testo alla lettera; mai modificare a mano DECISIONS.md/index.md.
- Chiedere conferma prima di cancellare o spostare file.
- Dopo ogni commit: push e verifica del remoto (se il token è disponibile; altrimenti elencare all'utente i file modificati/eliminati, li pusha lui).
- Niente budget di sessione: bloccare una sessione a metà non ha senso (decisione netta dell'utente, 2026-11-04). Non riproporlo.
- Se l'utente ha già dichiarato una scelta (es. "ho messo l'implementer a effort medio"), applicarla e allineare i file, senza ripresentarla come decisione (errore della sessione 5).
- Vuole configurazioni lean, senza copie superflue; preferisce che i file siano già pronti da incollare sulla piattaforma.

## Continuità tra ambienti (keywords: abbonamento, locale, credito api, claude code)
- Richiesta dell'utente (2026-11-05): tutto ciò che si produce deve essere utilizzabile anche da sessioni Claude Code locali, perché se finisce il credito API continua con l'abbonamento. Quindi: memoria in `.claude/memoria/` committata, task degli agenti in file committati, percorsi relativi, nessuna informazione necessaria solo in /tmp, /mnt o nei thread della piattaforma.

## File temporanei degli agenti (keywords: tmp, fuori perimetro, cancellare, notifica)
- Decisione netta dell'utente (sessione 8, molto irritato): i file temporanei lasciati dagli agenti (es. /tmp/..., tmp_path di pytest, wheel scaricati) il coordinator li verifica e li CANCELLA DIRETTAMENTE, senza segnalarli all'utente. Non menzionarli più nei resoconti. Vale come conferma permanente alla cancellazione per i soli file temporanei degli agenti (non per file del repository o della memoria). Segnalare solo se un file fuori perimetro è nel repository, contiene dati sensibili o non è un temporaneo.
- Non cancellare i file di servizio della piattaforma (/tmp/ale-*) né le sandbox del coordinator ancora in uso.

## Lezioni (keywords: errori, verifiche, risultati negativi)
- Verificare che un percorso esista prima di scriverlo in un prompt (docs/fonti e docs/memoria erano stati citati senza esistere).
- Un agente non sa dichiarare con certezza il proprio modello: il modello si verifica nella configurazione della piattaforma.
- I report degli agenti vanno verificati sui file: il Registrar aveva attribuito all'utente una proposta del coordinatore (DA-C3-04).
- La patch v1.5 interrotta nella sessione 1 è stata scartata: non cercarla.
- Python che riscrive file CRLF li converte in LF e gonfia il diff: preservare le terminazioni (file in docs/fonti/).
- Lo schema di risposta degli agenti sta solo nel prompt (e nella descrizione per il coordinator); niente strumenti custom di output sulla piattaforma (sessione 3).
- Non attribuire una causa prima di averla provata: nella sessione 3 ho detto "quasi certamente lo schema" e poi gli errori indicavano un'interruzione.
- Prima di indicare un comando di test in un task, verificarne l'esito completo (non solo `tail`): `node --test test/` fallisce su Node 22, serve `node --test`.
- L'utente non vuole dover chiedere azioni ovvie: commit delle prove nel repo e aggiornamento dell'handoff si fanno senza che lo chieda (le regole sono ora nel prompt del coordinator).
- Non chiedere agli agenti il proprio modello nei collaudi: si verifica nella configurazione.
- Collaudo sessione 5: il code-reader su Haiku sbaglia nelle sintesi (numero di riga inventato su un file letto "per intero", contraddizione falsa marcata verificata). Verificare sempre a campione file:riga dei suoi report prima di passarli al doc-writer.
- Sessione 8: con test di riproduzione forniti come criterio di fine, l'implementer piega il codice ai test (mantiene production_override e SELECT perché i test li usano) e introduce costanti nuove (timeout 2000 ms) presentandole come 'decisioni mancanti'. Rileggere sempre il codice nuovo per DX-22, non solo l'esito dei test.
- L'implementer tende a codificare come costanti i valori "decisi" (es. intervallo 1-168 h): controllare DX-22 anche su min/max, non solo sui default.
- Nei task usare `node --test` e non `npm test`: npm scrive un log in `~/.npm/_logs/`, che risulta come file fuori perimetro nel controllo della regola 6 (sessione 6).
- Per individuare file non previsti dopo un collaudo funziona così: `touch marker` prima di avviare gli agenti, poi `find / -xdev -newer marker -type f` escludendo /proc, /sys, la sandbox e /var/lib/postgresql.
- Il doc-writer tende a dare per "verificati sul codice" i punti del dossier del code-reader anche quando non li ha ricontrollati (sessione 6).
- Gli auditor (sessione 6) a volte aggiungono al JSON chiavi fuori schema: controllare. Sessione 7: il plan-auditor aggiunge "controlli" (vuota o null) anche con il prompt 1.16 e con il divieto esplicito nel task: probabile confusione con la chiave "controllato"; da proporre all'utente un ritocco del prompt (es. rinominare "controllato" o un esempio esplicito).
- Utile per collaudi su codice: Postgres 16 è installato nel container (`service postgresql start`), npm registry raggiungibile.
- Sessione 7: il regulatory-researcher con 6 domande su GDPR, EDPB, DPF e NIS2 in un solo task è fallito per contesto esaurito (1,26M token > 1M), senza scrivere nulla nel registro. Causa probabile, non verificata: testi integrali EUR-Lex letti più volte. Contromisura: task piccoli e in sequenza (una norma per volta), ogni atto letto una sola volta, registro aggiornato subito dopo ogni lettura.
- Sessione 7, errore grave: ho ricordato all'utente due azioni (impegno del coordinator, cache della sessione 3) che aveva già fatto e già comunicato, perché nessuna sessione le aveva tolte da azioni-utente.md. Regola: appena l'utente dice che un'azione è fatta o chiusa, si aggiorna azioni-utente.md nello stesso turno, prima di ogni altra cosa. Nel dubbio su una voce aperta, chiedere "è ancora aperta?" invece di ripresentarla come da fare.
- Sessione 7: il doc-writer (catalogo variabili) ha scritto /tmp/x.json (elenco variabili, 18 KB) nonostante la regola comune 6: ha Bash. Ricontrollare sempre con find -newer dopo ogni doc-writer; valutare con l'utente se togliergli Bash.
- Sessione 8: il compliance-auditor ha aggiunto la chiave fuori schema «da_aggiungere_al_registro» (vuota). Ricorrente negli auditor: ricordare nel task «solo le chiavi dello schema».
- Sessione 8: il registrar ha usato di nuovo «Decisa con riserva» su un «ok» semplice dell'utente; corretto rimandandogli il testo. Nei task del registrar scrivere esplicitamente: stati ammessi solo quelli della legenda, «ok» = «Decisa».
- Sessione 7: il registrar ha aggiunto di sua iniziativa stati nuovi alla legenda di DECISIONS ("Decisa con riserva", "Bloccante"). Controllare sempre le righe fuori dalle tabelle nel diff del registrar (intestazione, legenda).
- Sessione 7: un doc-writer (B1) ha riassunto le righe passate dello Storico modifiche per "tagliare": lo storico non si riscrive. Controllare nel diff che le righe precedenti dello Storico siano intatte (ripristinate dal coordinator con git show HEAD). Mettere il divieto nel brief/task.
- Politica sui thread (decisione dell'utente, sessione 7): l'utente non usa le API e dalla console non può archiviare thread specifici. Quindi: massimo 25 thread per sessione; riusare sempre con send_to_agent i thread IDLE dello stesso tipo (dicendo NUOVO INCARICO e quale file non toccare più); creare un thread nuovo solo per un tipo di agente non ancora lanciato nella sessione; pianificare i lanci paralleli dentro il limite; a limite raggiunto, proporre una sessione nuova.
- Sessione 7: i doc-writer, anche col divieto nel task, tendono a riassumere le righe vecchie dello Storico: dopo ogni doc-writer ripristinarle dalla versione in git (script effimero /tmp/s7/restore_storico.py: riscrivere se manca) e controllare la riga della versione precedente.
