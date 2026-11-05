"""Criterio 11: negli segmenti tool e decision gli argomenti compaiono solo
come HMAC, mai in chiaro: test con argomenti contenenti PII.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from gravya_e1.models import SegmentStart
from gravya_e1.tracing import TracingHelper

PII_ARGS = {"email": "mario.rossi@example.com", "telefono": "+39 333 1234567"}


def test_tool_args_solo_hmac_mai_in_chiaro(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now):
    tenant_id = str(uuid.uuid4())
    key_provider.set_key(tenant_id, "v1", b"chiave-di-prova-sintetica-non-un-segreto-reale")
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    raw = json.dumps(PII_ARGS, sort_keys=True).encode("utf-8")
    result = helper.hash_tool_args(tenant_id, raw)
    assert result is not None
    digest, key_ref = result

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        kind="tool",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gen_ai.tool.name": "send-email",
            "gen_ai.tool.call.id": "call-1",
            "gravya.tool.args_hash": digest,
            "gravya.hash.key_ref": key_ref,
        },
    )
    helper.start_segment(admin_conn, segment)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]
    assert attrs["gravya.tool.args_hash"] == digest
    for pii_value in PII_ARGS.values():
        assert pii_value not in json.dumps(attrs)
    assert "email" not in attrs  # nessuna chiave in chiaro degli argomenti


def test_decision_args_solo_hmac_mai_in_chiaro(admin_conn, variables, signal_sink, key_provider, ensure_partitions_now):
    tenant_id = str(uuid.uuid4())
    key_provider.set_key(tenant_id, "v1", b"altra-chiave-di-prova-sintetica")
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=False)

    raw = json.dumps(PII_ARGS, sort_keys=True).encode("utf-8")
    digest, key_ref = helper.hash_tool_args(tenant_id, raw)

    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id),
        kind="decision",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gravya.decision.kind": "hitl",
            "gravya.decision.id": "req-1",
            "gravya.decision.args_hash": digest,
            "gravya.hash.key_ref": key_ref,
        },
    )
    helper.start_segment(admin_conn, segment)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]
    assert attrs["gravya.decision.args_hash"] == digest
    for pii_value in PII_ARGS.values():
        assert pii_value not in json.dumps(attrs)
