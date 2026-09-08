from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from lib.plugin_integrations import PluginIntegrations


class CodexIntegrations:
    def install(self) -> tuple[str, ...]:
        if shutil.which("codex") is None:
            return ("pending: CLI do Codex não está disponível",)
        return (
            self._install_deja(),
            *self._install_plugins(),
        )

    def _install_plugins(self) -> tuple[str, ...]:
        source_root = Path(__file__).resolve().parents[3]
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
