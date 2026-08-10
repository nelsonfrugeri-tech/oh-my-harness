"""Validate freshness and source shape of signed policy evidence."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from dashboard_models import PolicyEvidence

_TABLE_NAME = re.compile(r"^[\w]+\.[\w]+\.[\w]+$")


def evidence_errors(evidence: PolicyEvidence) -> tuple[str, ...]:
    """Return all policy evidence validation errors."""
    now = datetime.now(timezone.utc)
    checks = (
        (evidence.generated_at <= now, "policy evidence generated_at is in the future"),
        (
            now - evidence.generated_at <= timedelta(minutes=5),
            "policy evidence is older than five minutes",
        ),
        (evidence.expires_at > now, "policy evidence has expired"),
        (
            evidence.expires_at > evidence.generated_at,
            "policy evidence expires_at must be after generated_at",
        ),
        (
            evidence.expires_at - evidence.generated_at <= timedelta(hours=1),
            "policy evidence lifetime exceeds one hour",
        ),
        (_sources_are_unique(evidence), "policy evidence sources must be unique"),
    )
    return tuple(message for passed, message in checks if not passed) + _shape_errors(
        evidence
    )


def _shape_errors(evidence: PolicyEvidence) -> tuple[str, ...]:
    invalid = tuple(
        item.source for item in evidence.sources if not _TABLE_NAME.match(item.source)
    )
    if not invalid:
        return ()
    return (
        "policy evidence sources must use catalog.schema.table: " + ", ".join(invalid),
    )


def _sources_are_unique(evidence: PolicyEvidence) -> bool:
    names = tuple(item.source.lower() for item in evidence.sources)
    return len(names) == len(set(names))
