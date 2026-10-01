from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from kb.app.errors import EnvironmentFailure

from kb.app.ports import SearchIndexPort
from kb.entities.kinds import EntityKind
from kb.note.model import Note
from kb.note.vocabulary import Status
from kb.search.model import DEFAULT_EXCLUSIONS, Embedding, SearchHit
from kb.search.payload import point_id, to_payload

_Result = TypeVar('_Result')


class QdrantIndex(SearchIndexPort):
    def __init__(self, url: str, *, collection: str = 'knowledge-base', timeout: int = 10):
        self.client = QdrantClient(url=url, timeout=timeout)
        self.collection = collection
        self.timeout = timeout

    def ensure_collection(self, *, dimension: int = 1024) -> None:
        if not _retry(lambda: self.client.collection_exists(self.collection)):
            _retry(lambda: self.client.create_collection(
                self.collection, vectors_config={'dense': models.VectorParams(size=dimension, distance=models.Distance.COSINE)},
                sparse_vectors_config={'sparse': models.SparseVectorParams()}))
        configuration = _retry(lambda: self.client.get_collection(self.collection)).config.params
        vectors = configuration.vectors
        if not isinstance(vectors, dict) or 'dense' not in vectors or vectors['dense'].size != dimension:
            raise EnvironmentFailure('Collection dense dimension does not match the fixed embedding model.')
        if not configuration.sparse_vectors or 'sparse' not in configuration.sparse_vectors:
            raise EnvironmentFailure('Collection must define the sparse vector.')
        keywords = ('kind', 'scope', 'domain', 'entity_path', 'type', 'status', 'tags',
                    'path_prefixes', 'url_hosts', 'figures[].currency', 'figures[].unit')
        for name in (*keywords, *(f'entities.{kind.value}' for kind in EntityKind)):
            self._index(name, models.PayloadSchemaType.KEYWORD)
        self._index('version', models.PayloadSchemaType.INTEGER)
        self._index('legacy', models.PayloadSchemaType.BOOL)
        self._index('figures[].value', models.PayloadSchemaType.FLOAT)
        for name in ('created_at', 'updated_at', 'occurred_at', 'dates[].at'):
            self._index(name, models.PayloadSchemaType.DATETIME)

    def upsert(self, note: Note, vector: object) -> None:
        if note.frontmatter.status != Status.ACTIVE:
            raise ValueError('Only active notes may be indexed.')
        embedding = _embedding(vector)
        point = models.PointStruct(
            id=point_id(note.frontmatter.id, note.frontmatter.version), payload=to_payload(note),
            vector={'dense': list(embedding.dense), 'sparse': _sparse(embedding)})
        _retry(lambda: self.client.upsert(self.collection, [point], wait=True))

    def set_payload(self, point_id: str, fields: dict[str, object]) -> None:
        _retry(lambda: self.client.set_payload(self.collection, fields, [point_id], wait=True))

    def search(self, vector: object, filters: dict[str, object], *,
               include_history: bool = False, include_legacy: bool = False) -> tuple[SearchHit, ...]:
        embedding = _embedding(vector)
        selected = _filter(filters, include_history=include_history, include_legacy=include_legacy)
        prefetch = [models.Prefetch(query=list(embedding.dense), using='dense', filter=selected, limit=40),
                    models.Prefetch(query=_sparse(embedding), using='sparse', filter=selected, limit=40)]
        result = _retry(lambda: self.client.query_points(
            self.collection, prefetch=prefetch, query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=selected, limit=10, with_payload=True, timeout=self.timeout))
        return tuple(SearchHit(str(point.id), point.score, point.payload or {}) for point in result.points)

    def mark_legacy(self, prefix: str, *, source_paths: tuple[str, ...] | None = None) -> int:
        if prefix != 'backup/':
            raise ValueError('Legacy migration requires the backup/ prefix.')
        sources = frozenset(source_paths) if source_paths is not None else None
        offset = None
        matched = 0
        while True:
            points, next_offset = _retry(lambda: self.client.scroll(
                self.collection, limit=100, offset=offset, with_payload=True, with_vectors=False))
            updates: list[models.SetPayloadOperation] = []
            for point in points:
                payload = point.payload or {}
                if payload.get('kind') == 'session':
                    session_id = payload.get('session_id') or str(point.id)
                    domain = payload.get('domain')
                    if sources is not None and not isinstance(domain, str):
                        raise EnvironmentFailure('Legacy session point has no domain for manifest matching.')
                    if sources is not None and f'{domain}/sessions/{session_id}.json' not in sources:
                        continue
                    fields = {'legacy': True}
                else:
                    path = payload.get('path')
                    if not isinstance(path, str) or not path:
                        raise EnvironmentFailure('Legacy migration cannot match a note without its source path.')
                    original_path = path.removeprefix(prefix)
                    if sources is not None and original_path not in sources:
                        continue
                    if path.split('/')[-1] in {'INSTRUCTION.md', 'index.md'}:
                        continue
                    fields = {'legacy': True, 'path': prefix + original_path}
                matched += 1
                if all(payload.get(key) == value for key, value in fields.items()):
                    continue
                updates.append(models.SetPayloadOperation(set_payload=models.SetPayload(
                    payload=fields, points=[point.id])))
            if updates:
                _retry(lambda: self.client.batch_update_points(self.collection, updates, wait=True))
            if next_offset is None:
                break
            offset = next_offset
        return matched

    def _index(self, field: str, schema: models.PayloadSchemaType) -> None:
        _retry(lambda: self.client.create_payload_index(self.collection, field, schema, wait=True))


def _filter(filters: dict[str, object], *, include_history: bool, include_legacy: bool) -> models.Filter:
    excluded = [models.FieldCondition(key=item.key, match=models.MatchValue(value=item.value))
                for item in DEFAULT_EXCLUSIONS
                if not (include_history and item.value == 'superseded')
                and not (include_legacy and item.key == 'legacy')]
    clauses = [models.Filter.model_validate(filters)]
    if not include_legacy:
        states = ['active', 'superseded'] if include_history else ['active']
        clauses.append(models.Filter(must=[models.FieldCondition(key='status', match=models.MatchAny(any=states))]))
    return models.Filter(must=clauses, must_not=excluded)


def _embedding(vector: object) -> Embedding:
    if not isinstance(vector, Embedding) or not vector.dense:
        raise ValueError('A dense and sparse Embedding is required.')
    return vector


def _sparse(vector: Embedding) -> models.SparseVector:
    return models.SparseVector(indices=[item.index for item in vector.sparse],
                               values=[item.value for item in vector.sparse])


def _retry(operation: Callable[[], _Result]) -> _Result:
    for attempt in range(3):
        try:
            return operation()
        except (ResponseHandlingException, UnexpectedResponse) as error:
            retryable = not isinstance(error, UnexpectedResponse) or error.status_code >= 500 or error.status_code == 429
            if not retryable or attempt == 2:
                raise RuntimeError('Qdrant request failed after bounded retries.') from error
            time.sleep(random.uniform(0, 0.1 * 2 ** attempt))
    raise RuntimeError('Unreachable retry state.')
