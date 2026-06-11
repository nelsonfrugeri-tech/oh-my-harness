"""Tests for oh_my_harness.agents.preferences.install."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from oh_my_harness.agents.preferences.install import write_initial_preferences
from oh_my_harness.agents.preferences.markers import USER_PREFS_END, USER_PREFS_START
from oh_my_harness.kb.agents.injector import InjectAction

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FROZEN_DATE = "2026-06-11"


def _freeze_now(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze _now_iso() to a deterministic date."""
    monkeypatch.setattr(
        "oh_my_harness.agents.preferences.install._now_iso",
        lambda: _FROZEN_DATE,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWriteInitialPreferences:
    def test_creates_file_when_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _freeze_now(monkeypatch)
        action = write_initial_preferences(home=tmp_path)
        assert action == InjectAction.CREATED
        target = tmp_path / ".claude" / "CLAUDE.md"
        assert target.exists()

    def test_inserts_block_in_existing_file_without_markers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _freeze_now(monkeypatch)
        target = tmp_path / ".claude" / "CLAUDE.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Existing content\n", encoding="utf-8")
        action = write_initial_preferences(home=tmp_path)
        assert action == InjectAction.INSERTED
        content = target.read_text(encoding="utf-8")
        assert USER_PREFS_START in content
        assert USER_PREFS_END in content
        assert "Existing content" in content

    def test_unchanged_on_second_run(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch)
        # Freeze platform calls so content is identical both runs
        with (
            patch("platform.system", return_value="TestOS"),
            patch("platform.node", return_value="test-machine"),
        ):
            write_initial_preferences(home=tmp_path)
            action2 = write_initial_preferences(home=tmp_path)
        assert action2 == InjectAction.UNCHANGED

    def test_block_contains_os(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch)
        with patch("platform.system", return_value="Darwin"):
            write_initial_preferences(home=tmp_path)
        content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Darwin" in content

    def test_block_contains_machine(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch)
        with patch("platform.node", return_value="my-test-box"):
            write_initial_preferences(home=tmp_path)
        content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "my-test-box" in content

    def test_block_contains_locale(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _freeze_now(monkeypatch)
        write_initial_preferences(home=tmp_path)
        content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "pt-BR" in content

    def test_block_contains_updated_em(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _freeze_now(monkeypatch)
        write_initial_preferences(home=tmp_path)
        content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Atualizado em" in content
        assert _FROZEN_DATE in content

    def test_two_blocks_coexist_in_same_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """omk:rules and omh:user-prefs blocks must coexist without collision."""
        from oh_my_harness.kb.agents.injector import END_MARKER, START_MARKER

        _freeze_now(monkeypatch)
        # First write the omk:rules block
        target = tmp_path / ".claude" / "CLAUDE.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"{START_MARKER}\n## Rules\n{END_MARKER}\n",
            encoding="utf-8",
        )
        # Then write user-prefs
        write_initial_preferences(home=tmp_path)
        content = target.read_text(encoding="utf-8")
        assert START_MARKER in content
        assert USER_PREFS_START in content
        assert USER_PREFS_END in content
