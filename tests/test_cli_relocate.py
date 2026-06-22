"""Tests for `omh kb relocate` — moving a KB's data root.

Covers the plan/execute split: directory computation + collision detection, the
file move, and that config.toml (both sections) and the CLAUDE.md block are
updated to the new path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from oh_my_harness.kb.cli.config import (
    CLIConfig,
    OmkConfig,
    OmkCoreConfig,
    OmkHarnessConfig,
    Universe,
    load_config,
    load_omk_config,
    save_config,
    save_omk_config,
)
from oh_my_harness.kb.cli.relocate import RelocateError, RelocateRunner
from oh_my_harness.kb.services import collection_name_for


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setenv("OMH_CONFIG_DIR", str(tmp_path / "cfg"))
    old_root = tmp_path / "old"
    kb_dir = old_root / "test_kb"
    (kb_dir / "proj").mkdir(parents=True)
    (kb_dir / "proj" / "note.md").write_text("note", encoding="utf-8")

    save_omk_config(
        OmkConfig(
            core=OmkCoreConfig(notes_root=old_root, default_kb="test_kb"),
            harness=OmkHarnessConfig(active="claude-code"),
        )
    )
    save_config(
        CLIConfig(
            universes=[
                Universe(
                    name="test_kb",
                    notes_root=kb_dir,
                    collection=collection_name_for("test_kb"),
                )
            ],
            active="test_kb",
        )
    )
    return {
        "tmp": tmp_path,
        "old_root": old_root,
        "kb_dir": kb_dir,
        "home": tmp_path / "home",
        "new_root": tmp_path / "new",
    }


def test_plan_computes_dirs_and_items(env: dict[str, Any]) -> None:
    plan = RelocateRunner().plan(env["new_root"])
    assert plan.kb_name == "test_kb"
    assert plan.old_kb_dir == env["kb_dir"]
    assert plan.new_kb_dir == env["new_root"] / "test_kb"
    assert "proj" in plan.items_to_move
    assert plan.collisions == []


def test_plan_same_location_raises(env: dict[str, Any]) -> None:
    with pytest.raises(RelocateError, match="same"):
        RelocateRunner().plan(env["old_root"])


def test_execute_moves_files_and_updates_config_and_claude_md(env: dict[str, Any]) -> None:
    runner = RelocateRunner()
    plan = runner.plan(env["new_root"])
    with patch.object(Path, "home", return_value=env["home"]):
        report = runner.execute(plan)

    new_kb = env["new_root"] / "test_kb"
    # Files moved, old dir gone.
    assert (new_kb / "proj" / "note.md").read_text(encoding="utf-8") == "note"
    assert not env["kb_dir"].exists()
    # Both config sections updated.
    assert load_omk_config().core.notes_root == env["new_root"]
    moved_universe = load_config().get("test_kb")
    assert moved_universe is not None
    assert moved_universe.notes_root == new_kb
    # CLAUDE.md block re-rendered with the new absolute path.
    claude_md = (env["home"] / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    assert str(new_kb) in claude_md
    assert report.moved == 1


def test_execute_aborts_on_collision(env: dict[str, Any]) -> None:
    (env["new_root"] / "test_kb" / "proj").mkdir(parents=True)  # pre-existing 'proj'
    runner = RelocateRunner()
    plan = runner.plan(env["new_root"])
    assert "proj" in plan.collisions
    with pytest.raises(RelocateError, match="already contains"):
        runner.execute(plan)
