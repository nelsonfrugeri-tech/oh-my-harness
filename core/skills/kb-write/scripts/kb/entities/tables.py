import re
from collections.abc import Mapping
from datetime import datetime

from .currencies import ISO_CURRENCIES
from .kinds import EntityKind, SINGULAR_KINDS
from .model import DateEntry, Entity, EntityTables, Figure, TimelineEntry, Violation
from .numbers import parse_number
from .secrets import find_secrets

TABLE_HEADERS = {
    'Entities': ('Entidade', 'Tipo', 'Quem/o que é', 'Relação', 'Período', 'Fonte'),
    'Dates': ('Data', 'O que é', 'Quem', 'Status', 'Fonte'),
    'Figures': ('Valor', 'Unidade', 'O que mede', 'Quando', 'Fonte'),
    'Timeline': ('Quando', 'Quem', 'O quê', 'Como', 'Evidência'),
}


def parse_tables(sections: Mapping[str, str]) -> EntityTables:
    """Parse conditional tables; malformed rows produce explicit violations."""
    issues: list[Violation] = []
    entities: list[Entity] = []
    dates: list[DateEntry] = []
    figures: list[Figure] = []
    timeline: list[TimelineEntry] = []
    for name, headers in TABLE_HEADERS.items():
        if name not in sections:
            continue
        rows, errors = _rows(name, sections[name], headers)
        issues.extend(errors)
        for row in rows:
            issue = _validate_row(name, row)
            if issue:
                issues.append(issue)
            elif name == 'Entities':
                kind = SINGULAR_KINDS.get(row[1]) or EntityKind(row[1])
                entities.append(Entity(kind, row[0], *row[2:]))
            elif name == 'Dates':
                dates.append(DateEntry(*row))
            elif name == 'Figures':
                amount = parse_number(row[0])
                assert amount is not None
                figures.append(Figure(amount, *row[1:]))
            else:
                timeline.append(TimelineEntry(*row))
    return EntityTables(tuple(entities), tuple(dates), tuple(figures), tuple(timeline), tuple(issues))


def _cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip().strip('`') for cell in re.split(r'(?<!\\)\|', line.strip().strip('|')))


def _rows(name: str, text: str, headers: tuple[str, ...]) -> tuple[list[tuple[str, ...]], list[Violation]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2 or _cells(lines[0]) != headers:
        return [], [Violation('table-header', name, 'Cabeçalho inválido.')]
    separator = _cells(lines[1])
    if len(separator) != len(headers) or not all(re.fullmatch(r':?-{3,}:?', cell) for cell in separator):
        return [], [Violation('table-separator', name, 'Separador de tabela inválido.')]
    rows: list[tuple[str, ...]] = []
    issues: list[Violation] = []
    for line in lines[2:]:
        cells = _cells(line)
        if len(cells) != len(headers) or not all(cells):
            issues.append(Violation('table-row', name, 'Linha incompleta ou inválida.'))
        elif cells in rows:
            issues.append(Violation('table-duplicate', name, 'Linha duplicada.'))
        else:
            rows.append(cells)
    return rows, issues


def _validate_row(name: str, row: tuple[str, ...]) -> Violation | None:
    if any(find_secrets(cell) for cell in row):
        return Violation('secret', name, 'Dado sensível recusado.')
    if name == 'Entities':
        if row[1] not in SINGULAR_KINDS and row[1] not in {kind.value for kind in EntityKind}:
            return Violation('entity-kind', name, 'Tipo de entidade desconhecido.')
        return None
    at = row[3] if name == 'Figures' else row[0]
    if not _rfc3339(at):
        return Violation('timestamp', name, 'Data deve ser RFC 3339 com fuso.')
    if name != 'Figures':
        return None
    if parse_number(row[0]) is None:
        return Violation('figure-number', name, 'Valor numérico inválido.')
    unit = row[1].split('/')[0]
    if (re.fullmatch(r'[A-Z]{3}', unit) or unit in {'R$', '$', '€'}) and unit not in ISO_CURRENCIES:
        return Violation('currency', name, 'Moeda deve usar código ISO 4217.')
    return None


def _rfc3339(value: str) -> bool:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
        return False
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).utcoffset() is not None
    except ValueError:
        return False
