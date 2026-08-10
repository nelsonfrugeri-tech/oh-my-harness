"""Inspect SQL relation nodes recursively with CTE-aware scope."""

from __future__ import annotations

from dataclasses import dataclass

from sql_ctes import NameKey, name_key, parse_ctes
from sql_parentheses import closing_parenthesis
from sql_tokenizer import SqlToken, TokenKind, tokenize_sql


@dataclass(frozen=True)
class RelationInspection:
    sources: tuple[str, ...]
    errors: tuple[str, ...]


def inspect_relations(sql: str) -> RelationInspection:
    """Return static external sources and unsupported relation errors."""
    return _RelationParser(tokenize_sql(sql)).inspect()


class _RelationParser:
    def __init__(self, tokens: tuple[SqlToken, ...]) -> None:
        self._tokens = tokens
        self._sources: list[str] = []
        self._errors: list[str] = []

    def inspect(self) -> RelationInspection:
        try:
            self._inspect_scope(0, len(self._tokens), frozenset())
        except ValueError as error:
            self._errors.append(str(error))
        return RelationInspection(
            tuple(dict.fromkeys(self._sources)),
            tuple(dict.fromkeys(self._errors)),
        )

    def _inspect_scope(
        self, start: int, end: int, inherited: frozenset[NameKey]
    ) -> None:
        layout = parse_ctes(self._tokens, start, end)
        available = inherited | layout.names
        for span_start, span_end in layout.spans:
            self._inspect_scope(span_start, span_end, available)
        self._scan_body(layout.body_start, end, available)

    def _scan_body(
        self, start: int, end: int, cte_names: frozenset[NameKey]
    ) -> None:
        position = start
        while position < end:
            token = self._tokens[position]
            if token.kind is TokenKind.LEFT_PAREN:
                position = self._inspect_parenthesized(position, end, cte_names)
                continue
            if token.is_keyword("FROM") or token.is_keyword("JOIN"):
                position = self._inspect_relation(position + 1, end, cte_names)
                continue
            position += 1

    def _inspect_parenthesized(
        self, opening: int, end: int, cte_names: frozenset[NameKey]
    ) -> int:
        closing = closing_parenthesis(self._tokens, opening, end)
        position = opening + 1
        if position < closing and self._tokens[position].starts_query:
            self._inspect_scope(position, closing, cte_names)
            return min(closing + 1, end)
        while position < closing:
            if self._tokens[position].kind is TokenKind.LEFT_PAREN:
                position = self._inspect_parenthesized(position, closing, cte_names)
                continue
            position += 1
        return min(closing + 1, end)

    def _inspect_relation(
        self, start: int, end: int, cte_names: frozenset[NameKey]
    ) -> int:
        if start >= end:
            self._errors.append("source relation is missing")
            return end
        if self._tokens[start].kind is TokenKind.LEFT_PAREN:
            next_position = start + 1
            if next_position >= end or not self._tokens[next_position].starts_query:
                self._errors.append("parenthesized source must be a SELECT query")
            return start
        if not self._tokens[start].is_identifier:
            self._errors.append("source relation must be a static identifier")
            return start + 1
        parts, cursor = self._relation_parts(start, end)
        label = ".".join(token.value for token in parts)
        if cursor < end and self._tokens[cursor].kind is TokenKind.LEFT_PAREN:
            self._errors.append(f"table-valued functions are not allowed: {label}")
            return cursor
        if len(parts) == 1 and name_key(parts[0]) in cte_names:
            return cursor
        if len(parts) == 3:
            self._sources.append(label)
            return cursor
        self._errors.append(
            f"source relation must use static catalog.schema.table: {label}"
        )
        return cursor

    def _relation_parts(self, start: int, end: int) -> tuple[tuple[SqlToken, ...], int]:
        parts = [self._tokens[start]]
        cursor = start + 1
        while cursor + 1 < end and self._is_qualified_part(cursor):
            parts.append(self._tokens[cursor + 1])
            cursor += 2
        return tuple(parts), cursor

    def _is_qualified_part(self, position: int) -> bool:
        return (
            self._tokens[position].kind is TokenKind.DOT
            and self._tokens[position + 1].is_identifier
        )
