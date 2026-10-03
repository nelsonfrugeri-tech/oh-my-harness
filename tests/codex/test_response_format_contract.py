from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_START = "<!-- output-response:start -->"
_END = "<!-- output-response:end -->"


class ResponseFormatContractTest(unittest.TestCase):
    def test_global_adapters_embed_the_canonical_contract(self) -> None:
        canonical = self._read("core/policies/response-format-contract.md").strip()

        self.assertEqual(canonical, self._embedded_contract("harness/codex/AGENTS.md"))
        self.assertEqual(canonical, self._embedded_contract("harness/claude/CLAUDE.md"))

    def test_contract_defines_language_depth_visuals_and_references(self) -> None:
        contract = self._read("core/policies/response-format-contract.md")
        flat = " ".join(contract.split())

        self.assertIn("consulte o agent `knowledge-base`", flat)
        self.assertIn("Responda em português do Brasil", flat)
        self.assertIn("ABNT NBR ISO 24495-1", flat)
        self.assertIn("ASD-STE100", flat)
        self.assertIn("progressive disclosure", flat)
        self.assertIn("até 800 caracteres", flat)
        self.assertIn("até 1.600 caracteres", flat)
        self.assertIn("até 4.000 caracteres", flat)
        self.assertIn("não conte código, tabelas, gráficos", flat)
        self.assertIn("Use uma visualização quando ela reduzir materialmente", flat)
        self.assertIn("Quando uma tool ou um output schema exigir formato específico", flat)
        self.assertIn("encerre com `### Referências`", flat)

    def _embedded_contract(self, relative: str) -> str:
        content = self._read(relative)
        pattern = re.escape(_START) + r"\n(.*?)\n" + re.escape(_END)
        matches = re.findall(pattern, content, flags=re.DOTALL)
        self.assertEqual(1, len(matches), relative)
        return matches[0].strip()

    def _read(self, relative: str) -> str:
        return _ROOT.joinpath(relative).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
