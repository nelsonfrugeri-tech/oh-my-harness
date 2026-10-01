from kb.app.context import Context
from kb.note.model import Note
from kb.note.naming import RESERVED_FILES


def identity_conflicts(note: Note, context: Context) -> tuple[str, ...]:
    for path in context.store.paths():
        parts = path.split('/')
        if parts[0] == 'backup' or '.history' in parts or parts[-1] in RESERVED_FILES:
            continue
        if parts[-1] == 'approved.md':
            continue
        existing = context.store.read(path)
        if existing.frontmatter.id == note.frontmatter.id and existing.path != note.path:
            return ('The note id already belongs to a different path',)
    return ()
