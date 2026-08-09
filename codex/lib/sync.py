from __future__ import annotations

from lib.layout import InstallLayout
from lib.links import ManagedLinks
from lib.managed_config import ManagedConfig


class InstallConflict(RuntimeError):
    """Raised when installation would overwrite user-owned state."""


class CodexInstaller:
    def __init__(self, layout: InstallLayout, replace_global_agents: bool = False) -> None:
        self._links = ManagedLinks(layout, InstallConflict)
        self._config = ManagedConfig(layout, InstallConflict, replace_global_agents)

    def install(self) -> tuple[str, ...]:
        self._links.preflight()
        self._config.preflight()
        return (*self._links.install(), *self._config.install())

    def validate(self) -> tuple[str, ...]:
        return (*self._links.validate(), *self._config.validate())
