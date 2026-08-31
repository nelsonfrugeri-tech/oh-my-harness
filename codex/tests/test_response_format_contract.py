from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_START = "<!-- response-format:start -->"
_END = "<!-- response-format:end -->"


class ResponseFormatContractTest(unittest.TestCase):
    def test_global_adapters_embed_the_canonical_contract(self) -> None:
        canonical = self._read("policies/response-format-contract.md").strip()

        self.assertEqual(canonical, self._embedded_contract("codex/AGENTS.md"))
        self.assertEqual(canonical, self._embedded_contract("claude-code/CLAUDE.md"))

    def test_specific_output_contract_overrides_only_presentation_shape(self) -> None:
        contract = self._read("policies/response-format-contract.md")
        flat = " ".join(contract.split())

        self.assertIn("`evidence` é o mindset primário", flat)
        self.assertIn("toda resposta e em qualquer formato", flat)
        self.assertIn("evidence → didactic-visual → formato específico", flat)
        self.assertIn("fallback vinculante", flat)
        self.assertIn("nunca invente evidência", flat)
        self.assertIn("toda resposta final", flat)
        self.assertIn("`didactic-visual`", flat)
        self.assertIn("**REGRA DURA.** É obrigatório", flat)
        self.assertIn("fallback degradado", flat)
        self.assertIn("uma vez por sessão", flat)
        self.assertIn("não obriga a criar um visual", flat)
        self.assertIn("prevalece somente sobre a forma", flat)
        self.assertIn("evidence, provenance, incerteza", flat)
        self.assertIn("conclusão ou resposta direta na primeira frase", flat)
        self.assertIn("parágrafos curtos e coesos", flat)
        self.assertIn("Use bullets somente", flat)
        self.assertIn("progressive disclosure", flat)
        self.assertIn("todas as camadas materialmente necessárias", flat)
        self.assertIn("não depende de widgets colapsáveis", flat)
        self.assertIn("nunca removendo conteúdo material", flat)
        self.assertIn("requisito, mecanismo, evidência decisiva", flat)
        self.assertIn("três ou mais elementos", flat)
        self.assertIn("O tamanho sozinho não justifica", flat)
        self.assertIn("Não repita a conclusão", flat)

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
