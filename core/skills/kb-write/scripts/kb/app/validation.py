from dataclasses import asdict

from kb.app.context import Context
from kb.app.catalog import published
from kb.app.identity import identity_conflicts
from kb.entities.proof import prove
from kb.entities.secrets import find_secrets
from kb.entities.tables import parse_tables
from kb.note.model import Note
from kb.note.validation import ValidationContext, validate


def validate_candidate(note: Note, context: Context, *, transcript: str | None,
                       previous: Note | None, approved_degraded: bool) -> tuple[str, ...]:
    report = validate(note, ValidationContext(context.machine_id, published(context.store)))
    errors = [f'{issue.field}: {issue.message}' for issue in report.issues]
    if find_secrets(str(asdict(note.frontmatter)) + '\n' + note.body):
        errors.append('Sensitive material is forbidden in notes')
    tables = parse_tables({section.heading: section.text for section in note.sections})
    inherited = asdict(previous.frontmatter.entities) if previous else None
    inherited_tables = parse_tables({s.heading: s.text for s in previous.sections}) if previous else None
    proof = prove(asdict(note.frontmatter.entities), note.body, transcript,
                  inherited, tables=tables, inherited_tables=inherited_tables)
    for issue in proof.issues:
        if transcript is None and approved_degraded and 'transcript' in str(issue).lower():
            continue
        errors.append(str(issue))
    if transcript is None:
        if not approved_degraded:
            errors.append('Transcript unavailable; explicit --approved-degraded is required')
        sources = next((s.text for s in note.sections if s.heading == 'Sources'), '')
        if 'entidades não foram comprovadas' not in sources.casefold():
            errors.append('Sources must record: entidades não foram comprovadas')
    errors.extend(identity_conflicts(note, context))
    return tuple(errors)
