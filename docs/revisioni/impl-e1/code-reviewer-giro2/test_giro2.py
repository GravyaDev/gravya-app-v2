"""Riproduzioni del giro 2 del code-reviewer (head bc32c72). Ogni test asserisce il comportamento CORRETTO
richiesto da E1 v1.6 / dalle decisioni: FAIL = difetto dimostrato; PASS = tentativo di rottura fallito
(controllo positivo). Il nome del test dice quale dei due e' atteso nella sezione 'atteso' del docstring."""
from __future__ import annotations

import hashlib
import socket
import threading
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from gravya_e1 import whitelist as wl
from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
from gravya_e1.db import writer_transaction
from gravya_e1.models import SegmentEnd, SegmentStart, TraceStart
from gravya_e1.signals import InMemorySignalSink, PostgresSignalSink
from gravya_e1.tracing import TracingHelper

DB = "gravya_e1_review2"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def seg(kind, attrs=None, tenant=None, trace=None, **kw):
    return SegmentStart(segment_id=uuid.uuid4(), trace_id=trace or uuid.uuid4(), tenant_id=tenant or uuid.uuid4(),
                        kind=kind, started_at=NOW(), attributes=attrs or {}, **kw)


def stored(conn, sid):
    conn.rollback()
    with conn.cursor() as cur:
        cur.execute("SELECT attributes, name, status FROM gravya_trace_segments WHERE segment_id=%s", (str(sid),))
        return cur.fetchone()


def helper(prod_variables, sink, kp):
    return TracingHelper(prod_variables, sink, kp, production_override=True)


# ---- G1/G2: formati "stretti" ma con ancoraggio `$` (accetta un "\n" finale) -------------------------------
def test_G1_hash_con_newline_finale_deve_essere_scartato():
    """atteso: FAIL. `^[0-9a-f]{64}$` con re.match accetta 64 cifre + '\\n' (65 caratteri)."""
    assert wl.hash_hex("a" * 64 + "\n", 2048) is False


def test_G1b_hash_con_newline_scritto_in_db(admin_conn, prod_variables, key_provider, partitions):
    """atteso: FAIL. Un valore di 65 caratteri finisce in attributes (criterio 4 / B4 non chiuso)."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    s = seg("llm", {"gravya.prompt.key": "prompt_greeting", "gravya.prompt.version": "1.0", "gravya.prompt.hash": "a" * 64 + "\n"})
    h.start_segment(admin_conn, s)
    attrs, _, _ = stored(admin_conn, s.segment_id)
    assert "gravya.prompt.hash" not in attrs, repr(attrs.get("gravya.prompt.hash"))


@pytest.mark.parametrize("fn,val", [
    (wl.opaque_id, "tool_abc\n"), (wl.version_identifier, "1.0\n"), (wl.model_identifier, "gpt-4\n"),
    (wl.key_ref_format, "v1\n"), (wl.loose_token, "run-1\n"), (wl.destination_id, "dest_abc\n"),
])
def test_G2_newline_finale_negli_identificativi(fn, val):
    """atteso: FAIL per tutti: stessa causa (`$` senza fullmatch)."""
    assert fn(val, 2048) is False


@pytest.mark.parametrize("val", [
    "urn:uuid:" + "12345678-1234-5678-1234-567812345678", "{12345678-1234-5678-1234-567812345678}",
    "1234567812345678123456781234567-8", "----12345678123456781234567812345678----", "0x" + "1" * 30,
])
def test_G2b_uuid_non_canonico_deve_essere_scartato(val):
    """atteso: FAIL. uuid.UUID() accetta urn:, graffe, trattini ovunque, prefisso 0x: il valore e' scritto cosi' com'e'."""
    assert wl.uuid_identifier(val, 2048) is False


# ---- G3: formato "prefisso_corpo" non e' un vocabolario: PII con prefisso passa ------------------------
@pytest.mark.parametrize("val", ["mario_rossi", "tel_3331234567", "cf_RSSMRA80A01H501U", "iban_IT60X0542811101000000123456",
                                 "email_marioRossiExampleCom"])
def test_G3_pii_con_prefisso_deve_essere_scartata(val):
    """atteso: FAIL. Il formato stretto respinge la forma grezza ma non la stessa PII con un prefisso+underscore."""
    assert wl.opaque_id(val, 2048) is False


@pytest.mark.parametrize("val", ["mario.rossi.example.com", "api.openai.com", "RossiMario.1980"])
def test_G3b_model_identifier_accetta_domini_e_nomi(val):
    """atteso: FAIL. gen_ai.provider.name/model accettano punti: domini e nomi con punti passano."""
    assert wl.model_identifier(val, 2048) is False


# ---- G4: scrittura asincrona/bufferizzata (decisione: "buffer asincrono come in E1 §5") -----------------
def test_G4a_la_scrittura_e_sincrona_nel_chiamante(admin_conn, prod_variables, key_provider, partitions):
    """atteso: FAIL. Se la scrittura fosse in background, subito dopo start_segment la riga potrebbe non esserci:
    qui c'e' sempre (commit completato nel thread del chiamante) => nessun buffer asincrono."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    seen_immediately = 0
    for _ in range(20):
        s = seg("agent", {"gen_ai.agent.id": "agent_a"})
        h.start_segment(admin_conn, s)
        if stored(admin_conn, s.segment_id) is not None:
            seen_immediately += 1
    assert seen_immediately < 20, "tutte le 20 righe committate prima del ritorno di start_segment: scrittura sincrona"


def _lock_segments_partition(seconds_holder):
    locker = psycopg.connect(f"dbname={DB}")
    with locker.cursor() as cur:
        cur.execute("SELECT c.relname FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid "
                    "JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='gravya_trace_segments' ORDER BY 1 LIMIT 1")
        part = cur.fetchone()[0]
        cur.execute(f"LOCK TABLE {part} IN ACCESS EXCLUSIVE MODE")
    return locker


def test_G4b_con_db_lento_un_secondo_chiamante_aspetta_oltre_il_timeout(prod_variables, key_provider, partitions, admin_conn):
    """atteso: FAIL. Timeout di scrittura = 2000 ms. Con la partizione bloccata il primo chiamante attende ~2 s;
    il secondo resta in coda sul lock della connessione unica: ~4 s (> timeout). 'Il chiamante non aspetta' e' falso."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    h.start_segment(admin_conn, seg("agent", {"gen_ai.agent.id": "agent_a"}))  # apre la connessione propria
    locker = _lock_segments_partition(None)
    durations = {}

    def run(name):
        c = psycopg.connect(f"dbname={DB}")
        a = time.perf_counter()
        h.start_segment(c, seg("agent", {"gen_ai.agent.id": "agent_a"}))
        durations[name] = time.perf_counter() - a
        c.close()

    ts = [threading.Thread(target=run, args=(n,)) for n in ("A", "B")]
    for t in ts:
        t.start()
        time.sleep(0.2)
    for t in ts:
        t.join(30)
    locker.rollback(); locker.close()
    timeout_s = 2.0
    assert max(durations.values()) <= timeout_s + 0.5, f"attese: {durations}"


class _FreezableProxy:
    def __init__(self, target_host="127.0.0.1", target_port=5432):
        self.frozen = False
        self.srv = socket.socket(); self.srv.bind(("127.0.0.1", 0)); self.srv.listen(8)
        self.port = self.srv.getsockname()[1]
        self.target = (target_host, target_port)
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            u = socket.create_connection(self.target)
            for a, b in ((c, u), (u, c)):
                threading.Thread(target=self._pipe, args=(a, b), daemon=True).start()

    def _pipe(self, a, b):
        try:
            while True:
                d = a.recv(65536)
                if not d:
                    break
                while self.frozen:
                    time.sleep(0.05)
                    # dati scartati: la rete "si blocca" senza chiudere la connessione
                if not self.frozen:
                    b.sendall(d)
        except OSError:
            pass


def test_G5_stallo_di_rete_blocca_il_chiamante_senza_limite(prod_variables, key_provider, partitions):
    """atteso: FAIL. statement_timeout e' lato server: con la rete bloccata dopo la connessione il client
    resta in recv() per sempre (nessun timeout lato client, nessun connect_timeout): il chiamante e' appeso."""
    try:
        psycopg.connect("host=127.0.0.1 user=root dbname=postgres").close()
    except Exception:
        pytest.skip("TCP verso PostgreSQL non disponibile")
    proxy = _FreezableProxy()
    caller = psycopg.connect(f"host=127.0.0.1 port={proxy.port} user=root dbname={DB}")
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    h.start_segment(caller, seg("agent", {"gen_ai.agent.id": "agent_a"}))      # connessione propria via proxy
    proxy.frozen = True
    done = threading.Event()

    def run():
        h.start_segment(caller, seg("agent", {"gen_ai.agent.id": "agent_a"}))
        done.set()

    t = threading.Thread(target=run, daemon=True); t.start()
    finished = done.wait(timeout=8)
    proxy.frozen = False
    assert finished, "start_segment ancora bloccato dopo 8 s (timeout configurato: 2 s)"


# ---- G6: fail-open con kind non valido in produzione ------------------------------------------------------
def test_G6_end_segment_kind_sconosciuto_non_deve_sollevare_in_produzione(admin_conn, prod_variables, key_provider, partitions):
    """atteso: FAIL. end_segment(kind='bogus') solleva ValueError dall'helper anche in produzione."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    t = uuid.uuid4()
    h.end_segment(admin_conn, SegmentEnd(segment_id=uuid.uuid4(), tenant_id=t, ended_at=NOW(), status="ok"), "bogus")


# ---- G7: credenziali della connessione propria ------------------------------------------------------------
def test_G7_get_parameters_non_contiene_la_password():
    """atteso: FAIL. L'helper apre la connessione propria con conn.info.get_parameters(): psycopg omette la password,
    quindi con autenticazione a password la connessione propria non puo' autenticarsi (ogni scrittura persa in silenzio)."""
    c = psycopg.connect("host=127.0.0.1 user=root dbname=postgres password=non-un-segreto-reale")
    assert "password" in c.info.get_parameters()


# ---- G8: SECURITY DEFINER e trace_id tra tenant -------------------------------------------------------------
def test_G8a_tenant_puo_creare_una_traccia_con_il_trace_id_di_un_altro_e_bloccargli_i_segmenti(admin_conn, prod_variables, key_provider, partitions):
    """atteso: FAIL. start_trace non usa il controllo cross-tenant: A crea una riga con il trace_id di B; da quel momento
    i segmenti di B su quel trace_id sono rifiutati (la funzione vede 'traccia di un altro tenant')."""
    sink = InMemorySignalSink()
    h = helper(prod_variables, sink, key_provider)
    a, b, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=b, run_id="run-b", root_kind="agent", started_at=NOW()))
    h.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=a, run_id="run-a", root_kind="agent", started_at=NOW()))
    s = seg("agent", {"gen_ai.agent.id": "agent_b"}, tenant=b, trace=tid)
    h.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id) is not None, "segmento legittimo di B rifiutato per colpa della traccia di A"


def test_G8b_oracolo_di_esistenza_della_funzione_security_definer(admin_conn, partitions, prod_variables, key_provider):
    """atteso: FAIL (rilievo minore). Un writer del tenant X chiede se un trace_id esiste presso un altro tenant,
    passando un p_tenant_id arbitrario (non legato al GUC di sessione): oracolo di esistenza cross-tenant."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    victim, tid = uuid.uuid4(), uuid.uuid4()
    h.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=victim, run_id="run-v", root_kind="agent", started_at=NOW()))
    attacker = uuid.uuid4()
    with writer_transaction(admin_conn, str(attacker)) as c, c.cursor() as cur:
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s, %s)", (str(tid), str(uuid.uuid4())))
        exists_elsewhere = cur.fetchone()[0]
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s, %s)", (str(uuid.uuid4()), str(uuid.uuid4())))
        random_id = cur.fetchone()[0]
    assert not (exists_elsewhere and not random_id), "la funzione distingue trace_id esistenti da inesistenti per qualunque chiamante"


def test_G8c_funzione_definer_dipende_dall_owner_bypassrls(admin_conn, partitions, prod_variables, key_provider):
    """atteso: FAIL (dedotto per il caso di produzione con owner non superuser). Le tabelle hanno FORCE RLS: una funzione
    SECURITY DEFINER il cui owner non e' superuser/BYPASSRLS e' soggetta alle policy. Qui si esegue lo STESSO SELECT della
    funzione sotto RLS (ruolo writer, tenant B): non vede la traccia del tenant A => con un owner non superuser la funzione
    tornerebbe false e il controllo cross-tenant sarebbe inefficace. La migrazione non crea un owner dedicato BYPASSRLS ne'
    verifica chi sia l'owner (qui e' `root`, superuser: il controllo funziona solo per questo)."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    a, b, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    h.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=a, run_id="run-a", root_kind="agent", started_at=NOW()))
    with writer_transaction(admin_conn, str(b)) as c, c.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM gravya_traces WHERE trace_id=%s AND tenant_id <> %s)", (str(tid), str(b)))
        under_rls = cur.fetchone()[0]
    assert under_rls is True, "sotto RLS (owner non superuser) il SELECT della funzione non vede la traccia dell'altro tenant"


# ---- G9: guardia di produzione spegnibile dal codice ------------------------------------------------------
def test_G9_production_override_false_non_deve_spegnere_la_guardia_di_produzione(monkeypatch, signal_sink, key_provider):
    """atteso: FAIL. Con API_ENV=production, SnapshotVariableRegistry(production_override=False) accetta le variabili
    'da definire' (guardia spenta da codice applicativo). Nessun test fisso richiede il caso override=False in produzione."""
    monkeypatch.setenv("API_ENV", "production")
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, production_override=False)
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, key_provider, production_override=False)


# ---- G10: writer_transaction (positivi) ---------------------------------------------------------------------
def test_G10_writer_transaction_ripristina_dopo_eccezione_nella_transazione_del_chiamante(admin_conn, partitions):
    """atteso: PASS (tentativo di rottura fallito)."""
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1")
    with pytest.raises(psycopg.errors.Error):
        with writer_transaction(admin_conn, str(uuid.uuid4()), statement_timeout_ms=1500) as c, c.cursor() as cur:
            cur.execute("SELECT 1/0")
    with admin_conn.cursor() as cur:
        cur.execute("SELECT current_user, current_setting('app.tenant_id', true), current_setting('statement_timeout')")
        u, g, t = cur.fetchone()
    assert u == "root" and g in (None, "") and t == "0"


# ---- G11: DB (positivi) -----------------------------------------------------------------------------------------
def test_G11_trigger_e_privilegi_di_colonna(admin_conn, partitions, prod_variables, key_provider):
    """atteso: PASS. UPDATE su riga chiusa rifiutato dal DB; UPDATE su tenant_id negato; trigger presente sulle partizioni."""
    h = helper(prod_variables, InMemorySignalSink(), key_provider)
    t, tid = uuid.uuid4(), uuid.uuid4()
    h.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=t, run_id="run-1", root_kind="agent", started_at=NOW()))
    with admin_conn.cursor() as cur:
        cur.execute("UPDATE gravya_traces SET ended_at=now() WHERE trace_id=%s", (str(tid),))
    admin_conn.commit()
    with pytest.raises(psycopg.errors.IntegrityConstraintViolation):
        with writer_transaction(admin_conn, str(t)) as c, c.cursor() as cur:
            cur.execute("UPDATE gravya_traces SET status='failed' WHERE trace_id=%s", (str(tid),))
    admin_conn.rollback()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with writer_transaction(admin_conn, str(t)) as c, c.cursor() as cur:
            cur.execute("UPDATE gravya_traces SET tenant_id=%s WHERE trace_id=%s", (str(uuid.uuid4()), str(tid)))
    admin_conn.rollback()
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM pg_trigger WHERE tgname='no_update_after_close' AND NOT tgisinternal")
        assert cur.fetchone()[0] >= 2


# ---- G12: partizioni con TimeZone non UTC ---------------------------------------------------------------------
def test_G12_ensure_partition_con_timezone_di_sessione_non_utc(admin_conn, prod_variables):
    """atteso: FAIL. pg_get_expr mostra i confini nel TimeZone della sessione ('2031-07-01 02:00:00+02'): il codice usa
    [:19] come se fossero UTC. Un timestamp UTC entro 2 ore dall'inizio del mese viene considerato non coperto."""
    from gravya_e1.partitions import ensure_partition
    admin_conn.execute("SET TimeZone = 'Europe/Rome'")
    first = datetime(2031, 7, 10, tzinfo=timezone.utc)
    name1 = ensure_partition(admin_conn, "gravya_traces", first, prod_variables)
    near_start = datetime(2031, 7, 1, 0, 30, tzinfo=timezone.utc)   # appartiene alla stessa partizione di luglio (UTC)
    name2 = ensure_partition(admin_conn, "gravya_traces", near_start, prod_variables)
    assert name2 == name1, (name1, name2)


# ---- G13: tipo atteso per variabile ---------------------------------------------------------------------------
@pytest.mark.parametrize("var,val", [("e1.write_buffer_size", "abc"), ("e1.write_statement_timeout_ms", "abc"),
                                     ("e1.write_buffer_size", 0), ("e1.write_statement_timeout_ms", 0)])
def test_G13_valore_di_tipo_o_intervallo_inatteso_blocca_con_errore_tipizzato_e_segnale(make_registry, signal_sink, key_provider, var, val):
    """atteso: FAIL. L'interfaccia accetta qualunque scalare: 'abc' provoca TypeError (non VariableUnavailableError, senza segnale);
    0 e' accettato (statement_timeout=0 in PostgreSQL = nessun timeout; buffer 0 corretto in silenzio a 1 da max(1, ...))."""
    reg = make_registry({var: {"value": val, "unit": "x", "status": "deciso"}})
    try:
        TracingHelper(reg, signal_sink, key_provider, production_override=True)
        raise AssertionError("avvio consentito con valore non valido")
    except VariableUnavailableError:
        pass
    assert any(s.kind.startswith("e5.variable_invalid") for s in signal_sink.signals)


# ---- G14: test del criterio 5 e accoppiamento alla connessione del chiamante ---------------------------------------
def test_G14a_connessione_chiusa_del_chiamante_perde_la_traccia_anche_con_db_sano(prod_variables, key_provider, partitions):
    """atteso: FAIL. Il DB e' sano: la perdita e' causata solo dal fatto che il chiamante passa una connessione chiusa
    (il primo uso di conn.info.get_parameters() fallisce). E' il caso che il test del criterio 5 simula: non e' una 'scrittura
    di traccia non riuscita' ma un parametro sbagliato. La perdita non dipende dallo stato reale del DB."""
    sink = InMemorySignalSink()
    h = helper(prod_variables, sink, key_provider)
    broken = psycopg.connect(f"dbname={DB}"); broken.close()
    h.start_segment(broken, seg("agent", {"gen_ai.agent.id": "agent_a"}))
    assert h.loss_count == 0, "perdita con DB sano: accoppiata alla connessione del chiamante"


def test_G14b_scrittura_realmente_fallita_e_fail_open_e_poi_si_riprende(admin_conn, prod_variables, key_provider, partitions):
    """atteso: PASS. Backend terminato: perdita contata, nessuna eccezione; la scrittura successiva riconnette e riesce."""
    sink = InMemorySignalSink()
    h = helper(prod_variables, sink, key_provider)
    h.start_segment(admin_conn, seg("agent", {"gen_ai.agent.id": "agent_a"}))
    with psycopg.connect(f"dbname={DB}", autocommit=True) as k:
        k.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname=%s "
                  "AND application_name='' AND pid <> %s", (DB, admin_conn.info.backend_pid))
    h.start_segment(admin_conn, seg("agent", {"gen_ai.agent.id": "agent_a"}))
    assert h.loss_count >= 1 and "trace.write_failed" in sink.kinds()
    s = seg("agent", {"gen_ai.agent.id": "agent_a"})
    h.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id) is not None


def test_G14c_nessuna_partizione_perdita_contata(admin_conn, prod_variables, key_provider, partitions):
    """atteso: PASS. started_at senza partizione: perdita contata e segnalata, nessuna eccezione."""
    sink = InMemorySignalSink()
    h = helper(prod_variables, sink, key_provider)
    s = SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), kind="agent",
                     started_at=datetime(2099, 1, 1, tzinfo=timezone.utc), attributes={})
    h.start_segment(admin_conn, s)
    assert h.loss_count == 1


# ---- G15/G16: tabella dei segnali, contesto del tenant -----------------------------------------------------------
def test_G15_tabella_segnali_il_writer_non_deve_avere_select(admin_conn):
    """atteso: FAIL. DECISIONS (2026-11-05): tabella dei segnali provvisoria, 'solo inserimento'. Il writer ha ancora SELECT."""
    with admin_conn.cursor() as cur:
        cur.execute("SELECT has_table_privilege('gravya_writer','gravya_signals_min_audit','SELECT')")
        assert cur.fetchone()[0] is False


def test_G15b_sink_postgres_non_scrive_come_writer(admin_conn):
    """atteso: FAIL (minore). Con RLS forzata il sink (che non imposta app.tenant_id) funziona solo come superuser:
    come writer l'INSERT di un segnale con tenant e' rifiutato dal WITH CHECK."""
    rejected = False
    try:
        with admin_conn.transaction():
            admin_conn.execute("SET LOCAL ROLE gravya_writer")
            admin_conn.execute("INSERT INTO gravya_signals_min_audit (id, kind, tenant_id, payload) VALUES (%s,'x',%s,'{}')",
                               (str(uuid.uuid4()), str(uuid.uuid4())))
    except psycopg.errors.InsufficientPrivilege:
        rejected = True
    admin_conn.rollback()
    assert not rejected, "INSERT di un segnale come writer rifiutato dal WITH CHECK: il sink e' usabile solo da superuser"


def test_G16_helper_non_ha_un_contesto_di_tenant_proprio():
    """atteso: FAIL. E1 §6: segmento con tenant diverso dal contesto 'rifiutato dal WITH CHECK e dall'helper'. L'helper non
    ha alcun contesto: tenant_id arriva dal modello e lo stesso valore imposta il GUC, quindi WITH CHECK e' sempre soddisfatto."""
    import inspect
    params = set(inspect.signature(TracingHelper.__init__).parameters) | set(inspect.signature(TracingHelper.start_segment).parameters)
    assert any("tenant" in p or "context" in p for p in params), sorted(params)


# ---- G17: log di ripiego -----------------------------------------------------------------------------------------
def test_G17_log_di_ripiego_riporta_il_nome_dell_evento(caplog):
    """atteso: FAIL. Il campo 'event' passa solo in `extra`, non nel messaggio: con la configurazione di default
    il log e' 'segnale_non_scrivibile' senza evento ne' tenant."""
    import logging
    from gravya_e1.signals import log_fallback
    caplog.set_level(logging.WARNING, logger="gravya_e1.signals_fallback")
    log_fallback("trace.write_failed", tenant_id="t", table="gravya_traces", count=1)
    assert any("trace.write_failed" in r.getMessage() for r in caplog.records)


def test_G17b_log_di_ripiego_con_campo_name_non_deve_sparire(caplog):
    """atteso: FAIL (latente). 'name' e' ammesso in ALLOWED_SIGNAL_FIELDS ma e' un attributo riservato di LogRecord:
    extra={'name':...} solleva KeyError, inghiottito dal ripiego di ultima istanza: nessun log."""
    import logging
    from gravya_e1.signals import log_fallback
    caplog.set_level(logging.WARNING, logger="gravya_e1.signals_fallback")
    log_fallback("e5.variable_unreadable", name="e1.write_buffer_size", reason="x")
    assert caplog.records


def test_G18_nome_di_chiave_scartata_in_formato_puntato_porta_contenuto(admin_conn, prod_variables, key_provider, partitions):
    """atteso: FAIL (minore). Il nome della chiave scartata e' riportato se e' 'puntato minuscolo <=64': una frase in minuscolo
    con punti al posto degli spazi passa e finisce nel segnale (qui InMemory: payload['key'])."""
    sink = InMemorySignalSink()
    h = helper(prod_variables, sink, key_provider)
    key = "il.cliente.mario.rossi.chiede.il.rimborso.della.fattura"
    h.start_segment(admin_conn, seg("agent", {key: "x"}))
    reported = [s.payload.get("key") for s in sink.signals if s.kind == "trace.segment_attribute_discarded"]
    assert key not in reported, reported


def test_G19_helper_non_ha_un_modo_per_chiudere_la_connessione_propria():
    """atteso: FAIL (minore). Nessun close()/shutdown: la connessione propria resta aperta finche' vive il processo."""
    assert any(hasattr(TracingHelper, n) for n in ("close", "shutdown", "stop"))
