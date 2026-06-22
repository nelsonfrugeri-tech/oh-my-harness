"""OAuth 2.1 Resource Server layer for the HTTP transport.

Verifies the token-rejection path and the Starlette wiring (Protected Resource
Metadata served, /mcp requires a token) without needing a real Authorization
Server — JWKS discovery is skipped by passing ``jwks_url`` explicitly.
"""

from __future__ import annotations

from pathlib import Path

from _helpers import StubEmbedder
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from oh_my_harness.kb.mcp.auth import AuthConfig, JwtTokenVerifier, _claim_scopes
from oh_my_harness.kb.mcp.server import build_context, build_http_app
from oh_my_harness.kb.storage import QdrantStore

_AUTH = AuthConfig(
    issuer_url="https://auth.example.com",
    resource_url="https://kb.example.com/mcp",
    jwks_url="https://auth.example.com/jwks",  # set → no network discovery
)


def _app(tmp_path: Path, *, auth: AuthConfig | None) -> Starlette:
    context = build_context(
        universe="test",
        store=QdrantStore(":memory:"),
        embedder=StubEmbedder(),
        notes_root=tmp_path,
    )
    return build_http_app(context, auth=auth)


def test_claim_scopes_handles_both_shapes() -> None:
    assert _claim_scopes({"scope": "a b c"}) == ["a", "b", "c"]
    assert _claim_scopes({"scp": ["x", "y"]}) == ["x", "y"]
    assert _claim_scopes({}) == []


async def test_verify_token_rejects_invalid_token() -> None:
    verifier = JwtTokenVerifier(_AUTH)
    assert await verifier.verify_token("not-a-real-jwt") is None


def test_no_auth_app_has_only_mcp_mount(tmp_path: Path) -> None:
    app = _app(tmp_path, auth=None)
    paths = [r.path for r in app.routes if isinstance(r, Mount)]
    assert paths == ["/mcp"]
    # No protected-resource-metadata route when auth is off.
    assert not any(
        isinstance(r, Route) and "oauth-protected-resource" in r.path for r in app.routes
    )


def test_auth_app_serves_protected_resource_metadata(tmp_path: Path) -> None:
    app = _app(tmp_path, auth=_AUTH)
    # RFC 9728: the metadata path carries the resource's path suffix (/mcp).
    with TestClient(app) as client:
        resp = client.get("/.well-known/oauth-protected-resource/mcp")
    assert resp.status_code == 200
    body = resp.json()
    assert body["resource"] == "https://kb.example.com/mcp"
    assert any(
        s.rstrip("/") == "https://auth.example.com" for s in body["authorization_servers"]
    )


def test_auth_app_requires_token_on_mcp(tmp_path: Path) -> None:
    app = _app(tmp_path, auth=_AUTH)
    with TestClient(app) as client:
        resp = client.get("/mcp/", headers={"Accept": "text/event-stream"})
    assert resp.status_code == 401
