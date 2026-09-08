from pathlib import Path
import unittest


_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeBaseSessionDistillationContractTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        return _ROOT.joinpath(relative_path).read_text(encoding="utf-8")

    def test_session_domain_uses_git_root_instead_of_current_directory(self) -> None:
        session = " ".join(self._read("core/skills/kb-session/SKILL.md").split())

        self.assertIn("git -C <cwd> rev-parse --show-toplevel", session)
        self.assertIn("Git root basename", session)
        self.assertIn("never the `cwd` basename", session)
        self.assertIn("including sessions started in a subdirectory", session)
        self.assertIn("reuse the registered canonical project slug", session)
        self.assertIn("never divert a session record", session)

    def test_long_session_distillation_has_complete_auditable_coverage(self) -> None:
        session = self._read("core/skills/kb-session/SKILL.md")
        normalized = " ".join(session.split())
        write = self._read("core/skills/kb-write/SKILL.md")
        agents = (
            self._read("harness/claude/agents/tools/knowledge-base.md"),
            self._read("harness/codex/agents/knowledge-base.toml"),
        )

        self.assertIn("Complete session distillation", session)
        self.assertIn("coverage ledger", session)
        self.assertIn("chronological intervals", session)
        self.assertIn("no unprocessed interval", normalized)
        self.assertIn("parsing failure, unclassified record", session)
        self.assertIn("total raw records", session)
        self.assertIn("Detect credentials, tokens, secrets, and personal data", session)
        self.assertIn("obtain human confirmation before writing", normalized)
        self.assertIn("`kb-write` collision gate", session)
        self.assertIn("note plan", write)
        self.assertIn("create | supersede | skip", write)
        self.assertIn("Re-running the same corpus", write)
        self.assertIn("distillation_key", write)
        self.assertIn("omh-kb-distillation-v1", write)
        self.assertIn("canonical UTF-8 JSON", write)
        self.assertIn("Search disk exactly", write)
        self.assertIn("target exists", write)
        self.assertIn("ancestor indexes", write)
        self.assertIn("mutable or derived structures may be reconciled", write)
        self.assertIn("reconcile and then `skip`", write)
        self.assertIn("one knowledge item per note", write)
        self.assertIn("`distillation_key`", self._read("core/skills/kb-infra/SKILL.md"))
        for agent in agents:
            with self.subTest(agent=agent[:80]):
                normalized_agent = " ".join(agent.split()).lower()
                self.assertIn("`kb-session`", normalized_agent)
                self.assertIn("`kb-write`", normalized_agent)
                self.assertIn("session work to their owning skills", normalized_agent)
                self.assertIn("immutable notes", normalized_agent)
                self.assertIn("living session records", normalized_agent)

    def test_readme_blocks_canonical_domain_collisions(self) -> None:
        readme = " ".join(self._read("README.md").split())

        self.assertIn("collision at the canonical domain blocks writes", readme)
        self.assertIn(
            "persistent resolver shared by note and session writers",
            readme,
        )
        self.assertIn("a local alias is never created", readme)


if __name__ == "__main__":
    unittest.main()
