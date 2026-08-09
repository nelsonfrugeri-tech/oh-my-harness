from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class CodexIntegrations:
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
            return "pending: install Deja, then run `deja install codex`"
        result = subprocess.run(
            [executable, "install", "codex"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"pending: Deja Codex integration failed: {result.stderr.strip()}"
        command = [
            "codex",
            "mcp",
            "add",
            "--env",
            "DEJA_INCLUDE_SUBAGENTS=1",
            "deja",
            "--",
            executable,
            "mcp",
        ]
        configured = self._run_mcp_add(command, "Deja MCP with subagent indexing")
        if configured.startswith("pending:"):
            return configured
        return "configured: Deja hooks and MCP with subagent indexing"

    def _install_graphify(self) -> str:
        if self._mcp_exists("graphify"):
            return "ok: Graphify MCP"
        executable = self._graphify_server()
        if executable is None:
            return "pending: install graphifyy with its MCP server, then rerun this installer"
        command = [
            "codex",
            "mcp",
            "add",
            "--env",
            "GRAPHIFY_PROJECT_DIR=.",
            "graphify",
            "--",
            str(executable),
        ]
        return self._run_mcp_add(command, "Graphify MCP")

    def _install_x_docs(self) -> str:
        if self._mcp_exists("x-docs"):
            return "ok: X Docs MCP"
        command = ["codex", "mcp", "add", "x-docs", "--url", "https://docs.x.com/mcp"]
        return self._run_mcp_add(command, "X Docs MCP")

    def _check_x_api(self) -> str:
        if self._mcp_exists("xapi"):
            return "ok: authenticated X API MCP"
        return "optional: X API MCP requires xurl, OAuth approval, and a paid X API plan"

    def _mcp_exists(self, name: str) -> bool:
        result = subprocess.run(
            ["codex", "mcp", "get", name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        return result.returncode == 0

    def _graphify_server(self) -> Optional[Path]:
        discovered = shutil.which("graphify-mcp-server")
        candidates = (
            Path(discovered) if discovered else Path("/__missing__"),
            Path.home() / "projects/mcps/graphify/.venv/bin/graphify-mcp-server",
            Path.home() / ".local/bin/graphify-mcp-server",
        )
        return next((path for path in candidates if path.is_file()), None)

    def _run_mcp_add(self, command: list[str], label: str) -> str:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"pending: {label} registration failed: {result.stderr.strip()}"
        return f"configured: {label}"
