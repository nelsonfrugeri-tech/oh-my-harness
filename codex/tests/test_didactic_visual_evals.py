from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast


_ROOT = Path(__file__).resolve().parents[2]
_EXPECTED_IDS = frozenset(
    {
        "architecture-flow",
        "decorative-visual",
        "plugin-only",
        "quantitative-comparison",
        "unsupported-metric",
        "simple-fact",
    }
)


class DidacticVisualEvalContractTest(unittest.TestCase):
    def test_corpus_has_unique_complete_cases(self) -> None:
        cases = self._cases()
        identifiers = tuple(case["id"] for case in cases)

        self.assertEqual(_EXPECTED_IDS, set(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(set(case) == {"id", "prompt", "required"} for case in cases))
        self.assertTrue(all(isinstance(case["prompt"], str) and case["prompt"] for case in cases))
        self.assertTrue(all(self._valid_requirements(case["required"]) for case in cases))

    def test_protocol_requires_isolated_behavioral_evaluation(self) -> None:
        protocol = _ROOT.joinpath("evals/didactic-visual/README.md").read_text(
            encoding="utf-8"
        )

        for required in ("fresh session", "plugin-only", "pass", "required", "evaluator"):
            self.assertIn(required, protocol)

    def _cases(self) -> list[dict[str, object]]:
        path = _ROOT / "evals/didactic-visual/cases.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, list)
        return cast(list[dict[str, object]], value)

    def _valid_requirements(self, value: object) -> bool:
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, str) and bool(item) for item in value
        )


if __name__ == "__main__":
    unittest.main()
