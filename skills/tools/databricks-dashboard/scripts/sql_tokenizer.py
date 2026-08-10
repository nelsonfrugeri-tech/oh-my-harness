"""Tokenize the SQL subset needed for fail-closed relation inspection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from sql_comment_lexer import strip_sql_comments


class TokenKind(Enum):
    WORD = "word"
    QUOTED_IDENTIFIER = "quoted_identifier"
    STRING = "string"
    DOT = "dot"
    LEFT_PAREN = "left_paren"
    RIGHT_PAREN = "right_paren"
    COMMA = "comma"
    OTHER = "other"


@dataclass(frozen=True)
class SqlToken:
    kind: TokenKind
    value: str

    def is_keyword(self, keyword: str) -> bool:
        return self.kind is TokenKind.WORD and self.value.upper() == keyword

    @property
    def is_identifier(self) -> bool:
        return self.kind in {TokenKind.WORD, TokenKind.QUOTED_IDENTIFIER}

    @property
    def starts_query(self) -> bool:
        return self.is_keyword("SELECT") or self.is_keyword("WITH")


_PUNCTUATION: Final = {
    ".": TokenKind.DOT,
    "(": TokenKind.LEFT_PAREN,
    ")": TokenKind.RIGHT_PAREN,
    ",": TokenKind.COMMA,
}
_QUOTES: Final = {
    "'": TokenKind.STRING,
    '"': TokenKind.QUOTED_IDENTIFIER,
    "`": TokenKind.QUOTED_IDENTIFIER,
}


def tokenize_sql(sql: str) -> tuple[SqlToken, ...]:
    """Return comment-free tokens while preserving quoted lexical units."""
    return _SqlTokenizer(strip_sql_comments(sql)).tokenize()


class _SqlTokenizer:
    def __init__(self, sql: str) -> None:
        self._sql = sql
        self._position = 0

    def tokenize(self) -> tuple[SqlToken, ...]:
        tokens: list[SqlToken] = []
        while self._position < len(self._sql):
            self._skip_whitespace()
            if self._position < len(self._sql):
                tokens.append(self._next_token())
        return tuple(tokens)

    def _skip_whitespace(self) -> None:
        while self._position < len(self._sql) and self._sql[self._position].isspace():
            self._position += 1

    def _next_token(self) -> SqlToken:
        character = self._sql[self._position]
        quoted_kind = _QUOTES.get(character)
        if quoted_kind is not None:
            return self._read_quoted(character, quoted_kind)
        if _is_word_character(character):
            return self._read_word()
        self._position += 1
        return SqlToken(_PUNCTUATION.get(character, TokenKind.OTHER), character)

    def _read_word(self) -> SqlToken:
        start = self._position
        while self._position < len(self._sql):
            if not _is_word_character(self._sql[self._position]):
                break
            self._position += 1
        return SqlToken(TokenKind.WORD, self._sql[start : self._position])

    def _read_quoted(self, delimiter: str, kind: TokenKind) -> SqlToken:
        start = self._position + 1
        self._position += 1
        while self._position < len(self._sql):
            if self._consume_quoted_character(delimiter):
                break
        value = self._sql[start : self._position - 1]
        return SqlToken(kind, value.replace(delimiter * 2, delimiter))

    def _consume_quoted_character(self, delimiter: str) -> bool:
        character = self._sql[self._position]
        if character == "\\" and delimiter in {"'", '"'}:
            self._position += 2
            return False
        self._position += 1
        if character != delimiter:
            return False
        if self._position < len(self._sql) and self._sql[self._position] == delimiter:
            self._position += 1
            return False
        return True


def _is_word_character(character: str) -> bool:
    return character.isalnum() or character in "_$-"
