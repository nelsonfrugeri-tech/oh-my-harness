from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))

from kb.entities.tables import TABLE_HEADERS
from kb.note.template import render_reference, render_template
from kb.note.vocabulary import NoteType


class NoteTemplateTests(unittest.TestCase):
    def test_reference_is_generated_from_schema(self):
        reference = ROOT / 'core/skills/kb-write/references/note-template.md'
        self.assertEqual(reference.read_text(), render_reference())

    def test_each_template_has_exact_required_order_and_conditionals(self):
        expected = {
            NoteType.DECISION: ('Decision', 'Context', 'Options', 'Consequences', 'How to apply'),
            NoteType.EVENT: ('What happened', 'Timeline', 'Outcome'),
            NoteType.PROCEDURE: ('Goal', 'When to use', 'Prerequisites', 'Steps', 'Verification'),
            NoteType.REFERENCE: ('Facts', 'Scope'),
            NoteType.CONVERSATION: ('Participants', 'Key facts', 'Outcome'),
        }
        for kind, headings in expected.items():
            with self.subTest(kind=kind):
                template = render_template(kind)
                positions = [template.index('## ' + name + '\n') for name in headings]
                self.assertEqual(positions, sorted(positions))
                for conditional in ('Entities', 'Dates', 'Figures'):
                    self.assertIn('## ' + conditional + '\n', template)
                for entity in ('people', 'companies', 'products', 'brands', 'roles', 'projects',
                               'apps', 'urls', 'repos', 'paths', 'documents', 'emails', 'names'):
                    self.assertIn('  ' + entity + ': []', template)
                self.assertEqual('occurred_at:' in template, kind is NoteType.EVENT)

    def test_template_table_headers_match_the_entity_parser(self):
        template = render_template(NoteType.EVENT)
        for heading, columns in TABLE_HEADERS.items():
            body = template.split('## ' + heading + '\n', 1)[1]
            header = next(line for line in body.splitlines() if line.startswith('|'))
            self.assertEqual(columns, tuple(cell.strip() for cell in header.strip('|').split('|')))

    def test_identity_and_superseded_fields_are_not_in_new_note_template(self):
        template = render_template(NoteType.REFERENCE)
        self.assertNotIn('repository_path:', template)
        self.assertNotIn('superseded_reason:', template)
        self.assertIn('status: pending', template)


if __name__ == '__main__':
    unittest.main()
