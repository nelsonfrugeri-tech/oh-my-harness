from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.filesystem import FileNoteStore
from kb.adapters.backup_filesystem import FileBackupStore
from kb.app.backup import backup
from kb.app.backup_model import Applied, Planned
from kb.app.context import Context
from test_kb_note_bundle import FixedClock


class LegacyIndex:
    def mark_legacy(self, prefix, *, source_paths=None):
        return 4


class BackupPreservationTest(unittest.TestCase):
    def test_backup_is_byte_preserving_idempotent_and_documents_legacy(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            store = FileNoteStore(path)
            store.write_text('work/projects/demo/old.md', 'old bytes\n')
            store.write_text('.obsidian/config.json', '{}')
            store.write_text('.trash/removed.md', 'removed')
            context = Context(store, FixedClock(), 'unused', LegacyIndex())
            template = (ROOT / 'core/skills/kb-write/scripts/kb/app/assets/backup-instruction.md').read_text()
            options = dict(template=template, reason='Preservação do formato antigo.', plan='kb-note-model-r1')
            before = sorted(str(p.relative_to(path)) for p in path.rglob('*'))
            self.assertIsInstance(backup(context, FileBackupStore(path), apply=False, **options), Planned)
            self.assertEqual(before, sorted(str(p.relative_to(path)) for p in path.rglob('*')))
            first = backup(context, FileBackupStore(path), apply=True, **options)
            self.assertIsInstance(first, Applied)
            self.assertEqual(b'old bytes\n', (path / 'backup/work/projects/demo/old.md').read_bytes())
            self.assertEqual('{}', store.read_text('.obsidian/config.json'))
            self.assertEqual('removed', store.read_text('.trash/removed.md'))
            instruction = store.read_text('backup/INSTRUCTION.md')
            self.assertIn(first.manifest_sha256, instruction)
            second = backup(context, FileBackupStore(path), apply=True, **options)
            self.assertEqual(first, second)
            self.assertEqual(instruction, store.read_text('backup/INSTRUCTION.md'))

    def test_unavailable_icloud_placeholder_blocks_apply(self):
        from kb.app.backup_model import Blocked
        with tempfile.TemporaryDirectory() as root:
            store = FileNoteStore(Path(root))
            store.write_text('.missing.md.icloud', 'placeholder')
            context = Context(store, FixedClock(), 'unused', LegacyIndex())
            result = backup(context, FileBackupStore(Path(root)), apply=True,
                            template='', reason='migration', plan='plan')
            self.assertIsInstance(result, Blocked)
            self.assertFalse(store.exists('backup/.manifest.json'))

    def test_tampered_manifest_cannot_move_a_file_outside_bundle(self):
        import json
        with tempfile.TemporaryDirectory() as root:
            store = FileNoteStore(Path(root))
            store.write_text('backup/.manifest.json', json.dumps({'entries': [
                {'path': '../outside.md', 'sha256': 'bad', 'size': 1}],
                'at': '2026-10-01T00:00:00Z', 'reason': 'migration', 'plan': 'plan'}))
            context = Context(store, FixedClock(), 'unused', LegacyIndex())
            with self.assertRaises(ValueError):
                backup(context, FileBackupStore(Path(root)), apply=True,
                       template='', reason='migration', plan='plan')
