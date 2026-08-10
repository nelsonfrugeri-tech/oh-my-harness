from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.layout import InstallLayout
from lib.managed_config import ManagedConfig
from lib.sync import InstallConflict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCTRINE = _REPO_ROOT / "doctrine" / "epistemics.md"
_CLAUDE_MD = _REPO_ROOT / "claude-code" / "CLAUDE.md"
_CODEX_AGENTS = _REPO_ROOT / "codex" / "AGENTS.md"


class DoctrineParityTest(unittest.TestCase):
    """The epistemic doctrine is single-sourced and must reach both harnesses unchanged.

    Claude Code loads it through a native `@` import; Codex inlines it at install time.
    These tests are the contract that keeps the two representations from drifting.
    """

    def test_doctrine_source_exists_and_carries_the_rules(self) -> None:
        text = _DOCTRINE.read_text(encoding="utf-8")
        self.assertIn("Todo dado afirmado foi observado", text)
        self.assertIn("hipótese", text)
        self.assertIn("Crítica é colaboração", text)
        self.assertIn("medido", text)

    def test_codex_source_carries_the_token_exactly_once(self) -> None:
        source = _CODEX_AGENTS.read_text(encoding="utf-8")
        self.assertEqual(1, source.count("{omh_doctrine}"))
        self.assertNotIn("Todo dado afirmado foi observado", source)

    def test_claude_source_imports_the_same_file_and_does_not_duplicate_it(self) -> None:
        source = _CLAUDE_MD.read_text(encoding="utf-8")
        self.assertIn("@doctrine/epistemics.md", source)
        self.assertNotIn("Todo dado afirmado foi observado", source)

    def test_rendered_agents_inlines_the_doctrine_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            layout = InstallLayout(_REPO_ROOT, Path(home) / "codex", Path(home) / "agents")
            ManagedConfig(layout, InstallConflict, replace_global_agents=False).install()
            rendered = layout.global_agents_file.read_text(encoding="utf-8")
        doctrine = _DOCTRINE.read_text(encoding="utf-8").strip()
        self.assertIn(doctrine, rendered)
        self.assertNotIn("{omh_doctrine}", rendered)

    def test_missing_doctrine_source_fails_preflight_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "source"
            adapter = source / "codex"
            adapter.mkdir(parents=True)
            adapter.joinpath("AGENTS.md").write_text("Rules.\n\n{omh_doctrine}\n", encoding="utf-8")
            adapter.joinpath("hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
            layout = InstallLayout(source, Path(root) / "codex-home", Path(root) / "agents-home")
            config = ManagedConfig(layout, InstallConflict, replace_global_agents=False)
            with self.assertRaises(InstallConflict):
                config.preflight()
            self.assertFalse(layout.global_agents_file.exists())


if __name__ == "__main__":
    unittest.main()
