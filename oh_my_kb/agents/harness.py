"""Harness registry — maps harness names to their target file and detection signal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class Harness:
    name: str
    target_filename: str
    detection_signal: str | None
    scope: Literal["global", "project"] = "project"


HARNESS_REGISTRY: dict[str, Harness] = {
    "claude-code": Harness(
        "claude-code",
        "CLAUDE.md",
        ".claude",
        scope="global",
    ),
    "claude-desktop": Harness(
        "claude-desktop",
        "CLAUDE.md",
        None,
        scope="project",
    ),
}


class UnknownHarnessError(ValueError):
    """Raised when harness name is not in HARNESS_REGISTRY."""


def resolve_harness(name: str) -> Harness:
    """Return the :class:`Harness` for *name*, raising :class:`UnknownHarnessError` if absent."""
    try:
        return HARNESS_REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(HARNESS_REGISTRY))
        raise UnknownHarnessError(f"unknown harness '{name}'; known: {known}") from None


def target_path_for(harness: Harness, project_path: Path) -> Path:
    """Return the absolute path to the harness rules file.

    For *global* harnesses (scope='global'), the path is always resolved relative
    to the user's home directory regardless of *project_path*.  For *project*
    harnesses the file lives under *project_path*.
    """
    if harness.scope == "global":
        # Global harnesses always resolve to ~/.claude/<target_filename>
        # (or the appropriate global config directory based on detection_signal).
        if harness.detection_signal:
            return Path.home() / harness.detection_signal / harness.target_filename
        return Path.home() / harness.target_filename
    return project_path / harness.target_filename
