"""Inspect explicit comparisons involving temporal source columns."""

from __future__ import annotations

from dataclasses import dataclass

from sql_column_operand import ColumnOperand
from sql_comparison_tokens import ComparisonTokens
from sql_parentheses import closing_parenthesis
from sql_temporal_names import is_temporal_column_name
from sql_tokenizer import SqlToken, TokenKind

_LITERAL_KEYWORDS = frozenset(("DATE", "DATETIME", "TIME", "TIMESTAMP"))


@dataclass(frozen=True)
class TemporalComparisonInspection:
    safe: bool = False
    self_reference: bool = False

    def merged(
        self, other: "TemporalComparisonInspection"
    ) -> "TemporalComparisonInspection":
        return TemporalComparisonInspection(
            self.safe or other.safe,
            self.self_reference or other.self_reference,
        )


def inspect_temporal_comparisons(
    tokens: tuple[SqlToken, ...], start: int, end: int
) -> TemporalComparisonInspection:
    """Classify temporal comparisons and self-referential bounds."""
    result = TemporalComparisonInspection()
    position = start
    while position < end:
        token = tokens[position]
        if token.kind is TokenKind.LEFT_PAREN:
            closing = closing_parenthesis(tokens, position, end)
            nested = position + 1
            if nested < closing and not tokens[nested].starts_query:
                result = result.merged(
                    inspect_temporal_comparisons(tokens, nested, closing)
                )
            position = closing + 1
            continue
        if _is_temporal_column(tokens, position, end):
            result = result.merged(_inspect_column(tokens, position, start, end))
        position += 1
    return result


def _is_temporal_column(
    tokens: tuple[SqlToken, ...], position: int, end: int
) -> bool:
    token = tokens[position]
    if not token.is_identifier or not is_temporal_column_name(token.value):
        return False
    if position + 1 >= end:
        return True
    next_token = tokens[position + 1]
    if next_token.kind in {TokenKind.DOT, TokenKind.LEFT_PAREN}:
        return False
    return not (
        token.kind is TokenKind.WORD
        and token.value.upper() in _LITERAL_KEYWORDS
        and next_token.kind is TokenKind.STRING
    )


def _inspect_column(
    tokens: tuple[SqlToken, ...], position: int, start: int, end: int
) -> TemporalComparisonInspection:
    source = ColumnOperand.ending_at(tokens, position, start)
    if position + 1 < end and tokens[position + 1].is_keyword("BETWEEN"):
        return _inspect_between(tokens, source, position + 2, end)
    if position + 1 < end and ComparisonTokens.is_operator(tokens[position + 1]):
        other_start = ComparisonTokens.after_operator(tokens, position + 1, end)
        other_end = ComparisonTokens.expression_end(tokens, other_start, end)
        return _classify_expression(tokens, source, other_start, other_end)
    if position > start and ComparisonTokens.is_operator(tokens[position - 1]):
        other_end = ComparisonTokens.before_operator(tokens, position - 1, start)
        other_start = ComparisonTokens.expression_start(tokens, start, other_end + 1)
        return _classify_expression(tokens, source, other_start, other_end + 1)
    return TemporalComparisonInspection()


def _inspect_between(
    tokens: tuple[SqlToken, ...], source: ColumnOperand, start: int, end: int
) -> TemporalComparisonInspection:
    conjunction = ComparisonTokens.between_conjunction(tokens, start, end)
    if conjunction >= end or start >= conjunction or conjunction + 1 >= end:
        return TemporalComparisonInspection()
    upper_start = conjunction + 1
    upper_end = ComparisonTokens.expression_end(tokens, upper_start, end)
    self_reference = source.is_referenced_in(tokens, start, conjunction)
    self_reference |= source.is_referenced_in(tokens, upper_start, upper_end)
    return TemporalComparisonInspection(not self_reference, self_reference)


def _classify_expression(
    tokens: tuple[SqlToken, ...],
    source: ColumnOperand,
    start: int,
    end: int,
) -> TemporalComparisonInspection:
    if start >= end:
        return TemporalComparisonInspection()
    self_reference = source.is_referenced_in(tokens, start, end)
    return TemporalComparisonInspection(not self_reference, self_reference)
