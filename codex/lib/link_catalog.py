from __future__ import annotations

from pathlib import Path

from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest


class ManagedLinkCatalog:
    def __init__(self, layout: InstallLayout, manifest: ManagedLinkManifest) -> None:
        self._layout = layout
        self._manifest = manifest

    def orphans(self) -> tuple[Path, ...]:
        expected = {target for target, _source in self.expected_entries()}
        return self._manifest.orphans(expected)

    def current_entries(self) -> tuple[tuple[Path, Path], ...]:
        return tuple(
            (target, source)
            for target, source in self.expected_entries()
            if target.is_symlink() and target.resolve() == source.resolve()
        )

    def expected_entries(self) -> tuple[tuple[Path, Path], ...]:
        adapter = ((self._layout.installed_adapter, self._layout.adapter),)
        hooks = self._entries(self._layout.hook_sources(), self._layout.installed_hooks)
        rules = self._entries(self._layout.rule_sources(), self._layout.installed_rules)
        skills = self._entries(
            self._layout.skill_sources(), self._layout.personal_skills
        )
        agents = self._entries(self._layout.agent_sources(), self._layout.custom_agents)
        return (*adapter, *hooks, *rules, *skills, *agents)

    def _entries(
        self,
        sources: tuple[Path, ...],
        destination: Path,
    ) -> tuple[tuple[Path, Path], ...]:
        return tuple((destination / source.name, source) for source in sources)
