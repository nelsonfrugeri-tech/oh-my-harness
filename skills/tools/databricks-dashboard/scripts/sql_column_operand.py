"""Normalize SQL identifier paths used as comparison operands."""

from __future__ import annotations

from dataclasses import dataclass

from sql_tokenizer import SqlToken, TokenKind


@dataclass(frozen=True)
class ColumnOperand:
    """Case-normalized qualified or unqualified column operand."""

    parts: tuple[str, ...]

    @classmethod
    def starting_at(
        cls, tokens: tuple[SqlToken, ...], start: int, end: int
    ) -> "ColumnOperand":
        if start >= end or not tokens[start].is_identifier:
            return cls(())
        parts = [tokens[start].value.lower()]
        position = start + 1
        while position + 1 < end:
            if tokens[position].kind is not TokenKind.DOT:
                break
            if not tokens[position + 1].is_identifier:
                break
            parts.append(tokens[position + 1].value.lower())
            position += 2
        return cls(tuple(parts))

    @classmethod
    def ending_at(
        cls, tokens: tuple[SqlToken, ...], end: int, start: int
    ) -> "ColumnOperand":
        if end < start or not tokens[end].is_identifier:
            return cls(())
        parts = [tokens[end].value.lower()]
        position = end - 1
        while position - 1 >= start:
            if tokens[position].kind is not TokenKind.DOT:
                break
            if not tokens[position - 1].is_identifier:
                break
            parts.insert(0, tokens[position - 1].value.lower())
            position -= 2
        return cls(tuple(parts))

    @property
    def exists(self) -> bool:
        return bool(self.parts)

    def is_same_source(self, other: "ColumnOperand") -> bool:
        if not self.exists or not other.exists:
            return False
        if self.parts[-1] != other.parts[-1]:
            return False
        return (
            len(self.parts) == 1
            or len(other.parts) == 1
            or self.parts == other.parts
        )

    def is_referenced_in(
        self, tokens: tuple[SqlToken, ...], start: int, end: int
    ) -> bool:
        """Return whether an operand expression references this source column."""
        for position in range(start, end):
            if not _starts_column_path(tokens, position, start):
                continue
            candidate = ColumnOperand.starting_at(tokens, position, end)
            after_path = position + (len(candidate.parts) * 2) - 1
            is_function = (
                after_path < end
                and tokens[after_path].kind is TokenKind.LEFT_PAREN
            )
            if not is_function and self.is_same_source(candidate):
                return True
        return False


def _starts_column_path(
    tokens: tuple[SqlToken, ...], position: int, start: int
) -> bool:
    if not tokens[position].is_identifier:
        return False
    if position == start:
        return True
    previous = tokens[position - 1]
    return previous.kind is not TokenKind.DOT and previous.value != ":"
