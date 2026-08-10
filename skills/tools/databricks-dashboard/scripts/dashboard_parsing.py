"""Parse and validate JSON structures used by portable dashboards."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from dashboard_models import Dataset, Definition, SourceEvidence
from json_object import JsonObject, JsonValue


def object_from_file(path: Path, label: str) -> JsonObject:
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{label} must be a JSON object")
    return JsonObject.from_mapping(data)


def definition_from_data(data: JsonObject) -> Definition:
    _require_definition_fields(data)
    serialized = _serialized_dashboard(data)
    return Definition(
        title=string(data["display_name"], "display_name"),
        warehouse_id=string(data["warehouse_id"], "warehouse_id"),
        parent_path=string(data.get("parent_path", "/"), "parent_path"),
        serialized_dashboard=serialized,
        datasets=datasets(serialized.get("datasets")),
        smoke_parameters=optional_objects(data.get("smoke_parameters", ())),
    )


def source_evidence(data: JsonObject) -> SourceEvidence:
    allowed = data.get("allowed")
    if not isinstance(allowed, bool):
        raise TypeError("source evidence allowed must be a boolean")
    return SourceEvidence(
        source=string(data.get("source"), "source"),
        allowed=allowed,
        reference=string(data.get("reference"), "reference"),
    )


def objects(value: JsonValue, label: str) -> tuple[JsonObject, ...]:
    if not isinstance(value, tuple) or not all(
        isinstance(item, JsonObject) for item in value
    ):
        raise ValueError(f"{label} entries must be objects")
    return tuple(value)


def string(value: JsonValue, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def timestamp(value: JsonValue, label: str) -> datetime:
    parsed = datetime.fromisoformat(string(value, label).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _require_definition_fields(data: JsonObject) -> None:
    required = ("display_name", "warehouse_id", "serialized_dashboard")
    missing = tuple(key for key in required if key not in data)
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def _serialized_dashboard(data: JsonObject) -> JsonObject:
    serialized = data["serialized_dashboard"]
    if not isinstance(serialized, JsonObject):
        raise TypeError("serialized_dashboard must be a JSON object")
    return serialized


def datasets(value: JsonValue) -> tuple[Dataset, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError("datasets must be a non-empty list")
    return tuple(_dataset(item) for item in objects(value, "datasets"))


def optional_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    if not isinstance(value, tuple):
        raise TypeError("smoke_parameters must be a list")
    return objects(value, "smoke_parameters")


def _dataset(item: JsonObject) -> Dataset:
    query_lines = item.get("queryLines")
    if not isinstance(query_lines, tuple) or not query_lines:
        raise ValueError("dataset.queryLines must be a non-empty list")
    if not all(isinstance(line, str) for line in query_lines):
        raise ValueError("dataset.queryLines entries must be strings")
    sql = "".join(query_lines)
    if not sql.strip():
        raise ValueError("dataset.queryLines must contain SQL")
    return Dataset(name=string(item.get("name"), "dataset.name"), sql=sql)
