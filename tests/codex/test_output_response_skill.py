from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SKILL_DIR = _ROOT / "core/skills/output-response"
_LABELS = (
    "🟢 **FATO VERIFICADO**",
    "🔵 **RESULTADO DERIVADO**",
    "🟠 **INFERÊNCIA**",
    "🟡 **HIPÓTESE**",
    "🟣 **ESTIMATIVA**",
    "🔴 **DESCONHECIDO**",
    "⚪ **DECISÃO**",
)


def _flat(relative: str) -> str:
    return " ".join(_SKILL_DIR.joinpath(relative).read_text(encoding="utf-8").split())


class OutputResponseSkillTest(unittest.TestCase):
    def test_replaces_the_evidence_and_didactic_visual_skills(self) -> None:
        self.assertTrue(_SKILL_DIR.joinpath("SKILL.md").is_file())
        self.assertIn("name: output-response", _flat("SKILL.md"))

    def test_every_reference_is_linked_from_the_skill(self) -> None:
        skill = _flat("SKILL.md")
        references = sorted(_SKILL_DIR.joinpath("references").glob("*.md"))

        self.assertEqual(
            [
                "claim-taxonomy.md", "decision-protocol.md", "representation.md",
                "review-rubric.md", "writing-standards.md",
            ],
            [path.name for path in references],
        )
        for path in references:
            with self.subTest(reference=path.name):
                self.assertIn(f"references/{path.name}", skill)

    def test_skill_carries_the_literal_labels_for_plugin_only_installs(self) -> None:
        skill = _SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8")

        for label in _LABELS:
            with self.subTest(label=label):
                self.assertIn(label, skill)

    def test_every_assertion_is_labelled_and_transitions_are_not(self) -> None:
        skill = _flat("SKILL.md").lower()

        self.assertIn("every assertion", skill)
        self.assertIn("transitional sentences and instructions carry no label", skill)
        self.assertNotIn("ceremonial labels", skill)
        self.assertNotIn("label only certainty boundaries", skill)

    def test_labels_and_writing_standards_are_complementary(self) -> None:
        skill = _flat("SKILL.md").lower()

        self.assertIn("labels and writing standards are complementary", skill)
        self.assertIn("epistemic status", skill)

    def test_ambiguous_entity_is_searched_before_asking(self) -> None:
        skill = _flat("SKILL.md").lower()

        self.assertIn("search the web or the repository first", skill)

    def test_question_rule_and_budget_are_stated(self) -> None:
        skill = _flat("SKILL.md").lower()

        for phrase in (
            "ambiguity, alignment, divergence, or a decision",
            "decide, state the choice, and proceed",
            "800",
            "1600",
            "code review, diagnosis, and plan",
            "core answer first",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

    def test_writing_standards_paraphrase_and_cite_both_sources(self) -> None:
        standards = _flat("references/writing-standards.md").lower()

        for phrase in (
            "abnt nbr iso 24495-1:2024",
            "relevance", "findability", "understandability", "usability",
            "asd-ste100", "issue 9",
            "20 words", "25 words",
            "one instruction per sentence",
            "active voice",
            "one term per concept",
            "the english controlled dictionary does not transfer",
            "technical terms, jargon, and proper names stay in english",
            "a diagnosis investigates a concrete failure",
            "fenced blocks", "table rows",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, standards)

    def test_representation_keeps_the_visual_guard(self) -> None:
        representation = _flat("references/representation.md").lower()

        for phrase in (
            "apply the visual guard",
            "use prose when",
            "request for a large diagram does not override this guard",
            "prefer terminal-native ascii",
            "every visual element maps to established content",
            "for quantitative content, render only values whose provenance already satisfies "
            "the evidence contract, including unit, population or denominator, observation "
            "window, source, and method; preserve scale and proportionality and never infer "
            "causality from visual proximity.",
            "explainability",
            "table", "flow", "timeline", "tree", "wireframe",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, representation)

    def test_plugin_only_install_is_not_blocked_by_a_missing_global_prompt(self) -> None:
        skill = _flat("SKILL.md").lower()

        self.assertIn(
            "in a plugin-only installation, the absence of a global prompt is not a blocker",
            skill,
        )

    def test_decision_protocol_requires_inspectable_evidence(self) -> None:
        decision = _flat("references/decision-protocol.md")

        self.assertIn("Every verified fact, derived result, and inference must point", decision)
        self.assertIn("to inspectable evidence", decision)
        self.assertNotIn("or states why no source exists", decision)

    def test_codex_interface_invokes_the_new_skill(self) -> None:
        interface = _SKILL_DIR.joinpath("agents/openai.yaml").read_text(encoding="utf-8")

        self.assertIn("$output-response", interface)


if __name__ == "__main__":
    unittest.main()
