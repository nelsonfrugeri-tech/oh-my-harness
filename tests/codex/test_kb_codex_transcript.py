import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.transcript_claude import ClaudeTranscriptSource
from kb.app.harvest import Harvested, harvest
from kb.app.errors import TranscriptFailure
from kb.dispatch import dispatch
from types import SimpleNamespace


def item(kind, **fields):
    return {'type': 'response_item', 'payload': {'type': kind, **fields}}


class CodexTranscriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'session.jsonl'

    def write(self, records):
        self.path.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in records), encoding='utf-8')

    def test_claude_unicode_separator_is_content_not_jsonl_boundary(self):
        self.write([{'type': 'user', 'message': {'content': 'Antes\u2028depois https://example.org/docs'}}])
        self.assertIn('Antes\u2028depois', ClaudeTranscriptSource().load(str(self.path)))

    def test_dispatch_codex_harvest_recovers_messages_tools_and_remote_relationships(self):
        self.write([{'type': 'session_meta', 'payload': {'cwd': '/metadata/only'}},
                    item('message', role='user', content=[{'type': 'input_text', 'text': 'Leia https://example.org/docs\u2028agora.'}]),
                    item('function_call', name='exec_command', arguments=json.dumps({'cmd': "git remote -v; cat '/tmp/My Project/note.md'"}), call_id='remote'),
                    item('function_call_output', call_id='remote', output='origin https://example.org/project (fetch)'),
                    item('custom_tool_call', name='apply_patch', call_id='patch', input='*** Begin Patch\n*** Add File: /tmp/example.md\n+conteúdo\n*** End Patch'),
                    item('custom_tool_call_output', call_id='patch', output='https://example.org/result'),
                    {'type': 'turn_context', 'payload': {'summary': 'https://metadata.invalid'}}])
        result = dispatch(SimpleNamespace(command='harvest', transcript=str(self.path)), None)
        self.assertIsInstance(result, Harvested)
        values = {(c.kind.value, c.value) for c in result.candidates}
        self.assertIn(('urls', 'https://example.org/docs'), values)
        self.assertIn(('repos', 'https://example.org/project'), values)
        self.assertIn(('paths', '/tmp/My Project/note.md'), values)
        self.assertIn(('paths', '/tmp/example.md'), values)
        self.assertNotIn(('paths', '/metadata/only'), values)
        self.assertFalse(any('metadata.invalid' in v for _, v in values))

    def test_codex_load_excludes_metadata_reasoning_and_filters_secrets(self):
        from kb.adapters.transcript import TranscriptSource
        self.write([{'type': 'session_meta', 'payload': {'base_instructions': 'private metadata'}},
                    item('reasoning', summary=[{'text': 'private reasoning'}], encrypted_content='private ciphertext'),
                    item('message', role='assistant', content=[{'type': 'output_text', 'text': 'Mensagem https://example.org/public password=fixture-secret'}])])
        text = TranscriptSource().load(str(self.path))
        self.assertIn('https://example.org/public', text)
        for excluded in ('private metadata', 'private reasoning', 'private ciphertext', 'fixture-secret'):
            self.assertNotIn(excluded, text)

    def test_structured_secret_fields_do_not_become_load_or_harvest_evidence(self):
        from kb.adapters.transcript import TranscriptSource
        self.write([item('function_call', name='fetch', call_id='secret',
                         arguments=json.dumps({'password': 'short-fixture', 'senha': 'fixture-senha', 'url': 'https://example.org/public',
                                               'headers': {'authorization': 'secret-fixture'}})),
                    item('function_call_output', call_id='secret',
                         output={'token': 'output-fixture', 'data': [{'api_key': 'nested-fixture',
                                                                 'text': 'Resultado público.'}]})])
        adapter = TranscriptSource()
        text = adapter.load(str(self.path))
        for secret in ('short-fixture', 'secret-fixture', 'output-fixture', 'nested-fixture', 'fixture-senha'):
            self.assertNotIn(secret, text)
        self.assertIn('https://example.org/public', text)
        self.assertIn('Resultado público.', text)
        self.assertIsInstance(harvest(adapter, str(self.path)), Harvested)

    def test_unsupported_content_and_unpaired_outputs_fail_with_safe_diagnostic(self):
        from kb.adapters.transcript import TranscriptSource
        for record in (item('future_evidence', text='private-fixture'),
                       item('function_call_output', call_id='absent', output='private-fixture'),
                       item('message', role='user', content=[{'type': 'future_text', 'text': 'private-fixture'}])):
            self.write([{'type': 'session_meta', 'payload': {}}, record])
            with self.assertRaises(TranscriptFailure) as error:
                TranscriptSource().load(str(self.path))
            self.assertNotIn('private-fixture', str(error.exception))

    def test_mixed_event_messages_are_preserved_without_duplicate_mirrors(self):
        from kb.adapters.transcript import TranscriptSource
        self.write([item('message', role='user', content=[{'type': 'input_text', 'text': 'Mensagem espelhada.'}]),
                    {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'Mensagem espelhada.'}},
                    {'type': 'event_msg', 'payload': {'type': 'agent_message', 'message': 'Mensagem apenas no evento.'}}])
        text = TranscriptSource().load(str(self.path))
        self.assertEqual(1, text.count('Mensagem espelhada.'))
        self.assertIn('Mensagem apenas no evento.', text)

    def test_ambiguous_call_identity_is_rejected(self):
        from kb.adapters.transcript import TranscriptSource
        self.write([item('function_call', name='exec_command', call_id='same', arguments='{"cmd":"git remote -v"}'),
                    item('function_call', name='exec_command', call_id='same', arguments='{"cmd":"echo other"}')])
        with self.assertRaisesRegex(TranscriptFailure, 'duplicated'):
            TranscriptSource().load(str(self.path))

    def test_codex_dispatch_writes_readable_pending_and_indexes_only_on_approve(self):
        from dataclasses import replace
        import test_kb_note_bundle as fixtures
        from kb.adapters.markdown import render_note
        from kb.app.outcomes import Approved, Pending
        fixture = fixtures.PendingPublicationTest()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.write([item('message', role='user', content=[{'type': 'input_text', 'text': 'Sessão sem entidades.'}])])
        note_file = Path(self.tmp.name) / 'note.md'
        note_file.write_text(render_note(fixture.note))
        args = SimpleNamespace(command='write', transcript=str(self.path), path=fixture.path,
                               file=str(note_file), reason='', approved_degraded=False,
                               description=['work/projeto=O projeto de exemplo.', 'work/projeto/notas=As notas do projeto.'])
        result = dispatch(args, fixture.context)
        self.assertIsInstance(result, Pending)
        self.assertEqual(fixture.path, result.pending_path)
        self.assertEqual('pending', fixture.store.read(result.pending_path).frontmatter.status.value)
        self.assertEqual([], fixture.index.notes)
        args.command = 'approve'
        self.assertIsInstance(dispatch(args, fixture.context), Approved)
        self.assertTrue(fixture.index.notes)
        updated = replace(fixture.note, frontmatter=replace(fixture.note.frontmatter, title='Referência revisada do projeto'))
        note_file.write_text(render_note(updated))
        args.command, args.reason = 'write', 'A referência mudou para explicar a nova decisão do projeto.'
        prior_count = len(fixture.index.notes)
        result = dispatch(args, fixture.context)
        self.assertIsInstance(result, Pending)
        self.assertEqual(fixture.path.replace('/modelo.md', '/.pending/modelo.md'), result.pending_path)
        self.assertEqual('pending', fixture.store.read(result.pending_path).frontmatter.status.value)
        self.assertEqual('Referência revisada do projeto', fixture.store.read(result.pending_path).frontmatter.title)
        self.assertEqual('Referência do projeto', fixture.store.read(fixture.path).frontmatter.title)
        self.assertEqual(prior_count, len(fixture.index.notes))


if __name__ == '__main__':
    unittest.main()
