from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


class DatabricksDashboardContractTest(unittest.TestCase):
    def test_dashboard_assets_when_ported_then_are_installable(self) -> None:
        skill = _ROOT / "skills/tools/databricks-dashboard/SKILL.md"
        agent = _ROOT / "agents/tools/databricks-dashboard.md"
        adapter = _ROOT / "codex/agents/databricks-dashboard.toml"

        self.assertTrue(skill.is_file())
        self.assertTrue(agent.is_file())
        self.assertTrue(adapter.is_file())
        self.assertIn("databricks-sql", skill.read_text(encoding="utf-8"))
        self.assertIn(
            'name = "databricks-dashboard"', adapter.read_text(encoding="utf-8")
        )

    def test_dashboard_scripts_when_ported_then_preserve_lifecycle_tools(self) -> None:
        scripts = _ROOT / "skills/tools/databricks-dashboard/scripts"
        expected = {
            "create_dashboard.py",
            "export_dashboard.py",
            "publish_dashboard.py",
            "validate_dashboard.py",
        }

        self.assertEqual(
            {path.name for path in scripts.glob("*.py")} & expected, expected
        )

    def test_dashboard_assets_use_universal_filesystem_primitives(self) -> None:
        assets = (
            "skills/tools/databricks-dashboard/SKILL.md",
            "skills/tools/databricks-dashboard/references/harness-adapters.md",
            "agents/tools/databricks-dashboard.md",
            "codex/agents/databricks-dashboard.toml",
        )

        for asset in assets:
            with self.subTest(asset=asset):
                content = _ROOT.joinpath(asset).read_text(encoding="utf-8")
                self.assertNotIn("`filesystem`", content)


class KbSessionContractTest(unittest.TestCase):
    def test_codex_rollout_discovery_when_session_memory_is_unavailable_then_has_fallback(
        self,
    ) -> None:
        content = _ROOT.joinpath("skills/tools/kb-session/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("### codex (on this machine)", content)
        self.assertIn("$CODEX_HOME/sessions", content)
        self.assertIn("session_meta", content)
        self.assertIn("payload.cwd", content)
        self.assertIn("payload.id", content)

    def test_codex_adapter_when_documenting_transcripts_then_matches_session_skill(
        self,
    ) -> None:
        content = _ROOT.joinpath("codex/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("$CODEX_HOME/sessions/YYYY/MM/DD/rollout-", content)
        self.assertIn("transcript_path", content)


if __name__ == "__main__":
    unittest.main()
