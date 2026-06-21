"""On-disk note format: front-matter keys + round-trip with extension fields."""

from __future__ import annotations

from datetime import UTC, datetime

from oh_my_harness.kb.core import Note, NoteType, from_markdown, to_markdown


def _note(**overrides: object) -> Note:
    payload: dict[str, object] = {
        "title": "Desenho das tools",
        "type": NoteType.DECISION,
        "project": "oh-my-harness",
        "kb_name": "engineering",
        "summary": "Decisão arquitetural sobre as tools do MCP.",
    }
    payload.update(overrides)
    return Note.model_validate(payload)


def test_frontmatter_uses_interoperable_keys() -> None:
    md = to_markdown(_note(created_at=datetime(2026, 5, 31, tzinfo=UTC), entities=["x"]))
    # Interoperable keys, not the internal field names.
    assert "description:" in md
    assert "timestamp:" in md
    assert "tags:" in md
    assert "summary:" not in md
    assert "created_at:" not in md
    assert "entities:" not in md


def test_resource_omitted_when_absent() -> None:
    assert "resource:" not in to_markdown(_note())


def test_resource_emitted_when_present() -> None:
    md = to_markdown(_note(type=NoteType.REFERENCE, resource="https://example.com/doc"))
    assert "resource: https://example.com/doc" in md


def test_extra_meta_preserved_round_trip() -> None:
    note = _note(custom_key="value", numbers=[1, 2, 3])
    assert note.extra_meta == {"custom_key": "value", "numbers": [1, 2, 3]}
    restored = from_markdown(to_markdown(note))
    assert restored.extra_meta == {"custom_key": "value", "numbers": [1, 2, 3]}


def test_round_trip_equality_with_interoperable_keys() -> None:
    original = _note(
        created_at=datetime(2026, 5, 31, 14, 30, tzinfo=UTC),
        entities=["nelson", "qdrant"],
    )
    assert from_markdown(to_markdown(original)) == original


def test_reads_legacy_frontmatter_keys() -> None:
    legacy = (
        "---\n"
        "title: Legacy note\n"
        "type: decision\n"
        "project: oh-my-harness\n"
        "universe: engineering\n"
        "summary: summary in the legacy key\n"
        "created_at: '2026-05-31T14:30:00+00:00'\n"
        "entities:\n"
        "- a\n"
        "---\n\n"
        "corpo\n"
    )
    note = from_markdown(legacy)
    assert note.summary == "summary in the legacy key"
    assert note.kb_name == "engineering"
    assert note.entities == ["a"]
    assert note.created_at == datetime(2026, 5, 31, 14, 30, tzinfo=UTC)
