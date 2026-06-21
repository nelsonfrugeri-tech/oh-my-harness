"""Tests for the UUID↔path link index used to render in-body link references."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from oh_my_harness.kb.core import Note, NoteType, to_markdown
from oh_my_harness.kb.core.link_index import LinkEntry, LinkIndex


def _write_note(notes_root: Path, project: str, slug: str, note_id: UUID) -> Note:
    note = Note(
        id=note_id,
        slug=slug,
        title=f"Note {slug}",
        type=NoteType.REFERENCE,
        project=project,
        kb_name="engineering",
        summary="summary",
    )
    path = notes_root / project / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_markdown(note), encoding="utf-8")
    return note


def test_build_from_disk_indexes_notes(tmp_path: Path) -> None:
    a = uuid4()
    _write_note(tmp_path, "proj", "alpha", a)
    index = LinkIndex.build_from_disk(tmp_path)
    entry = index.get(a)
    assert entry is not None
    assert entry.rel_path == Path("proj/alpha.md")


def test_build_from_disk_skips_reserved_files(tmp_path: Path) -> None:
    (tmp_path / "index.md").write_text("# root\n", encoding="utf-8")
    (tmp_path / "proj").mkdir()
    (tmp_path / "proj" / "log.md").write_text("# Log\n", encoding="utf-8")
    a = uuid4()
    _write_note(tmp_path, "proj", "alpha", a)
    # Reserved files have no note front-matter; build must not choke on them and
    # must still index the real note.
    index = LinkIndex.build_from_disk(tmp_path)
    assert index.get(a) is not None


def test_resolve_link_same_directory(tmp_path: Path) -> None:
    a, b = uuid4(), uuid4()
    _write_note(tmp_path, "proj", "alpha", a)
    _write_note(tmp_path, "proj", "beta", b)
    index = LinkIndex.build_from_disk(tmp_path)
    assert index.resolve_link(b, Path("proj/alpha.md")) == "beta.md"


def test_resolve_link_cross_project(tmp_path: Path) -> None:
    a, b = uuid4(), uuid4()
    _write_note(tmp_path, "p1", "alpha", a)
    _write_note(tmp_path, "p2", "beta", b)
    index = LinkIndex.build_from_disk(tmp_path)
    assert index.resolve_link(b, Path("p1/alpha.md")) == "../p2/beta.md"


def test_resolve_link_unknown_returns_none() -> None:
    index = LinkIndex({})
    assert index.resolve_link(uuid4(), Path("p/a.md")) is None


def test_link_entry_is_returned() -> None:
    u = uuid4()
    entry = LinkEntry(uuid=u, title="T", rel_path=Path("p/a.md"))
    index = LinkIndex({u: entry})
    assert index.get(u) is entry
