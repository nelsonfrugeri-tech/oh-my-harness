"""Natural-language trigger phrases for the o-agents-mcp tools.

Kept in a dedicated module (separate from ``oh_my_harness.kb.agents.harness``)
so that the agents package has no hard import dependency on the kb package, and
``render_dynamic_block`` can import only what it needs from each side.
"""

from __future__ import annotations

# Maps tool name → human-readable PT-BR trigger phrase(s).
AGENTS_TOOL_TRIGGERS: dict[str, str] = {
    "develop_leap_update": (
        "atualize minhas preferências, aprenda com minhas sessões, o que você sabe sobre mim"
    ),
}
