from __future__ import annotations

import json
from pathlib import Path


def load_legacy_agent_names(
    path: Path, conflict: type[RuntimeError]
) -> frozenset[str]:
    """Loads and validates the v1 legacy managed-agent manifest."""
    if not path.is_file():
        raise conflict(f"legacy managed agents manifest is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise conflict(f"invalid legacy managed agents manifest: {path}")
    names = data.get("agents")
    if data.get("version") != 1 or not isinstance(names, list):
        raise conflict(f"invalid legacy managed agents manifest: {path}")
    if not all(_valid_name(name) for name in names):
        raise conflict(f"invalid legacy managed agents manifest: {path}")
    return frozenset(names)


def _valid_name(name: object) -> bool:
    return isinstance(name, str) and Path(name).name == name
