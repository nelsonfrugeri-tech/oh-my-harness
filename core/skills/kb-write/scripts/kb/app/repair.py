import re
from dataclasses import replace

from kb.app.catalog import published
from kb.app.context import Context
from kb.note.graph import derive_children, mirror_related
from kb.note.index_page import IndexEntry, render_index
from kb.note.model import Note
from kb.search.payload import point_id


def repair(context: Context, source: Note, descriptions: tuple[tuple[str, str], ...], *,
           publishing: bool = False) -> None:
    notes = published(context.store)
    for note in mirror_related(source, notes):
        children = derive_children(note.path.relative_path, notes)
        updated = replace(note, frontmatter=replace(note.frontmatter, children=children))
        if updated != context.store.read(note.path.relative_path):
            context.store.write(updated)
        if context.index is not None and not (publishing and updated.path == source.path):
            context.index.set_payload(point_id(updated.frontmatter.id, updated.frontmatter.version),
                                      {'parent': updated.frontmatter.parent,
                                       'related': list(updated.frontmatter.related),
                                       'children': list(updated.frontmatter.children)})
    _indexes(context, source, dict(descriptions))


def _indexes(context: Context, source: Note, descriptions: dict[str, str]) -> None:
    scope = source.path.scope.value
    domain = source.path.domain
    domain_path = f'{scope}/{domain}'
    entries = _existing(context, domain_path + '/index.md')
    for depth in range(1, len(source.path.entities) + 1):
        entity = source.path.entities[:depth]
        key = domain_path + '/' + '/'.join(entity)
        if entity not in entries:
            if key not in descriptions:
                raise ValueError(f'Approved entity description required: {key}')
            entries[entity] = descriptions[key]
    context.store.write_text(domain_path + '/index.md', render_index(tuple(
        IndexEntry(path, description) for path, description in entries.items())))
    scopes = _existing(context, scope + '/index.md')
    if (domain,) not in scopes:
        if domain_path not in descriptions:
            raise ValueError(f'Approved domain description required: {domain_path}')
        scopes[(domain,)] = descriptions[domain_path]
    context.store.write_text(scope + '/index.md', render_index(tuple(
        IndexEntry(path, description) for path, description in scopes.items())))


def _existing(context: Context, path: str) -> dict[tuple[str, ...], str]:
    if not context.store.exists(path):
        return {}
    text = context.store.read_text(path)
    return {tuple(target.rstrip('/').split('/')): description
            for target, description in re.findall(r'^\s*- \[[^\]]+\]\(([^)]+)\) — (.+)$',
                                                   text, re.MULTILINE)}
