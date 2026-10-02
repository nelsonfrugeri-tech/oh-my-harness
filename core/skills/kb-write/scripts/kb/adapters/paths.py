"""Resolve one oh-my-harness machine path: CLI flag > env var > XDG config file > missing.

Standard library only: hooks and skills run this file by path before the KB venv exists.
Usage as a script: ``python3 paths.py OMH_KB_ROOT`` prints the path, or exits 3 with
``missing path: OMH_KB_ROOT`` on stderr. A missing value is never defaulted. Any other failure
(unknown name, non-absolute value, unreadable config) exits 2, so callers never mistake a broken
configuration for an absent one. Runs on Python 3.9, the oldest system python3 hooks may meet.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

NAMES = frozenset({'OMH_KB_ROOT', 'OMH_KB_RUNTIME', 'OMH_SITES_ROOT'})
MISSING_EXIT = 3
UNKNOWN_EXIT = 2


class MissingPath(RuntimeError):
    """No layer defines the path; the main session must ask the user and record it."""

    def __init__(self, name: str):
        super().__init__(f'missing path: {name}')


class InvalidConfig(ValueError):
    """The configuration exists but cannot yield a usable path; the user must fix it."""


def config_file() -> Path:
    # XDG Base Directory: a relative XDG_CONFIG_HOME is invalid and must be ignored.
    base = os.environ.get('XDG_CONFIG_HOME', '')
    root = Path(base) if os.path.isabs(base) else Path.home() / '.config'
    return root / 'omh' / 'config'


def _from_config(name: str) -> str:
    path = config_file()
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except FileNotFoundError:
        return ''
    except (OSError, UnicodeDecodeError) as error:
        raise InvalidConfig(f'unreadable config: {path}') from error
    for line in lines:
        key, separator, value = line.partition('=')
        if separator and not key.lstrip().startswith('#') and key.strip() == name and value.strip():
            return value.strip()
    return ''


def resolve(name: str, flag: str | None = None) -> Path:
    if name not in NAMES:
        raise InvalidConfig(f'unknown path: {name}')
    value = flag or os.environ.get(name, '') or _from_config(name)
    if not value:
        raise MissingPath(name)
    path = Path(value).expanduser()
    # Values are literal: no quotes, no $VAR, no relative path that would land in the cwd.
    if not path.is_absolute():
        raise InvalidConfig(f'invalid path: {name}')
    return path


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print('usage: paths.py OMH_<NAME>', file=sys.stderr)
        return UNKNOWN_EXIT
    try:
        print(resolve(argv[0]))
    except MissingPath as error:
        print(error, file=sys.stderr)
        return MISSING_EXIT
    except InvalidConfig as error:
        print(error, file=sys.stderr)
        return UNKNOWN_EXIT
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
