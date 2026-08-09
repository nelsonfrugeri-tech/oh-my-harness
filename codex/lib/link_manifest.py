from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from lib.atomic_file import atomic_write
from lib.layout import InstallLayout


class ManagedLinkManifest:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._path = layout.links_manifest
        self._conflict = conflict

    def orphans(self, expected: set[Path]) -> tuple[Path, ...]:
        return tuple(
            sorted(
                target
                for target, source in self._entries()
                if target not in expected and self._is_recorded_link(target, source)
            )
        )

    def write(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        content = self._content(entries)
        if self._path.exists() and self._path.read_text(encoding="utf-8") == content:
            return f"ok: {self._path}"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(self._path, content)
        return f"updated: {self._path}"

    def validate(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        if not self._path.exists() or self._path.read_text(encoding="utf-8") != self._content(entries):
            raise self._conflict(f"managed links manifest is missing or stale: {self._path}")
        return f"ok: {self._path}"

    def _entries(self) -> tuple[tuple[Path, Path], ...]:
        if not self._path.exists():
            return ()
        data = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1:
            raise self._conflict(f"invalid managed links manifest: {self._path}")
        links = data.get("links")
        if not isinstance(links, list):
            raise self._conflict(f"invalid managed links manifest: {self._path}")
        entries = []
        for entry in links:
            if not isinstance(entry, dict):
                raise self._conflict(f"invalid managed links manifest: {self._path}")
            target, source = entry.get("target"), entry.get("source")
            if not isinstance(target, str) or not isinstance(source, str):
                raise self._conflict(f"invalid managed links manifest: {self._path}")
            entries.append((Path(target), Path(source)))
        return tuple(entries)

    def _is_recorded_link(self, target: Path, source: Path) -> bool:
        if not target.is_symlink():
            return False
        linked = target.readlink()
        absolute = linked if linked.is_absolute() else target.parent / linked
        return absolute.resolve() == source.resolve()

    def _content(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        links = [{"target": str(target), "source": str(source)} for target, source in entries]
        return json.dumps({"version": 1, "links": links}, indent=2) + "\n"
