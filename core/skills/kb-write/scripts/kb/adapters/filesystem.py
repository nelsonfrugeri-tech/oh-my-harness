from __future__ import annotations

import os
import tempfile
from pathlib import Path

from kb.app.ports import NoteStorePort
from kb.note.model import Note


class FileNoteStore(NoteStorePort):
    def __init__(self, root: Path):
        self.root = root.resolve()

    def resolve(self, path: str) -> Path:
        relative = Path(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Path must be relative to the bundle')
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError('Path escapes the bundle')
        return target

    def read(self, path: str, logical_path: str | None = None) -> Note:
        from kb.adapters.markdown import parse_note
        return parse_note(self.read_text(path), logical_path or path)

    def write(self, note: Note, path: str | None = None) -> None:
        from kb.adapters.markdown import render_note
        self.write_text(path or note.path.relative_path, render_note(note))

    def read_text(self, path: str) -> str:
        return self.resolve(path).read_text(encoding='utf-8')

    def write_text(self, path: str, text: str) -> None:
        target = self.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.' + target.name + '.',
                                                suffix='.tmp', dir=target.parent)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def exists(self, path: str) -> bool:
        return self.resolve(path).is_file()

    def remove(self, path: str) -> None:
        self.resolve(path).unlink(missing_ok=True)

    def prune(self, paths: tuple[str, ...]) -> None:
        for path in sorted(paths, key=lambda value: len(value.split('/')), reverse=True):
            try:
                self.resolve(path).rmdir()
            except OSError:
                continue

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(str(path.relative_to(self.root))
                            for path in self.root.rglob('*.md')
                            if not path.is_symlink()
                            and path.resolve().is_relative_to(self.root)))

    def files(self) -> tuple[str, ...]:
        return tuple(sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*')
                            if path.is_file() and not path.is_symlink()
                            and path.resolve().is_relative_to(self.root)))

    def directories(self) -> tuple[str, ...]:
        return tuple(sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*')
                            if path.is_dir() and not path.is_symlink()
                            and path.resolve().is_relative_to(self.root)))
