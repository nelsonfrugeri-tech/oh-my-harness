import json
from dataclasses import replace

from kb.app.context import Context
from kb.note.model import Note
from kb.search.payload import embed_text

QUEUE_PATH = '.repair.json'


def save_repairs(context: Context, notes: tuple[Note, ...]) -> None:
    if not notes:
        return
    entries = [{'path': note.path.relative_path, 'id': note.frontmatter.id,
                'version': note.frontmatter.version, 'parent': note.frontmatter.parent,
                'related': list(note.frontmatter.related), 'children': list(note.frontmatter.children)}
               for note in notes]
    context.store.write_text(QUEUE_PATH, json.dumps(entries, ensure_ascii=False))


def resume_repairs(context: Context) -> None:
    if not context.store.exists(QUEUE_PATH):
        return
    if context.index is None or context.embedder is None:
        raise RuntimeError('Index and embedder required to resume graph repair')
    entries = json.loads(context.store.read_text(QUEUE_PATH))
    for entry in entries:
        note = context.store.read(entry['path'])
        if (note.frontmatter.id, note.frontmatter.version) != (entry['id'], entry['version']):
            raise RuntimeError('Graph repair revision changed; repair must finish before publication')
        updated = replace(note, frontmatter=replace(note.frontmatter, parent=entry['parent'],
                          related=tuple(entry['related']), children=tuple(entry['children'])))
        if updated != note:
            context.store.write(updated)
        # Upsert also restores missing derived points; replay survives failure after disk write.
        context.index.upsert(updated, context.embedder.embed(embed_text(updated)))
    context.store.remove(QUEUE_PATH)
