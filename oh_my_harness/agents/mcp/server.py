"""``o-agents-mcp`` — agents-side stdio MCP server.

Hosts agent-facing tools.  Currently registers ``develop_leap_update``
(issue #56).  Future agent tools land here by extending
:func:`build_server`.

Structure mirrors ``oh_my_harness.kb.mcp.server``:
- :class:`AgentsServerContext` — frozen dataclass for runtime deps
- :func:`build_context` — fabricates the context from env
- :func:`build_server` — wires the :class:`Server` with tool handlers
- :func:`_log_startup` — logs boot message to stderr
- :func:`_serve` — asyncio coroutine that runs the stdio transport
- :func:`main` — entry point (registered as ``o-agents-mcp`` in pyproject.toml)
"""

from __future__ import annotations

import asyncio
import signal
import sys
from dataclasses import dataclass
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from oh_my_harness.agents.mcp.tools import DEVELOP_LEAP_UPDATE_TOOL, handle_develop_leap_update

SERVER_NAME = "o-agents-mcp"


@dataclass(frozen=True, slots=True)
class AgentsServerContext:
    """Runtime snapshot for the agents MCP server.

    Currently no fields — ``develop_leap_update`` reads ``ANTHROPIC_API_KEY``
    from env at call time.  Concrete deps will be added here when tools
    need shared state (e.g. an LLM client pool).
    """


def build_context() -> AgentsServerContext:
    """Construct the server context from the current environment."""
    return AgentsServerContext()


def build_server(context: AgentsServerContext) -> Server[Any, Any]:
    """Construct a :class:`Server` with the agents tools registered.

    Args:
        context: Runtime snapshot (unused while no tool needs shared state).

    Returns:
        Configured :class:`Server` instance ready to run the stdio transport.
    """
    server: Server[Any, Any] = Server(SERVER_NAME)

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def _list_tools() -> list[Tool]:
        return [DEVELOP_LEAP_UPDATE_TOOL]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "develop_leap_update":
            return await handle_develop_leap_update(arguments)
        return [TextContent(type="text", text=f"unknown tool: {name}")]

    return server


def _log_startup(context: AgentsServerContext) -> None:
    print(
        (
            f"{SERVER_NAME} ready\n"
            f"  tools      : develop_leap_update"
        ),
        file=sys.stderr,
        flush=True,
    )


async def _serve() -> None:
    context = build_context()
    server = build_server(context)
    _log_startup(context)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    """``[project.scripts] o-agents-mcp`` entry point."""

    def _handle_sigterm(signum: int, frame: object) -> None:
        # SIGTERM is the standard shutdown signal in containers and systemd.
        # Without this handler asyncio.run raises SystemExit with no message,
        # making container logs silent on graceful shutdown.
        print(f"{SERVER_NAME} stopped (SIGTERM)", file=sys.stderr)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        print(f"{SERVER_NAME} stopped", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    main()
