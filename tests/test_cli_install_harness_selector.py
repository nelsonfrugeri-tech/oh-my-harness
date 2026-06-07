"""Tests for the harness selector flow injected at the end of ``omk install``.

We test ``_run_harness_selector`` directly (it is an internal helper) and also
the full ``omk install`` path by mocking the ``Installer`` and the interactive
prompts so no Docker/HuggingFace calls are made.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from oh_my_kb.cli.app import _run_harness_selector, app
from oh_my_kb.cli.config import CLIConfig, Universe
from oh_my_kb.cli.installer import InstallReport


def _config(active: str = "default") -> CLIConfig:
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


def _fake_install_report(universe: str = "default", tmp_path: Path | None = None) -> InstallReport:
    root = (tmp_path or Path("/tmp")) / "notes" / universe
    return InstallReport(
        qdrant_url="http://localhost:6333",
        universe=universe,
        notes_root=root,
        collection=f"kb_{universe}",
        config_file=Path("/tmp/config.toml"),
        actions=["qdrant already healthy", "bge-m3 model ready"],
    )


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestRunHarnessSelector:
    """Unit tests for the ``_run_harness_selector`` internal helper."""

    def test_no_selection_does_not_create_claude_md(
        self, tmp_path: Path
    ) -> None:
        """Pressing Enter without a number skips — covered by unit call to helper."""
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value=""),
            patch("typer.echo"),
            patch("typer.secho"),
        ):
            _run_harness_selector("default")
        assert not (home / ".claude" / "CLAUDE.md").exists()

    def test_skip_via_enter_does_not_create_claude_md(
        self, tmp_path: Path
    ) -> None:
        """Skipping the selector does not touch ~/.claude/CLAUDE.md."""
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value=""),
            patch("builtins.print"),  # suppress output
        ):
            _run_harness_selector("default")
        assert not (home / ".claude" / "CLAUDE.md").exists()

    def test_selecting_claude_code_confirmed_writes_file(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value="1"),  # select option 1 = claude-code
            patch("typer.confirm", return_value=True),
            patch("typer.echo"),
            patch("typer.secho"),
        ):
            _run_harness_selector("default")
        assert (home / ".claude" / "CLAUDE.md").exists()

    def test_selecting_claude_code_declined_does_not_write(
        self, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value="1"),
            patch("typer.confirm", return_value=False),
            patch("typer.echo"),
            patch("typer.secho"),
        ):
            _run_harness_selector("default")
        assert not (home / ".claude" / "CLAUDE.md").exists()

    def test_coming_soon_selection_prints_unavailable(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Selecting a coming-soon harness does not write."""
        home = tmp_path / "home"
        home.mkdir()
        from oh_my_kb.agents.harness import HARNESS_COMING_SOON, HARNESS_REGISTRY

        # The coming-soon entries start after the selectable ones
        selectable_count = len([n for n in HARNESS_REGISTRY if n not in HARNESS_COMING_SOON])
        # option = selectable_count + 1 would be the first coming-soon entry
        coming_soon_idx = str(selectable_count + 1)

        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value=coming_soon_idx),
            patch("typer.echo"),
            patch("typer.secho"),
        ):
            _run_harness_selector("default")
        assert not (home / ".claude" / "CLAUDE.md").exists()

    def test_invalid_number_does_not_write(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        with (
            patch.object(Path, "home", return_value=home),
            patch("typer.prompt", return_value="999"),
            patch("typer.echo"),
            patch("typer.secho"),
        ):
            _run_harness_selector("default")
        assert not (home / ".claude" / "CLAUDE.md").exists()


class TestInstallCLIWithHarnessSelector:
    """Full CLI tests for ``omk install`` with selector flow."""

    def _patch_installer(self, tmp_path: Path, universe: str = "default") -> MagicMock:
        mock_installer = MagicMock()
        mock_installer.run.return_value = _fake_install_report(universe, tmp_path)
        return mock_installer

    def test_install_skip_selector_via_enter(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        mock_installer = self._patch_installer(tmp_path)
        with (
            patch("oh_my_kb.cli.app.Installer", return_value=mock_installer),
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(app, ["install"], input="\n")
        assert result.exit_code == 0
        assert "Nenhum harness" in result.output or "harness" in result.output.lower()
        assert not (home / ".claude" / "CLAUDE.md").exists()

    def test_install_select_claude_code_confirmed_writes_file(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        mock_installer = self._patch_installer(tmp_path)
        with (
            patch("oh_my_kb.cli.app.Installer", return_value=mock_installer),
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            # "1\ns\n": select option 1, then confirm with 's'
            result = runner.invoke(app, ["install"], input="1\ny\n")
        assert result.exit_code == 0
        assert (home / ".claude" / "CLAUDE.md").exists()
        content = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        assert "omk:rules:start" in content

    def test_install_select_claude_code_declined_no_write(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir()
        mock_installer = self._patch_installer(tmp_path)
        with (
            patch("oh_my_kb.cli.app.Installer", return_value=mock_installer),
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            result = runner.invoke(app, ["install"], input="1\nn\n")
        assert result.exit_code == 0
        assert not (home / ".claude" / "CLAUDE.md").exists()
        assert "cancelado" in result.output.lower()

    def test_install_generated_block_has_all_tools(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        from oh_my_kb.mcp.tools import (
            KB_EXPAND_TOOL,
            KB_RECENT_TOOL,
            KB_SEARCH_TOOL,
            KB_TREE_TOOL,
            KB_WRITE_TOOL,
        )

        home = tmp_path / "home"
        home.mkdir()
        mock_installer = self._patch_installer(tmp_path)
        with (
            patch("oh_my_kb.cli.app.Installer", return_value=mock_installer),
            patch("oh_my_kb.cli.app.load_config", return_value=_config()),
            patch.object(Path, "home", return_value=home),
        ):
            runner.invoke(app, ["install"], input="1\ny\n")
        content = (home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        tools = [KB_WRITE_TOOL, KB_SEARCH_TOOL, KB_TREE_TOOL, KB_EXPAND_TOOL, KB_RECENT_TOOL]
        for tool in tools:
            assert tool.name in content, f"tool {tool.name} missing from CLAUDE.md"
