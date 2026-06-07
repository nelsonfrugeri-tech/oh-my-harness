"""Typer CliRunner tests for ``omk bootstrap``.

The ``bootstrap_cmd`` now shows a warning and requires explicit confirmation
before writing.  All tests that write a file must supply ``input="y\\n"``
("y" to confirm) to the runner invocation.
Tests that cover the decline path supply ``input="n\\n"`` or empty input.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from oh_my_kb.cli.app import app
from oh_my_kb.cli.config import CLIConfig, Universe


def _config(active: str = "test-universe") -> CLIConfig:
    return CLIConfig(
        universes=[
            Universe(
                name=active,
                notes_root=Path("/tmp/oh-my-kb") / active,
                collection=f"kb_{active.replace('-', '_')}",
            )
        ],
        active=active,
    )


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestBootstrapCLIWarning:
    """The warning must always be shown before any write happens."""

    def test_warning_shown_before_write(self, runner: CliRunner, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="n\n"
            )
        output_lower = result.output.lower()
        assert "aviso" in output_lower or "modificar" in output_lower

    def test_warning_shows_target_file_path(self, runner: CliRunner, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="n\n"
            )
        assert "CLAUDE.md" in result.output or ".claude" in result.output

    def test_decline_prints_bootstrap_cancelado(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="n\n"
            )
        assert result.exit_code == 0
        assert "cancelado" in result.output.lower()

    def test_decline_does_not_create_file(self, runner: CliRunner, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="n\n"
            )
        assert not (home / ".claude" / "CLAUDE.md").exists()


class TestBootstrapCLISuccess:
    """Confirm path: user supplies 's'/'y' and the file is written."""

    def test_creates_global_claude_md_and_exits_zero(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert result.exit_code == 0, result.output
        assert (home / ".claude" / "CLAUDE.md").exists()

    def test_project_path_does_not_affect_global_target(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        project = tmp_path / "some-project"
        project.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app,
                ["bootstrap", "--harness", "claude-code", "--project-path", str(project)],
                input="y\n",
            )
        assert result.exit_code == 0, result.output
        # File must be at the global path, not inside the project
        assert (home / ".claude" / "CLAUDE.md").exists()
        assert not (project / "CLAUDE.md").exists()

    def test_success_output_contains_kb_mcp_rules(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert result.exit_code == 0
        assert "kb-mcp rules" in result.output

    def test_output_contains_expected_fields(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config("my-universe")),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert "universe" in result.output
        assert "target" in result.output
        assert "action" in result.output
        assert "bytes" in result.output

    def test_output_target_shows_global_path(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert ".claude" in result.output
        assert "CLAUDE.md" in result.output

    def test_generated_block_contains_all_tools(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """The written file must contain all currently registered MCP tools."""
        from oh_my_kb.mcp.tools import (
            KB_EXPAND_TOOL,
            KB_RECENT_TOOL,
            KB_SEARCH_TOOL,
            KB_TREE_TOOL,
            KB_WRITE_TOOL,
        )

        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        claude_md = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        for tool in [KB_WRITE_TOOL, KB_SEARCH_TOOL, KB_TREE_TOOL, KB_EXPAND_TOOL, KB_RECENT_TOOL]:
            assert tool.name in claude_md, f"tool {tool.name} missing from generated block"

    def test_harness_scope_global_path_independent_of_cwd(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Harness.scope == 'global' path is always ~/.claude/CLAUDE.md regardless of cwd."""
        from oh_my_kb.agents.harness import HARNESS_REGISTRY

        assert HARNESS_REGISTRY["claude-code"].scope == "global"
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert result.exit_code == 0
        assert (home / ".claude" / "CLAUDE.md").exists()


class TestBootstrapCLIErrors:
    def test_unknown_harness_exits_nonzero(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        with patch("oh_my_kb.cli.app.load_config", return_value=_config()):
            result = runner.invoke(
                app,
                ["bootstrap", "--harness", "unknown-harness"],
            )
        assert result.exit_code != 0

    def test_unknown_harness_error_mentions_unknown(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        with patch("oh_my_kb.cli.app.load_config", return_value=_config()):
            result = runner.invoke(
                app,
                ["bootstrap", "--harness", "unknown-harness"],
            )
        assert "unknown" in result.output.lower() or "error" in result.output.lower()


class TestBootstrapCLIIdempotent:
    def test_second_run_prints_already_up_to_date(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
            result = runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
        assert result.exit_code == 0
        assert "already up to date" in result.output

    def test_rerun_after_block_update_regenerates(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Re-running after a trigger change updates the block (content drift)."""
        from oh_my_kb.agents import harness as harness_mod

        home = tmp_path / "home"
        home.mkdir()
        with (
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            runner.invoke(
                app, ["bootstrap", "--harness", "claude-code"], input="y\n"
            )
            original_content = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")

            # Simulate adding a new trigger (triggers content drift)
            new_triggers = dict(harness_mod.TOOL_TRIGGERS)
            new_triggers["kb_write"] = "Unique test trigger phrase xyz987"
            with patch.object(harness_mod, "TOOL_TRIGGERS", new_triggers):
                result = runner.invoke(
                    app, ["bootstrap", "--harness", "claude-code"], input="y\n"
                )

        assert result.exit_code == 0
        updated_content = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Unique test trigger phrase xyz987" in updated_content
        assert updated_content != original_content
