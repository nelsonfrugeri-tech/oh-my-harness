#!/usr/bin/env python3
"""Static file server with HTTP basic auth — the local half of a password-protected tunnel.

The tunnel engine (cloudflared, ngrok, …) only forwards traffic; the password lives here so
the protection holds no matter which engine is in front of it.

Credentials come from the environment so they never land in a file on disk:

    SITE_ROOT=/abs/path/to/site SITE_SHA256="$SHA256" AUTH_USER="$USER" AUTH_PW="$PW" PORT=8822 \
        python3 auth_server.py

Binds to 127.0.0.1 only — the tunnel is the sole path in from the outside.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

REALM: Final = "analysis"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"{name} is required (set it in the environment, never in this file)")
    return value


def _approved_content(root: Path, expected_sha256: str) -> bytes:
    candidate = root / "index.html"
    if not root.is_dir() or not candidate.is_file() or candidate.is_symlink():
        sys.exit(f"SITE_ROOT must contain a regular, non-symlink index.html: {root}")
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        sys.exit("SITE_SHA256 must be a lowercase SHA-256 digest")
    content = candidate.read_bytes()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if not hmac.compare_digest(actual_sha256, expected_sha256):
        sys.exit("index.html does not match the approved SITE_SHA256")
    return content


def _port() -> int:
    value = int(os.environ.get("PORT", "8822"))
    if not 1 <= value <= 65535:
        sys.exit("PORT must be between 1 and 65535")
    return value


SITE_ROOT: Final = Path(_required("SITE_ROOT"))
AUTH_USER: Final = _required("AUTH_USER")
AUTH_PW: Final = _required("AUTH_PW")
SITE_SHA256: Final = _required("SITE_SHA256")
PORT: Final = _port()
SITE_CONTENT: Final = _approved_content(SITE_ROOT, SITE_SHA256)

EXPECTED: Final = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PW}".encode()).decode()


class AuthHandler(BaseHTTPRequestHandler):
    """Serve only the approved index file to authenticated requests."""

    server_version = "omh-site"
    sys_version = ""

    def _authed(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return hmac.compare_digest(supplied, EXPECTED)

    def _challenge(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", f'Basic realm="{REALM}"')
        self.end_headers()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self) -> None:
        if not self._authed():
            self._challenge()
            return
        self._serve(include_body=True)

    def do_HEAD(self) -> None:
        if not self._authed():
            self._challenge()
            return
        self._serve(include_body=False)

    def _serve(self, include_body: bool) -> None:
        if urlsplit(self.path).path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(SITE_CONTENT)))
        self.end_headers()
        if include_body:
            self.wfile.write(SITE_CONTENT)

    def log_message(self, *args: object) -> None:
        """Silent: request logs would leak the tunnel's traffic into the shell."""


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), AuthHandler).serve_forever()
