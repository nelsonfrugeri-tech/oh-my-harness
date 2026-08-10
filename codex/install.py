from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from lib.integrations import CodexIntegrations
from lib.home_paths import configured_home, validated_home
from lib.layout import InstallLayout
from lib.sync import CodexInstaller, InstallConflict


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install oh-my-harness into Codex global state."
    )
    parser.add_argument(
        "--check", action="store_true", help="Validate without changing files."
    )
    parser.add_argument("--skip-integrations", action="store_true")
    parser.add_argument(
        "--replace-global-agents",
        action="store_true",
        help="Replace an unowned legacy global AGENTS.md after creating a backup.",
    )
    parser.add_argument(
        "--migrate-legacy-agents",
        action="store_true",
        help="Back up and replace agents owned by the legacy v1 manifest.",
    )
    codex_default = configured_home("CODEX_HOME", ".codex")
    agents_default = configured_home("AGENTS_HOME", ".agents")
    parser.add_argument("--codex-home", type=Path, default=codex_default)
    parser.add_argument("--agents-home", type=Path, default=agents_default)
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    source_root = Path(__file__).resolve().parent.parent
    try:
        layout = InstallLayout(
            source_root,
            validated_home(arguments.codex_home, "--codex-home", source_root),
            validated_home(arguments.agents_home, "--agents-home", source_root),
        )
        installer = CodexInstaller(
            layout,
            arguments.replace_global_agents,
            arguments.migrate_legacy_agents,
        )
        if arguments.check:
            results = installer.validate()
        else:
            installed = installer.install()
            integrations = _install_integrations(layout, arguments.skip_integrations)
            results = (
                *installed,
                "committed: Codex core installation",
                *integrations,
            )
    except (
        InstallConflict,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print("\n".join(results))
    return 0


def _install_integrations(
    layout: InstallLayout, skip_integrations: bool
) -> tuple[str, ...]:
    if skip_integrations:
        return ("skipped: optional integrations",)
    try:
        return CodexIntegrations(layout.codex_home).install()
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return (
            "pending: integrations failed after the Codex core installation "
            f"committed successfully: {error}",
        )


if __name__ == "__main__":
    raise SystemExit(main())
