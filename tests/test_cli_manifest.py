"""Tests for oh_my_kb.cli.manifest."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from oh_my_kb.cli.manifest import (
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
    Manifest,
    ManifestEntry,
    _now_utc_z,
    load_manifest,
    manifest_path,
    save_manifest,
    upsert_entry,
)

# ---------------------------------------------------------------------------
# manifest_path
# ---------------------------------------------------------------------------


def test_manifest_path_uses_home(tmp_path: Path) -> None:
    path = manifest_path(home=tmp_path)
    assert path == tmp_path / ".claude" / MANIFEST_FILENAME


def test_manifest_path_default_is_under_home() -> None:
    path = manifest_path()
    assert path.name == MANIFEST_FILENAME
    assert ".claude" in path.parts


# ---------------------------------------------------------------------------
# _now_utc_z
# ---------------------------------------------------------------------------


def test_now_utc_z_ends_with_z() -> None:
    ts = _now_utc_z()
    assert ts.endswith("Z"), f"Expected Z suffix, got: {ts!r}"
    assert "+" not in ts, "Should not contain +00:00"


# ---------------------------------------------------------------------------
# Manifest serialisation round-trip
# ---------------------------------------------------------------------------


def test_manifest_to_dict_contains_schema_version() -> None:
    m = Manifest()
    d = m.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION


def test_manifest_round_trip_empty() -> None:
    m = Manifest()
    d = m.to_dict()
    m2 = Manifest.from_dict(d)
    assert m2.schema_version == SCHEMA_VERSION
    assert m2.resources == {}


def test_manifest_round_trip_with_entries() -> None:
    m = Manifest()
    entry = ManifestEntry(
        uri="skill://scribe/SKILL.md",
        local_path="~/.claude/skills/scribe/SKILL.md",
        content_version="1.0.0",
        pulled_at="2026-06-09T14:32:00Z",
        sha256="a" * 64,
    )
    m.resources["skills/scribe"] = entry
    d = m.to_dict()
    m2 = Manifest.from_dict(d)
    assert "skills/scribe" in m2.resources
    e = m2.resources["skills/scribe"]
    assert e.uri == "skill://scribe/SKILL.md"
    assert e.content_version == "1.0.0"
    assert e.sha256 == "a" * 64


# ---------------------------------------------------------------------------
# save_manifest / load_manifest
# ---------------------------------------------------------------------------


def test_save_creates_file(tmp_path: Path) -> None:
    m = Manifest()
    path = save_manifest(m, home=tmp_path)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    m = Manifest()
    save_manifest(m, home=tmp_path)
    assert (tmp_path / ".claude").is_dir()


def test_load_roundtrip(tmp_path: Path) -> None:
    m = Manifest()
    upsert_entry(
        manifest=m,
        resource_id="skills/scribe",
        uri="skill://scribe/SKILL.md",
        local_path="~/.claude/skills/scribe/SKILL.md",
        content_version="1.0.0",
        sha256="b" * 64,
    )
    save_manifest(m, home=tmp_path)
    m2 = load_manifest(home=tmp_path)
    assert "skills/scribe" in m2.resources
    assert m2.resources["skills/scribe"].content_version == "1.0.0"


def test_load_raises_file_not_found_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(home=tmp_path)


def test_load_raises_value_error_on_wrong_schema(tmp_path: Path) -> None:
    path = manifest_path(home=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 99, "updated_at": "2026-01-01T00:00:00Z", "resources": {}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="schema_version"):
        load_manifest(home=tmp_path)


def test_save_updates_updated_at(tmp_path: Path) -> None:
    m = Manifest()
    time.sleep(0.01)
    save_manifest(m, home=tmp_path)
    m2 = load_manifest(home=tmp_path)
    # updated_at should have been refreshed by save
    assert m2.updated_at.endswith("Z")


# ---------------------------------------------------------------------------
# upsert_entry
# ---------------------------------------------------------------------------


def test_upsert_entry_creates_new(tmp_path: Path) -> None:
    m = Manifest()
    entry = upsert_entry(
        manifest=m,
        resource_id="skills/scribe",
        uri="skill://scribe/SKILL.md",
        local_path="~/.claude/skills/scribe/SKILL.md",
        content_version="1.0.0",
        sha256="c" * 64,
    )
    assert "skills/scribe" in m.resources
    assert entry.sha256 == "c" * 64


def test_upsert_entry_overwrites_existing(tmp_path: Path) -> None:
    m = Manifest()
    upsert_entry(
        manifest=m,
        resource_id="skills/scribe",
        uri="skill://scribe/SKILL.md",
        local_path="~/.claude/skills/scribe/SKILL.md",
        content_version="1.0.0",
        sha256="d" * 64,
    )
    upsert_entry(
        manifest=m,
        resource_id="skills/scribe",
        uri="skill://scribe/SKILL.md",
        local_path="~/.claude/skills/scribe/SKILL.md",
        content_version="1.1.0",
        sha256="e" * 64,
    )
    assert m.resources["skills/scribe"].content_version == "1.1.0"
    assert m.resources["skills/scribe"].sha256 == "e" * 64
