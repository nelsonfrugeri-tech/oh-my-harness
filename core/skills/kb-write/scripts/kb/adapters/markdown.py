from __future__ import annotations

import dataclasses
import re
from enum import Enum
from pathlib import PurePosixPath

import yaml

from kb.adapters.yaml_codec import load_frontmatter
from kb.adapters.markdown_sections import parse_sections
from kb.note.model import Entities, Frontmatter, Generated, Note, NotePath, Section
from kb.note.vocabulary import Harness, NoteType, Scope, Status


def parse_note(text: str, path: str) -> Note:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        raise ValueError('Expected a YAML frontmatter block')
    boundary = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == '---'), None)
    if boundary is None:
        raise ValueError('Unclosed YAML frontmatter block')
    raw = load_frontmatter(''.join(lines[1:boundary]))
    frontmatter = _frontmatter(raw)
    parts = list(PurePosixPath(path).parts)
    if '.pending' in parts:
        parts.remove('.pending')
    if len(parts) < 4 or parts[-1] != parts[-2] + '.md':
        raise ValueError('Expected scope/domain/name/name.md')
    note_path = NotePath(Scope(parts[0]), parts[1], tuple(parts[2:-2]), parts[-2])
    sections = parse_sections(''.join(lines[boundary + 1:]))
    return Note(note_path, frontmatter, sections)


def _frontmatter(raw: dict) -> Frontmatter:
    allowed = {field.name for field in dataclasses.fields(Frontmatter)}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError('Unknown frontmatter fields: ' + ', '.join(sorted(unknown)))
    _validate_scalars(raw)
    data = dict(raw)
    try:
        data['type'] = NoteType(data['type'])
        data['status'] = Status(data['status'])
        generated = dict(data['generated'])
        generated['harness'] = Harness(generated['harness'])
        data['generated'] = Generated(**generated)
        entities = data['entities']
        keys = {field.name for field in dataclasses.fields(Entities)}
        if not isinstance(entities, dict) or set(entities) != keys:
            raise ValueError('entities must contain exactly the 13 schema keys')
        if any(not isinstance(v, list) or any(not isinstance(x, str) for x in v)
               for v in entities.values()):
            raise ValueError('Entity values must be lists of strings')
        data['entities'] = Entities(**{k: tuple(v) for k, v in entities.items()})
        for key in ('tags', 'related', 'children'):
            if not isinstance(data.get(key, []), list) or any(not isinstance(item, str) for item in data.get(key, [])):
                raise ValueError(f'{key} must be a list')
            data[key] = tuple(data.get(key, []))
        return Frontmatter(**data)
    except (KeyError, TypeError) as error:
        raise ValueError(f'Invalid frontmatter: {error}') from error


def render_note(note: Note) -> str:
    raw = _plain(dataclasses.asdict(note.frontmatter))
    raw = {key: value for key, value in raw.items() if value is not None or key == 'parent' or key == 'remote_url' and note.frontmatter.repository_path}
    frontmatter = yaml.safe_dump(raw, allow_unicode=True, sort_keys=False).rstrip()
    return f'---\n{frontmatter}\n---\n\n{note.body}\n'


def _plain(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _validate_scalars(raw: dict) -> None:
    required = ('id', 'type', 'title', 'description', 'summary', 'status', 'created_at', 'updated_at')
    optional = ('occurred_at', 'parent', 'superseded_at', 'superseded_reason',
                'repository_path', 'remote_url', 'default_branch')
    for key in required:
        if not isinstance(raw.get(key), str):
            raise ValueError(f'{key} must be a string')
    for key in optional:
        if raw.get(key) is not None and not isinstance(raw[key], str):
            raise ValueError(f'{key} must be a string or null')
    generated = raw.get('generated')
    if not isinstance(generated, dict) or set(generated) != {'harness', 'model', 'session_id', 'cwd', 'machine_id'}:
        raise ValueError('generated must contain the five provenance fields')
    for key, value in generated.items():
        if not isinstance(value, str) and not (key == 'model' and value is None):
            raise ValueError(f'generated.{key} has an invalid type')
    if type(raw.get('version')) is not int:
        raise ValueError('version must be an integer')
