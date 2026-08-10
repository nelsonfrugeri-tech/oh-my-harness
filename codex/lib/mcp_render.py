"""TOML rendering for imported MCP servers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from lib.mcp_import import McpImport


def append_servers(text: str, servers: tuple[McpImport, ...]) -> str:
    blocks = tuple(render_server(server.name, server.definition) for server in servers)
    prefix = text.rstrip()
    return (prefix + "\n\n" if prefix else "") + "\n\n".join(blocks) + "\n"


def render_server(name: str, definition: Mapping[str, object]) -> str:
    table = f"mcp_servers.{_string(name)}"
    identity, scalars, nested = _split(definition)
    lines = [f"[{table}]", *_render_values(identity)]
    lines.extend(_render_values(scalars))
    for section, values in nested.items():
        lines.extend(("", f"[{table}.{_string(section)}]", *_render_values(values)))
    return "\n".join(lines)


def _split(
    definition: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, Mapping[str, object]]]:
    identity_keys = {"command", "args", "cwd", "url"}
    identity = {key: value for key, value in definition.items() if key in identity_keys}
    nested = {
        key: cast(Mapping[str, object], value)
        for key, value in definition.items()
        if isinstance(value, dict)
    }
    scalars = {
        key: value
        for key, value in definition.items()
        if key not in identity_keys and key not in nested
    }
    return identity, scalars, nested


def _render_values(values: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(f"{_key(key)} = {_value(value)}" for key, value in values.items())


def _key(value: str) -> str:
    return value if value.replace("_", "").isalnum() else _string(value)


def _string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError("legacy MCP definition contains an unsupported TOML value")
