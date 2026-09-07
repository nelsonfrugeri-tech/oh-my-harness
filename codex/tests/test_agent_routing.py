from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST = json.loads(
    _ROOT.joinpath("agents/routing.json").read_text(encoding="utf-8")
)


class AgentRoutingContractTest(unittest.TestCase):
    def test_catalog_has_complete_portable_roles(self) -> None:
        roles = _MANIFEST["roles"]
        families = _MANIFEST["role_families"]
        codex = _MANIFEST["adapter_specs"]["codex-toml"]["overlays"]

        self.assertEqual(11, len(roles))
        self.assertEqual(set(roles), set(families))
        self.assertEqual(set(roles), set(codex))

    def test_evals_dependency_requires_the_renamed_entry(self) -> None:
        dependency = _MANIFEST["catalog_contract"]["dependencies"]["evals"]

        self.assertEqual("0.3.1", dependency["minimum_version"])
        self.assertEqual(["evals:evals-start"], dependency["entries"])
        for role_id in ("ai-engineer", "qa"):
            route = next(
                route
                for route in _MANIFEST["roles"][role_id]["routes"]
                if route["id"] == "ai-evals"
            )
            with self.subTest(role=role_id):
                self.assertEqual("evals:evals-start", route["entry"])
                self.assertIn("claude plugin update evals@ai-evals-course", route["degraded_behavior"])

    def test_local_skill_order_preserves_evidence_and_presentation(self) -> None:
        for role_id, role in _MANIFEST["roles"].items():
            with self.subTest(role=role_id):
                self.assertEqual("evidence", role["local_skills"][0])
                self.assertEqual("didactic-visual", role["local_skills"][-1])

    def test_optional_dependencies_have_safe_routes(self) -> None:
        dependencies = _MANIFEST["catalog_contract"]["dependencies"]
        self.assertTrue(all(item["optional"] for item in dependencies.values()))

        for role_id, role in _MANIFEST["roles"].items():
            priorities = [route["priority"] for route in role["routes"]]
            self.assertEqual(len(priorities), len(set(priorities)))
            for route in role["routes"]:
                with self.subTest(role=role_id, route=route["id"]):
                    dependency = dependencies[route["dependency"]]
                    self.assertIn(route["entry"], dependency["entries"])
                    self.assertTrue(route["match"]["any_of"])
                    self.assertTrue(route["degraded_behavior"].strip())

    def test_registered_fixtures_cover_and_execute_routing(self) -> None:
        fixtures = _MANIFEST["fixtures"]
        categories = {fixture["category"] for fixture in fixtures}
        required = {
            "repo-signal", "explicit", "implicit", "near-miss",
            "overlap", "abstention", "missing-plugin",
        }
        self.assertTrue(required <= categories)

        declared = {
            (role_id, route["id"], route["entry"])
            for role_id, role in _MANIFEST["roles"].items()
            for route in role["routes"]
        }
        covered = {
            (fixture["role"], fixture["expected_route"], fixture["expected_entry"])
            for fixture in fixtures
            if fixture["expected_kind"] == "entry"
        }
        self.assertEqual(declared, covered)

        for fixture in fixtures:
            with self.subTest(fixture=fixture["id"]):
                self.assertEqual(_expected(fixture), _route(fixture))

    def test_adapters_equal_canonical_rendering(self) -> None:
        families = _MANIFEST["role_families"]
        for role_id, role in _MANIFEST["roles"].items():
            shared_path = _ROOT.joinpath(
                "agents", families[role_id], f"{role_id}.md"
            )
            codex_path = _ROOT.joinpath("codex", "agents", f"{role_id}.toml")
            with self.subTest(role=role_id):
                self.assertEqual(
                    _render_shared(role_id, role),
                    shared_path.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    _render_codex(role_id, role),
                    codex_path.read_text(encoding="utf-8"),
                )

    def test_knowledge_base_role_routes_named_entities_and_addresses(self) -> None:
        description = _MANIFEST["roles"]["knowledge-base"]["description"].lower()

        for signal in (
            "named-entity",
            "address lookup",
            "opening a known project",
            "locating a repository or path",
            "returning a repository url",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, description)

    def test_runtime_claims_remain_bounded(self) -> None:
        runtime = _MANIFEST["runtime_validation"]

        self.assertEqual("required", runtime["standard_gate"]["status"])
        self.assertEqual(
            "supplemental", runtime["installed_catalog_probe"]["status"]
        )
        self.assertEqual(
            "diagnostic-only", runtime["main_agent_probe"]["status"]
        )
        self.assertEqual(
            "unsupported", runtime["native_activation_observation"]["status"]
        )
        custom = runtime["custom_agent_invocation"]
        self.assertEqual("unverified", custom["status"])
        self.assertEqual("unsatisfied", custom["release_gate"])


def _render_body(role: dict[str, object]) -> str:
    syntax = _MANIFEST["routing_syntax"]
    header = "| " + " | ".join(syntax["columns"]) + " |"
    divider = "| " + " | ".join("---" for _ in syntax["columns"]) + " |"
    rows = "\n".join(_route_row(route) for route in role["routes"])
    route_block = "\n".join(
        (
            syntax["start_marker"],
            syntax["heading"],
            "",
            syntax["availability_notice"],
            "",
            header,
            divider,
            rows,
            syntax["end_marker"],
        )
    )
    skills = ", ".join(f"`{skill}`" for skill in role["local_skills"])
    sections = (
        f"# {role['title']}",
        role["summary"],
        f"Use the installed local skills {skills} when applicable.",
        role["implementation_guidance"],
        route_block,
        _bullet_section("## Operating contract", role["operating_contract"]),
        _bullet_section("## Boundaries", role["boundaries"]),
    )
    return "\n\n".join(sections) + "\n"


def _route_row(route: dict[str, object]) -> str:
    positive = ", ".join(route["match"]["any_of"])
    excluded = ", ".join(route["match"]["none_of"]) or "none"
    cells = (
        f"`{route['id']}`",
        positive,
        excluded,
        f"`{route['entry']}`",
        route["sequence"],
        route["degraded_behavior"],
    )
    return "| " + " | ".join(cells) + " |"


def _bullet_section(heading: str, values: list[str]) -> str:
    return heading + "\n\n" + "\n".join(f"- {value}" for value in values)


def _render_shared(role_id: str, role: dict[str, object]) -> str:
    overlay = _MANIFEST["adapter_specs"]["shared-markdown"]["overlays"][role_id]
    skills = "\n".join(f"  - {skill}" for skill in role["local_skills"])
    frontmatter = "\n".join(
        (
            "---",
            f"version: {overlay['version']}",
            f"name: {role_id}",
            "description: >",
            f"  {role['description']}",
            f"model: {overlay['model']}",
            "tools: " + ", ".join(overlay["tools"]),
            "skills:",
            skills,
            "---",
        )
    )
    return frontmatter + "\n\n" + _render_body(role)


def _render_codex(role_id: str, role: dict[str, object]) -> str:
    name = json.dumps(role_id, ensure_ascii=False)
    description = json.dumps(role["description"], ensure_ascii=False)
    body = _render_body(role).rstrip()
    return (
        f"name = {name}\n"
        f"description = {description}\n"
        'developer_instructions = """\n'
        f"{body}\n"
        '"""\n'
    )


def _route(fixture: dict[str, object]) -> tuple[object, ...]:
    role = _MANIFEST["roles"][fixture["role"]]
    signals = " ".join(fixture["repository_signals"])
    prompt = " ".join(f"{fixture['prompt']} {signals}".casefold().split())
    available = set(fixture["available_dependencies"])
    routes = sorted(role["routes"], key=lambda item: item["priority"], reverse=True)
    for route in routes:
        policy = route["match"]
        positive = any(_contains(prompt, phrase) for phrase in policy["any_of"])
        excluded = any(_contains(prompt, phrase) for phrase in policy["none_of"])
        if not positive or excluded:
            continue
        if route["dependency"] in available:
            return "entry", route["id"], route["entry"], None
        return "degraded", route["id"], None, route["degraded_behavior"]
    return "none", None, None, None


def _expected(fixture: dict[str, object]) -> tuple[object, ...]:
    return (
        fixture["expected_kind"],
        fixture["expected_route"],
        fixture["expected_entry"],
        fixture["expected_message"],
    )


def _contains(prompt: str, phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(phrase.casefold())}(?!\w)"
    return re.search(pattern, prompt) is not None


if __name__ == "__main__":
    unittest.main()
