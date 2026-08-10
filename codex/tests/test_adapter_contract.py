from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]


class AdapterContractTest(unittest.TestCase):
    def test_every_portable_agent_has_a_codex_adapter(self) -> None:
        shared = {
            self._yaml_name(path)
            for path in _ROOT.glob("agents/**/*.md")
            if path.name != "claude-code.md"
        }
        adapters = {
            self._toml_name(path)
            for path in _ROOT.glob("codex/agents/*.toml")
            if path.name != "codex.toml"
        }
        self.assertEqual(shared, adapters)

    def test_skill_leaf_names_are_unique_for_codex(self) -> None:
        sources = (
            *_ROOT.glob("skills/**/SKILL.md"),
            *_ROOT.glob("codex/skills/**/SKILL.md"),
        )
        names = [path.parent.name for path in sources if path.parent.name != "claude-code"]
        self.assertEqual(len(names), len(set(names)))

    def test_feature_skill_uses_portable_orchestration(self) -> None:
        content = _ROOT.joinpath("skills/engineers/feature/SKILL.md").read_text(encoding="utf-8")
        forbidden = ("Workflow({", "AskUserQuestion", "use the tool `Agent`")
        self.assertFalse(any(token in content for token in forbidden))
        self.assertIn("Portable orchestration contract", content)

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

        self.assertFalse(any(token in content for token in ("CLAUDE.md", "Explore", "dataviz")))
        self.assertIn("abstract `tunnel` capability", content)
        self.assertIn("[a-z0-9]+(?:-[a-z0-9]+)*", content)
        self.assertIn("https://", content)

    def test_codex_hook_has_a_managed_session_start(self) -> None:
        data = json.loads(_ROOT.joinpath("codex/hooks.json").read_text(encoding="utf-8"))
        groups = data["hooks"]["SessionStart"]
        commands = [handler["command"] for group in groups for handler in group["hooks"]]
        self.assertTrue(any("omh-managed: context" in command for command in commands))
        self.assertTrue(any("{codex_home}/hooks/context-load.sh" in command for command in commands))

    def test_context_loader_is_shared_and_executable(self) -> None:
        loader = _ROOT / "hooks/context-load.sh"
        claude_adapter = _ROOT / "claude-code/hooks/context-load.sh"

        self.assertTrue(loader.is_file())
        self.assertTrue(loader.stat().st_mode & 0o111)
        self.assertIn("../../hooks/context-load.sh", claude_adapter.read_text(encoding="utf-8"))

    def test_context_agents_resolve_the_git_root(self) -> None:
        shared = _ROOT.joinpath("agents/tools/context.md").read_text(encoding="utf-8")
        codex = _ROOT.joinpath("codex/agents/context.toml").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --show-toplevel", shared)
        self.assertIn("git rev-parse --show-toplevel", codex)

    def _yaml_name(self, path: Path) -> str:
        match = re.search(r"^name:\s*([^\s]+)", path.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""

    def _toml_name(self, path: Path) -> str:
        match = re.search(r'^name\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(match, str(path))
        return match.group(1) if match else ""
