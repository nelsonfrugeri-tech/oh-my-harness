from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.plugin_integrations import PluginIntegrations


class PluginIntegrationsTest(unittest.TestCase):
    def setUp(self) -> None:
        source = Path(__file__).resolve().parents[2]
        self._integrations = PluginIntegrations(source)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_adds_official_marketplaces_and_plugins(self, run: Mock) -> None:
        run.side_effect = tuple(
            Mock(returncode=0, stdout=output, stderr="")
            for output in (
                '{"marketplaces": []}', "", self._langchain_marketplace_json(),
                '{"installed": []}', "", "", '{"marketplaces": []}', "",
                self._evals_marketplace_json(), '{"installed": []}', "",
            )
        )

        result = self._integrations.install()

        self.assertEqual(self._configured_results(), result)
        self._assert_install_commands(run)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_does_not_change_a_reconciled_state(self, run: Mock) -> None:
        marketplaces = self._marketplaces_json()
        installed = self._installed_json()
        run.side_effect = tuple(
            Mock(returncode=0, stdout=output, stderr="")
            for output in (marketplaces, installed, marketplaces, installed)
        )

        result = self._integrations.install()

        self.assertEqual(self._ok_results(), result)
        self.assertEqual(4, run.call_count)

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_rejects_a_marketplace_with_the_wrong_source(self, run: Mock) -> None:
        run.return_value = Mock(
            returncode=0,
            stdout=(
                '{"marketplaces": [{"name": "ai-evals-course",'
                '"marketplaceSource": {"source": "https://example.invalid/evals.git"}}]}'
            ),
            stderr="",
        )

        result = self._install_catalog("ai-evals-course")

        self.assertEqual(
            "pending: a origem do marketplace AI Evals diverge: https://example.invalid/evals.git",
            result,
        )

    @patch("lib.plugin_integrations.subprocess.run")
    def test_install_revalidates_the_source_after_marketplace_registration(self, run: Mock) -> None:
        run.side_effect = (
            Mock(returncode=0, stdout='{"marketplaces": []}', stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(
                returncode=0,
                stdout=(
                    '{"marketplaces": [{"name": "ai-evals-course",'
                    '"marketplaceSource": {"source": "https://example.invalid/evals.git"}}]}'
                ),
                stderr="",
            ),
        )

        result = self._install_catalog("ai-evals-course")

        self.assertEqual(
            "pending: a origem do marketplace AI Evals diverge: https://example.invalid/evals.git",
            result,
        )
        self.assertEqual(3, run.call_count)

    def _assert_install_commands(self, run: Mock) -> None:
        expected = (
            self._command("plugin", "marketplace", "add", "langchain-ai/langchain-plugins"),
            self._command("plugin", "add", "langchain-skills@langchain-plugins"),
            self._command("plugin", "add", "langchain-mcp@langchain-plugins"),
            self._command("plugin", "marketplace", "add", "ai-evals-course/evals-skills"),
            self._command("plugin", "add", "evals@ai-evals-course"),
        )
        self.assertTrue(all(command in run.call_args_list for command in expected))

    def _install_catalog(self, name: str) -> str:
        catalog = next(
            item for item in self._integrations._catalogs() if item.marketplace_name == name
        )
        return self._integrations._install_catalog(catalog)

    def _command(self, *arguments: str) -> call:
        return call(
            ["codex", *arguments], check=False, capture_output=True, text=True, timeout=60
        )

    def _configured_results(self) -> tuple[str, ...]:
        return (
            "configured: skills LangChain e documentação viva",
            "configured: skills oficiais de avaliação de AI",
        )

    def _ok_results(self) -> tuple[str, ...]:
        return (
            "ok: skills LangChain e documentação viva",
            "ok: skills oficiais de avaliação de AI",
        )

    def _marketplaces_json(self) -> str:
        return (
            '{"marketplaces": ['
            '{"name": "langchain-plugins", "marketplaceSource": {'
            '"source": "https://github.com/langchain-ai/langchain-plugins.git"}},'
            '{"name": "ai-evals-course", "marketplaceSource": {'
            '"source": "https://github.com/ai-evals-course/evals-skills.git"}}]}'
        )

    def _langchain_marketplace_json(self) -> str:
        return (
            '{"marketplaces": [{"name": "langchain-plugins", "marketplaceSource": {'
            '"source": "https://github.com/langchain-ai/langchain-plugins.git"}}]}'
        )

    def _evals_marketplace_json(self) -> str:
        return (
            '{"marketplaces": [{"name": "ai-evals-course", "marketplaceSource": {'
            '"source": "https://github.com/ai-evals-course/evals-skills.git"}}]}'
        )

    def _installed_json(self) -> str:
        return (
            '{"installed": ['
            '{"pluginId": "langchain-skills@langchain-plugins", "enabled": true},'
            '{"pluginId": "langchain-mcp@langchain-plugins", "enabled": true},'
            '{"pluginId": "evals@ai-evals-course", "enabled": true}]}'
        )


if __name__ == "__main__":
    unittest.main()
