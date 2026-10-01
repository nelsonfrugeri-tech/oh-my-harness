from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from kb.adapters.markdown import parse_note, render_note
from kb.note.model import Section
from test_kb_note_domain import sample_note


class MarkdownBoundaryTest(unittest.TestCase):
    def test_roundtrip_preserves_plan_headings_and_separators_inside_fences(self):
        note = sample_note()
        for fence in ('```', '~~~'):
            text = f'A decisão está no plano.\n\n{fence}markdown\n## Objective\n\n---\n\nO plano.\n{fence}'
            candidate = replace(note, sections=(Section('Facts', text), note.sections[1]))
            parsed = parse_note(render_note(candidate), candidate.path.relative_path)
            self.assertEqual(candidate, parsed)

    def test_duplicate_yaml_field_is_rejected(self):
        note = sample_note()
        rendered = render_note(note).replace('version: 1', 'version: 1\nversion: 2')
        with self.assertRaisesRegex(ValueError, 'distinct'):
            parse_note(rendered, note.path.relative_path)

    def test_non_string_provenance_is_rejected_at_boundary(self):
        note = sample_note()
        rendered = render_note(note).replace('session_id: session-1', 'session_id: 123')
        with self.assertRaisesRegex(ValueError, 'invalid type'):
            parse_note(rendered, note.path.relative_path)

    def test_unquoted_rfc3339_is_parsed_as_contract_string(self):
        note = sample_note()
        rendered = render_note(note).replace("'2026-10-01T10:00:00Z'", '2026-10-01T10:00:00Z')
        self.assertEqual(note, parse_note(rendered, note.path.relative_path))
