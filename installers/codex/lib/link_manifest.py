from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from lib.atomic_file import atomic_write
from lib.layout import InstallLayout


class ManagedLinkManifest:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._layout = layout
        self._path = layout.links_manifest
        self._conflict = conflict

    def stale(self, expected: set[tuple[Path, Path]]) -> tuple[Path, ...]:
        return tuple(
            sorted(
                target
                for target, source in self._entries()
                if (target, source) not in expected
                and self._is_recorded_link(target, source)
            )
        )

    def owns_target(self, target: Path) -> bool:
        return any(
            recorded_target == target and self._is_recorded_link(target, source)
            for recorded_target, source in self._entries()
        )

    def owns(self, target: Path, source: Path) -> bool:
        return (target, source) in self._entries() and self._is_recorded_link(target, source)

    def write(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        content = self._content(entries)
        if self._path.exists() and self._path.read_text(encoding="utf-8") == content:
            return f"ok: {self._path}"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(self._path, content)
        return f"atualizado: {self._path}"

    def validate(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        if not self._path.exists() or self._path.read_text(encoding="utf-8") != self._content(entries):
            raise self._conflict(f"manifesto de links gerenciados ausente ou desatualizado: {self._path}")
        return f"ok: {self._path}"

    def _entries(self) -> tuple[tuple[Path, Path], ...]:
        try:
            content = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ()
        except (OSError, UnicodeError) as error:
            raise self._invalid_manifest() from error
        try:
            return self._parse_entries(json.loads(content))
        except (ValueError, OSError) as error:
            raise self._invalid_manifest() from error

    def _parse_entries(self, data: object) -> tuple[tuple[Path, Path], ...]:
        if not isinstance(data, dict) or data.get("version") != 1:
            raise self._invalid_manifest()
        links = data.get("links")
        if not isinstance(links, list):
            raise self._invalid_manifest()
        entries: dict[Path, Path] = {}
        for entry in links:
            target, source = self._parse_entry(entry)
            if target in entries:
                raise self._invalid_manifest()
            entries[target] = source
        return tuple(entries.items())

    def _parse_entry(self, entry: object) -> tuple[Path, Path]:
        if not isinstance(entry, dict):
            raise self._invalid_manifest()
        target, source = entry.get("target"), entry.get("source")
        if not isinstance(target, str) or not isinstance(source, str):
            raise self._invalid_manifest()
        paths = Path(target), Path(source)
        if any(not path.is_absolute() or ".." in path.parts for path in paths):
            raise self._invalid_manifest()
        if not self._safe_target(paths[0]):
            raise self._invalid_manifest()
        return paths

    def _safe_target(self, target: Path) -> bool:
        if target == self._layout.installed_adapter:
            return True
        parents = (self._layout.personal_skills, self._layout.installed_hooks)
        # Older adapters recorded agent symlinks before switching to managed copies.
        legacy_agent = target.parent == self._layout.custom_agents and target.suffix == ".toml"
        return (target.parent in parents or legacy_agent) and not target.parent.is_symlink()

    def _invalid_manifest(self) -> RuntimeError:
        return self._conflict(f"manifesto de links gerenciados inválido: {self._path}")

    def _is_recorded_link(self, target: Path, source: Path) -> bool:
        if not target.is_symlink():
            return False
        linked = target.readlink()
        absolute = linked if linked.is_absolute() else target.parent / linked
        try:
            return absolute.samefile(source)
        except FileNotFoundError:
            # Package moves leave dangling legacy links that still prove ownership.
            return absolute.resolve() == source.resolve()

    def _content(self, entries: tuple[tuple[Path, Path], ...]) -> str:
        links = [{"target": str(target), "source": str(source)} for target, source in entries]
        return json.dumps({"version": 1, "links": links}, indent=2) + "\n"
