from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.integration_transport import McpState, graphify_server
from lib.integrations import CodexIntegrations


class CodexIntegrationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self._codex_home = Path(self._temporary.name) / "codex-home"
        self._integrations = CodexIntegrations(self._codex_home)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    @patch("lib.integrations.shutil.which", return_value=None)
    def test_install_reports_missing_codex(self, _which: object) -> None:
        self.assertEqual(
            self._integrations.install(),
            ("pending: Codex CLI is not available",),
        )

    @patch.object(CodexIntegrations, "_check_x_api", return_value="xapi")
    @patch.object(
        CodexIntegrations,
        "_install_remote",
        side_effect=("excalidraw", "x-docs"),
    )
    @patch.object(CodexIntegrations, "_install_graphify", return_value="graphify")
    @patch.object(CodexIntegrations, "_install_deja", return_value="deja")
    @patch("lib.integrations.shutil.which", return_value="/usr/bin/codex")
    def test_install_runs_every_supported_integration(
        self,
        _which: object,
        _deja: object,
        _graphify: object,
        _remote: object,
        _x_api: object,
    ) -> None:
        self.assertEqual(
            self._integrations.install(),
            ("deja", "graphify", "excalidraw", "x-docs", "xapi"),
        )

    @patch("lib.integrations.subprocess.run")
    @patch.object(CodexIntegrations, "_mcp_state", return_value=McpState.MISSING)
    def test_excalidraw_uses_the_official_remote_server(
        self,
        _state: Mock,
        run: Mock,
    ) -> None:
        run.return_value = Mock(returncode=0, stderr="")

        result = self._integrations._install_remote(
            "excalidraw", "Excalidraw MCP", "https://mcp.excalidraw.com"
        )

        self.assertEqual("configured: Excalidraw MCP", result)
        self.assertEqual(
            [
                "codex",
                "mcp",
                "add",
                "excalidraw",
                "--url",
                "https://mcp.excalidraw.com",
            ],
            run.call_args.args[0],
        )

    @patch("lib.integrations.subprocess.run")
    @patch.object(CodexIntegrations, "_mcp_state", return_value=McpState.DRIFTED)
    def test_excalidraw_transport_drift_is_never_overwritten(
        self,
        _state: Mock,
        run: Mock,
    ) -> None:
        result = self._integrations._install_remote(
            "excalidraw", "Excalidraw MCP", "https://mcp.excalidraw.com"
        )

        self.assertIn("different transport", result)
        run.assert_not_called()

    @patch("lib.integrations.subprocess.run")
    @patch.object(CodexIntegrations, "_mcp_state", return_value=McpState.MISSING)
    @patch("lib.integrations.shutil.which")
    def test_deja_install_registers_mcp_without_indexing_transcripts(
        self,
        which: Mock,
        _state: Mock,
        run: Mock,
    ) -> None:
        which.return_value = "/opt/homebrew/bin/deja"
        run.return_value = Mock(returncode=0, stderr="")

        result = self._integrations._install_deja()

        self.assertIn("transcript indexing disabled", result)
        self.assertEqual(
            run.call_args,
            call(
                [
                    "codex",
                    "mcp",
                    "add",
                    "deja",
                    "--",
                    "/opt/homebrew/bin/deja",
                    "mcp",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env=run.call_args.kwargs["env"],
            ),
        )

    @patch("lib.integrations.subprocess.run")
    @patch.object(CodexIntegrations, "_mcp_state", return_value=McpState.MISSING)
    @patch.object(
        CodexIntegrations,
        "_graphify_server",
        return_value=Path("/opt/homebrew/bin/graphify-mcp"),
    )
    def test_graphify_uses_current_mcp_executable_without_project_cwd(
        self,
        _server: Mock,
        _state: Mock,
        run: Mock,
    ) -> None:
        run.return_value = Mock(returncode=0, stderr="")

        result = self._integrations._install_graphify()

        self.assertEqual("configured: Graphify MCP", result)
        self.assertNotIn("GRAPHIFY_PROJECT_DIR", str(run.call_args_list))
        self.assertIn("/opt/homebrew/bin/graphify-mcp", str(run.call_args_list))

    @patch("lib.integration_transport.shutil.which")
    def test_graphify_discovery_rejects_non_executable_files(self, which: Mock) -> None:
        candidate = Path(self._temporary.name) / "graphify-mcp"
        candidate.write_text("not executable", encoding="utf-8")
        candidate.chmod(0o600)
        which.side_effect = (
            lambda name: str(candidate) if name == "graphify-mcp" else None
        )

        with patch.object(Path, "home", return_value=Path(self._temporary.name)):
            self.assertIsNone(graphify_server())

    @patch("lib.integration_transport.subprocess.run")
    def test_every_codex_subprocess_receives_selected_home(self, run: Mock) -> None:
        run.return_value = Mock(returncode=0)

        self._integrations._mcp_exists("deja")

        self.assertEqual(
            str(self._codex_home), run.call_args.kwargs["env"]["CODEX_HOME"]
        )

    @patch("lib.integrations.subprocess.run")
    @patch.object(CodexIntegrations, "_mcp_state", return_value=McpState.DRIFTED)
    @patch("lib.integrations.shutil.which", return_value="/usr/local/bin/deja")
    def test_deja_transport_drift_is_never_overwritten(
        self,
        _which: Mock,
        _state: Mock,
        run: Mock,
    ) -> None:
        result = self._integrations._install_deja()

        self.assertIn("different transport", result)
        run.assert_not_called()

    @patch("lib.integration_transport.subprocess.run")
    def test_mcp_transport_is_validated_from_codex_json(self, run: Mock) -> None:
        run.return_value = Mock(
            returncode=0,
            stdout=(
                '{"transport":{"type":"stdio","command":"/bin/tool",'
                '"args":["serve"],"cwd":null}}'
            ),
        )

        matches = self._integrations._mcp_state(
            "tool",
            {"type": "stdio", "command": "/bin/tool", "args": ["serve"]},
        )
        drifted = self._integrations._mcp_state(
            "tool",
            {"type": "stdio", "command": "/bin/other", "args": ["serve"]},
        )

        self.assertIs(McpState.MATCHES, matches)
        self.assertIs(McpState.DRIFTED, drifted)


if __name__ == "__main__":
    unittest.main()
