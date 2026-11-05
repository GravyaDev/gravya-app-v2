"""Istantanee di variabili complete per i test (evita di duplicare le 7
variabili di E1 in ogni file). Usato per costruire istantanee ad-hoc dove un
test deve variare una sola voce e lasciare le altre valide."""
from __future__ import annotations

DEV_E1_VARIABLES = {
    "e1.partition_interval_months": {"value": 1, "unit": "months", "status": "deciso"},
    "e1.overhead_p95_ms": {"value": 5, "unit": "ms", "status": "deciso"},
    "e1.write_buffer_size": {"value": 100, "unit": "count", "status": "deciso"},
    "e1.attributes.max_value_bytes": {"value": 2048, "unit": "bytes", "status": "deciso"},
    "e1.write_statement_timeout_ms": {"value": 2000, "unit": "ms", "status": "deciso"},
    "e1.write_connect_timeout_s": {"value": 2, "unit": "s", "status": "deciso", "min": 2},
    "e1.write_tcp_keepalives_idle_s": {"value": 10, "unit": "s", "status": "deciso"},
    "e1.write_tcp_keepalives_interval_s": {"value": 5, "unit": "s", "status": "deciso"},
    "e1.write_tcp_keepalives_count": {"value": 3, "unit": "count", "status": "deciso"},
    "e1.write_tcp_user_timeout_ms": {"value": 5000, "unit": "ms", "status": "deciso"},
}


def snapshot_with(overrides: dict | None = None) -> dict:
    """Ritorna {"variables": {...}} con le 9 variabili di sviluppo, piu' override."""
    variables = {k: dict(v) for k, v in DEV_E1_VARIABLES.items()}
    if overrides:
        for name, entry in overrides.items():
            variables[name] = entry
    return {"variables": variables}
