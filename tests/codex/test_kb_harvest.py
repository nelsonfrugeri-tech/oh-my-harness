import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))

from kb.adapters.transcript_claude import ClaudeTranscriptSource
from kb.app.harvest import Harvested, Unavailable, harvest
from kb.entities.kinds import EntityKind


def tool(name, arguments, identifier='tool-1'):
    return {'type': 'assistant', 'message': {'role': 'assistant', 'content': [
        {'type': 'tool_use', 'id': identifier, 'name': name, 'input': arguments}]}}


def result(text, identifier='tool-1'):
    return {'type': 'user', 'message': {'role': 'user', 'content': [
        {'type': 'tool_result', 'tool_use_id': identifier, 'content': text}]}}


class HarvestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'session.jsonl'
        self.adapter = ClaudeTranscriptSource()

    def _write(self, records):
        self.source.write_text('\n'.join(json.dumps(record) for record in records) + '\n')

    def _candidates(self):
        outcome = harvest(self.adapter, str(self.source))
        self.assertIsInstance(outcome, Harvested)
        return {(candidate.kind, candidate.value) for candidate in outcome.candidates}

    def test_harvests_web_fetch_search_and_browser_urls(self):
        self._write([tool('WebFetch', {'url': 'https://example.com/docs'}),
                     tool('WebSearch', {'query': 'docs'}, 'search'),
                     result('Found https://example.com/results', 'search'),
                     tool('mcp__browser__navigate', {'url': 'https://example.com/page'})])
        values = self._candidates()
        for url in ('https://example.com/docs', 'https://example.com/results', 'https://example.com/page'):
            self.assertIn((EntityKind.URLS, url), values)

    def test_harvests_explicit_tool_paths_with_spaces_and_bash_paths(self):
        records = [tool(name, {'file_path' if name in ('Read', 'Write', 'Edit') else 'path':
                              '/tmp/My Project/' + name}) for name in ('Read', 'Write', 'Edit', 'Grep', 'Glob')]
        records.append(tool('Bash', {'command': "cat '/tmp/My Project/output.md'"}))
        self._write(records)
        values = self._candidates()
        for name in ('Read', 'Write', 'Edit', 'Grep', 'Glob', 'output.md'):
            self.assertIn((EntityKind.PATHS, '/tmp/My Project/' + name), values)
        self.assertNotIn((EntityKind.PATHS, '/tmp/My'), values)

    def test_harvests_https_and_ssh_git_remotes_as_repositories(self):
        self._write([tool('Bash', {'command': 'git remote -v'}, 'remote'),
                     result('origin https://github.com/acme/project (fetch)\n'
                            'upstream git@github.com:acme/other.git (push)', 'remote')])
        values = self._candidates()
        self.assertIn((EntityKind.REPOS, 'https://github.com/acme/project'), values)
        self.assertIn((EntityKind.REPOS, 'git@github.com:acme/other.git'), values)

    def test_harvests_apps_only_from_explicit_access_requests(self):
        self._write([tool('mcp__computer_use__request_access', {'app': 'Final Cut Pro'}),
                     tool('mcp__computer_use__request_access', {'apps': ['Cursor', 'LinkedIn']}),
                     result('An unrelated mention of Safari')])
        values = self._candidates()
        for app in ('final-cut-pro', 'cursor', 'linkedin'):
            self.assertIn((EntityKind.APPS, app), values)
        self.assertNotIn((EntityKind.APPS, 'safari'), values)

    def test_subagents_and_tool_results_are_loaded_from_session_directory(self):
        self._write([result('A sessão principal.')])
        child = self.root / 'session/subagents/agent.jsonl'
        child.parent.mkdir(parents=True)
        child.write_text(json.dumps(tool('Read', {'file_path': '/tmp/subagent.md'})))
        output = self.root / 'session/tool-results/result.txt'
        output.parent.mkdir(parents=True)
        output.write_text('https://example.com/child')
        values = self._candidates()
        self.assertIn((EntityKind.PATHS, '/tmp/subagent.md'), values)
        self.assertIn((EntityKind.URLS, 'https://example.com/child'), values)
        self.assertIn('/tmp/subagent.md', self.adapter.load(str(self.source)))

    def test_harvest_filters_secrets_before_extraction_and_normalization(self):
        self._write([result('https://example.com/?token=fake-secret\npassword=/tmp/private.txt\n'
                            'https://example.com/public'),
                     tool('mcp__computer_use__request_access', {'app': 'password=fake-secret'}),
                     tool('WebFetch', {'headers': {'token': 'https://example.com/secret'}})])
        values = self._candidates()
        self.assertEqual({(EntityKind.URLS, 'https://example.com/public')}, values)

    def test_codex_malformed_and_missing_transcripts_are_unavailable(self):
        for text in ('{"type":"session_meta","payload":{}}\n', '{broken', '[]\n', ''):
            self.source.write_text(text)
            self.assertIsInstance(harvest(self.adapter, str(self.source)), Unavailable)
        self.assertIsInstance(harvest(self.adapter, str(self.root / 'missing')), Unavailable)

    def test_external_symlink_tool_results_are_not_read(self):
        self._write([result('A sessão principal.')])
        outside = self.root / 'outside.txt'
        outside.write_text('https://example.com/outside')
        linked = self.root / 'session/tool-results/link.txt'
        linked.parent.mkdir(parents=True)
        linked.symlink_to(outside)
        self.assertEqual(set(), self._candidates())


if __name__ == '__main__':
    unittest.main()
