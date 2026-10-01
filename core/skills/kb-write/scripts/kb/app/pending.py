import json
from dataclasses import dataclass

from kb.app.ports import NoteStorePort


@dataclass(frozen=True)
class PendingMetadata:
    reason: str
    descriptions: tuple[tuple[str, str], ...]
    approved_degraded: bool
    updating: bool
    base_id: str | None
    base_version: int | None
    at: str
    created_dirs: tuple[str, ...] = ()


def paths(path: str) -> tuple[str, str]:
    folder, name = path.rsplit('/', 1)
    return f'{folder}/.pending/{name}', f'{folder}/.pending/metadata.json'


def save(store: NoteStorePort, path: str, metadata: PendingMetadata) -> None:
    from dataclasses import asdict
    store.write_text(paths(path)[1], json.dumps(asdict(metadata), ensure_ascii=False))


def load(store: NoteStorePort, path: str) -> PendingMetadata:
    raw = json.loads(store.read_text(paths(path)[1]))
    raw['created_dirs'] = tuple(raw.get('created_dirs', ()))
    raw['descriptions'] = tuple(tuple(item) for item in raw['descriptions'])
    return PendingMetadata(**raw)


def created_dirs(store: NoteStorePort, path: str) -> tuple[str, ...]:
    parts = path.split('/')[:-1]
    parents = ['/'.join(parts[:depth]) for depth in range(1, len(parts) + 1)]
    parents.append('/'.join(parts) + '/.pending')
    existing = set(store.directories())
    return tuple(parent for parent in parents if parent not in existing)
