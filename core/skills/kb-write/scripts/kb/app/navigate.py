from kb.app.catalog import published
from kb.app.context import Context
from kb.note.model import Note


def navigate(path: str, context: Context) -> tuple[Note, ...]:
    notes = {note.path.relative_path: note for note in published(context.store)}
    if path not in notes:
        return ()
    note = notes[path]
    links = (*note.frontmatter.children, *note.frontmatter.related, note.frontmatter.parent)
    return tuple(notes[link] for link in dict.fromkeys(links) if link in notes)
