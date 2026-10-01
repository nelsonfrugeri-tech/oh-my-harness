from dataclasses import dataclass
from typing import Protocol

from kb.entities.model import Candidate
from kb.entities.secrets import find_secrets


@dataclass(frozen=True)
class Harvested:
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class Unavailable:
    reason: str


class HarvestSourcePort(Protocol):
    def harvest_candidates(self, path: str) -> tuple[Candidate, ...]: ...


def harvest(source: HarvestSourcePort, path: str) -> Harvested | Unavailable:
    try:
        candidates = source.harvest_candidates(path)
    except (OSError, ValueError, TypeError, RecursionError):
        return Unavailable('Transcript is unavailable, malformed or unsupported; no candidates were produced')
    safe = tuple(candidate for candidate in candidates if not find_secrets(candidate.value))
    return Harvested(tuple(dict.fromkeys(safe)))
