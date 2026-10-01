import re

from .language import is_pt_br
from .link_validation import validate_links
from .metadata_validation import validate_metadata
from .model import Note
from .naming import check_name
from .report import ValidationContext, ValidationIssue, ValidationReport
from .section_validation import validate_sections
from .vocabulary import Scope


def validate(note: Note, context: ValidationContext) -> ValidationReport:
    issues = list(validate_metadata(note, context))
    if not isinstance(note.path.scope, Scope):
        issues.append(ValidationIssue('path.scope', 'must be work or person'))
    names = (note.path.domain, *note.path.entities, note.path.name)
    for index, name in enumerate(names):
        parent = names[index - 1] if index else None
        issues.extend(ValidationIssue('path', message) for message in check_name(name, parent=parent))
    tags = note.frontmatter.tags
    if not 1 <= len(tags) <= 6 or len(set(tags)) != len(tags):
        issues.append(ValidationIssue('tags', 'requires 1–6 distinct tags'))
    for tag in tags:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', tag):
            issues.append(ValidationIssue('tags', 'must be lowercase kebab-case'))
    issues.extend(validate_sections(note))
    if context.check_links and isinstance(note.path.scope, Scope):
        issues.extend(validate_links(note, context))
    if context.check_language:
        texts = (('title', note.frontmatter.title), ('description', note.frontmatter.description),
                 ('summary', note.frontmatter.summary), ('body', note.body))
        if note.frontmatter.superseded_reason is not None:
            texts += (('superseded_reason', note.frontmatter.superseded_reason),)
        for field, text in texts:
            if not is_pt_br(text):
                issues.append(ValidationIssue(field, 'every prose paragraph must be in pt-BR'))
    return ValidationReport(tuple(issues))
