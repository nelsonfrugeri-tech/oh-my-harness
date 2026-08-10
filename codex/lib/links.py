from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path

from lib.layout import InstallLayout
from lib.legacy_agents import LegacyAgentMigration
from lib.link_catalog import ManagedLinkCatalog
from lib.link_manifest import ManagedLinkManifest
from lib.link_operations import LinkOperations
from lib.managed_skills import ManagedSkills


class ManagedLinks:
    def __init__(
        self,
        layout: InstallLayout,
        conflict: type[RuntimeError],
        migrate_legacy_agents: bool = False,
    ) -> None:
        self._layout = layout
        self._conflict = conflict
        self._manifest = ManagedLinkManifest(layout, conflict)
        self._catalog = ManagedLinkCatalog(layout, self._manifest)
        self._legacy = LegacyAgentMigration(layout, conflict, migrate_legacy_agents)
        self._operations = LinkOperations(conflict, self._legacy)
        self._skills = ManagedSkills(layout, self._operations)

    def transaction(self) -> AbstractContextManager[None]:
        return self._legacy.transaction()

    def transaction_paths(self) -> tuple[Path, ...]:
        managed = tuple(
            target
            for target, _source in self._catalog.expected_entries()
            if target.parent != self._layout.personal_skills
        )
        managed = (*managed, *self._skills.transaction_targets())
        return (*self._catalog.orphans(), *managed, self._layout.links_manifest)

    def install(self) -> tuple[str, ...]:
        results = [*self._remove_orphans()]
        results.append(
            self._operations.publish(
                self._layout.adapter, self._layout.installed_adapter
            )
        )
        results.extend(
            self._operations.publish(path, self._layout.installed_hooks / path.name)
            for path in self._layout.hook_sources()
        )
        results.extend(
            self._operations.publish(path, self._layout.installed_rules / path.name)
            for path in self._layout.rule_sources()
        )
        results.extend(self._skills.install())
        results.extend(
            self._operations.publish(path, self._layout.custom_agents / path.name)
            for path in self._layout.agent_sources()
        )
        results.append(self._manifest.write(self._catalog.current_entries()))
        return tuple(results)

    def preflight(self) -> None:
        self._manifest.preflight(self._catalog.expected_entries())
        expected_agents = frozenset(
            source.name for source in self._layout.agent_sources()
        )
        self._legacy.preflight(expected_agents)
        self._operations.preflight(self._layout.adapter, self._layout.installed_adapter)
        for source in self._layout.hook_sources():
            self._operations.preflight(
                source, self._layout.installed_hooks / source.name
            )
        for source in self._layout.rule_sources():
            self._operations.preflight(
                source, self._layout.installed_rules / source.name
            )
        self._skills.preflight()
        for source in self._layout.agent_sources():
            self._operations.preflight(source, self._layout.custom_agents / source.name)

    def validate(self) -> tuple[str, ...]:
        orphans = self._catalog.orphans()
        if orphans:
            raise self._conflict(f"stale managed links: {', '.join(map(str, orphans))}")
        results = [
            self._operations.validate(
                self._layout.installed_adapter, self._layout.adapter
            )
        ]
        results.extend(
            self._operations.validate(self._layout.installed_hooks / path.name, path)
            for path in self._layout.hook_sources()
        )
        results.extend(
            self._operations.validate(self._layout.installed_rules / path.name, path)
            for path in self._layout.rule_sources()
        )
        results.extend(self._skills.validate())
        results.extend(
            self._operations.validate(self._layout.custom_agents / path.name, path)
            for path in self._layout.agent_sources()
        )
        results.append(self._manifest.validate(self._catalog.current_entries()))
        return tuple(results)

    def _remove_orphans(self) -> tuple[str, ...]:
        results = []
        for target in self._catalog.orphans():
            target.unlink()
            results.append(f"removed stale managed link: {target}")
        return tuple(results)
