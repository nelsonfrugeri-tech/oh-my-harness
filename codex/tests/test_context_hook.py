from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_HOOK = _ROOT / "hooks/context-load.sh"
_CLAUDE_HOOK = _ROOT / "claude-code/hooks/context-load.sh"


class ContextHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        root = Path(self._temporary.name)
        self._repository = root / "Example Project"
        self._knowledge_base = root / "knowledge-base"
        self._repository.mkdir()
        self._git("init")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test User")
        self._repository.joinpath("README.md").write_text("initial\n", encoding="utf-8")
        self._commit("initial")

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_missing_report_requests_full_analysis(self) -> None:
        output = self._run_hook()

        self.assertIn("modo **FULL**", output)
        self.assertIn("example-project", output)

    def test_claude_adapter_resolves_shared_loader_through_symlink(self) -> None:
        installed = Path(self._temporary.name) / "claude/hooks/context-load.sh"
        installed.parent.mkdir(parents=True)
        installed.symlink_to(_CLAUDE_HOOK)

        output = self._run_hook(installed)

        self.assertIn("modo **FULL**", output)

    def test_current_report_injects_snapshot_without_refresh_request(self) -> None:
        self._write_report(self._head())

        output = self._run_hook()

        self.assertIn("## Current snapshot", output)
        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("AÇÃO:", output)

    def test_stale_report_injects_snapshot_and_requests_delta_analysis(self) -> None:
        previous = self._head()
        self._write_report(previous)
        self._repository.joinpath("change.txt").write_text("changed\n", encoding="utf-8")
        self._commit("change")

        output = self._run_hook()

        self.assertIn("DRIFT: 1 commits", output)
        self.assertIn("modo **DELTA**", output)
        self.assertIn("Architecture: portable core", output)

    def _run_hook(self, executable: Path = _HOOK) -> str:
        environment = {**os.environ, "OMH_KB_ROOT": str(self._knowledge_base)}
        result = subprocess.run(
            [str(executable)],
            cwd=self._repository,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def _write_report(self, last_hash: str) -> None:
        report = self._knowledge_base / "work/projects/example-project/context.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\n"
            f"last_hash: {last_hash}\n"
            "generated_at: 2026-08-09T00:00:00Z\n"
            "---\n\n"
            "## Current snapshot\n\n"
            "Architecture: portable core\n",
            encoding="utf-8",
        )

    def _head(self) -> str:
        return self._git("rev-parse", "HEAD").stdout.strip()

    def _commit(self, message: str) -> None:
        self._git("add", ".")
        self._git("commit", "-m", message)

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self._repository,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
