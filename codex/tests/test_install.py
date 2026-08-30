from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.layout import InstallLayout
from lib.skill_identity import graphify_distribution_matches
from lib.sync import CodexInstaller, InstallConflict
import install as install_module


class CodexInstallerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        root = Path(self._temporary.name)
        self._source = root / "source"
        self._codex_home = root / "codex-home"
        self._agents_home = root / "agents-home"
        self._create_source()
        self._layout = InstallLayout(self._source, self._codex_home, self._agents_home)
        self._installer = CodexInstaller(self._layout)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_install_links_artifacts_and_preserves_user_configuration(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._codex_home.joinpath("AGENTS.md").write_text("Personal rule.\n", encoding="utf-8")
        existing_hooks = {"hooks": {"SessionStart": [{"hooks": [{"command": "deja hook"}]}]}}
        self._codex_home.joinpath("hooks.json").write_text(
            json.dumps(existing_hooks),
            encoding="utf-8",
        )

        self._installer.install()

        self.assertTrue(self._agents_home.joinpath("skills/example").is_symlink())
        installed_agent = self._codex_home / "agents/developer.toml"
        self.assertTrue(installed_agent.is_file())
        self.assertFalse(installed_agent.is_symlink())
        self.assertEqual('name = "developer"\n', installed_agent.read_text(encoding="utf-8"))
        self.assertTrue(self._codex_home.joinpath("hooks/context-load.sh").is_symlink())
        agents = self._codex_home.joinpath("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Personal rule.", agents)
        self.assertIn("Shared rules.", agents)
        hooks = self._codex_home.joinpath("hooks.json").read_text(encoding="utf-8")
        self.assertIn("deja hook", hooks)
        self.assertIn("omh-managed: context", hooks)

    def test_install_preserves_user_handler_in_managed_hook_group(self) -> None:
        self._codex_home.mkdir(parents=True)
        mixed_group = {
            "matcher": "startup|resume",
            "hooks": [
                {"command": "old # omh-managed: context"},
                {"command": "deja hook"},
            ],
        }
        self._codex_home.joinpath("hooks.json").write_text(
            json.dumps({"hooks": {"SessionStart": [mixed_group]}}),
            encoding="utf-8",
        )

        self._installer.install()

        hooks = json.loads(self._codex_home.joinpath("hooks.json").read_text(encoding="utf-8"))
        commands = [
            handler["command"]
            for group in hooks["hooks"]["SessionStart"]
            for handler in group["hooks"]
        ]
        self.assertIn("deja hook", commands)
        self.assertEqual(1, sum("omh-managed: context" in command for command in commands))

    def test_install_removes_only_orphaned_managed_links(self) -> None:
        retired_source = self._source / "skills/retired"
        retired_source.mkdir(parents=True)
        retired_source.joinpath("SKILL.md").write_text("---\nname: retired\n---\n", encoding="utf-8")
        self._installer.install()
        managed = self._agents_home / "skills/retired"
        shutil.rmtree(retired_source)
        personal_source = self._source / "personal-artifact"
        personal_source.mkdir()
        external = self._agents_home / "skills/personal"
        external.symlink_to(personal_source)

        results = self._installer.install()

        self.assertFalse(managed.exists())
        self.assertFalse(managed.is_symlink())
        self.assertTrue(external.is_symlink())
        self.assertTrue(any(result.startswith("link gerenciado desatualizado removido:") for result in results))

    def test_install_preserves_machine_capability_mappings(self) -> None:
        self._installer.install()
        target = self._codex_home / "AGENTS.md"
        configured = target.read_text(encoding="utf-8").replace(
            "_(configure during installation)_",
            "GitHub connector",
        ).replace("_(optional tunnel)_", "Approved private tunnel")
        target.write_text(configured, encoding="utf-8")
        source = self._source / "codex/AGENTS.md"
        source.write_text(
            source.read_text(encoding="utf-8").replace("Shared rules.", "Updated rules."),
            encoding="utf-8",
        )

        self._installer.install()

        merged = target.read_text(encoding="utf-8")
        self.assertIn("GitHub connector", merged)
        self.assertIn("Approved private tunnel", merged)
        self.assertIn("Updated rules.", merged)

    def test_invalid_hook_shape_fails_before_any_write(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._codex_home.joinpath("hooks.json").write_text(
            json.dumps({"hooks": {"SessionStart": None}}),
            encoding="utf-8",
        )

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())
        self.assertFalse(self._codex_home.joinpath("AGENTS.md").exists())

    def test_install_is_idempotent(self) -> None:
        self._installer.install()
        first_agents = self._codex_home.joinpath("AGENTS.md").read_text(encoding="utf-8")

        self._installer.install()

        second_agents = self._codex_home.joinpath("AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(first_agents, second_agents)
        self.assertTrue(all(result.startswith("ok:") for result in self._installer.validate()))

    def test_install_updates_an_unchanged_managed_agent_copy(self) -> None:
        self._installer.install()
        source = self._source / "codex/agents/developer.toml"
        source.write_text('name = "developer"\ndescription = "updated"\n', encoding="utf-8")

        self._installer.install()

        target = self._codex_home / "agents/developer.toml"
        self.assertEqual(source.read_text(encoding="utf-8"), target.read_text(encoding="utf-8"))

    def test_install_migrates_a_managed_agent_symlink_to_a_copy(self) -> None:
        source = self._source / "codex/agents/developer.toml"
        target = self._codex_home / "agents/developer.toml"
        target.parent.mkdir(parents=True)
        target.symlink_to(source)
        manifest = {"version": 1, "links": [{"target": str(target), "source": str(source)}]}
        self._layout.links_manifest.write_text(json.dumps(manifest), encoding="utf-8")

        self._installer.install()

        self.assertTrue(target.is_file())
        self.assertFalse(target.is_symlink())
        self.assertEqual(source.read_text(encoding="utf-8"), target.read_text(encoding="utf-8"))

    def test_failed_agent_copy_preserves_the_managed_agent_symlink(self) -> None:
        source = self._source / "codex/agents/developer.toml"
        target = self._codex_home / "agents/developer.toml"
        target.parent.mkdir(parents=True)
        target.symlink_to(source)
        manifest = {"version": 1, "links": [{"target": str(target), "source": str(source)}]}
        self._layout.links_manifest.write_text(json.dumps(manifest), encoding="utf-8")

        with mock.patch("lib.agent_copies.atomic_write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self._installer.install()

        self.assertTrue(target.is_symlink())
        self.assertEqual(source.resolve(), target.resolve())

    def test_install_refuses_to_replace_a_modified_managed_agent_copy(self) -> None:
        self._installer.install()
        target = self._codex_home / "agents/developer.toml"
        target.write_text('name = "personal"\n', encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_install_rejects_an_agent_manifest_target_outside_the_managed_directory(self) -> None:
        outside = self._temporary.name + "/outside.toml"
        manifest = {
            "version": 1,
            "agents": [{"target": outside, "source": outside, "sha256": "0" * 64}],
        }
        self._codex_home.mkdir(parents=True)
        self._layout.agents_manifest.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_install_rejects_a_structurally_invalid_agent_manifest(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._layout.agents_manifest.write_text('{"version": 1, "agents": [{}]}', encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_install_rejects_invalid_agent_manifest_json(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._layout.agents_manifest.write_text("{", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_install_refuses_to_replace_user_owned_skill(self) -> None:
        skill = self._agents_home / "skills/example"
        skill.mkdir(parents=True)

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())

    def test_hook_parent_conflict_fails_before_any_write(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._codex_home.joinpath("hooks").write_text("user-owned", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())
        self.assertFalse(self._agents_home.exists())

    def test_entrypoint_does_not_run_integrations_after_preflight_conflict(self) -> None:
        conflict = self._codex_home / "oh-my-harness"
        conflict.mkdir(parents=True)
        arguments = [
            "install.py",
            "--codex-home",
            str(self._codex_home),
            "--agents-home",
            str(self._agents_home),
        ]

        with mock.patch.object(sys, "argv", arguments):
            with mock.patch.object(install_module.CodexIntegrations, "install") as integrations:
                self.assertEqual(1, install_module.main())

        integrations.assert_not_called()

    def test_install_preserves_compatible_external_graphify(self) -> None:
        source = self._create_graphify_source()
        target = self._agents_home / "skills/graphify"
        target.parent.mkdir(parents=True)
        shutil.copytree(source, target)
        target.joinpath(".graphify_version").write_text("0.9.27", encoding="utf-8")

        results = self._installer.install()

        self.assertTrue(any(result.startswith("preservada:") for result in results))
        self.assertFalse(target.is_symlink())

    def test_install_rejects_external_graphify_with_same_version_and_different_content(
        self,
    ) -> None:
        self._create_graphify_source()
        target = self._agents_home / "skills/graphify"
        target.mkdir(parents=True)
        target.joinpath("SKILL.md").write_text("upstream content\n", encoding="utf-8")
        target.joinpath(".graphify_version").write_text("0.9.27", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())

    def test_install_rejects_external_graphify_with_changed_reference(self) -> None:
        source = self._create_graphify_source()
        target = self._agents_home / "skills/graphify"
        target.parent.mkdir(parents=True)
        shutil.copytree(source, target)
        target.joinpath(".graphify_version").write_text("0.9.27", encoding="utf-8")
        target.joinpath("references/hooks.md").write_text("stale hooks\n", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_validate_detects_external_graphify_after_source_changes(self) -> None:
        source = self._create_graphify_source()
        target = self._agents_home / "skills/graphify"
        target.parent.mkdir(parents=True)
        shutil.copytree(source, target)
        target.joinpath(".graphify_version").write_text("0.9.27", encoding="utf-8")
        self._installer.install()
        source.joinpath("references/hooks.md").write_text("new harness hooks\n", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.validate()

    def test_install_rejects_external_graphify_with_invalid_version_marker(self) -> None:
        source = self._create_graphify_source()
        target = self._agents_home / "skills/graphify"
        target.parent.mkdir(parents=True)
        shutil.copytree(source, target)
        target.joinpath(".graphify_version").write_bytes(b"\xff")

        with self.assertRaises(InstallConflict):
            self._installer.install()

    def test_graphify_identity_rejects_unencodable_paths(self) -> None:
        error = UnicodeEncodeError("utf-8", "\udcff", 0, 1, "surrogate")
        with mock.patch("lib.skill_identity._tree_digest", side_effect=error):
            matches = graphify_distribution_matches(Path("source"), Path("target"))

        self.assertFalse(matches)

    def test_validate_detects_stale_managed_agents_block(self) -> None:
        self._installer.install()
        target = self._codex_home / "AGENTS.md"
        content = target.read_text(encoding="utf-8").replace("Shared rules.", "Stale rules.")
        target.write_text(content, encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.validate()

    def test_install_can_replace_confirmed_legacy_global_agents(self) -> None:
        self._codex_home.mkdir(parents=True)
        target = self._codex_home / "AGENTS.md"
        target.write_text("Legacy oh-my-harness rules.\n", encoding="utf-8")

        CodexInstaller(self._layout, replace_global_agents=True).install()

        self.assertNotIn("Legacy", target.read_text(encoding="utf-8"))
        backup = self._codex_home / "AGENTS.md.omh.bak"
        self.assertIn("Legacy", backup.read_text(encoding="utf-8"))

    def _create_source(self) -> None:
        skill = self._source / "skills/example"
        agent = self._source / "codex/agents"
        hook = self._source / "hooks"
        skill.mkdir(parents=True)
        agent.mkdir(parents=True)
        hook.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text("---\nname: example\n---\n", encoding="utf-8")
        agent.joinpath("developer.toml").write_text('name = "developer"\n', encoding="utf-8")
        hook.joinpath("context-load.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        agents_content = """Shared rules.

| Capability | Purpose | Codex provider on this machine |
| --- | --- | --- |
| `code-host` | Pull requests | _(configure during installation)_ |
| `tunnel` | Temporary exposure | _(optional tunnel)_ |
"""
        self._source.joinpath("codex/AGENTS.md").write_text(agents_content, encoding="utf-8")
        hooks = {
            "hooks": {
                "SessionStart": [{"hooks": [{"command": "run # omh-managed: context"}]}]
            }
        }
        self._source.joinpath("codex/hooks.json").write_text(json.dumps(hooks), encoding="utf-8")

    def _create_graphify_source(self) -> Path:
        source = self._source / "skills/graphify"
        references = source / "references"
        references.mkdir(parents=True)
        source.joinpath("SKILL.md").write_text(
            "---\nupstream_version: 0.9.27\nname: graphify\n---\nWorkspace safety.\n",
            encoding="utf-8",
        )
        references.joinpath("hooks.md").write_text("native hooks\n", encoding="utf-8")
        return source


if __name__ == "__main__":
    unittest.main()
