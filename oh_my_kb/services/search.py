"""Hybrid search service.

Converts a natural-language query into dense + sparse vectors via the
injected :class:`Embedder`, asks Qdrant's Query API to fetch top results for
each vector independently, and fuses the two ranked lists with Reciprocal
Rank Fusion. Filters (``project``, ``archived``) are applied as Qdrant
payload conditions so they run server-side rather than after fusion.

A missing universe collection is *not* an error — it just means "no notes
yet in this universe", and the service returns an empty list.
"""

from __future__ import annotations

from dataclasses import dataclass

from qdrant_client.models import (
    Condition,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
)
from qdrant_client.models import (
    SparseVector as QdrantSparseVector,
)

from oh_my_kb.embedding import Embedder
from oh_my_kb.services.indexer import collection_name_for
from oh_my_kb.storage import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, QdrantStore

_PREFETCH_MULTIPLIER = 4


@dataclass(frozen=True, slots=True)
class SearchResult:
    id: str
    title: str
    summary: str
    type: str
    project: str
    created_at: str
    path: str
    score: float


class SearchService:
    def __init__(self, store: QdrantStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder

    def search(
        self,
        query: str,
        universe: str,
        project: str | None = None,
        top_k: int = 5,
        include_archived: bool = False,
    ) -> list[SearchResult]:
        collection = collection_name_for(universe)
        if not self._store.collection_exists(collection):
            return []

        embedding = self._embedder.embed_text(query)
        prefetch_limit = max(top_k * _PREFETCH_MULTIPLIER, top_k)
        payload_filter = _build_filter(project=project, include_archived=include_archived)

        # Filters are applied at the prefetch level so each candidate set
        # is already narrowed before RRF fusion runs.
        prefetch = [
            Prefetch(
                query=embedding.dense,
                using=DENSE_VECTOR_NAME,
                filter=payload_filter,
                limit=prefetch_limit,
            ),
            Prefetch(
                query=QdrantSparseVector(
                    indices=embedding.sparse.indices,
                    values=embedding.sparse.values,
                ),
                using=SPARSE_VECTOR_NAME,
                filter=payload_filter,
                limit=prefetch_limit,
            ),
        ]

        response = self._store.client.query_points(
            collection_name=collection,
            prefetch=prefetch,
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        results: list[SearchResult] = []
        for point in response.points:
            payload = point.payload or {}
            results.append(
                SearchResult(
                    id=str(payload.get("id", point.id)),
                    title=str(payload.get("title", "")),
                    summary=str(payload.get("summary", "")),
                    type=str(payload.get("type", "")),
                    project=str(payload.get("project", "")),
                    created_at=str(payload.get("created_at", "")),
                    path=str(payload.get("path", "")),
                    score=float(point.score),
                )
            )
        return results


def _build_filter(*, project: str | None, include_archived: bool) -> Filter | None:
    must: list[Condition] = []
    must_not: list[Condition] = []
    if project is not None:
        must.append(FieldCondition(key="project", match=MatchValue(value=project)))
    if not include_archived:
        must_not.append(FieldCondition(key="archived", match=MatchValue(value=True)))
    if not must and not must_not:
        return None
    return Filter(must=must or None, must_not=must_not or None)
