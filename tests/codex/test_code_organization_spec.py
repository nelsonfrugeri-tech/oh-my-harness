from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SPEC = "core/skills/implement/references/way-of-building.md"
_ANCHOR = "way-of-building.md#organize-code-by-domain"


def _read(relative: str) -> str:
    return _ROOT.joinpath(relative).read_text(encoding="utf-8")


def _flat(relative: str) -> str:
    return " ".join(_read(relative).split())


class CodeOrganizationSpecTest(unittest.TestCase):
    def test_spec_lives_in_one_dedicated_section_of_way_of_building(self) -> None:
        spec = _read(_SPEC)
        self.assertEqual(1, spec.count("## Organize code by domain"))

        section = _flat(_SPEC).split("## Organize code by domain", 1)[1].split("## Add structure")[0]
        for required in (
            "declared layers with a one-way dependency direction",
            "The domain imports no framework, no I/O, and no model client",
            "Name and scope each bounded context",
            "never in the entry point or an adapter",
            "**One file type per directory.**",
            "`ai/agent/prompts/prompt.md`",
            "a `Protocol` owned by the consumer",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)

    def test_form_follows_state_through_one_decision_table(self) -> None:
        section = _flat(_SPEC).split("## Organize code by domain", 1)[1].split("## Add structure")[0]
        for row in (
            "| Domain data: entity, value object, result type |",
            "| Business rule |",
            "| State with identity or a lifecycle",
            "| Adapter to an external system |",
            "| Orchestration facade |",
        ):
            with self.subTest(row=row):
                self.assertIn(row, section)
        for required in (
            "Frozen model or dataclass",
            "Class implementing a declared `Protocol`",
            "exempt from the public-method cap",
            "A stateless class with public methods is a function in disguise.",
            "`domain/planning.py`",
            "`domain/proposal.py`",
            "`ai/agent/gate.py`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)

    def test_size_rules_use_only_the_measured_numbers(self) -> None:
        section = _flat(_SPEC).split("## Organize code by domain", 1)[1].split("## Add structure")[0]
        for required in (
            "about 100 lines per file",
            "up to about 130",
            "136-line `domain/planning.py`",
            "Over 150 lines: a mandatory deep re-evaluation, not a block",
            "A function over 50 lines is a hard limit",
            "at most three public methods",
            "splits by family into a package",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)

        self.assertIn(
            "size is a signal to inspect, and responsibility is the reason to split",
            section,
        )
        self.assertIn("never become a failing gate", section)
        self.assertIn(
            "Do not split by a universal line or symbol count",
            _read("core/skills/implement/references/code-craft.md"),
        )
        self.assertEqual(
            (),
            tuple(
                number
                for number in re.findall(r"\b\d{2,3}\b", section)
                if number not in {"100", "112", "126", "130", "136", "150", "302", "293", "50"}
            ),
        )

    def test_spec_covers_eval_harness_and_experiment_code(self) -> None:
        section = _flat(_SPEC).split("## Organize code by domain", 1)[1].split("## Add structure")[0]

        self.assertIn("including eval, harness, and experiment code", section)

    def test_component_assets_live_in_their_own_subdirectory(self) -> None:
        spec = _flat(_SPEC)

        self.assertNotIn("A prompt is a Markdown file next to the module", spec)
        self.assertIn("loaded once as a module constant by one small helper", spec)
        self.assertIn("own asset subdirectory, such as `ai/agent/prompts/prompt.md`", spec)

    def test_comments_are_rare_and_docstrings_are_for_published_interfaces(self) -> None:
        spec = _flat(_SPEC)
        craft = _flat("core/skills/implement/references/code-craft.md")

        self.assertNotIn("Docstrings on public entry points and ports state the contract", spec)
        self.assertIn("Do not fill code with comments", spec)
        self.assertIn("only for genuinely complex code", spec)
        self.assertIn("in one line", spec)
        self.assertIn(
            "Docstrings only on the public API of a library or a published interface", spec
        )
        self.assertIn("never on a private function", spec)
        self.assertIn("Remove narration that merely repeats the code", craft)

    def test_first_slice_installs_the_two_enforced_caps(self) -> None:
        spec = _flat(_SPEC)

        self.assertIn("architecture test that parses imports", spec)
        self.assertIn("function-length cap", spec)
        self.assertIn("public-method cap", spec)

    def test_each_mode_references_the_one_spec_with_its_own_verb(self) -> None:
        verbs = {
            "core/skills/discoverer/SKILL.md": "Design the code organization",
            "core/skills/developer/SKILL.md": "install the mechanical checks",
            "core/skills/reviewer/SKILL.md": "Police the code organization",
        }
        for relative, verb in verbs.items():
            content = _flat(relative)
            with self.subTest(path=relative):
                self.assertIn(verb, content)
                self.assertIn(_ANCHOR, content)

    def test_modes_do_not_restate_the_spec_rules(self) -> None:
        for relative in (
            "core/skills/discoverer/SKILL.md",
            "core/skills/developer/SKILL.md",
            "core/skills/discoverer/references/plan.md",
        ):
            content = _flat(relative)
            with self.subTest(path=relative):
                self.assertNotIn("A stateless class with public methods", content)
                self.assertNotIn("about 100 lines", content)

    def test_plan_requires_the_architecture_design(self) -> None:
        plan = _read("core/skills/discoverer/references/plan.md")
        flat = _flat("core/skills/discoverer/references/plan.md")

        self.assertIn("## Architecture", plan)
        for field in (
            "- Bounded contexts:",
            "- Layers:",
            "- Directory tree:",
            "- Business rules:",
        ):
            with self.subTest(field=field):
                self.assertIn(field, plan)
        self.assertIn("one file type per directory", flat)
        self.assertIn("asset subdirectory", flat)
        self.assertIn("relates to", flat)
        self.assertIn("a plan without them is not ready", flat)

    def test_developer_installs_the_checks_and_writes_the_re_evaluation(self) -> None:
        developer = _flat("core/skills/developer/SKILL.md")
        pull_request = _flat("core/skills/developer/references/pull-request.md")

        self.assertIn("In the first slice, install the mechanical checks", developer)
        self.assertIn("the repository's own entry point", developer)
        self.assertIn("architecture import test", developer)
        self.assertIn("`Protocol` exemption", developer)
        self.assertIn("Every later slice obeys the spec", developer)
        self.assertIn("**Files over 150 lines:**", pull_request)
        self.assertIn("single responsibility", pull_request)

    def test_reviewer_carries_one_severity_per_rule(self) -> None:
        reviewer = _flat("core/skills/reviewer/SKILL.md")
        major = (
            "| Layer violation, or a domain that imports a framework, I/O, or a model client | MAJOR |",
            "| Business rule outside the domain | MAJOR |",
            "| Mixed file types in one directory | MAJOR |",
            "| Stateless class with public methods | MAJOR |",
            "| Function over 50 lines | MAJOR |",
            "| Class with more than three public methods, unless it implements a declared `Protocol` | MAJOR |",
        )
        minor = (
            "| Missing re-evaluation of a file over 150 lines | MINOR |",
            "| Module that should split by family into a package | MINOR |",
            "| Unnecessary comment or docstring | MINOR |",
        )
        for row in (*major, *minor):
            with self.subTest(row=row):
                self.assertIn(row, reviewer)
        self.assertIn("Anchor each finding at `file:line` with the measured number", reviewer)
        self.assertIn("file size alone is never a finding", reviewer)


if __name__ == "__main__":
    unittest.main()
