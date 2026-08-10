from __future__ import annotations

import errno
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal


@dataclass(frozen=True)
class _Preimage:
    path: Path
    kind: Literal["missing", "file", "symlink"]
    content: Path | None = None
    link_target: Path | None = None


@contextmanager
def install_transaction(
    paths: tuple[Path, ...], conflict: type[RuntimeError]
) -> Iterator[None]:
    unique_paths = tuple(dict.fromkeys(paths))
    missing_directories = _missing_directories(unique_paths)
    with tempfile.TemporaryDirectory(prefix="omh-install-rollback-") as temporary:
        root = Path(temporary)
        preimages = tuple(
            _capture(path, root / str(index), conflict)
            for index, path in enumerate(unique_paths)
        )
        try:
            yield
        except BaseException as failure:
            errors = _rollback(preimages, missing_directories)
            if errors:
                details = "; ".join(errors)
                raise conflict(f"installer rollback failed: {details}") from failure
            raise


def _capture(
    path: Path, storage: Path, conflict: type[RuntimeError]
) -> _Preimage:
    if path.is_symlink():
        return _Preimage(path, "symlink", link_target=path.readlink())
    if path.is_file():
        shutil.copy2(path, storage)
        return _Preimage(path, "file", content=storage)
    if not path.exists():
        return _Preimage(path, "missing")
    raise conflict(f"unsupported transactional install target: {path}")


def _missing_directories(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    missing: set[Path] = set()
    for path in paths:
        candidate = path.parent
        while not candidate.exists() and not candidate.is_symlink():
            missing.add(candidate)
            candidate = candidate.parent
    return tuple(sorted(missing, key=lambda path: len(path.parts), reverse=True))


def _rollback(
    preimages: tuple[_Preimage, ...], missing_directories: tuple[Path, ...]
) -> tuple[str, ...]:
    errors: list[str] = []
    for preimage in reversed(preimages):
        try:
            _restore(preimage)
        except OSError as error:
            errors.append(f"restore {preimage.path}: {error}")
    errors.extend(_remove_created_directories(missing_directories))
    return tuple(errors)


def _restore(preimage: _Preimage) -> None:
    _remove_leaf(preimage.path)
    if preimage.kind == "missing":
        return
    if preimage.kind == "file" and preimage.content is not None:
        shutil.copy2(preimage.content, preimage.path)
        return
    if preimage.kind == "symlink" and preimage.link_target is not None:
        preimage.path.symlink_to(preimage.link_target)
        return
    raise OSError(f"invalid transaction preimage: {preimage.path}")


def _remove_leaf(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.exists():
        raise OSError(f"transaction target became a directory: {path}")


def _remove_created_directories(paths: tuple[Path, ...]) -> tuple[str, ...]:
    errors: list[str] = []
    for path in paths:
        try:
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError as error:
            if error.errno not in {errno.ENOTEMPTY, errno.EEXIST}:
                errors.append(f"remove directory {path}: {error}")
    return tuple(errors)
