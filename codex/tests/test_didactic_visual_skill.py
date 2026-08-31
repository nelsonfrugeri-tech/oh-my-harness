from __future__ import annotations

import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SKILL = _ROOT / "codex/skills/didactic-visual/SKILL.md"


class DidacticVisualSkillTest(unittest.TestCase):
    def test_skill_is_codex_plugin_native(self) -> None:
        self.assertTrue(_SKILL.is_file())
        self.assertFalse((_ROOT / "skills/didactic-visual").exists())

    def test_skill_declares_discovery_and_visualization_contract(self) -> None:
        content = _SKILL.read_text(encoding="utf-8")

        self.assertIn("name: didactic-visual", content)
        self.assertIn("Use when", content)
        self.assertIn("progressive disclosure", content.lower())
        self.assertIn("explainability", content.lower())
        self.assertIn("mechanism", content.lower())
        self.assertIn(
            "problem → components → method → evidence → results → limitations → next steps",
            content.lower(),
        )
        self.assertIn("official names", content.lower())
        self.assertIn("data concepts", content.lower())
        self.assertIn("Hard prerequisite", content)
        self.assertIn("`oh-my-harness:evidence`", content)
        self.assertIn("active `AGENTS.md` evidence contract", content)
        self.assertIn("Stop and report the missing prerequisite", content)
        self.assertIn("at least one useful visual", content)
        self.assertIn("terminal-native chart", content)
        self.assertIn("unit, time window, source", content)
        self.assertIn("ASCII", content)
        self.assertIn("table", content.lower())
        self.assertIn("user's language", content)
        self.assertIn("Do not use", content)


if __name__ == "__main__":
    unittest.main()
