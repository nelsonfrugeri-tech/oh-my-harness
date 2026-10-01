from .model import Note
from .report import ValidationContext, ValidationIssue
from .vocabulary import Status


def validate_links(note: Note, context: ValidationContext) -> tuple[ValidationIssue, ...]:
    fm = note.frontmatter
    source = note.path.relative_path
    known = {candidate.path.relative_path: candidate for candidate in context.notes}
    issues: list[ValidationIssue] = []
    links = (('parent', (fm.parent,) if fm.parent else ()), ('related', fm.related), ('children', fm.children))
    for field, targets in links:
        if len(set(targets)) != len(targets):
            issues.append(ValidationIssue(field, 'duplicate links are not allowed'))
        for target in targets:
            parts = target.split('/')
            if target == source or any(part in ('.history', '.pending', 'backup', '..', '.', '') for part in parts):
                issues.append(ValidationIssue(field, 'link must target another current note: ' + target))
                continue
            candidate = known.get(target)
            if candidate is None or candidate.frontmatter.status is not Status.ACTIVE:
                issues.append(ValidationIssue(field, 'link target must exist and be active: ' + target))
    current = fm.parent
    visited = {source}
    while current and current in known:
        if current in visited:
            issues.append(ValidationIssue('parent', 'parent relationship must not form a cycle'))
            break
        visited.add(current)
        current = known[current].frontmatter.parent
    return tuple(issues)
