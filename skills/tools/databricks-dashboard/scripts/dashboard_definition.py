"""Public parsing interface for portable Lakeview dashboard definitions."""

from __future__ import annotations

from pathlib import Path

from dashboard_models import Definition, PolicyEvidence
from dashboard_parsing import definition_from_data, object_from_file
from dashboard_policy import policy_evidence_from_data, policy_payload


def load_definition(path: Path) -> Definition:
    """Load a validated portable dashboard definition from JSON."""
    return definition_from_data(object_from_file(path, "definition"))


def load_policy_evidence(path: Path) -> PolicyEvidence:
    """Load and verify signed policy evidence from JSON."""
    return policy_evidence_from_data(object_from_file(path, "policy evidence"))


_policy_payload = policy_payload
