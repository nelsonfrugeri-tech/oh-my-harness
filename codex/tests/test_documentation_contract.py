from __future__ import annotations

import re
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]


class DocumentationContractTest(unittest.TestCase):
    def test_syncthing_preserves_existing_folder_configuration(self) -> None:
        content = _ROOT.joinpath(
            "skills/tools/sync-transport/references/syncthing.md"
        ).read_text(encoding="utf-8")

        self.assertIn("CURRENT_FOLDER=", content)
        self.assertIn("PROPOSED_FOLDER=", content)
        self.assertRegex(content, r"preserves every\s+existing field")
        self.assertIn("exact diff", content)
        self.assertIn("explicit authorization", content)
        self.assertIn("--data-binary \"$PROPOSED_FOLDER\"", content)
        self.assertIn("Only when the folder is absent", content)
        self.assertNotIn("curl -s ", content)

    def test_sync_model_matches_readme_catalog(self) -> None:
        agent = _ROOT.joinpath("agents/tools/sync.md").read_text(encoding="utf-8")
        readme = _ROOT.joinpath("README.md").read_text(encoding="utf-8")
        match = re.search(r"^model:\s*([^\s]+)", agent, re.MULTILINE)

        self.assertIsNotNone(match)
        model = match.group(1) if match else ""
        self.assertRegex(
            readme,
            rf"(?m)^\| `tools`\s+\| `sync`\s+\|.*\| {re.escape(model)}\s+\|$",
        )

    def test_adapted_skills_do_not_claim_unverified_fidelity(self) -> None:
        paths = tuple(_ROOT.glob("skills/engineers/langchain/**/SKILL.md"))
        contents = "\n".join(path.read_text(encoding="utf-8") for path in paths)

        self.assertNotIn("fiel ao upstream", contents)
        self.assertNotIn("faithful to upstream", contents.lower())
        self.assertIn("https://github.com/langchain-ai/langchain-skills", contents)
        for path in paths:
            content = path.read_text(encoding="utf-8")
            if "adaptation_status: local-adaptation" not in content:
                continue
            with self.subTest(path=path):
                self.assertRegex(
                    content,
                    r"(?m)^upstream_version: [0-9a-f]{40}$",
                )


if __name__ == "__main__":
    unittest.main()
