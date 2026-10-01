import re
from collections.abc import Mapping, Sequence
from datetime import datetime

from .extraction import extract
from .kinds import EntityKind, LITERAL_KINDS
from .model import Candidate, CandidateKind, EntityTables, ValidationReport, Violation
from .normalization import normalize
from .narrative import narrative
from .secrets import find_secrets


def prove(declared: Mapping[str, Sequence[str]], prose: str, transcript: str | None,
          inherited: Mapping[str, Sequence[str]] | None = None, *,
          tables: EntityTables | None = None,
          inherited_tables: EntityTables | None = None) -> ValidationReport:
    """Check both declaration directions; unavailable transcript never counts as proof."""
    issues = _schema(declared)
    if issues:
        return ValidationReport(tuple(issues), transcript is not None)
    text = narrative(prose)
    candidates = tuple(Candidate(EntityKind(key), value) for key, values in declared.items() for value in values)
    for item in candidates:
        if find_secrets(item.value):
            issues.append(Violation('secret', item.kind.value, 'Dado sensível recusado.'))
            continue
        if not _present(item, text):
            issues.append(Violation('absent-from-prose', item.kind.value, item.value))
        prior = inherited.get(item.kind.value, ()) if inherited else ()
        if transcript is not None and item.value not in prior and not _present(item, transcript):
            issues.append(Violation('absent-from-transcript', item.kind.value, item.value))
    if find_secrets(prose):
        issues.append(Violation('secret', 'body', 'Dado sensível recusado.'))
    if transcript is None:
        issues.append(Violation('transcript-unavailable', 'transcript', 'Entidades não comprovadas.'))
    if tables is not None:
        issues.extend(tables.issues)
        issues.extend(_table_proof(candidates, tables, text, transcript, inherited_tables))
    structured = tables or EntityTables()
    allowed = set(candidates) | _table_candidates(structured)
    allowed.update(Candidate(CandidateKind.DATE, entry.at) for entry in structured.figures)
    for item in extract(prose):
        if not _declared(item, allowed):
            message = 'Dado sensível recusado.' if find_secrets(item.value) else item.value
            issues.append(Violation('undeclared', item.kind.value, message))
    return ValidationReport(tuple(issues), transcript is not None)


def _schema(declared: Mapping[str, Sequence[str]]) -> list[Violation]:
    issues: list[Violation] = []
    if set(declared) != {kind.value for kind in EntityKind}:
        issues.append(Violation('entity-keys', 'entities', 'As 13 chaves do enum são obrigatórias.'))
    for key, values in declared.items():
        if isinstance(values, str) or not isinstance(values, (list, tuple)):
            issues.append(Violation('entity-list', key, 'Esperada lista de strings.'))
        elif any(not isinstance(value, str) or not value.strip() for value in values):
            issues.append(Violation('entity-value', key, 'Entidade deve ser texto não vazio.'))
        elif key in {kind.value for kind in EntityKind} and EntityKind(key) not in LITERAL_KINDS and any(
                normalize(EntityKind(key), value) != value for value in values):
            issues.append(Violation('entity-slug', key, 'Nome deve ser kebab-case normalizado.'))
        elif len(set(values)) != len(values):
            issues.append(Violation('entity-duplicate', key, 'Entidade duplicada.'))
    return issues


def _present(item: Candidate, text: str) -> bool:
    if isinstance(item.kind, EntityKind):
        if item.kind in LITERAL_KINDS:
            return re.search(r'(?<![\w/])' + re.escape(item.value) + r'(?![\w/?#.-])', text) is not None
        words = normalize(item.kind, text)
        return f'-{normalize(item.kind, item.value)}-' in f'-{words}-'
    return any(_equivalent(item, candidate) for candidate in extract(text))


def _table_candidates(tables: EntityTables) -> set[Candidate]:
    dates = {Candidate(CandidateKind.DATE, entry.at) for entry in tables.dates}
    figures = {Candidate(CandidateKind.FIGURE, f'{entry.value.normalize():f} {entry.unit}') for entry in tables.figures}
    return dates | figures


def _table_proof(candidates: tuple[Candidate, ...], tables: EntityTables,
                 prose: str, transcript: str | None, inherited: EntityTables | None) -> list[Violation]:
    issues: list[Violation] = []
    rows = {Candidate(entity.kind, entity.value) for entity in tables.entities}
    for missing in set(candidates) ^ rows:
        message = 'Dado sensível recusado.' if find_secrets(missing.value) else missing.value
        issues.append(Violation('entity-table-parity', missing.kind.value, message))
    previous = inherited or EntityTables()
    new = EntityTables(dates=tuple(entry for entry in tables.dates if entry not in previous.dates),
                       figures=tuple(entry for entry in tables.figures if entry not in previous.figures))
    additions = _table_candidates(new)
    for item in _table_candidates(tables):
        if not _present(item, prose):
            issues.append(Violation('absent-from-prose', item.kind.value, item.value))
        if transcript is not None and item in additions and not _present(item, transcript):
            issues.append(Violation('absent-from-transcript', item.kind.value, item.value))
    return issues


def _declared(item: Candidate, allowed: set[Candidate]) -> bool:
    return any(_equivalent(item, candidate) for candidate in allowed)


def _equivalent(left: Candidate, right: Candidate) -> bool:
    if left.kind != right.kind:
        return False
    if left.kind == CandidateKind.DATE:
        if 'T' in left.value and 'T' in right.value:
            try:
                return datetime.fromisoformat(left.value.replace('Z', '+00:00')) == datetime.fromisoformat(right.value.replace('Z', '+00:00'))
            except ValueError:
                return False
        return _date(left.value) == _date(right.value)
    if left.kind == CandidateKind.FIGURE:
        return left.value.split('/')[0] == right.value.split('/')[0]
    return left.value == right.value


def _date(value: str) -> str:
    if '/' in value:
        try:
            return datetime.strptime(value, '%d/%m/%Y').date().isoformat()
        except ValueError:
            return value
    return value[:10]
