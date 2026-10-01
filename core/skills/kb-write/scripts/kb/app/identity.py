from kb.app.catalog import note_path
from kb.app.context import Context
from kb.note.model import Note


def identity_conflicts(note: Note, context: Context) -> tuple[str, ...]:
    for path in context.store.paths():
        if not note_path(path, include_pending=True):
            continue
        existing = context.store.read(path)
        if existing.frontmatter.id == note.frontmatter.id and existing.path != note.path:
            return ('The note id already belongs to a different path',)
    return ()
