from __future__ import annotations

import errno
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "installers/codex"))

from lib.layout import InstallLayout
from lib.link_manifest import ManagedLinkManifest
from lib.sync import InstallConflict


class ManagedLinkManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self._root = Path(self._temporary.name).resolve()
        self._layout = InstallLayout(self._root / "source", self._root / "codex", self._root / "agents")
        self._layout.codex_home.mkdir()
        self._manifest = ManagedLinkManifest(self._layout, InstallConflict)

    def _write(self, entries: tuple[tuple[Path, Path], ...]) -> None:
        links = [{"target": str(target), "source": str(source)} for target, source in entries]
        self._layout.links_manifest.write_text(json.dumps({"version": 1, "links": links}))

    def test_invalid_paths_and_duplicate_targets_are_rejected(self) -> None:
        target = self._layout.personal_skills / "example"
        source = self._root / "old-source"
        invalid = (
            ((self._root / "outside", source),),
            ((Path("relative"), source),),
            ((target.parent / ".." / "skills" / target.name, source),),
            ((target / "nested", source),),
            ((target, Path("relative")),),
            ((target, source / ".." / "other"),),
            ((target, source), (target, source)),
            ((self._layout.custom_agents / "unrelated.txt", source),),
        )
        for entries in invalid:
            with self.subTest(entries=entries):
                self._write(entries)
                with self.assertRaisesRegex(InstallConflict, str(self._layout.links_manifest)):
                    self._manifest.stale(set())

    def test_parent_symlink_cannot_authorize_removal_outside_managed_directory(self) -> None:
        outside = self._root / "outside"
        outside.mkdir()
        self._layout.agents_home.mkdir()
        self._layout.personal_skills.symlink_to(outside)
        target = self._layout.personal_skills / "example"
        source = self._root / "old-source"
        target.symlink_to(source)
        self._write(((target, source),))
        with self.assertRaises(InstallConflict):
            self._manifest.stale(set())
        self.assertTrue((outside / "example").is_symlink())

    def test_configured_codex_home_alias_is_an_authorized_root(self) -> None:
        alias = self._root / "codex-home-alias"
        alias.symlink_to(self._layout.codex_home)
        layout = InstallLayout(self._layout.source_root, alias, self._layout.agents_home)
        source = self._root / "legacy-source"
        layout.installed_adapter.symlink_to(source)
        self._write(((layout.installed_adapter, source),))

        manifest = ManagedLinkManifest(layout, InstallConflict)

        self.assertTrue(manifest.owns_target(layout.installed_adapter))
        self.assertEqual((self._layout.installed_adapter,), manifest.stale(set()))

    def test_hooks_and_agent_directory_aliases_cannot_authorize_removal(self) -> None:
        outside = self._root / "outside"
        outside.mkdir()
        source = self._root / "legacy-source"
        for parent, name in (
            (self._layout.installed_hooks, "hook.sh"),
            (self._layout.custom_agents, "agent.toml"),
        ):
            with self.subTest(parent=parent):
                parent.symlink_to(outside)
                target = parent / name
                target.symlink_to(source)
                self._write(((target, source),))
                with self.assertRaises(InstallConflict):
                    self._manifest.stale(set())
                self.assertEqual(source, target.readlink())

    def test_duplicate_targets_through_home_alias_are_rejected(self) -> None:
        alias = self._root / "codex-alias"
        alias.symlink_to(self._layout.codex_home)
        source = self._root / "legacy-source"
        self._write((
            (self._layout.installed_adapter, source),
            (alias / "oh-my-harness", source),
        ))
        with self.assertRaises(InstallConflict):
            self._manifest.stale(set())

    def test_physical_paths_do_not_bypass_redirected_managed_directories(self) -> None:
        for parent, name in (
            (self._layout.personal_skills, "skill"),
            (self._layout.installed_hooks, "hook.sh"),
            (self._layout.custom_agents, "agent.toml"),
        ):
            with self.subTest(parent=parent):
                outside = self._root / f"outside-{name}"
                outside.mkdir()
                parent.parent.mkdir(parents=True, exist_ok=True)
                parent.symlink_to(outside)
                source = self._root / "legacy-source"
                target = outside / name
                target.symlink_to(source)
                self._write(((target, source),))
                with self.assertRaises(InstallConflict):
                    self._manifest.stale(set())
                self.assertEqual(source, target.readlink())

    def test_unconfigured_direct_parent_alias_does_not_authorize_removal(self) -> None:
        self._layout.personal_skills.mkdir(parents=True)
        alias = self._root / "skills-alias"
        alias.symlink_to(self._layout.personal_skills)
        source = self._root / "legacy-source"
        target = alias / "example"
        target.symlink_to(source)
        self._write(((target, source),))
        with self.assertRaises(InstallConflict):
            self._manifest.stale(set())
        self.assertEqual(source, target.readlink())

    def test_expected_path_resolution_error_names_the_directory(self) -> None:
        target = self._layout.installed_adapter
        with mock.patch.object(Path, "resolve", side_effect=OSError(errno.ELOOP, "loop")):
            with self.assertRaises(InstallConflict) as raised:
                self._manifest.stale({(target, self._root / "source")})
        self.assertIn(str(target.parent), str(raised.exception))
        self.assertNotIn("manifesto", str(raised.exception))

    def test_directory_containment_loop_reports_manifest_conflict(self) -> None:
        self._layout.personal_skills.mkdir(parents=True)
        self._layout.custom_agents.symlink_to(self._layout.custom_agents)
        source = self._root / "legacy-source"
        target = self._layout.personal_skills / "example"
        target.symlink_to(source)
        self._write(((target, source),))
        with self.assertRaisesRegex(InstallConflict, "oh-my-harness-links.json"):
            self._manifest.stale(set())
        self.assertEqual(source, target.readlink())

    def test_corrupt_or_unreadable_manifest_reports_install_conflict(self) -> None:
        for content in (b"{", b"\xff", b'{"version": 2}', b'{"version": 1, "links": [null]}'):
            with self.subTest(content=content):
                self._layout.links_manifest.write_bytes(content)
                with self.assertRaisesRegex(InstallConflict, str(self._layout.links_manifest)):
                    self._manifest.stale(set())
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(InstallConflict, str(self._layout.links_manifest)):
                self._manifest.stale(set())

    def test_existing_source_uses_filesystem_identity(self) -> None:
        source = self._root / "Source"
        source.write_text("same inode")
        alias = self._root / "source-alias"
        os.link(source, alias)
        target = self._layout.installed_adapter
        target.symlink_to(alias)
        self._write(((target, source),))
        self.assertTrue(self._manifest.owns_target(target))

    def test_filesystem_identity_errors_fail_closed(self) -> None:
        source = self._root / "source-file"
        source.write_text("source")
        target = self._layout.installed_adapter
        target.symlink_to(source)
        self._write(((target, source),))
        for error_code in (errno.ENOTDIR, errno.ELOOP, errno.EACCES):
            with self.subTest(error_code=error_code), mock.patch.object(
                Path, "samefile", side_effect=OSError(error_code, "identity unavailable")
            ):
                with self.assertRaisesRegex(InstallConflict, "oh-my-harness-links.json"):
                    self._manifest.stale(set())
                self.assertEqual(source, target.readlink())

    def test_legacy_home_aliases_normalize_only_target_parents(self) -> None:
        self._layout.personal_skills.mkdir(parents=True)
        codex_alias = self._root / "codex-alias"
        agents_alias = self._root / "agents-alias"
        codex_alias.symlink_to(self._layout.codex_home)
        agents_alias.symlink_to(self._layout.agents_home)
        source = self._root / "missing-legacy-source"
        target = self._layout.personal_skills / "example"
        target.symlink_to(source)
        self._layout.installed_adapter.symlink_to(source)
        self._write(((agents_alias / "skills/example", source), (codex_alias / "oh-my-harness", source)))

        self.assertTrue(self._manifest.owns_target(target))
        self.assertTrue(self._manifest.owns_target(self._layout.installed_adapter))
        self.assertEqual(
            {target, self._layout.installed_adapter}, set(self._manifest.stale(set()))
        )


if __name__ == "__main__":
    unittest.main()
