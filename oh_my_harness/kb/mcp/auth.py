"""Optional OAuth 2.1 Resource Server support for the HTTP transport.

When the server is exposed publicly (e.g. for Claude's remote connector), MCP
clients require OAuth 2.1: the server advertises its Authorization Server via
Protected Resource Metadata (RFC 9728) and validates the bearer JWT on every
request. We act as a **Resource Server only** — the Authorization Server is
external (e.g. WorkOS AuthKit), so this code never issues tokens, only verifies
them.

stdio and unauthenticated local HTTP are unaffected: auth is wired in only when
an :class:`AuthConfig` is provided (i.e. an issuer + public URL are configured).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import anyio
import httpx
import jwt
from mcp.server.auth.provider import AccessToken, TokenVerifier

if TYPE_CHECKING:
    from starlette.middleware import Middleware
    from starlette.routing import Route
    from starlette.types import ASGIApp


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Resource-server configuration for the HTTP transport.

    Attributes:
        issuer_url: The external Authorization Server (e.g. a WorkOS AuthKit
            issuer). Advertised in the Protected Resource Metadata and used as
            the expected JWT ``iss``.
        resource_url: The public URL of this MCP resource. Used as the RFC 8707
            audience the JWT must carry and as the PRM ``resource``.
        required_scopes: Scopes the token must include (empty = none required).
        jwks_url: JWKS endpoint of the issuer. Discovered from the issuer's
            OpenID configuration when ``None``.
    """

    issuer_url: str
    resource_url: str
    required_scopes: list[str] = field(default_factory=list)
    jwks_url: str | None = None


def _discover_jwks_url(issuer_url: str) -> str:
    config_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    resp = httpx.get(config_url, timeout=10.0)
    resp.raise_for_status()
    jwks_uri = resp.json().get("jwks_uri")
    if not jwks_uri:
        raise ValueError(f"no 'jwks_uri' in OpenID configuration at {config_url}")
    return str(jwks_uri)


def _claim_scopes(claims: dict[str, Any]) -> list[str]:
    scope = claims.get("scope")
    if isinstance(scope, str):
        return scope.split()
    scp = claims.get("scp")
    if isinstance(scp, list):
        return [str(s) for s in scp]
    return []


class JwtTokenVerifier(TokenVerifier):
    """Verify RS256 JWTs issued by an external OAuth 2.1 Authorization Server.

    Validates signature (against the issuer's JWKS), ``aud`` (must equal the
    configured resource URL), ``iss`` and expiry, then enforces required scopes.
    Returns ``None`` on any failure — the bearer middleware turns that into a 401.
    """

    def __init__(self, config: AuthConfig) -> None:
        self._config = config
        jwks_url = config.jwks_url or _discover_jwks_url(config.issuer_url)
        # PyJWKClient caches keys and fetches lazily on first use.
        self._jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            signing_key = await anyio.to_thread.run_sync(
                self._jwks_client.get_signing_key_from_jwt, token
            )
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._config.resource_url,
                issuer=self._config.issuer_url,
                options={"require": ["exp", "iat"]},
            )
        except Exception:
            return None

        scopes = _claim_scopes(claims)
        if self._config.required_scopes and not set(self._config.required_scopes) <= set(
            scopes
        ):
            return None

        expires_at = claims.get("exp")
        return AccessToken(
            token=token,
            client_id=str(claims.get("client_id") or claims.get("azp") or ""),
            scopes=scopes,
            expires_at=int(expires_at) if expires_at is not None else None,
            subject=str(claims["sub"]) if "sub" in claims else None,
            claims=claims,
        )


def build_auth_layer(
    config: AuthConfig, mcp_handler: ASGIApp
) -> tuple[ASGIApp, list[Route], list[Middleware]]:
    """Return the auth-wrapped MCP handler, the PRM routes, and the middleware.

    Mirrors how the MCP SDK's high-level server wires a resource server:
    a bearer auth backend authenticates every request, the ``/mcp`` endpoint is
    wrapped to require a valid token, and the Protected Resource Metadata routes
    are served unauthenticated so clients can discover the Authorization Server.
    """
    from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
    from mcp.server.auth.middleware.bearer_auth import (
        BearerAuthBackend,
        RequireAuthMiddleware,
    )
    from mcp.server.auth.routes import (
        build_resource_metadata_url,
        create_protected_resource_routes,
    )
    from pydantic import AnyHttpUrl
    from starlette.middleware import Middleware
    from starlette.middleware.authentication import AuthenticationMiddleware

    verifier = JwtTokenVerifier(config)
    resource_url = AnyHttpUrl(config.resource_url)
    issuer_url = AnyHttpUrl(config.issuer_url)
    resource_metadata_url = build_resource_metadata_url(resource_url)

    protected_handler: ASGIApp = RequireAuthMiddleware(
        mcp_handler, config.required_scopes, resource_metadata_url
    )
    prm_routes = create_protected_resource_routes(
        resource_url, [issuer_url], config.required_scopes or None
    )
    middleware = [
        Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(verifier)),
        Middleware(AuthContextMiddleware),
    ]
    return protected_handler, prm_routes, middleware
