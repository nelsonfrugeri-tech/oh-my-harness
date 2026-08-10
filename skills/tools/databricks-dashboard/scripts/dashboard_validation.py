"""Orchestrate deterministic dashboard validation."""

from __future__ import annotations

from collections.abc import Mapping

from dashboard_evidence_validation import evidence_errors
from dashboard_layout_validation import definition_errors
from dashboard_models import Definition, PolicyEvidence, SourceEvidence
from dashboard_sql import extract_sources, sql_errors


def validate(definition: Definition, evidence: PolicyEvidence) -> tuple[str, ...]:
    """Return all validation errors without performing a remote operation."""
    return (
        definition_errors(definition)
        + evidence_errors(evidence)
        + _dataset_errors(definition, evidence)
    )


def _dataset_errors(
    definition: Definition, evidence: PolicyEvidence
) -> tuple[str, ...]:
    approved = {item.source.lower(): item for item in evidence.sources}
    return tuple(
        error
        for dataset in definition.datasets
        for error in _single_dataset_errors(dataset.name, dataset.sql, approved)
    )


def _single_dataset_errors(
    name: str, sql: str, approved: Mapping[str, SourceEvidence]
) -> tuple[str, ...]:
    sources = extract_sources(sql)
    source_errors = _unapproved_source_errors(name, sources, approved)
    missing_source = (
        () if sources else (f"dataset {name} has no fully qualified source",)
    )
    return sql_errors(name, sql) + missing_source + source_errors


def _unapproved_source_errors(
    name: str,
    sources: tuple[str, ...],
    approved: Mapping[str, SourceEvidence],
) -> tuple[str, ...]:
    return tuple(
        f"dataset {name} uses unapproved source: {source}"
        for source in sources
        if source.lower() not in approved or not approved[source.lower()].allowed
    )


__all__ = ("extract_sources", "validate")
