"""Tests for the bundle artifact renderers (pure functions)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from oh_my_harness.kb.core import Note, NoteType
from oh_my_harness.kb.core.link_index import LinkEntry, LinkIndex
from oh_my_harness.kb.services.bundle import (
    RELATED_END,
    RELATED_START,
    apply_related_to_body,
    render_bundle_index,
    render_log,
    render_related_block,
    render_root_index,
    strip_related_block,
)


def _note(slug: str, **overrides: object) -> Note:
    payload: dict[str, object] = {
        "slug": slug,
        "title": f"Note {slug}",
        "type": NoteType.DECISION,
        "project": "oh-my-harness",
        "kb_name": "engineering",
        "summary": "summary",
    }
    payload.update(overrides)
    return Note.model_validate(payload)


def test_render_root_index_has_format_version_and_links() -> None:
    md = render_root_index(["proj-b", "proj-a"])
    assert 'format_version: "0.1"' in md
    assert "- [proj-a](proj-a/index.md)" in md
    assert md.index("proj-a") < md.index("proj-b")


def test_render_root_index_empty() -> None:
    md = render_root_index([])
    assert 'format_version: "0.1"' in md
    assert "No projects yet" in md


def test_render_bundle_index_groups_by_type() -> None:
    notes = [_note("a", type=NoteType.DECISION), _note("b", type=NoteType.EVENT)]
    md = render_bundle_index(notes)
    assert "## decision" in md
    assert "## event" in md
    assert "- [Note a](a.md)" in md


def test_render_log_newest_first_and_marks_archived() -> None:
    old = _note("old", created_at=datetime(2026, 1, 1, tzinfo=UTC))
    new = _note("new", created_at=datetime(2026, 6, 1, tzinfo=UTC), archived=True)
    md = render_log([old, new])
    assert md.index("new") < md.index("old")
    assert "Deprecation" in md
    assert "Creation" in md


def test_render_related_block_renders_links_with_uuid_comment() -> None:
    target_id = uuid4()
    index = LinkIndex(
        {target_id: LinkEntry(target_id, "Target", Path("oh-my-harness/target.md"))}
    )
    note = _note("source", links_out=[target_id])
    block = render_related_block(note, index)
    assert block.startswith(RELATED_START)
    assert block.rstrip().endswith(RELATED_END)
    assert "## Related" in block
    assert "[Target](target.md)" in block
    assert f"<!-- omh-link: {target_id} -->" in block


def test_render_related_block_empty_when_no_links() -> None:
    assert render_related_block(_note("x"), LinkIndex({})) == ""


def test_render_related_block_unresolved_placeholder() -> None:
    missing = uuid4()
    block = render_related_block(_note("source", links_out=[missing]), LinkIndex({}))
    assert "_(unresolved)_" in block
    assert f"<!-- omh-link: {missing} -->" in block


def test_apply_related_is_idempotent() -> None:
    block = f"{RELATED_START}\n## Related\n\n- x\n{RELATED_END}"
    body = "# Context\n\ntexto"
    once = apply_related_to_body(body, block)
    twice = apply_related_to_body(once, block)
    assert once == twice
    assert "# Context" in once
    assert once.count(RELATED_START) == 1


def test_strip_related_removes_block() -> None:
    body = f"# Context\n\ntexto\n\n{RELATED_START}\n## Related\n- x\n{RELATED_END}\n"
    assert strip_related_block(body).strip() == "# Context\n\ntexto"


def test_apply_empty_block_clears_existing() -> None:
    body = f"# Context\n\n{RELATED_START}\n## Related\n- x\n{RELATED_END}"
    cleared = apply_related_to_body(body, "")
    assert RELATED_START not in cleared
    assert "# Context" in cleared
