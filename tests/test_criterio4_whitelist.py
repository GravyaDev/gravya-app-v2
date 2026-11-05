"""Criterio 4: whitelist di chiavi e valori.

Nessun attributo fuori whitelist e nessun valore fuori formato viene
scritto, in particolare contenuti di prompt, risposte, argomenti o
risultati dei tool. In produzione l'attributo e' scartato e un segnale
arriva ad A5 con kind, chiave, motivo e conteggio: un valore sentinella nel
payload non compare in nessuna riga della tabella di audit (0 risultati).
In sviluppo/test lo stesso payload fa fallire la scrittura (§6).

Giro 3: la scrittura e' asincrona (coda + thread di sfondo): `flush()` prima
di interrogare il database.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from gravya_e1.models import SegmentStart
from gravya_e1.signals import PostgresSignalSink
from gravya_e1.tracing import AttributeRejectedError

SENTINEL = "SENTINELLA-PII-non-deve-comparire-mai-42f9"


def test_payload_con_testo_libero_fallisce_in_sviluppo(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now, make_helper):
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)
    tenant_id = uuid.uuid4()
    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=tenant_id,
        kind="llm",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gen_ai.provider.name": "openai",
            "gravya.prompt.rendered_text": f"Ciao, il mio numero di telefono e' {SENTINEL}",
        },
    )
    try:
        helper.start_segment(admin_conn, segment)
        raised = False
    except AttributeRejectedError:
        raised = True
    assert raised


def test_attributo_scartato_in_produzione_mai_nella_tabella_di_audit(
    admin_conn, variables, key_provider, ensure_partitions_now, make_helper
):
    """Giro 4 (CA G3-05): il nome della chiave scartata e' riportato per intero
    SOLO se e' una chiave nota della whitelist reale di E1 (qui
    `gen_ai.agent.id`, di valore non conforme); una chiave fuori whitelist
    (`gravya.prompt.rendered_text`, mai dichiarata: un tentativo di
    contrabbandare testo nel NOME della chiave) non viene mai riportata per
    intero, nemmeno nel segnale: solo la sua lunghezza."""
    signal_sink = PostgresSignalSink(admin_conn)
    helper = make_helper(variables, signal_sink, key_provider, production_override=True)
    tenant_id = uuid.uuid4()
    segment_id = uuid.uuid4()
    unknown_key = f"gravya.prompt.rendered_text_{SENTINEL}"
    segment = SegmentStart(
        segment_id=segment_id,
        trace_id=uuid.uuid4(),
        tenant_id=tenant_id,
        kind="agent",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gen_ai.agent.id": f"non conforme {SENTINEL}",  # chiave nota, valore fuori formato
            unknown_key: "x",  # chiave MAI dichiarata nella whitelist
        },
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment_id),)
        )
        row = cur.fetchone()
    assert row is not None
    assert "gen_ai.agent.id" not in row[0]
    assert unknown_key not in row[0]

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT payload FROM gravya_signals_min_audit "
            "WHERE kind = 'trace.segment_attribute_discarded' AND tenant_id = %s ORDER BY id",
            (str(tenant_id),),
        )
        signals = [r[0] for r in cur.fetchall()]
    assert len(signals) == 2
    by_reported_key = {p.get("key"): p for p in signals}
    assert "gen_ai.agent.id" in by_reported_key, "una chiave NOTA della whitelist deve essere riportata per intero"
    unknown_payload = by_reported_key[None]
    assert "key" not in unknown_payload or unknown_payload.get("key") is None
    assert unknown_payload["key_length"] == len(unknown_key)
    for payload in signals:
        assert "reason" in payload and "count" in payload
        assert SENTINEL not in str(payload)

    # Ricerca del valore sentinella: 0 risultati, ne' nei segmenti ne' nei segnali.
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM gravya_trace_segments WHERE attributes::text LIKE %s",
            (f"%{SENTINEL}%",),
        )
        count_segments = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*) FROM gravya_signals_min_audit WHERE payload::text LIKE %s",
            (f"%{SENTINEL}%",),
        )
        count_signals = cur.fetchone()[0]
    assert count_segments == 0
    assert count_signals == 0
