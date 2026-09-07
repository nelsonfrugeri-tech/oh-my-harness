from pathlib import Path
import subprocess
import tempfile
import unittest


_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBaseTaxonomyContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")

    def test_write_routes_project_knowledge_through_a_topic(self) -> None:
        contract = self._read("skills/kb-write/SKILL.md")

        self.assertIn("scope -> domain -> topic -> concept", contract)
        self.assertIn(
            "work/projects/<project>/<topic>/<YYYY-MM-DD>--<short-slug>.md",
            contract,
        )
        self.assertIn(
            "`type` does not select the directory",
            " ".join(contract.split()),
        )
        self.assertNotIn("Pasta nasce na **segunda** nota", contract)

    def test_project_resolution_asks_only_when_identity_is_unknown(self) -> None:
        contract = " ".join(self._read("skills/kb-write/SKILL.md").split())

        self.assertIn("explicit project name", contract)
        self.assertIn("`remote_url`", contract)
        self.assertIn("observed Git root", contract)
        self.assertIn("never search for another slug", contract)
        self.assertIn("stable Git identity is unavailable", contract)
        self.assertIn("ask once for the canonical name and slug", contract)
        self.assertIn("collision blocks writing", contract)
        self.assertIn("existing artifact without sufficient identity", contract)
        self.assertIn("fails closed", contract)
        self.assertIn("`explorer`, `kb-session`, and `context-load.sh`", contract)

    def test_topic_path_and_short_filename_are_stable(self) -> None:
        contract = self._read("skills/kb-write/SKILL.md")
        normalized = " ".join(contract.split())

        self.assertIn("2-6 substantive terms", contract)
        self.assertIn(
            "never move or rename a note during a normal write",
            normalized,
        )
        self.assertIn("Concept ID", contract)
        self.assertNotIn("<slug-do-titulo>", contract)

    def test_topic_is_indexed_and_available_to_retrieval(self) -> None:
        write = self._read("skills/kb-write/SKILL.md")
        infra = self._read("skills/kb-infra/SKILL.md")
        retrieval = self._read("skills/kb-retrieval/SKILL.md")

        self.assertIn("topic: <stable-subject>", write)
        self.assertIn("`topic`", infra)
        self.assertIn("`topic`", infra)
        self.assertIn("`topic`", retrieval)
        self.assertIn("topic folder", retrieval)

    def test_agents_enforce_the_same_topic_first_routing(self) -> None:
        paths = (
            "agents/tools/knowledge-base.md",
            "codex/agents/knowledge-base.toml",
        )

        for path in paths:
            with self.subTest(path=path):
                content = self._read(path)
                normalized = " ".join(content.split()).lower()
                self.assertIn("canonical project/context to topic to concept", normalized)
                self.assertIn("block domain collisions", normalized)
                self.assertIn("instead of inventing alternate slugs", normalized)
                self.assertIn("writing, retrieval, and session work", normalized)
                self.assertIn("owning skills", normalized)

    def test_readme_documents_topic_first_layout(self) -> None:
        readme = self._read("README.md")

        self.assertIn("<topic>/", readme)
        self.assertIn("<date>--<short-slug>.md", readme)
        self.assertIn("topic-first", readme)
        self.assertNotIn("one folder per entity type", readme)

    def test_disk_timeline_is_recursive_and_excludes_reserved_files(self) -> None:
        retrieval = self._read("skills/kb-retrieval/SKILL.md")
        command = next(
            line.strip().strip("`.")
            for line in retrieval.splitlines()
            if line.strip().startswith("`find ~/knowledge-base/<domain>")
        )

        with tempfile.TemporaryDirectory() as temporary:
            domain = Path(temporary)
            old_note = domain / "z-topic/2025-01-01--old-note.md"
            new_note = domain / "a-topic/subtopic/2026-09-01--new-note.md"
            reserved = domain / "zz-topic/index.md"
            for path in (old_note, new_note, reserved):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            result = subprocess.run(
                command.replace("~/knowledge-base/<domain>", str(domain)),
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual([str(new_note), str(old_note)], result.stdout.splitlines())

    def test_disk_type_filter_parses_only_yaml_frontmatter(self) -> None:
        retrieval = self._read("skills/kb-retrieval/SKILL.md")
        normalized = " ".join(retrieval.split())

        self.assertIn("yaml.safe_load", retrieval)
        self.assertIn("only the first YAML frontmatter block", normalized)
        self.assertIn('lines.index("---", 1)', retrieval)
        self.assertIn("~/knowledge-base/<domain> type system", retrieval)
        self.assertNotIn('text.split("---", 2)', retrieval)
        self.assertNotIn('grep -rl "^type:', retrieval)
