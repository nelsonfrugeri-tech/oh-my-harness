"""Real Qdrant migration with legacy sessions lacking note paths."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'core/skills/kb-write/scripts'))


@unittest.skipUnless(os.environ.get('OMH_KB_TEST_QDRANT_URL'), 'isolated Qdrant endpoint not provided')
class SessionMigrationTests(unittest.TestCase):
    def test_manifest_migration_includes_sessions_preserves_vectors_and_skips_new_sessions(self):
        from uuid import uuid4
        from qdrant_client import models
        from kb.adapters.qdrant import QdrantIndex
        collection = 'review-session-migration-' + uuid4().hex
        index = QdrantIndex(os.environ['OMH_KB_TEST_QDRANT_URL'], collection=collection)
        self.addCleanup(index.client.close)
        index.ensure_collection(dimension=3)
        self.addCleanup(index.client.delete_collection, collection)
        note_id, session_id, newer_id = [str(uuid4()) for _ in range(3)]
        vector = {'dense': [1.0, 0.0, 0.0], 'sparse': models.SparseVector(indices=[1], values=[1.0])}
        index.client.upsert(collection, [
            models.PointStruct(id=note_id, vector=vector, payload={'kind': 'note', 'path': 'work/project/old.md'}),
            models.PointStruct(id=session_id, vector=vector, payload={'kind': 'session',
                               'domain': 'work/projects/project', 'session_id': session_id})], wait=True)
        sources = ('work/project/old.md', f'work/projects/project/sessions/{session_id}.json')
        before = {str(p.id): p.vector for p in index.client.retrieve(collection, [note_id, session_id], with_vectors=True)}
        self._backup_with_resume(index, sources)
        index.client.upsert(collection, [models.PointStruct(id=newer_id, vector=vector,
                            payload={'kind': 'session', 'domain': 'work/projects/project', 'session_id': newer_id})], wait=True)
        self.assertEqual(2, index.mark_legacy('backup/', source_paths=sources))
        records = {str(p.id): p for p in index.client.retrieve(collection, [note_id, session_id, newer_id], with_vectors=True)}
        self.assertEqual(before, {key: records[key].vector for key in before})
        self.assertEqual('backup/work/project/old.md', records[note_id].payload['path'])
        self.assertTrue(records[session_id].payload['legacy'])
        self.assertNotIn('path', records[session_id].payload)
        self.assertNotIn('legacy', records[newer_id].payload)
        # Older records can identify their session by the point ID alone.
        index.client.delete_payload(collection, ['session_id'], [session_id], wait=True)
        self.assertEqual(2, index.mark_legacy('backup/', source_paths=sources))

    def _backup_with_resume(self, index, sources):
        from kb.adapters.backup_filesystem import FileBackupStore
        from kb.adapters.filesystem import FileNoteStore
        from kb.adapters.clock import SystemClock
        from kb.app.backup import backup
        from kb.app.backup_model import Applied, LegacyPending
        from kb.app.context import Context
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        store = FileNoteStore(Path(temporary.name))
        for source in sources:
            store.write_text(source, 'fixture bytes')
        context = Context(store, SystemClock(), 'unused', index)
        storage = FileBackupStore(Path(temporary.name))
        options = dict(apply=True, template='Legado: {legacy_points}', reason='Migração de teste.', plan='plan')
        with patch.object(index, 'mark_legacy', side_effect=RuntimeError('fixture offline')):
            interrupted = backup(context, storage, **options)
        self.assertIsInstance(interrupted, LegacyPending)
        self.assertIn('fixture offline', interrupted.reason)
        self.assertFalse(store.exists('backup/INSTRUCTION.md'))
        completed = backup(context, storage, **options)
        self.assertIsInstance(completed, Applied)
        self.assertEqual(2, completed.legacy_points)
        self.assertEqual('Legado: 2', store.read_text('backup/INSTRUCTION.md'))
        for source in sources:
            self.assertEqual('fixture bytes', store.read_text('backup/' + source))
        self.assertEqual(completed, backup(context, storage, **options))
