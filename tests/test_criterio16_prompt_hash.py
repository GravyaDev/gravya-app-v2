"""Criterio 16: gravya.prompt.hash e' l'hash del template, mai del render.

Test con un render contenente PII: nessun hash di render (ne' testo di
render) compare nella riga. E1 non calcola l'hash del prompt: lo riceve da
chi emette il segmento (B1/E2) gia' calcolato sul template; qui si verifica
che la whitelist non lasci passare nulla legato al render (ne' testo libero,
ne' una seconda chiave hash), cosi' l'unico hash possibile in riga resta
quello dichiarato dal chiamante come hash del template (E1 §4.2, DA-E1-09).
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from gravya_e1.models import SegmentStart
from gravya_e1.signals import PostgresSignalSink
from gravya_e1.tracing import TracingHelper

TEMPLATE_HASH = hashlib.sha256(b"template:greeting:v3").hexdigest()
RENDER_TEXT_WITH_PII = "Ciao Mario Rossi, la tua email e' mario.rossi@example.com"
RENDER_HASH = hashlib.sha256(RENDER_TEXT_WITH_PII.encode("utf-8")).hexdigest()


def test_solo_hash_del_template_in_riga_mai_render(admin_conn, variables, key_provider, ensure_partitions_now):
    signal_sink = PostgresSignalSink(admin_conn)
    helper = TracingHelper(variables, signal_sink, key_provider, production_override=True)
    segment = SegmentStart(
        segment_id=uuid.uuid4(),
        trace_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        kind="llm",
        started_at=datetime.now(timezone.utc),
        attributes={
            "gravya.prompt.key": "greeting",
            "gravya.prompt.version": "v3",
            "gravya.prompt.hash": TEMPLATE_HASH,
            # tentativi non ammessi dalla whitelist: testo renderizzato e un
            # secondo hash (del render) sotto un nome non previsto da E1 §4.2
            "gravya.prompt.rendered_text": RENDER_TEXT_WITH_PII,
            "gravya.prompt.rendered_hash": RENDER_HASH,
        },
    )
    helper.start_segment(admin_conn, segment)

    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT attributes FROM gravya_trace_segments WHERE segment_id = %s", (str(segment.segment_id),)
        )
        attrs = cur.fetchone()[0]

    assert attrs["gravya.prompt.hash"] == TEMPLATE_HASH
    assert "gravya.prompt.rendered_text" not in attrs
    assert "gravya.prompt.rendered_hash" not in attrs
    assert RENDER_HASH not in attrs.values()
    assert RENDER_TEXT_WITH_PII not in str(attrs)
