from kb.app.ports import NoteStorePort
from kb.note.model import Note
from kb.note.naming import EXCLUDED_DIRS, RESERVED_FILES
from kb.note.vocabulary import Status


def note_path(path: str, *, include_pending: bool = False) -> bool:
    parts = path.split('/')
    if include_pending and len(parts) > 2 and parts[-2] == '.pending':
        parts.pop(-2)
    if len(parts) < 4 or parts[0] not in {'work', 'person'}:
        return False
    if any(part in EXCLUDED_DIRS or part.startswith('.') for part in parts):
        return False
    return parts[-1] not in RESERVED_FILES and parts[-1] == parts[-2] + '.md'


def published(store: NoteStorePort) -> tuple[Note, ...]:
    notes = []
    for path in store.paths():
        if not note_path(path):
            continue
        note = store.read(path)
        if note.frontmatter.status == Status.ACTIVE:
            notes.append(note)
    return tuple(notes)
