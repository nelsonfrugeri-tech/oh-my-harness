from dataclasses import dataclass, asdict
from datetime import datetime
import re

from kb.app.context import Context
from kb.app.graph_check import graph_errors
from kb.app.pending import load as load_pending
from kb.entities.proof import prove
from kb.entities.secrets import find_secrets
from kb.entities.tables import parse_tables
from kb.note.naming import RESERVED_FILES
from kb.note.validation import ValidationContext, validate
from kb.note.vocabulary import Status


@dataclass(frozen=True)
class PendingAge:
    path: str
    age_seconds: float


@dataclass(frozen=True)
class Checked:
    errors: tuple[str, ...]
    pending: tuple[PendingAge, ...]
    notes: int


def check(context: Context) -> Checked:
    errors, pending, notes = _artifact_errors(context), [], []
    origins = {}
    for path in context.store.paths():
        parts = path.split('/')
        if 'backup' in parts or parts[-1] in RESERVED_FILES:
            continue
        if len(parts) > 1 and parts[-2:] == ['.pending', '.receipt.md']:
            continue
        if re.search(r' \d+\.md$', path):
            errors.append(f'{path}: iCloud conflict copy')
            continue
        try:
            logical = '/'.join((*parts[:-2], parts[-3] + '.md')) if '.history' in parts else path
            note = context.store.read(path, logical)
            if '.history' in parts and note.frontmatter.status != Status.SUPERSEDED:
                raise ValueError('A frozen version must have status superseded')
            notes.append(note)
            origins[note] = path
            if note.frontmatter.status == Status.PENDING:
                pending.append(_pending_age(note, path, context))
        except (ValueError, TypeError, OSError) as error:
            errors.append(f'{path}: {error}')
    active = tuple(note for note in notes if note.frontmatter.status == Status.ACTIVE)
    for note in notes:
        report = validate(note, ValidationContext(context.machine_id, active,
                          check_links='/.history/' not in origins[note]))
        errors.extend(f'{origins[note]}: {issue.field}: {issue.message}'
                      for issue in report.issues)
        errors.extend(_content_errors(note, origins[note]))
        if note.frontmatter.status == Status.ACTIVE:
            errors.extend(_index_errors(note, context))
    errors.extend(graph_errors(tuple(notes)))
    identifiers = {}
    for note in notes:
        identifiers.setdefault(note.frontmatter.id, set()).add(note.path.relative_path)
    errors.extend(f'{identifier}: duplicate id across paths' for identifier, paths in identifiers.items()
                  if len(paths) > 1)
    errors.extend(_orphan_indexes(context))
    return Checked(tuple(errors), tuple(pending), len(notes))


def _index_errors(note, context):
    base = f'{note.path.scope.value}/{note.path.domain}'
    index_path = base + '/index.md'
    if not context.store.exists(index_path):
        return [f'{index_path}: missing domain index']
    content = context.store.read_text(index_path)
    errors = []
    for depth in range(1, len(note.path.entities) + 1):
        link = '/'.join(note.path.entities[:depth]) + '/'
        if f']({link})' not in content:
            errors.append(f'{index_path}: missing entity {link}')
    scope_index = note.path.scope.value + '/index.md'
    if not context.store.exists(scope_index):
        errors.append(f'{scope_index}: missing scope index')
    elif f']({note.path.domain}/)' not in context.store.read_text(scope_index):
        errors.append(f'{scope_index}: missing domain entry {note.path.domain}')
    return errors


def _content_errors(note, source):
    tables = parse_tables({section.heading: section.text for section in note.sections})
    proof = prove(asdict(note.frontmatter.entities), note.body, None, tables=tables)
    errors = [f'{source}: {issue.code}: {issue.message}'
              for issue in proof.issues if issue.code != 'transcript-unavailable']
    if find_secrets(str(asdict(note.frontmatter))):
        errors.append(f'{source}: sensitive frontmatter')
    return errors


def _artifact_errors(context):
    errors = []
    for path in context.store.files():
        if path.startswith('backup/') or '/.history/' in path:
            continue
        if path.endswith('.tmp'):
            errors.append(f'{path}: orphan temporary file')
    for path in context.store.directories():
        parts = path.split('/')
        if len(parts) < 3 or parts[0] not in {'work', 'person'} or any(p.startswith('.') for p in parts):
            continue
        if context.store.exists(path + '/' + parts[-1] + '.md'):
            continue
        descendants = [p for p in context.store.paths() if p.startswith(path + '/')]
        if _only_pending(descendants, context):
            continue
        index = '/'.join(parts[:2]) + '/index.md'
        link = '/'.join(parts[2:]) + '/'
        if not context.store.exists(index) or f']({link})' not in context.store.read_text(index):
            errors.append(f'{path}: entity directory missing from domain index')
    return errors


def _only_pending(paths, context):
    candidates = [path for path in paths if path.split('/')[-1] not in RESERVED_FILES]
    if not candidates:
        return False
    for path in candidates:
        if '/.pending/' in path:
            continue
        try:
            if context.store.read(path).frontmatter.status != Status.PENDING:
                return False
        except (ValueError, TypeError, OSError):
            return False
    return True


def _orphan_indexes(context):
    errors = []
    directories = set(context.store.directories())
    for path in context.store.paths():
        parts = path.split('/')
        if parts[-1] != 'index.md' or parts[0] not in {'work', 'person'} or len(parts) > 3:
            continue
        parent = '/'.join(parts[:-1])
        content = context.store.read_text(path)
        for target in re.findall(r'^\s*- \[[^\]]+\]\(([^)]+)\)', content, re.MULTILINE):
            resolved = parent + '/' + target.rstrip('/')
            if '..' in target.split('/') or resolved not in directories:
                errors.append(f'{path}: orphan index entry {target}')
    return errors


def _pending_age(note, path, context):
    metadata = load_pending(context.store, note.path.relative_path)
    created = datetime.fromisoformat(metadata.at.replace('Z', '+00:00'))
    now = datetime.fromisoformat(context.clock.now().replace('Z', '+00:00'))
    return PendingAge(path, max(0, (now - created).total_seconds()))
