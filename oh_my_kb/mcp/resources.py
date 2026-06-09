"""Static MCP resources served by ``o-kb-mcp``.

The scribe skill (``skill://scribe/SKILL.md``) and its body template
(``skill://scribe/template.md``) are served from disk **on every request**
so editing the file shows up on the next read without restarting the
server. The disk files live next to this module under ``skills/scribe/<locale>/``,
so the package install is the unit of distribution and the running server is
the unit of editing.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import NamedTuple

from mcp.types import Annotations, Resource

from oh_my_kb.i18n import DEFAULT_LOCALE, resolve_locale_path

SKILLS_DIR = Path(__file__).parent / "skills"
SCRIBE_DIR = SKILLS_DIR / "scribe"

SCRIBE_SKILL_URI = "skill://scribe/SKILL.md"
SCRIBE_TEMPLATE_URI = "skill://scribe/template.md"

_URI_TO_FILENAME: dict[str, str] = {
    SCRIBE_SKILL_URI: "SKILL.md",
    SCRIBE_TEMPLATE_URI: "template.md",
}

# Regex to extract content_version from HTML comment frontmatter.
# Matches patterns like: <!-- content_version: 1.0.0 | ... -->
_VERSION_RE = re.compile(r"content_version:\s*([^\s|]+)")

# Short resource ID used by the CLI.
_URI_TO_RESOURCE_ID: dict[str, str] = {
    SCRIBE_SKILL_URI: "skills/scribe",
    SCRIBE_TEMPLATE_URI: "skills/scribe-template",
}


class ResourceMeta(NamedTuple):
    """Metadata computed from a resource file on disk."""

    content_version: str
    sha256: str


def _read_file_for_locale(uri: str, locale: str = DEFAULT_LOCALE) -> str:
    """Read the raw content of a resource file from disk."""
    filename = _URI_TO_FILENAME.get(uri)
    if filename is None:
        raise ValueError(f"unknown resource uri: {uri!r}")
    return resolve_locale_path(SCRIBE_DIR, filename, locale).read_text(encoding="utf-8")


def parse_content_version(content: str) -> str:
    """Extract the ``content_version`` from an HTML-comment frontmatter.

    Returns ``"0.0.0"`` when the frontmatter is absent or unparseable so
    callers always receive a valid SemVer string.
    """
    match = _VERSION_RE.search(content)
    if match:
        return match.group(1).strip()
    return "0.0.0"


def compute_sha256(content: str) -> str:
    """Return lowercase hex SHA-256 of *content* encoded as UTF-8."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def resource_meta(uri: str, locale: str = DEFAULT_LOCALE) -> ResourceMeta:
    """Return version + sha256 for the resource at *uri* / *locale*."""
    content = _read_file_for_locale(uri, locale)
    return ResourceMeta(
        content_version=parse_content_version(content),
        sha256=compute_sha256(content),
    )


def list_scribe_resources(locale: str = DEFAULT_LOCALE) -> list[Resource]:
    """Return the static catalog of scribe resources with version metadata.

    The ``annotations`` dict on each resource carries ``content_version``
    and ``sha256`` so CLI clients can compare against the local manifest
    without a full download.
    """
    results: list[Resource] = []
    for uri, name, title, description in [
        (
            SCRIBE_SKILL_URI,
            "scribe",
            "Scribe skill",
            (
                "Playbook for writing well-formed notes via kb_write — type "
                "decision, summary as dense prose, entity extraction, "
                "links via kb_search. Read once per kb_write call until "
                "o-kb-agents automates it."
            ),
        ),
        (
            SCRIBE_TEMPLATE_URI,
            "scribe-template",
            "Scribe — note body template",
            (
                "Required structure of the note body, with per-type "
                "sections. The summary is separate prose, not part of "
                "this template."
            ),
        ),
    ]:
        meta = resource_meta(uri, locale)
        results.append(
            Resource(
                uri=uri,  # type: ignore[arg-type]
                name=name,
                title=title,
                description=description,
                mimeType="text/markdown",
                annotations=Annotations(  # type: ignore[call-arg]
                    content_version=meta.content_version,
                    sha256=meta.sha256,
                    resource_id=_URI_TO_RESOURCE_ID[uri],
                ),
            )
        )
    return results


def read_scribe_resource(uri: str, locale: str = DEFAULT_LOCALE) -> str:
    """Return the markdown content of the resource at ``uri`` for ``locale``.

    Reads the disk file each call — edits to the markdown reflect on the
    next read without a server restart.

    ``locale`` defaults to ``DEFAULT_LOCALE``; the MCP server call site passes
    no locale so existing ``read_scribe_resource(uri)`` callers are unaffected.
    """
    return _read_file_for_locale(uri, locale)
