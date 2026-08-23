from __future__ import annotations

import base64
import hashlib
import http.client
import importlib.util
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import cast
from unittest.mock import patch


_ROOT = Path(__file__).resolve().parents[2]
_SERVER = _ROOT / "skills/site-expose/scripts/auth_server.py"


class SiteServerIntegrationTest(unittest.TestCase):
    def test_loopback_server_enforces_authentication_over_http(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            content = b"<h1>approved</h1>"
            site.joinpath("index.html").write_bytes(content)
            module = self._load_server(site, content)
            try:
                server = ThreadingHTTPServer(("127.0.0.1", 0), module.AuthHandler)
            except PermissionError:
                self.skipTest("the execution sandbox blocks loopback socket binding")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = cast(tuple[str, int], server.server_address)
                self.assertEqual("127.0.0.1", host)
                unauthorized_status, _ = self._request(port)
                self.assertEqual(401, unauthorized_status)
                authorized = self._request(port, self._authorization())
                self.assertEqual((200, content), authorized)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def _load_server(self, site: Path, content: bytes) -> ModuleType:
        spec = importlib.util.spec_from_file_location("site_auth_server_integration", _SERVER)
        if spec is None or spec.loader is None:
            self.fail("unable to load auth server module")
        module = importlib.util.module_from_spec(spec)
        environment = {
            "SITE_ROOT": str(site),
            "SITE_SHA256": hashlib.sha256(content).hexdigest(),
            "AUTH_USER": "viewer",
            "AUTH_PW": "one-time-secret",
            "PORT": "8822",
        }
        with patch.dict(os.environ, environment):
            spec.loader.exec_module(module)
        return module

    def _request(
        self, port: int, authorization: str | None = None
    ) -> tuple[int, bytes]:
        headers = {} if authorization is None else {"Authorization": authorization}
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request("GET", "/index.html", headers=headers)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def _authorization(self) -> str:
        token = base64.b64encode(b"viewer:one-time-secret").decode("ascii")
        return f"Basic {token}"
