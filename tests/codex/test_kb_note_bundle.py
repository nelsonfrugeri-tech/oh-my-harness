from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))
from test_kb_note_domain import MACHINE, sample_note


class FixedClock:
    def now(self):
        return '2026-10-02T10:00:00Z'


class RecordingIndex:
    def __init__(self):
        self.notes = []
        self.payloads = []

    def upsert(self, note, vector):
        self.notes.append(note)

    def set_payload(self, point_id, fields):
        self.payloads.append((point_id, fields))


class FixedEmbedder:
    def embed(self, text):
        return (1.0,)


class PendingPublicationTest(unittest.TestCase):
    def setUp(self):
        from kb.adapters.filesystem import FileNoteStore
        from kb.app.context import Context
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = FileNoteStore(Path(self.directory.name))
        self.index = RecordingIndex()
        self.context = Context(self.store, FixedClock(), MACHINE, self.index, FixedEmbedder())
        self.note = sample_note()
        self.path = self.note.path.relative_path

    def propose(self, note=None, reason=''):
        from kb.app.write import write
        return write(note or self.note, self.context, transcript='Sessão sem entidades.',
                     reason=reason, descriptions=(('work/projeto', 'O projeto de exemplo.'),
                                                 ('work/projeto/notas', 'As notas do projeto.')))

    def test_pending_has_no_index_links_or_search_point(self):
        from kb.app.catalog import published
        from kb.app.outcomes import Pending
        self.assertIsInstance(self.propose(), Pending)
        self.assertEqual('pending', self.store.read(self.path).frontmatter.status.value)
        self.assertEqual((), published(self.store))
        self.assertFalse(self.store.exists('work/projeto/index.md'))
        self.assertEqual([], self.index.notes)

    def test_approval_publishes_index_and_update_freezes_only_on_approval(self):
        from kb.app.approve import approve
        from kb.app.outcomes import Approved, Pending
        self.assertIsInstance(self.propose(), Pending)
        result = approve(self.path, self.context, transcript='Sessão sem entidades.')
        self.assertIsInstance(result, Approved)
        self.assertTrue(self.store.exists('work/projeto/index.md'))
        replacement = replace(self.note, frontmatter=replace(self.note.frontmatter,
                              title='Referência revisada do projeto'))
        reason = 'A referência mudou para explicar a nova decisão do projeto.'
        self.assertIsInstance(self.propose(replacement, reason), Pending)
        self.assertEqual(1, self.store.read(self.path).frontmatter.version)
        self.assertFalse(any('/.history/' in p for p in self.store.paths()))
        self.assertIsInstance(approve(self.path, self.context, transcript='Sessão.'), Approved)
        active = self.store.read(self.path)
        self.assertEqual(2, active.frontmatter.version)
        frozen = [p for p in self.store.paths() if '/.history/' in p]
        self.assertEqual(1, len(frozen))
        self.assertEqual(self.note.frontmatter.created_at, active.frontmatter.created_at)
        self.assertEqual(2, approve(self.path, self.context, transcript='Sessão.').version)

    def test_update_without_reason_writes_nothing(self):
        from kb.app.approve import approve
        from kb.app.outcomes import Rejected
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        before = {p: self.store.read_text(p) for p in self.store.paths()}
        self.assertIsInstance(self.propose(), Rejected)
        self.assertEqual(before, {p: self.store.read_text(p) for p in self.store.paths()})

    def test_failure_after_promotion_resumes_without_duplicate_history(self):
        from kb.app.approve import approve
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        replacement = replace(self.note, frontmatter=replace(self.note.frontmatter,
                              title='Referência revisada do projeto'))
        self.propose(replacement, 'A referência mudou para explicar a nova decisão do projeto.')
        original = self.index.upsert
        def fail(note, vector):
            raise RuntimeError('simulated outage')
        self.index.upsert = fail
        with self.assertRaises(RuntimeError):
            approve(self.path, self.context, transcript='Sessão.')
        self.assertEqual(2, self.store.read(self.path).frontmatter.version)
        self.index.upsert = original
        self.assertEqual(2, approve(self.path, self.context, transcript='Sessão.').version)
        self.assertEqual(1, len([p for p in self.store.paths() if '/.history/' in p]))

    def test_rejection_removes_only_pending_revision(self):
        from kb.app.approve import approve
        from kb.app.reject import reject
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        before = self.store.read_text(self.path)
        self.propose(reason='O contexto exige uma revisão dos fatos do projeto.')
        reject(self.path, self.context)
        self.assertEqual(before, self.store.read_text(self.path))
        self.assertFalse(any('/.history/' in p for p in self.store.paths()))

    def test_proposal_without_required_entity_descriptions_is_rejected(self):
        from kb.app.write import write
        from kb.app.outcomes import Rejected
        result = write(self.note, self.context, transcript='Sessão.')
        self.assertIsInstance(result, Rejected)
        self.assertEqual((), self.store.paths())

    def test_new_proposal_cannot_overwrite_unfinished_approval(self):
        from kb.app.approve import approve
        from kb.app.outcomes import Rejected
        self.propose()
        original = self.index.upsert
        def fail(note, vector):
            raise RuntimeError('simulated outage')
        self.index.upsert = fail
        with self.assertRaises(RuntimeError):
            approve(self.path, self.context, transcript='Sessão.')
        replacement = replace(self.note, frontmatter=replace(self.note.frontmatter,
                              title='Outra proposta ainda não aprovada'))
        self.assertIsInstance(self.propose(replacement), Rejected)
        self.index.upsert = original
        self.assertEqual(1, approve(self.path, self.context, transcript='Sessão.').version)

    def test_rejecting_new_proposal_leaves_no_orphan_directories(self):
        from kb.app.check import check
        from kb.app.reject import reject
        self.propose()
        reject(self.path, self.context)
        self.assertEqual((), check(self.context).errors)

    def test_check_rejects_an_orphan_index_entry(self):
        from kb.app.approve import approve
        from kb.app.check import check
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        path = 'work/projeto/index.md'
        self.store.write_text(path, self.store.read_text(path) + '- [ghost/](ghost/) — Entidade ausente.\n')
        self.assertTrue(any('orphan index' in error for error in check(self.context).errors))

    def test_duplicate_uuid_at_another_path_is_rejected(self):
        from kb.app.outcomes import Rejected
        self.propose()
        duplicate = replace(self.note, path=replace(self.note.path, name='duplicate'))
        self.assertIsInstance(self.propose(duplicate), Rejected)

    def test_pending_age_starts_when_proposed(self):
        from kb.app.check import check
        self.propose()
        self.assertEqual(0, check(self.context).pending[0].age_seconds)

    def test_rejection_preserves_preexisting_entity_directory(self):
        from kb.app.reject import reject
        from kb.app.check import check
        Path(self.directory.name, 'work/projeto/notas').mkdir(parents=True)
        self.store.write_text('work/index.md', '- [projeto/](projeto/) — O projeto.\n')
        self.store.write_text('work/projeto/index.md', '- [notas/](notas/) — As notas.\n')
        self.propose()
        reject(self.path, self.context)
        self.assertTrue(Path(self.directory.name, 'work/projeto/notas').is_dir())
        self.assertEqual((), check(self.context).errors)

    def test_parent_child_graph_and_pending_update_remain_consistent(self):
        from kb.app.approve import approve
        from kb.app.check import check
        from uuid import uuid4
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        child = replace(self.note, path=replace(self.note.path, name='filha'),
                        frontmatter=replace(self.note.frontmatter, id=str(uuid4()), parent=self.path))
        self.propose(child)
        approve(child.path.relative_path, self.context, transcript='Sessão.')
        self.assertEqual((), check(self.context).errors)
        self.propose(child, 'A revisão mantém a relação com a nota original do projeto.')
        self.assertEqual((), check(self.context).errors)
        parent = self.store.read(self.path)
        self.store.write(replace(parent, frontmatter=replace(parent.frontmatter, children=())))
        self.assertTrue(any('inverse parent' in error for error in check(self.context).errors))

    def test_moving_then_rejecting_preserves_directory_ownership(self):
        from kb.app.move import move
        from kb.app.reject import reject
        from kb.app.check import check
        self.propose()
        target = replace(self.note.path, name='renomeada')
        move(self.path, target, self.context)
        reject(target.relative_path, self.context)
        self.assertEqual((), check(self.context).errors)

    def test_check_validates_frozen_versions_outside_backup(self):
        from kb.app.approve import approve
        from kb.app.check import check
        self.propose()
        approve(self.path, self.context, transcript='Sessão.')
        changed = replace(self.note, frontmatter=replace(self.note.frontmatter,
                          title='Referência revisada do projeto'))
        self.propose(changed, reason='A referência mudou para explicar a nova decisão do projeto.')
        approve(self.path, self.context, transcript='Sessão.')
        self.assertEqual((), check(self.context).errors)
        frozen = next(p for p in self.store.paths() if '/.history/' in p)
        self.store.write_text(frozen, self.store.read_text(frozen).replace('status: superseded', 'status: invalid'))
        self.assertTrue(check(self.context).errors)
