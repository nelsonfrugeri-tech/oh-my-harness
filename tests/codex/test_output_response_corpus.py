from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import cast

_ROOT = Path(__file__).resolve().parents[2]
_EVAL = _ROOT / "core/evals/output-response"
_KINDS = frozenset({"direct", "explanation", "decision", "code_review", "diagnosis", "plan"})

# The 18 cases migrated from the evidence (12) and didactic-visual (6) corpora keep their
# prompt and required items verbatim; only the removed skill names inside prompts became
# `output-response`. Each digest is the first 16 hex characters of
# sha256(json.dumps([prompt, required], ensure_ascii=False)), computed from the master
# files of the two old corpora with that rename applied.
_MIGRATED = {
    "unsupported-number": "3695da7fb9027a42",
    "repository-count": "07fe4810630163d1",
    "correlation-root-cause": "3ddf278ee427513f",
    "hotfix-without-telemetry": "9b789d31963a2f2e",
    "hotfix-with-evidence": "e72b6a18176a7c7d",
    "stale-session-memory": "fe4dd289c1025159",
    "nominal-mcp-health": "1909cf8930dbdbbc",
    "conflicting-primary-sources": "bac5fddd9585bfbf",
    "critique-without-alternative": "b507a7885b69705e",
    "uncalibrated-confidence": "026463e21b177ea7",
    "passing-tests-overclaim": "bc1b9896e37b5d72",
    "metric-without-window": "c7eb71e6696ec315",
    "architecture-flow": "e8c0c2501b54460b",
    "decorative-visual": "5d940360450553e9",
    "plugin-only": "2f39a74e9971aa2a",
    "quantitative-comparison": "3aa62739a3aba311",
    "unsupported-metric": "6e605afe55b58c5b",
    "simple-fact": "4d06135bc2101cfb",
}
_NEW = {
    "label-direct-fact": "direct",
    "label-mixed-status": "explanation",
    "label-transition-instruction": "explanation",
    "label-plugin-only": "direct",
    "budget-direct": "direct",
    "budget-explanation": "explanation",
    "budget-decision": "decision",
    "budget-exempt-plan": "plan",
    "budget-exempt-code-review": "code_review",
    "question-unknown-term": "direct",
    "question-default-choice": "direct",
    "question-genuine-ambiguity": "direct",
    "sentence-length": "explanation",
}


def _digest(case: dict[str, object]) -> str:
    payload = json.dumps([case["prompt"], case["required"]], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class OutputResponseCorpusTest(unittest.TestCase):
    def test_corpus_has_unique_complete_cases(self) -> None:
        cases = self._cases()
        identifiers = [case["id"] for case in cases]

        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(set(_MIGRATED) | set(_NEW), set(identifiers))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual({"id", "kind", "prompt", "required"}, set(case))
                self.assertIn(case["kind"], _KINDS)
                self.assertTrue(isinstance(case["prompt"], str) and case["prompt"])
                self.assertTrue(self._valid_requirements(case["required"]))

    def test_migrated_cases_keep_prompt_and_required_verbatim(self) -> None:
        by_id = {case["id"]: case for case in self._cases()}

        for identifier, digest in _MIGRATED.items():
            with self.subTest(case=identifier):
                self.assertEqual(digest, _digest(by_id[identifier]))

    def test_new_cases_declare_the_planned_kind(self) -> None:
        by_id = {case["id"]: case for case in self._cases()}

        for identifier, kind in _NEW.items():
            with self.subTest(case=identifier):
                self.assertEqual(kind, by_id[identifier]["kind"])

    def test_every_exempt_kind_and_budgeted_kind_is_covered(self) -> None:
        self.assertEqual(_KINDS, {case["kind"] for case in self._cases()})

    def test_scenario_prompts_are_pinned(self) -> None:
        by_id = {case["id"]: case for case in self._cases()}

        self.assertEqual("Qual a diferença entre TCP e UDP?", by_id["budget-direct"]["prompt"])
        self.assertEqual("o que é jev?", by_id["question-unknown-term"]["prompt"])
        self.assertIn("núcleo na primeira frase", by_id["budget-explanation"]["required"])

    def test_protocol_is_reproducible_and_scoped(self) -> None:
        protocol = _EVAL.joinpath("README.md").read_text(encoding="utf-8")

        for required in (
            "fresh session", "harness", "model", "commit", "pass", "required",
            "plugin-only", "evaluator", "count_budget.py", "kind", "exempt",
        ):
            with self.subTest(required=required):
                self.assertIn(required, protocol)

    def test_old_corpora_are_removed(self) -> None:
        for name in ("evidence", "didactic-visual"):
            with self.subTest(corpus=name):
                self.assertFalse(_ROOT.joinpath("core/evals", name).exists())

    def _cases(self) -> list[dict[str, object]]:
        value = json.loads(_EVAL.joinpath("cases.json").read_text(encoding="utf-8"))
        self.assertIsInstance(value, list)
        return cast(list[dict[str, object]], value)

    def _valid_requirements(self, value: object) -> bool:
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, str) and bool(item) for item in value
        )


if __name__ == "__main__":
    unittest.main()
