"""Riproduzioni dei rilievi del code-reviewer. Ogni test asserisce il comportamento CORRETTO
richiesto da E1 v1.6: un test che FALLISCE dimostra il difetto nel codice del branch.
Un test che PASSA e' un tentativo di rottura fallito (controllo positivo)."""
from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta

import psycopg
import pytest

from gravya_e1.db import writer_transaction
from gravya_e1.models import SegmentEnd, SegmentStart, TraceStart
from gravya_e1.partitions import partition_bounds
from gravya_e1.signals import InMemorySignalSink, PostgresSignalSink
from gravya_e1.tracing import AttributeRejectedError, TracingHelper
from gravya_e1 import whitelist as wl

SENT = "SENTINELLA-REVIEWER-9d3c"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def seg(kind, attrs, tenant=None, trace=None):
    return SegmentStart(segment_id=uuid.uuid4(), trace_id=trace or uuid.uuid4(), tenant_id=tenant or uuid.uuid4(),
                        kind=kind, started_at=NOW(), attributes=attrs)


def stored(conn, segment_id):
    with conn.cursor() as cur:
        cur.execute("SELECT attributes FROM gravya_trace_segments WHERE segment_id=%s", (str(segment_id),))
        r = cur.fetchone()
    return None if r is None else r[0]


# R1 -- valore fuori formato hash accettato (criterio 4: "nessun valore fuori formato")
@pytest.mark.parametrize("bad", [
    "0x" + "a" * 62,            # prefisso 0x
    "a_" * 31 + "ab",          # underscore interni (int() li accetta)
    " " + "a" * 62 + " ",       # spazi ai bordi
    "A" * 64,                   # maiuscolo (hexdigest e' minuscolo)
])
def test_R1_hash_fuori_formato_deve_essere_scartato(bad):
    assert wl.hash_hex(bad, 2048) is False


def test_R1b_hash_fuori_formato_scritto_in_db(admin_conn, variables, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    s = seg("llm", {"gravya.prompt.hash": " " + "a" * 62 + " "})
    helper.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id) == {}, "valore fuori formato scritto"


# R2 -- valore non hashable in gravya.decision.outcome: eccezione che esce dall'helper in produzione (rompe fail-open)
def test_R2_outcome_non_hashable_non_deve_far_crashare_l_esecuzione(admin_conn, prod_variables, key_provider, partitions):
    sink = InMemorySignalSink()
    helper = TracingHelper(prod_variables, sink, key_provider, production_override=True)
    s = seg("decision", {"gravya.decision.kind": "policy", "gravya.decision.outcome": ["allow"]})
    helper.start_segment(admin_conn, s)  # deve scartare e segnalare, non sollevare
    assert stored(admin_conn, s.segment_id) == {}


# R3 -- se la destinazione dei segnali fallisce, il fallimento si propaga all'esecuzione (fail-open rotto)
def test_R3_segnale_non_scrivibile_non_deve_bloccare_l_esecuzione(prod_variables, key_provider):
    broken = psycopg.connect("dbname=gravya_e1_review"); broken.close()
    helper = TracingHelper(prod_variables, PostgresSignalSink(broken), key_provider, production_override=True)
    s = seg("agent", {"gen_ai.agent.id": "a1"})
    helper.start_segment(broken, s)  # DB giu': traccia persa + segnale non scrivibile -> deve proseguire


# R4 -- il NOME della chiave scartata (contenuto arbitrario del chiamante) finisce nella tabella di audit
def test_R4_nome_chiave_scartata_non_deve_portare_contenuto_in_audit(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, PostgresSignalSink(admin_conn), key_provider, production_override=True)
    s = seg("llm", {f"Il cliente Mario Rossi chiede {SENT}": "x"})
    helper.start_segment(admin_conn, s)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_signals_min_audit WHERE payload::text LIKE %s", (f"%{SENT}%",))
        assert cur.fetchone()[0] == 0, "contenuto nel nome della chiave scritto nell'audit"


# R5 -- SHA-256 semplice degli argomenti (non HMAC), senza key_ref, accettato come gravya.tool.args_hash
def test_R5_hash_non_hmac_senza_chiave_non_deve_essere_scritto(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    plain = hashlib.sha256(b'{"email": "mario.rossi@example.com"}').hexdigest()
    s = seg("tool", {"gen_ai.tool.name": "send-email", "gravya.tool.args_hash": plain})  # nessuna chiave per il tenant
    helper.start_segment(admin_conn, s)
    attrs = stored(admin_conn, s.segment_id)
    assert "gravya.tool.args_hash" not in attrs, "SHA-256 semplice di argomenti PII scritto senza chiave del tenant"


# R6 -- hash del render in gravya.prompt.hash accettato (limite dichiarato dall'implementer; il test del branch non lo copre)
def test_R6_hash_del_render_in_prompt_hash(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    render_hash = hashlib.sha256("Ciao Mario Rossi, mario.rossi@example.com".encode()).hexdigest()
    s = seg("llm", {"gravya.prompt.hash": render_hash})
    helper.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id).get("gravya.prompt.hash") != render_hash


# R7 -- segmento chiuso modificabile; kind di end_segment non verificato
def test_R7a_segmento_chiuso_non_modificabile(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    t = uuid.uuid4(); s = seg("agent", {"gen_ai.agent.id": "a1"}, tenant=t)
    helper.start_segment(admin_conn, s)
    helper.end_segment(admin_conn, SegmentEnd(segment_id=s.segment_id, tenant_id=t, ended_at=NOW(), status="ok"), "agent")
    helper.end_segment(admin_conn, SegmentEnd(segment_id=s.segment_id, tenant_id=t, ended_at=NOW(), status="error"), "agent")
    with admin_conn.cursor() as cur:
        cur.execute("SELECT status FROM gravya_trace_segments WHERE segment_id=%s", (str(s.segment_id),))
        assert cur.fetchone()[0] == "ok", "segmento chiuso riscritto (E1 §6/§7: nessuna modifica dopo la chiusura)"


def test_R7b_end_segment_kind_sbagliato_scrive_attributi_di_un_altro_kind(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    t = uuid.uuid4(); s = seg("agent", {"gen_ai.agent.id": "a1"}, tenant=t)
    helper.start_segment(admin_conn, s)
    helper.end_segment(admin_conn, SegmentEnd(segment_id=s.segment_id, tenant_id=t, ended_at=NOW(), status="ok",
                       attributes={"gravya.decision.kind": "policy"}), "decision")
    assert "gravya.decision.kind" not in stored(admin_conn, s.segment_id), "attributo di decision scritto in un segmento agent"


# R8 -- DB lento: la scrittura e' sincrona, nessun buffer/timeout; il run resta bloccato
def test_R8_db_lento_non_deve_bloccare_l_esecuzione(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    locker = psycopg.connect("dbname=gravya_e1_review")
    with locker.cursor() as cur:
        cur.execute("SELECT c.relname FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid "
                    "JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='gravya_trace_segments' LIMIT 1")
        part = cur.fetchone()[0]
        cur.execute(f"LOCK TABLE {part} IN ACCESS EXCLUSIVE MODE")  # simula DB lento/bloccato
    done = threading.Event()
    def run():
        c = psycopg.connect("dbname=gravya_e1_review")
        helper.start_segment(c, seg("agent", {"gen_ai.agent.id": "a1"}))
        done.set(); c.close()
    th = threading.Thread(target=run, daemon=True); th.start()
    finished = done.wait(timeout=3)
    locker.rollback(); locker.close(); th.join(10)
    assert finished, "start_segment bloccato >3s: nessun buffer asincrono ne' timeout (E1 §5/§6)"


def test_R8b_write_buffer_size_letto_ma_mai_usato():
    import inspect, gravya_e1.tracing as t
    src = inspect.getsource(t)
    assert src.count("_write_buffer_size") > 1, "e1.write_buffer_size e' letto in __init__ ma non usato altrove"


# R9 -- 'identificativo opaco' accetta PII-like e URL-like
@pytest.mark.parametrize("v", ["RSSMRA80A01H501U", "3331234567", "mario.rossi", "IT60X0542811101000000123456", "A" * 2000])
def test_R9_opaque_id_non_deve_accettare_dati_personali_o_testo_codificato(v):
    assert wl.opaque_id(v, 2048) is False


@pytest.mark.parametrize("v", ["api.openai.com/v1/chat/completions", "www.example.com", "10.0.0.1:8080/x"])
def test_R9b_destination_non_deve_accettare_url_senza_schema(v):
    assert wl.destination_id(v, 2048) is False


# R10 -- ruolo/RLS: controlli positivi (tentativi di rottura falliti)
def test_R10a_rls_su_segmenti_isolamento_e_with_check(admin_conn, partitions):
    ta, tb = uuid.uuid4(), uuid.uuid4(); sid = uuid.uuid4()
    with writer_transaction(admin_conn, str(ta)) as c, c.cursor() as cur:
        cur.execute("INSERT INTO gravya_trace_segments (segment_id,trace_id,tenant_id,kind,started_at,redaction_version) "
                    "VALUES (%s,%s,%s,'agent',%s,1)", (str(sid), str(uuid.uuid4()), str(ta), NOW()))
    with writer_transaction(admin_conn, str(tb)) as c, c.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_trace_segments WHERE segment_id=%s", (str(sid),))
        assert cur.fetchone()[0] == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with writer_transaction(admin_conn, str(tb)) as c, c.cursor() as cur:
            cur.execute("INSERT INTO gravya_trace_segments (segment_id,trace_id,tenant_id,kind,started_at,redaction_version) "
                        "VALUES (%s,%s,%s,'agent',%s,1)", (str(uuid.uuid4()), str(uuid.uuid4()), str(ta), NOW()))
    admin_conn.rollback()


def test_R10b_writer_non_accede_direttamente_alle_partizioni(admin_conn, partitions):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with writer_transaction(admin_conn, str(uuid.uuid4())) as c, c.cursor() as cur:
            cur.execute("SELECT relname FROM pg_class WHERE relname LIKE 'gravya_traces_p%' LIMIT 1")
            # nome partizione letto dal catalogo (leggibile); lettura diretta: deve essere negata
            name = cur.fetchone()[0]
            cur.execute(f"SELECT count(*) FROM {name}")
    admin_conn.rollback()


def test_R10c_update_cross_tenant_non_ha_effetto(admin_conn, partitions):
    ta, tb = uuid.uuid4(), uuid.uuid4(); tid = uuid.uuid4()
    with writer_transaction(admin_conn, str(ta)) as c, c.cursor() as cur:
        cur.execute("INSERT INTO gravya_traces (trace_id,tenant_id,run_id,root_kind,started_at) VALUES (%s,%s,'r','agent',%s)",
                    (str(tid), str(ta), NOW()))
    with writer_transaction(admin_conn, str(tb)) as c, c.cursor() as cur:
        cur.execute("UPDATE gravya_traces SET status='hacked' WHERE trace_id=%s", (str(tid),))
        assert cur.rowcount == 0
        cur.execute("DELETE FROM gravya_traces WHERE trace_id=%s", (str(tid),)) if False else None


def test_R10d_writer_non_puo_leggere_segnali_di_tutti_i_tenant(admin_conn, partitions):
    # tabella provvisoria senza RLS: il writer (multi-tenant) legge i segnali di ogni tenant
    sink = PostgresSignalSink(admin_conn); sink.emit("trace.write_failed", tenant_id=str(uuid.uuid4()), count=1)
    with writer_transaction(admin_conn, str(uuid.uuid4())) as c, c.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_signals_min_audit")
        assert cur.fetchone()[0] == 0, "il writer del tenant X legge i segnali di altri tenant (nessuna RLS sulla tabella provvisoria)"


# R11 -- segmento di un tenant agganciato al trace_id di un altro tenant
def test_R11_segmento_con_trace_id_di_altro_tenant_deve_essere_rifiutato(admin_conn, prod_variables, key_provider, partitions):
    ta, tb = uuid.uuid4(), uuid.uuid4(); tid = uuid.uuid4()
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    helper.start_trace(admin_conn, TraceStart(trace_id=tid, tenant_id=ta, run_id="r", root_kind="agent", started_at=NOW()))
    s = seg("agent", {"gen_ai.agent.id": "x"}, tenant=tb, trace=tid)
    helper.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id) is None, "segmento di tenant B agganciato alla traccia di tenant A"


# R12 -- chiave HMAC vuota considerata 'valida'
def test_R12_chiave_vuota_non_e_una_chiave_valida(prod_variables, key_provider):
    t = str(uuid.uuid4()); key_provider.set_key(t, "v1", b"")
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    assert helper.hash_tool_args(t, b"x") is None


# R13 -- writer_transaction dentro una transazione gia' aperta: ruolo e tenant restano impostati nel chiamante
def test_R13_writer_transaction_non_deve_lasciare_ruolo_e_tenant_nella_transazione_del_chiamante(admin_conn, partitions):
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1")                      # transazione del chiamante gia' aperta (psycopg: autocommit off)
    t = uuid.uuid4()
    with writer_transaction(admin_conn, str(t)) as c, c.cursor() as cur:
        cur.execute("SELECT 1")
    with admin_conn.cursor() as cur:
        cur.execute("SELECT current_user, current_setting('app.tenant_id', true)")
        user, guc = cur.fetchone()
    assert user == "root" and guc in (None, ""), f"dopo la scrittura: current_user={user}, app.tenant_id={guc}"


def test_R13b_helper_in_transazione_del_chiamante_rompe_le_istruzioni_successive(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1")                      # es. B2: transazione unica con audit fail-closed
    helper.start_segment(admin_conn, seg("agent", {"gen_ai.agent.id": "a1"}))
    with admin_conn.cursor() as cur:                 # istruzione successiva del chiamante, come ruolo del chiamante
        cur.execute("SELECT count(*) FROM alembic_version")   # il writer non ha privilegi su questa tabella


# R14 -- partizioni
def test_R14a_partition_bounds_con_timestamp_non_utc():
    tz2 = timezone(timedelta(hours=2))
    ts = datetime(2031, 6, 1, 0, 30, tzinfo=tz2)         # = 2031-05-31 22:30 UTC
    start, end = partition_bounds(ts, 1)
    assert start <= ts.astimezone(timezone.utc) < end, f"[{start}, {end}) non contiene {ts.astimezone(timezone.utc)}"


def test_R14b_ensure_partition_con_intervallo_cambiato_dichiara_copertura_falsa(admin_conn, tmp_path, signal_sink):
    from gravya_e1.config.variables import SnapshotVariableRegistry
    from gravya_e1.partitions import ensure_partition
    def reg(m):
        p = tmp_path / f"s{m}.json"
        p.write_text(json.dumps({"variables": {"e1.partition_interval_months": {"value": m, "unit": "months", "status": "deciso"}}}))
        return SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=p, production_override=False)
    ensure_partition(admin_conn, "gravya_traces", datetime(2031, 3, 10, tzinfo=timezone.utc), reg(1))
    name = ensure_partition(admin_conn, "gravya_traces", datetime(2031, 4, 15, tzinfo=timezone.utc), reg(2))
    t = uuid.uuid4()
    # la funzione dice di aver garantito la partizione per aprile: inserire una riga di aprile deve funzionare
    with admin_conn.cursor() as cur:
        cur.execute("INSERT INTO gravya_traces (trace_id,tenant_id,run_id,root_kind,started_at) VALUES (%s,%s,'r','agent',%s)",
                    (str(uuid.uuid4()), str(t), datetime(2031, 4, 15, tzinfo=timezone.utc)))


# R15 -- guardia di produzione: tentativi
def test_R15_guardia_produzione_letta_da_ambiente_blocca_avvio(monkeypatch, signal_sink, key_provider):
    from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
    monkeypatch.setenv("API_ENV", "production")
    reg = SnapshotVariableRegistry(signal_sink=signal_sink)      # senza override: legge l'ambiente
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, key_provider)


def test_R15b_informativo_guardia_solo_valore_esatto_production(monkeypatch, signal_sink, key_provider):
    # NON e' un rilievo: l'invariante e' `API_ENV=production` esatto. Con 'Production' o API_ENV assente
    # l'helper parte come sviluppo (il valore di sviluppo e' ammesso): documentato come tentativo di rottura.
    from gravya_e1.config.variables import SnapshotVariableRegistry
    monkeypatch.setenv("API_ENV", "Production")
    reg = SnapshotVariableRegistry(signal_sink=signal_sink)
    TracingHelper(reg, signal_sink, key_provider)   # non solleva


# R16 -- controllo positivo: valore fuori formato in chiave ammessa NON arriva ne' al segmento ne' all'audit
def test_R16_valore_fuori_formato_in_chiave_ammessa_scartato(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, PostgresSignalSink(admin_conn), key_provider, production_override=True)
    s = seg("agent", {"gen_ai.agent.name": f"Mario Rossi chiede {SENT}-val"})
    helper.start_segment(admin_conn, s)
    assert stored(admin_conn, s.segment_id) == {}
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_signals_min_audit WHERE payload::text LIKE %s", (f"%{SENT}-val%",))
        assert cur.fetchone()[0] == 0


# R17 -- colonne fuori whitelist (name, status, run_id, workflow_id...) scritte senza alcuna validazione
def test_R17_name_e_status_testo_libero_non_devono_essere_scritti(admin_conn, prod_variables, key_provider, partitions):
    helper = TracingHelper(prod_variables, InMemorySignalSink(), key_provider, production_override=True)
    t = uuid.uuid4()
    s = SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=t, kind="llm", started_at=NOW(),
                     name=f"Riassumi la mail di Mario Rossi mario.rossi@example.com {SENT}-name",
                     attributes={})
    helper.start_segment(admin_conn, s)
    helper.end_segment(admin_conn, SegmentEnd(segment_id=s.segment_id, tenant_id=t, ended_at=NOW(),
                                              status=f"errore: telefono +39 333 1234567 {SENT}-status"), "llm")
    helper.start_trace(admin_conn, TraceStart(trace_id=uuid.uuid4(), tenant_id=t, root_kind="agent", started_at=NOW(),
                                              run_id=f"run per Mario Rossi {SENT}-run"))
    with admin_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM gravya_trace_segments WHERE name LIKE %s OR status LIKE %s", (f"%{SENT}%", f"%{SENT}%"))
        n_seg = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM gravya_traces WHERE run_id LIKE %s", (f"%{SENT}%",))
        n_tr = cur.fetchone()[0]
    assert (n_seg, n_tr) == (0, 0), f"testo libero scritto fuori whitelist: segmenti={n_seg}, tracce={n_tr}"


# R18 -- istantanea con struttura non valida: errore non tipizzato e nessun segnale (DX-17: blocca e segnala)
@pytest.mark.parametrize("snap", [{"variables": {"x.y": 5}}, {"variables": []}, [1, 2]])
def test_R18_istantanea_malformata_blocca_con_errore_tipizzato_e_segnale(tmp_path, signal_sink, snap):
    from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
    p = tmp_path / "s.json"; p.write_text(json.dumps(snap))
    try:
        SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=p, production_override=False).get("x.y")
    except VariableUnavailableError:
        pass
    assert signal_sink.signals, "nessun segnale prodotto (o eccezione non tipizzata)"
