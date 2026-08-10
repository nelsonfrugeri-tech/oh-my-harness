"""Opt-in import of legacy Claude MCP definitions into Codex."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from lib.mcp_config import backup_config, load_config, validate_config, write_config
from lib.mcp_render import append_servers


@dataclass(frozen=True)
class McpImport:
    name: str
    definition: Mapping[str, object]

    def matches(self, other: Mapping[str, object]) -> bool:
        return _canonical(self.definition) == _canonical(other)


@dataclass(frozen=True)
class McpImportResult:
    added: tuple[str, ...]
    skipped_existing: tuple[str, ...]
    skipped_equivalent: tuple[str, ...]
    backup: Path | None

    def summary(self) -> str:
        return json.dumps(
            {
                "added": self.added,
                "skipped_existing": self.skipped_existing,
                "skipped_equivalent": self.skipped_equivalent,
                "backup": str(self.backup) if self.backup else None,
            },
            ensure_ascii=False,
        )


def import_legacy_mcps(
    home: Path, codex_home: Path, *, dry_run: bool = False, check: bool = False
) -> McpImportResult:
    existing, text = load_config(codex_home / "config.toml")
    additions, conflicts, equivalent = _reconcile(_legacy_servers(home), existing)
    result = McpImportResult(_names(additions), conflicts, equivalent, None)
    if dry_run or check or not additions:
        return result
    path = codex_home / "config.toml"
    rendered = append_servers(text, additions)
    validate_config(rendered)
    backup = backup_config(path, text)
    write_config(path, rendered)
    return McpImportResult(result.added, conflicts, equivalent, backup)


def _canonical(value: object) -> object:
    if isinstance(value, Mapping):
        return tuple(
            sorted((str(key), _canonical(item)) for key, item in value.items())
        )
    if isinstance(value, (list, tuple)):
        return tuple(_canonical(item) for item in value)
    return value


def _names(servers: tuple[McpImport, ...]) -> tuple[str, ...]:
    return tuple(server.name for server in servers)


def _legacy_servers(home: Path) -> tuple[McpImport, ...]:
    selected: dict[str, McpImport] = {}
    for path in (home / ".claude.json", home / ".claude" / ".mcp.json"):
        selected.update({server.name: server for server in _servers_from(path)})
    return tuple(selected[name] for name in sorted(selected))


def _servers_from(path: Path) -> tuple[McpImport, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("mcpServers", {})
    if not isinstance(raw, dict):
        raise TypeError(f"legacy MCP servers in {path} must be an object")
    return tuple(_server(str(name), value) for name, value in raw.items())


def _server(name: str, value: object) -> McpImport:
    if not isinstance(value, dict):
        raise TypeError(f"legacy MCP server {name} must be an object")
    return McpImport(name, {key: item for key, item in value.items() if key != "type"})


def _reconcile(
    incoming: tuple[McpImport, ...], existing: Mapping[str, Mapping[str, object]]
) -> tuple[tuple[McpImport, ...], tuple[str, ...], tuple[str, ...]]:
    additions = tuple(
        item
        for item in incoming
        if item.name not in existing and not _matches_any(item, existing)
    )
    conflicts = tuple(item.name for item in incoming if item.name in existing)
    equivalent = tuple(
        item.name
        for item in incoming
        if item.name not in existing and _matches_any(item, existing)
    )
    return additions, conflicts, equivalent


def _matches_any(item: McpImport, existing: Mapping[str, Mapping[str, object]]) -> bool:
    return any(item.matches(definition) for definition in existing.values())
