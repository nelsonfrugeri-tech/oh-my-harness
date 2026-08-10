"""Parse local CTE declarations without leaking names across query scopes."""

from __future__ import annotations

from dataclasses import dataclass

from sql_parentheses import closing_parenthesis
from sql_tokenizer import SqlToken, TokenKind

NameKey = tuple[bool, str]
_Span = tuple[int, int]


@dataclass(frozen=True)
class CteLayout:
    names: frozenset[NameKey]
    spans: tuple[_Span, ...]
    body_start: int


def parse_ctes(tokens: tuple[SqlToken, ...], start: int, end: int) -> CteLayout:
    """Return CTE names, query spans, and the outer query body position."""
    if start >= end or not tokens[start].is_keyword("WITH"):
        return CteLayout(frozenset(), (), start)
    return _read_ctes(tokens, start + 1, end)


def _read_ctes(tokens: tuple[SqlToken, ...], start: int, end: int) -> CteLayout:
    cursor = _skip_recursive(tokens, start, end)
    names: list[NameKey] = []
    spans: list[_Span] = []
    while cursor < end and tokens[cursor].is_identifier:
        name = tokens[cursor]
        cursor = _skip_column_names(tokens, cursor + 1, end)
        _require_keyword(tokens, cursor, end, "AS")
        cursor += 1
        _require_kind(tokens, cursor, end, TokenKind.LEFT_PAREN)
        closing = closing_parenthesis(tokens, cursor, end)
        names.append(name_key(name))
        spans.append((cursor + 1, closing))
        cursor = closing + 1
        if cursor >= end or tokens[cursor].kind is not TokenKind.COMMA:
            break
        cursor += 1
    return CteLayout(frozenset(names), tuple(spans), cursor)


def _skip_recursive(tokens: tuple[SqlToken, ...], position: int, end: int) -> int:
    if position < end and tokens[position].is_keyword("RECURSIVE"):
        return position + 1
    return position


def _skip_column_names(
    tokens: tuple[SqlToken, ...], position: int, end: int
) -> int:
    if position >= end or tokens[position].kind is not TokenKind.LEFT_PAREN:
        return position
    return closing_parenthesis(tokens, position, end) + 1


def _require_keyword(
    tokens: tuple[SqlToken, ...], position: int, end: int, keyword: str
) -> None:
    if position >= end or not tokens[position].is_keyword(keyword):
        raise ValueError("SQL contains an invalid CTE declaration")


def _require_kind(
    tokens: tuple[SqlToken, ...], position: int, end: int, kind: TokenKind
) -> None:
    if position >= end or tokens[position].kind is not kind:
        raise ValueError("SQL contains an invalid CTE declaration")


def name_key(token: SqlToken) -> NameKey:
    quoted = token.kind is TokenKind.QUOTED_IDENTIFIER
    return quoted, token.value if quoted else token.value.lower()
