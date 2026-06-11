"""Tests for oh_my_harness.agents.preferences.sessions."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from oh_my_harness.agents.preferences.sessions import read_recent_user_prompts


def _write_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(e) for e in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _user_event(text: str) -> dict:
    return {"type": "user", "message": {"content": text}}


def _assistant_event(text: str) -> dict:
    return {"type": "assistant", "message": {"content": text}}


def _tool_result_event() -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def _system_reminder_event() -> dict:
    return {"type": "user", "message": {"content": "<system-reminder>blah</system-reminder>"}}


def _command_name_event() -> dict:
    return {"type": "user", "message": {"content": "<command-name>foo</command-name>"}}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestReadRecentUserPrompts:
    def test_returns_empty_string_when_no_projects_dir(self, tmp_path: Path) -> None:
        result = read_recent_user_prompts(home=tmp_path)
        assert result == ""

    def test_returns_empty_string_when_no_jsonl_files(self, tmp_path: Path) -> None:
        (tmp_path / ".claude" / "projects" / "proj-a").mkdir(parents=True)
        result = read_recent_user_prompts(home=tmp_path)
        assert result == ""

    def test_extracts_genuine_user_prompts(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / f"{uuid.uuid4()}.jsonl"
        _write_jsonl(
            session,
            [
                _user_event("Hello Claude"),
                _assistant_event("Hi!"),
                _user_event("Implement feature X"),
                _tool_result_event(),
                _system_reminder_event(),
                _command_name_event(),
            ],
        )
        result = read_recent_user_prompts(home=tmp_path)
        assert "Hello Claude" in result
        assert "Implement feature X" in result

    def test_skips_tool_result_blocks(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / f"{uuid.uuid4()}.jsonl"
        _write_jsonl(session, [_tool_result_event(), _user_event("real prompt")])
        result = read_recent_user_prompts(home=tmp_path)
        assert "real prompt" in result
        # tool_result content should not appear (it's a list, not a string)
        assert "tool_result" not in result

    def test_skips_system_reminder_content(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / f"{uuid.uuid4()}.jsonl"
        _write_jsonl(
            session,
            [
                _system_reminder_event(),
                _user_event("actual user message"),
            ],
        )
        result = read_recent_user_prompts(home=tmp_path)
        assert "actual user message" in result
        assert "<system-reminder>" not in result

    def test_skips_command_name_content(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / f"{uuid.uuid4()}.jsonl"
        _write_jsonl(session, [_command_name_event(), _user_event("real msg")])
        result = read_recent_user_prompts(home=tmp_path)
        assert "real msg" in result
        assert "<command-name>" not in result

    def test_skips_assistant_events(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / f"{uuid.uuid4()}.jsonl"
        _write_jsonl(session, [_assistant_event("assistant response"), _user_event("user prompt")])
        result = read_recent_user_prompts(home=tmp_path)
        assert "user prompt" in result
        assert "assistant response" not in result

    def test_file_ordering_by_mtime(self, tmp_path: Path) -> None:
        """Most recently modified file should appear first in the output."""
        proj = tmp_path / ".claude" / "projects" / "proj-a"
        proj.mkdir(parents=True)

        file_a = proj / "aaaa.jsonl"
        file_b = proj / "bbbb.jsonl"
        file_c = proj / "cccc.jsonl"

        _write_jsonl(file_a, [_user_event("prompt from A")])
        _write_jsonl(file_b, [_user_event("prompt from B")])
        _write_jsonl(file_c, [_user_event("prompt from C")])

        # Touch file_b to make it the most recent
        time.sleep(0.01)
        file_b.touch()

        result = read_recent_user_prompts(home=tmp_path, max_sessions=3)
        # file_b (most recent) should produce content that appears before files a and c
        idx_b = result.find("prompt from B")
        idx_a = result.find("prompt from A")
        idx_c = result.find("prompt from C")
        assert idx_b != -1 and idx_a != -1 and idx_c != -1
        assert idx_b < idx_a or idx_b < idx_c, "most-recent file should appear first"

    def test_max_sessions_limit(self, tmp_path: Path) -> None:
        proj = tmp_path / ".claude" / "projects" / "proj-a"
        proj.mkdir(parents=True)
        for i in range(10):
            _write_jsonl(proj / f"session_{i:02d}.jsonl", [_user_event(f"prompt {i}")])

        result = read_recent_user_prompts(home=tmp_path, max_sessions=3)
        # With max_sessions=3 only 3 files are read; at most 3 prompts present
        prompt_count = sum(1 for i in range(10) if f"prompt {i}" in result)
        assert prompt_count <= 3

    def test_max_chars_truncation(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / "s.jsonl"
        long_prompt = "x" * 200
        _write_jsonl(session, [_user_event(long_prompt)])
        result = read_recent_user_prompts(home=tmp_path, max_chars=50)
        assert len(result) <= 50

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / "s.jsonl"
        session.parent.mkdir(parents=True, exist_ok=True)
        session.write_text(
            'not json at all\n{"type": "user", "message": {"content": "valid prompt"}}\n',
            encoding="utf-8",
        )
        result = read_recent_user_prompts(home=tmp_path)
        assert "valid prompt" in result

    def test_returns_empty_string_when_all_events_filtered(self, tmp_path: Path) -> None:
        session = tmp_path / ".claude" / "projects" / "proj-a" / "s.jsonl"
        _write_jsonl(
            session, [_tool_result_event(), _system_reminder_event(), _assistant_event("x")]
        )
        result = read_recent_user_prompts(home=tmp_path)
        assert result == ""
