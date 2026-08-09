from __future__ import annotations

from pathlib import Path
from typing import Type

from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest


class ManagedLinks:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._layout = layout
        self._conflict = conflict
        self._manifest = ManagedLinkManifest(layout, conflict)

    def install(self) -> tuple[str, ...]:
        results = [*self._remove_orphans()]
        results.append(self._link(self._layout.adapter, self._layout.installed_adapter))
        results.extend(self._install_skills())
        results.extend(
            self._link(path, self._layout.custom_agents / path.name)
            for path in self._layout.agent_sources()
        )
        results.append(self._manifest.write(self._current_entries()))
        return tuple(results)

    def preflight(self) -> None:
        self._check_available(self._layout.adapter, self._layout.installed_adapter)
        for source in self._layout.skill_sources():
            target = self._layout.personal_skills / source.name
            if not self._is_compatible_external_graphify(source, target):
                self._check_available(source, target)
        for source in self._layout.agent_sources():
            self._check_available(source, self._layout.custom_agents / source.name)

    def validate(self) -> tuple[str, ...]:
        orphans = self._managed_orphans()
        if orphans:
            raise self._conflict(f"stale managed links: {', '.join(map(str, orphans))}")
        results = [self._check_link(self._layout.installed_adapter, self._layout.adapter)]
        results.extend(self._check_skill(path) for path in self._layout.skill_sources())
        results.extend(
            self._check_link(self._layout.custom_agents / path.name, path)
            for path in self._layout.agent_sources()
        )
        results.append(self._manifest.validate(self._current_entries()))
        return tuple(results)

    def _install_skills(self) -> tuple[str, ...]:
        return tuple(self._install_skill(path) for path in self._layout.skill_sources())

    def _remove_orphans(self) -> tuple[str, ...]:
        results = []
        for target in self._managed_orphans():
            target.unlink()
            results.append(f"removed stale managed link: {target}")
        return tuple(results)

    def _managed_orphans(self) -> tuple[Path, ...]:
        expected = {
            self._layout.personal_skills / source.name
            for source in self._layout.skill_sources()
        }
        expected.update(
            self._layout.custom_agents / source.name
            for source in self._layout.agent_sources()
        )
        expected.add(self._layout.installed_adapter)
        return self._manifest.orphans(expected)

    def _current_entries(self) -> tuple[tuple[Path, Path], ...]:
        candidates = ((self._layout.installed_adapter, self._layout.adapter),)
        skills = (
            (self._layout.personal_skills / source.name, source)
            for source in self._layout.skill_sources()
        )
        agents = (
            (self._layout.custom_agents / source.name, source)
            for source in self._layout.agent_sources()
        )
        return tuple(
            (target, source)
            for target, source in (*candidates, *skills, *agents)
            if target.is_symlink() and target.resolve() == source.resolve()
        )

    def _install_skill(self, source: Path) -> str:
        target = self._layout.personal_skills / source.name
        if self._is_compatible_external_graphify(source, target):
            return f"preserved: compatible external Graphify skill at {target}"
        return self._link(source, target)

    def _check_skill(self, source: Path) -> str:
        target = self._layout.personal_skills / source.name
        if self._is_compatible_external_graphify(source, target):
            return f"ok: compatible external Graphify skill at {target}"
        return self._check_link(target, source)

    def _link(self, source: Path, target: Path) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() and target.resolve() == source.resolve():
            return f"ok: {target}"
        if target.exists() or target.is_symlink():
            raise self._conflict(f"refusing to replace existing path: {target}")
        target.symlink_to(source)
        return f"linked: {target}"

    def _check_available(self, source: Path, target: Path) -> None:
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        if target.exists() or target.is_symlink():
            raise self._conflict(f"refusing to replace existing path: {target}")

    def _check_link(self, target: Path, source: Path) -> str:
        if not target.is_symlink() or target.resolve() != source.resolve():
            raise self._conflict(f"invalid or missing managed link: {target}")
        return f"ok: {target}"

    def _is_compatible_external_graphify(self, source: Path, target: Path) -> bool:
        if source.name != "graphify" or target.is_symlink() or not target.is_dir():
            return False
        version_file = target / ".graphify_version"
        if not version_file.is_file():
            return False
        expected = self._upstream_version(source / "SKILL.md")
        return version_file.read_text(encoding="utf-8").strip() == expected

    def _upstream_version(self, skill_file: Path) -> str:
        for line in skill_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("upstream_version:"):
                return line.partition(":")[2].strip()
        return ""
