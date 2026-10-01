from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))


class BundleBoundaryTest(unittest.TestCase):
    def test_store_rejects_paths_outside_bundle(self):
        from kb.adapters.filesystem import FileNoteStore
        with tempfile.TemporaryDirectory() as root:
            store = FileNoteStore(Path(root))
            for target in ('../outside.md', '/tmp/outside.md'):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    store.resolve(target)

    def test_store_rejects_symlink_escape(self):
        from kb.adapters.filesystem import FileNoteStore
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as external:
            Path(root, 'escape').symlink_to(external)
            with self.assertRaises(ValueError):
                FileNoteStore(Path(root)).resolve('escape/note.md')

    def test_atomic_write_preserves_previous_bytes_until_replace(self):
        from kb.adapters.filesystem import FileNoteStore
        with tempfile.TemporaryDirectory() as root:
            store = FileNoteStore(Path(root))
            store.write_text('work/demo/index.md', 'before')
            store.write_text('work/demo/index.md', 'after')
            self.assertEqual('after', Path(root, 'work/demo/index.md').read_text())
            self.assertEqual([], list(Path(root).rglob('*.tmp')))
