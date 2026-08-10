#!/usr/bin/env python3
"""Explicitly import legacy Claude MCP servers into Codex."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from lib.home_paths import configured_home, validated_home
from lib.mcp_import import import_legacy_mcps


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    default = configured_home("CODEX_HOME", ".codex")
    parser.add_argument("--codex-home", type=Path, default=default)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--dry-run", action="store_true", help="Report changes without writing."
    )
    modes.add_argument(
        "--check", action="store_true", help="Validate import changes without writing."
    )
    parsed = parser.parse_args(arguments)
    try:
        source_root = Path(__file__).resolve().parent.parent
        codex_home = validated_home(parsed.codex_home, "--codex-home", source_root)
        result = import_legacy_mcps(
            parsed.home.expanduser(),
            codex_home,
            dry_run=parsed.dry_run,
            check=parsed.check,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(result.summary())
    if parsed.check and result.added:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
