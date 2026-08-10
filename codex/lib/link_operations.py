from __future__ import annotations

from pathlib import Path

from lib.legacy_agents import LegacyAgentMigration


class LinkOperations:
    def __init__(
        self,
        conflict: type[RuntimeError],
        legacy: LegacyAgentMigration,
    ) -> None:
        self._conflict = conflict
        self._legacy = legacy

    def publish(self, source: Path, target: Path) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() and target.resolve() == source.resolve():
            return f"ok: {target}"
        if self._legacy.can_adopt(source, target):
            return self._legacy.adopt(source, target)
        if target.exists() or target.is_symlink():
            raise self._conflict(f"refusing to replace existing path: {target}")
        target.symlink_to(source)
        return f"linked: {target}"

    def preflight(self, source: Path, target: Path) -> None:
        self._check_parent(target)
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        if self._legacy.can_adopt(source, target):
            return
        if target.exists() or target.is_symlink():
            raise self._conflict(f"refusing to replace existing path: {target}")

    def validate(self, target: Path, source: Path) -> str:
        if not target.is_symlink() or target.resolve() != source.resolve():
            raise self._conflict(f"invalid or missing managed link: {target}")
        return f"ok: {target}"

    def _check_parent(self, target: Path) -> None:
        candidate = target.parent
        while not candidate.exists() and not candidate.is_symlink():
            candidate = candidate.parent
        if not candidate.is_dir():
            raise self._conflict(
                f"refusing to create inside non-directory path: {candidate}"
            )
