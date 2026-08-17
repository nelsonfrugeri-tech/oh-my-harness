from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


class AdapterContractTest(unittest.TestCase):
    def test_every_portable_agent_has_a_codex_adapter(self) -> None:
        shared = {self._yaml_name(path) for path in _ROOT.glob("agents/**/*.md")}
        adapters = {
            self._toml_name(path)
            for path in _ROOT.glob("codex/agents/*.toml")
            if path.name != "codex.toml"
        }
        self.assertEqual(shared, adapters)

    def test_legacy_agent_adapters_preserve_their_skills(self) -> None:
        expected = {
            "claude-code": ("claude-code",),
            "sync": ("sync-bundle", "sync-transport"),
        }

        for name, skills in expected.items():
            content = _ROOT.joinpath("codex", "agents", f"{name}.toml").read_text(
                encoding="utf-8"
            )
            for skill in skills:
                self.assertIn(f"`{skill}`", content)

    def test_legacy_skills_are_shipped_in_the_portable_layout(self) -> None:
        expected = (
            "skills/engineers/create-feature/SKILL.md",
            "skills/engineers/langchain/deep-agents-core/SKILL.md",
            "skills/engineers/langchain/deep-agents-memory/SKILL.md",
            "skills/engineers/langchain/deep-agents-orchestration/SKILL.md",
            "skills/style/didactic-visual/SKILL.md",
            "skills/engineers/langchain/ecosystem-primer/SKILL.md",
            "skills/engineers/langchain/langchain-dependencies/SKILL.md",
            "skills/engineers/langchain/langchain-fundamentals/SKILL.md",
            "skills/engineers/langchain/langchain-rag/SKILL.md",
            "skills/engineers/langchain/langgraph-fundamentals/SKILL.md",
            "skills/engineers/langchain/langgraph-human-in-the-loop/SKILL.md",
            "skills/engineers/langchain/langgraph-persistence/SKILL.md",
            "skills/tools/sync-bundle/SKILL.md",
            "skills/tools/sync-transport/SKILL.md",
            "skills/tools/sync-transport/references/syncthing.md",
        )
        missing = [path for path in expected if not _ROOT.joinpath(path).is_file()]
        self.assertEqual(missing, [])

    def test_sync_and_destruction_contracts_use_the_codex_policy(self) -> None:
        sync = _ROOT.joinpath("skills/tools/sync-transport/SKILL.md").read_text(
            encoding="utf-8"
        )
        rules = _ROOT.joinpath("codex/rules/destructive.rules").read_text(
            encoding="utf-8"
        )

        self.assertIn("`AGENTS.md`", sync)
        self.assertNotIn("`CLAUDE.md`", sync)
        self.assertIn('pattern = ["git", "reset", "--hard"]', rules)
        self.assertIn('pattern = ["kubectl", "delete"]', rules)

    def test_skill_leaf_names_are_unique_for_codex(self) -> None:
        sources = (
            *_ROOT.glob("skills/**/SKILL.md"),
            *_ROOT.glob("codex/skills/**/SKILL.md"),
        )
        names = [
            path.parent.name for path in sources if path.parent.name != "claude-code"
        ]
        self.assertEqual(len(names), len(set(names)))

    def test_feature_skill_uses_portable_orchestration(self) -> None:
        content = _ROOT.joinpath("skills/engineers/feature/SKILL.md").read_text(
            encoding="utf-8"
        )
        forbidden = ("Workflow({", "AskUserQuestion", "use the tool `Agent`")
        self.assertFalse(any(token in content for token in forbidden))
        self.assertIn("Portable orchestration contract", content)

    def test_create_feature_assets_use_abstract_capabilities(self) -> None:
        paths = (
            _ROOT / "skills/engineers/create-feature/SKILL.md",
            _ROOT / "skills/engineers/create-feature/references/create-feature.ts",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        forbidden = (
            "~/.claude",
            "~/.codex",
            "mcp__",
            "kb_write",
            "~/knowledge-base",
            "`gh`",
            "`glab`",
        )

        self.assertFalse(any(token in content for token in forbidden))
        self.assertIn("`code-host`", content)
        self.assertIn("`memory`", content)

    def test_ecosystem_primer_uses_the_web_capability(self) -> None:
        content = _ROOT.joinpath(
            "skills/engineers/langchain/ecosystem-primer/SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("mcp__", content)
        self.assertIn("`web` capability", content)

    def test_ecosystem_primer_references_only_shipped_layer_skills(self) -> None:
        content = _ROOT.joinpath(
            "skills/engineers/langchain/ecosystem-primer/SKILL.md"
        ).read_text(encoding="utf-8")
        absent = (
            "langchain-python-quickstart",
            "langchain-typescript-quickstart",
            "langgraph-python-quickstart",
            "langgraph-typescript-quickstart",
            "deepagents-python-quickstart",
            "deepagents-typescript-quickstart",
            "langchain-middleware",
        )

        self.assertFalse(any(name in content for name in absent))

    def test_dependency_guidance_requires_resolved_pins_and_lockfiles(self) -> None:
        content = _ROOT.joinpath(
            "skills/engineers/langchain/langchain-dependencies/SKILL.md"
        ).read_text(encoding="utf-8")
        lower = content.lower()

        self.assertNotIn('"latest"', content)
        self.assertNotIn("use latest", lower)
        self.assertIn("security advisories", lower)
        self.assertIn("exact", lower)
        self.assertIn("lockfile", lower)

    def test_syncthing_requires_authorization_before_configuration(self) -> None:
        content = _ROOT.joinpath(
            "skills/tools/sync-transport/references/syncthing.md"
        ).read_text(encoding="utf-8")

        self.assertIn("explicit authorization", content)
        self.assertIn('\\"type\\": \\"sendonly\\"', content)
        self.assertNotIn("`type: sendreceive` is the default", content)

    def test_readme_badges_match_the_portable_catalog(self) -> None:
        readme = _ROOT.joinpath("README.md").read_text(encoding="utf-8")
        agents = len(tuple(_ROOT.glob("agents/**/*.md")))
        skills = len(tuple(_ROOT.glob("skills/**/SKILL.md")))

        self.assertIn(f"badge/agents-{agents}-", readme)
        self.assertIn(f"badge/skills-{skills}-", readme)

    def test_excalidraw_agent_uses_only_the_abstract_canvas_capability(self) -> None:
        paths = (
            _ROOT / "agents/tools/excalidraw.md",
            _ROOT / "skills/tools/excalidraw-diagrams/SKILL.md",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertIn("`diagram-canvas`", content)
        self.assertNotIn("mcp__", content)
        self.assertNotIn("mcp-excalidraw-server", content)

    def test_slack_agent_preserves_voice_and_draft_safety(self) -> None:
        paths = (
            _ROOT / "agents/tools/slack.md",
            _ROOT / "skills/tools/slack-messaging/SKILL.md",
            _ROOT / "codex/agents/slack.toml",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertIn("primeira pessoa do singular", content.lower())
        self.assertIn("team-messaging", content)
        self.assertIn("rascunho", content.lower())
        self.assertIn("lançamento", content.lower())
        self.assertNotIn("mcp__", content)
        self.assertIn("nome canônico", content.lower())
        self.assertIn("```text", content)

    def test_slack_capability_is_declared_by_both_harnesses(self) -> None:
        claude = _ROOT.joinpath("claude-code", "CLAUDE.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("codex", "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("`team-messaging`", claude)
        self.assertIn("`team-messaging`", codex)

    def test_engineering_agents_load_the_evidence_skill(self) -> None:
        roles = ("ai-engineer", "architect", "developer", "qa", "sre", "tech-pm")

        for role in roles:
            with self.subTest(role=role):
                shared = _ROOT.joinpath(f"agents/engineers/{role}.md").read_text(
                    encoding="utf-8"
                )
                codex = _ROOT.joinpath(f"codex/agents/{role}.toml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("  - evidence", shared)
                self.assertIn("`evidence`", codex)

    def test_site_skills_are_harness_neutral(self) -> None:
        paths = (
            _ROOT / "skills/tools/site-report/SKILL.md",
            _ROOT / "skills/tools/site-expose/SKILL.md",
        )
        content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertFalse(
            any(token in content for token in ("CLAUDE.md", "Explore", "dataviz"))
        )
        self.assertIn("abstract `tunnel` capability", content)
        self.assertIn("[a-z0-9]+(?:-[a-z0-9]+)*", content)
        self.assertIn("https://", content)

    def test_codex_hook_has_a_managed_session_start(self) -> None:
        data = json.loads(
            _ROOT.joinpath("codex/hooks.json").read_text(encoding="utf-8")
        )
        groups = data["hooks"]["SessionStart"]
        commands = [
            handler["command"] for group in groups for handler in group["hooks"]
        ]
        self.assertTrue(any("omh-managed: context" in command for command in commands))
        self.assertTrue(
            any("{codex_home}/hooks/context-load.sh" in command for command in commands)
        )

    def test_context_loader_is_shared_and_executable(self) -> None:
        loader = _ROOT / "hooks/context-load.sh"
        claude_adapter = _ROOT / "claude-code/hooks/context-load.sh"

        self.assertTrue(loader.is_file())
        self.assertTrue(loader.stat().st_mode & 0o111)
        self.assertIn(
            "../../hooks/context-load.sh", claude_adapter.read_text(encoding="utf-8")
        )

    def test_context_agents_resolve_the_git_root(self) -> None:
        shared = _ROOT.joinpath("agents/tools/context.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("codex/agents/context.toml").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --show-toplevel", shared)
        self.assertIn("git rev-parse --show-toplevel", codex)

    def _yaml_name(self, path: Path) -> str:
        match = re.search(
            r"^name:\s*([^\s]+)", path.read_text(encoding="utf-8"), re.MULTILINE
        )
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""

    def _toml_name(self, path: Path) -> str:
        match = re.search(
            r'^name\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE
        )
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""
