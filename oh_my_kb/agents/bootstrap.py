"""Bootstrap — inject the kb-mcp rules block into a harness rules file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from oh_my_kb.agents.harness import resolve_harness, target_path_for
from oh_my_kb.agents.injector import InjectAction, inject_block
from oh_my_kb.agents.template import render_rules
from oh_my_kb.cli.config import CLIConfig


@dataclass(frozen=True, slots=True)
class BootstrapReport:
    harness: str
    universe: str
    target_file: Path
    action: InjectAction
    bytes_written: int


class NoActiveUniverseError(RuntimeError):
    """Raised when CLIConfig.active is None."""


def bootstrap(
    *,
    harness: str,
    project_path: Path,
    config: CLIConfig,
) -> BootstrapReport:
    """Inject the kb-mcp rules block into *harness*'s target file.

    Raises:
        NoActiveUniverseError: if ``config.active`` is ``None``.
        UnknownHarnessError: if *harness* is not in :data:`HARNESS_REGISTRY`.
        FileNotFoundError: if *project_path* does not exist or is not a directory.
    """
    if config.active is None:
        raise NoActiveUniverseError("no active universe; run `omk install` first")

    h = resolve_harness(harness)  # raises UnknownHarnessError if unknown

    if not project_path.is_dir():
        raise FileNotFoundError(
            f"project path does not exist or is not a directory: {project_path}"
        )

    target = target_path_for(h, project_path)
    universe = config.active

    new_block = render_rules(universe)

    current = target.read_text(encoding="utf-8") if target.exists() else None
    new_content, action = inject_block(current, new_block)

    if action != InjectAction.UNCHANGED:
        target.write_text(new_content, encoding="utf-8")

    return BootstrapReport(
        harness=h.name,
        universe=universe,
        target_file=target,
        action=action,
        bytes_written=len(new_content.encode("utf-8")),
    )
