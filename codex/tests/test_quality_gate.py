from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_GATE = _ROOT / "claude-code/hooks/quality-gate.sh"


@unittest.skipUnless(shutil.which("jq"), "jq is required by the quality gate")
class QualityGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        temporary = Path(self._temporary.name)
        self._repo = temporary / "repo"
        self._cache = temporary / "cache"
        self._repo.mkdir()
        self._git("init", "-q")
        self._repo.joinpath("tracked.txt").write_text("content\n", encoding="utf-8")
        self._git("add", "tracked.txt")

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_untrusted_repository_defers_without_running_commands(self) -> None:
        self._configure(test="false")

        self.assertEqual("", self._run_gate())

    def test_trusted_repository_runs_every_discovered_check(self) -> None:
        self._configure(format="true", lint="true", typecheck="true", test="true")
        self._trust_repository()

        decision = self._decision(self._run_gate())

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("format lint typecheck test", decision["permissionDecisionReason"])

    def test_trusted_repository_denies_commit_when_a_check_fails(self) -> None:
        self._configure(test="false")
        self._trust_repository()

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("FAILED at test", decision["permissionDecisionReason"])

    def test_explicit_bypass_allows_without_repository_trust(self) -> None:
        self._configure(test="false")

        decision = self._decision(self._run_gate("OMH_GATE=off git commit -m test"))

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("NOT verified", decision["permissionDecisionReason"])

    def _configure(self, **commands: str) -> None:
        config = self._repo / ".claude/quality-gate.json"
        config.parent.mkdir()
        config.write_text(json.dumps(commands), encoding="utf-8")
        self._git("add", str(config.relative_to(self._repo)))

    def _trust_repository(self) -> None:
        common_dir = self._git("rev-parse", "--path-format=absolute", "--git-common-dir")
        signature = hashlib.sha256(common_dir.encode()).hexdigest()[:12]
        marker = self._cache / "omh-quality-gate/trusted" / signature
        marker.parent.mkdir(parents=True)
        marker.touch()

    def _run_gate(self, command: str = "git commit -m test") -> str:
        payload = {"cwd": str(self._repo), "tool_input": {"command": command}}
        completed = subprocess.run(
            ("bash", str(_GATE)),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env={**os.environ, "XDG_CACHE_HOME": str(self._cache)},
        )
        return completed.stdout.strip()

    def _git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=self._repo,
            text=True,
            capture_output=True,
            check=True,
        )
        return completed.stdout.strip()

    def _decision(self, output: str) -> dict[str, str]:
        return json.loads(output)["hookSpecificOutput"]


if __name__ == "__main__":
    unittest.main()
