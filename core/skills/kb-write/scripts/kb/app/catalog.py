from kb.app.ports import NoteStorePort
from kb.note.model import Note
from kb.note.vocabulary import Status


def published(store: NoteStorePort) -> tuple[Note, ...]:
    notes = []
    for path in store.paths():
        parts = path.split('/')
        if any(part.startswith('.') or part == 'backup' for part in parts):
            continue
        if parts[-1] in {'index.md', 'INSTRUCTION.md', 'log.md'}:
            continue
        note = store.read(path)
        if note.frontmatter.status == Status.ACTIVE:
            notes.append(note)
    return tuple(notes)
