"""Agent bootstrap rules template — static loader and dynamic block generator."""

from __future__ import annotations

import datetime
from pathlib import Path

from oh_my_kb.i18n import DEFAULT_LOCALE, resolve_locale_path

_AGENTS_DIR: Path = Path(__file__).parent
_RULES_FILENAME: str = "rules_template.md"


def load_template(locale: str = DEFAULT_LOCALE) -> str:
    """Return the raw rules_template.md for the requested locale, with fallback."""
    path = resolve_locale_path(_AGENTS_DIR, _RULES_FILENAME, locale=locale)
    return path.read_text(encoding="utf-8")


def render_rules(universe: str, locale: str = DEFAULT_LOCALE) -> str:
    """Return the bootstrap rules with ``{universe}`` substituted."""
    return load_template(locale=locale).replace("{universe}", universe)


def render_dynamic_block(universe: str) -> str:
    """Generate the full rules block dynamically from the MCP registry.

    Instead of a static template, this function:
    1. Imports the tool objects directly from ``oh_my_kb.mcp.tools`` (no server
       spin-up needed — they are statically importable Python objects).
    2. Calls ``list_scribe_resources()`` to get the current resource list.
    3. Renders one bullet per tool (using ``TOOL_TRIGGERS`` for the human-readable
       trigger phrase, falling back to the tool description if no trigger exists).
    4. Renders one bullet per resource.

    The result is injected between the sentinel markers by :func:`inject_block`.

    Note: the marker line includes an HTML comment with the generation timestamp
    and the universe name so that stale blocks are easy to diagnose after
    ``omk universe use <other>`` changes the active universe without re-running
    bootstrap.
    """
    from oh_my_kb.agents.harness import TOOL_TRIGGERS
    from oh_my_kb.mcp.resources import list_scribe_resources
    from oh_my_kb.mcp.tools import ALL_TOOLS

    resources = list_scribe_resources()
    # ALL_TOOLS preserves canonical insertion order: write-first for priority.
    tools = ALL_TOOLS

    generated_at = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%dT%H:%MZ")

    lines: list[str] = [
        f"<!-- omk:meta generated:{generated_at} universe:{universe} -->",
        f"## oh-my-kb — Base de Conhecimento (universe: {universe})",
        "",
        "### Tools disponíveis",
        "",
    ]

    for tool in tools:
        trigger = TOOL_TRIGGERS.get(tool.name)
        if trigger is None:
            # Fallback: use the tool description (trimmed to 120 chars to avoid verbosity)
            raw_desc: str = tool.description or ""
            trigger = raw_desc[:120].rstrip() + ("..." if len(raw_desc) > 120 else "")
            trigger += "  # (no trigger configured — using tool description)"
        lines.append(f"- `{tool.name}` — {trigger}")

    lines += [
        "",
        "### Resources disponíveis",
        "",
    ]

    for resource in resources:
        # Use only the first sentence of the description to avoid verbosity in the block.
        desc_full: str = resource.description or resource.name
        first_sentence = desc_full.split(". ")[0].rstrip(".")
        lines.append(f"- `{resource.uri}` — {first_sentence}.")

    lines += [
        "",
        "### Regras gerais",
        "",
        # Rule 1: The universe is server-bound (ADR-002); the LLM must NOT pass it
        # as a parameter — tools have additionalProperties:false with no universe field.
        "- O universe ativo é definido pelo servidor MCP (KB_UNIVERSE) e nunca deve"
        " ser passado como parâmetro nas tools — ele é injetado automaticamente.",
        # Rule 2: Read once per session, not once per call, to avoid redundant reads.
        "- Leia skill://scribe/SKILL.md antes do PRIMEIRO kb_write da sessão.",
        # Rule 3: Precise routing — search for content/theme, tree for structure/existence.
        "- Prefira kb_search quando a pergunta é sobre conteúdo ou tema;"
        " use kb_tree quando a pergunta é sobre o que existe no universe"
        " ou em um projeto específico.",
    ]

    return "\n".join(lines)
