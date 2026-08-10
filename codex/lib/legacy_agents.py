from __future__ import annotations

import shutil
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from lib.legacy_agent_manifest import load_legacy_agent_names
from lib.legacy_agent_recovery import LegacyAgentRecovery
from lib.layout import InstallLayout


class LegacyAgentMigration:
    def __init__(
        self,
        layout: InstallLayout,
        conflict: type[RuntimeError],
        enabled: bool,
    ) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self._layout = layout
        self._conflict = conflict
        self._enabled = enabled
        self._backup = layout.codex_home / "backups" / f"omh-legacy-agents-{timestamp}"
        self._names: frozenset[str] = frozenset()
        self._recovery = LegacyAgentRecovery()

    def preflight(self, expected: frozenset[str]) -> None:
        if not self._enabled:
            return
        names = self._manifest_names()
        missing = names - expected
        if missing:
            joined = ", ".join(sorted(missing))
            raise self._conflict(f"legacy managed agents missing from source: {joined}")
        for name in names:
            target = self._layout.custom_agents / name
            occupied = self._occupied_staging_path(target)
            if occupied:
                raise self._conflict(
                    f"legacy migration temporary path exists: {occupied}"
                )
            if target.exists() and not target.is_file():
                raise self._conflict(
                    f"legacy managed agent is not a regular file: {target}"
                )
            backup = self._backup / "agents" / name
            if target.is_file() and not target.is_symlink() and backup.exists():
                raise self._conflict(f"legacy migration backup already exists: {backup}")
        self._names = names

    @contextmanager
    def transaction(self) -> Iterator[None]:
        try:
            yield
        except BaseException as failure:
            errors = self._recovery.restore_all()
            if errors:
                details = "; ".join(errors)
                raise self._conflict(
                    f"legacy agent migration rollback failed: {details}"
                ) from failure
            raise
        finally:
            self._recovery.clear()

    def can_adopt(self, source: Path, target: Path) -> bool:
        return (
            self._enabled
            and source.name == target.name
            and target.name in self._names
            and target.is_file()
            and not target.is_symlink()
        )

    def adopt(self, source: Path, target: Path) -> str:
        backup = self._backup / "agents" / target.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        self._backup_manifest()
        temporary = self._temporary(target)
        self._recovery.record(target, backup, temporary)
        temporary.symlink_to(source)
        target.replace(backup)
        temporary.replace(target)
        return f"migrated legacy managed agent: {target} (backup: {backup})"

    def _manifest_names(self) -> frozenset[str]:
        path = self._layout.custom_agents / ".oh-my-harness-managed.json"
        return load_legacy_agent_names(path, self._conflict)

    def _backup_manifest(self) -> None:
        destination = self._backup / ".oh-my-harness-managed.json"
        if destination.exists():
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = self._layout.custom_agents / ".oh-my-harness-managed.json"
        shutil.copy2(source, destination)

    def _temporary(self, target: Path) -> Path:
        return target.with_name(f".{target.name}.omh-migration")

    def _occupied_staging_path(self, target: Path) -> Path | None:
        restored = target.with_name(f".{target.name}.omh-restore")
        for path in (self._temporary(target), restored):
            if path.exists() or path.is_symlink():
                return path
        return None
