from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections.abc import Callable
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import install as install_module
from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest
from lib.link_operations import LinkOperations
from lib.links import ManagedLinks
from lib.managed_agents import ManagedAgents
from lib.managed_hooks import ManagedHooks
from lib.sync import CodexInstaller, InstallConflict


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
        self._codex_home.joinpath("AGENTS.md").write_text(
            "Personal rule.\n", encoding="utf-8"
        )
        existing_hooks = {
            "hooks": {"SessionStart": [{"hooks": [{"command": "deja hook"}]}]}
        }
        self._codex_home.joinpath("hooks.json").write_text(
            json.dumps(existing_hooks),
            encoding="utf-8",
        )

        self._installer.install()

        self.assertTrue(self._agents_home.joinpath("skills/example").is_symlink())
        self.assertTrue(self._codex_home.joinpath("agents/developer.toml").is_symlink())
        self.assertTrue(self._codex_home.joinpath("hooks/context-load.sh").is_symlink())
        self.assertTrue(
            self._codex_home.joinpath("rules/destructive.rules").is_symlink()
        )
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

        hooks = json.loads(
            self._codex_home.joinpath("hooks.json").read_text(encoding="utf-8")
        )
        commands = [
            handler["command"]
            for group in hooks["hooks"]["SessionStart"]
            for handler in group["hooks"]
        ]
        self.assertIn("deja hook", commands)
        self.assertEqual(
            1, sum("omh-managed: context" in command for command in commands)
        )

    def test_install_removes_only_orphaned_managed_links(self) -> None:
        retired_source = self._source / "skills/engineers/retired"
        retired_source.mkdir(parents=True)
        retired_source.joinpath("SKILL.md").write_text(
            "---\nname: retired\n---\n", encoding="utf-8"
        )
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
        self.assertTrue(
            any(result.startswith("removed stale managed link:") for result in results)
        )

    def test_install_preserves_machine_capability_mappings(self) -> None:
        self._installer.install()
        target = self._codex_home / "AGENTS.md"
        configured = (
            target.read_text(encoding="utf-8")
            .replace(
                "_(configure during installation)_",
                "GitHub connector",
            )
            .replace("_(optional tunnel)_", "Approved private tunnel")
            .replace(
                "_(local sync)_",
                "Private sync adapter",
            )
            .replace(
                "_(governed SQL)_",
                "Private Databricks SQL adapter",
            )
        )
        target.write_text(configured, encoding="utf-8")
        source = self._source / "codex/AGENTS.md"
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "Shared rules.", "Updated rules."
            ),
            encoding="utf-8",
        )

        self._installer.install()

        merged = target.read_text(encoding="utf-8")
        self.assertIn("GitHub connector", merged)
        self.assertIn("Approved private tunnel", merged)
        self.assertIn("Private sync adapter", merged)
        self.assertIn("Private Databricks SQL adapter", merged)
        self.assertIn("Updated rules.", merged)

    def test_install_composes_local_machine_overlay(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._codex_home.joinpath("AGENTS.local.md").write_text(
            "Private machine adapter.\n",
            encoding="utf-8",
        )

        self._installer.install()

        agents = self._codex_home.joinpath("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Shared rules.", agents)
        self.assertIn("# Local machine overlay", agents)
        self.assertIn("Private machine adapter.", agents)

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

    def test_symlinked_agents_config_fails_preflight_without_replacement(self) -> None:
        self._assert_symlinked_config_is_preserved("AGENTS.md", "Personal rules.\n")

    def test_symlinked_hooks_config_fails_preflight_without_replacement(self) -> None:
        self._assert_symlinked_config_is_preserved(
            "hooks.json", '{"hooks": {}}\n'
        )

    def test_install_is_idempotent(self) -> None:
        self._installer.install()
        first_agents = self._codex_home.joinpath("AGENTS.md").read_text(
            encoding="utf-8"
        )

        self._installer.install()

        second_agents = self._codex_home.joinpath("AGENTS.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(first_agents, second_agents)
        self.assertTrue(
            all(result.startswith("ok:") for result in self._installer.validate())
        )

    def test_install_refuses_to_replace_user_owned_skill(self) -> None:
        skill = self._agents_home / "skills/example"
        skill.mkdir(parents=True)

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())

    def test_install_refuses_regular_legacy_agent_without_migration(self) -> None:
        target = self._codex_home / "agents/developer.toml"
        target.parent.mkdir(parents=True)
        target.write_text('name = "legacy-developer"\n', encoding="utf-8")
        target.parent.joinpath(".oh-my-harness-managed.json").write_text(
            json.dumps({"version": 1, "agents": ["developer.toml"]}),
            encoding="utf-8",
        )

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(target.is_symlink())
        self.assertIn("legacy-developer", target.read_text(encoding="utf-8"))

    def test_explicit_legacy_migration_backs_up_and_links_managed_agents(self) -> None:
        target = self._codex_home / "agents/developer.toml"
        target.parent.mkdir(parents=True)
        target.write_text('name = "legacy-developer"\n', encoding="utf-8")
        target.parent.joinpath("corporate.toml").write_text(
            'name = "corporate"\n',
            encoding="utf-8",
        )
        target.parent.joinpath(".oh-my-harness-managed.json").write_text(
            json.dumps({"version": 1, "agents": ["developer.toml"]}),
            encoding="utf-8",
        )

        CodexInstaller(self._layout, migrate_legacy_agents=True).install()

        self.assertTrue(target.is_symlink())
        self.assertEqual(
            self._source.joinpath("codex/agents/developer.toml").resolve(),
            target.resolve(),
        )
        self.assertTrue(target.parent.joinpath("corporate.toml").is_file())
        backups = tuple(
            self._codex_home.glob("backups/omh-legacy-agents-*/agents/developer.toml")
        )
        self.assertEqual(1, len(backups))
        self.assertIn("legacy-developer", backups[0].read_text(encoding="utf-8"))

    def test_legacy_migration_rolls_back_when_commit_rename_fails(self) -> None:
        targets = self._create_legacy_agents("developer.toml")
        target = targets[0]
        temporary = target.with_name(f".{target.name}.omh-migration")
        original_replace = Path.replace

        def fail_commit(path: Path, destination: Path) -> Path:
            if path == temporary and destination == target:
                raise OSError("injected commit failure")
            return original_replace(path, destination)

        with (
            mock.patch.object(Path, "replace", new=fail_commit),
            self.assertRaisesRegex(OSError, "injected commit failure"),
        ):
            CodexInstaller(self._layout, migrate_legacy_agents=True).install()

        self._assert_legacy_agents_restored(targets)
        self.assertFalse(temporary.is_symlink())
        self._assert_backup_contents("developer.toml")

    def test_legacy_migration_rolls_back_first_agent_when_second_fails(self) -> None:
        targets = self._create_legacy_agents("developer.toml", "qa.toml")
        second = targets[1]
        temporary = second.with_name(f".{second.name}.omh-migration")
        original_replace = Path.replace

        def fail_second_commit(path: Path, destination: Path) -> Path:
            if path == temporary and destination == second:
                raise OSError("injected second agent failure")
            return original_replace(path, destination)

        with (
            mock.patch.object(Path, "replace", new=fail_second_commit),
            self.assertRaisesRegex(OSError, "injected second agent failure"),
        ):
            CodexInstaller(self._layout, migrate_legacy_agents=True).install()

        self._assert_legacy_agents_restored(targets)
        self._assert_backup_contents("developer.toml", "qa.toml")

    def test_legacy_migration_rolls_back_after_links_finish(self) -> None:
        targets = self._create_legacy_agents("developer.toml")

        with (
            mock.patch(
                "lib.sync.ManagedConfig.install",
                side_effect=OSError("injected config failure"),
            ),
            self.assertRaisesRegex(OSError, "injected config failure"),
        ):
            CodexInstaller(self._layout, migrate_legacy_agents=True).install()

        self._assert_legacy_agents_restored(targets)
        self._assert_backup_contents("developer.toml")

    def test_install_rolls_back_after_each_link_publish(self) -> None:
        targets = (
            self._layout.installed_adapter,
            self._layout.installed_hooks / "context-load.sh",
            self._layout.installed_rules / "destructive.rules",
            self._layout.personal_skills / "example",
            self._layout.custom_agents / "developer.toml",
        )
        original_publish = LinkOperations.publish

        for failed_target in targets:
            with (
                self.subTest(target=failed_target),
                mock.patch.object(
                    LinkOperations,
                    "publish",
                    new=self._fail_after_publish(failed_target, original_publish),
                ),
                self.assertRaisesRegex(OSError, "injected publish failure"),
            ):
                self._installer.install()

            self._assert_clean_install_targets()

    def test_install_rolls_back_after_manifest_write(self) -> None:
        original_write = ManagedLinkManifest.write

        def fail_after_write(
            manifest: ManagedLinkManifest,
            entries: tuple[tuple[Path, Path], ...],
        ) -> str:
            original_write(manifest, entries)
            raise OSError("injected manifest failure")

        with (
            mock.patch.object(ManagedLinkManifest, "write", new=fail_after_write),
            self.assertRaisesRegex(OSError, "injected manifest failure"),
        ):
            self._installer.install()

        self._assert_clean_install_targets()

    def test_install_restores_existing_manifest_after_rewrite(self) -> None:
        self._installer.install()
        manifest = self._layout.links_manifest.read_text(encoding="utf-8")
        skill = self._source / "skills/engineers/second"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: second\n---\n", encoding="utf-8"
        )
        original_write = ManagedLinkManifest.write

        def fail_after_write(
            managed_manifest: ManagedLinkManifest,
            entries: tuple[tuple[Path, Path], ...],
        ) -> str:
            original_write(managed_manifest, entries)
            raise OSError("injected manifest rewrite failure")

        with (
            mock.patch.object(ManagedLinkManifest, "write", new=fail_after_write),
            self.assertRaisesRegex(OSError, "injected manifest rewrite failure"),
        ):
            self._installer.install()

        self.assertEqual(
            manifest, self._layout.links_manifest.read_text(encoding="utf-8")
        )
        self.assertFalse(self._agents_home.joinpath("skills/second").is_symlink())

    def test_install_rolls_back_agents_file_after_its_write(self) -> None:
        self._codex_home.mkdir(parents=True)
        target = self._layout.global_agents_file
        target.write_text("Personal rule.\n", encoding="utf-8")
        original_install = ManagedAgents.install

        def fail_after_write(agents: ManagedAgents) -> str:
            original_install(agents)
            raise OSError("injected AGENTS.md failure")

        with (
            mock.patch.object(ManagedAgents, "install", new=fail_after_write),
            self.assertRaisesRegex(OSError, "injected AGENTS.md failure"),
        ):
            self._installer.install()

        self.assertEqual("Personal rule.\n", target.read_text(encoding="utf-8"))
        self.assertEqual(
            "Personal rule.\n",
            target.with_suffix(".md.omh.bak").read_text(encoding="utf-8"),
        )
        self._assert_clean_link_targets()

    def test_install_rolls_back_hooks_file_after_its_write(self) -> None:
        self._codex_home.mkdir(parents=True)
        agents = self._layout.global_agents_file
        hooks = self._layout.hooks_file
        agents.write_text("Personal rule.\n", encoding="utf-8")
        hooks.write_text('{"hooks": {}}\n', encoding="utf-8")
        original_install = ManagedHooks.install

        def fail_after_write(managed_hooks: ManagedHooks) -> str:
            original_install(managed_hooks)
            raise OSError("injected hooks.json failure")

        with (
            mock.patch.object(ManagedHooks, "install", new=fail_after_write),
            self.assertRaisesRegex(OSError, "injected hooks.json failure"),
        ):
            self._installer.install()

        self.assertEqual("Personal rule.\n", agents.read_text(encoding="utf-8"))
        self.assertEqual('{"hooks": {}}\n', hooks.read_text(encoding="utf-8"))
        self.assertTrue(agents.with_suffix(".md.omh.bak").is_file())
        self.assertTrue(hooks.with_suffix(".json.omh.bak").is_file())
        self._assert_clean_link_targets()

    def test_install_restores_orphan_when_removal_fails(self) -> None:
        source = self._source / "skills/engineers/retired"
        source.mkdir(parents=True)
        source.joinpath("SKILL.md").write_text(
            "---\nname: retired\n---\n", encoding="utf-8"
        )
        self._installer.install()
        orphan = self._agents_home / "skills/retired"
        linked_source = orphan.readlink()
        manifest = self._layout.links_manifest.read_text(encoding="utf-8")
        shutil.rmtree(source)
        original_remove = ManagedLinks._remove_orphans

        def fail_after_remove(links: ManagedLinks) -> tuple[str, ...]:
            original_remove(links)
            raise OSError("injected orphan failure")

        with (
            mock.patch.object(ManagedLinks, "_remove_orphans", new=fail_after_remove),
            self.assertRaisesRegex(OSError, "injected orphan failure"),
        ):
            self._installer.install()

        self.assertTrue(orphan.is_symlink())
        self.assertEqual(linked_source, orphan.readlink())
        self.assertEqual(
            manifest, self._layout.links_manifest.read_text(encoding="utf-8")
        )

    def test_hook_parent_conflict_fails_before_any_write(self) -> None:
        self._codex_home.mkdir(parents=True)
        self._codex_home.joinpath("hooks").write_text("user-owned", encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.install()

        self.assertFalse(self._codex_home.joinpath("oh-my-harness").exists())
        self.assertFalse(self._agents_home.exists())

    def test_entrypoint_does_not_run_integrations_after_preflight_conflict(
        self,
    ) -> None:
        conflict = self._codex_home / "oh-my-harness"
        conflict.mkdir(parents=True)
        arguments = [
            "install.py",
            "--codex-home",
            str(self._codex_home),
            "--agents-home",
            str(self._agents_home),
        ]

        with (
            mock.patch.object(sys, "argv", arguments),
            mock.patch.object(
                install_module.CodexIntegrations, "install"
            ) as integrations,
        ):
            self.assertEqual(1, install_module.main())

        integrations.assert_not_called()

    def test_entrypoint_reports_integration_failure_after_core_commit_as_pending(
        self,
    ) -> None:
        arguments = [
            "install.py",
            "--codex-home",
            str(self._codex_home),
            "--agents-home",
            str(self._agents_home),
        ]
        output = StringIO()
        errors = StringIO()

        with (
            mock.patch.object(sys, "argv", arguments),
            mock.patch.object(
                install_module.CodexInstaller, "install", return_value=("core",)
            ),
            mock.patch.object(
                install_module.CodexIntegrations,
                "install",
                side_effect=OSError("integration unavailable"),
            ),
            mock.patch("sys.stdout", output),
            redirect_stderr(errors),
        ):
            self.assertEqual(0, install_module.main())

        self.assertIn("committed: Codex core installation", output.getvalue())
        self.assertIn("pending: integrations", output.getvalue())
        self.assertNotIn("error:", errors.getvalue())

    def test_entrypoint_defaults_to_environment_homes(self) -> None:
        arguments = ["install.py"]
        environment = {
            "CODEX_HOME": str(self._codex_home),
            "AGENTS_HOME": str(self._agents_home),
        }

        with (
            mock.patch.object(sys, "argv", arguments),
            mock.patch.dict("os.environ", environment),
        ):
            parsed = install_module._arguments()

        self.assertEqual(self._codex_home, parsed.codex_home)
        self.assertEqual(self._agents_home, parsed.agents_home)

    def test_entrypoint_treats_blank_environment_homes_as_unset(self) -> None:
        arguments = ["install.py"]

        with (
            mock.patch.object(sys, "argv", arguments),
            mock.patch.dict(
                "os.environ",
                {"CODEX_HOME": "   ", "AGENTS_HOME": ""},
            ),
            mock.patch.object(Path, "home", return_value=self._source.parent),
        ):
            parsed = install_module._arguments()

        self.assertEqual(self._source.parent / ".codex", parsed.codex_home)
        self.assertEqual(self._source.parent / ".agents", parsed.agents_home)

    def test_entrypoint_rejects_relative_and_source_owned_homes(self) -> None:
        invalid_arguments = (
            ["install.py", "--codex-home", "relative", "--check"],
            [
                "install.py",
                "--codex-home",
                str(Path(__file__).resolve().parents[2] / "private-codex"),
                "--check",
            ],
        )

        for arguments in invalid_arguments:
            with (
                self.subTest(arguments=arguments),
                mock.patch.object(sys, "argv", arguments),
                redirect_stderr(StringIO()),
            ):
                self.assertEqual(1, install_module.main())

    def test_install_preserves_compatible_external_graphify(self) -> None:
        source = self._source / "skills/tools/graphify"
        source.mkdir(parents=True)
        source.joinpath("SKILL.md").write_text(
            "---\nupstream_version: 0.9.27\nname: graphify\n---\n",
            encoding="utf-8",
        )
        target = self._agents_home / "skills/graphify"
        target.mkdir(parents=True)
        target.joinpath(".graphify_version").write_text("0.9.27", encoding="utf-8")

        results = self._installer.install()

        self.assertTrue(any(result.startswith("preserved:") for result in results))
        self.assertFalse(target.is_symlink())

    def test_repeated_config_updates_backup_each_current_preimage(self) -> None:
        self._installer.install()
        target = self._layout.global_agents_file
        source = self._layout.adapter / "AGENTS.md"
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "Shared rules.", "First shared rules."
            ),
            encoding="utf-8",
        )
        self._installer.install()
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "First shared rules.", "Second shared rules."
            ),
            encoding="utf-8",
        )

        self._installer.install()

        backups = tuple(self._codex_home.glob("AGENTS.md.omh.bak*"))
        contents = tuple(path.read_text(encoding="utf-8") for path in backups)
        self.assertGreaterEqual(len(backups), 2)
        self.assertTrue(any("Shared rules." in text for text in contents))
        self.assertTrue(any("First shared rules." in text for text in contents))

    def test_manifest_rejects_unconfined_entries_before_pruning(self) -> None:
        source = self._source / "skills/engineers/retired"
        outside = self._source.parent / "outside"
        outside.mkdir()
        cases = (
            ("relative", str(source)),
            (str(outside / "target"), str(source)),
            (str(self._agents_home / "skills/retired"), str(outside / "source")),
        )

        for target, recorded_source in cases:
            with self.subTest(target=target, source=recorded_source):
                self._write_manifest(target, recorded_source)
                manifest = ManagedLinkManifest(self._layout, InstallConflict)
                with self.assertRaises(InstallConflict):
                    manifest.orphans(set())

    def test_manifest_rejects_target_whose_managed_parent_is_symlinked_outside(
        self,
    ) -> None:
        outside = self._source.parent / "outside-skills"
        outside.mkdir()
        self._agents_home.mkdir()
        self._agents_home.joinpath("skills").symlink_to(outside)
        target = self._agents_home / "skills/retired"
        source = self._source / "skills/engineers/retired"
        source.mkdir(parents=True)
        target.symlink_to(source)
        self._write_manifest(str(target), str(source))

        manifest = ManagedLinkManifest(self._layout, InstallConflict)
        with self.assertRaises(InstallConflict):
            manifest.orphans(set())

        self.assertTrue(target.is_symlink())

    def test_manifest_rejects_source_symlink_that_escapes_source_root(self) -> None:
        outside = self._source.parent / "outside-source"
        outside.mkdir()
        source = self._source / "skills/engineers/escape"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.symlink_to(outside)
        target = self._agents_home / "skills/escape"
        self._write_manifest(str(target), str(source))

        manifest = ManagedLinkManifest(self._layout, InstallConflict)
        with self.assertRaises(InstallConflict):
            manifest.orphans(set())

    def test_legacy_and_link_modules_remain_within_code_craft_size_limit(self) -> None:
        library = Path(__file__).resolve().parents[1] / "lib"
        for name in ("legacy_agents.py", "links.py"):
            with self.subTest(name=name):
                lines = library.joinpath(name).read_text(encoding="utf-8").splitlines()
                self.assertLessEqual(len(lines), 120)

    def test_validate_detects_stale_managed_agents_block(self) -> None:
        self._installer.install()
        target = self._codex_home / "AGENTS.md"
        content = target.read_text(encoding="utf-8").replace(
            "Shared rules.", "Stale rules."
        )
        target.write_text(content, encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._installer.validate()

    def test_install_can_replace_confirmed_legacy_global_agents(self) -> None:
        self._codex_home.mkdir(parents=True)
        target = self._codex_home / "AGENTS.md"
        target.write_text(
            """Legacy oh-my-harness rules.

| Capability | Purpose | Codex provider on this machine |
| --- | --- | --- |
| `code-host` | Pull requests | Private GitLab adapter |
""",
            encoding="utf-8",
        )
        self._codex_home.joinpath("AGENTS.local.md").write_text(
            "Private machine rule.\n",
            encoding="utf-8",
        )

        CodexInstaller(self._layout, replace_global_agents=True).install()

        content = target.read_text(encoding="utf-8")
        self.assertNotIn("Legacy", content)
        self.assertIn("Private GitLab adapter", content)
        self.assertIn("Private machine rule.", content)
        backup = self._codex_home / "AGENTS.md.omh.bak"
        self.assertIn("Legacy", backup.read_text(encoding="utf-8"))

    def _create_source(self) -> None:
        skill = self._source / "skills/engineers/example"
        agent = self._source / "codex/agents"
        hook = self._source / "hooks"
        rules = self._source / "codex/rules"
        skill.mkdir(parents=True)
        agent.mkdir(parents=True)
        hook.mkdir(parents=True)
        rules.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: example\n---\n", encoding="utf-8"
        )
        agent.joinpath("developer.toml").write_text(
            'name = "developer"\n', encoding="utf-8"
        )
        hook.joinpath("context-load.sh").write_text(
            "#!/usr/bin/env bash\n", encoding="utf-8"
        )
        rules.joinpath("destructive.rules").write_text(
            'prefix_rule(pattern=["rm"], decision="prompt")\n',
            encoding="utf-8",
        )
        agents_content = """Shared rules.

| Capability | Purpose | Codex provider on this machine |
| --- | --- | --- |
| `code-host` | Pull requests | _(configure during installation)_ |
| `databricks-sql` | Governed SQL | _(governed SQL)_ |
| `file-sync` | Cross-machine sync | _(local sync)_ |
| `tunnel` | Temporary exposure | _(optional tunnel)_ |
"""
        self._source.joinpath("codex/AGENTS.md").write_text(
            agents_content, encoding="utf-8"
        )
        hooks = {
            "hooks": {
                "SessionStart": [{"hooks": [{"command": "run # omh-managed: context"}]}]
            }
        }
        self._source.joinpath("codex/hooks.json").write_text(
            json.dumps(hooks), encoding="utf-8"
        )

    def _create_legacy_agents(self, *names: str) -> tuple[Path, ...]:
        agent_sources = self._source / "codex/agents"
        targets = tuple(self._codex_home / "agents" / name for name in names)
        for source, target in zip((agent_sources / name for name in names), targets):
            source.write_text(f'name = "{source.stem}"\n', encoding="utf-8")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f'name = "legacy-{target.stem}"\n', encoding="utf-8")
        self._codex_home.joinpath("agents/.oh-my-harness-managed.json").write_text(
            json.dumps({"version": 1, "agents": list(names)}),
            encoding="utf-8",
        )
        return targets

    def _write_manifest(self, target: str, source: str) -> None:
        self._layout.links_manifest.parent.mkdir(parents=True, exist_ok=True)
        self._layout.links_manifest.write_text(
            json.dumps(
                {"version": 1, "links": [{"target": target, "source": source}]}
            ),
            encoding="utf-8",
        )

    def _assert_symlinked_config_is_preserved(
        self, name: str, content: str
    ) -> None:
        external = self._source.parent / f"external-{name}"
        external.write_text(content, encoding="utf-8")
        target = self._codex_home / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(external)

        with self.assertRaisesRegex(InstallConflict, "symbolic link"):
            self._installer.install()

        self.assertTrue(target.is_symlink())
        self.assertEqual(content, external.read_text(encoding="utf-8"))

    def _assert_legacy_agents_restored(self, targets: tuple[Path, ...]) -> None:
        for target in targets:
            self.assertFalse(target.is_symlink())
            self.assertEqual(
                f'name = "legacy-{target.stem}"\n',
                target.read_text(encoding="utf-8"),
            )

    def _assert_backup_contents(self, *names: str) -> None:
        for name in names:
            backups = tuple(
                self._codex_home.glob(f"backups/omh-legacy-agents-*/agents/{name}")
            )
            self.assertEqual(1, len(backups))
            self.assertEqual(
                f'name = "legacy-{Path(name).stem}"\n',
                backups[0].read_text(encoding="utf-8"),
            )

    def _assert_clean_install_targets(self) -> None:
        self.assertFalse(self._layout.global_agents_file.exists())
        self.assertFalse(self._layout.hooks_file.exists())
        self._assert_clean_link_targets()
        self.assertFalse(self._layout.codex_home.exists())
        self.assertFalse(self._layout.agents_home.exists())

    def _fail_after_publish(
        self,
        failed_target: Path,
        publish: Callable[[LinkOperations, Path, Path], str],
    ) -> Callable[[LinkOperations, Path, Path], str]:
        def failure(operation: LinkOperations, source: Path, target: Path) -> str:
            result = publish(operation, source, target)
            if target == failed_target:
                raise OSError(f"injected publish failure: {target}")
            return result

        return failure

    def _assert_clean_link_targets(self) -> None:
        targets = (
            self._layout.installed_adapter,
            self._layout.installed_hooks / "context-load.sh",
            self._layout.installed_rules / "destructive.rules",
            self._layout.personal_skills / "example",
            self._layout.custom_agents / "developer.toml",
            self._layout.links_manifest,
        )
        for target in targets:
            self.assertFalse(target.exists())
            self.assertFalse(target.is_symlink())
        for directory in (
            self._layout.installed_hooks,
            self._layout.installed_rules,
            self._layout.custom_agents,
            self._layout.personal_skills,
        ):
            self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
