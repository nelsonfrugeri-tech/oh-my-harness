from __future__ import annotations

from lib.agent_copies import ManagedAgentCopies
from lib.layout import InstallLayout
from lib.links import ManagedLinks
from lib.managed_config import ManagedConfig
from lib.permissions import ManagedPermissions


class InstallConflict(RuntimeError):
    """Raised when installation would overwrite user-owned state."""


class CodexInstaller:
    def __init__(self, layout: InstallLayout, replace_global_agents: bool = False) -> None:
        self._links = ManagedLinks(layout, InstallConflict)
        self._agents = ManagedAgentCopies(layout, InstallConflict)
        self._config = ManagedConfig(layout, InstallConflict, replace_global_agents)
        self._permissions = ManagedPermissions(layout, InstallConflict)

    def install(self) -> tuple[str, ...]:
        self._links.preflight()
        self._agents.preflight()
        self._config.preflight()
        self._permissions.preflight()
        return (
            *self._agents.install(),
            *self._links.install(),
            *self._config.install(),
            self._permissions.install(),
        )

    def validate(self) -> tuple[str, ...]:
        return (
            *self._links.validate(),
            *self._agents.validate(),
            *self._config.validate(),
            self._permissions.validate(),
        )
