from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.plugin_integrations import PluginIntegrations


class PluginIntegrationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._source = Path(__file__).resolve().parents[2]
        self._integrations = PluginIntegrations(self._source)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_adds_marketplace_and_required_plugins(self, run: Mock) -> None:
        run.side_effect = (
            Mock(returncode=0, stdout='{"marketplaces": []}', stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout='{"installed": []}', stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
        )

        result = self._integrations.install()

        self.assertEqual("configured: LangChain skills and live documentation", result)
        self.assertEqual(
            [
                call(
                    ["codex", "plugin", "marketplace", "list", "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
                call(
                    [
                        "codex",
                        "plugin",
                        "marketplace",
                        "add",
                        "langchain-ai/langchain-plugins",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
                call(
                    ["codex", "plugin", "list", "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
                call(
                    ["codex", "plugin", "add", "langchain-skills@langchain-plugins"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
                call(
                    ["codex", "plugin", "add", "langchain-mcp@langchain-plugins"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
            ],
            run.call_args_list,
        )

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_does_not_change_an_already_reconciled_state(self, run: Mock) -> None:
        run.side_effect = (
            Mock(
                returncode=0,
                stdout=(
                    '{"marketplaces": [{"name": "langchain-plugins",'
                    '"marketplaceSource": {'
                    '"source": "https://github.com/langchain-ai/langchain-plugins.git"}}]}'
                ),
                stderr="",
            ),
            Mock(
                returncode=0,
                stdout=(
                    '{"installed": ['
                    '{"pluginId": "langchain-skills@langchain-plugins", "enabled": true},'
                    '{"pluginId": "langchain-mcp@langchain-plugins", "enabled": true}'
                    ']}'
                ),
                stderr="",
            ),
        )

        result = self._integrations.install()

        self.assertEqual("ok: LangChain skills and live documentation", result)
        self.assertEqual(2, run.call_count)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_rejects_a_marketplace_with_the_official_name_and_wrong_source(
        self, run: Mock
    ) -> None:
        run.return_value = Mock(
            returncode=0,
            stdout=(
                '{"marketplaces": [{"name": "langchain-plugins",'
                '"marketplaceSource": {"source": "https://example.invalid/plugins.git"}}]}'
            ),
            stderr="",
        )

        result = self._integrations.install()

        self.assertEqual(
            "pending: LangChain marketplace source mismatch: https://example.invalid/plugins.git",
            result,
        )
        self.assertEqual(1, run.call_count)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_reports_a_marketplace_error_without_adding_plugins(self, run: Mock) -> None:
        run.side_effect = (
            Mock(returncode=0, stdout='{"marketplaces": []}', stderr=""),
            Mock(returncode=1, stdout="", stderr="network unavailable"),
        )

        result = self._integrations.install()

        self.assertEqual(
            "pending: LangChain marketplace registration failed: network unavailable",
            result,
        )
        self.assertEqual(2, run.call_count)


if __name__ == "__main__":
    unittest.main()
