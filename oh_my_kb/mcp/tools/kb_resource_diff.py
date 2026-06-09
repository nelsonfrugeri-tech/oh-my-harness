"""``kb_resource_diff`` MCP tool — show unified diff between local and server resources."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

KB_RESOURCE_DIFF_TOOL = Tool(
    name="kb_resource_diff",
    description=(
        "Show a unified diff between the local version of one or all oh-my-kb resources "
        "in ~/.claude/ and the current server version. Use when the user asks what changed, "
        "what is new, or wants to inspect differences before updating. Pass 'resource' to "
        "scope the diff to a single resource ID (e.g. 'skills/scribe'); omit it to diff all "
        "resources at once. Requires the manifest to exist — if missing, instruct the user "
        "to run 'omk resource pull --all' first."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "resource": {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Resource ID to diff (e.g. 'skills/scribe'). Omit to diff all."
                ),
            }
        },
        "additionalProperties": False,
    },
)

_SECTION_WIDTH = 80


def _section_header(title: str) -> str:
    padding = max(0, _SECTION_WIDTH - 5 - len(title))
    return f"─── {title} " + "─" * padding


async def handle_kb_resource_diff(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Return plain-text unified diff between local and server resource versions."""
    from oh_my_kb.cli.manifest import load_manifest
    from oh_my_kb.services.resource_ops import _ID_TO_URI, compute_diff

    resource_id: str | None = arguments.get("resource")

    # Load manifest — required for diff
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        return [
            TextContent(
                type="text",
                text=(
                    "kb_resource_diff: erro — manifest não encontrado em "
                    "~/.claude/.omk-manifest.json.\n"
                    "Execute 'omk resource pull --all' para baixar os resources "
                    "antes de comparar."
                ),
            )
        ]
    except Exception as exc:
        return [TextContent(type="text", text=f"kb_resource_diff: error — {exc}")]

    # Compute diff — may raise KeyError for invalid resource_id
    try:
        result = compute_diff(manifest=manifest, resource_id=resource_id)
    except KeyError:
        available = ", ".join(sorted(_ID_TO_URI.keys()))
        return [
            TextContent(
                type="text",
                text=(
                    f"kb_resource_diff: erro — resource '{resource_id}'"
                    " não encontrado no servidor.\n"
                    f"Resources disponíveis: {available}."
                ),
            )
        ]
    except Exception as exc:
        return [TextContent(type="text", text=f"kb_resource_diff: error — {exc}")]

    if result.changed_count == 0 and result.unchanged_count == 0:
        return [
            TextContent(
                type="text",
                text="kb_resource_diff: nenhum resource encontrado.",
            )
        ]

    # All unchanged
    if result.changed_count == 0:
        total = len(result.entries)
        if total == 1:
            rid = result.entries[0].resource_id
            ver = result.entries[0].server_version
            return [
                TextContent(
                    type="text",
                    text=f"kb_resource_diff: {rid} está atualizado (versão {ver})",
                )
            ]
        return [
            TextContent(
                type="text",
                text=(
                    f"kb_resource_diff: todos os resources estão atualizados "
                    f"({total} verificados)"
                ),
            )
        ]

    # Mixed or all changed
    lines: list[str] = [
        f"kb_resource_diff: {result.changed_count} resource com alterações, "
        f"{result.unchanged_count} sem alterações"
    ]

    for entry in result.entries:
        lines.append("")
        if entry.is_changed:
            local_ver = entry.local_version or "none"
            title = (
                f"{entry.resource_id}"
                f"  (local: {local_ver} → servidor: {entry.server_version})"
            )
            lines.append(_section_header(title))
            lines.append("")
            if entry.diff_text:
                lines.append(entry.diff_text)
        else:
            local_ver = entry.local_version or "none"
            title = (
                f"{entry.resource_id}"
                f"  (local: {local_ver} = servidor: {entry.server_version})"
            )
            lines.append(_section_header(title) + " sem alterações ─")

    lines.append("")
    lines.append("  Use kb_resource_update para aplicar as atualizações.")

    return [TextContent(type="text", text="\n".join(lines))]
