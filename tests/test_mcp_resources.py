"""Resource handlers — `skill://scribe/SKILL.md` and template.

We test the resources module directly (it's where the disk read happens)
and verify the wiring at the Server level by calling the same list/read
helpers the SDK calls behind the decorator.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from oh_my_kb.mcp import resources as resources_module
from oh_my_kb.mcp.resources import (
    SCRIBE_DIR,
    SCRIBE_SKILL_URI,
    SCRIBE_TEMPLATE_URI,
    compute_sha256,
    list_scribe_resources,
    parse_content_version,
    read_scribe_resource,
    resource_meta,
)


def test_list_includes_both_scribe_resources() -> None:
    resources = list_scribe_resources()
    uris = {str(r.uri) for r in resources}
    assert SCRIBE_SKILL_URI in uris
    assert SCRIBE_TEMPLATE_URI in uris


def test_resources_carry_useful_metadata() -> None:
    resources = list_scribe_resources()
    by_uri = {str(r.uri): r for r in resources}
    skill = by_uri[SCRIBE_SKILL_URI]
    template = by_uri[SCRIBE_TEMPLATE_URI]

    assert skill.mimeType == "text/markdown"
    assert template.mimeType == "text/markdown"
    assert skill.description and "kb_write" in skill.description
    assert template.description and "template" in template.description.lower()


def test_list_exposes_content_version_in_annotations() -> None:
    """list_scribe_resources() must include content_version in annotations."""
    resources = list_scribe_resources()
    for r in resources:
        assert r.annotations is not None, f"annotations missing on {r.uri}"
        extra = r.annotations.model_extra or {}
        assert "content_version" in extra, f"content_version missing on {r.uri}"
        version = extra["content_version"]
        # Must be a SemVer-style string like "1.0.0"
        assert re.match(r"^\d+\.\d+\.\d+$", version), (
            f"Expected SemVer, got {version!r} on {r.uri}"
        )


def test_list_exposes_sha256_in_annotations() -> None:
    """list_scribe_resources() must include sha256 in annotations."""
    resources = list_scribe_resources()
    for r in resources:
        assert r.annotations is not None
        extra = r.annotations.model_extra or {}
        assert "sha256" in extra, f"sha256 missing on {r.uri}"
        sha = extra["sha256"]
        assert len(sha) == 64, f"Expected 64-char hex, got len={len(sha)}"
        assert re.match(r"^[0-9a-f]{64}$", sha), f"Not lowercase hex: {sha!r}"


def test_list_exposes_resource_id_in_annotations() -> None:
    """list_scribe_resources() must include resource_id for CLI use."""
    resources = list_scribe_resources()
    by_uri = {str(r.uri): r for r in resources}
    skill = by_uri[SCRIBE_SKILL_URI]
    tmpl = by_uri[SCRIBE_TEMPLATE_URI]
    assert skill.annotations is not None
    assert tmpl.annotations is not None
    assert (skill.annotations.model_extra or {}).get("resource_id") == "skills/scribe"
    assert (tmpl.annotations.model_extra or {}).get("resource_id") == "skills/scribe-template"


def test_read_skill_returns_file_content() -> None:
    text = read_scribe_resource(SCRIBE_SKILL_URI)
    # Sanity check: must mention the major sections the spec requires.
    assert "Scribe" in text
    assert "summary" in text
    assert "type" in text
    assert "kb_search" in text
    assert "template" in text


def test_read_template_returns_file_content() -> None:
    text = read_scribe_resource(SCRIBE_TEMPLATE_URI)
    assert "template" in text.lower()
    assert "decision" in text.lower()
    assert "summary" in text.lower()


def test_read_unknown_uri_raises() -> None:
    with pytest.raises(ValueError):
        read_scribe_resource("skill://does/not/exist.md")


def test_edits_to_disk_reflect_on_re_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resources are read from disk **on every call** so edits show up live."""
    with tempfile.TemporaryDirectory() as td:
        fake_scribe_dir = Path(td) / "scribe"
        fake_locale_dir = fake_scribe_dir / "pt-BR"
        fake_locale_dir.mkdir(parents=True)
        fake = fake_locale_dir / "SKILL.md"
        fake.write_text("version-one", encoding="utf-8")
        monkeypatch.setattr(resources_module, "SCRIBE_DIR", fake_scribe_dir)

        assert read_scribe_resource(SCRIBE_SKILL_URI) == "version-one"

        fake.write_text("version-two", encoding="utf-8")
        assert read_scribe_resource(SCRIBE_SKILL_URI) == "version-two"


def test_skill_and_template_files_exist_in_package() -> None:
    from oh_my_kb.i18n import DEFAULT_LOCALE

    assert (SCRIBE_DIR / DEFAULT_LOCALE / "SKILL.md").is_file()
    assert (SCRIBE_DIR / DEFAULT_LOCALE / "template.md").is_file()


# ---------------------------------------------------------------------------
# parse_content_version
# ---------------------------------------------------------------------------


def test_parse_content_version_semver() -> None:
    content = "<!-- content_version: 1.0.0 | locale: pt-BR -->\n# Title"
    assert parse_content_version(content) == "1.0.0"


def test_parse_content_version_legacy_int() -> None:
    content = "<!-- content_version: 2 | locale: pt-BR -->\n# Title"
    assert parse_content_version(content) == "2"


def test_parse_content_version_missing_returns_default() -> None:
    content = "# No frontmatter here"
    assert parse_content_version(content) == "0.0.0"


def test_parse_content_version_extra_spaces() -> None:
    content = "<!-- content_version:   1.2.3  | locale: pt-BR -->"
    assert parse_content_version(content) == "1.2.3"


# ---------------------------------------------------------------------------
# compute_sha256
# ---------------------------------------------------------------------------


def test_compute_sha256_is_64_hex_chars() -> None:
    digest = compute_sha256("hello world")
    assert len(digest) == 64
    assert re.match(r"^[0-9a-f]{64}$", digest)


def test_compute_sha256_deterministic() -> None:
    assert compute_sha256("test") == compute_sha256("test")


def test_compute_sha256_different_inputs_differ() -> None:
    assert compute_sha256("a") != compute_sha256("b")


# ---------------------------------------------------------------------------
# resource_meta
# ---------------------------------------------------------------------------


def test_resource_meta_returns_semver_version() -> None:
    meta = resource_meta(SCRIBE_SKILL_URI)
    assert re.match(r"^\d+\.\d+\.\d+$", meta.content_version), (
        f"Expected SemVer, got {meta.content_version!r}"
    )


def test_resource_meta_returns_sha256() -> None:
    meta = resource_meta(SCRIBE_SKILL_URI)
    assert len(meta.sha256) == 64
    assert re.match(r"^[0-9a-f]{64}$", meta.sha256)


def test_resource_meta_sha256_matches_content() -> None:
    content = read_scribe_resource(SCRIBE_SKILL_URI)
    meta = resource_meta(SCRIBE_SKILL_URI)
    assert meta.sha256 == compute_sha256(content)


def test_resource_meta_version_matches_file_frontmatter() -> None:
    content = read_scribe_resource(SCRIBE_SKILL_URI)
    meta = resource_meta(SCRIBE_SKILL_URI)
    assert meta.content_version == parse_content_version(content)
