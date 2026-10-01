from dataclasses import fields
import re

from .model import Note
from .report import ValidationIssue
from .sections import COMMON_OPTIONAL, CONDITIONAL_SECTIONS, SCHEMAS
from .vocabulary import NoteType


def validate_sections(note: Note) -> tuple[ValidationIssue, ...]:
    if not isinstance(note.frontmatter.type, NoteType):
        return ()
    schema = SCHEMAS[note.frontmatter.type]
    headings = tuple(section.heading for section in note.sections)
    allowed = schema.required + schema.optional + COMMON_OPTIONAL + CONDITIONAL_SECTIONS
    issues: list[ValidationIssue] = []
    if tuple(heading for heading in headings if heading in schema.required) != schema.required:
        issues.append(ValidationIssue('sections', 'required sections missing, duplicated or out of order: ' + ', '.join(schema.required)))
    if len(set(headings)) != len(headings):
        issues.append(ValidationIssue('sections', 'duplicate headings are not allowed'))
    for section in note.sections:
        if section.heading not in allowed:
            issues.append(ValidationIssue('sections', 'unknown heading: ' + section.heading))
        if not section.text.strip():
            issues.append(ValidationIssue('sections', 'section must not be empty: ' + section.heading))
        if _nested_heading(section.text):
            issues.append(ValidationIssue('sections', 'nested level-two headings must be parsed as sections'))
    entities = note.frontmatter.entities
    if any(getattr(entities, field.name) for field in fields(entities)) and 'Entities' not in headings:
        issues.append(ValidationIssue('sections', 'declared entities require Entities section'))
    if note.frontmatter.type is NoteType.EVENT:
        issues.extend(_timeline(note))
    return tuple(issues)


def _nested_heading(text: str) -> bool:
    fence = ''
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*', line):
                fence = ''
            continue
        opening = re.match(r' {0,3}(`{3,}|~{3,})(.*)$', line)
        if opening and not (opening[1].startswith('`') and '`' in opening[2]):
            fence = opening[1]
            continue
        if re.match(r'^##\s', line):
            return True
    return False


def _timeline(note: Note) -> list[ValidationIssue]:
    sections = tuple(section for section in note.sections if section.heading == 'Timeline')
    if not sections:
        return []
    lines = tuple(line.strip() for line in sections[0].text.splitlines() if line.strip())
    expected = ('Quando', 'Quem', 'O quê', 'Como', 'Evidência')
    header = tuple(cell.strip() for cell in lines[0].strip('|').split('|')) if lines else ()
    if len(lines) < 3 or header != expected:
        return [ValidationIssue('Timeline', 'requires table Quando | Quem | O quê | Como | Evidência with rows')]
    return []
