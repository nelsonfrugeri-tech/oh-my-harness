"""Regression cases from the first external note-model review."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.transcript_claude import ClaudeTranscriptSource
from kb.app.harvest import Harvested, Unavailable, harvest
from kb.cli import main
from kb.note.language import is_pt_br


class AdapterRegressionTests(unittest.TestCase):
    def test_administrative_records_do_not_disable_message_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            records = [{'type': kind, 'text': 'https://metadata.invalid'} for kind in
                       ('attachment', 'mode', 'ai-title', 'future-administrative-record')]
            records.append({'type': 'user', 'message': {'content': 'Leia https://example.org/docs'}})
            path.write_text('\n'.join(json.dumps(record) for record in records))
            adapter = ClaudeTranscriptSource()
            result = harvest(adapter, str(path))
            self.assertIsInstance(result, Harvested)
            self.assertEqual(['https://example.org/docs'], [candidate.value for candidate in result.candidates])
            self.assertNotIn('metadata.invalid', adapter.load(str(path)))

    def test_binary_tool_artifacts_do_not_disable_text_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps({'type': 'user', 'message': {'content': 'Leia https://example.org/docs'}}))
            artifacts = Path(directory) / 'session/tool-results'
            artifacts.mkdir(parents=True)
            (artifacts / 'report.pdf').write_bytes(b'%PDF-1.7\xff\xfe')
            result = harvest(ClaudeTranscriptSource(), str(path))
            self.assertIsInstance(result, Harvested)
            self.assertEqual(['https://example.org/docs'], [candidate.value for candidate in result.candidates])

    def test_invalid_utf8_text_artifact_reports_safe_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps({'type': 'user', 'message': {'content': 'A sessão principal.'}}))
            artifacts = Path(directory) / 'session/tool-results'
            artifacts.mkdir(parents=True)
            (artifacts / 'report.txt').write_bytes(b'private-fixture\xff\xfe')
            result = harvest(ClaudeTranscriptSource(), str(path))
            self.assertIsInstance(result, Unavailable)
            self.assertIn('UTF-8', result.reason)
            self.assertNotIn('private-fixture', result.reason)

    def test_unsupported_root_is_not_validated_by_child_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps({'type': 'unknown'}))
            children = Path(directory) / 'session/subagents'
            children.mkdir(parents=True)
            (children / 'agent.jsonl').write_text(json.dumps({'type': 'user', 'message': {'content': 'A sessão filha.'}}))
            self.assertIsInstance(harvest(ClaudeTranscriptSource(), str(path)), Unavailable)

    def test_unknown_only_transcript_is_unavailable_with_safe_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps({'type': 'unknown', 'secret': 'private-fixture'}))
            result = harvest(ClaudeTranscriptSource(), str(path))
            self.assertIsInstance(result, Unavailable)
            self.assertIn('supported message', result.reason)
            self.assertNotIn('private-fixture', result.reason)

    def test_portuguese_fragments_and_technical_titles(self):
        for text in ('Deploy canário Kubernetes', 'Rollback Argo CD staging',
                     'Reunião OKRs data platform Q4', 'Proposta Aurora recrutadora Ana', 'Pipeline falhou.'):
            with self.subTest(text=text):
                self.assertTrue(is_pt_br(text))

    def test_short_english_and_english_table_prose_are_rejected(self):
        for text in ('It failed.', 'Deployment failed.', 'The recruiter', 'She accepted.',
                     'A pessoa foi contratada.\n\n| Nome | Papel |\n|---|---|\n'
                     '| ana | She is the recruiter who sent the offer |'):
            with self.subTest(text=text):
                self.assertFalse(is_pt_br(text))

    def test_missing_machine_identity_id_is_environment_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = root / 'identity.json'
            identity.write_text('{}')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['check', '--root', directory, '--identity', str(identity), '--json'])
            self.assertEqual(4, code)
            self.assertEqual('Degraded', json.loads(output.getvalue())['status'])
