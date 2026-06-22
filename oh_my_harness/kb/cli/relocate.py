"""Relocate a knowledge base's data root (e.g. to an iCloud / Obsidian vault).

Moving the markdown bundles is not enough — several places point at the old
path and must be updated together, or the system ends up half-migrated:

1. The bundle files on disk (moved to the new location).
2. ``config.toml``: the ``[core] notes_root`` (data root) and the active
   knowledge base's ``notes_root`` (CLIConfig).
3. The ``CLAUDE.md`` rules block, which **hardcodes the absolute KB path**
   (re-rendered via :func:`do_bootstrap`).

The Qdrant index is unaffected: its payloads store paths *relative* to the
notes-root, and relocation preserves that relative structure — so a reindex is
optional (offered, not required).

The runner is split into :meth:`RelocateRunner.plan` (pure, no side effects —
drives ``--dry-run``) and :meth:`RelocateRunner.execute`, mirroring the
dependency-injected style of :class:`~oh_my_harness.kb.cli.reindex.ReindexRunner`.
"""

from __future__ import annotations

import contextlib
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from oh_my_harness.kb.agents.bootstrap import BootstrapReport, do_bootstrap
from oh_my_harness.kb.cli.config import (
    CLIConfig,
    OmkConfig,
    load_config,
    load_omk_config,
    save_config,
    save_omk_config,
)


class RelocateError(RuntimeError):
    """Raised when relocation cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class RelocatePlan:
    """What a relocation would do — computed without touching anything."""

    kb_name: str
    old_kb_dir: Path
    new_data_root: Path
    new_kb_dir: Path
    items_to_move: list[str] = field(default_factory=list)
    collisions: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RelocateReport:
    kb_name: str
    new_kb_dir: Path
    moved: int
    claude_md_action: str
    reindexed: bool


ConfigLoader = Callable[[], CLIConfig]
OmkLoader = Callable[[], OmkConfig]


@dataclass
class RelocateRunner:
    config_loader: ConfigLoader = load_config
    omk_loader: OmkLoader = load_omk_config

    def plan(self, new_data_root: Path, kb_name: str | None = None) -> RelocatePlan:
        """Compute the relocation plan for *kb_name* (or the active KB)."""
        cfg = self.config_loader()
        resolved = kb_name if kb_name is not None else cfg.active
        if resolved is None:
            raise RelocateError("no active knowledge base — run `omh install` or pass --kb")

        universe = cfg.get(resolved)
        if universe is None:
            raise RelocateError(f"knowledge base '{resolved}' is not in the config")

        old_kb_dir = universe.notes_root
        new_data_root = new_data_root.expanduser()
        # Use the raw KB name (matching how the CLAUDE.md path is derived in
        # bootstrap), not a slug, so the directory name stays consistent with the
        # existing layout (e.g. "knowledge_base", not "knowledge-base").
        new_kb_dir = new_data_root / resolved

        if not old_kb_dir.exists():
            raise RelocateError(f"current KB directory does not exist: {old_kb_dir}")
        if new_kb_dir.resolve() == old_kb_dir.resolve():
            raise RelocateError("new location is the same as the current one")

        items = sorted(p.name for p in old_kb_dir.iterdir())
        collisions = (
            sorted(name for name in items if (new_kb_dir / name).exists())
            if new_kb_dir.exists()
            else []
        )
        return RelocatePlan(
            kb_name=resolved,
            old_kb_dir=old_kb_dir,
            new_data_root=new_data_root,
            new_kb_dir=new_kb_dir,
            items_to_move=items,
            collisions=collisions,
        )

    def execute(self, plan: RelocatePlan, *, reindex: bool = False) -> RelocateReport:
        """Perform the move + config + CLAUDE.md updates described by *plan*."""
        if plan.collisions:
            raise RelocateError(
                "destination already contains: "
                + ", ".join(plan.collisions)
                + " — resolve the conflict before relocating"
            )

        plan.new_kb_dir.mkdir(parents=True, exist_ok=True)
        moved = 0
        for name in plan.items_to_move:
            shutil.move(str(plan.old_kb_dir / name), str(plan.new_kb_dir / name))
            moved += 1
        # Remove the now-empty old directory (ignore if it isn't empty/gone).
        with contextlib.suppress(OSError):
            plan.old_kb_dir.rmdir()

        self._update_config(plan)
        report = do_bootstrap(self._harness(), plan.kb_name)

        reindexed = False
        if reindex:
            from oh_my_harness.kb.cli.reindex import ReindexRunner

            ReindexRunner().run(plan.kb_name)
            reindexed = True

        return RelocateReport(
            kb_name=plan.kb_name,
            new_kb_dir=plan.new_kb_dir,
            moved=moved,
            claude_md_action=_action_str(report),
            reindexed=reindexed,
        )

    def _update_config(self, plan: RelocatePlan) -> None:
        omk = self.omk_loader()
        save_omk_config(replace(omk, core=replace(omk.core, notes_root=plan.new_data_root)))

        cfg = self.config_loader()
        universes = [
            replace(u, notes_root=plan.new_kb_dir) if u.name == plan.kb_name else u
            for u in cfg.universes
        ]
        save_config(replace(cfg, universes=universes))

    def _harness(self) -> str:
        return self.omk_loader().harness.active


def _action_str(report: BootstrapReport) -> str:
    return str(report.action)
