from dataclasses import asdict
import json
from urllib.parse import urlsplit

from kb.entities.tables import parse_tables
from kb.note.model import Note

from .embedding_text import embed_text
from .identity import point_id
from .model import DEFAULT_EXCLUSIONS

__all__ = ['DEFAULT_EXCLUSIONS', 'embed_text', 'point_id', 'to_payload']


def to_payload(note: Note, *, path: str | None = None, legacy: bool = False) -> dict[str, object]:
    fields = note.frontmatter
    target = path or note.path.relative_path
    if target.split('/')[-1] in {'INSTRUCTION.md', 'index.md'}:
        raise ValueError('Reserved navigation or migration files cannot be indexed.')
    tables = parse_tables({section.heading: section.text for section in note.sections})
    if tables.issues:
        raise ValueError('Invalid structured tables cannot be indexed.')
    figures = [dict(asdict(entry), value=float(entry.value),
                    currency=entry.unit.split('/')[0]) for entry in tables.figures]
    payload: dict[str, object] = json.loads(json.dumps(asdict(fields)))
    payload.update({
        'kind': 'note', 'path': target, 'scope': note.path.scope.value,
        'domain': note.path.domain, 'entity_path': '/'.join(note.path.entities), 'legacy': legacy,
        'dates': [asdict(entry) for entry in tables.dates], 'figures': figures,
        'path_prefixes': _prefixes(fields.entities.paths),
        'url_hosts': sorted({urlsplit(url).hostname for url in fields.entities.urls if urlsplit(url).hostname}),
    })
    return payload


def _prefixes(paths: tuple[str, ...]) -> list[str]:
    prefixes: set[str] = set()
    for path in paths:
        parts = path.split('/')
        for length in range(1, len(parts) + 1):
            value = '/'.join(parts[:length])
            if value:
                prefixes.add(value)
        if path.startswith('/'):
            prefixes.add('/')
    return sorted(prefixes)
