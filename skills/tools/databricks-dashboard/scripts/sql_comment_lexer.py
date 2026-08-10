"""Lex SQL comments without interpreting markers inside quoted text."""

from __future__ import annotations

from enum import Enum
from typing import Callable, Final


class _Mode(Enum):
    NORMAL = "input"
    SINGLE_QUOTE = "single-quoted string"
    DOUBLE_QUOTE = "double-quoted identifier"
    BACKTICK = "backtick-quoted identifier"
    LINE_COMMENT = "line comment"
    BLOCK_COMMENT = "block comment"


_COMMENT_OPENERS: Final = {"--": _Mode.LINE_COMMENT, "/*": _Mode.BLOCK_COMMENT}
_QUOTE_OPENERS: Final = {
    "'": _Mode.SINGLE_QUOTE,
    '"': _Mode.DOUBLE_QUOTE,
    "`": _Mode.BACKTICK,
}
_DELIMITERS: Final = {
    _Mode.SINGLE_QUOTE: "'",
    _Mode.DOUBLE_QUOTE: '"',
    _Mode.BACKTICK: "`",
}
_BACKSLASH_ESCAPES: Final = frozenset({_Mode.SINGLE_QUOTE, _Mode.DOUBLE_QUOTE})
_LINE_BREAKS: Final = frozenset({"\n", "\r"})


def strip_sql_comments(sql: str) -> str:
    """Remove real SQL comments and reject unterminated lexical structures."""
    return _SqlCommentLexer(sql).strip()


class _SqlCommentLexer:
    def __init__(self, sql: str) -> None:
        self._sql = sql
        self._position = 0
        self._mode = _Mode.NORMAL
        self._output: list[str] = []
        self._scanners: dict[_Mode, Callable[[], None]] = {
            _Mode.NORMAL: self._scan_normal,
            _Mode.SINGLE_QUOTE: self._scan_quoted,
            _Mode.DOUBLE_QUOTE: self._scan_quoted,
            _Mode.BACKTICK: self._scan_quoted,
            _Mode.LINE_COMMENT: self._scan_line_comment,
            _Mode.BLOCK_COMMENT: self._scan_block_comment,
        }

    def strip(self) -> str:
        while self._position < len(self._sql):
            self._scanners[self._mode]()
        self._ensure_terminated()
        return "".join(self._output)

    def _scan_normal(self) -> None:
        opener = self._sql[self._position : self._position + 2]
        comment_mode = _COMMENT_OPENERS.get(opener)
        if comment_mode is not None:
            self._output.append(" ")
            self._mode = comment_mode
            self._position += 2
            return
        character = self._sql[self._position]
        self._mode = _QUOTE_OPENERS.get(character, _Mode.NORMAL)
        self._output.append(character)
        self._position += 1

    def _scan_quoted(self) -> None:
        character = self._sql[self._position]
        self._output.append(character)
        if character == "\\" and self._mode in _BACKSLASH_ESCAPES:
            self._copy_next_character()
            return
        delimiter = _DELIMITERS[self._mode]
        if character != delimiter:
            self._position += 1
            return
        if self._peek() == delimiter:
            self._copy_next_character()
            return
        self._mode = _Mode.NORMAL
        self._position += 1

    def _scan_line_comment(self) -> None:
        character = self._sql[self._position]
        if character in _LINE_BREAKS:
            self._output.append(character)
            self._mode = _Mode.NORMAL
        self._position += 1

    def _scan_block_comment(self) -> None:
        if self._sql.startswith("*/", self._position):
            self._mode = _Mode.NORMAL
            self._position += 2
            return
        character = self._sql[self._position]
        if character in _LINE_BREAKS:
            self._output.append(character)
        self._position += 1

    def _copy_next_character(self) -> None:
        next_position = self._position + 1
        if next_position < len(self._sql):
            self._output.append(self._sql[next_position])
        self._position += 2

    def _peek(self) -> str:
        return self._sql[self._position + 1 : self._position + 2]

    def _ensure_terminated(self) -> None:
        if self._mode in {_Mode.NORMAL, _Mode.LINE_COMMENT}:
            return
        raise ValueError(f"unterminated SQL {self._mode.value}")
