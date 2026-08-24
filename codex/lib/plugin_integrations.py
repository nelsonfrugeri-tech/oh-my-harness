from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PluginCatalog:
    label: str
    summary: str
    marketplace_name: str
    marketplace_source: str
    marketplace_remote_url: str
    plugins: tuple[str, ...]


@dataclass(frozen=True)
class MarketplaceState:
    source: str | None
    pending: str | None


class PluginIntegrations:
    def __init__(self, source_root: Path) -> None:
        self._catalog_file = source_root / "codex/integrations/plugins.json"

    def install(self) -> tuple[str, ...]:
        return tuple(self._install_catalog(catalog) for catalog in self._catalogs())

    def _install_catalog(self, catalog: PluginCatalog) -> str:
        marketplace = self._marketplace(catalog)
        if marketplace.startswith("pending:"):
            return marketplace
        installed = self._installed_plugins()
        missing = tuple(plugin for plugin in catalog.plugins if self._plugin_id(plugin, catalog) not in installed)
        if not missing:
            return f"ok: {catalog.summary}"
        for plugin in missing:
            result = self._run(["codex", "plugin", "add", self._plugin_id(plugin, catalog)])
            if result.returncode != 0:
                return f"pending: a instalação do plugin {catalog.label} falhou: {result.stderr.strip()}"
        return f"configured: {catalog.summary}"

    def _catalogs(self) -> tuple[PluginCatalog, ...]:
        content = json.loads(self._catalog_file.read_text(encoding="utf-8"))
        catalogs = content["marketplaces"]
        if not isinstance(catalogs, list) or not catalogs:
            raise ValueError("os marketplaces de plugins devem ser uma lista não vazia")
        return tuple(self._catalog(item) for item in catalogs)

    def _catalog(self, content: object) -> PluginCatalog:
        entry = self._object(content, "todo marketplace de plugins deve ser um objeto")
        marketplace = self._object(
            entry.get("marketplace"),
            "todo marketplace de plugins deve conter sua configuração",
        )
        return PluginCatalog(
            self._string(entry, "label"),
            self._string(entry, "summary"),
            self._string(marketplace, "name"),
            self._string(marketplace, "source"),
            self._string(marketplace, "remote_url"),
            self._plugins(entry),
        )

    def _object(self, value: object, message: str) -> Mapping[str, object]:
        if not isinstance(value, dict):
            raise ValueError(message)
        return value

    def _string(self, content: Mapping[str, object], field: str) -> str:
        value = content.get(field)
        if not isinstance(value, str):
            raise ValueError("os campos do marketplace de plugins devem ser strings")
        return value

    def _plugins(self, content: Mapping[str, object]) -> tuple[str, ...]:
        plugins = content.get("plugins")
        if not isinstance(plugins, list) or not all(isinstance(plugin, str) for plugin in plugins):
            raise ValueError("os nomes de plugins devem ser uma lista de strings")
        if not plugins:
            raise ValueError("o catálogo de plugins não pode estar vazio")
        return tuple(plugins)

    def _marketplace(self, catalog: PluginCatalog) -> str:
        state = self._marketplace_state(catalog)
        if state.pending is not None:
            return state.pending
        if state.source is None:
            registration = self._register_marketplace(catalog)
            if registration.startswith("pending:"):
                return registration
            state = self._marketplace_state(catalog)
            if state.pending is not None:
                return state.pending
        return self._source_status(state.source, catalog)

    def _marketplace_state(self, catalog: PluginCatalog) -> MarketplaceState:
        result = self._run(["codex", "plugin", "marketplace", "list", "--json"])
        if result.returncode != 0:
            return MarketplaceState(
                None,
                f"pending: a consulta ao marketplace {catalog.label} falhou: {result.stderr.strip()}",
            )
        return MarketplaceState(self._marketplace_source(result.stdout, catalog), None)

    def _source_status(self, source: str | None, catalog: PluginCatalog) -> str:
        if source == catalog.marketplace_remote_url:
            return "ok"
        return f"pending: a origem do marketplace {catalog.label} diverge: {source}"

    def _marketplace_source(self, output: str, catalog: PluginCatalog) -> str | None:
        marketplaces = json.loads(output)["marketplaces"]
        current = next((item for item in marketplaces if item["name"] == catalog.marketplace_name), None)
        if not isinstance(current, dict):
            return None
        source = current.get("marketplaceSource", {})
        if not isinstance(source, dict):
            return None
        remote_url = source.get("source")
        return remote_url if isinstance(remote_url, str) else None

    def _register_marketplace(self, catalog: PluginCatalog) -> str:
        result = self._run(
            ["codex", "plugin", "marketplace", "add", catalog.marketplace_source]
        )
        if result.returncode != 0:
            return f"pending: o registro do marketplace {catalog.label} falhou: {result.stderr.strip()}"
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
