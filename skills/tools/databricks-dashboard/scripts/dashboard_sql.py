"""Fail-closed SQL inspection for portable dashboard datasets."""

from __future__ import annotations

import re

from sql_comment_lexer import strip_sql_comments
from sql_query_policy import query_policy_errors
from sql_relations import RelationInspection, inspect_relations

_READ_ONLY = re.compile(r"^\s*(WITH\b[\s\S]+?\bSELECT\b|SELECT\b)", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(ALTER|COPY|CREATE|DELETE|DROP|INSERT|MERGE|TRUNCATE|UPDATE)\b", re.IGNORECASE
)
_DYNAMIC_SOURCE = re.compile(
    r"\b(?:FROM|JOIN)\s+(?:IDENTIFIER\s*\(|\$\{|:[\w$-]+)", re.IGNORECASE
)


def extract_sources(sql: str) -> tuple[str, ...]:
    """Return all fully qualified source relations outside SQL comments."""
    try:
        return inspect_relations(sql).sources
    except ValueError:
        return ()


def sql_errors(name: str, sql: str) -> tuple[str, ...]:
    try:
        sanitized = sanitize(sql)
        relation_inspection = inspect_relations(sanitized)
        query_errors = query_policy_errors(sanitized)
    except ValueError as error:
        return (f"dataset {name} has invalid SQL: {error}",)
    checks = (
        (
            _READ_ONLY.match(sanitized) and not _FORBIDDEN.search(sanitized),
            "must use read-only SELECT SQL",
        ),
        (";" not in sanitized.rstrip(";"), "must contain one statement"),
        (
            not re.search(r"\bSELECT\s+\*", sanitized, re.IGNORECASE),
            "must not use SELECT *",
        ),
        (
            not _DYNAMIC_SOURCE.search(sanitized),
            "must not use dynamic source identifiers",
        ),
    )
    standard_errors = tuple(
        f"dataset {name} {message}" for passed, message in checks if not passed
    )
    policy_errors = tuple(
        f"dataset {name} {error}" for error in query_errors
    )
    return standard_errors + policy_errors + _relation_errors(name, relation_inspection)


def sanitize(sql: str) -> str:
    """Remove SQL comments before enforcing source and safety rules."""
    return strip_sql_comments(sql)


def _relation_errors(name: str, inspection: RelationInspection) -> tuple[str, ...]:
    return tuple(f"dataset {name} {error}" for error in inspection.errors)
