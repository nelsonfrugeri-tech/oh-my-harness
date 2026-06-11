"""Tests for oh_my_harness.agents.preferences.llm."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oh_my_harness.agents.preferences.llm import MissingAnthropicKeyError, extract_preferences


def _make_mock_client(response_text: str) -> MagicMock:
    """Build a minimal mock for anthropic.Anthropic with a pre-set response."""
    client = MagicMock()
    message_obj = MagicMock()
    content_obj = MagicMock()
    content_obj.text = response_text
    message_obj.content = [content_obj]
    client.messages.create.return_value = message_obj
    return client


class TestExtractPreferences:
    def test_returns_stripped_bullet_text(self) -> None:
        mock_client = _make_mock_client("- pt-BR\n- prefere typer\n")
        result = extract_preferences("dummy prompts", client=mock_client)
        assert result == "- pt-BR\n- prefere typer"

    def test_calls_correct_model(self) -> None:
        mock_client = _make_mock_client("- ok\n")
        extract_preferences("dummy", client=mock_client)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"

    def test_uses_max_tokens_800(self) -> None:
        mock_client = _make_mock_client("- ok\n")
        extract_preferences("dummy", client=mock_client)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["max_tokens"] == 800

    def test_system_prompt_contains_key_phrase(self) -> None:
        mock_client = _make_mock_client("- ok\n")
        extract_preferences("dummy", client=mock_client)
        call_kwargs = mock_client.messages.create.call_args
        system = call_kwargs.kwargs["system"]
        assert "preferências" in system.lower() or "extrair" in system.lower()
        assert "markdown" in system.lower()

    def test_user_message_is_curated_prompts(self) -> None:
        mock_client = _make_mock_client("- ok\n")
        extract_preferences("my special prompts", client=mock_client)
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert any(m.get("content") == "my special prompts" for m in messages)

    def test_raises_missing_key_error_when_env_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(MissingAnthropicKeyError):
            extract_preferences("prompts", client=None)

    def test_raises_missing_key_error_contains_key_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(MissingAnthropicKeyError, match="ANTHROPIC_API_KEY"):
            extract_preferences("prompts", client=None)

    def test_instantiates_client_from_env_when_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        mock_client_instance = _make_mock_client("- pref\n")
        with patch("anthropic.Anthropic", return_value=mock_client_instance) as mock_cls:
            result = extract_preferences("prompts", client=None)
        mock_cls.assert_called_once_with(api_key="sk-test-key")
        assert "pref" in result
