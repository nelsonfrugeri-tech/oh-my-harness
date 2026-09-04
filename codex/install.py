from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from lib.integrations import CodexIntegrations
from lib.layout import InstallLayout
from lib.sync import CodexInstaller, InstallConflict


_MINIMUM_CODEX_VERSION = (0, 138, 0)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Instala oh-my-harness no estado global do Codex.")
    parser.add_argument("--check", action="store_true", help="Valida sem alterar arquivos.")
    parser.add_argument("--skip-integrations", action="store_true")
    parser.add_argument(
        "--replace-global-agents",
        action="store_true",
        help="Substitui um AGENTS.md global legado sem dono após criar um backup.",
    )
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--agents-home", type=Path, default=Path.home() / ".agents")
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    source_root = Path(__file__).resolve().parent.parent
    layout = InstallLayout(
        source_root,
        arguments.codex_home.expanduser(),
        arguments.agents_home.expanduser(),
    )
    installer = CodexInstaller(layout, arguments.replace_global_agents)
    try:
        _require_permissions_profiles()
        if arguments.check:
            results = installer.validate()
        else:
            installed = installer.install()
            integrations = () if arguments.skip_integrations else CodexIntegrations().install()
            results = (*installed, *integrations)
    except (
        InstallConflict,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1
    print("\n".join(results))
    return 0


def _require_permissions_profiles() -> None:
    result = subprocess.run(
        ["codex", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)
    if match is None:
        raise InstallConflict("não foi possível determinar a versão do Codex")
    version = tuple(int(part) for part in match.groups())
    if version < _MINIMUM_CODEX_VERSION:
        required = ".".join(str(part) for part in _MINIMUM_CODEX_VERSION)
        raise InstallConflict(f"Codex {required} ou posterior é necessário")


if __name__ == "__main__":
    raise SystemExit(main())
