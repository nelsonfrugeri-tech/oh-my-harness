from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from lib.atomic_file import atomic_write
from lib.regular_config import require_regular_config
from lib.toml_backend import TomlBackend


def load_config(path: Path) -> tuple[Mapping[str, Mapping[str, object]], str]:
    require_regular_config(path, "global config.toml")
    backend = TomlBackend.load()
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    servers = backend.parse(text).get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise TypeError("config.toml mcp_servers must be a table")
    return cast(Mapping[str, Mapping[str, object]], servers), text


def validate_config(content: str) -> None:
    TomlBackend.load().parse(content)


def backup_config(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.parent / "backups" / f"mcp-import-{stamp}" / "config.toml"
    backup.parent.mkdir(parents=True, exist_ok=True)
    preimage = path.read_text(encoding="utf-8") if path.exists() else content
    atomic_write(backup, preimage, mode=0o600)
    return backup


def write_config(path: Path, content: str) -> None:
    require_regular_config(path, "global config.toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, content, mode=0o600)
