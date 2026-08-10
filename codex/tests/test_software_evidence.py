from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_START = "<!-- software-evidence:start -->"
_END = "<!-- software-evidence:end -->"


class SoftwareEvidenceContractTest(unittest.TestCase):
    def test_global_adapters_embed_the_canonical_contract(self) -> None:
        canonical = self._canonical_contract()

        self.assertEqual(canonical, self._embedded_contract("codex/AGENTS.md"))
        self.assertEqual(canonical, self._embedded_contract("claude-code/CLAUDE.md"))

    def test_contract_defines_claim_classes_and_quantitative_provenance(self) -> None:
        contract = self._canonical_contract()
        claim_classes = (
            "Verified fact",
            "Derived result",
            "Inference",
            "Hypothesis",
            "Estimate",
            "Unknown",
            "Decision",
        )

        self.assertTrue(all(name in contract for name in claim_classes))
        self.assertIn("unit, population, time window, source, and method", contract)
        self.assertIn("calibration data", contract)
        self.assertIn("software engineering work", contract)

    def test_evidence_skill_contains_only_referenced_resources(self) -> None:
        skill = _ROOT / "skills/engineers/evidence/SKILL.md"
        content = skill.read_text(encoding="utf-8")
        references = tuple((_ROOT / "skills/engineers/evidence/references").glob("*.md"))
        decision = self._read("skills/engineers/evidence/references/decision-protocol.md")

        self.assertIn("name: evidence", content)
        self.assertGreaterEqual(len(references), 3)
        self.assertTrue(all(f"references/{path.name}" in content for path in references))
        self.assertIn("Every verified fact, derived result, and inference", decision)
        self.assertNotIn("or states why no source exists", decision)

    def test_evidence_reviewer_is_read_only_and_has_codex_parity(self) -> None:
        shared = _ROOT.joinpath("agents/engineers/evidence-reviewer.md").read_text(
            encoding="utf-8"
        )
        codex = _ROOT.joinpath("codex/agents/evidence-reviewer.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn("name: evidence-reviewer", shared)
        self.assertIn('name = "evidence-reviewer"', codex)
        self.assertIn("read-only", shared.lower())
        self.assertIn("read-only", codex.lower())
        self.assertIn("fals", shared.lower())
        self.assertIn("fals", codex.lower())

    def test_core_software_workflows_invoke_the_evidence_contract(self) -> None:
        paths = (
            "skills/engineers/feature/SKILL.md",
            "skills/engineers/implement/references/workflow-bug-fix.md",
            "skills/engineers/manage/SKILL.md",
            "skills/engineers/research/SKILL.md",
            "skills/engineers/review/SKILL.md",
            "skills/engineers/design/SKILL.md",
            "claude-code/workflows/create-feature.ts",
        )

        for relative in paths:
            with self.subTest(path=relative):
                content = _ROOT.joinpath(relative).read_text(encoding="utf-8").lower()
                self.assertIn("evidence", content)
                self.assertIn("hypoth", content)
        research = _ROOT.joinpath("skills/engineers/research/SKILL.md").read_text()
        manage = _ROOT.joinpath("skills/engineers/manage/SKILL.md").read_text()
        self.assertNotIn("Minimum 3 sources", research)
        self.assertNotIn("Apresentar como fato", research)
        self.assertNotIn("~30%", manage)
        self.assertNotIn("Buffer: 20%", manage)
        feature = self._read("skills/engineers/feature/SKILL.md")
        adapter = self._read("claude-code/workflows/create-feature.ts")
        self.assertIn("evidence-reviewer", feature)
        self.assertIn("block-pending-evidence", feature)
        self.assertIn("unknowns:", feature)
        self.assertIn("refinementUnknowns", adapter)

    def _canonical_contract(self) -> str:
        path = _ROOT / "policies/software-evidence-contract.md"
        return path.read_text(encoding="utf-8").strip()

    def _embedded_contract(self, relative: str) -> str:
        content = self._read(relative)
        pattern = re.escape(_START) + r"\n(.*?)\n" + re.escape(_END)
        matches = re.findall(pattern, content, flags=re.DOTALL)
        self.assertEqual(1, len(matches), relative)
        return matches[0].strip()

    def _read(self, relative: str) -> str:
        return _ROOT.joinpath(relative).read_text(encoding="utf-8")
