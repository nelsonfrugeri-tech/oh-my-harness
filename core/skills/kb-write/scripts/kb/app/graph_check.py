from kb.note.graph import derive_children
from kb.note.model import Note
from kb.note.vocabulary import Status


def graph_errors(notes: tuple[Note, ...]) -> tuple[str, ...]:
    active = {note.path.relative_path: note for note in notes if note.frontmatter.status == Status.ACTIVE}
    errors = []
    for path, note in active.items():
        expected = derive_children(path, tuple(active.values()))
        if set(note.frontmatter.children) != set(expected):
            errors.append(f'{path}: children differs from inverse parent links')
        for target in note.frontmatter.related:
            if target in active and path not in active[target].frontmatter.related:
                errors.append(f'{path}: related link is not mirrored at {target}')
    return tuple(errors)
