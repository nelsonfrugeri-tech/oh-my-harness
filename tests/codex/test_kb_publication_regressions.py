import unittest
import os
from dataclasses import replace
from uuid import UUID

import test_kb_note_bundle as fixtures
from kb.app.approve import approve
from kb.app.catalog import published
from kb.app.check import check
from kb.app.outcomes import Approved, Pending, Rejected


class PublicationRegressions(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PendingPublicationTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store = self.fixture.store
        self.context = self.fixture.context

    def publish(self, name='modelo', number=1):
        note = replace(self.fixture.note, path=replace(self.fixture.note.path, name=name),
                       frontmatter=replace(self.fixture.note.frontmatter,
                                           id=str(UUID(int=UUID('34e7a6fe-fc09-4b5d-af42-4b6f0828b350').int + number))))
        self.assertIsInstance(self.fixture.propose(note), Pending)
        self.assertIsInstance(approve(note.path.relative_path, self.context, transcript='Sessão.'), Approved)
        return self.store.read(note.path.relative_path)

    def propose_update(self, note):
        return self.fixture.propose(note, 'O contexto mudou para documentar os fatos do projeto.')

    def test_approved_is_a_valid_note_name_and_history_is_preserved(self):
        note = self.publish('approved')
        updated = replace(note, frontmatter=replace(note.frontmatter, title='Referência revisada do projeto'))
        self.assertIsInstance(self.propose_update(updated), Pending)
        result = approve(note.path.relative_path, self.context, transcript='Sessão.')
        self.assertEqual(2, result.version)
        self.assertEqual('active', self.store.read(note.path.relative_path).frontmatter.status.value)
        self.assertEqual(1, len([p for p in self.store.paths() if '/.history/' in p]))
        self.assertEqual(1, len(published(self.store)))
        self.assertEqual(2, check(self.context).notes)

    def test_link_change_waits_for_approval_without_a_new_version(self):
        first, other = self.publish(), self.publish('outra', 2)
        path = first.path.relative_path
        changed = replace(first, frontmatter=replace(first.frontmatter, related=(other.path.relative_path,)))
        self.assertIsInstance(self.propose_update(changed), Pending)
        self.assertEqual((), self.store.read(path).frontmatter.related)
        self.assertEqual(1, approve(path, self.context, transcript='Sessão.').version)
        self.assertEqual(first.frontmatter.updated_at, self.store.read(path).frontmatter.updated_at)
        self.assertEqual((path,), self.store.read(other.path.relative_path).frontmatter.related)
        self.assertFalse(any('/.history/' in p for p in self.store.paths()))

    def test_identical_proposal_does_not_freeze(self):
        note = self.publish()
        self.propose_update(note)
        self.assertEqual(1, approve(note.path.relative_path, self.context, transcript='Sessão.').version)
        self.assertFalse(any('/.history/' in p for p in self.store.paths()))

    def test_unrelated_notes_do_not_receive_remote_writes(self):
        self.publish()
        self.fixture.index.notes.clear()
        self.fixture.index.payloads.clear()
        self.publish('outra', 2)
        self.assertEqual(1, len(self.fixture.index.notes))
        self.assertEqual([], self.fixture.index.payloads)

    def test_conflict_copy_and_trash_do_not_block_writes(self):
        note = self.publish()
        self.store.write_text(note.path.relative_path.replace('modelo.md', 'modelo 2.md'), 'conflict')
        self.store.write_text('.trash/old.md', 'trash')
        self.assertIsInstance(self.propose_update(note), Pending)
        self.assertTrue(any('modelo 2.md' in issue for issue in check(self.context).errors))

    def test_reason_is_normalized_before_pending(self):
        note = self.publish()
        self.assertIsInstance(self.fixture.propose(note, ' ' * 20 + 'Razão válida.'), Rejected)

    def test_crash_before_history_blocks_reproposal_and_resumes(self):
        note = self.publish()
        path = note.path.relative_path
        updated = replace(note, frontmatter=replace(note.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(updated)
        original = self.store.write
        def fail_history(value, destination=None):
            if destination and '/.history/' in destination:
                raise RuntimeError('crash before history')
            original(value, destination)
        self.store.write = fail_history
        with self.assertRaisesRegex(RuntimeError, 'crash before history'):
            approve(path, self.context, transcript='Sessão.')
        self.store.write = original
        self.assertIsInstance(self.propose_update(updated), Rejected)
        self.assertEqual(2, approve(path, self.context, transcript='Sessão.').version)
        self.assertEqual(1, len([p for p in self.store.paths() if '/.history/' in p]))

    def test_crash_during_cleanup_can_resume(self):
        note = self.publish()
        path = note.path.relative_path
        updated = replace(note, frontmatter=replace(note.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(updated)
        original = self.store.remove
        def fail_metadata(target):
            if target.endswith('metadata.json'):
                raise RuntimeError('crash at metadata cleanup')
            original(target)
        self.store.remove = fail_metadata
        with self.assertRaisesRegex(RuntimeError, 'crash at metadata cleanup'):
            approve(path, self.context, transcript='Sessão.')
        self.store.remove = original
        self.assertEqual(2, approve(path, self.context, transcript='Sessão.').version)
        self.assertFalse(any('/.pending/' in p for p in self.store.files()))

    def test_missing_approval_is_rejected(self):
        self.assertIsInstance(approve('work/projeto/absent/absent.md', self.context,
                                      transcript='Sessão.'), Rejected)

    def test_repair_failure_after_disk_write_is_replayed(self):
        parent = self.publish()
        child = replace(self.fixture.note, path=replace(self.fixture.note.path, name='filha'),
                        frontmatter=replace(self.fixture.note.frontmatter, id=str(UUID(int=2, version=4)),
                                            parent=parent.path.relative_path))
        self.assertIsInstance(self.fixture.propose(child), Pending)
        original = self.fixture.index.upsert
        def fail_neighbor(note, vector):
            if note.path == parent.path:
                raise RuntimeError('neighbor unavailable')
            original(note, vector)
        self.fixture.index.upsert = fail_neighbor
        with self.assertRaisesRegex(RuntimeError, 'neighbor unavailable'):
            approve(child.path.relative_path, self.context, transcript='Sessão.')
        self.assertTrue(any(note.path == child.path for note in self.fixture.index.notes))
        self.assertTrue(self.store.exists('.repair.json'))
        self.assertEqual((child.path.relative_path,), self.store.read(parent.path.relative_path).frontmatter.children)
        self.fixture.index.upsert = original
        approve(child.path.relative_path, self.context, transcript='Sessão.')
        self.assertFalse(self.store.exists('.repair.json'))
        self.assertEqual((child.path.relative_path,), self.fixture.index.notes[-2].frontmatter.children)
        self.assertTrue(all(note.frontmatter.status.value == 'active' for note in self.fixture.index.notes))

    def test_crash_after_metadata_removal_cleans_orphan_receipt(self):
        note = self.publish()
        path = note.path.relative_path
        updated = replace(note, frontmatter=replace(note.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(updated)
        original = self.store.remove
        def fail_after_metadata(target):
            original(target)
            if target.endswith('metadata.json'):
                raise RuntimeError('metadata removed')
        self.store.remove = fail_after_metadata
        with self.assertRaisesRegex(RuntimeError, 'metadata removed'):
            approve(path, self.context, transcript='Sessão.')
        self.store.remove = original
        self.assertEqual(2, approve(path, self.context, transcript='Sessão.').version)
        self.assertFalse(any('/.pending/' in p for p in self.store.files()))
        self.assertIsInstance(self.propose_update(self.store.read(path)), Pending)

    def test_crash_after_history_is_resumable(self):
        note = self.publish()
        path = note.path.relative_path
        updated = replace(note, frontmatter=replace(note.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(updated)
        original = self.store.write
        def fail_after_history(value, destination=None):
            original(value, destination)
            if destination and '/.history/' in destination:
                raise RuntimeError('history written')
        self.store.write = fail_after_history
        with self.assertRaisesRegex(RuntimeError, 'history written'):
            approve(path, self.context, transcript='Sessão.')
        self.store.write = original
        self.assertIsInstance(self.propose_update(updated), Rejected)
        self.assertEqual(2, approve(path, self.context, transcript='Sessão.').version)
        self.assertEqual(1, len([p for p in self.store.paths() if '/.history/' in p]))

    def test_approved_note_uuid_cannot_be_reused(self):
        note = self.publish('approved')
        duplicate = replace(note, path=replace(note.path, name='outra'))
        self.assertIsInstance(self.fixture.propose(duplicate), Rejected)

    @unittest.skipUnless(os.environ.get('OMH_KB_TEST_QDRANT_URL'),
                         'isolated Qdrant endpoint not provided')
    def test_qdrant_missing_neighbor_and_interrupted_repair_are_recoverable(self):
        from uuid import uuid4
        from qdrant_client import models
        from kb.adapters.qdrant import QdrantIndex
        from kb.search.model import Embedding, SparseWeight
        from kb.search.payload import point_id
        collection = 'publication-regression-' + uuid4().hex
        index = QdrantIndex(os.environ['OMH_KB_TEST_QDRANT_URL'], collection=collection)
        self.addCleanup(index.client.close)
        index.ensure_collection(dimension=3)
        self.addCleanup(index.client.delete_collection, collection)
        class Embedder:
            def embed(self, text):
                return Embedding((1.0, 0.0, 0.0), (SparseWeight(1, 1.0),))
        self.context = replace(self.context, index=index, embedder=Embedder())
        self.fixture.context = self.context
        parent = self.publish()
        parent_id = point_id(parent.frontmatter.id, 1)
        index.client.delete(collection, models.PointIdsList(points=[parent_id]), wait=True)
        child = replace(self.fixture.note, path=replace(self.fixture.note.path, name='filha'),
                        frontmatter=replace(self.fixture.note.frontmatter, id=str(UUID(int=2, version=4)),
                                            parent=parent.path.relative_path))
        self.fixture.propose(child)
        original = index.upsert
        def fail_neighbor(note, vector):
            if note.path == parent.path:
                raise RuntimeError('interrupted missing-neighbor repair')
            original(note, vector)
        index.upsert = fail_neighbor
        with self.assertRaisesRegex(RuntimeError, 'interrupted missing-neighbor repair'):
            approve(child.path.relative_path, self.context, transcript='Sessão.')
        child_id = point_id(child.frontmatter.id, 1)
        self.assertEqual('active', index.client.retrieve(collection, [child_id])[0].payload['status'])
        self.assertEqual([], index.client.retrieve(collection, [parent_id]))
        index.upsert = original
        self.assertIsInstance(approve(child.path.relative_path, self.context, transcript='Sessão.'), Approved)
        self.assertEqual([child.path.relative_path], index.client.retrieve(collection, [parent_id])[0].payload['children'])
        self.assertFalse(self.store.exists('.repair.json'))

    def test_parent_change_and_removal_preserve_version_and_repair_both_parents(self):
        first, second, child = self.publish('primeira'), self.publish('segunda', 2), self.publish('filha', 3)
        path = child.path.relative_path
        for parent in (first.path.relative_path, second.path.relative_path, None):
            candidate = replace(self.store.read(path), frontmatter=replace(
                self.store.read(path).frontmatter, parent=parent))
            self.assertIsInstance(self.propose_update(candidate), Pending)
            self.assertEqual(1, approve(path, self.context, transcript='Sessão.').version)
            current = self.store.read(path)
            self.assertEqual(child.frontmatter.updated_at, current.frontmatter.updated_at)
            for ancestor in (first, second):
                expected = (path,) if ancestor.path.relative_path == parent else ()
                self.assertEqual(expected, self.store.read(ancestor.path.relative_path).frontmatter.children)
        self.assertFalse(any('/.history/' in p for p in self.store.paths()))

    def test_another_publication_waits_until_the_interrupted_one_finishes(self):
        first, other = self.publish(), self.publish('outra', 2)
        changed = replace(first, frontmatter=replace(first.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(changed)
        original = self.fixture.index.upsert
        def fail(note, vector):
            raise RuntimeError('publication interrupted')
        self.fixture.index.upsert = fail
        with self.assertRaisesRegex(RuntimeError, 'publication interrupted'):
            approve(first.path.relative_path, self.context, transcript='Sessão.')
        self.fixture.index.upsert = original
        related = replace(other, frontmatter=replace(other.frontmatter, related=(first.path.relative_path,)))
        self.assertIsInstance(self.propose_update(related), Pending)
        self.assertIsInstance(approve(other.path.relative_path, self.context, transcript='Sessão.'), Rejected)
        approve(first.path.relative_path, self.context, transcript='Sessão.')
        self.assertIsInstance(approve(other.path.relative_path, self.context, transcript='Sessão.'), Approved)
        self.assertEqual((other.path.relative_path,), self.store.read(first.path.relative_path).frontmatter.related)

    def test_external_repair_cannot_change_an_unfinished_publication(self):
        from kb.app.repair import repair
        first, other = self.publish(), self.publish('outra', 2)
        changed = replace(first, frontmatter=replace(first.frontmatter, title='Referência revisada do projeto'))
        self.propose_update(changed)
        original = self.fixture.index.upsert
        def fail(note, vector):
            raise RuntimeError('publication interrupted')
        self.fixture.index.upsert = fail
        with self.assertRaisesRegex(RuntimeError, 'publication interrupted'):
            approve(first.path.relative_path, self.context, transcript='Sessão.')
        self.fixture.index.upsert = original
        for original_source in (first, other):
            source = self.store.read(original_source.path.relative_path)
            target = other if original_source == first else first
            candidate = replace(source, frontmatter=replace(source.frontmatter,
                                related=(target.path.relative_path,)))
            before = {path: self.store.read_text(path) for path in self.store.files()}
            with self.assertRaisesRegex(RuntimeError, 'Resume unfinished approval'):
                repair(self.context, candidate, ())
            self.assertEqual(before, {path: self.store.read_text(path) for path in self.store.files()})
        self.assertIsInstance(approve(first.path.relative_path, self.context, transcript='Sessão.'), Approved)
