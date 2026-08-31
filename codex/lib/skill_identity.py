from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Collection, Protocol


_EXTERNAL_GRAPHIFY_MARKER = Path(".graphify_version")
_READ_CHUNK_SIZE = 64 * 1024


class _UnsupportedSkillTree(RuntimeError):
    pass


class _Digest(Protocol):
    def update(self, value: bytes) -> None:
        ...


def graphify_distribution_matches(source: Path, target: Path) -> bool:
    try:
        source_digest = _tree_digest(source, ignored=())
        target_digest = _tree_digest(target, ignored=(_EXTERNAL_GRAPHIFY_MARKER,))
    except (OSError, UnicodeError, _UnsupportedSkillTree):
        return False
    return source_digest == target_digest


def _tree_digest(root: Path, ignored: Collection[Path]) -> str:
    digest = sha256()
    ignored_paths = frozenset(ignored)
    for path in _regular_files(root, ignored_paths):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(b"P")
        digest.update(len(relative).to_bytes(8, byteorder="big"))
        digest.update(relative)
        _update_digest(digest, path)
        digest.update(b"E")
    return digest.hexdigest()


def _regular_files(root: Path, ignored: frozenset[Path]) -> tuple[Path, ...]:
    files = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative in ignored:
            continue
        if path.is_symlink():
            raise _UnsupportedSkillTree(f"skill tree contains a symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise _UnsupportedSkillTree(f"skill tree contains a special file: {relative}")
        files.append(path)
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))


def _update_digest(digest: _Digest, path: Path) -> None:
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(_READ_CHUNK_SIZE), b""):
            digest.update(b"C")
            digest.update(len(chunk).to_bytes(8, byteorder="big"))
            digest.update(chunk)
