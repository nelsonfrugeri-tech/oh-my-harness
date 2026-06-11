"""Read recent Claude Code session files and extract genuine user prompts."""

from __future__ import annotations

import json
from pathlib import Path

# Prefixes that identify non-user events (tool echoes, system content, etc.)
_SKIP_PREFIXES = (
    "<local-command-caveat>",
    "<command-name>",
    "<system-reminder>",
    "<command-output>",
)


def _is_genuine_user_prompt(text: str) -> bool:
    """Return True if *text* looks like a real user-typed prompt."""
    stripped = text.strip()
    return bool(stripped) and not any(stripped.startswith(p) for p in _SKIP_PREFIXES)


def _extract_prompts_from_file(path: Path) -> list[str]:
    """Return genuine user prompts from a single JSONL session file."""
    prompts: list[str] = []
    try:
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, dict):
                continue
            if event.get("type") != "user":
                continue

            message = event.get("message")
            if not isinstance(message, dict):
                continue

            content = message.get("content")
            # Keep only plain string content — skip list (tool_result blocks etc.)
            if isinstance(content, str) and _is_genuine_user_prompt(content):
                prompts.append(content.strip())
    except OSError:
        pass

    return prompts


def read_recent_user_prompts(
    home: Path | None = None,
    max_sessions: int = 5,
    max_chars: int = 50_000,
) -> str:
    """Return a curated string of recent user prompts from Claude Code sessions.

    Globs JSONL files under ``<home>/.claude/projects/*/*.jsonl``, sorts them
    by modification time (most-recent first), takes the top *max_sessions*
    files, extracts genuine user prompts from each, then concatenates
    everything into a single string that is truncated to *max_chars* from the
    most-recent end.

    Args:
        home: Override for :func:`Path.home`.  Useful in tests.
        max_sessions: Maximum number of session files to read.
        max_chars: Maximum total character budget for the returned string.

    Returns:
        Concatenated user prompts, or an empty string if none found.
    """
    base = home if home is not None else Path.home()
    projects_dir = base / ".claude" / "projects"

    if not projects_dir.exists():
        return ""

    # Collect all JSONL session files
    session_files = list(projects_dir.glob("*/*.jsonl"))
    if not session_files:
        return ""

    # Sort by modification time descending (most recent first)
    session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    session_files = session_files[:max_sessions]

    # Build per-session blocks (most recent file first → at the start)
    session_blocks: list[str] = []
    for path in session_files:
        prompts = _extract_prompts_from_file(path)
        if prompts:
            session_blocks.append("\n".join(prompts))

    if not session_blocks:
        return ""

    combined = "\n\n---\n\n".join(session_blocks)

    # Truncate to max_chars from the most-recent end (beginning of the string)
    if len(combined) > max_chars:
        combined = combined[:max_chars]

    return combined
