from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from lib.plugin_integrations import PluginIntegrations


class CodexIntegrations:
    def install(self) -> tuple[str, ...]:
        if shutil.which("codex") is None:
            return ("pending: CLI do Codex não está disponível",)
        return (
            self._install_deja(),
            self._install_graphify(),
            self._install_langchain(),
        )

    def _install_langchain(self) -> str:
        source_root = Path(__file__).resolve().parents[2]
        return PluginIntegrations(source_root).install()

    def _install_deja(self) -> str:
        executable = shutil.which("deja")
        if executable is None:
            return "pending: instale Deja e execute `deja install codex`"
        result = subprocess.run(
            [executable, "install", "codex"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"pending: a integração Deja com Codex falhou: {result.stderr.strip()}"
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
        configured = self._run_mcp_add(command, "MCP Deja com indexação de subagents")
        if configured.startswith("pending:"):
            return configured
        return "configured: hooks e MCP Deja com indexação de subagents"

    def _install_graphify(self) -> str:
        if self._mcp_exists("graphify"):
            return "ok: MCP Graphify"
        executable = self._graphify_server()
        if executable is None:
            return "pending: instale graphifyy com seu servidor MCP e execute este installer novamente"
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
            return f"pending: o registro de {label} falhou: {result.stderr.strip()}"
        return f"configured: {label}"
