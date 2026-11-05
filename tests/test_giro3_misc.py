"""Prove aggiuntive del giro 3 (bloccanti e rilievi del secondo BLOCCA).

Ogni funzione qui prova un'affermazione del report "Giro 3" che non era gia'
coperta da un test aggiornato dei criteri 1-18 o dalla suite di riproduzione
del code-reviewer.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

import psycopg
import pytest

from _pgconn import pg_dsn
from gravya_e1 import whitelist as wl
from gravya_e1.db import writer_transaction
from gravya_e1.models import SegmentEnd, SegmentStart, TraceStart
from gravya_e1.signals import log_fallback
from gravya_e1.tracing import AttributeRejectedError

TEST_DB = "gravya_e1_test"
NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


# --- G7: connessione propria con credenziale a password, mai dal chiamante ---


def test_helper_scrive_con_connessione_propria_a_password_via_tcp(
    variables, signal_sink, key_provider, make_helper, ensure_partitions_now, password_auth_conninfo
):
    """G7: l'helper non legge mai i parametri dalla connessione del chiamante.

    Prova diretta (sostituisce test_G7 della riproduzione, che verifica solo
    un fatto generale di psycopg, non il nostro codice): l'helper scrive
    davvero usando `conninfo` con autenticazione a password via TCP, mentre
    la connessione passata come `conn` ai metodi pubblici resta quella
    normale del test (senza password) e non viene mai usata per i parametri
    di connessione.
    """
    helper = make_helper(variables, signal_sink, key_provider, production_override=False, conninfo=password_auth_conninfo)
    caller_conn = psycopg.connect(pg_dsn(TEST_DB))  # connessione del chiamante: nessuna password, ignorata

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="agent",
        started_at=NOW(),
        attributes={"gen_ai.agent.id": "agent_1"},
    )
    helper.start_segment(caller_conn, segment)
    assert helper.flush(timeout=5)
    assert helper.loss_count == 0

    with caller_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),))
        assert cur.fetchone() is not None, "la scrittura con conninfo a password non e' arrivata al database"


# --- G8: la funzione SECURITY DEFINER ha un solo parametro e usa il GUC -----


def test_funzione_security_definer_ha_un_solo_parametro(admin_conn):
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT pg_get_function_identity_arguments(oid) FROM pg_proc WHERE proname = 'gravya_e1_trace_owned_by_other_tenant'"
        )
        signatures = {row[0] for row in cur.fetchall()}
    assert signatures == {"p_trace_id uuid"}, (
        f"la funzione ha {len(signatures)} firme ({signatures}): deve avere solo (uuid), senza p_tenant_id (G8)"
    )


def test_funzione_security_definer_usa_il_guc_non_un_parametro(admin_conn, ensure_partitions_now):
    """La funzione a un parametro legge il tenant dal GUC di sessione, non da un argomento."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    trace_id = uuid.uuid4()
    with writer_transaction(admin_conn, str(tenant_a)) as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at) VALUES (%s,%s,%s,'agent',%s)",
            (str(trace_id), str(tenant_a), str(uuid.uuid4()), NOW()),
        )
    # sessione di tenant_b: la funzione deve vedere che trace_id e' di un altro tenant (true)
    with writer_transaction(admin_conn, str(tenant_b)) as c, c.cursor() as cur:
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(trace_id),))
        assert cur.fetchone()[0] is True
    # sessione di tenant_a (lo stesso proprietario): non e' "di un altro tenant" (false)
    with writer_transaction(admin_conn, str(tenant_a)) as c, c.cursor() as cur:
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(trace_id),))
        assert cur.fetchone()[0] is False


def test_funzione_security_definer_bypassa_rls_sotto_ruolo_non_superuser(admin_conn, ensure_partitions_now):
    """G8c: a differenza di una SELECT diretta sotto RLS, la funzione reale (proprietario
    gravya_e1_so_owner, BYPASSRLS) vede la riga anche quando la sessione e' un writer non superuser."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    trace_id = uuid.uuid4()
    with writer_transaction(admin_conn, str(tenant_a)) as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO gravya_traces (trace_id, tenant_id, run_id, root_kind, started_at) VALUES (%s,%s,%s,'agent',%s)",
            (str(trace_id), str(tenant_a), str(uuid.uuid4()), NOW()),
        )
    with writer_transaction(admin_conn, str(tenant_b)) as c, c.cursor() as cur:
        cur.execute("SELECT current_user, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        current_user, _ = cur.fetchone()
        assert current_user == "gravya_writer"  # la sessione e' davvero il writer non superuser
        cur.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname = 'gravya_writer'")
        assert cur.fetchone()[0] is False  # il writer stesso non ha BYPASSRLS
        cur.execute("SELECT gravya_e1_trace_owned_by_other_tenant(%s)", (str(trace_id),))
        assert cur.fetchone()[0] is True, "la funzione non vede la riga: BYPASSRLS del proprietario non funziona"


# --- G16: contesto del tenant --------------------------------------------


def test_tenant_context_rifiuta_modello_con_tenant_diverso_in_sviluppo(variables, signal_sink, key_provider, make_helper):
    context_tenant = uuid.uuid4()
    helper = make_helper(variables, signal_sink, key_provider, production_override=False, tenant_context=str(context_tenant))
    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),  # diverso dal contesto
        kind="agent",
        started_at=NOW(),
        attributes={"gen_ai.agent.id": "agent_1"},
    )
    with pytest.raises(AttributeRejectedError):
        helper.start_segment(None, segment)


def test_tenant_context_scarta_con_segnale_in_produzione(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    context_tenant = uuid.uuid4()
    other_tenant = uuid.uuid4()
    helper = make_helper(variables, signal_sink, key_provider, production_override=True, tenant_context=str(context_tenant))
    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=other_tenant,
        kind="agent",
        started_at=NOW(),
        attributes={"gen_ai.agent.id": "agent_1"},
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),))
        assert cur.fetchone() is None
    assert "trace.tenant_context_mismatch" in signal_sink.kinds()


def test_tenant_context_accetta_modello_con_lo_stesso_tenant(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    context_tenant = uuid.uuid4()
    helper = make_helper(variables, signal_sink, key_provider, production_override=False, tenant_context=str(context_tenant))
    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=context_tenant,
        kind="agent",
        started_at=NOW(),
        attributes={"gen_ai.agent.id": "agent_1"},
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),))
        assert cur.fetchone() is not None


# --- G6: kind sconosciuto non deve sollevare in produzione ------------------


def test_end_segment_kind_sconosciuto_non_solleva_in_produzione(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    helper = make_helper(variables, signal_sink, key_provider, production_override=True)
    helper.end_segment(
        admin_conn,
        SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"),
        "kind_sconosciuto_bogus",
    )  # non deve sollevare
    assert helper.flush(timeout=5)  # giro 4: i segnali sono asincroni (coda propria, G3-01)
    assert "trace.segment_attribute_discarded" in signal_sink.kinds()


def test_end_segment_kind_sconosciuto_solleva_in_sviluppo(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    with pytest.raises(AttributeRejectedError):
        helper.end_segment(
            admin_conn,
            SegmentEnd(segment_id=uuid.uuid4(), tenant_id=uuid.uuid4(), ended_at=NOW(), status="ok"),
            "kind_sconosciuto_bogus",
        )


# --- G9: production_override puo' solo irrigidire -------------------------


def test_production_override_false_non_spegne_la_guardia(monkeypatch, signal_sink, key_provider):
    from gravya_e1.config.variables import SnapshotVariableRegistry, VariableUnavailableError
    from gravya_e1.tracing import TracingHelper

    monkeypatch.setenv("API_ENV", "production")
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, production_override=False)
    with pytest.raises(VariableUnavailableError):
        TracingHelper(reg, signal_sink, key_provider, production_override=False)


# --- G4/G5: coda non bloccante, flush, close, buffer pieno ------------------


def test_dopo_start_segment_la_riga_non_e_necessariamente_scritta(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    """G4a: a differenza di una scrittura sincrona, subito dopo il ritorno di
    start_segment la coda puo' non aver ancora processato la riga."""
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    locker = psycopg.connect(pg_dsn(TEST_DB))
    with locker.cursor() as cur:
        cur.execute(
            "SELECT c.relname FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid "
            "JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='gravya_trace_segments' ORDER BY 1 LIMIT 1"
        )
        part = cur.fetchone()[0]
        cur.execute(f"LOCK TABLE {part} IN ACCESS EXCLUSIVE MODE")
    try:
        segment = SegmentStart(
            segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), kind="agent",
            started_at=NOW(), attributes={"gen_ai.agent.id": "agent_1"},
        )
        start = time.perf_counter()
        helper.start_segment(admin_conn, segment)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"start_segment ha aspettato {elapsed:.3f}s: non e' solo validazione+accodamento"
        # Non si interroga la tabella bloccata qui: con ACCESS EXCLUSIVE
        # tenuto da `locker`, anche una semplice SELECT resterebbe in attesa
        # (ogni lettura e' incompatibile con ACCESS EXCLUSIVE), bloccando
        # questo stesso test invece di dimostrare l'asincronia.
    finally:
        locker.rollback()
        locker.close()
    assert helper.flush(timeout=5)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),))
        assert cur.fetchone() is not None, "dopo flush() la riga deve essere scritta"


def test_coda_piena_perdita_contata_senza_attesa(signal_sink, key_provider, tmp_path):
    """G4: con la coda piena, una nuova scrittura e' una perdita immediata, senza attesa."""
    import json

    from _e1vars import snapshot_with
    from gravya_e1.config.variables import SnapshotVariableRegistry
    from gravya_e1.tracing import TracingHelper

    # Giro 4 (CR N13): `tmp_path` (cancellato da pytest), mai un file in /tmp.
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot_with({"e1.write_buffer_size": {"value": 1, "unit": "count", "status": "deciso"}})))
    reg = SnapshotVariableRegistry(signal_sink=signal_sink, snapshot_path=path, production_override=False)

    # conninfo verso una porta che non risponde: il thread di sfondo resta
    # occupato a lungo nel connect_timeout, cosi' la coda (dimensione 1) si
    # riempie subito con la prima scrittura.
    helper = TracingHelper(
        reg, signal_sink, key_provider, production_override=False,
        conninfo="host=127.0.0.1 port=1 connect_timeout=5 dbname=postgres user=root",
    )
    try:
        seg1 = SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), kind="agent",
                            started_at=NOW(), attributes={"gen_ai.agent.id": "agent_1"})
        seg2 = SegmentStart(segment_id=uuid.uuid4(), trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), kind="agent",
                            started_at=NOW(), attributes={"gen_ai.agent.id": "agent_1"})
        start = time.perf_counter()
        helper.start_segment(None, seg1)  # occupa il worker (connessione lenta)
        helper.start_segment(None, seg2)  # la coda (size=1) e' gia' piena: perdita immediata
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"start_segment con coda piena ha aspettato {elapsed:.3f}s"
        assert helper.loss_count >= 1
    finally:
        helper.close(timeout=1)


def test_close_ferma_il_thread_e_la_connessione(variables, signal_sink, key_provider):
    from gravya_e1.tracing import TracingHelper

    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False, conninfo=pg_dsn(TEST_DB))
    assert hasattr(helper, "close")
    assert hasattr(helper, "flush")
    helper.close(timeout=5)
    assert helper._worker_thread.is_alive() is False


# --- G17/G17b: log di ripiego ------------------------------------------------


def test_log_fallback_riporta_evento_e_tenant_nel_messaggio(caplog):
    caplog.set_level(logging.WARNING, logger="gravya_e1.signals_fallback")
    log_fallback("trace.write_failed", tenant_id="t-123", table="gravya_traces", count=1)
    assert any("trace.write_failed" in r.getMessage() and "t-123" in r.getMessage() for r in caplog.records)


def test_log_fallback_con_campo_name_non_perde_il_log(caplog):
    """G17b: 'name' e' un attributo riservato di LogRecord: non deve essere passato come extra."""
    caplog.set_level(logging.WARNING, logger="gravya_e1.signals_fallback")
    log_fallback("e5.variable_unreadable", name="e1.write_buffer_size", reason="assente")
    assert caplog.records, "nessun log scritto: il campo 'name' ha fatto fallire log_fallback"


# --- G18: nome della chiave scartata, segmenti limitati ---------------------


def test_nome_chiave_con_troppi_segmenti_non_e_riportato():
    key = "il.cliente.mario.rossi.chiede.il.rimborso.della.fattura"
    name, length = wl.safe_signal_key_name(key)
    assert name is None
    assert length == len(key)


def test_nome_chiave_whitelist_reale_e_riportato():
    name, _ = wl.safe_signal_key_name("gen_ai.tool.call.id")
    assert name == "gen_ai.tool.call.id"


# --- formati decisi nel giro 3: run_id e reviewer_ref -----------------------


def test_run_id_non_uuid_rifiutato_in_sviluppo(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    trace = TraceStart(trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), run_id="mario_rossi", root_kind="agent", started_at=NOW())
    with pytest.raises(AttributeRejectedError):
        helper.start_trace(admin_conn, trace)


def test_run_id_uuid_canonico_accettato(admin_conn, variables, signal_sink, key_provider, make_helper, ensure_partitions_now):
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    trace = TraceStart(trace_id=uuid.uuid4(), tenant_id=uuid.uuid4(), run_id=str(uuid.uuid4()), root_kind="agent", started_at=NOW())
    helper.start_trace(admin_conn, trace)
    assert helper.flush(timeout=5)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM gravya_traces WHERE trace_id = %s", (str(trace.trace_id),))
        assert cur.fetchone() is not None


@pytest.mark.parametrize("bad", ["mario_rossi", "reviewer_not-a-uuid", "reviewer_", "prefix_" + "1" * 36])
def test_reviewer_ref_rifiuta_non_uuid_con_prefisso(bad):
    assert wl.reviewer_ref_format(bad, 2048) is False


def test_reviewer_ref_accetta_prefisso_piu_uuid_canonico():
    value = "reviewer_" + str(uuid.uuid4())
    assert wl.reviewer_ref_format(value, 2048) is True
