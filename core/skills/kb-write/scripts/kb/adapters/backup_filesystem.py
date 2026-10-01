import hashlib
import os
from pathlib import Path

from kb.app.errors import EnvironmentFailure

from kb.app.backup_model import BackupManifest, BackupStorePort, ManifestEntry


class FileBackupStore(BackupStorePort):
    def __init__(self, root: Path):
        self.root = root.resolve()

    def inventory(self) -> BackupManifest:
        entries, unavailable = [], []
        for base, directories, names in os.walk(self.root, followlinks=False):
            if Path(base) == self.root:
                directories[:] = [name for name in directories
                                  if name not in {'backup', '.obsidian', '.trash'}]
            for name in list(directories):
                directory = Path(base) / name
                if directory.is_symlink():
                    unavailable.append(str(directory.relative_to(self.root)))
                    directories.remove(name)
            for name in names:
                file = Path(base) / name
                relative = str(file.relative_to(self.root))
                if file.is_symlink() or name.endswith('.icloud'):
                    unavailable.append(relative)
                    continue
                try:
                    stat = file.stat()
                    if getattr(stat, 'st_flags', 0) & 0x40000000:
                        unavailable.append(relative)
                        continue
                    entries.append(ManifestEntry(relative, _digest(file), stat.st_size))
                except OSError:
                    unavailable.append(relative)
        return BackupManifest(tuple(sorted(entries, key=lambda item: item.path)),
                              tuple(sorted(unavailable)))

    def move(self, manifest: BackupManifest) -> None:
        for entry in manifest.entries:
            source = self._resolve(entry.path)
            target = self._resolve('backup/' + entry.path)
            if target.exists():
                if _digest(target) != entry.sha256 or source.exists():
                    raise EnvironmentFailure(f'Backup collision: {entry.path}')
                continue
            if _digest(source) != entry.sha256:
                raise EnvironmentFailure(f'File changed after inventory: {entry.path}')
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
        for base, directories, _ in os.walk(self.root, topdown=False):
            path = Path(base)
            if path == self.root or path.parts[len(self.root.parts)] in {'backup', '.obsidian', '.trash'}:
                continue
            if not any(path.iterdir()):
                path.rmdir()

    def verify(self, manifest: BackupManifest) -> bool:
        return all(_digest(self._resolve('backup/' + entry.path)) == entry.sha256
                   for entry in manifest.entries)

    def _resolve(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Manifest path must stay inside the bundle')
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root) or target == self.root:
            raise ValueError('Manifest path escapes the bundle')
        return target


def _digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
