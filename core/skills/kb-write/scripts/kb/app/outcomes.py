from dataclasses import dataclass


@dataclass(frozen=True)
class Pending:
    path: str
    new_entities: tuple[str, ...]
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class Approved:
    path: str
    version: int


@dataclass(frozen=True)
class Rejected:
    errors: tuple[str, ...]


@dataclass(frozen=True)
class Degraded:
    reason: str


@dataclass(frozen=True)
class Discarded:
    path: str


@dataclass(frozen=True)
class Moved:
    old: str
    new: str
