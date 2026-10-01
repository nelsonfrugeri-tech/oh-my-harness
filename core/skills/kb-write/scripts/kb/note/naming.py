from enum import StrEnum
import re

RESERVED_FILES = frozenset(('index.md', 'INSTRUCTION.md'))
EXCLUDED_DIRS = frozenset(('.history', '.pending', 'backup', '.obsidian', '.trash'))
NAME_PATTERN = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+){0,2}')


class DirectoryKind(StrEnum):
    NOTE = 'note'
    ENTITY = 'entity'
    EXCLUDED = 'excluded'


def check_name(name: str, *, parent: str | None = None) -> tuple[str, ...]:
    if not NAME_PATTERN.fullmatch(name):
        return ('name must be lowercase kebab-case, start with a letter and contain at most 3 words',)
    if parent and set(parent.split('-')).issubset(name.split('-')):
        return ('name must not repeat its parent',)
    if name in EXCLUDED_DIRS or name in ('index', 'instruction'):
        return ('name is reserved',)
    return ()


def classify_dir(name: str, filenames: tuple[str, ...]) -> DirectoryKind:
    if name in EXCLUDED_DIRS or name.startswith('.'):
        return DirectoryKind.EXCLUDED
    if name + '.md' in filenames:
        return DirectoryKind.NOTE
    return DirectoryKind.ENTITY
