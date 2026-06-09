"""Tests for the kb_resource_list MCP tool handler."""

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
from oh_my_kb.mcp.tools.kb_resource_list import handle_kb_resource_list
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
                content_version="1.0.0",
                pulled_at=_NOW,
                sha256="0" * 64,  # wrong sha — outdated
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
# Case 1: manifest absent — warning inline, NOT error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_manifest_absent_shows_server_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    result = await handle_kb_resource_list({})
    assert len(result) == 1
    text = result[0].text
    assert "resources disponíveis no servidor" in text
    assert "manifest local não encontrado" in text
    assert "skills/scribe" in text
    assert "não instalado" in text
    assert "omk resource pull --all" in text


# ---------------------------------------------------------------------------
# Case 2: all up to date
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_up_to_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_list({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_list:" in text
    assert "✓ atualizado" in text
    assert "Todos os resources estão atualizados." in text


# ---------------------------------------------------------------------------
# Case 3: some outdated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_with_outdated_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_stale_manifest(tmp_path)
    result = await handle_kb_resource_list({})
    assert len(result) == 1
    text = result[0].text
    assert "● desatualizado" in text
    assert "kb_resource_update" in text


# ---------------------------------------------------------------------------
# Case 4: correct counts in header
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_shows_resource_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_list({})
    text = result[0].text
    assert "skills/scribe" in text
    assert _TEMPLATE_ID in text


# ---------------------------------------------------------------------------
# Case 5: does NOT mention universe
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_does_not_mention_universe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_list({})
    text = result[0].text
    assert "(universe:" not in text
