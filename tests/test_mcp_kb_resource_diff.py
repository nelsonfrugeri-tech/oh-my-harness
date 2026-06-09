"""Tests for the kb_resource_diff MCP tool handler."""

from __future__ import annotations

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
from oh_my_kb.mcp.tools.kb_resource_diff import handle_kb_resource_diff
from oh_my_kb.services.resource_ops import _extract_content_version, _sha256_of

_NOW = "2026-06-09T00:00:00Z"
_SCRIBE_ID = "skills/scribe"
_TEMPLATE_ID = "skills/scribe-template"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_current_manifest(tmp_path: Path) -> None:
    scribe = read_scribe_resource(SCRIBE_SKILL_URI)
    template = read_scribe_resource(SCRIBE_TEMPLATE_URI)
    m = Manifest(
        updated_at=_NOW,
        resources={
            _SCRIBE_ID: ManifestEntry(
                uri=SCRIBE_SKILL_URI,
                local_path="~/.claude/skills/scribe/SKILL.md",
                content_version=_extract_content_version(scribe),
                pulled_at=_NOW,
                sha256=_sha256_of(scribe),
            ),
            _TEMPLATE_ID: ManifestEntry(
                uri=SCRIBE_TEMPLATE_URI,
                local_path="~/.claude/skills/scribe/template.md",
                content_version=_extract_content_version(template),
                pulled_at=_NOW,
                sha256=_sha256_of(template),
            ),
        },
    )
    save_manifest(m, home=tmp_path)


def _make_stale_manifest(tmp_path: Path) -> None:
    template = read_scribe_resource(SCRIBE_TEMPLATE_URI)
    m = Manifest(
        updated_at=_NOW,
        resources={
            _SCRIBE_ID: ManifestEntry(
                uri=SCRIBE_SKILL_URI,
                local_path="~/.claude/skills/scribe/SKILL.md",
                content_version="0.9.0",
                pulled_at=_NOW,
                sha256="0" * 64,
            ),
            _TEMPLATE_ID: ManifestEntry(
                uri=SCRIBE_TEMPLATE_URI,
                local_path="~/.claude/skills/scribe/template.md",
                content_version=_extract_content_version(template),
                pulled_at=_NOW,
                sha256=_sha256_of(template),
            ),
        },
    )
    save_manifest(m, home=tmp_path)


# ---------------------------------------------------------------------------
# Case 1: manifest absent → error text (not raise)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_manifest_absent_returns_error_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    result = await handle_kb_resource_diff({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_diff: erro" in text
    assert "manifest não encontrado" in text
    assert "omk resource pull --all" in text


# ---------------------------------------------------------------------------
# Case 2: all up to date
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_all_up_to_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_diff({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_diff: todos os resources estão atualizados" in text


# ---------------------------------------------------------------------------
# Case 3: with changes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_with_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_stale_manifest(tmp_path)
    result = await handle_kb_resource_diff({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_diff:" in text
    assert "alterações" in text
    assert "skills/scribe" in text
    assert "kb_resource_update" in text


# ---------------------------------------------------------------------------
# Case 4: single resource scoped diff — valid resource
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_single_valid_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_diff({"resource": _SCRIBE_ID})
    assert len(result) == 1
    text = result[0].text
    assert "skills/scribe" in text


# ---------------------------------------------------------------------------
# Case 5: invalid resource ID → error text (not raise)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_invalid_resource_returns_error_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_diff({"resource": "skills/inexistente"})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_diff: erro" in text
    assert "skills/inexistente" in text
    assert "não encontrado no servidor" in text
    assert "skills/scribe" in text  # available resources listed
