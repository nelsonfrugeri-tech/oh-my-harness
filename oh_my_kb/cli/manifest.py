"""Manifest layer for ``omk resource`` commands.

Tracks which MCP resources have been pulled locally, their version, and
their sha256 so ``omk resource diff`` can detect drift without a download.

Schema (``~/.claude/.omk-manifest.json``):

.. code-block:: json

    {
      "schema_version": 1,
      "updated_at": "2026-06-09T14:32:00Z",
      "resources": {
        "skills/scribe": {
          "uri": "skill://scribe/SKILL.md",
          "local_path": "~/.claude/skills/scribe/SKILL.md",
          "content_version": "1.0.0",
          "pulled_at": "2026-06-09T14:32:00Z",
          "sha256": "a3f1c2d4..."
        }
      }
    }
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

MANIFEST_FILENAME = ".omk-manifest.json"
SCHEMA_VERSION = 1


def _now_utc_z() -> str:
    """Return current UTC timestamp in ISO 8601 with 'Z' suffix."""
    return (
        datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


@dataclass
class ManifestEntry:
    """A single resource entry in the manifest."""

    uri: str
    local_path: str  # kept with ~ not expanded
    content_version: str
    pulled_at: str
    sha256: str


@dataclass
class Manifest:
    """In-memory representation of ``~/.claude/.omk-manifest.json``."""

    schema_version: int = SCHEMA_VERSION
    updated_at: str = field(default_factory=_now_utc_z)
    resources: dict[str, ManifestEntry] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize to a plain dict ready for JSON serialisation."""
        return {
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
            "resources": {
                resource_id: asdict(entry)
                for resource_id, entry in self.resources.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Manifest:
        """Deserialise from a plain dict (loaded from JSON)."""
        raw_resources = data.get("resources")
        raw_resources_dict: dict[str, dict[str, str]] = (
            raw_resources if isinstance(raw_resources, dict) else {}
        )
        resources: dict[str, ManifestEntry] = {
            resource_id: ManifestEntry(**entry_data)
            for resource_id, entry_data in raw_resources_dict.items()
        }
        raw_schema = data.get("schema_version", SCHEMA_VERSION)
        schema_version = raw_schema if isinstance(raw_schema, int) else SCHEMA_VERSION
        raw_updated = data.get("updated_at")
        updated_at = raw_updated if isinstance(raw_updated, str) else _now_utc_z()
        return cls(
            schema_version=schema_version,
            updated_at=updated_at,
            resources=resources,
        )


def manifest_path(home: Path | None = None) -> Path:
    """Return the path to the manifest file.

    Args:
        home: Override for ``Path.home()`` — used in tests.
    """
    base = home if home is not None else Path.home()
    return base / ".claude" / MANIFEST_FILENAME


def load_manifest(home: Path | None = None) -> Manifest:
    """Load the manifest from disk.

    Raises:
        FileNotFoundError: when the manifest file does not exist.
        ValueError: when ``schema_version`` is unsupported.
    """
    path = manifest_path(home)
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = data.get("schema_version", 0)
    if schema != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported manifest schema_version {schema!r}; expected {SCHEMA_VERSION}."
        )
    return Manifest.from_dict(data)


def save_manifest(manifest: Manifest, home: Path | None = None) -> Path:
    """Persist *manifest* to disk and return the written path.

    Creates ``~/.claude/`` if it does not exist.
    """
    path = manifest_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest.updated_at = _now_utc_z()
    path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def upsert_entry(
    manifest: Manifest,
    resource_id: str,
    uri: str,
    local_path: str,
    content_version: str,
    sha256: str,
) -> ManifestEntry:
    """Create or update a manifest entry and return it."""
    entry = ManifestEntry(
        uri=uri,
        local_path=local_path,
        content_version=content_version,
        pulled_at=_now_utc_z(),
        sha256=sha256,
    )
    manifest.resources[resource_id] = entry
    return entry
