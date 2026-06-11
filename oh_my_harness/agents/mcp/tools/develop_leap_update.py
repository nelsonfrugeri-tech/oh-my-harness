"""``develop_leap_update`` MCP tool — extract and persist user preferences."""

from __future__ import annotations

import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from oh_my_harness.agents.preferences.block import render_block_with_insights
from oh_my_harness.agents.preferences.llm import MissingAnthropicKeyError, extract_preferences
from oh_my_harness.agents.preferences.markers import USER_PREFS_END, USER_PREFS_START
from oh_my_harness.agents.preferences.sessions import read_recent_user_prompts
from oh_my_harness.kb.agents.injector import inject_block

DEVELOP_LEAP_UPDATE_TOOL = Tool(
    name="develop_leap_update",
    description=(
        "Lê as sessões recentes do Claude Code, extrai sinais de preferência do "
        "usuário via LLM e atualiza a seção '## Preferências do Usuário' em "
        "~/.claude/CLAUDE.md.  "
        "Use quando o usuário disser: 'atualize minhas preferências', "
        "'aprenda com minhas sessões' ou 'o que você sabe sobre mim'."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
)


async def handle_develop_leap_update(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Execute ``develop_leap_update``.

    Reads recent user prompts from Claude Code session files, calls the Claude
    API to extract preference signals, then injects the updated block into
    ``~/.claude/CLAUDE.md``.

    Returns a :class:`~mcp.types.TextContent` summary describing the action
    taken plus a short preview of the extracted insights.
    """
    # 1. Read recent sessions
    curated = read_recent_user_prompts()
    if not curated:
        return [
            TextContent(
                type="text",
                text=(
                    "develop_leap_update: nenhuma sessão encontrada em "
                    "~/.claude/projects/.  Execute o Claude Code em algum projeto "
                    "primeiro para gerar histórico de sessões."
                ),
            )
        ]

    # 2. Extract preferences via LLM
    try:
        insights = extract_preferences(curated)
    except MissingAnthropicKeyError as exc:
        return [
            TextContent(
                type="text",
                text=(
                    f"develop_leap_update: erro de configuração — {exc}  "
                    "Defina ANTHROPIC_API_KEY no ambiente do servidor MCP e tente novamente."
                ),
            )
        ]

    # 3. Build the new block
    now_iso = datetime.now(tz=UTC).date().isoformat()
    new_block = render_block_with_insights(
        now_iso=now_iso,
        system=platform.system(),
        machine=platform.node(),
        locale="pt-BR",
        insights_md=insights,
    )

    # 4. Inject into ~/.claude/CLAUDE.md
    target = Path.home() / ".claude" / "CLAUDE.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    current = target.read_text(encoding="utf-8") if target.exists() else None
    new_content, action = inject_block(
        current,
        new_block,
        start_marker=USER_PREFS_START,
        end_marker=USER_PREFS_END,
    )
    if action.value != "unchanged":
        target.write_text(new_content, encoding="utf-8")

    # 5. Build summary response
    preview = insights[:200].rstrip()
    if len(insights) > 200:
        preview += "..."

    return [
        TextContent(
            type="text",
            text=(
                f"develop_leap_update: {action.value.upper()}  \n"
                f"Arquivo: {target}  \n"
                f"Prévia dos sinais extraídos:\n{preview}"
            ),
        )
    ]
