"""UUID↔path index for resolving in-body link references.

A note's canonical graph lives in its ``links_out`` front-matter as UUIDs, which
stay valid across renames. For interoperability the same edges are also rendered
as markdown path links in the note body, so any plain markdown tool can follow
them. This index maps each note's UUID to its on-disk path so the body
``## Related`` renderer can turn those UUIDs into relative path links.

The index is **derived and fully rebuildable from disk** — never a source of
truth. It is rebuilt from the front-matter ``id`` + actual file path of every
note, so manual edits or moves self-heal on the next rebuild.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from oh_my_harness.kb.core.serialization import from_markdown

# Reserved filenames that are navigation/history, never note documents.
RESERVED_FILENAMES: frozenset[str] = frozenset({"index.md", "log.md"})


@dataclass(frozen=True, slots=True)
class LinkEntry:
    """A resolved note location: its title and path relative to ``notes_root``."""

    uuid: UUID
    title: str
    rel_path: Path


class LinkIndex:
    """In-memory UUID → :class:`LinkEntry` map, built by scanning disk."""

    def __init__(self, entries: dict[UUID, LinkEntry]) -> None:
        self._entries = entries

    @classmethod
    def build_from_disk(cls, notes_root: Path) -> LinkIndex:
        """Scan ``notes_root`` for note ``.md`` files and index id → path.

        Reserved files (``index.md``/``log.md``) and unparseable files are
        skipped — a malformed note must not abort the index build.
        """
        entries: dict[UUID, LinkEntry] = {}
        for md_path in sorted(notes_root.rglob("*.md")):
            if md_path.name in RESERVED_FILENAMES:
                continue
            try:
                note = from_markdown(md_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            entries[note.id] = LinkEntry(
                uuid=note.id,
                title=note.title,
                rel_path=md_path.relative_to(notes_root),
            )
        return cls(entries)

    def get(self, uuid: UUID) -> LinkEntry | None:
        return self._entries.get(uuid)

    def resolve_link(self, uuid: UUID, from_rel_path: Path) -> str | None:
        """Return a relative markdown target for ``uuid``.

        ``from_rel_path`` is the source note's path relative to ``notes_root``.
        Returns ``None`` when the target is unknown — a broken link, which the
        caller renders as a placeholder (broken links are tolerated).
        """
        entry = self._entries.get(uuid)
        if entry is None:
            return None
        rel = os.path.relpath(entry.rel_path, start=from_rel_path.parent)
        return Path(rel).as_posix()
