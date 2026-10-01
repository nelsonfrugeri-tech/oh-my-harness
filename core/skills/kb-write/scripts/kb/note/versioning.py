from dataclasses import replace

from .model import FrozenVersion, Note, VersionedUpdate
from .report import ValidationIssue, ValidationReport
from .timestamps import parse_timestamp
from .vocabulary import REASON_LIMITS, Status


def needs_new_version(previous: Note, replacement: Note) -> bool:
    old = previous.frontmatter
    compared = replace(replacement.frontmatter, parent=old.parent, children=old.children, related=old.related,
                       updated_at=old.updated_at, status=old.status)
    return replace(replacement, frontmatter=compared) != previous


def freeze(previous: Note, replacement: Note, *, at: str,
           reason: str) -> VersionedUpdate | ValidationReport:
    if not REASON_LIMITS[0] <= len(reason.strip()) <= REASON_LIMITS[1]:
        return ValidationReport((ValidationIssue('superseded_reason', 'reason must contain 30–500 characters'),))
    timestamp = parse_timestamp(at)
    updated = parse_timestamp(previous.frontmatter.updated_at)
    if timestamp is None or updated is None or timestamp < updated:
        return ValidationReport((ValidationIssue('superseded_at', 'timestamp must be UTC and not precede updated_at'),))
    if previous.path != replacement.path or previous.frontmatter.id != replacement.frontmatter.id:
        return ValidationReport((ValidationIssue('id', 'an update must retain the note id and path'),))
    old = previous.frontmatter
    frozen_note = replace(previous, frontmatter=replace(old, status=Status.SUPERSEDED,
                          superseded_at=at, superseded_reason=reason))
    frozen_path = history_path(previous.path.relative_path, old.version, at)
    current = replace(replacement, frontmatter=replace(replacement.frontmatter,
                      id=old.id, version=old.version + 1, created_at=old.created_at,
                      updated_at=at, status=Status.ACTIVE, superseded_at=None, superseded_reason=None))
    return VersionedUpdate(FrozenVersion(frozen_note, frozen_path), current)


def history_path(path: str, version: int, at: str) -> str:
    folder, name = path.rsplit("/", 1)
    return f"{folder}/.history/{at[:10]}--v{version}--{name}"
