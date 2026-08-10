"""Navigate comparison operators and BETWEEN bounds."""

from __future__ import annotations

from sql_parentheses import closing_parenthesis
from sql_tokenizer import SqlToken, TokenKind

_COMPARISON_CHARACTERS = frozenset(("<", ">", "=", "!"))


class ComparisonTokens:
    """Provide structural token positions for comparison parsing."""

    @staticmethod
    def is_operator(token: SqlToken) -> bool:
        return token.kind is TokenKind.OTHER and token.value in _COMPARISON_CHARACTERS

    @classmethod
    def after_operator(
        cls, tokens: tuple[SqlToken, ...], position: int, end: int
    ) -> int:
        while position < end and cls.is_operator(tokens[position]):
            position += 1
        return position

    @classmethod
    def before_operator(
        cls, tokens: tuple[SqlToken, ...], position: int, start: int
    ) -> int:
        while position >= start and cls.is_operator(tokens[position]):
            position -= 1
        return position

    @staticmethod
    def between_conjunction(
        tokens: tuple[SqlToken, ...], start: int, end: int
    ) -> int:
        position = start
        while position < end:
            if tokens[position].kind is TokenKind.LEFT_PAREN:
                position = closing_parenthesis(tokens, position, end) + 1
                continue
            if tokens[position].is_keyword("AND"):
                return position
            position += 1
        return end

    @staticmethod
    def expression_end(
        tokens: tuple[SqlToken, ...], start: int, end: int
    ) -> int:
        position = start
        while position < end:
            if tokens[position].kind is TokenKind.LEFT_PAREN:
                position = closing_parenthesis(tokens, position, end) + 1
                continue
            if tokens[position].is_keyword("AND"):
                return position
            position += 1
        return end

    @staticmethod
    def expression_start(
        tokens: tuple[SqlToken, ...], start: int, end: int
    ) -> int:
        expression_start = start
        position = start
        while position < end:
            if tokens[position].kind is TokenKind.LEFT_PAREN:
                position = closing_parenthesis(tokens, position, end) + 1
                continue
            if tokens[position].is_keyword("AND"):
                expression_start = position + 1
            position += 1
        return expression_start
