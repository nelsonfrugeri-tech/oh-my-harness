from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'core/skills/kb-write/scripts'))

from kb.note.graph import derive_children, mirror_related
from kb.note.index_page import IndexEntry, missing_entries, render_index
from kb.note.language import is_pt_br
from kb.note.model import Entities, Frontmatter, Generated, Note, NotePath, Section
from kb.note.naming import DirectoryKind, check_name, classify_dir
from kb.note.report import ValidationContext, ValidationReport
from kb.note.validation import validate
from kb.note.versioning import freeze, needs_new_version
from kb.note.vocabulary import Harness, NoteType, Scope, Status

MACHINE = '11a1ac55-d102-4e8c-9aaf-4137ee16aef3'
PROSE = 'A nota apresenta o contexto da decisão e os motivos para a mudança no projeto.'


def sample_note() -> Note:
    fm = Frontmatter(
        id='34e7a6fe-fc09-4b5d-af42-4b6f0828b357', type=NoteType.REFERENCE,
        title='Referência do projeto', description=PROSE * 2, summary=PROSE * 9,
        tags=('projeto',), status=Status.ACTIVE, version=1,
        created_at='2026-10-01T10:00:00Z', updated_at='2026-10-01T10:00:00Z',
        generated=Generated(Harness.CODEX, None, 'session-1', '/tmp/project', MACHINE))
    return Note(NotePath(Scope.WORK, 'projeto', ('notas',), 'modelo'), fm,
                (Section('Facts', PROSE), Section('Scope', PROSE)))


class NoteValidationTests(unittest.TestCase):
    def test_valid_reference_is_accepted_and_frozen(self):
        note = sample_note()
        self.assertTrue(validate(note, ValidationContext(MACHINE)).valid)
        with self.assertRaises(FrozenInstanceError):
            note.frontmatter.title = 'changed'

    def test_text_limits_reject_each_boundary_violation(self):
        note = sample_note()
        for field, lengths in (('title', (9, 71)), ('description', (119, 301)),
                               ('summary', (599, 1501))):
            for length in lengths:
                with self.subTest(field=field, length=length):
                    changed = replace(note, frontmatter=replace(note.frontmatter, **{field: 'a' * length}))
                    report = validate(changed, ValidationContext(MACHINE, check_language=False))
                    self.assertIn(field, tuple(issue.field for issue in report.issues))

    def test_invalid_enum_and_event_timestamp_are_rejected(self):
        note = sample_note()
        for fields in ({'type': 'incident'}, {'status': 'unknown'},
                       {'type': NoteType.EVENT}, {'occurred_at': '2026-10-01T10:00:00Z'}):
            with self.subTest(fields=fields):
                changed = replace(note, frontmatter=replace(note.frontmatter, **fields))
                self.assertFalse(validate(changed, ValidationContext(MACHINE)).valid)

    def test_invalid_provenance_uuid_and_time_are_rejected(self):
        note = sample_note()
        for fields in ({'id': 'bad'}, {'version': 0}, {'version': True},
                       {'created_at': '2026-10-02T10:00:00Z'},
                       {'updated_at': '2026-10-01T10:00:00+03:00'},
                       {'generated': replace(note.frontmatter.generated, machine_id='other')},
                       {'generated': replace(note.frontmatter.generated, cwd='relative')}):
            with self.subTest(fields=fields):
                self.assertFalse(validate(replace(note, frontmatter=replace(note.frontmatter, **fields)),
                                          ValidationContext(MACHINE)).valid)

    def test_missing_unknown_duplicate_and_reordered_sections_are_rejected(self):
        note = sample_note()
        for sections in ((Section('Facts', PROSE),), tuple(reversed(note.sections)),
                         note.sections + (Section('Unknown', PROSE),),
                         note.sections + (Section('Facts', PROSE),)):
            with self.subTest(sections=sections):
                self.assertFalse(validate(replace(note, sections=sections), ValidationContext(MACHINE)).valid)

    def test_fenced_plan_headings_and_delimiters_are_content(self):
        note = sample_note()
        for fence in ('```', '~~~'):
            with self.subTest(fence=fence):
                text = PROSE + '\n\n' + fence + 'markdown\n## Objective\n---\nA decisão do projeto.\n' + fence
                changed = replace(note, sections=(Section('Facts', text), note.sections[1]))
                self.assertTrue(validate(changed, ValidationContext(MACHINE)).valid)
        changed = replace(note, sections=(Section('Facts', PROSE + '\n## Objective\n' + PROSE), note.sections[1]))
        self.assertFalse(validate(changed, ValidationContext(MACHINE)).valid)

    def test_optional_sections_may_precede_required_sections(self):
        note = sample_note()
        changed = replace(note, sections=(Section('Caveats', PROSE),) + note.sections)
        self.assertTrue(validate(changed, ValidationContext(MACHINE)).valid)

    def test_identity_fields_only_belong_to_domain_identity(self):
        note = sample_note()
        fm = replace(note.frontmatter, repository_path='/tmp/project', remote_url='https://example.com/repo',
                     default_branch='main')
        self.assertFalse(validate(replace(note, frontmatter=fm), ValidationContext(MACHINE)).valid)
        identity = replace(note, path=NotePath(Scope.WORK, 'projeto', (), 'identity'), frontmatter=fm)
        self.assertTrue(validate(identity, ValidationContext(MACHINE)).valid)

    def test_code_identity_allows_redacted_remote_but_requires_path_and_branch(self):
        note = sample_note()
        identity = replace(note, path=NotePath(Scope.WORK, 'projeto', (), 'identity'),
                           frontmatter=replace(note.frontmatter, repository_path='/tmp/project',
                                               remote_url=None, default_branch='main'))
        self.assertTrue(validate(identity, ValidationContext(MACHINE)).valid)
        for changes in ({'repository_path': None}, {'default_branch': None}, {'remote_url': ''}):
            with self.subTest(changes=changes):
                changed = replace(identity, frontmatter=replace(identity.frontmatter, **changes))
                self.assertFalse(validate(changed, ValidationContext(MACHINE)).valid)

    def test_conditional_entities_section_is_required(self):
        note = sample_note()
        changed = replace(note, frontmatter=replace(note.frontmatter, entities=Entities(people=('ana',))))
        self.assertIn('sections', tuple(i.field for i in validate(changed, ValidationContext(MACHINE)).issues))


    def test_decision_requires_how_to_apply(self):
        note = sample_note()
        decision = replace(note, frontmatter=replace(note.frontmatter, type=NoteType.DECISION),
                           sections=tuple(Section(name, PROSE) for name in
                                          ('Decision', 'Context', 'Options', 'Consequences')))
        self.assertFalse(validate(decision, ValidationContext(MACHINE)).valid)
        complete = replace(decision, sections=decision.sections + (Section('How to apply', PROSE),))
        self.assertTrue(validate(complete, ValidationContext(MACHINE)).valid)

    def test_event_requires_a_timeline_table(self):
        note = sample_note()
        fm = replace(note.frontmatter, type=NoteType.EVENT, occurred_at='2026-10-01T10:00:00-03:00')
        event = replace(note, frontmatter=fm, sections=(Section('What happened', PROSE),
                        Section('Timeline', PROSE), Section('Outcome', PROSE)))
        self.assertFalse(validate(event, ValidationContext(MACHINE)).valid)
        table = ('| Quando | Quem | O quê | Como | Evidência |\n'
                 '| --- | --- | --- | --- | --- |\n'
                 '| 2026-10-01T10:00:00Z | codex | A mudança | Pela revisão | A sessão |')
        event = replace(event, sections=(event.sections[0], Section('Timeline', table), event.sections[2]))
        self.assertTrue(validate(event, ValidationContext(MACHINE)).valid)

    def test_superseded_metadata_is_conditional(self):
        note = sample_note()
        for fields in ({'status': Status.SUPERSEDED}, {'superseded_reason': PROSE},
                       {'status': Status.SUPERSEDED, 'superseded_at': '2026-09-01T10:00:00Z',
                        'superseded_reason': PROSE}):
            with self.subTest(fields=fields):
                self.assertFalse(validate(replace(note, frontmatter=replace(note.frontmatter, **fields)),
                                          ValidationContext(MACHINE)).valid)

    def test_tags_have_their_own_count_and_kebab_contract(self):
        note = sample_note()
        for tags in ((), ('Repeated',), ('one', 'one'), tuple('abcdefg')):
            self.assertFalse(validate(replace(note, frontmatter=replace(note.frontmatter, tags=tags)),
                                      ValidationContext(MACHINE)).valid)
        tags = ('one-two-three-four',)
        self.assertTrue(validate(replace(note, frontmatter=replace(note.frontmatter, tags=tags)),
                                 ValidationContext(MACHINE)).valid)

    def test_invalid_scope_returns_a_report(self):
        note = replace(sample_note(), path=NotePath('invalid', 'projeto', (), 'modelo'))
        self.assertFalse(validate(note, ValidationContext(MACHINE)).valid)


class NamingAndLanguageTests(unittest.TestCase):
    def test_names_reject_repeated_parent_too_many_words_and_case(self):
        for name in ('codex-adapter', 'one-two-three-four', 'Upper', '../escape', '2026-10-01-note'):
            self.assertTrue(check_name(name, parent='codex'))
        self.assertFalse(check_name('adapter', parent='codex'))

    def test_classification_uses_same_named_file_and_excludes_internal_dirs(self):
        self.assertEqual(classify_dir('model', ('model.md',)), DirectoryKind.NOTE)
        self.assertEqual(classify_dir('model', ('other.md',)), DirectoryKind.ENTITY)
        for name in ('.history', 'backup', '.pending'):
            self.assertEqual(classify_dir(name, ()), DirectoryKind.EXCLUDED)

    def test_outer_fence_keeps_shorter_inner_fences_as_code(self):
        for fence, inner in (('````', '```'), ('~~~~', '~~~'), ('````', '~~~')):
            with self.subTest(fence=fence, inner=inner):
                text = (PROSE + '\n\n' + fence + 'markdown\n' + inner + 'python\n'
                        'The system stores the data and returns the result.\n' + inner + '\n'
                        'The user should not see this code as prose.\n' + fence)
                self.assertTrue(is_pt_br(text))
                self.assertFalse(is_pt_br(text + '\n\nThe system returns the result to the user.'))

    def test_paragraph_language_ignores_code_urls_and_tables(self):
        self.assertTrue(is_pt_br(PROSE + '\n\n```python\nreturn self.value\n```\n\n| Name | Value |\n| --- | --- |'))
        self.assertTrue(is_pt_br('O pipeline de embeddings usa retry e backoff para manter os dados no cache.'))
        self.assertFalse(is_pt_br('The system stores the data and returns the result to the user.'))
        self.assertFalse(is_pt_br(PROSE + '\n\nThe system stores the data and returns it to the user.'))


class VersionAndGraphTests(unittest.TestCase):
    def test_freeze_preserves_old_content_and_advances_current_version(self):
        old = sample_note()
        new = replace(old, sections=(Section('Facts', PROSE * 2), old.sections[1]))
        result = freeze(old, new, at='2026-10-02T10:00:00Z', reason='O contexto foi atualizado após a revisão do projeto.')
        self.assertNotIsInstance(result, ValidationReport)
        self.assertEqual(result.frozen.note.sections, old.sections)
        self.assertEqual(result.frozen.note.frontmatter.status, Status.SUPERSEDED)
        self.assertEqual(result.frozen.relative_path, 'work/projeto/notas/modelo/.history/2026-10-02--v1--modelo.md')
        self.assertEqual(result.current.frontmatter.version, 2)
        self.assertEqual(result.current.frontmatter.id, old.frontmatter.id)
        self.assertEqual(result.current.frontmatter.created_at, old.frontmatter.created_at)

    def test_freeze_refuses_missing_reason(self):
        note = sample_note()
        self.assertIsInstance(freeze(note, note, at='2026-10-02T10:00:00Z', reason=''), ValidationReport)

    def test_navigation_changes_do_not_create_versions(self):
        note = sample_note()
        changed = replace(note, frontmatter=replace(note.frontmatter, children=('other.md',), related=('peer.md',)))
        self.assertFalse(needs_new_version(note, changed))
        self.assertTrue(needs_new_version(note, replace(note, sections=())))

    def test_links_require_existing_active_target_outside_history(self):
        note = sample_note()
        for target in ('missing.md', 'work/projeto/.history/old.md', note.path.relative_path):
            changed = replace(note, frontmatter=replace(note.frontmatter, parent=target))
            self.assertFalse(validate(changed, ValidationContext(MACHINE, (note,))).valid)

    def test_children_and_related_are_derived_in_both_directions(self):
        parent = sample_note()
        child = replace(parent, path=replace(parent.path, name='child'),
                        frontmatter=replace(parent.frontmatter, parent=parent.path.relative_path, related=(parent.path.relative_path,)))
        self.assertEqual(derive_children(parent.path.relative_path, (parent, child)), (child.path.relative_path,))
        mirrored = mirror_related(child, (parent, child))
        self.assertEqual(mirrored[0].frontmatter.related, (child.path.relative_path,))
        removed = mirror_related(replace(child, frontmatter=replace(child.frontmatter, related=())), mirrored)
        self.assertEqual(removed[0].frontmatter.related, ())

    def test_index_missing_entries_and_nested_rendering(self):
        entry = IndexEntry(('notes',), 'Notas do projeto')
        child = IndexEntry(('notes', 'decisions'), 'Decisões do projeto')
        self.assertEqual(missing_entries((('notes',), ('notes', 'decisions')), (entry,)), (('notes', 'decisions'),))
        self.assertIn('  - [decisions/](notes/decisions/) — Decisões do projeto', render_index((child, entry)))


if __name__ == '__main__':
    unittest.main()
