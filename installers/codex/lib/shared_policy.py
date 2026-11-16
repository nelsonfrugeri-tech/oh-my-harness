"""Expose the shared policy renderer in installers/policy to the Codex adapter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

_INSTALLERS: Final = Path(__file__).resolve().parents[2]
if str(_INSTALLERS) not in sys.path:
    sys.path.insert(0, str(_INSTALLERS))

from policy.permissions import load_policy  # noqa: E402
from policy.render import RULES_HEADER, render_codex_filesystem, render_codex_rules  # noqa: E402

__all__ = ("RULES_HEADER", "load_policy", "render_codex_filesystem", "render_codex_rules")
