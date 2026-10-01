from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.filesystem import FileNoteStore
from kb.app.check import check
from kb.app.context import Context
from test_kb_note_bundle import FixedClock
from test_kb_note_domain import MACHINE


class BundleCheckTest(unittest.TestCase):
    def test_conflict_and_temporary_artifact_are_reported_without_parsing_backup(self):
        with tempfile.TemporaryDirectory() as root:
            store = FileNoteStore(Path(root))
            store.write_text('work/demo/topic/topic 2.md', 'conflict')
            store.write_text('work/demo/topic/.topic.md.tmp', 'interrupted')
            store.write_text('backup/old.md', 'legacy format')
            store.write_text('backup/INSTRUCTION.md', 'reserved')
            report = check(Context(store, FixedClock(), MACHINE))
            self.assertTrue(any('iCloud conflict' in error for error in report.errors))
            self.assertTrue(any('orphan temporary' in error for error in report.errors))
            self.assertFalse(any('backup/' in error for error in report.errors))

    def test_empty_entity_directory_requires_index_entry(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'work/demo/orphan').mkdir(parents=True)
            report = check(Context(FileNoteStore(Path(root)), FixedClock(), MACHINE))
            self.assertTrue(any('orphan' in error for error in report.errors))
