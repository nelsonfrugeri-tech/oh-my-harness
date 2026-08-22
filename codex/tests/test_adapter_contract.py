from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]


class AdapterContractTest(unittest.TestCase):
    def test_codex_plugin_matches_the_shared_plugin_identity(self) -> None:
        codex = json.loads(
            _ROOT.joinpath(".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        claude = json.loads(
            _ROOT.joinpath(".claude-plugin/plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            _ROOT.joinpath(".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )

        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual(claude["version"], marketplace["metadata"]["version"])
        self.assertEqual("./skills/", codex["skills"])
        self.assertIn("./claude-code/skills/", claude["skills"])
        self.assertNotIn("./skills/codex/", claude["skills"])
        self.assertNotIn("./skills/", claude["skills"])
        self.assertTrue(_ROOT.joinpath("hooks/hooks.json").is_file())

    def test_codex_marketplace_exposes_the_repository_plugin(self) -> None:
        marketplace = json.loads(
            _ROOT.joinpath(".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        plugin = marketplace["plugins"][0]

        self.assertEqual("oh-my-harness", marketplace["name"])
        self.assertEqual("oh-my-harness", plugin["name"])
        self.assertEqual({"source": "local", "path": "./"}, plugin["source"])
        self.assertEqual("AVAILABLE", plugin["policy"]["installation"])
        self.assertEqual("ON_INSTALL", plugin["policy"]["authentication"])

    def test_shared_skills_are_flat_for_native_plugin_discovery(self) -> None:
        skill_roots = tuple(
            path for path in _ROOT.joinpath("skills").iterdir() if path.is_dir()
        )

        self.assertTrue(skill_roots)
        self.assertTrue(all(path.joinpath("SKILL.md").is_file() for path in skill_roots))
        self.assertNotIn("claude-code", {path.name for path in skill_roots})

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_codex_cli_installs_the_expected_skill_inventory(self) -> None:
        manifest = json.loads(
            _ROOT.joinpath(".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as temporary:
            env = {**os.environ, "CODEX_HOME": temporary}
            self._run_codex(env, "plugin", "marketplace", "add", str(_ROOT))
            self._run_codex(
                env,
                "plugin",
                "add",
                "oh-my-harness@oh-my-harness",
            )
            installed = Path(temporary).joinpath(
                "plugins/cache/oh-my-harness/oh-my-harness",
                manifest["version"],
            )

            shared = {
                path.name
                for path in installed.joinpath("skills").iterdir()
                if path.is_dir()
            }
            expected = {
                path.name
                for path in _ROOT.joinpath("skills").iterdir()
                if path.is_dir()
            }
            self.assertEqual(expected, shared)
            self.assertTrue(installed.joinpath("skills/codex/SKILL.md").is_file())
            self.assertTrue(installed.joinpath("hooks/hooks.json").is_file())

    def test_plugin_hooks_use_the_codex_schema_and_standalone_instructions(self) -> None:
        hooks = json.loads(_ROOT.joinpath("hooks/hooks.json").read_text(encoding="utf-8"))
        handlers = [
            handler
            for groups in hooks["hooks"].values()
            for group in groups
            for handler in group["hooks"]
        ]
        context_loader = _ROOT.joinpath("hooks/context-load.sh").read_text(encoding="utf-8")

        self.assertTrue(all("if" not in handler for handler in handlers))
        self.assertIn("Run the `explorer` skill", context_loader)
        self.assertNotIn("invoke the `context` agent", context_loader)

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
        content = _ROOT.joinpath("skills/feature/SKILL.md").read_text(encoding="utf-8")
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
            _ROOT / "skills/site-report/SKILL.md",
            _ROOT / "skills/site-expose/SKILL.md",
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

    def _run_codex(self, env: dict[str, str], *arguments: str) -> None:
        completed = subprocess.run(
            ("codex", *arguments),
            cwd=_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
