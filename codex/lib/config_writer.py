from __future__ import annotations

import shutil
from pathlib import Path

from lib.atomic_file import atomic_write
from lib.regular_config import require_regular_config


class ConfigWriter:
    """Writes managed configuration while retaining every replaced preimage."""

    def write_if_changed(self, target: Path, content: str) -> str:
        require_regular_config(target, "managed global config")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_text(encoding="utf-8") == content:
            return f"ok: {target}"
        self._backup_existing(target)
        atomic_write(target, content)
        return f"updated: {target}"

    def _backup_existing(self, target: Path) -> None:
        if not target.exists():
            return
        backup = self._available_backup(target)
        with target.open("rb") as source, backup.open("xb") as destination:
            shutil.copyfileobj(source, destination)
        backup.chmod(target.stat().st_mode)

    @staticmethod
    def _available_backup(target: Path) -> Path:
        primary = target.with_suffix(target.suffix + ".omh.bak")
        if not primary.exists():
            return primary
        index = 1
        while primary.with_name(f"{primary.name}.{index}").exists():
            index += 1
        return primary.with_name(f"{primary.name}.{index}")
