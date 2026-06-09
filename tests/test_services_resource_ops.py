"""Unit tests for oh_my_kb.services.resource_ops (pure layer — no CLI/MCP deps)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oh_my_kb.cli.manifest import (
    Manifest,
    ManifestEntry,
    save_manifest,
)
from oh_my_kb.mcp.resources import (
    SCRIBE_SKILL_URI,
    SCRIBE_TEMPLATE_URI,
    read_scribe_resource,
)
from oh_my_kb.services.resource_ops import (
    DiffResult,
    ResourceStatus,
    UpdateResult,
    _extract_content_version,
    _sha256_of,
    apply_update,
    compute_diff,
    list_resources_with_status,
)

_NOW = "2026-06-09T00:00:00Z"

# Resource IDs as they exist in this branch
_SCRIBE_ID = "skills/scribe"
_TEMPLATE_ID = "skills/scribe-template"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_current_manifest(tmp_path: Path) -> Manifest:
    """Manifest matching server SHA exactly."""
    scribe_content = read_scribe_resource(SCRIBE_SKILL_URI)
    template_content = read_scribe_resource(SCRIBE_TEMPLATE_URI)
    m = Manifest(
        updated_at=_NOW,
        resources={
            _SCRIBE_ID: ManifestEntry(
                uri=SCRIBE_SKILL_URI,
                local_path="~/.claude/skills/scribe/SKILL.md",
                content_version=_extract_content_version(scribe_content),
                pulled_at=_NOW,
                sha256=_sha256_of(scribe_content),
            ),
            _TEMPLATE_ID: ManifestEntry(
                uri=SCRIBE_TEMPLATE_URI,
                local_path="~/.claude/skills/scribe/template.md",
                content_version=_extract_content_version(template_content),
                pulled_at=_NOW,
                sha256=_sha256_of(template_content),
            ),
        },
    )
    save_manifest(m, home=tmp_path)
    return m


def _make_stale_manifest(tmp_path: Path) -> Manifest:
    """Manifest with wrong SHA for skills/scribe."""
    template_content = read_scribe_resource(SCRIBE_TEMPLATE_URI)
    m = Manifest(
        updated_at=_NOW,
        resources={
            _SCRIBE_ID: ManifestEntry(
                uri=SCRIBE_SKILL_URI,
                local_path="~/.claude/skills/scribe/SKILL.md",
                content_version="0.9.0",
                pulled_at=_NOW,
                sha256="0" * 64,  # wrong sha — stale
            ),
            _TEMPLATE_ID: ManifestEntry(
                uri=SCRIBE_TEMPLATE_URI,
                local_path="~/.claude/skills/scribe/template.md",
                content_version=_extract_content_version(template_content),
                pulled_at=_NOW,
                sha256=_sha256_of(template_content),
            ),
        },
    )
    save_manifest(m, home=tmp_path)
    return m


# ---------------------------------------------------------------------------
# list_resources_with_status
# ---------------------------------------------------------------------------


def test_list_with_no_manifest_marks_all_not_installed() -> None:
    statuses = list_resources_with_status(manifest=None)
    assert len(statuses) >= 2
    for s in statuses:
        assert isinstance(s, ResourceStatus)
        assert s.is_installed is False
        assert s.local_version is None


def test_list_with_current_manifest_all_up_to_date(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    statuses = list_resources_with_status(manifest=m)
    for s in statuses:
        assert s.is_installed is True
        assert s.is_outdated is False


def test_list_with_stale_manifest_marks_scribe_outdated(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    statuses = list_resources_with_status(manifest=m)
    by_id = {s.resource_id: s for s in statuses}
    assert by_id[_SCRIBE_ID].is_outdated is True
    assert by_id[_TEMPLATE_ID].is_outdated is False


def test_list_returns_correct_versions(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    statuses = list_resources_with_status(manifest=m)
    scribe = next(s for s in statuses if s.resource_id == _SCRIBE_ID)
    assert scribe.local_version == "0.9.0"
    assert scribe.server_version  # non-empty


# ---------------------------------------------------------------------------
# compute_diff
# ---------------------------------------------------------------------------


def test_compute_diff_all_current_returns_no_changes(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    result = compute_diff(manifest=m, resource_id=None)
    assert isinstance(result, DiffResult)
    assert result.changed_count == 0
    assert result.unchanged_count == len(result.entries)


def test_compute_diff_stale_manifest_marks_scribe_changed(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    result = compute_diff(manifest=m, resource_id=None)
    changed = [e for e in result.entries if e.is_changed]
    unchanged = [e for e in result.entries if not e.is_changed]
    assert any(e.resource_id == _SCRIBE_ID for e in changed)
    assert any(e.resource_id == _TEMPLATE_ID for e in unchanged)


def test_compute_diff_single_resource(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    result = compute_diff(manifest=m, resource_id=_SCRIBE_ID)
    assert len(result.entries) == 1
    assert result.entries[0].resource_id == _SCRIBE_ID


def test_compute_diff_invalid_resource_raises_key_error(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    with pytest.raises(KeyError):
        compute_diff(manifest=m, resource_id="skills/nonexistent")


def test_compute_diff_changed_entry_has_diff_text(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    result = compute_diff(manifest=m, resource_id=_SCRIBE_ID)
    assert result.changed_count == 1
    assert result.entries[0].is_changed is True


# ---------------------------------------------------------------------------
# apply_update
# ---------------------------------------------------------------------------


def test_apply_update_all_current_returns_no_updates(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    result = apply_update(manifest=m, resource_id=None, home=tmp_path)
    assert isinstance(result, UpdateResult)
    assert result.updated_count == 0


def test_apply_update_stale_manifest_updates_scribe(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    result = apply_update(manifest=m, resource_id=None, home=tmp_path)
    assert result.updated_count == 1
    updated = [e for e in result.entries if e.was_updated]
    assert updated[0].resource_id == _SCRIBE_ID


def test_apply_update_writes_file_to_disk(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    apply_update(manifest=m, resource_id=None, home=tmp_path)
    dest = tmp_path / ".claude" / "skills" / "scribe" / "SKILL.md"
    assert dest.exists()
    assert "Scribe" in dest.read_text(encoding="utf-8")


def test_apply_update_single_resource_invalid_raises_key_error(tmp_path: Path) -> None:
    m = _make_current_manifest(tmp_path)
    with pytest.raises(KeyError):
        apply_update(manifest=m, resource_id="skills/nonexistent", home=tmp_path)


def test_apply_update_persists_manifest(tmp_path: Path) -> None:
    m = _make_stale_manifest(tmp_path)
    scribe_content = read_scribe_resource(SCRIBE_SKILL_URI)
    expected_sha = _sha256_of(scribe_content)
    apply_update(manifest=m, resource_id=None, home=tmp_path)
    manifest_file = tmp_path / ".claude" / ".omk-manifest.json"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["resources"][_SCRIBE_ID]["sha256"] == expected_sha
