"""Tests for ``omh kb resources`` and ``omh kb agents`` subgroups.

Acceptance criteria covered:
- ``omh kb resources list`` reaches the list command
- ``omh kb resources pull`` (no name, no --all) exits 1
- ``omh kb resources diff`` exits 0 or 1 (routed correctly)
- ``omh kb resources update`` (no manifest) exits 1
- ``omh kb agents list`` exits 0 with stub message
- ``omh kb agents pull`` exits 0 with stub message
- ``omh kb agents diff`` exits 0 with stub message
- ``omh kb agents update`` exits 0 with stub message
- top-level ``omh resource`` subgroup is gone
"""

from __future__ import annotations

from typer.testing import CliRunner

from oh_my_harness.kb.cli.app import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# omh kb resources — routing
# ---------------------------------------------------------------------------


def test_kb_resources_list_exits_0(fake_claude_home: object) -> None:
    """``omh kb resources list`` routes to list_cmd and exits 0."""
    result = runner.invoke(app, ["kb", "resources", "list"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "skills/scribe" in result.output


def test_kb_resources_pull_no_args_exits_1(fake_claude_home: object) -> None:
    """``omh kb resources pull`` without args exits 1."""
    result = runner.invoke(app, ["kb", "resources", "pull"], catch_exceptions=False)
    assert result.exit_code == 1


def test_kb_resources_diff_no_manifest_exits_1(fake_claude_home: object) -> None:
    """``omh kb resources diff`` with no manifest exits 1."""
    result = runner.invoke(app, ["kb", "resources", "diff"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "manifest" in result.output.lower()


def test_kb_resources_update_no_manifest_exits_1(fake_claude_home: object) -> None:
    """``omh kb resources update`` with no manifest exits 1."""
    result = runner.invoke(app, ["kb", "resources", "update"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "manifest" in result.output.lower()


# ---------------------------------------------------------------------------
# omh kb agents — stubs
# ---------------------------------------------------------------------------


def test_kb_agents_list_exits_0() -> None:
    """``omh kb agents list`` exits 0 with stub message."""
    result = runner.invoke(app, ["kb", "agents", "list"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "em breve" in result.output.lower()


def test_kb_agents_pull_exits_0() -> None:
    """``omh kb agents pull`` exits 0 with stub message."""
    result = runner.invoke(app, ["kb", "agents", "pull"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "em breve" in result.output.lower()


def test_kb_agents_diff_exits_0() -> None:
    """``omh kb agents diff`` exits 0 with stub message."""
    result = runner.invoke(app, ["kb", "agents", "diff"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "em breve" in result.output.lower()


def test_kb_agents_update_exits_0() -> None:
    """``omh kb agents update`` exits 0 with stub message."""
    result = runner.invoke(app, ["kb", "agents", "update"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "em breve" in result.output.lower()


# ---------------------------------------------------------------------------
# top-level omh resource subgroup is gone
# ---------------------------------------------------------------------------


def test_top_level_resource_subgroup_removed() -> None:
    """``omh resource`` is no longer a top-level subgroup."""
    result = runner.invoke(app, ["resource", "list"], catch_exceptions=False)
    assert result.exit_code != 0


def test_top_level_help_does_not_show_resource() -> None:
    """Top-level ``omh --help`` no longer lists ``resource`` as a subcommand."""
    result = runner.invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    lines = result.output.splitlines()
    top_level_commands = [
        line.strip().split()[0]
        for line in lines
        if line.strip() and not line.strip().startswith("-")
    ]
    assert "resource" not in top_level_commands
