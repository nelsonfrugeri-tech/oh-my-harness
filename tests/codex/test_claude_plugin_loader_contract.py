from __future__ import annotations

import json
import re
import tempfile
import textwrap
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_PLUGIN = json.loads(
    _ROOT.joinpath(".claude-plugin/plugin.json").read_text(encoding="utf-8")
)
_MANIFEST = json.loads(
    _ROOT.joinpath("core/agents/routing.json").read_text(encoding="utf-8")
)
# The claude.ai / Cowork plugin loader rejects a skill whose frontmatter description exceeds
# this many characters, and the Git marketplace sync drops that skill without an error. The
# Claude Code CLI validator does not enforce the limit, so only this contract catches it.
_DESCRIPTION_LIMIT = 1024
# The harness adapter agent is Claude-specific and therefore not a portable role in
# routing.json, exactly as `codex.toml` is excluded from the Codex adapter comparison.
_HARNESS_ADAPTER_AGENT = "claude-code"


class ClaudePluginLoaderContractTest(unittest.TestCase):
    """Keep the Claude plugin loadable by both the CLI and the claude.ai loader.

    The claude.ai loader ignores an explicit `agents` list and discovers agents only in the
    default root `agents/` directory, while the CLI validator rejects directory entries in
    that list. A flat root `agents/` with no `agents` key is the only layout both accept.
    """

    def test_manifest_relies_on_default_agent_discovery(self) -> None:
        self.assertNotIn("agents", _PLUGIN)

    def test_root_agents_are_flat_markdown_files(self) -> None:
        agents_dir = _ROOT / "agents"

        self.assertTrue(agents_dir.is_dir())
        # Dotfiles such as an ignored `.DS_Store` are neither shipped nor agents.
        entries = tuple(
            entry for entry in agents_dir.iterdir() if not entry.name.startswith(".")
        )
        self.assertTrue(entries)
        for entry in entries:
            with self.subTest(entry=entry.name):
                self.assertTrue(entry.is_file(), "the default loader does not recurse")
                self.assertEqual(".md", entry.suffix)

    def test_root_agents_are_exactly_the_declared_claude_roles(self) -> None:
        on_disk = {path.stem for path in _ROOT.glob("agents/*.md")}
        expected = set(_MANIFEST["roles"]) | {_HARNESS_ADAPTER_AGENT}

        self.assertEqual(expected, on_disk)
        self.assertTrue(
            _ROOT.joinpath(
                "harness/claude/skills", _HARNESS_ADAPTER_AGENT, "SKILL.md"
            ).is_file()
        )

    def test_agent_names_match_their_file_names(self) -> None:
        # The scoped name is `<plugin>:<frontmatter name>`; keeping the file stem equal to it
        # makes the flat layout unambiguous and the published names stable.
        for path in _ROOT.glob("agents/*.md"):
            with self.subTest(agent=path.name):
                self.assertEqual(path.stem, _frontmatter_scalar(self, path, "name"))

    def test_shared_markdown_template_resolves_to_the_root_agents(self) -> None:
        template = _MANIFEST["adapter_specs"]["shared-markdown"]["path_template"]
        families = _MANIFEST["role_families"]

        for role_id in _MANIFEST["roles"]:
            with self.subTest(role=role_id):
                path = _ROOT / template.format(role=role_id, family=families[role_id])
                self.assertEqual(_ROOT / "agents" / f"{role_id}.md", path)
                self.assertTrue(path.is_file())

    def test_shipped_skill_descriptions_fit_the_loader_limit(self) -> None:
        skills = tuple(
            path
            for root in _PLUGIN["skills"]
            for path in sorted(_ROOT.joinpath(root).glob("*/SKILL.md"))
        )

        self.assertTrue(skills)
        for path in skills:
            with self.subTest(path=path.relative_to(_ROOT).as_posix()):
                _assert_description_within_limit(self, path)

    def test_shipped_agent_descriptions_fit_the_loader_limit(self) -> None:
        agents = tuple(sorted(_ROOT.glob("agents/*.md")))

        self.assertTrue(agents)
        for path in agents:
            with self.subTest(path=path.relative_to(_ROOT).as_posix()):
                _assert_description_within_limit(self, path)


class DescriptionMeasurementTest(unittest.TestCase):
    """Prove the limit check cannot under-measure any YAML scalar form it accepts."""

    # 24 lines of 60 characters fold, with one space per line break, into 1463 characters.
    _LINES = tuple("x" * 60 for _ in range(24))
    _FOLDED_LENGTH = 24 * 60 + 23

    def test_plain_multi_line_description_over_the_limit_fails(self) -> None:
        continuation = "\n".join(f"  {line}" for line in self._LINES[1:])
        frontmatter = f"description: {self._LINES[0]}\n{continuation}\nname: probe"

        self.assertGreater(self._FOLDED_LENGTH, _DESCRIPTION_LIMIT)
        self.assertGreaterEqual(self._measure(frontmatter), self._FOLDED_LENGTH)
        with self.assertRaises(AssertionError):
            self._check(frontmatter)

    def test_double_quoted_multi_line_description_over_the_limit_fails(self) -> None:
        continuation = "\n".join(f"  {line}" for line in self._LINES[1:])
        frontmatter = f'description: "{self._LINES[0]}\n{continuation}"\nname: probe'

        self.assertGreaterEqual(self._measure(frontmatter), self._FOLDED_LENGTH)
        with self.assertRaises(AssertionError):
            self._check(frontmatter)

    def test_block_description_over_the_limit_fails(self) -> None:
        body = "\n".join(f"  {line}" for line in self._LINES)
        for indicator in ("|", ">"):
            with self.subTest(indicator=indicator):
                frontmatter = f"description: {indicator}\n{body}\nname: probe"

                self.assertGreaterEqual(self._measure(frontmatter), self._FOLDED_LENGTH)
                with self.assertRaises(AssertionError):
                    self._check(frontmatter)

    def test_single_line_description_is_measured_exactly(self) -> None:
        for frontmatter in (
            'description: "short and quoted"\nname: probe',
            "description: short and quoted\nname: probe",
        ):
            with self.subTest(frontmatter=frontmatter):
                self.assertEqual(len("short and quoted"), self._measure(frontmatter))
                self._check(frontmatter)

    def _measure(self, frontmatter: str) -> int:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write(Path(temporary), frontmatter)
            return len(_frontmatter_scalar(self, path, "description"))

    def _check(self, frontmatter: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _assert_description_within_limit(self, self._write(Path(temporary), frontmatter))

    def _write(self, directory: Path, frontmatter: str) -> Path:
        path = directory / "SKILL.md"
        path.write_text(f"---\n{frontmatter}\n---\n\nBody.\n", encoding="utf-8")
        return path


def _assert_description_within_limit(test: unittest.TestCase, path: Path) -> None:
    description = _frontmatter_scalar(test, path, "description")
    test.assertTrue(description.strip(), f"{path} has an empty description")
    test.assertLessEqual(len(description), _DESCRIPTION_LIMIT, str(path))


def _frontmatter_scalar(test: unittest.TestCase, path: Path, key: str) -> str:
    """Return a top-level frontmatter scalar, never shorter than its YAML value.

    Block scalars are rebuilt with literal (`|`) semantics and clip chomping. Folding (`>`)
    replaces each single line break with one space and collapses blank lines, so the literal
    length is an upper bound for a folded value.

    Plain and quoted values may continue on indented lines. They are folded by joining every
    trimmed line with one space, which equals YAML folding except that a blank line counts one
    character more, and quoted escapes such as `\\"` or `''` count as written. Every deviation
    over-measures, so the limit check can reject a valid description but never accept a long one.
    """
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    test.assertIsNotNone(match, f"{path} has no frontmatter")
    lines = match.group(1).splitlines() if match else []
    for index, line in enumerate(lines):
        name, separator, rest = line.partition(":")
        if name != key or not separator:
            continue
        continuation = []
        for follower in lines[index + 1 :]:
            if follower.strip() and not follower.startswith((" ", "\t")):
                break
            continuation.append(follower)
        value = rest.strip()
        if value[:1] in ("|", ">"):
            return textwrap.dedent("\n".join(continuation)).strip("\n") + "\n"
        folded = " ".join(part.strip() for part in (value, *continuation)).strip()
        return folded[1:-1] if folded[:1] in ("'", '"') else folded
    test.fail(f"{path} has no frontmatter key {key!r}")
    return ""


if __name__ == "__main__":
    unittest.main()
