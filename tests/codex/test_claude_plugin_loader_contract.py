from __future__ import annotations

import json
import re
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
        entries = tuple(agents_dir.iterdir())
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

    def test_shipped_skill_and_agent_descriptions_fit_the_loader_limit(self) -> None:
        skills = tuple(
            path
            for root in _PLUGIN["skills"]
            for path in sorted(_ROOT.joinpath(root).glob("*/SKILL.md"))
        )
        agents = tuple(sorted(_ROOT.glob("agents/*.md")))

        self.assertTrue(skills)
        self.assertTrue(agents)
        for path in (*skills, *agents):
            with self.subTest(path=path.relative_to(_ROOT).as_posix()):
                description = _frontmatter_scalar(self, path, "description")
                self.assertTrue(description.strip())
                self.assertLessEqual(len(description), _DESCRIPTION_LIMIT)


def _frontmatter_scalar(test: unittest.TestCase, path: Path, key: str) -> str:
    """Return a top-level frontmatter scalar, measuring block scalars conservatively.

    Block scalars are rebuilt with literal (`|`) semantics and clip chomping. Folding (`>`)
    replaces each single line break with one space and collapses blank lines, so the literal
    length is an upper bound for a folded value and never under-reports it.
    """
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    test.assertIsNotNone(match, f"{path} has no frontmatter")
    lines = match.group(1).splitlines() if match else []
    for index, line in enumerate(lines):
        name, separator, rest = line.partition(":")
        if name != key or not separator:
            continue
        value = rest.strip()
        if value[:1] not in ("|", ">"):
            return value.strip("'\"")
        block = []
        for follower in lines[index + 1 :]:
            if follower.strip() and not follower.startswith((" ", "\t")):
                break
            block.append(follower)
        return textwrap.dedent("\n".join(block)).strip("\n") + "\n"
    test.fail(f"{path} has no frontmatter key {key!r}")
    return ""


if __name__ == "__main__":
    unittest.main()
