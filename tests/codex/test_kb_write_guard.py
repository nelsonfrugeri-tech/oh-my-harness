import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / 'core/hooks/kb-write-guard.sh'


class KbWriteGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle = self.root / 'kb'
        self.bundle.mkdir()

    def _run(self, path, *, tool='Write', cwd=None):
        payload = {'tool_name': tool, 'tool_input': {'file_path': str(path)},
                   'cwd': str(cwd or self.root)}
        result = subprocess.run(['bash', str(HOOK)], input=json.dumps(payload),
                                text=True, capture_output=True,
                                env=dict(os.environ, OMH_KB_ROOT=str(self.bundle)), timeout=5)
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)['hookSpecificOutput'] if result.stdout else None

    def test_direct_write_and_edit_inside_bundle_are_denied(self):
        for tool in ('Write', 'Edit'):
            decision = self._run(self.bundle / 'work/domain/new/new.md', tool=tool)
            self.assertEqual('deny', decision['permissionDecision'])
            self.assertIn('kb.py', decision['permissionDecisionReason'])

    def test_relative_paths_resolve_from_payload_cwd(self):
        decision = self._run('work/new.md', cwd=self.bundle)
        self.assertEqual('deny', decision['permissionDecision'])

    def test_outside_paths_and_non_markdown_files_are_not_guarded(self):
        self.assertIsNone(self._run(self.root / 'kb-other/note.md'))
        self.assertIsNone(self._run(self.root / 'product.md'))
        self.assertIsNone(self._run(self.bundle / 'identity.json'))

    def test_symlink_alias_into_bundle_is_denied(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.bundle, target_is_directory=True)
        self.assertEqual('deny', self._run(alias / 'note.md')['permissionDecision'])

    def test_symlink_out_of_bundle_still_denies_bundle_named_write(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.bundle / 'link').symlink_to(outside, target_is_directory=True)
        self.assertEqual('deny', self._run(self.bundle / 'link/note.md')['permissionDecision'])

    def test_case_alias_matches_filesystem_identity(self):
        alias = self.root / 'KB'
        if alias.exists():
            self.assertTrue(alias.samefile(self.bundle))
            self.assertEqual('deny', self._run(alias / 'work/new.md')['permissionDecision'])
        else:
            alias.mkdir()
            self.assertIsNone(self._run(alias / 'work/new.md'))

    def test_cli_and_other_tool_calls_are_not_matched(self):
        self.assertIsNone(self._run(self.bundle / 'note.md', tool='Bash'))
        self.assertIsNone(self._run(self.bundle / 'note.md', tool='Read'))

    def test_malformed_payload_is_denied_without_exposing_input(self):
        result = subprocess.run(['bash', str(HOOK)], input='{broken', text=True, capture_output=True,
                                env=dict(os.environ, OMH_KB_ROOT=str(self.bundle)), timeout=5)
        self.assertEqual(0, result.returncode)
        self.assertEqual('deny', json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'])
        self.assertNotIn('{broken', result.stdout)

    def test_guard_is_registered_for_write_and_edit_in_both_harnesses(self):
        for harness in ('claude', 'codex'):
            manifest = json.loads((ROOT / f'harness/{harness}/hooks/hooks.json').read_text())
            guards = [entry for entry in manifest['hooks']['PreToolUse']
                      if any('kb-write-guard.sh' in hook['command'] for hook in entry['hooks'])]
            self.assertEqual(1, len(guards))
            self.assertEqual('Write|Edit', guards[0]['matcher'])


if __name__ == '__main__':
    unittest.main()
