from dataclasses import dataclass


@dataclass(frozen=True)
class IndexEntry:
    entity_path: tuple[str, ...]
    description: str


def missing_entries(entity_paths: tuple[tuple[str, ...], ...],
                    entries: tuple[IndexEntry, ...]) -> tuple[tuple[str, ...], ...]:
    listed = {entry.entity_path for entry in entries}
    return tuple(path for path in entity_paths if path not in listed)


def render_index(entries: tuple[IndexEntry, ...]) -> str:
    lines = ['# Index', '']
    for entry in sorted(entries, key=lambda value: value.entity_path):
        path = '/'.join(entry.entity_path)
        indent = '  ' * (len(entry.entity_path) - 1)
        lines.append(f'{indent}- [{entry.entity_path[-1]}/]({path}/) — {entry.description}')
    return '\n'.join(lines) + '\n'
