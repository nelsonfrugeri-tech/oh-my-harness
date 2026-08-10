from __future__ import annotations

import os
from pathlib import Path


def configured_home(environment_name: str, default_leaf: str) -> Path:
    raw = os.environ.get(environment_name)
    if raw is None or not raw.strip():
        return Path.home() / default_leaf
    return Path(raw).expanduser()


def validated_home(path: Path, label: str, source_root: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise ValueError(f"{label} must be an absolute path: {path}")
    resolved = expanded.resolve(strict=False)
    if _is_within(resolved, source_root.resolve()):
        raise ValueError(f"{label} must be outside the oh-my-harness source tree")
    return resolved


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
