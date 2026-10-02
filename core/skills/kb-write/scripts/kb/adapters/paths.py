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
    if os.path.isabs(base):
        return Path(base) / 'omh' / 'config'
    home = _home()
    if home is None:
        raise InvalidConfig('unusable home: HOME must be absolute to locate the config file')
    return home / '.config' / 'omh' / 'config'


def _from_config(name: str) -> str:
    path = config_file()
    if path.is_symlink() and not path.exists():
        raise InvalidConfig(f'unreadable config: {path}')
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except FileNotFoundError:
        return ''
    except (OSError, UnicodeDecodeError) as error:
        raise InvalidConfig(f'unreadable config: {path}') from error
    found = ''
    # Not shell syntax: `KEY=value` only. The last non-empty assignment wins, so appending a
    # corrected line takes effect; `export KEY=...` is rejected rather than silently skipped.
    for number, line in enumerate(lines, 1):
        key, separator, value = line.partition('=')
        key = key.strip()
        if not separator or key.startswith('#'):
            continue
        if len(key.split()) > 1:
            raise InvalidConfig(f'invalid line {number}: {path}')
        if key == name and value.strip():
            found = value.strip()
    return found


def resolve(name: str, flag: str | None = None) -> Path:
    if name not in NAMES:
        raise InvalidConfig(f'unknown path: {name}')
    value = (flag or '').strip() or os.environ.get(name, '').strip() or _from_config(name)
    if not value:
        raise MissingPath(name)
    path = Path(value).expanduser() if _literal(value) else None
    if path is None or not path.is_absolute() or path in (Path('/'), _home()):
        raise InvalidConfig(f'invalid path: {name}')
    return path


def _home() -> Path | None:
    # An empty HOME makes Python expand `~` to `/`; treat it as unusable instead.
    home = Path.home()
    return home if home.is_absolute() and home != Path('/') else None


def _literal(value: str) -> bool:
    # Grammar: an absolute path, or `~/` + path under an absolute HOME. No quotes, `$`, or inline
    # `#` comment (they would be kept verbatim); a `~` later in the path is a literal character.
    if any(character in value for character in '$"\'') or ' #' in value or '\t#' in value:
        return False
    if value.startswith('~/'):
        return _home() is not None
    return value.startswith('/')


def main(argv: list[str]) -> int:
    if argv == ['--config-file']:
        return _print_config_file()
    if len(argv) != 1:
        print('usage: paths.py OMH_<NAME> | --config-file', file=sys.stderr)
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


def _print_config_file() -> int:
    try:
        print(config_file())
    except InvalidConfig as error:
        print(error, file=sys.stderr)
        return UNKNOWN_EXIT
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
