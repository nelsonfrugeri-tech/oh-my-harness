from __future__ import annotations

from pathlib import Path

from lib.config_writer import ConfigWriter
from lib.layout import InstallLayout
from lib.managed_agents import ManagedAgents
from lib.managed_hooks import ManagedHooks


class ManagedConfig:
    """Coordinates the independently managed global instructions and hooks."""

    def __init__(
        self,
        layout: InstallLayout,
        conflict: type[RuntimeError],
        replace_global_agents: bool,
    ) -> None:
        writer = ConfigWriter()
        self._layout = layout
        self._agents = ManagedAgents(layout, conflict, replace_global_agents, writer)
        self._hooks = ManagedHooks(layout, conflict, writer)

    def transaction_paths(self) -> tuple[Path, ...]:
        return self._layout.global_agents_file, self._layout.hooks_file

    def install(self) -> tuple[str, ...]:
        return self._agents.install(), self._hooks.install()

    def preflight(self) -> None:
        self._agents.preflight()
        self._hooks.preflight()

    def validate(self) -> tuple[str, ...]:
        return self._agents.validate(), self._hooks.validate()
