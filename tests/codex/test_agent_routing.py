from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST = json.loads(
    _ROOT.joinpath("core/agents/routing.json").read_text(encoding="utf-8")
)
_PLUGINS_FILE = _ROOT / "harness/codex/integrations/plugins.json"
_RUNBOOK_FILE = _ROOT / "harness/claude/skills/claude-code/SKILL.md"
_SELF_DISTRIBUTION = "oh-my-harness@oh-my-harness"


class AgentRoutingContractTest(unittest.TestCase):
    def test_catalog_has_complete_portable_roles(self) -> None:
        roles = _MANIFEST["roles"]
        families = _MANIFEST["role_families"]
        codex = _MANIFEST["adapter_specs"]["codex-toml"]["overlays"]

        self.assertEqual(8, len(roles))
        self.assertEqual(set(roles), set(families))
        self.assertEqual(set(roles), set(codex))

    def test_evals_dependency_requires_the_renamed_entry(self) -> None:
        dependency = _MANIFEST["catalog_contract"]["dependencies"]["evals"]

        self.assertEqual("0.3.1", dependency["minimum_version"])
        self.assertEqual(["evals:evals-start"], dependency["entries"])
        for role_id in ("ai-engineer",):
            route = next(
                route
                for route in _MANIFEST["roles"][role_id]["routes"]
                if route["id"] == "ai-evals"
            )
            with self.subTest(role=role_id):
                self.assertEqual("evals:evals-start", route["entry"])
                self.assertIn("claude plugin update evals@ai-evals-course", route["degraded_behavior"])

    def test_every_contracted_dependency_is_addressable(self) -> None:
        dependencies = _MANIFEST["catalog_contract"]["dependencies"]

        self.assertTrue(dependencies)
        for name, dependency in dependencies.items():
            with self.subTest(dependency=name):
                self.assertEqual(
                    name, dependency["distribution"].split("@", 1)[0]
                )
                self.assertRegex(dependency["distribution"], r"^[^@]+@[^@]+$")
                self.assertRegex(dependency["minimum_version"], r"^\d+\.\d+\.\d+$")
                self.assertIsInstance(dependency["installed_by_default"], bool)
                self.assertTrue(dependency["entries"])
                for entry in dependency["entries"]:
                    self.assertTrue(entry.strip())

    def test_entry_names_match_the_declared_provider_surface(self) -> None:
        # A contract that only agrees with itself cannot catch the defect this contract
        # exists to prevent: `evals:start` vs `evals:evals-start` was consistent in every
        # place it appeared and still pointed at a skill that does not exist. Each entry
        # is therefore checked against the provider surface declared beside it.
        for name, dependency in _MANIFEST["catalog_contract"]["dependencies"].items():
            with self.subTest(dependency=name):
                entries = set(dependency["entries"])
                kind = dependency["entry_kind"]
                if kind == "skill":
                    for entry in entries:
                        self.assertTrue(
                            entry.startswith(f"{name}:"),
                            f"{entry} is not namespaced by its own plugin",
                        )
                elif kind == "mcp-tool":
                    declared = {
                        tool
                        for server in dependency["servers"].values()
                        for tool in server["tools"]
                    }
                    self.assertEqual(declared, entries)
                elif kind == "mcp-server":
                    self.assertEqual(set(dependency["servers"]), entries)
                else:
                    self.fail(f"unknown entry_kind {kind!r}")

    def test_skill_entries_are_pinned_to_the_verified_upstream_names(self) -> None:
        # A namespace check cannot catch a wrong leaf: `langsmith-dataset` vs
        # `langsmith-datasets` is namespaced correctly and still points at nothing. The
        # leaf lives upstream, so the verified names are pinned here, the same technique
        # `test_evals_dependency_requires_the_renamed_entry` already uses. Each set was
        # read from the published plugin, not inferred.
        verified = {
            "evals": {"evals:evals-start"},
            "langchain-skills": {
                "langchain-skills:ecosystem-primer",
                "langchain-skills:eval-engineering",
                "langchain-skills:langsmith-online-eval-engineering",
            },
            "langsmith-skills": {
                "langsmith-skills:langsmith-trace",
                "langsmith-skills:langsmith-dataset",
                "langsmith-skills:langsmith-evaluator",
            },
        }
        dependencies = _MANIFEST["catalog_contract"]["dependencies"]
        skills = {
            name
            for name, dependency in dependencies.items()
            if dependency["entry_kind"] == "skill"
        }

        self.assertEqual(skills, set(verified))
        for name, entries in verified.items():
            with self.subTest(dependency=name):
                self.assertEqual(entries, set(dependencies[name]["entries"]))

    def test_every_mcp_tool_entry_resolves_to_one_server_prefix(self) -> None:
        # `entry: search_docs_by_lang_chain` is a bare tool name and the plugin exposes two
        # servers, so the agent needs the prefix to call it without guessing.
        for name, dependency in _MANIFEST["catalog_contract"]["dependencies"].items():
            if dependency["entry_kind"] != "mcp-tool":
                continue
            for entry in dependency["entries"]:
                owners = [
                    server["harness_prefix"]
                    for server in dependency["servers"].values()
                    if entry in server["tools"]
                ]
                with self.subTest(dependency=name, entry=entry):
                    self.assertEqual(1, len(owners))

    def test_declared_capabilities_exist_in_both_guidance_tables(self) -> None:
        # `capability` names an abstract provider that the guidance tables bind to a
        # concrete tool. Declaring one that no table binds is the same "declared and not
        # plugged" defect this contract exists to prevent, one level up.
        claude = _ROOT.joinpath("harness/claude/CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("harness/codex/AGENTS.md").read_text(encoding="utf-8")

        for name, dependency in _MANIFEST["catalog_contract"]["dependencies"].items():
            capability = dependency.get("capability")
            if capability is None:
                continue
            with self.subTest(dependency=name, capability=capability):
                self.assertIn(f"`{capability}`", claude)
                self.assertIn(f"`{capability}`", codex)

    def test_every_installed_plugin_is_declared_in_the_contract(self) -> None:
        dependencies = _MANIFEST["catalog_contract"]["dependencies"]
        contracted = {
            dependency["distribution"]
            for dependency in dependencies.values()
            if dependency["installed_by_default"]
        }

        self.assertEqual(contracted, _codex_installed_plugins())
        self.assertEqual(contracted, _claude_installed_plugins())

    def test_plugins_left_out_are_declared_instead_of_omitted(self) -> None:
        dependencies = _MANIFEST["catalog_contract"]["dependencies"]
        excluded = json.loads(_PLUGINS_FILE.read_text(encoding="utf-8"))[
            "declared_not_installed"
        ]

        self.assertTrue(excluded)
        for name, reason in excluded.items():
            with self.subTest(plugin=name):
                self.assertFalse(dependencies[name]["installed_by_default"])
                self.assertTrue(reason.strip())

        # The loop above iterates over the declaration, so removing an entry from it
        # shortens the loop instead of failing. The inverse assertion is what forbids the
        # omission this test is named after.
        uninstalled = {
            name
            for name, dependency in _MANIFEST["catalog_contract"]["dependencies"].items()
            if not dependency["installed_by_default"]
        }
        self.assertEqual(uninstalled, set(excluded))

    def test_evidence_reviewer_executes_without_write_access(self) -> None:
        overlay = _MANIFEST["adapter_specs"]["shared-markdown"]["overlays"]["evidence-reviewer"]

        self.assertEqual("policy", _MANIFEST["role_families"]["evidence-reviewer"])
        self.assertIn("Bash", overlay["tools"])
        self.assertNotIn("Write", overlay["tools"])
        self.assertNotIn("Edit", overlay["tools"])

    def test_codex_evidence_reviewer_enforces_the_read_only_sandbox(self) -> None:
        spec = _MANIFEST["adapter_specs"]["codex-toml"]

        self.assertIn("sandbox_mode", spec["allowed_overlays"])
        self.assertEqual(
            "read-only", spec["overlays"]["evidence-reviewer"]["sandbox_mode"]
        )
        adapter = _ROOT.joinpath(
            "harness/codex/agents/evidence-reviewer.toml"
        ).read_text(encoding="utf-8")
        self.assertIn('sandbox_mode = "read-only"\n', adapter)

        for role_id in _MANIFEST["roles"]:
            if role_id == "evidence-reviewer":
                continue
            with self.subTest(role=role_id):
                other = _ROOT.joinpath(
                    "harness/codex/agents", f"{role_id}.toml"
                ).read_text(encoding="utf-8")
                self.assertNotIn("sandbox_mode", other)

    def test_software_engineer_refuses_an_unresilient_external_call(self) -> None:
        requirements = (
            "an external call without a timeout",
            "an idempotent retry with backoff and jitter",
            "a circuit breaker or explicitly justified failure behavior",
        )
        contract = " ".join(
            _MANIFEST["roles"]["software-engineer"]["operating_contract"]
        )
        rendered = (
            "harness/claude/agents/engineers/software-engineer.md",
            "harness/codex/agents/software-engineer.toml",
        )
        for requirement in requirements:
            with self.subTest(surface="manifest", requirement=requirement):
                self.assertIn(requirement, contract)
            for path in rendered:
                adapter = " ".join(
                    _ROOT.joinpath(path).read_text(encoding="utf-8").split()
                )
                with self.subTest(surface=path, requirement=requirement):
                    self.assertIn(requirement, adapter)

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
                "harness/claude/agents", families[role_id], f"{role_id}.md"
            )
            codex_path = _ROOT.joinpath("harness/codex", "agents", f"{role_id}.toml")
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

    def test_adapters_omit_external_routing_when_routes_are_empty(self) -> None:
        syntax = _MANIFEST["routing_syntax"]
        forbidden = (
            syntax["start_marker"], syntax["end_marker"], syntax["heading"],
            syntax["availability_notice"],
            "| " + " | ".join(syntax["columns"]) + " |",
            "| " + " | ".join("---" for _ in syntax["columns"]) + " |",
        )
        for role_id, role in _MANIFEST["roles"].items():
            for render in (_render_shared, _render_codex):
                with self.subTest(role=role_id, adapter=render.__name__):
                    rendered = render(role_id, {**role, "routes": []})
                    for fragment in forbidden:
                        self.assertNotIn(fragment, rendered)
                    self.assertIn(role["implementation_guidance"], rendered)
                    self.assertIn("## Operating contract", rendered)
                    self.assertIn("## Boundaries", rendered)


def _codex_installed_plugins() -> set[str]:
    catalog = json.loads(_PLUGINS_FILE.read_text(encoding="utf-8"))
    return {
        f"{plugin}@{marketplace['marketplace']['name']}"
        for marketplace in catalog["marketplaces"]
        for plugin in marketplace["plugins"]
    }


def _claude_installed_plugins() -> set[str]:
    runbook = _RUNBOOK_FILE.read_text(encoding="utf-8")
    installed = set(re.findall(r"claude plugin install (\S+@\S+)", runbook))
    return installed - {_SELF_DISTRIBUTION}


def _render_body(role: dict[str, object]) -> str:
    skills = ", ".join(f"`{skill}`" for skill in role["local_skills"])
    sections = (
        f"# {role['title']}",
        role["summary"],
        f"Use the installed local skills {skills} when applicable.",
        role["implementation_guidance"],
        _render_routes(role),
        _bullet_section("## Operating contract", role["operating_contract"]),
        _bullet_section("## Boundaries", role["boundaries"]),
    )
    return "\n\n".join(section for section in sections if section) + "\n"


def _render_routes(role: dict[str, object]) -> str:
    if not role["routes"]:
        return ""
    syntax = _MANIFEST["routing_syntax"]
    header = "| " + " | ".join(syntax["columns"]) + " |"
    divider = "| " + " | ".join("---" for _ in syntax["columns"]) + " |"
    rows = "\n".join(_route_row(route) for route in role["routes"])
    return "\n".join(
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
    overlay = _MANIFEST["adapter_specs"]["codex-toml"]["overlays"][role_id]
    name = json.dumps(role_id, ensure_ascii=False)
    description = json.dumps(role["description"], ensure_ascii=False)
    body = _render_body(role).rstrip()
    sandbox = (
        f"sandbox_mode = {json.dumps(overlay['sandbox_mode'], ensure_ascii=False)}\n"
        if "sandbox_mode" in overlay
        else ""
    )
    return (
        f"name = {name}\n"
        f"description = {description}\n"
        f"{sandbox}"
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
