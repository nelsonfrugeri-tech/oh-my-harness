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

        self.assertIn("name: didactic-visual", content)
        self.assertIn("Use ao explicar", content)
        self.assertIn("progressive disclosure", content.lower())
        self.assertIn("explainability", content.lower())
        self.assertIn("mecanismo", content.lower())
        self.assertIn(
            "problema → componentes → método → evidência → resultados → limitações → próximos passos",
            content.lower(),
        )
        self.assertIn("nomes oficiais", content.lower())
        self.assertIn("conceitos de dados", content.lower())
        self.assertIn("Prerequisite: evidence first", content)
        self.assertIn("`oh-my-harness:evidence`", content)
        self.assertIn("evidence contract ativo no harness", content)
        self.assertIn("additional constraints", content)
        self.assertIn("ausência não é um blocker", content)
        self.assertNotIn("If either dependency is unavailable", content)
        self.assertIn("pelo menos um visual útil", content)
        self.assertIn("Um pedido explícito não elimina", content)
        self.assertIn("responda sem visual", content)
        self.assertIn("terminal-native chart", content)
        self.assertIn("unidade, população ou denominador", content)
        self.assertIn("ASCII", content)
        self.assertIn("table", content.lower())
        self.assertIn("idioma do usuário", content)
        self.assertIn("Não use", content)


if __name__ == "__main__":
    unittest.main()
