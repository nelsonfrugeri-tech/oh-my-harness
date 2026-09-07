from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


_TABLE_HEADER: Final = re.compile(r"^\s*\[\[?.+\]\]?\s*(?:#.*)?$")


@dataclass(frozen=True)
class _State:
    multiline_quote: str = ""
    square_depth: int = 0
    curly_depth: int = 0


def split_root(content: str) -> tuple[str, str]:
    """Split TOML root keys from tables without mistaking compound values for headers."""
    state = _State()
    offset = 0
    for line in content.splitlines(keepends=True):
        if _is_table_header(line, state):
            return content[:offset], content[offset:]
        state = _scan_line(line, state)
        offset += len(line)
    return content, ""


def top_level_lines(content: str) -> tuple[str, ...]:
    """Return lexical top-level lines, excluding multiline strings and compound values."""
    state = _State()
    result: list[str] = []
    for line in content.splitlines():
        if not state.multiline_quote and state.square_depth == 0 and state.curly_depth == 0:
            result.append(line)
        state = _scan_line(line, state)
    return tuple(result)


def _is_table_header(line: str, state: _State) -> bool:
    return (
        not state.multiline_quote
        and state.square_depth == 0
        and state.curly_depth == 0
        and _TABLE_HEADER.match(line) is not None
    )


def _scan_line(line: str, state: _State) -> _State:
    quote = state.multiline_quote
    square = state.square_depth
    curly = state.curly_depth
    index = 0
    while index < len(line):
        if quote:
            index, quote = _close_multiline(line, index, quote)
            continue
        if line[index] == "#":
            break
        if line.startswith(('"""', "'''"), index):
            quote = line[index : index + 3]
            index += 3
            continue
        if line[index] in "\"'":
            index = _skip_string(line, index, line[index])
            continue
        square += (line[index] == "[") - (line[index] == "]")
        curly += (line[index] == "{") - (line[index] == "}")
        index += 1
    return _State(quote, max(square, 0), max(curly, 0))


def _close_multiline(line: str, index: int, quote: str) -> tuple[int, str]:
    closing = line.find(quote, index)
    if closing < 0:
        return len(line), quote
    if quote == '"""' and _is_escaped(line, closing):
        return closing + 1, quote
    return closing + 3, ""


def _skip_string(line: str, index: int, quote: str) -> int:
    cursor = index + 1
    while cursor < len(line):
        if line[cursor] == quote and (quote == "'" or not _is_escaped(line, cursor)):
            return cursor + 1
        cursor += 1
    return cursor


def _is_escaped(line: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and line[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1
