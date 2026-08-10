"""Detect sensitive Databricks function calls from lexical tokens."""

from __future__ import annotations

from sql_tokenizer import SqlToken, TokenKind

_SENSITIVE_FUNCTIONS = frozenset(("secret", "try_secret"))
_SECRET_ERROR = "must not call secret or try_secret functions"
_IDENTIFIER_ERROR = "must not use dynamic IDENTIFIER calls"


def sensitive_function_errors(tokens: tuple[SqlToken, ...]) -> tuple[str, ...]:
    """Return an error when a sensitive function is invoked."""
    errors: list[str] = []
    for position, token in enumerate(tokens[:-1]):
        if not token.is_identifier:
            continue
        if tokens[position + 1].kind is not TokenKind.LEFT_PAREN:
            continue
        name = token.value.lower()
        if name in _SENSITIVE_FUNCTIONS:
            errors.append(_SECRET_ERROR)
        elif name == "identifier":
            errors.append(_IDENTIFIER_ERROR)
    return tuple(dict.fromkeys(errors))
