"""Criterio 11: negli segmenti tool e decision gli argomenti compaiono solo
come HMAC, mai in chiaro: test con argomenti contenenti PII.

Giro 2 (CR R5/R6, non tautologico): l'helper calcola lui stesso l'HMAC a
partire dagli argomenti grezzi (`raw_arguments`); un hash gia' calcolato dal
chiamante (anche un HMAC corretto, o un SHA-256 semplice) passato come
`gravya.tool.args_hash`/`gravya.decision.args_hash` viene scartato (B6): lo
dimostriamo esplicitamente, non solo verificando che il PII non compaia.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

from gravya_e1.hashing import compute_args_hmac
from gravya_e1.models import SegmentStart

PII_ARGS = {"email": "mario.rossi@example.com", "telefono": "+39 333 1234567"}


def test_tool_args_solo_hmac_calcolato_dall_helper(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now, make_helper):
    tenant_id = str(uuid.uuid4())
    key_bytes = b"chiave-di-prova-sintetica-non-un-segreto-reale!"
    key_provider.set_key(tenant_id, "v1", key_bytes)
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)

    raw = json.dumps(PII_ARGS, sort_keys=True).encode("utf-8")
    expected_digest, expected_ref = compute_args_hmac(key_provider, tenant_id, raw)

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        kind="tool",
        started_at=datetime.now(timezone.utc),
        attributes={"gen_ai.tool.name": "tool_sendemail", "gen_ai.tool.call.id": "call_1"},
        raw_arguments=raw,
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]

    # L'hash memorizzato e' esattamente quello calcolato dall'helper con la
    # chiave del tenant (non un hash qualunque a 64 cifre esadecimali: e'
    # verificato ricalcolandolo in modo indipendente, criterio 15).
    assert attrs["gravya.tool.args_hash"] == expected_digest
    assert attrs["gravya.hash.key_ref"] == expected_ref
    independent = hmac.new(key_bytes, raw, hashlib.sha256).hexdigest()
    assert attrs["gravya.tool.args_hash"] == independent

    for pii_value in PII_ARGS.values():
        assert pii_value not in json.dumps(attrs)
    assert "email" not in attrs


def test_tool_args_hash_fornito_dal_chiamante_e_scartato(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now, make_helper):
    """B6: un hash gia' calcolato dal chiamante (anche un semplice SHA-256) non e' accettato."""
    tenant_id = str(uuid.uuid4())
    key_provider.set_key(tenant_id, "v1", b"chiave-di-prova-sintetica-non-un-segreto-reale!")
    helper = make_helper(variables, signal_sink, key_provider, production_override=True)

    raw = json.dumps(PII_ARGS, sort_keys=True).encode("utf-8")
    plain_sha256 = hashlib.sha256(raw).hexdigest()

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        kind="tool",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gen_ai.tool.name": "tool_sendemail",
            "gravya.tool.args_hash": plain_sha256,  # fornito dal chiamante: deve essere scartato
        },
        raw_arguments=None,  # il chiamante non passa argomenti grezzi, solo l'hash gia' fatto
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]
    assert "gravya.tool.args_hash" not in attrs, "hash fornito dal chiamante accettato (B6 violato)"
    assert "trace.segment_attribute_discarded" in signal_sink.kinds()


def test_decision_args_solo_hmac_calcolato_dall_helper(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now, make_helper):
    tenant_id = str(uuid.uuid4())
    key_bytes = b"altra-chiave-di-prova-sintetica-non-un-segreto!"
    key_provider.set_key(tenant_id, "v1", key_bytes)
    helper = make_helper(variables, signal_sink, key_provider, production_override=False)

    raw = json.dumps(PII_ARGS, sort_keys=True).encode("utf-8")
    expected_digest, expected_ref = compute_args_hmac(key_provider, tenant_id, raw)

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        kind="decision",
        started_at=datetime.now(timezone.utc),
        attributes={"gravya.decision.kind": "hitl", "gravya.decision.id": str(uuid.uuid4())},
        raw_arguments=raw,
    )
    helper.start_segment(admin_conn, segment)
    assert helper.flush(timeout=5)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]
    assert attrs["gravya.decision.args_hash"] == expected_digest
    assert attrs["gravya.hash.key_ref"] == expected_ref
    for pii_value in PII_ARGS.values():
        assert pii_value not in json.dumps(attrs)
