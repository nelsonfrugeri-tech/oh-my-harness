"""Wiring tests for the o-agents-mcp server.

We don't spin up the stdio transport here.  We prove the wiring at the
function level:

1. ``build_context`` returns an :class:`AgentsServerContext` instance.
2. ``build_server`` registers handlers for ``ListToolsRequest`` and
   ``CallToolRequest``.
3. The ``list_tools`` handler returns ``[DEVELOP_LEAP_UPDATE_TOOL]``.
4. The ``call_tool`` handler dispatches ``develop_leap_update`` to the handler.
5. The ``call_tool`` handler returns a ``TextContent`` fallback for unknown names.
6. ``main`` is callable and installs a SIGTERM handler (checked via signal.getsignal).
"""

from __future__ import annotations

import signal
from unittest.mock import patch

from oh_my_harness.agents.mcp.server import (
    AgentsServerContext,
    build_context,
    build_server,
)

# ---------------------------------------------------------------------------
# 1. build_context
# ---------------------------------------------------------------------------


def test_build_context_returns_context() -> None:
    ctx = build_context()
    assert isinstance(ctx, AgentsServerContext)


# ---------------------------------------------------------------------------
# 2. build_server — handler registration
# ---------------------------------------------------------------------------


def test_build_server_registers_handlers() -> None:
    from mcp.types import CallToolRequest, ListToolsRequest

    ctx = build_context()
    server = build_server(ctx)

    assert server.name == "o-agents-mcp"
    assert ListToolsRequest in server.request_handlers, "list_tools handler not registered"
    assert CallToolRequest in server.request_handlers, "call_tool handler not registered"


# ---------------------------------------------------------------------------
# 3. list_tools returns [DEVELOP_LEAP_UPDATE_TOOL]
# ---------------------------------------------------------------------------


async def test_list_tools_returns_develop_leap() -> None:
    from mcp.types import ListToolsRequest

    from oh_my_harness.agents.mcp.tools import DEVELOP_LEAP_UPDATE_TOOL

    ctx = build_context()
    server = build_server(ctx)

    handler = server.request_handlers[ListToolsRequest]
    request = ListToolsRequest(method="tools/list")
    response = await handler(request)
    # MCP SDK wraps the result in ServerResult with a .root attribute.
    tools = response.root.tools  # type: ignore[union-attr]
    assert len(tools) == 1
    assert tools[0].name == DEVELOP_LEAP_UPDATE_TOOL.name


# ---------------------------------------------------------------------------
# 4. call_tool unknown returns TextContent with "unknown tool:"
# ---------------------------------------------------------------------------


async def test_call_tool_unknown_returns_text() -> None:
    from mcp.types import CallToolRequest, CallToolRequestParams, TextContent

    ctx = build_context()
    server = build_server(ctx)

    handler = server.request_handlers[CallToolRequest]
    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="anything", arguments={}),
    )
    response = await handler(request)
    contents = response.root.content  # type: ignore[union-attr]
    assert len(contents) == 1
    item = contents[0]
    assert isinstance(item, TextContent)
    assert item.text.startswith("unknown tool: ")
    assert "anything" in item.text


# ---------------------------------------------------------------------------
# 4b. call_tool dispatches develop_leap_update to its handler
# ---------------------------------------------------------------------------


async def test_call_tool_develop_leap_dispatches() -> None:
    from unittest.mock import AsyncMock, patch

    from mcp.types import CallToolRequest, CallToolRequestParams, TextContent

    ctx = build_context()
    server = build_server(ctx)

    mock_result = [TextContent(type="text", text="develop_leap mocked")]

    handler = server.request_handlers[CallToolRequest]
    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="develop_leap_update", arguments={}),
    )

    with patch(
        "oh_my_harness.agents.mcp.server.handle_develop_leap_update",
        new=AsyncMock(return_value=mock_result),
    ):
        response = await handler(request)

    contents = response.root.content  # type: ignore[union-attr]
    assert len(contents) == 1
    assert isinstance(contents[0], TextContent)
    assert "develop_leap mocked" in contents[0].text


# ---------------------------------------------------------------------------
# 5. main installs SIGTERM handler
# ---------------------------------------------------------------------------


def test_main_handles_sigterm_signal_setup() -> None:
    """main() must be callable and register a SIGTERM handler before running."""
    from oh_my_harness.agents.mcp.server import main

    assert callable(main)

    # Intercept asyncio.run so we don't start the transport.
    # Close the coroutine in the side_effect to avoid the "coroutine was
    # never awaited" RuntimeWarning.
    import inspect

    def _close_coro(coro: object) -> None:
        if inspect.iscoroutine(coro):
            coro.close()  # type: ignore[union-attr]

    with patch("oh_my_harness.agents.mcp.server.asyncio.run", side_effect=_close_coro):
        main()

    handler = signal.getsignal(signal.SIGTERM)
    assert callable(handler), "SIGTERM handler was not installed"
