"""Write the initial Preferências do Usuário block into ~/.claude/CLAUDE.md."""

from __future__ import annotations

import platform
from datetime import UTC, datetime
from pathlib import Path

from oh_my_harness.agents.preferences.block import render_initial_block
from oh_my_harness.agents.preferences.markers import USER_PREFS_END, USER_PREFS_START
from oh_my_harness.kb.agents.injector import InjectAction, inject_block


def _now_iso() -> str:
    """Return today's UTC date as an ISO-format string (``YYYY-MM-DD``)."""
    return datetime.now(tz=UTC).date().isoformat()


def write_initial_preferences(home: Path | None = None) -> InjectAction:
    """Inject the initial user-prefs block into ``~/.claude/CLAUDE.md``.

    If the file already contains the ``omh:user-prefs`` markers with identical
    content, the file is **not** rewritten and :attr:`InjectAction.UNCHANGED` is
    returned — making the call idempotent.

    Args:
        home: Override for :func:`Path.home`.  Useful in tests to avoid
            touching the real ``~/.claude/CLAUDE.md``.

    Returns:
        :class:`~oh_my_harness.kb.agents.injector.InjectAction` indicating what
        happened (``CREATED``, ``INSERTED``, ``REPLACED``, or ``UNCHANGED``).
    """
    base = home if home is not None else Path.home()
    target = base / ".claude" / "CLAUDE.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    new_block = render_initial_block(
        now_iso=_now_iso(),
        system=platform.system(),
        machine=platform.node(),
    )

    current = target.read_text(encoding="utf-8") if target.exists() else None
    new_content, action = inject_block(
        current,
        new_block,
        start_marker=USER_PREFS_START,
        end_marker=USER_PREFS_END,
    )

    if action != InjectAction.UNCHANGED:
        target.write_text(new_content, encoding="utf-8")

    return action
