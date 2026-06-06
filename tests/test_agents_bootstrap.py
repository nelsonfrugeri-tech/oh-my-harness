"""Integration tests for :func:`oh_my_kb.agents.bootstrap.bootstrap`."""

from __future__ import annotations

from pathlib import Path

import pytest

from oh_my_kb.agents.bootstrap import NoActiveUniverseError, bootstrap
from oh_my_kb.agents.harness import UnknownHarnessError
from oh_my_kb.agents.injector import START_MARKER, InjectAction
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


class TestBootstrapCreated:
    def test_file_does_not_exist_creates_file(self, tmp_path: Path) -> None:
        cfg = _config()
        report = bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        assert report.action == InjectAction.CREATED
        target = tmp_path / "CLAUDE.md"
        assert target.exists()

    def test_created_file_contains_universe(self, tmp_path: Path) -> None:
        cfg = _config("work")
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        target = tmp_path / "CLAUDE.md"
        assert "work" in target.read_text(encoding="utf-8")

    def test_created_file_contains_markers(self, tmp_path: Path) -> None:
        cfg = _config()
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        target = tmp_path / "CLAUDE.md"
        assert START_MARKER in target.read_text(encoding="utf-8")

    def test_report_fields_are_correct(self, tmp_path: Path) -> None:
        cfg = _config("my-universe")
        report = bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        assert report.harness == "claude-code"
        assert report.universe == "my-universe"
        assert report.target_file == tmp_path / "CLAUDE.md"
        assert report.bytes_written > 0


class TestBootstrapInserted:
    def test_file_with_user_content_no_markers_returns_inserted(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "CLAUDE.md"
        target.write_text("# My project rules\n\nDo not disturb.\n", encoding="utf-8")
        cfg = _config()
        report = bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        assert report.action == InjectAction.INSERTED

    def test_user_content_preserved_on_insert(self, tmp_path: Path) -> None:
        target = tmp_path / "CLAUDE.md"
        target.write_text("# My project rules\n\nDo not disturb.\n", encoding="utf-8")
        cfg = _config()
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        text = target.read_text(encoding="utf-8")
        assert "# My project rules" in text
        assert "Do not disturb." in text


class TestBootstrapIdempotent:
    def test_second_call_returns_unchanged(self, tmp_path: Path) -> None:
        cfg = _config()
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        report2 = bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        assert report2.action == InjectAction.UNCHANGED

    def test_unchanged_file_not_rewritten(self, tmp_path: Path) -> None:
        cfg = _config()
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        target = tmp_path / "CLAUDE.md"
        mtime_before = target.stat().st_mtime
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)
        mtime_after = target.stat().st_mtime
        assert mtime_before == mtime_after


class TestBootstrapReplaced:
    def test_different_universe_returns_replaced(self, tmp_path: Path) -> None:
        cfg1 = _config("universe-one")
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg1)
        cfg2 = _config("universe-two")
        report2 = bootstrap(harness="claude-code", project_path=tmp_path, config=cfg2)
        assert report2.action == InjectAction.REPLACED

    def test_replaced_file_contains_new_universe(self, tmp_path: Path) -> None:
        cfg1 = _config("universe-one")
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg1)
        cfg2 = _config("universe-two")
        bootstrap(harness="claude-code", project_path=tmp_path, config=cfg2)
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "universe-two" in text
        assert "universe-one" not in text


class TestBootstrapErrors:
    def test_no_active_universe_raises(self, tmp_path: Path) -> None:
        cfg = CLIConfig(universes=[], active=None)
        with pytest.raises(NoActiveUniverseError):
            bootstrap(harness="claude-code", project_path=tmp_path, config=cfg)

    def test_unknown_harness_raises(self, tmp_path: Path) -> None:
        cfg = _config()
        with pytest.raises(UnknownHarnessError):
            bootstrap(harness="unknown-harness", project_path=tmp_path, config=cfg)

    def test_nonexistent_project_path_raises(self, tmp_path: Path) -> None:
        cfg = _config()
        with pytest.raises(FileNotFoundError):
            bootstrap(
                harness="claude-code",
                project_path=tmp_path / "does-not-exist",
                config=cfg,
            )
