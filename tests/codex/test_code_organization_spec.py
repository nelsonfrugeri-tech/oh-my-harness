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


def _section() -> str:
    return _flat(_SPEC).split("## Organize code by domain", 1)[1].split("## Add structure")[0]


class CodeOrganizationSpecTest(unittest.TestCase):
    def test_spec_lives_in_one_dedicated_section_of_way_of_building(self) -> None:
        spec = _read(_SPEC)
        self.assertEqual(1, spec.count("## Organize code by domain"))

        section = _section()
        for required in (
            "declared layers with a one-way dependency direction",
            "The domain imports no framework, no I/O, and no model client",
            "Name and scope each bounded context",
            "never in the entry point or an adapter",
            "`ai/agent/prompts/prompt.md`",
            "a `Protocol` owned by the consumer",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)

    def test_assets_never_share_a_directory_with_the_modules_that_use_them(self) -> None:
        # Narrowed to the measured problem, a prompt beside its module: a directory of
        # sibling data or documentation artifacts, such as an eval corpus with its README,
        # is not a violation. The census in the pull request shows zero findings in this
        # repository under this wording.
        section = _section()

        self.assertIn(
            "Never mix source modules with the assets or documentation they use", section
        )
        self.assertIn("its own asset subdirectory", section)
        self.assertIn("is not a violation", section)
        self.assertNotIn("**One file type per directory.**", section)

    def test_a_module_holds_one_behavior(self) -> None:
        self.assertIn(
            "A module that holds more than one behavior splits by behavior", _section()
        )

    def test_form_follows_state_through_one_decision_table(self) -> None:
        section = _section()
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

    def test_a_vocabulary_module_has_one_verdict_on_splitting(self) -> None:
        section = _section()

        self.assertNotIn("unlimited", section)
        self.assertIn(
            "Many, while the module still reads as one family; when it stops, split by family",
            section,
        )
        # The measured example and the split rule must agree: ten types in 126 lines is the
        # size at which the vocabulary splits, not a size the table blesses.
        proposal = section.split("`domain/proposal.py` holds ten frozen data classes", 1)[1]
        self.assertIn("the size at which the vocabulary splits by family", proposal[:120])

    def test_size_rules_use_only_the_measured_numbers(self) -> None:
        section = _section()
        for required in (
            "about 100 lines per file",
            "up to about 130",
            "136-line `domain/planning.py`",
            "Between about 131 and 150 lines, inspect cohesion",
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
            "the check the developer installs on the first slice of a greenfield project",
            section,
        )
        self.assertIn(
            "Do not split by a universal line or symbol count",
            _read("core/skills/implement/references/code-craft.md"),
        )
        # Every number in the section is a measurement of one of the two reference projects:
        # 100/130/131/150/50 are the calibrated limits, 136/126 the good project's
        # `domain/planning.py` and `domain/proposal.py`, and 302/293/112 the worst eval,
        # harness, and experiment files. A number outside this set is an invented threshold,
        # so the pattern stays `\d+` rather than a fixed width.
        self.assertEqual(
            (),
            tuple(
                number
                for number in re.findall(r"\d+", section)
                if number
                not in {"100", "112", "126", "130", "131", "136", "150", "302", "293", "50"}
            ),
        )

    def test_spec_covers_eval_harness_and_experiment_code(self) -> None:
        self.assertIn("including eval, harness, and experiment code", _section())

    def test_public_method_cap_exempts_a_framework_owned_surface(self) -> None:
        section = _section()

        self.assertIn("a framework owns its public surface", section)
        self.assertIn("`unittest.TestCase`", section)
        self.assertIn("A test module carries the same re-evaluation", section)

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
            "core/skills/reviewer/SKILL.md",
            "core/skills/discoverer/references/plan.md",
        ):
            content = _flat(relative)
            with self.subTest(path=relative):
                self.assertNotIn("A stateless class with public methods is a function", content)
                self.assertNotIn("about 100 lines", content)

    def test_each_threshold_number_has_one_authoritative_home(self) -> None:
        documents = {
            path.relative_to(_ROOT).as_posix(): " ".join(
                path.read_text(encoding="utf-8").split()
            )
            for path in (*_ROOT.glob("core/skills/**/*.md"), _ROOT / "README.md")
        }
        expected = {
            "over 50 lines": {_SPEC},
            "three public methods": {_SPEC},
            # The 150-line trigger also belongs to the two author-side artifacts that must
            # write the re-evaluation. The reviewer reads the cap from the spec instead.
            "150 lines": {
                _SPEC,
                "core/skills/developer/SKILL.md",
                "core/skills/developer/references/pull-request.md",
            },
        }
        for threshold, owners in expected.items():
            with self.subTest(threshold=threshold):
                self.assertEqual(
                    owners,
                    {path for path, text in documents.items() if threshold in text},
                )

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
        self.assertIn("<function, class, or data type>", plan)
        self.assertIn("every directory and file the change creates", flat)
        self.assertIn("asset subdirectory", flat)
        self.assertIn("relates to", flat)
        self.assertIn("a plan without them is not ready", flat)
        # One owner per concern: the tree lives in `Architecture`, and the reuse section
        # keeps only the reuse decisions.
        reuse = flat.split("## Reuse", 1)[1].split("## Architecture")[0]
        self.assertNotIn("layout", reuse)

    def test_discoverer_names_both_plan_sections_it_fills(self) -> None:
        discoverer = _flat("core/skills/discoverer/SKILL.md")

        self.assertIn("`Architecture` and `Domain entities` fields", discoverer)

    def test_developer_installs_the_checks_where_the_repository_has_none(self) -> None:
        developer = _flat("core/skills/developer/SKILL.md")
        pull_request = _flat("core/skills/developer/references/pull-request.md")

        self.assertIn("In the first slice, install the mechanical checks", developer)
        self.assertIn("the repository's own entry point", developer)
        self.assertIn("architecture import test", developer)
        self.assertIn("`Protocol` exemption", developer)
        self.assertIn("Every later slice obeys the spec", developer)
        # Greenfield only, per way-of-building: an existing repository keeps its own gates.
        self.assertIn("in a greenfield repository, or when the approved plan declares", developer)
        self.assertIn("use the gates it already has and record the gap", developer)
        self.assertIn("never on the fast lane", developer)
        self.assertIn("**Files over 150 lines:**", pull_request)
        self.assertIn("single responsibility", pull_request)

    def test_reviewer_severities_hold_only_where_the_spec_was_adopted(self) -> None:
        reviewer = _flat("core/skills/reviewer/SKILL.md")

        self.assertIn(
            "these severities hold when the repository has adopted this specification",
            reviewer,
        )
        self.assertIn("follow the repository's own convention", reviewer)
        self.assertNotIn("not a preference the plan can waive", reviewer)

    def test_reviewer_carries_one_severity_per_rule(self) -> None:
        reviewer = _flat("core/skills/reviewer/SKILL.md")
        major = (
            "| Layer violation, or a domain that imports a framework, I/O, or a model client | MAJOR |",
            "| Business rule outside the domain | MAJOR |",
            "| Stateless class with public methods | MAJOR |",
            "| Function over the length cap | MAJOR |",
            "| Class over the public-method cap, with no exemption | MAJOR |",
        )
        minor = (
            "| Assets or documentation mixed with the modules that use them | MINOR |",
            "| Module that should split by behavior or by family | MINOR |",
            "| Missing re-evaluation of an oversized file | MINOR |",
        )
        for row in (*major, *minor):
            with self.subTest(row=row):
                self.assertIn(row, reviewer)
        self.assertIn("| Unnecessary comment or docstring | NIT |", reviewer)
        self.assertIn("Anchor each finding at `file:line` with the measured number", reviewer)
        self.assertIn("file size alone is never a finding", reviewer)

    def test_readme_points_at_the_specification(self) -> None:
        readme = _flat("README.md")

        self.assertIn(_ANCHOR, readme)
        self.assertIn("function-length and public-method caps", readme)

    def test_eval_protocols_wrap_at_one_hundred_columns(self) -> None:
        for path in sorted((_ROOT / "core/evals").glob("*/README.md")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                with self.subTest(path=path.relative_to(_ROOT), line=number):
                    self.assertLessEqual(len(line), 100)


if __name__ == "__main__":
    unittest.main()
