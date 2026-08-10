"""Match structural SQL parentheses from lexical tokens."""

from __future__ import annotations

from sql_tokenizer import SqlToken, TokenKind


def closing_parenthesis(
    tokens: tuple[SqlToken, ...], opening: int, end: int
) -> int:
    """Return the matching closing position or reject unbalanced SQL."""
    depth = 0
    for position in range(opening, end):
        kind = tokens[position].kind
        depth += kind is TokenKind.LEFT_PAREN
        depth -= kind is TokenKind.RIGHT_PAREN
        if depth == 0:
            return position
    raise ValueError("SQL contains unbalanced parentheses")
