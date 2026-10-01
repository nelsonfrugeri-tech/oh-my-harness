from dataclasses import dataclass

from .model import Note


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class ValidationContext:
    machine_id: str
    notes: tuple[Note, ...] = ()
    check_language: bool = True
    check_links: bool = True
