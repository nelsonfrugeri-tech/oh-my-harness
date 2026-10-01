from dataclasses import replace

from .model import Note
from .vocabulary import Status


def derive_children(parent: str, notes: tuple[Note, ...]) -> tuple[str, ...]:
    return tuple(sorted(note.path.relative_path for note in notes
                        if note.frontmatter.parent == parent and note.frontmatter.status is Status.ACTIVE))


def mirror_related(source: Note, notes: tuple[Note, ...]) -> tuple[Note, ...]:
    source_path = source.path.relative_path
    requested = set(source.frontmatter.related) if source.frontmatter.status is Status.ACTIVE else set()
    updated: list[Note] = []
    for note in notes:
        if note.path.relative_path == source_path:
            updated.append(source)
            continue
        related = set(note.frontmatter.related) - {source_path}
        if note.path.relative_path in requested and note.frontmatter.status is Status.ACTIVE:
            related.add(source_path)
        updated.append(replace(note, frontmatter=replace(note.frontmatter, related=tuple(sorted(related)))))
    return tuple(updated)
