from dataclasses import asdict, replace
import os
import json
import math
from pathlib import Path
import sys
import unittest
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'core/skills/kb-write/scripts'))
from kb.note.model import Entities, Section
from kb.note.vocabulary import Status
from kb.search.model import Embedding, SparseWeight
from kb.search.payload import embed_text, point_id, to_payload
from test_kb_note_domain import sample_note


class PayloadTests(unittest.TestCase):
    def test_point_identity_is_stable_per_version(self):
        identifier = sample_note().frontmatter.id
        self.assertEqual(point_id(identifier, 1), point_id(identifier, 1))
        self.assertEqual(5, UUID(point_id(identifier, 1)).version)
        self.assertNotEqual(point_id(identifier, 1), point_id(identifier, 2))

    def test_embedding_uses_only_approved_summary_fields(self):
        note = sample_note()
        self.assertEqual('\n\n'.join((note.frontmatter.title, note.frontmatter.description,
                                     note.frontmatter.summary)), embed_text(note))

    def test_payload_derives_address_prefixes_hosts_and_entities(self):
        note = sample_note()
        note = replace(note, frontmatter=replace(note.frontmatter, entities=Entities(
            urls=('https://Example.org/a',), paths=('/tmp/project/code.py',))))
        payload = to_payload(note)
        self.assertEqual(['example.org'], payload['url_hosts'])
        self.assertIn('/tmp/project', payload['path_prefixes'])
        self.assertEqual('work', payload['scope'])
        self.assertEqual('projeto', payload['domain'])
        self.assertEqual('notas', payload['entity_path'])
        self.assertEqual(13, len(payload['entities']))

    def test_figures_and_dates_are_structured_for_nested_filters(self):
        note = sample_note()
        figures = '| Valor | Unidade | O que mede | Quando | Fonte |\n|---|---|---|---|---|\n'
        figures += '|12500|BRL/mês|Proposta|2026-10-01T12:00:00Z|Sessão|'
        dates = '| Data | O que é | Quem | Status | Fonte |\n|---|---|---|---|---|\n'
        dates += '|2026-10-01T12:00:00Z|Prazo|Ana|Aberto|Sessão|'
        payload = to_payload(replace(note, sections=(Section('Figures', figures), Section('Dates', dates))))
        self.assertEqual(12500.0, payload['figures'][0]['value'])
        self.assertEqual('BRL', payload['figures'][0]['currency'])
        self.assertEqual('2026-10-01T12:00:00Z', payload['dates'][0]['at'])

    def test_payload_roundtrip_preserves_all_frontmatter_fields(self):
        note = sample_note()
        fm = replace(note.frontmatter, parent='work/projeto/pai/pai.md',
                     children=('work/projeto/filha/filha.md',),
                     related=('work/projeto/irma/irma.md',),
                     superseded_at='2026-10-02T12:00:00Z', superseded_reason='Contexto atualizado.',
                     repository_path='/tmp/project', remote_url='https://example.org/repo',
                     default_branch='main')
        payload = json.loads(json.dumps(to_payload(replace(note, frontmatter=fm))))
        expected = json.loads(json.dumps(asdict(fm)))
        self.assertEqual(expected, {key: payload.get(key) for key in expected})
        self.assertTrue(set(expected).issubset(payload))
        self.assertIsNone(payload['generated']['model'])

    def test_reserved_index_is_never_payload(self):
        with self.assertRaises(ValueError):
            to_payload(sample_note(), path='work/projeto/index.md')

    def test_reserved_instruction_is_never_payload(self):
        with self.assertRaises(ValueError):
            to_payload(sample_note(), path='backup/INSTRUCTION.md')


@unittest.skipUnless(os.environ.get('OMH_KB_TEST_QDRANT_URL'), 'isolated Qdrant endpoint not provided')
class QdrantIntegrationTests(unittest.TestCase):
    def setUp(self):
        from kb.adapters.qdrant import QdrantIndex
        self.index = QdrantIndex(os.environ['OMH_KB_TEST_QDRANT_URL'], collection='knowledge-base-e2e')
        self.index.ensure_collection(dimension=3)
        from qdrant_client import models
        self.index.client.delete('knowledge-base-e2e', models.FilterSelector(filter=models.Filter()), wait=True)
        self.vector = Embedding((1.0, 0.0, 0.0), (SparseWeight(1, 1.0),))

    def tearDown(self):
        self.index.client.close()

    def test_existing_collection_dimension_must_match_the_model(self):
        from kb.app.errors import EnvironmentFailure
        with self.assertRaises(EnvironmentFailure):
            self.index.ensure_collection(dimension=1024)

    def test_status_and_legacy_filters_apply_to_hybrid_search(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        frozen = replace(note, frontmatter=replace(note.frontmatter, version=2))
        self.index.upsert(frozen, self.vector)
        self.index.set_payload(point_id(note.frontmatter.id, 1), {'status': 'superseded'})
        legacy = replace(note, frontmatter=replace(note.frontmatter, version=3))
        self.index.upsert(legacy, self.vector)
        self.index.set_payload(point_id(note.frontmatter.id, 3), {'legacy': True})
        self.assertEqual(1, len(self.index.search(self.vector, {})))
        self.assertEqual(2, len(self.index.search(self.vector, {}, include_history=True)))
        self.assertEqual(2, len(self.index.search(self.vector, {}, include_legacy=True)))
        for status in (Status.PENDING, Status.DEPRECATED):
            with self.assertRaises(ValueError):
                self.index.upsert(replace(note, frontmatter=replace(note.frontmatter, status=status)), self.vector)

    def test_nested_float_filter_binds_amount_and_currency_to_same_row(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        self.index.set_payload(point_id(note.frontmatter.id, 1), {'figures': [
            {'value': 12500.0, 'currency': 'USD'}, {'value': 9000.0, 'currency': 'BRL'}]})
        filters = {'must': [{'nested': {'key': 'figures', 'filter': {'must': [
            {'key': 'currency', 'match': {'value': 'BRL'}}, {'key': 'value', 'range': {'gt': 10000}}]}}}]}
        self.assertEqual((), self.index.search(self.vector, filters))
        self.index.set_payload(point_id(note.frontmatter.id, 1), {'figures': [{'value': 12500.0, 'currency': 'BRL'}]})
        self.assertEqual(1, len(self.index.search(self.vector, filters)))
        schema = self.index.client.get_collection('knowledge-base-e2e').payload_schema
        self.assertEqual('float', schema['figures[].value'].data_type.value)

    def test_date_path_and_host_filters_return_only_matching_notes(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        self.index.set_payload(point_id(note.frontmatter.id, 1), {
            'dates': [{'at': '2026-10-02T12:00:00Z'}],
            'path_prefixes': ['/tmp/project'], 'url_hosts': ['example.org']})
        cases = [({'key': 'dates[].at', 'range': {'gte': '2026-10-01T00:00:00Z',
                                               'lt': '2026-11-01T00:00:00Z'}}, True),
                 ({'key': 'dates[].at', 'range': {'gte': '2026-11-01T00:00:00Z'}}, False),
                 ({'key': 'path_prefixes', 'match': {'value': '/tmp/project'}}, True),
                 ({'key': 'url_hosts', 'match': {'value': 'example.org'}}, True),
                 ({'key': 'url_hosts', 'match': {'value': 'other.org'}}, False)]
        for condition, expected in cases:
            with self.subTest(condition=condition):
                self.assertEqual(expected, bool(self.index.search(self.vector, {'must': [condition]})))

    def test_missing_legacy_field_is_supported_but_pending_is_always_hidden(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        identifier = point_id(note.frontmatter.id, 1)
        self.index.client.delete_payload('knowledge-base-e2e', ['legacy'], [identifier], wait=True)
        self.assertEqual(1, len(self.index.search(self.vector, {})))
        self.index.set_payload(identifier, {'status': 'pending'})
        self.assertEqual((), self.index.search(self.vector, {}, include_legacy=True, include_history=True))

    def test_legacy_migration_paginates_and_resumes_after_a_transport_failure(self):
        from qdrant_client import models
        from qdrant_client.http.exceptions import ResponseHandlingException
        from unittest.mock import patch
        note = sample_note()
        points = [models.PointStruct(id=point_id(note.frontmatter.id, i),
                  vector={'dense': [1.0, 0.0, 0.0], 'sparse': models.SparseVector(indices=[1], values=[1.0])},
                  payload={'path': f'work/project/note-{i}.md'}) for i in range(101)]
        self.index.client.upsert('knowledge-base-e2e', points, wait=True)
        original = self.index.client.scroll
        calls = 0
        def fail_after_first_page(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise ResponseHandlingException(OSError('fixture connection interrupted'))
            return original(*args, **kwargs)
        with patch.object(self.index.client, 'scroll', side_effect=fail_after_first_page):
            with self.assertRaises(RuntimeError):
                self.index.mark_legacy('backup/')
        self.assertEqual(101, self.index.mark_legacy('backup/'))
        self.assertEqual(101, self.index.mark_legacy('backup/'))
        records, _ = self.index.client.scroll('knowledge-base-e2e', limit=200)
        self.assertTrue(all(p.payload['path'].startswith('backup/work/') for p in records))

    def test_manifest_scopes_legacy_migration_and_preserves_new_notes(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        newer = replace(note, frontmatter=replace(note.frontmatter, version=2))
        self.index.upsert(newer, self.vector)
        second = point_id(note.frontmatter.id, 2)
        self.index.set_payload(second, {'path': 'work/new/note/note.md'})
        sources = (note.path.relative_path,)
        self.assertEqual(1, self.index.mark_legacy('backup/', source_paths=sources))
        self.assertEqual(1, self.index.mark_legacy('backup/', source_paths=sources))
        untouched = self.index.client.retrieve('knowledge-base-e2e', [second])[0].payload
        self.assertEqual('work/new/note/note.md', untouched['path'])
        self.assertFalse(untouched['legacy'])
        self.assertEqual('active', untouched['status'])

    def test_manifest_migration_refuses_points_without_a_source_path(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        self.index.client.delete_payload('knowledge-base-e2e', ['path'],
                                         [point_id(note.frontmatter.id, 1)], wait=True)
        with self.assertRaises(RuntimeError):
            self.index.mark_legacy('backup/', source_paths=(note.path.relative_path,))

    def test_legacy_marking_is_idempotent_and_preserves_vectors(self):
        note = sample_note()
        self.index.upsert(note, self.vector)
        identifier = point_id(note.frontmatter.id, 1)
        before = self.index.client.retrieve('knowledge-base-e2e', [identifier], with_vectors=True)[0].vector
        self.assertEqual(1, self.index.mark_legacy('backup/'))
        self.assertEqual(1, self.index.mark_legacy('backup/'))
        after = self.index.client.retrieve('knowledge-base-e2e', [identifier], with_vectors=True)[0]
        self.assertEqual(before, after.vector)
        self.assertEqual('backup/' + note.path.relative_path, after.payload['path'])
        self.assertEqual((), self.index.search(self.vector, {}))


@unittest.skipUnless(os.environ.get('OMH_KB_TEST_EMBEDDER') == '1', 'real embedding opt-in not provided')
class EmbedderRuntimeTests(unittest.TestCase):
    def test_real_bge_m3_returns_finite_dense_and_sparse_vectors(self):
        from kb.adapters.embedder import BgeM3Embedder
        vector = BgeM3Embedder().embed('A nota apresenta um prazo em outubro para a proposta de trabalho.')
        self.assertEqual(1024, len(vector.dense))
        self.assertTrue(vector.sparse)
        self.assertTrue(all(math.isfinite(value) for value in vector.dense))
        self.assertTrue(all(item.index >= 0 and math.isfinite(item.value) for item in vector.sparse))


if __name__ == '__main__':
    unittest.main()
