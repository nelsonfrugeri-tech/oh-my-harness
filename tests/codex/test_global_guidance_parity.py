from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SHARED_START = b"<!-- shared-guidance:start -->"
_SHARED_END = b"<!-- shared-guidance:end -->"

_CLAUDE_PREAMBLE = """# CLAUDE.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do harness e a todo subagent.

<!-- Mantenha este arquivo curto e focado nas regras que precisam valer em toda sessão. Detalhes
     operacionais pertencem às skills e carregam sob demanda. -->

---"""

_CODEX_PREAMBLE = """# AGENTS.md

Regras vinculantes deste ambiente. Aplicam-se a toda sessão do Codex e a todo subagent.

<!-- Mantenha este arquivo curto e focado nas regras que precisam valer em toda sessão. Detalhes
     operacionais pertencem às skills e carregam sob demanda. -->

---"""

_SHARED_HEADINGS = (
    "## Como penso, decido e respondo",
    "### Rotule o que afirma",
    "### Nunca finja certeza",
    "### Saiba o que cada evidência prova",
    "### Decida com fatos e evidências",
    "## Como executo, delego e supervisiono",
    "## Como respondo, explico e apresento",
    "### Antes de responder",
    "### Linguagem e estrutura",
    "### Profundidade",
    "### Apresentação visual",
)


def _normalize(text: str) -> str:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized_newlines.split("\n")).strip("\n")


def _extract_unique(text: bytes, start: bytes, end: bytes) -> tuple[bytes, bytes, bytes]:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one marker pair: {start}, {end}")
    before, remainder = text.split(start, 1)
    content, after = remainder.split(end, 1)
    if end in before or start in after:
        raise ValueError(f"misordered marker pair: {start}, {end}")
    return before, content, after


def _headings(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"(?m)^#{2,6} .+$", text))


class GlobalGuidanceParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self._claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_bytes()
        self._codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_bytes()

    def test_shared_guidance_is_identical(self) -> None:
        claude_shared = self._document(self._claude, _CLAUDE_PREAMBLE)
        codex_shared = self._document(self._codex, _CODEX_PREAMBLE)

        self._assert_shared_equal(claude_shared, codex_shared)

    def test_global_guidance_contains_only_the_three_behavioral_sections(self) -> None:
        for name, document, preamble in (
            ("claude", self._claude, _CLAUDE_PREAMBLE),
            ("codex", self._codex, _CODEX_PREAMBLE),
        ):
            with self.subTest(harness=name):
                shared = self._document(document, preamble).decode("utf-8")
                self.assertEqual(_SHARED_HEADINGS, _headings(shared))
                self.assertNotIn("## Ambiente", shared)
                self.assertNotIn("## Fluxo de PR", shared)
                self.assertNotIn("## Delta do", shared)

    def test_word_mutation_in_shared_guidance_is_detected(self) -> None:
        claude_shared = self._document(self._claude, _CLAUDE_PREAMBLE)
        codex_shared = self._document(self._codex, _CODEX_PREAMBLE)
        mutated = codex_shared.replace(
            "Raciocine a partir de evidências verificáveis.".encode("utf-8"),
            "Raciocine a partir de evidências disponíveis.".encode("utf-8"),
            1,
        )

        self.assertNotEqual(codex_shared, mutated)
        with self.assertRaises(AssertionError):
            self._assert_shared_equal(claude_shared, mutated)

    def _document(self, text: bytes, expected_preamble: str) -> bytes:
        preamble, shared, suffix = _extract_unique(text, _SHARED_START, _SHARED_END)
        self.assertEqual(_normalize(expected_preamble), _normalize(preamble.decode("utf-8")))
        self.assertEqual("", _normalize(suffix.decode("utf-8")))
        return shared.strip()

    def _assert_shared_equal(self, expected: bytes, actual: bytes) -> None:
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
