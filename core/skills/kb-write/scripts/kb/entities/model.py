from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .kinds import EntityKind


class CandidateKind(str, Enum):
    DATE = 'date'
    FIGURE = 'figure'


@dataclass(frozen=True)
class Candidate:
    kind: EntityKind | CandidateKind
    value: str


@dataclass(frozen=True)
class Entity:
    kind: EntityKind
    value: str
    description: str
    relation: str
    period: str
    source: str


@dataclass(frozen=True)
class DateEntry:
    at: str
    label: str
    who: str
    status: str
    source: str


@dataclass(frozen=True)
class Figure:
    value: Decimal
    unit: str
    label: str
    at: str
    source: str


@dataclass(frozen=True)
class TimelineEntry:
    at: str
    who: str
    what: str
    how: str
    evidence: str


@dataclass(frozen=True)
class Violation:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class EntityTables:
    entities: tuple[Entity, ...] = ()
    dates: tuple[DateEntry, ...] = ()
    figures: tuple[Figure, ...] = ()
    timeline: tuple[TimelineEntry, ...] = ()
    issues: tuple[Violation, ...] = ()


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Violation, ...] = ()
    transcript_available: bool = True

    @property
    def ok(self) -> bool:
        return not self.issues
