from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast


_ROOT = Path(__file__).resolve().parents[2]
_EXPECTED_IDS = {
    "discoverer": frozenset(
        {
            "no-product-code",
            "kr-scenario-mapping",
            "reuse-search",
            "fast-lane-redirect",
            "tool-agents-by-function",
            "approved-plan-persisted",
            "mandatory-requirements",
            "architecture-in-the-plan",
        }
    ),
    "developer": frozenset(
        {
            "e2e-evidence-before-done",
            "pr-conformance-matrix",
            "silent-deviation",
            "blocked-external-dependency",
            "fast-lane-guard",
            "walking-skeleton-first",
            "small-work-direct",
            "kb-holds-only-plan",
            "answer-review-proof-first",
            "answer-review-disagreement",
            "teardown-after-merge",
            "review-against-plan",
            "defect-local-fix",
            "defect-falsifies-plan",
            "real-tests-every-line",
            "architecture-checks-first-slice",
            "split-tool-module-by-responsibility",
            "existing-gates-respected",
            "oversized-file-re-evaluation",
            "form-follows-state",
            "comments-only-when-needed",
        }
    ),
    "reviewer": frozenset(
        {
            "text-only-triage",
            "proof-in-own-worktree",
            "inline-comment-with-evidence",
            "trivial-comment-no-test",
            "local-worktree-review",
            "fast-lane-no-plan",
            "ready-after-no-blocker",
            "blocker-stays-draft",
            "meta-review-noise",
            "one-point-at-a-time",
            "calibration-run",
            "matrix-is-not-verdict",
            "out-of-plan-proposal",
            "standards-blocker-outside-plan",
            "finding-falsifies-plan",
            "major-falsifies-plan-stays-draft",
            "structural-static-proof",
            "rereview-reruns-proof",
            "teardown-after-merge",
            "public-method-cap-major",
            "domain-purity-major",
            "mixed-assets-minor",
            "stateless-class-minor",
        }
    ),
}


class ModeCorporaTest(unittest.TestCase):
    def test_each_mode_has_a_corpus_of_unique_complete_cases(self) -> None:
        for mode, expected in _EXPECTED_IDS.items():
            cases = self._cases(mode)
            identifiers = tuple(case["id"] for case in cases)
            with self.subTest(mode=mode):
                self.assertEqual(expected, set(identifiers))
                self.assertEqual(len(identifiers), len(set(identifiers)))
                self.assertTrue(all(set(case) == {"id", "prompt", "required"} for case in cases))
                self.assertTrue(
                    all(isinstance(case["prompt"], str) and case["prompt"] for case in cases)
                )
                self.assertTrue(all(self._valid_requirements(case["required"]) for case in cases))

    def test_each_protocol_is_reproducible_and_starts_the_mode(self) -> None:
        for mode in _EXPECTED_IDS:
            protocol = _ROOT.joinpath("core/evals", mode, "README.md").read_text(
                encoding="utf-8"
            )
            for required in (
                "fresh session", "fixture", "harness", "model", "commit", "pass", "required",
                f"claude --agent oh-my-harness:{mode}",
            ):
                with self.subTest(mode=mode, required=required):
                    self.assertIn(required, protocol)

    def _cases(self, mode: str) -> list[dict[str, object]]:
        path = _ROOT / "core/evals" / mode / "cases.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, list)
        return cast(list[dict[str, object]], value)

    def _valid_requirements(self, value: object) -> bool:
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, str) and bool(item) for item in value
        )


if __name__ == "__main__":
    unittest.main()
