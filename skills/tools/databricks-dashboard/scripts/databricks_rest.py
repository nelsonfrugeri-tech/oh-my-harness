"""Portable Databricks REST client using only the Python standard library."""

from __future__ import annotations

import ipaddress
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

_RESOURCE_ID = re.compile(r"^[A-Za-z0-9-]{1,128}$")


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("Databricks API redirects are refused")


@dataclass(frozen=True)
class DatabricksClient:
    host: str
    token: str
    timeout_seconds: float

    @classmethod
    def from_environment(cls, token_env: str) -> DatabricksClient:
        resolved_host = os.environ.get("DATABRICKS_HOST", "")
        token = os.environ.get(token_env, "")
        if not resolved_host or not token:
            raise ValueError(
                "set DATABRICKS_HOST and the selected token environment variable"
            )
        trusted_hosts = tuple(
            item.strip().lower()
            for item in os.environ.get("DATABRICKS_TRUSTED_HOSTS", "").split(",")
            if item.strip()
        )
        _validate_host(resolved_host, trusted_hosts)
        timeout = float(os.environ.get("DATABRICKS_HTTP_TIMEOUT_SECONDS", "30"))
        if timeout <= 0:
            raise ValueError("DATABRICKS_HTTP_TIMEOUT_SECONDS must be positive")
        return cls(resolved_host.rstrip("/"), token, timeout)

    def request(
        self, method: str, path: str, payload: Mapping[str, object] | None = None
    ) -> dict[str, object]:
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(f"{self.host}{path}", data=body, method=method)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Content-Type", "application/json")
        try:
            with build_opener(RejectRedirects()).open(
                request, timeout=self.timeout_seconds
            ) as response:
                return _json_response(response.read())
        except HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"Databricks {error.code}: {detail}") from error


def _json_response(content: bytes) -> dict[str, object]:
    parsed: object = json.loads(content.decode() or "{}")
    if not isinstance(parsed, dict):
        raise TypeError("Databricks response must be a JSON object")
    return cast(dict[str, object], parsed)


def _validate_host(host: str, trusted_hosts: tuple[str, ...]) -> None:
    parsed = urlparse(host)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname or parsed.username or parsed.password:
        raise ValueError("DATABRICKS_HOST must be an HTTPS origin without credentials")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("DATABRICKS_HOST must not use an IP address")
    known_suffix = hostname.endswith((".databricks.com", ".azuredatabricks.net"))
    if not known_suffix and hostname not in trusted_hosts:
        raise ValueError("DATABRICKS_HOST is not a trusted Databricks workspace host")


def validated_resource_id(value: str, label: str = "resource ID") -> str:
    if not _RESOURCE_ID.fullmatch(value):
        raise ValueError(f"{label} contains invalid characters")
    return value
