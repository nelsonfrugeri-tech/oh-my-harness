"""Streamable HTTP transport for the knowledge-base MCP server.

The HTTP transport reuses the same ``build_server`` wiring as stdio, so these
tests assert the ASGI app is constructed and the MCP endpoint is mounted. The
full protocol round-trip is exercised manually (`omh serve` + an MCP client);
here we keep a fast, dependency-light construction check.
"""

from __future__ import annotations

from pathlib import Path

from _helpers import StubEmbedder
from starlette.applications import Starlette
from starlette.routing import Mount

from oh_my_harness.kb.mcp.server import build_context, build_http_app
from oh_my_harness.kb.storage import QdrantStore


def _context(tmp_path: Path, store: QdrantStore, embedder: StubEmbedder) -> object:
    return build_context(
        universe="test",
        store=store,
        embedder=embedder,
        notes_root=tmp_path,
    )


def test_build_http_app_returns_starlette(tmp_path: Path) -> None:
    app = build_http_app(_context(tmp_path, QdrantStore(":memory:"), StubEmbedder()))
    assert isinstance(app, Starlette)


def test_mcp_endpoint_is_mounted(tmp_path: Path) -> None:
    app = build_http_app(_context(tmp_path, QdrantStore(":memory:"), StubEmbedder()))
    mounts = [r for r in app.routes if isinstance(r, Mount)]
    assert any(m.path == "/mcp" for m in mounts), "expected an MCP mount at /mcp"


def test_stdio_transport_still_present() -> None:
    # The HTTP transport is additive — the stdio entry point must remain.
    from oh_my_harness.kb.mcp import server

    assert hasattr(server, "main")  # stdio entry point
    assert hasattr(server, "serve_http")  # new HTTP entry point
