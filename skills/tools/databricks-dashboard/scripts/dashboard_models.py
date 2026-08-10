"""Immutable models for portable Lakeview dashboard input."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from json_object import JsonObject


@dataclass(frozen=True)
class Dataset:
    name: str
    sql: str


@dataclass(frozen=True)
class Definition:
    title: str
    warehouse_id: str
    parent_path: str
    serialized_dashboard: JsonObject
    datasets: tuple[Dataset, ...]
    smoke_parameters: tuple[JsonObject, ...]


@dataclass(frozen=True)
class SourceEvidence:
    source: str
    allowed: bool
    reference: str


@dataclass(frozen=True)
class PolicyEvidence:
    policy: str
    issuer: str
    generated_at: datetime
    expires_at: datetime
    sources: tuple[SourceEvidence, ...]
