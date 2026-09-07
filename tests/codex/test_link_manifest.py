from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
