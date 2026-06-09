"""``kb_resource_list`` MCP tool — list all oh-my-kb resources with local status."""

from __future__ import annotations

from mcp.types import TextContent, Tool

KB_RESOURCE_LIST_TOOL = Tool(
    name="kb_resource_list",
    description=(
        "List all MCP resources available on the server and their local status "
        "(version pulled vs. current server version). Use when the user asks which "
        "skills or resources are installed, whether they are up to date, or wants "
        "an overview of what oh-my-kb provides. Takes no input — the active universe "
        "is server-bound."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
)


async def handle_kb_resource_list(
    arguments: dict[str, object],
) -> list[TextContent]:
    """Return a plain-text table of all resources and their status."""
    from oh_my_kb.cli.manifest import load_manifest
    from oh_my_kb.services.resource_ops import list_resources_with_status

    # Try to load manifest — no error on absence (manifest missing = not installed)
    manifest = None
    manifest_missing = False
    try:
        manifest = load_manifest()
    except FileNotFoundError:
        manifest_missing = True
    except Exception as exc:
        return [TextContent(type="text", text=f"kb_resource_list: error — {exc}")]

    try:
        statuses = list_resources_with_status(manifest)
    except Exception as exc:
        return [TextContent(type="text", text=f"kb_resource_list: error — {exc}")]

    total = len(statuses)
    lines: list[str] = []

    if manifest_missing:
        lines.append(
            f"kb_resource_list: {total} resources disponíveis no servidor "
            "(manifest local não encontrado)"
        )
        lines.append("")
        for s in statuses:
            lines.append(
                f"  {s.resource_id:<30}  servidor: {s.server_version}  (não instalado)"
            )
        lines.append("")
        lines.append(
            "  Execute 'omk resource pull --all' para instalar os resources localmente."
        )
        return [TextContent(type="text", text="\n".join(lines))]

    # Manifest present
    outdated_count = sum(1 for s in statuses if s.is_outdated or not s.is_installed)
    lines.append(f"kb_resource_list: {total} resources disponíveis")
    lines.append("")

    for s in statuses:
        local_ver = s.local_version or "—"
        status_symbol = (
            "● desatualizado" if not s.is_installed or s.is_outdated else "✓ atualizado"
        )
        server_ver = s.server_version
        lines.append(
            f"  {s.resource_id:<25}  local: {local_ver:<10}"
            f"  servidor: {server_ver:<10}  {status_symbol}"
        )

    lines.append("")
    if outdated_count == 0:
        lines.append("  Todos os resources estão atualizados.")
    else:
        word = "desatualizado" if outdated_count == 1 else "desatualizados"
        lines.append(
            f"  {outdated_count} {word}. Use kb_resource_update para atualizar."
        )

    return [TextContent(type="text", text="\n".join(lines))]
