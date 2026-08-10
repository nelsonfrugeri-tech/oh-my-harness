from __future__ import annotations

from pathlib import Path


def require_regular_config(
    path: Path, label: str, error_type: type[Exception] = ValueError
) -> None:
    """Reject config paths whose publication semantics are unsafe."""
    if path.is_symlink():
        raise error_type(f"{label} must not be a symbolic link: {path}")
    if path.exists() and not path.is_file():
        raise error_type(f"{label} must be a regular file: {path}")
