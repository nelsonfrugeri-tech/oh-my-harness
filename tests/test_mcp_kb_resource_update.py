"""Tests for the kb_resource_update MCP tool handler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
from oh_my_kb.mcp.tools.kb_resource_update import handle_kb_resource_update
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
async def test_update_manifest_absent_returns_error_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    result = await handle_kb_resource_update({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_update: erro" in text
    assert "manifest não encontrado" in text
    assert "omk resource pull --all" in text


# ---------------------------------------------------------------------------
# Case 2: all up to date
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_all_already_up_to_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_update({})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_update: todos os resources já estão na versão mais recente" in text


# ---------------------------------------------------------------------------
# Case 3: single resource already up to date
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_single_resource_already_up_to_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_update({"resource": _SCRIBE_ID})
    assert len(result) == 1
    text = result[0].text
    assert "já está na versão mais recente" in text
    assert "skills/scribe" in text


# ---------------------------------------------------------------------------
# Case 4: normal update (mocked sync)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_applies_stale_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_stale_manifest(tmp_path)

    with patch("oh_my_kb.mcp.tools.kb_resource_update._do_update_sync") as mock_sync:
        from oh_my_kb.services.resource_ops import ResourceUpdateEntry, UpdateResult

        mock_result = UpdateResult(
            entries=[
                ResourceUpdateEntry(
                    resource_id=_SCRIBE_ID,
                    old_version="0.9.0",
                    new_version="1.0.0",
                    local_path="~/.claude/skills/scribe/SKILL.md",
                    was_updated=True,
                ),
                ResourceUpdateEntry(
                    resource_id=_TEMPLATE_ID,
                    old_version="1.0.0",
                    new_version="1.0.0",
                    local_path="~/.claude/skills/scribe/template.md",
                    was_updated=False,
                ),
            ],
            claude_md_regenerated=True,
            claude_md_error=None,
        )
        mock_sync.return_value = (mock_result, None, None)

        result = await handle_kb_resource_update({})

    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_update: 1 atualizado, 1 sem alterações" in text
    assert "skills/scribe" in text
    assert "✓" in text
    assert "CLAUDE.md regenerado" in text


# ---------------------------------------------------------------------------
# Case 5: invalid resource ID → error text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_invalid_resource_returns_error_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_current_manifest(tmp_path)
    result = await handle_kb_resource_update({"resource": "skills/inexistente"})
    assert len(result) == 1
    text = result[0].text
    assert "kb_resource_update: erro" in text
    assert "skills/inexistente" in text
    assert "não encontrado no servidor" in text


# ---------------------------------------------------------------------------
# Case 6: do_bootstrap fails → partial success, warn about CLAUDE.md
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_bootstrap_failure_warns_but_does_not_revert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".claude").mkdir()
    _make_stale_manifest(tmp_path)

    with patch("oh_my_kb.mcp.tools.kb_resource_update._do_update_sync") as mock_sync:
        from oh_my_kb.services.resource_ops import ResourceUpdateEntry, UpdateResult

        mock_result = UpdateResult(
            entries=[
                ResourceUpdateEntry(
                    resource_id=_SCRIBE_ID,
                    old_version="0.9.0",
                    new_version="1.0.0",
                    local_path="~/.claude/skills/scribe/SKILL.md",
                    was_updated=True,
                ),
                ResourceUpdateEntry(
                    resource_id=_TEMPLATE_ID,
                    old_version="1.0.0",
                    new_version="1.0.0",
                    local_path="~/.claude/skills/scribe/template.md",
                    was_updated=False,
                ),
            ],
            claude_md_regenerated=False,
            claude_md_error="no active universe configured",
        )
        mock_sync.return_value = (mock_result, None, "no active universe configured")

        result = await handle_kb_resource_update({})

    assert len(result) == 1
    text = result[0].text
    assert f"✓ {_SCRIBE_ID}" in text
    assert "Aviso:" in text
    assert "CLAUDE.md não pôde ser regenerado" in text
    assert "omk install" in text
