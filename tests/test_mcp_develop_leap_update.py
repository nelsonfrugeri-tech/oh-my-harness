"""Tests for oh_my_harness.agents.mcp.tools.develop_leap_update."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.types import TextContent


async def _call(home: Path) -> list[TextContent]:
    """Invoke the handler with HOME patched to *home*."""
    from oh_my_harness.agents.mcp.tools.develop_leap_update import handle_develop_leap_update

    with patch.object(Path, "home", return_value=home):
        return await handle_develop_leap_update({})


class TestHandleDevelopLeapUpdate:
    async def test_creates_block_on_fresh_home(self, tmp_path: Path) -> None:
        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="I prefer Python",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                return_value="- Python\n- pt-BR",
            ),
        ):
            result = await _call(tmp_path)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        target = tmp_path / ".claude" / "CLAUDE.md"
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "<!-- omh:user-prefs:start -->" in content
        assert "<!-- omh:user-prefs:end -->" in content
        assert "Python" in content

    async def test_updates_block_on_second_call(self, tmp_path: Path) -> None:
        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="I prefer Python",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                return_value="- Python\n- pt-BR",
            ),
        ):
            await _call(tmp_path)

        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="I prefer Rust now",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                return_value="- Rust\n- pt-BR",
            ),
        ):
            await _call(tmp_path)

        content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        # Only one user-prefs block (no duplication)
        assert content.count("<!-- omh:user-prefs:start -->") == 1
        assert "Rust" in content
        # Old insight replaced
        assert "Python" not in content

    async def test_missing_api_key_returns_text_no_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from oh_my_harness.agents.preferences.llm import MissingAnthropicKeyError

        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="some prompts",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                side_effect=MissingAnthropicKeyError("ANTHROPIC_API_KEY not set"),
            ),
        ):
            result = await _call(tmp_path)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "ANTHROPIC_API_KEY" in result[0].text

    async def test_empty_sessions_returns_text(self, tmp_path: Path) -> None:
        with patch(
            "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
            return_value="",
        ):
            result = await _call(tmp_path)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should mention sessions or no sessions found
        assert "sessão" in result[0].text.lower() or "session" in result[0].text.lower()

    async def test_response_contains_action_label(self, tmp_path: Path) -> None:
        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="prompts",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                return_value="- pref\n",
            ),
        ):
            result = await _call(tmp_path)

        # Action label should be one of CREATED / INSERTED / REPLACED / UNCHANGED
        text = result[0].text.upper()
        assert any(label in text for label in ("CREATED", "INSERTED", "REPLACED", "UNCHANGED"))

    async def test_response_contains_insights_preview(self, tmp_path: Path) -> None:
        with (
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.read_recent_user_prompts",
                return_value="prompts",
            ),
            patch(
                "oh_my_harness.agents.mcp.tools.develop_leap_update.extract_preferences",
                return_value="- uses Python daily\n",
            ),
        ):
            result = await _call(tmp_path)

        assert "uses Python daily" in result[0].text
