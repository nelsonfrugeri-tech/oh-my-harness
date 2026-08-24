from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PluginCatalog:
    marketplace_name: str
    marketplace_source: str
    marketplace_remote_url: str
    plugins: tuple[str, ...]


class PluginIntegrations:
    def __init__(self, source_root: Path) -> None:
        self._catalog_file = source_root / "codex/integrations/plugins.json"

    def install(self) -> str:
        catalog = self._catalog()
        marketplace = self._marketplace(catalog)
        if marketplace.startswith("pending:"):
            return marketplace
        installed = self._installed_plugins()
        missing = tuple(
            plugin for plugin in catalog.plugins if self._plugin_id(plugin, catalog) not in installed
        )
        if not missing:
            return "ok: LangChain skills and live documentation"
        for plugin in missing:
            result = self._run(["codex", "plugin", "add", self._plugin_id(plugin, catalog)])
            if result.returncode != 0:
                return f"pending: LangChain plugin installation failed: {result.stderr.strip()}"
        return "configured: LangChain skills and live documentation"

    def _catalog(self) -> PluginCatalog:
        content = json.loads(self._catalog_file.read_text(encoding="utf-8"))
        marketplace = content["marketplace"]
        plugins = content["plugins"]
        name = marketplace["name"]
        source = marketplace["source"]
        remote_url = marketplace["remote_url"]
        if not all(isinstance(field, str) for field in (name, source, remote_url)):
            raise ValueError("plugin marketplace fields must be strings")
        if not isinstance(plugins, list) or not all(isinstance(plugin, str) for plugin in plugins):
            raise ValueError("plugin names must be a list of strings")
        if not plugins:
            raise ValueError("plugin catalog cannot be empty")
        return PluginCatalog(name, source, remote_url, tuple(plugins))

    def _marketplace(self, catalog: PluginCatalog) -> str:
        result = self._run(["codex", "plugin", "marketplace", "list", "--json"])
        if result.returncode != 0:
            return f"pending: LangChain marketplace lookup failed: {result.stderr.strip()}"
        marketplaces = json.loads(result.stdout)["marketplaces"]
        current = next(
            (item for item in marketplaces if item["name"] == catalog.marketplace_name),
            None,
        )
        if current is not None:
            source = current.get("marketplaceSource", {}).get("source")
            if source == catalog.marketplace_remote_url:
                return "ok"
            return f"pending: LangChain marketplace source mismatch: {source}"
        result = self._run(
            ["codex", "plugin", "marketplace", "add", catalog.marketplace_source]
        )
        if result.returncode != 0:
            return f"pending: LangChain marketplace registration failed: {result.stderr.strip()}"
        return "configured"

    def _installed_plugins(self) -> set[str]:
        result = self._run(["codex", "plugin", "list", "--json"])
        if result.returncode != 0:
            raise subprocess.SubprocessError(result.stderr.strip())
        return {
            item["pluginId"]
            for item in json.loads(result.stdout)["installed"]
            if item["enabled"]
        }

    def _plugin_id(self, plugin: str, catalog: PluginCatalog) -> str:
        return f"{plugin}@{catalog.marketplace_name}"

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
