from dataclasses import fields
from uuid import UUID

from .model import Frontmatter, Note
from .report import ValidationContext, ValidationIssue
from .timestamps import parse_timestamp
from .vocabulary import DESCRIPTION_LIMITS, Harness, NoteType, REASON_LIMITS, Status, SUMMARY_LIMITS, TITLE_LIMITS


def _uuid(value: str, *, version: int | None = None) -> bool:
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value and (version is None or parsed.version == version)


def _timestamps(fm: Frontmatter) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    created, updated = parse_timestamp(fm.created_at), parse_timestamp(fm.updated_at)
    if created is None:
        issues.append(ValidationIssue('created_at', 'must be RFC 3339 UTC'))
    if updated is None:
        issues.append(ValidationIssue('updated_at', 'must be RFC 3339 UTC'))
    if created and updated and created > updated:
        issues.append(ValidationIssue('updated_at', 'must not precede created_at'))
    if fm.type is NoteType.EVENT:
        if fm.occurred_at is None or parse_timestamp(fm.occurred_at, utc=False) is None:
            issues.append(ValidationIssue('occurred_at', 'event requires an RFC 3339 timestamp'))
    elif fm.occurred_at is not None:
        issues.append(ValidationIssue('occurred_at', 'only event may declare occurred_at'))
    if fm.status is Status.SUPERSEDED:
        at = parse_timestamp(fm.superseded_at or '')
        if at is None or (updated and at < updated):
            issues.append(ValidationIssue('superseded_at', 'superseded requires UTC timestamp >= updated_at'))
        if not REASON_LIMITS[0] <= len((fm.superseded_reason or '').strip()) <= REASON_LIMITS[1]:
            issues.append(ValidationIssue('superseded_reason', 'must contain 30–500 characters'))
    elif fm.superseded_at is not None or fm.superseded_reason is not None:
        issues.append(ValidationIssue('superseded_at', 'superseded fields require superseded status'))
    return issues


def _provenance(fm: Frontmatter, context: ValidationContext) -> list[ValidationIssue]:
    gen = fm.generated
    issues: list[ValidationIssue] = []
    if not isinstance(gen.harness, Harness):
        issues.append(ValidationIssue('generated.harness', 'must be claude-code, codex or cursor'))
    if not gen.session_id.strip():
        issues.append(ValidationIssue('generated.session_id', 'must not be empty'))
    if not gen.cwd.startswith('/'):
        issues.append(ValidationIssue('generated.cwd', 'must be absolute'))
    if not _uuid(gen.machine_id) or gen.machine_id != context.machine_id:
        issues.append(ValidationIssue('generated.machine_id', 'must match the stable machine identity UUID'))
    if gen.model is not None and not gen.model.strip():
        issues.append(ValidationIssue('generated.model', 'must be nonempty or null'))
    return issues


def _identity(note: Note) -> list[ValidationIssue]:
    fm = note.frontmatter
    repository = (fm.repository_path, fm.remote_url, fm.default_branch)
    is_identity = note.path.name == 'identity' and not note.path.entities
    if any(value is not None for value in repository) and not is_identity:
        return [ValidationIssue('repository_path', 'repository fields belong only to domain identity/identity.md')]
    if is_identity and fm.type is not NoteType.REFERENCE:
        return [ValidationIssue('type', 'identity must have reference type')]
    if any(value is not None for value in repository):
        if not all(value and value.strip() for value in (fm.repository_path, fm.default_branch)):
            return [ValidationIssue('repository_path', 'code identity requires repository_path and default_branch')]
        if fm.remote_url is not None and not fm.remote_url.strip():
            return [ValidationIssue('remote_url', 'must be nonempty or null when unavailable or redacted')]
        if fm.repository_path is not None and not fm.repository_path.startswith('/'):
            return [ValidationIssue('repository_path', 'repository_path must be absolute')]
    return []


def validate_metadata(note: Note, context: ValidationContext) -> tuple[ValidationIssue, ...]:
    fm = note.frontmatter
    issues: list[ValidationIssue] = []
    for field, limits in (('title', TITLE_LIMITS), ('description', DESCRIPTION_LIMITS), ('summary', SUMMARY_LIMITS)):
        if not limits[0] <= len(getattr(fm, field)) <= limits[1]:
            issues.append(ValidationIssue(field, f'must contain {limits[0]}–{limits[1]} characters'))
    if not isinstance(fm.type, NoteType):
        issues.append(ValidationIssue('type', 'must be decision, event, procedure, reference or conversation'))
    if not isinstance(fm.status, Status):
        issues.append(ValidationIssue('status', 'must be pending, active, deprecated or superseded'))
    if not _uuid(fm.id, version=4):
        issues.append(ValidationIssue('id', 'must be a canonical UUID v4'))
    if type(fm.version) is not int or fm.version < 1:
        issues.append(ValidationIssue('version', 'must be an integer >= 1'))
    for field in fields(fm.entities):
        values = getattr(fm.entities, field.name)
        if any(not value.strip() for value in values) or len(set(values)) != len(values):
            issues.append(ValidationIssue('entities.' + field.name, 'must contain distinct nonempty values'))
    return tuple(issues + _timestamps(fm) + _provenance(fm, context) + _identity(note))
