from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.integrations import CodexIntegrations


class CodexIntegrationsTest(unittest.TestCase):
    @patch("lib.integrations.shutil.which", return_value=None)
    def test_install_reports_missing_codex(self, _which: object) -> None:
        self.assertEqual(
            CodexIntegrations().install(),
            ("pending: Codex CLI is not available",),
        )

    @patch.object(CodexIntegrations, "_install_graphify", return_value="graphify")
    @patch.object(CodexIntegrations, "_install_langchain", return_value="langchain")
    @patch.object(CodexIntegrations, "_install_deja", return_value="deja")
    @patch("lib.integrations.shutil.which", return_value="/usr/bin/codex")
    def test_install_runs_every_supported_integration(
        self,
        _which: object,
        _deja: object,
        _langchain: object,
        _graphify: object,
    ) -> None:
        self.assertEqual(
            CodexIntegrations().install(),
            ("deja", "graphify", "langchain"),
        )

    @patch("lib.integrations.subprocess.run")
    @patch("lib.integrations.shutil.which")
    def test_deja_install_configures_subagent_indexing(
        self,
        which: Mock,
        run: Mock,
    ) -> None:
        which.return_value = "/opt/homebrew/bin/deja"
        run.return_value = Mock(returncode=0, stderr="")

        result = CodexIntegrations()._install_deja()

        self.assertIn("with subagent indexing", result)
        self.assertEqual(
            run.call_args_list[1],
            call(
                [
                    "codex",
                    "mcp",
                    "add",
                    "--env",
                    "DEJA_INCLUDE_SUBAGENTS=1",
                    "deja",
                    "--",
                    "/opt/homebrew/bin/deja",
                    "mcp",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            ),
        )


if __name__ == "__main__":
    unittest.main()
