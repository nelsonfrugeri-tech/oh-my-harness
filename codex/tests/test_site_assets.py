from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import os
import tempfile
import unittest
from email.message import Message
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast
from unittest.mock import Mock, patch


_ROOT = Path(__file__).resolve().parents[2]
_SERVER = _ROOT / "skills/site-expose/scripts/auth_server.py"


class _Handler(Protocol):
    path: str
    headers: Message
    wfile: io.BytesIO
    send_response: Mock
    send_header: Mock
    end_headers: Mock
    send_error: Mock

    def _authed(self) -> bool: ...

    def _serve(self, include_body: bool) -> None: ...


class SiteAuthServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self._site = Path(self._temporary.name) / "site"
        self._site.mkdir()
        self._site.joinpath("index.html").write_text("<h1>approved</h1>", encoding="utf-8")
        self._site.joinpath("private.txt").write_text("must not leak", encoding="utf-8")
        self._module = self._load_server()

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_authentication_uses_the_expected_header(self) -> None:
        handler = self._handler("/index.html")
        self.assertFalse(handler._authed())

        handler.headers["Authorization"] = self._authorization()

        self.assertTrue(handler._authed())

    def test_serves_only_the_approved_index(self) -> None:
        approved = self._handler("/index.html")
        rejected = self._handler("/private.txt")

        approved._serve(include_body=True)
        rejected._serve(include_body=True)

        approved.send_response.assert_called_once_with(200)
        self.assertEqual(b"<h1>approved</h1>", approved.wfile.getvalue())
        rejected.send_error.assert_called_once_with(404)

    def test_disables_caching_and_content_sniffing(self) -> None:
        handler = self._handler("/")

        with patch.object(BaseHTTPRequestHandler, "end_headers") as inherited:
            self._module.AuthHandler.end_headers(handler)

        handler.send_header.assert_any_call("Cache-Control", "no-store")
        handler.send_header.assert_any_call("X-Content-Type-Options", "nosniff")
        inherited.assert_called_once_with()

    def test_rejects_a_symlinked_index(self) -> None:
        root = Path(self._temporary.name) / "linked-site"
        root.mkdir()
        root.joinpath("index.html").symlink_to(self._site / "index.html")

        with self.assertRaises(SystemExit):
            self._module._approved_content(root, "0" * 64)

    def test_serves_the_approved_snapshot_after_source_mutation(self) -> None:
        self._site.joinpath("index.html").write_text("<h1>changed</h1>", encoding="utf-8")
        handler = self._handler("/")

        handler._serve(include_body=True)

        self.assertEqual(b"<h1>approved</h1>", handler.wfile.getvalue())

    def test_rejects_content_that_does_not_match_the_approved_hash(self) -> None:
        with self.assertRaises(SystemExit):
            self._module._approved_content(self._site, "0" * 64)

    def test_server_is_bound_to_loopback_in_the_entrypoint(self) -> None:
        source = _SERVER.read_text(encoding="utf-8")

        self.assertIn('ThreadingHTTPServer(("127.0.0.1", PORT)', source)

    def _load_server(self) -> ModuleType:
        spec = importlib.util.spec_from_file_location("site_auth_server_test", _SERVER)
        if spec is None or spec.loader is None:
            self.fail("unable to load auth server module")
        module = importlib.util.module_from_spec(spec)
        environment = {
            "SITE_ROOT": str(self._site),
            "SITE_SHA256": hashlib.sha256(b"<h1>approved</h1>").hexdigest(),
            "AUTH_USER": "viewer",
            "AUTH_PW": "one-time-secret",
            "PORT": "8822",
        }
        with patch.dict(os.environ, environment):
            spec.loader.exec_module(module)
        return module

    def _handler(self, path: str) -> _Handler:
        handler = self._module.AuthHandler.__new__(self._module.AuthHandler)
        handler.path = path
        handler.headers = Message()
        handler.wfile = io.BytesIO()
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.send_error = Mock()
        return cast(_Handler, handler)

    def _authorization(self) -> str:
        token = base64.b64encode(b"viewer:one-time-secret").decode("ascii")
        return f"Basic {token}"
