"""Recognize temporal predicates on direct external-source query scopes."""

from __future__ import annotations

from sql_parentheses import closing_parenthesis
from sql_temporal_comparison import inspect_temporal_comparisons
from sql_tokenizer import SqlToken, TokenKind

_BOUNDARIES = frozenset(
    (
        "GROUP",
        "HAVING",
        "QUALIFY",
        "ORDER",
        "LIMIT",
        "WINDOW",
        "UNION",
        "INTERSECT",
        "EXCEPT",
    )
)
_ERROR = "must include a recognized temporal predicate for external sources"
_OR_ERROR = "must not use OR predicates in portable SQL"
_SELF_ERROR = "must not compare a temporal column to itself"


def temporal_filter_errors(
    tokens: tuple[SqlToken, ...], start: int, end: int
) -> tuple[str, ...]:
    """Require a temporal predicate when this branch reads a direct external source."""
    external_source, where_start = _branch_shape(tokens, start, end)
    if where_start < 0:
        return ()
    where_end = _where_end(tokens, where_start, end)
    errors = (_OR_ERROR,) if _contains_or(tokens, where_start, where_end) else ()
    comparison = inspect_temporal_comparisons(tokens, where_start, where_end)
    if external_source and comparison.self_reference:
        errors += (_SELF_ERROR,)
    elif external_source and not comparison.safe:
        errors += (_ERROR,)
    return errors


def _branch_shape(
    tokens: tuple[SqlToken, ...], start: int, end: int
) -> tuple[bool, int]:
    external_source = False
    where_start = -1
    position = start
    while position < end:
        token = tokens[position]
        if token.kind is TokenKind.LEFT_PAREN:
            position = closing_parenthesis(tokens, position, end) + 1
            continue
        if token.is_keyword("FROM") or token.is_keyword("JOIN"):
            external_source |= _is_external_relation(tokens, position + 1, end)
        elif token.is_keyword("WHERE"):
            where_start = position + 1
        position += 1
    return external_source, where_start


def _is_external_relation(
    tokens: tuple[SqlToken, ...], start: int, end: int
) -> bool:
    if start >= end or not tokens[start].is_identifier:
        return False
    parts = 1
    position = start + 1
    while position + 1 < end:
        if tokens[position].kind is not TokenKind.DOT:
            break
        if not tokens[position + 1].is_identifier:
            break
        parts += 1
        position += 2
    return parts == 3


def _where_end(tokens: tuple[SqlToken, ...], start: int, end: int) -> int:
    position = start
    while position < end:
        token = tokens[position]
        if token.kind is TokenKind.LEFT_PAREN:
            position = closing_parenthesis(tokens, position, end) + 1
            continue
        if token.kind is TokenKind.WORD and token.value.upper() in _BOUNDARIES:
            return position
        position += 1
    return end


def _contains_or(tokens: tuple[SqlToken, ...], start: int, end: int) -> bool:
    return any(token.is_keyword("OR") for token in tokens[start:end])
