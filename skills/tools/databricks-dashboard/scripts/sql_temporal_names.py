"""Recognize portable temporal SQL identifiers and constructs."""

from __future__ import annotations

_TEMPORAL_NAMES = frozenset(
    (
        "date",
        "datetime",
        "dt",
        "time",
        "timestamp",
        "ts",
    )
)
_TEMPORAL_PREFIXES = (
    "date_",
    "datetime_",
    "dt_",
    "time_",
    "timestamp_",
    "ts_",
)
_TEMPORAL_SUFFIXES = (
    "_at",
    "_date",
    "_datetime",
    "_dt",
    "_time",
    "_timestamp",
    "_ts",
)


def is_temporal_column_name(value: str) -> bool:
    """Return whether an identifier names a recognized temporal value."""
    name = value.lower()
    return (
        name in _TEMPORAL_NAMES
        or name.startswith(_TEMPORAL_PREFIXES)
        or name.endswith(_TEMPORAL_SUFFIXES)
    )
