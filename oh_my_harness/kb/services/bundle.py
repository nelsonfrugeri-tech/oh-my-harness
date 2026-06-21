"""Bundle artifacts: reserved files (``index.md``/``log.md``) and the in-body
``## Related`` link block.

These are all **derived** from the notes and regenerated from disk (the
filesystem is the source of truth). The ``render_*`` functions are pure (no
I/O) so they are trivially unit-tested; :func:`materialize` does the scanning
and file writing.

Bundle layout (one bundle per project):

    <notes_root>/                 <- kb-scoped
      index.md                    <- root index, carries format_version
      <project>/                  <- a bundle
        index.md                  <- bundle index (navigation)
        log.md                    <- chronological history
        <slug>.md                 <- note documents
"""

from __future__ import annotations

from pathlib import Path

from oh_my_harness.kb.core import Note, from_markdown, slugify, to_markdown
from oh_my_harness.kb.core.link_index import RESERVED_FILENAMES, LinkIndex

FORMAT_VERSION = "0.1"

# Marker-delimited so the block can be stripped and regenerated idempotently
# without disturbing the author's body content.
RELATED_START = "<!-- omh:related:start -->"
RELATED_END = "<!-- omh:related:end -->"


def render_root_index(project_slugs: list[str]) -> str:
    """Render the kb-root ``index.md`` declaring ``format_version`` and bundles."""
    lines = [
        "---",
        f'format_version: "{FORMAT_VERSION}"',
        "---",
        "",
        "# Knowledge base",
        "",
    ]
    if project_slugs:
        for slug in sorted(project_slugs):
            lines.append(f"- [{slug}]({slug}/index.md)")
    else:
        lines.append("_No projects yet._")
    return "\n".join(lines) + "\n"


def render_bundle_index(notes: list[Note]) -> str:
    """Render a project bundle's ``index.md`` — notes grouped by ``type``.

    No front-matter (only the root index carries ``format_version``). Notes are
    siblings of this file, so links are bare ``<slug>.md``.
    """
    lines = ["# Index", ""]
    if not notes:
        lines.append("_No notes yet._")
        return "\n".join(lines) + "\n"
    by_type: dict[str, list[Note]] = {}
    for note in notes:
        by_type.setdefault(note.type.value, []).append(note)
    for type_name in sorted(by_type):
        lines.append(f"## {type_name}")
        lines.append("")
        for note in sorted(by_type[type_name], key=lambda n: n.slug):
            lines.append(f"- [{note.title}]({note.slug}.md)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_log(notes: list[Note]) -> str:
    """Render a project bundle's ``log.md`` — chronological, newest first.

    Reproducible from note metadata: each line is derived from ``created_at`` and
    ``archived``, so it can be rebuilt from disk at any time.
    """
    lines = ["# Log", ""]
    if not notes:
        lines.append("_No history yet._")
        return "\n".join(lines) + "\n"
    for note in sorted(notes, key=lambda n: n.created_at, reverse=True):
        marker = "Deprecation" if note.archived else "Creation"
        stamp = note.created_at.isoformat()
        lines.append(f"- {stamp} — **{marker}** — [{note.title}]({note.slug}.md)")
    return "\n".join(lines) + "\n"


def note_rel_path(note: Note) -> Path:
    """Path of ``note`` relative to ``notes_root`` (``<project>/<slug>.md``)."""
    return Path(slugify(note.project)) / f"{note.slug}.md"


def render_related_block(note: Note, index: LinkIndex) -> str:
    """Render the marker-delimited ``## Related`` block for ``note``.

    Returns ``""`` when the note has no outbound links. Each edge is a markdown
    path link (so external markdown tools can follow it) plus an ``omh-link``
    HTML comment carrying the UUID, so the binding survives a foreign edit to the
    link text/path. Unresolvable UUIDs render as a placeholder (broken links are
    tolerated).
    """
    if not note.links_out:
        return ""
    lines = [RELATED_START, "## Related", ""]
    for target in note.links_out:
        entry = index.get(target)
        if entry is None:
            lines.append(f"- _(unresolved)_ <!-- omh-link: {target} -->")
            continue
        link = index.resolve_link(target, note_rel_path(note))
        lines.append(f"- [{entry.title}]({link}) <!-- omh-link: {target} -->")
    lines.append(RELATED_END)
    return "\n".join(lines)


def strip_related_block(body: str) -> str:
    """Remove a previously generated ``## Related`` block from ``body``."""
    start = body.find(RELATED_START)
    if start == -1:
        return body
    end = body.find(RELATED_END, start)
    if end == -1:
        # Malformed (start without end) — drop from the start marker onward.
        return body[:start].rstrip()
    return (body[:start] + body[end + len(RELATED_END) :]).rstrip()


def apply_related_to_body(body: str, related_block: str) -> str:
    """Return ``body`` with its ``## Related`` block replaced by ``related_block``.

    Idempotent: stripping then re-appending yields a stable result, so repeated
    regeneration does not accumulate duplicate blocks.
    """
    stripped = strip_related_block(body)
    if not related_block:
        # No outbound links: leave the body untouched unless we actually removed
        # a stale block (then return the cleaned body).
        if stripped == body:
            return body
        cleaned = stripped.rstrip()
        return cleaned + "\n" if cleaned else ""
    cleaned = stripped.rstrip()
    sep = "\n\n" if cleaned else ""
    return f"{cleaned}{sep}{related_block}\n"


def materialize(notes_root: Path, *, rewrite_related: bool = False) -> None:
    """Regenerate the derived bundle files under ``notes_root`` from disk.

    Always (re)writes the reserved files: one ``index.md``/``log.md`` per project
    bundle plus a root ``index.md`` carrying ``format_version``. When
    ``rewrite_related`` is set, also regenerates every note's body ``## Related``
    block (resolved via a fresh link index) and re-serializes each note file.
    """
    parsed: list[tuple[Note, Path]] = []
    for md_path in sorted(notes_root.rglob("*.md")):
        if md_path.name in RESERVED_FILENAMES:
            continue
        try:
            note = from_markdown(md_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        parsed.append((note, md_path))

    by_project: dict[str, list[Note]] = {}
    for note, _path in parsed:
        by_project.setdefault(slugify(note.project), []).append(note)

    notes_root.mkdir(parents=True, exist_ok=True)
    (notes_root / "index.md").write_text(
        render_root_index(list(by_project)), encoding="utf-8"
    )
    for project_slug, notes in by_project.items():
        bundle_root = notes_root / project_slug
        bundle_root.mkdir(parents=True, exist_ok=True)
        (bundle_root / "index.md").write_text(
            render_bundle_index(notes), encoding="utf-8"
        )
        (bundle_root / "log.md").write_text(render_log(notes), encoding="utf-8")

    if not rewrite_related:
        return

    index = LinkIndex.build_from_disk(notes_root)
    for note, path in parsed:
        related = render_related_block(note, index)
        new_body = apply_related_to_body(note.body, related)
        path.write_text(
            to_markdown(note.model_copy(update={"body": new_body})), encoding="utf-8"
        )
