"""``o-kb-mcp`` — stdio server exposing kb_write, kb_search, kb_recent, kb_tree, kb_expand.

Dependencies (``QdrantStore``, ``BGEM3Embedder``, ``Indexer``,
:class:`SearchService`, :class:`RecentService`, :class:`NavigationService`)
are built **once** when the server boots and reused for every tool invocation
— that's the whole point of running an MCP server instead of doing one-shot
CLIs.  The knowledge base is server-bound via ``KB_NAME``; tool inputs cannot
change it.

The handlers themselves live in :mod:`oh_my_harness.kb.mcp.tools` so they can be
unit-tested without touching the SDK; this module only wires them into the
``Server`` instance and runs the stdio transport.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from starlette.applications import Starlette

    from oh_my_harness.kb.mcp.auth import AuthConfig

from oh_my_harness.kb.embedding import BGEM3Embedder, Embedder
from oh_my_harness.kb.mcp.config import get_active_kb, get_active_notes_root
from oh_my_harness.kb.mcp.tools import (
    KB_EXPAND_TOOL,
    KB_RECENT_TOOL,
    KB_SEARCH_TOOL,
    KB_TREE_TOOL,
    KB_WRITE_TOOL,
    handle_kb_expand,
    handle_kb_recent,
    handle_kb_search,
    handle_kb_tree,
    handle_kb_write,
)
from oh_my_harness.kb.services import (
    Indexer,
    NavigationService,
    RecentService,
    SearchService,
)
from oh_my_harness.kb.storage import QdrantStore, get_qdrant_url

SERVER_NAME = "o-kb-mcp"


@dataclass(frozen=True, slots=True)
class KBServerContext:
    """Snapshot of everything the server needs at request time.

    Immutable so multiple coroutines reading the same context can never see
    a half-built dependency graph.
    """

    kb_name: str
    qdrant_url: str
    notes_root: Path
    store: QdrantStore
    embedder: Embedder
    indexer: Indexer
    search_service: SearchService
    recent_service: RecentService
    navigation_service: NavigationService

    # Backward-compatible property for code that still reads .universe.
    @property
    def universe(self) -> str:
        return self.kb_name


def build_context(
    *,
    universe: str | None = None,
    qdrant_url: str | None = None,
    notes_root: Path | None = None,
    store: QdrantStore | None = None,
    embedder: Embedder | None = None,
) -> KBServerContext:
    """Resolve env → concrete deps. Every parameter is overridable for tests.

    The ``universe`` parameter is kept for backward compatibility with existing
    test call sites; it maps directly to the ``kb_name`` field.
    """
    resolved_kb = universe if universe is not None else get_active_kb()
    resolved_url = qdrant_url if qdrant_url is not None else get_qdrant_url()
    resolved_root = (
        notes_root if notes_root is not None else get_active_notes_root(resolved_kb)
    )
    resolved_store = store if store is not None else QdrantStore(resolved_url)
    resolved_embedder = embedder if embedder is not None else BGEM3Embedder()
    indexer = Indexer(
        store=resolved_store,
        embedder=resolved_embedder,
        notes_root=resolved_root,
    )
    search_service = SearchService(store=resolved_store, embedder=resolved_embedder)
    recent_service = RecentService(store=resolved_store, embedder=resolved_embedder)
    navigation_service = NavigationService(store=resolved_store, indexer=indexer)
    return KBServerContext(
        kb_name=resolved_kb,
        qdrant_url=resolved_url,
        notes_root=resolved_root,
        store=resolved_store,
        embedder=resolved_embedder,
        indexer=indexer,
        search_service=search_service,
        recent_service=recent_service,
        navigation_service=navigation_service,
    )


def build_server(context: KBServerContext) -> Server[Any, Any]:
    """Construct a :class:`Server` with all tools registered."""
    server: Server[Any, Any] = Server(SERVER_NAME)

    # mcp's decorator factories aren't typed — silence the strict-mypy
    # noise; the inner function signatures are still typed below.
    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def _list_tools() -> list[Tool]:
        return [
            KB_WRITE_TOOL,
            KB_SEARCH_TOOL,
            KB_RECENT_TOOL,
            KB_TREE_TOOL,
            KB_EXPAND_TOOL,
        ]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "kb_write":
            return await handle_kb_write(context.indexer, context.universe, arguments)
        if name == "kb_search":
            return await handle_kb_search(
                context.search_service, context.universe, arguments
            )
        if name == "kb_recent":
            return await handle_kb_recent(
                context.recent_service, context.universe, arguments
            )
        if name == "kb_tree":
            return await handle_kb_tree(
                context.navigation_service, context.universe, arguments
            )
        if name == "kb_expand":
            return await handle_kb_expand(
                context.navigation_service, context.universe, arguments
            )
        return [TextContent(type="text", text=f"unknown tool: {name}")]

    return server


def _log_startup(context: KBServerContext) -> None:
    print(
        (
            f"{SERVER_NAME} ready\n"
            f"  knowledge base : {context.kb_name}\n"
            f"  qdrant_url     : {context.qdrant_url}\n"
            f"  notes_root     : {context.notes_root}\n"
            f"  tools          : kb_write, kb_search, kb_recent, kb_tree, kb_expand\n"
            f"  model          : bge-m3 (lazy — first call triggers load/download ~2 GB)\n"
            f"  skills         : manage with `omh skills pull|diff|update`\n"
            f"  agents         : manage with `omh agents pull|diff|update`"
        ),
        file=sys.stderr,
        flush=True,
    )


def build_http_app(
    context: KBServerContext,
    *,
    json_response: bool = False,
    stateless: bool = False,
    auth: AuthConfig | None = None,
) -> Starlette:
    """Build a Starlette ASGI app exposing this server over Streamable HTTP.

    Reuses the exact same :func:`build_server` wiring as the stdio transport —
    only the transport differs, so both speak to the same knowledge base and
    the same dependency graph. The MCP endpoint is mounted at ``/mcp``; the
    session manager's task group is bound to the app lifespan so it lives for
    the whole server lifetime.

    When ``auth`` is given the server becomes an OAuth 2.1 Resource Server:
    the ``/mcp`` endpoint requires a valid bearer token and Protected Resource
    Metadata routes are added so remote clients (e.g. Claude's connector) can
    discover the Authorization Server. When ``auth`` is ``None`` the endpoint is
    open — fine for local/stdio-equivalent use, never for public exposure.

    Imports of the web/auth stack are local so the stdio entry point never pulls
    in starlette/uvicorn/jwt.
    """
    from collections.abc import AsyncIterator
    from contextlib import asynccontextmanager

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette as _Starlette
    from starlette.middleware import Middleware
    from starlette.routing import BaseRoute, Mount
    from starlette.types import Receive, Scope, Send

    server = build_server(context)
    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=json_response,
        stateless=stateless,
    )

    async def _handle_mcp(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @asynccontextmanager
    async def _lifespan(_app: _Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    routes: list[BaseRoute]
    middleware: list[Middleware] = []
    if auth is None:
        routes = [Mount("/mcp", app=_handle_mcp)]
    else:
        from oh_my_harness.kb.mcp.auth import build_auth_layer

        protected, prm_routes, middleware = build_auth_layer(auth, _handle_mcp)
        routes = [Mount("/mcp", app=protected), *prm_routes]

    return _Starlette(routes=routes, middleware=middleware, lifespan=_lifespan)


def serve_http(
    host: str,
    port: int,
    kb_name: str | None = None,
    auth: AuthConfig | None = None,
    notes_root: Path | None = None,
) -> None:
    """Run the knowledge-base MCP server over Streamable HTTP (blocking).

    The knowledge base is server-bound (``kb_name`` or ``$KB_NAME``); the bge-m3
    model still loads lazily on the first tool call. stdio is unaffected. When
    ``auth`` is given the endpoint requires OAuth 2.1 bearer tokens. ``notes_root``
    overrides where the bundles are read from (the CLI passes the configured KB
    path so relocations are respected).
    """
    import uvicorn

    context = build_context(universe=kb_name, notes_root=notes_root)
    context.notes_root.mkdir(parents=True, exist_ok=True)
    app = build_http_app(context, auth=auth)
    auth_status = f"OAuth 2.1 ({auth.issuer_url})" if auth else "none (open — local only)"
    print(
        (
            f"{SERVER_NAME} (streamable-http) ready\n"
            f"  knowledge base : {context.kb_name}\n"
            f"  endpoint       : http://{host}:{port}/mcp\n"
            f"  auth           : {auth_status}\n"
            f"  qdrant_url     : {context.qdrant_url}\n"
            f"  notes_root     : {context.notes_root}"
        ),
        file=sys.stderr,
        flush=True,
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


async def _serve() -> None:
    context = build_context()
    context.notes_root.mkdir(parents=True, exist_ok=True)
    server = build_server(context)
    _log_startup(context)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    """``[project.scripts] o-kb-mcp`` entry point."""

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
