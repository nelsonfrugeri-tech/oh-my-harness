from __future__ import annotations

import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SKILL = _ROOT / "skills/didactic-visual/SKILL.md"


class DidacticVisualSkillTest(unittest.TestCase):
    def test_skill_uses_the_shared_native_plugin_contract(self) -> None:
        self.assertTrue(_SKILL.is_file())

    def test_skill_declares_discovery_and_visualization_contract(self) -> None:
        content = _SKILL.read_text(encoding="utf-8")
        normalized = " ".join(content.split()).lower()

        self.assertIn("name: didactic-visual", content)
        self.assertIn("prerequisite: evidence first", normalized)
        self.assertIn("load `oh-my-harness:evidence`", normalized)
        self.assertIn("presentation only", normalized)
        self.assertIn("progressive disclosure", normalized)
        self.assertIn("explainability", normalized)
        self.assertIn("apply the visual guard", normalized)
        self.assertIn("use prose when", normalized)
        self.assertIn("request for a large diagram does not override this guard", normalized)
        self.assertIn("prefer terminal-native ascii", normalized)
        for representation in ("table", "flow", "timeline", "tree", "wireframe"):
            with self.subTest(representation=representation):
                self.assertIn(representation, normalized)
        self.assertIn("quantitative content", normalized)
        self.assertIn("preserve scale and proportionality", normalized)
        self.assertIn("every visual element maps to established content", normalized)


if __name__ == "__main__":
    unittest.main()
