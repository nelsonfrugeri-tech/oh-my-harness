from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class BackupManifest:
    entries: tuple[ManifestEntry, ...]
    unavailable: tuple[str, ...] = ()


@dataclass(frozen=True)
class Planned:
    manifest: BackupManifest


@dataclass(frozen=True)
class Applied:
    files: int
    manifest_sha256: str
    legacy_points: int


@dataclass(frozen=True)
class LegacyPending:
    files: int
    reason: str


class BackupStorePort(Protocol):
    def inventory(self) -> BackupManifest: ...
    def move(self, manifest: BackupManifest) -> None: ...
    def verify(self, manifest: BackupManifest) -> bool: ...
