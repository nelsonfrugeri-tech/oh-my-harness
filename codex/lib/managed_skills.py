from __future__ import annotations

from pathlib import Path

from lib.graphify_link import compatible_external_graphify
from lib.layout import InstallLayout
from lib.link_operations import LinkOperations


class ManagedSkills:
    """Owns skill-specific preservation and linking behavior."""

    def __init__(self, layout: InstallLayout, operations: LinkOperations) -> None:
        self._layout = layout
        self._operations = operations

    def transaction_targets(self) -> tuple[Path, ...]:
        return tuple(
            self._target(source)
            for source in self._layout.skill_sources()
            if not self._external(source)
        )

    def preflight(self) -> None:
        for source in self._layout.skill_sources():
            if not self._external(source):
                self._operations.preflight(source, self._target(source))

    def install(self) -> tuple[str, ...]:
        return tuple(self._install(source) for source in self._layout.skill_sources())

    def validate(self) -> tuple[str, ...]:
        return tuple(self._validate(source) for source in self._layout.skill_sources())

    def _install(self, source: Path) -> str:
        target = self._target(source)
        if self._external(source):
            return f"preserved: compatible external Graphify skill at {target}"
        return self._operations.publish(source, target)

    def _validate(self, source: Path) -> str:
        target = self._target(source)
        if self._external(source):
            return f"ok: compatible external Graphify skill at {target}"
        return self._operations.validate(target, source)

    def _external(self, source: Path) -> bool:
        return compatible_external_graphify(source, self._target(source))

    def _target(self, source: Path) -> Path:
        return self._layout.personal_skills / source.name
