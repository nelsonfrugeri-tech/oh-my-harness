from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


def graphify_server() -> Path | None:
    current = shutil.which("graphify-mcp")
    legacy = shutil.which("graphify-mcp-server")
    candidates = (
        Path(current) if current else Path("/__missing__"),
        Path(legacy) if legacy else Path("/__missing__"),
        Path.home() / ".local/bin/graphify-mcp",
        Path.home() / "projects/mcps/graphify/.venv/bin/graphify-mcp-server",
        Path.home() / ".local/bin/graphify-mcp-server",
    )
    return next(
        (path for path in candidates if path.is_file() and os.access(path, os.X_OK)),
        None,
    )


class McpState(Enum):
    MISSING = "missing"
    MATCHES = "matches"
    DRIFTED = "drifted"


@dataclass(frozen=True)
class McpInspector:
    codex_home: Path

    def state(self, name: str, expected: Mapping[str, object]) -> McpState:
        result = subprocess.run(
            ["codex", "mcp", "get", name, "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=self._environment(),
        )
        if result.returncode != 0:
            return McpState.MISSING
        try:
            payload = json.loads(result.stdout)
            transport = payload["transport"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return McpState.DRIFTED
        if not isinstance(transport, dict):
            return McpState.DRIFTED
        matches = all(transport.get(key) == value for key, value in expected.items())
        return McpState.MATCHES if matches else McpState.DRIFTED

    def exists(self, name: str) -> bool:
        result = subprocess.run(
            ["codex", "mcp", "get", name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            env=self._environment(),
        )
        return result.returncode == 0

    def _environment(self) -> dict[str, str]:
        return {**os.environ, "CODEX_HOME": str(self.codex_home)}
