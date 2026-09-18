from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast


_ROOT = Path(__file__).resolve().parents[2]
_EXPECTED_IDS = frozenset(
    {
        "greenfield-closed-categories",
        "greenfield-llm-app",
        "extensible-tools",
        "repository-convention-wins",
        "settled-decision",
        "silent-legacy-bugfix",
    }
)


class ImplementCorpusTest(unittest.TestCase):
    def test_corpus_has_unique_complete_cases(self) -> None:
        cases = self._cases()
        identifiers = tuple(case["id"] for case in cases)

        self.assertEqual(len(_EXPECTED_IDS), len(cases))
        self.assertEqual(_EXPECTED_IDS, set(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(set(case) == {"id", "prompt", "required"} for case in cases))
        self.assertTrue(all(isinstance(case["prompt"], str) and case["prompt"] for case in cases))
        self.assertTrue(all(self._valid_requirements(case["required"]) for case in cases))

    def test_protocol_is_reproducible_and_scoped(self) -> None:
        protocol = _ROOT.joinpath("core/evals/implement/README.md").read_text(
            encoding="utf-8"
        )

        for required in ("fresh session", "fixture", "harness", "model", "commit", "pass", "required"):
            self.assertIn(required, protocol)

    def test_reference_yields_to_repository_conventions(self) -> None:
        reference = " ".join(
            _ROOT.joinpath("core/skills/implement/references/way-of-building.md")
            .read_text(encoding="utf-8")
            .split()
        )
        craft = _ROOT.joinpath("core/skills/implement/references/code-craft.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("When the repository defines a convention for that concern, follow", reference)
        self.assertIn("[way-of-building.md](way-of-building.md)", craft)

    def _cases(self) -> list[dict[str, object]]:
        path = _ROOT / "core/evals/implement/cases.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, list)
        return cast(list[dict[str, object]], value)

    def _valid_requirements(self, value: object) -> bool:
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, str) and bool(item) for item in value
        )


if __name__ == "__main__":
    unittest.main()
