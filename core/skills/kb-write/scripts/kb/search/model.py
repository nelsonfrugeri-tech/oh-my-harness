from dataclasses import dataclass


@dataclass(frozen=True)
class SparseWeight:
    index: int
    value: float


@dataclass(frozen=True)
class Embedding:
    dense: tuple[float, ...]
    sparse: tuple[SparseWeight, ...]


@dataclass(frozen=True)
class SearchHit:
    id: str
    score: float
    payload: dict[str, object]


@dataclass(frozen=True)
class Exclusion:
    key: str
    value: str | bool


DEFAULT_EXCLUSIONS = (
    Exclusion('status', 'superseded'), Exclusion('legacy', True),
    Exclusion('status', 'pending'), Exclusion('status', 'deprecated'),
)
