"""Serialize the native Lakeview contract without lossy transformations."""

from __future__ import annotations

import json

from dashboard_definition import Definition


def serialized_dashboard(definition: Definition) -> str:
    return json.dumps(
        definition.serialized_dashboard.to_builtin(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
