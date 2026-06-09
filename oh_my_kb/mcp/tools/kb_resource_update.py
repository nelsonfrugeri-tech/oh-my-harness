"""``kb_resource_update`` MCP tool — apply pending updates and regenerate CLAUDE.md."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.types import TextContent, Tool

KB_RESOURCE_UPDATE_TOOL = Tool(
    name="kb_resource_update",
    description=(
        "Apply pending updates: download changed resources from the server to ~/.claude/, "
        "update the local manifest, and automatically regenerate ~/.claude/CLAUDE.md so "
        "the harness block reflects the latest content. Use when the user asks to update, "
        "sync, or apply updates to skills or resources. Pass 'resource' to update a single "
        "resource ID; omit it to update all with pending changes. Reports each file written "
        "and confirms CLAUDE.md regeneration."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "resource": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Resource ID to update (e.g. 'skills/scribe'). Omit to update all."
                ),
            }
        },
        "additionalProperties": False,
    },
)


def _do_update_sync(resource_id: str | None) -> tuple[object, str | None, str | None]:
    """Synchronous body run inside asyncio.to_thread.

    Returns (UpdateResult | None, sentinel_error | None, bootstrap_error | None).
    Sentinel errors:
      - "manifest_missing"        — manifest file absent
      - "invalid_resource:<id>:<available>"
    """
    from oh_my_kb.agents.bootstrap import do_bootstrap
    from oh_my_kb.cli.config import load_config, load_omk_config
    from oh_my_kb.cli.manifest import load_manifest
    from oh_my_kb.services.resource_ops import _ID_TO_URI, UpdateResult, apply_update

    # Load manifest
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        return None, None, "manifest_missing"

    # Validate resource_id
    if resource_id is not None and resource_id not in _ID_TO_URI:
        available = ", ".join(sorted(_ID_TO_URI.keys()))
        return None, None, f"invalid_resource:{resource_id}:{available}"

    # Apply update
    result: UpdateResult = apply_update(manifest=manifest, resource_id=resource_id)

    # Regenerate CLAUDE.md (best-effort)
    bootstrap_error: str | None = None
    if result.updated_count > 0:
        try:
            omk_cfg = load_omk_config()
            cli_cfg = load_config()
            harness = omk_cfg.harness.active
            universe = cli_cfg.active
            if universe is None:
                raise ValueError("no active universe configured")
            do_bootstrap(harness, universe)
            result.claude_md_regenerated = True
        except Exception as exc:
            bootstrap_error = str(exc)
            result.claude_md_error = bootstrap_error

    return result, None, bootstrap_error


async def handle_kb_resource_update(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Apply pending updates and return a plain-text report."""
    resource_id: str | None = arguments.get("resource")

    # Run in thread because apply_update writes files and do_bootstrap is sync
    try:
        result_obj, _unused, sentinel = await asyncio.to_thread(
            _do_update_sync, resource_id
        )
    except Exception as exc:
        return [TextContent(type="text", text=f"kb_resource_update: error — {exc}")]

    # Handle sentinel error cases
    if sentinel == "manifest_missing":
        return [
            TextContent(
                type="text",
                text=(
                    "kb_resource_update: erro — manifest não encontrado em "
                    "~/.claude/.omk-manifest.json.\n"
                    "Execute 'omk resource pull --all' para instalar os resources "
                    "antes de atualizar."
                ),
            )
        ]
    if sentinel and sentinel.startswith("invalid_resource:"):
        parts = sentinel.split(":", 2)
        rid = parts[1] if len(parts) > 1 else str(resource_id)
        available = parts[2] if len(parts) > 2 else ""
        return [
            TextContent(
                type="text",
                text=(
                    f"kb_resource_update: erro — resource '{rid}' não encontrado no servidor.\n"
                    f"Resources disponíveis: {available}."
                ),
            )
        ]

    from oh_my_kb.services.resource_ops import UpdateResult

    if not isinstance(result_obj, UpdateResult):
        return [TextContent(type="text", text="kb_resource_update: error — unexpected result")]

    result: UpdateResult = result_obj

    # Special case: single resource already up to date
    if resource_id is not None and result.updated_count == 0:
        entry = result.entries[0] if result.entries else None
        version = entry.new_version if entry else "?"
        return [
            TextContent(
                type="text",
                text=(
                    f"kb_resource_update: {resource_id} já está na versão mais recente "
                    f"({version})."
                ),
            )
        ]

    # All resources already up to date
    if result.updated_count == 0:
        total = len(result.entries)
        return [
            TextContent(
                type="text",
                text=(
                    f"kb_resource_update: todos os resources já estão na versão mais recente "
                    f"({total} verificados)."
                ),
            )
        ]

    # Normal case: some updated, some unchanged
    lines: list[str] = [
        f"kb_resource_update: {result.updated_count} atualizado, "
        f"{result.unchanged_count} sem alterações"
    ]
    lines.append("")

    for entry in result.entries:
        if entry.was_updated:
            old = entry.old_version or "none"
            lines.append(
                f"  ✓ {entry.resource_id:<25}  {old} → {entry.new_version}"
                f"  ({entry.local_path})"
            )
        else:
            lines.append(f"  ○ {entry.resource_id:<25}  sem alterações")

    lines.append("")
    if result.claude_md_regenerated:
        lines.append("  ✓ ~/.claude/CLAUDE.md regenerado.")
    elif result.claude_md_error:
        lines.append(
            f"  Aviso: ~/.claude/CLAUDE.md não pôde ser regenerado: {result.claude_md_error}."
        )
        lines.append("  Execute 'omk install' para corrigir.")

    return [TextContent(type="text", text="\n".join(lines))]
