from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from lib.integration_transport import McpInspector, McpState, graphify_server


@dataclass(frozen=True)
class CodexIntegrations:
    codex_home: Path

    def install(self) -> tuple[str, ...]:
        if shutil.which("codex") is None:
            return ("pending: Codex CLI is not available",)
        return (
            self._install_deja(),
            self._install_graphify(),
            self._install_x_docs(),
            self._check_x_api(),
        )

    def _install_deja(self) -> str:
        executable = shutil.which("deja")
        if executable is None:
            return "pending: install Deja, then rerun this installer"
        state = self._mcp_state(
            "deja",
            {"type": "stdio", "command": executable, "args": ["mcp"], "cwd": None},
        )
        if state is McpState.MATCHES:
            return "ok: Deja MCP (transcript indexing unchanged)"
        if state is McpState.DRIFTED:
            return (
                "pending: Deja MCP exists with a different transport; review manually"
            )
        command = [
            "codex",
            "mcp",
            "add",
            "deja",
            "--",
            executable,
            "mcp",
        ]
        configured = self._run_mcp_add(command, "Deja MCP")
        if configured.startswith("pending:"):
            return configured
        return "configured: Deja MCP (transcript indexing disabled)"

    def _install_graphify(self) -> str:
        executable = self._graphify_server()
        if executable is None:
            return "pending: install graphifyy with its MCP server, then rerun this installer"
        state = self._mcp_state(
            "graphify",
            {"type": "stdio", "command": str(executable), "args": [], "cwd": None},
        )
        if state is McpState.MATCHES:
            return "ok: Graphify MCP"
        if state is McpState.DRIFTED:
            return "pending: Graphify MCP exists with a different transport; review manually"
        command = [
            "codex",
            "mcp",
            "add",
            "graphify",
            "--",
            str(executable),
        ]
        return self._run_mcp_add(command, "Graphify MCP")

    def _install_x_docs(self) -> str:
        state = self._mcp_state(
            "x-docs", {"type": "streamable_http", "url": "https://docs.x.com/mcp"}
        )
        if state is McpState.MATCHES:
            return "ok: X Docs MCP"
        if state is McpState.DRIFTED:
            return (
                "pending: X Docs MCP exists with a different transport; review manually"
            )
        command = ["codex", "mcp", "add", "x-docs", "--url", "https://docs.x.com/mcp"]
        return self._run_mcp_add(command, "X Docs MCP")

    def _check_x_api(self) -> str:
        if self._mcp_exists("xapi"):
            return "ok: X API MCP configured; authentication not verified"
        return (
            "optional: X API MCP requires xurl, OAuth approval, and a paid X API plan"
        )

    def _mcp_exists(self, name: str) -> bool:
        return McpInspector(self.codex_home).exists(name)

    def _mcp_state(self, name: str, expected: Mapping[str, object]) -> McpState:
        return McpInspector(self.codex_home).state(name, expected)

    def _graphify_server(self) -> Path | None:
        return graphify_server()

    def _run_mcp_add(self, command: list[str], label: str) -> str:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._environment(),
        )
        if result.returncode != 0:
            return f"pending: {label} registration failed: {result.stderr.strip()}"
        return f"configured: {label}"

    def _environment(self) -> dict[str, str]:
        return {**os.environ, "CODEX_HOME": str(self.codex_home)}
