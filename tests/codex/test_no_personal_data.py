"""Guard against personal data and machine-specific paths in tracked files.

The library is account- and machine-agnostic by design: machine paths live in the
user's global harness configuration, never in the repository. The owner's name and
handle are allowed only in the plugin manifests' author fields; both are derived from
there so this test never hard-codes them and survives a fork.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from collections.abc import Callable, Iterator
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]

_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
)

# Reserved documentation domains (RFC 2606/6761) and public hosts used in examples.
_ALLOWED_EMAIL_DOMAINS = (
    "example.com", "example.org", "example.net", "example.edu",
    "github.com", "anthropic.com", "invalid", "test",
)

# Placeholder user names that appear in generic documentation.
_PLACEHOLDER_USERS = ("you", "user", "username", "runner", "shared")

_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2", ".ttf", ".zip"}

_HOME_PATH = re.compile(
    r"(?:/Users/|/home/)(?!(?:" + "|".join(_PLACEHOLDER_USERS) + r")(?=[/\s`'\"$]|$))"
    r"[A-Za-z0-9._-]+(?=[/\s`'\"$]|$)"
    r"|C:\\{1,2}Users\\{1,2}",
    re.IGNORECASE,
)
# An mDNS hostname ending in ".local"; the "~/.local/..." directory and file names such as
# "settings.local.json" do not match.
_LOCAL_HOSTNAME = re.compile(r"(?<![\w.~-])(?:[A-Za-z0-9-]+\.)*[A-Za-z0-9-]+\.local\b(?!\.\w)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def _tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=_ROOT, capture_output=True, check=True
    ).stdout
    files = []
    for raw in output.split(b"\0"):
        if not raw:
            continue
        path = _ROOT / raw.decode("utf-8", errors="surrogateescape")
        if path.suffix.lower() not in _BINARY_SUFFIXES:
            files.append(path)
    return files


def _lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield (line number, text) for a tracked path; a symlink yields its target as line 0."""
    relative = path.relative_to(_ROOT).as_posix()
    yield 0, relative
    if path.is_symlink():
        yield 0, os.readlink(path)
        return
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    for number, line in enumerate(text.splitlines(), start=1):
        yield number, line


def _scan(flag: Callable[[str, int, str], str | None]) -> list[str]:
    offenders = []
    for path in _tracked_files():
        relative = path.relative_to(_ROOT).as_posix()
        for number, line in _lines(path):
            hit = flag(relative, number, line)
            if hit:
                offenders.append(f"{relative}:{number}: {hit[:100]}")
    return offenders


def _owner_identity() -> tuple[frozenset[str], str]:
    """Return (name tokens, handle) declared in the manifests' author/owner fields."""
    tokens: set[str] = set()
    handle = ""
    for manifest in _MANIFESTS:
        data = json.loads((_ROOT / manifest).read_text(encoding="utf-8"))
        person = data.get("author") or data.get("owner") or {}
        if not isinstance(person, dict):
            continue
        for token in str(person.get("name", "")).split():
            if len(token) >= 4:
                tokens.add(token.lower())
        url = str(person.get("url", "")).rstrip("/")
        if url:
            handle = url.rsplit("/", 1)[-1].lower()
    return frozenset(tokens), handle


def _is_manifest_identity_field(relative: str, line: str) -> bool:
    lowered = line.lower()
    return relative in _MANIFESTS and any(
        key in lowered for key in ('"name"', '"url"', "developername")
    )


class NoPersonalDataTest(unittest.TestCase):
    def test_no_home_paths_or_local_hostnames(self) -> None:
        def flag(_relative: str, _number: int, line: str) -> str | None:
            match = _HOME_PATH.search(line) or _LOCAL_HOSTNAME.search(line)
            return match.group(0) if match else None

        self.assertEqual([], _scan(flag))

    def test_no_personal_email_addresses(self) -> None:
        def flag(_relative: str, _number: int, line: str) -> str | None:
            for match in _EMAIL.finditer(line):
                domain = match.group(1).lower()
                allowed = any(
                    domain == d or domain.endswith("." + d) for d in _ALLOWED_EMAIL_DOMAINS
                )
                if not allowed:
                    return match.group(0)
            return None

        self.assertEqual([], _scan(flag))

    def test_owner_identity_appears_only_in_manifest_author_fields(self) -> None:
        tokens, handle = _owner_identity()
        self.assertTrue(
            tokens, "manifest author/owner name must have at least one token of 4+ characters"
        )
        patterns = [re.compile(rf"\b{re.escape(token)}\b") for token in tokens]

        def flag(relative: str, _number: int, line: str) -> str | None:
            if _is_manifest_identity_field(relative, line):
                return None
            lowered = line.lower()
            if handle:
                lowered = lowered.replace(handle, "")
            for pattern in patterns:
                if pattern.search(lowered):
                    return line.strip()
            return None

        self.assertEqual([], _scan(flag))


if __name__ == "__main__":
    unittest.main()
