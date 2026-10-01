"""CLI remediation distinguishes note validation from environment failures."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.clock import SystemClock
from kb.adapters.filesystem import FileNoteStore
from kb.app.context import Context
from kb.cli import main


class CliErrorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = FileNoteStore(self.root)
        self.context = Context(self.store, SystemClock(), 'unused')

    def run_cli(self, args):
        output = io.StringIO()
        with patch('kb.cli.build_context', return_value=self.context), contextlib.redirect_stdout(output):
            code = main([*args, '--json'])
        return code, json.loads(output.getvalue())

    def test_backup_collision_requires_environment_repair(self):
        self.store.write_text('old.md', 'current')
        self.store.write_text('backup/old.md', 'different')
        code, result = self.run_cli(['backup', '--apply'])
        self.assertEqual(4, code)
        self.assertEqual('Degraded', result['status'])
        self.assertIn('Backup collision', result['reason'])
        self.assertEqual('current', self.store.read_text('old.md'))
        self.assertEqual('different', self.store.read_text('backup/old.md'))

    def test_unavailable_backup_is_blocked_not_success_or_note_rejection(self):
        self.store.write_text('.missing.md.icloud', 'placeholder')
        code, result = self.run_cli(['backup', '--apply'])
        self.assertEqual(4, code)
        self.assertEqual('Blocked', result['status'])
        self.assertFalse(self.store.exists('backup/.manifest.json'))

    def test_publication_preserves_safe_transcript_failure_reason(self):
        transcript = self.root / 'transcript.jsonl'
        transcript.write_text('{broken-private-fixture')
        code, result = self.run_cli(['validate', '--path', 'work/project/note/note.md',
                                     '--file', str(self.root / 'missing.md'), '--transcript', str(transcript)])
        self.assertEqual(4, code)
        self.assertIn('invalid JSON', result['reason'])
        self.assertNotIn('private-fixture', result['reason'])
