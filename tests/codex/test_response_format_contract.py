from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_START = "<!-- response-format:start -->"
_END = "<!-- response-format:end -->"


class ResponseFormatContractTest(unittest.TestCase):
    def test_global_adapters_embed_the_canonical_contract(self) -> None:
        canonical = self._read("core/policies/response-format-contract.md").strip()

        self.assertEqual(canonical, self._embedded_contract("harness/codex/AGENTS.md"))
        self.assertEqual(canonical, self._embedded_contract("harness/claude/CLAUDE.md"))

    def test_essence_is_identity_and_points_to_the_skill(self) -> None:
        flat = self._flat()

        self.assertIn("**É assim que você responde** — não é regra opcional, é quem você é.", flat)
        self.assertIn("toda resposta, em qualquer formato, segue um contrato só", flat.lower())
        self.assertIn("A skill `output-response` traz o detalhe", flat)
        self.assertIn("nunca invente evidência", flat)
        self.assertIn("uma vez por sessão", flat)
        self.assertNotIn("`evidence`", flat)
        self.assertNotIn("didactic-visual", flat)

    def test_essence_states_core_first_labels_and_writing_standards(self) -> None:
        flat = self._flat()

        for phrase in (
            "A primeira frase responde ou conclui, resumida e didática",
            "progressive disclosure",
            "sem receber uma conclusão enganosa",
            "nunca conteúdo material",
            "Frases de transição e instruções ficam sem rótulo",
            "ABNT NBR ISO 24495-1",
            "ASD-STE100",
            "frase procedural com até 20 palavras, descritiva com até 25",
            "uma instrução por frase, voz ativa e um termo por conceito",
            "Termos técnicos, jargões e nomes próprios ficam em inglês inline",
            "três ou mais elementos",
            "O tamanho sozinho não justifica",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)

    def test_essence_states_budget_and_exemptions(self) -> None:
        flat = self._flat()

        self.assertIn("Pergunta direta: até 800 caracteres contados", flat)
        self.assertIn("Explicação ou decisão: até 1600", flat)
        self.assertIn("tabelas, diagramas e código não contam", flat)
        self.assertIn("Code review, diagnóstico e plano estão isentos", flat)

    def test_question_rule_is_hard_and_bounded(self) -> None:
        flat = self._flat()

        for phrase in (
            "**REGRA DURA.** Pergunte somente diante de ambiguidade genuína",
            "alinhamento, divergência ou decisão — e sempre com uma recomendação",
            "Nunca pergunte o que a web, o repositório ou um comando respondem",
            "pesquise, no mínimo, todo termo ou entidade que o usuário mencionar",
            "decida, declare e siga",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)

    def test_specific_output_contract_overrides_only_presentation_shape(self) -> None:
        flat = self._flat()

        self.assertIn("prevalece somente sobre a forma", flat)
        self.assertIn("Não suspende rótulos, provenance, incerteza, idioma nem segurança", flat)

    def _flat(self) -> str:
        return " ".join(self._read("core/policies/response-format-contract.md").split())

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
