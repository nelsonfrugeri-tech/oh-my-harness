"""Scope-aware query policy inspection over SQL tokens."""

from __future__ import annotations

from sql_ctes import parse_ctes
from sql_parentheses import closing_parenthesis
from sql_sensitive_functions import sensitive_function_errors
from sql_temporal_predicate import temporal_filter_errors
from sql_tokenizer import SqlToken, TokenKind, tokenize_sql

_SET_OPERATORS = frozenset(("UNION", "INTERSECT", "EXCEPT"))
_FROM_BOUNDARIES = frozenset(
    ("WHERE", "GROUP", "HAVING", "QUALIFY", "ORDER", "LIMIT", "WINDOW")
)


def query_policy_errors(sql: str) -> tuple[str, ...]:
    """Return filter and join-policy failures for every query scope."""
    tokens = tokenize_sql(sql)
    return tuple(
        dict.fromkeys(
            _QueryPolicyParser(tokens).inspect() + sensitive_function_errors(tokens)
        )
    )


class _QueryPolicyParser:
    def __init__(self, tokens: tuple[SqlToken, ...]) -> None:
        self._tokens = tokens
        self._errors: list[str] = []

    def inspect(self) -> tuple[str, ...]:
        self._inspect_scope(0, len(self._tokens))
        return tuple(dict.fromkeys(self._errors))

    def _inspect_scope(self, start: int, end: int) -> None:
        layout = parse_ctes(self._tokens, start, end)
        for span_start, span_end in layout.spans:
            self._inspect_scope(span_start, span_end)
        self._inspect_branch(layout.body_start, end)

    def _inspect_branch(self, start: int, end: int) -> None:
        has_filter = False
        in_from_clause = False
        position = start
        while position < end:
            token = self._tokens[position]
            if token.kind is TokenKind.LEFT_PAREN:
                position = self._inspect_parenthesized(position, end)
                continue
            if self._is_set_operator(token):
                self._finish_branch(start, position, has_filter)
                self._inspect_branch(_next_branch(self._tokens, position + 1, end), end)
                return
            if token.is_keyword("FROM"):
                in_from_clause = True
            elif token.is_keyword("WHERE"):
                has_filter = True
                in_from_clause = False
            elif _is_from_boundary(token):
                in_from_clause = False
            elif token.kind is TokenKind.COMMA and in_from_clause:
                self._errors.append("must use explicit JOIN syntax")
            position += 1
        self._finish_branch(start, end, has_filter)

    def _inspect_parenthesized(self, opening: int, end: int) -> int:
        closing = closing_parenthesis(self._tokens, opening, end)
        nested_start = opening + 1
        if nested_start < closing and self._tokens[nested_start].starts_query:
            self._inspect_scope(nested_start, closing)
        return min(closing + 1, end)

    def _finish_branch(self, start: int, end: int, has_filter: bool) -> None:
        if not has_filter:
            self._errors.append("must include an explicit filter")
        self._errors.extend(temporal_filter_errors(self._tokens, start, end))

    @staticmethod
    def _is_set_operator(token: SqlToken) -> bool:
        return token.kind is TokenKind.WORD and token.value.upper() in _SET_OPERATORS


def _is_from_boundary(token: SqlToken) -> bool:
    return token.kind is TokenKind.WORD and token.value.upper() in _FROM_BOUNDARIES


def _next_branch(tokens: tuple[SqlToken, ...], position: int, end: int) -> int:
    if position >= end:
        return end
    if tokens[position].is_keyword("ALL") or tokens[position].is_keyword("DISTINCT"):
        return position + 1
    return position
