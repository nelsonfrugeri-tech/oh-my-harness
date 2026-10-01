from kb.note.model import Note


def embed_text(note: Note) -> str:
    fields = note.frontmatter
    return '\n\n'.join((fields.title, fields.description, fields.summary))
