from __future__ import annotations

from pathlib import Path
from typing import Type

from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest
from lib.skill_identity import graphify_distribution_matches


class ManagedLinks:
    def __init__(self, layout: InstallLayout, conflict: Type[RuntimeError]) -> None:
        self._layout = layout
        self._conflict = conflict
        self._manifest = ManagedLinkManifest(layout, conflict)

    def install(self) -> tuple[str, ...]:
        results = [*self._remove_orphans()]
        results.append(self._link(self._layout.adapter, self._layout.installed_adapter))
        results.extend(
            self._link(path, self._layout.installed_hooks / path.name)
            for path in self._layout.hook_sources()
        )
        results.extend(self._install_skills())
        results.extend(
            self._link(path, self._layout.custom_agents / path.name)
            for path in self._layout.agent_sources()
        )
        results.append(self._manifest.write(self._current_entries()))
        return tuple(results)

    def preflight(self) -> None:
        self._check_available(self._layout.adapter, self._layout.installed_adapter)
        for source in self._layout.hook_sources():
            self._check_available(source, self._layout.installed_hooks / source.name)
        for source in self._layout.skill_sources():
            target = self._layout.personal_skills / source.name
            if not self._is_compatible_external_graphify(source, target):
                self._check_available(source, target)
        for source in self._layout.agent_sources():
            self._check_available(source, self._layout.custom_agents / source.name)

    def validate(self) -> tuple[str, ...]:
        orphans = self._managed_orphans()
        if orphans:
            raise self._conflict(f"links gerenciados desatualizados: {', '.join(map(str, orphans))}")
        results = [self._check_link(self._layout.installed_adapter, self._layout.adapter)]
        results.extend(
            self._check_link(self._layout.installed_hooks / path.name, path)
            for path in self._layout.hook_sources()
        )
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
            results.append(f"link gerenciado desatualizado removido: {target}")
        return tuple(results)

    def _managed_orphans(self) -> tuple[Path, ...]:
        expected = {
            self._layout.personal_skills / source.name
            for source in self._layout.skill_sources()
        }
        expected.update(
            self._layout.installed_hooks / source.name
            for source in self._layout.hook_sources()
        )
        expected.update(
            self._layout.custom_agents / source.name
            for source in self._layout.agent_sources()
        )
        expected.add(self._layout.installed_adapter)
        return self._manifest.orphans(expected)

    def _current_entries(self) -> tuple[tuple[Path, Path], ...]:
        candidates = ((self._layout.installed_adapter, self._layout.adapter),)
        hooks = (
            (self._layout.installed_hooks / source.name, source)
            for source in self._layout.hook_sources()
        )
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
            for target, source in (*candidates, *hooks, *skills, *agents)
            if target.is_symlink() and target.resolve() == source.resolve()
        )

    def _install_skill(self, source: Path) -> str:
        target = self._layout.personal_skills / source.name
        if self._is_compatible_external_graphify(source, target):
            return f"preservada: skill Graphify externa compatível em {target}"
        return self._link(source, target)

    def _check_skill(self, source: Path) -> str:
        target = self._layout.personal_skills / source.name
        if self._is_compatible_external_graphify(source, target):
            return f"ok: skill Graphify externa compatível em {target}"
        return self._check_link(target, source)

    def _link(self, source: Path, target: Path) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() and target.resolve() == source.resolve():
            return f"ok: {target}"
        if target.exists() or target.is_symlink():
            raise self._conflict(f"recusando substituir path existente: {target}")
        target.symlink_to(source)
        return f"linkado: {target}"

    def _check_available(self, source: Path, target: Path) -> None:
        self._check_parent_directory(target)
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        if target.exists() or target.is_symlink():
            raise self._conflict(f"recusando substituir path existente: {target}")

    def _check_parent_directory(self, target: Path) -> None:
        candidate = target.parent
        while not candidate.exists() and not candidate.is_symlink():
            candidate = candidate.parent
        if not candidate.is_dir():
            raise self._conflict(f"recusando criar dentro de path que não é diretório: {candidate}")

    def _check_link(self, target: Path, source: Path) -> str:
        if not target.is_symlink() or target.resolve() != source.resolve():
            raise self._conflict(f"link gerenciado inválido ou ausente: {target}")
        return f"ok: {target}"

    def _is_compatible_external_graphify(self, source: Path, target: Path) -> bool:
        if source.name != "graphify" or target.is_symlink() or not target.is_dir():
            return False
        version_file = target / ".graphify_version"
        if version_file.is_symlink() or not version_file.is_file():
            return False
        expected = self._upstream_version(source / "SKILL.md")
        try:
            actual = version_file.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            return False
        return (
            bool(expected)
            and actual == expected
            and graphify_distribution_matches(source, target)
        )

    def _upstream_version(self, skill_file: Path) -> str:
        for line in skill_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("upstream_version:"):
                return line.partition(":")[2].strip()
        return ""
