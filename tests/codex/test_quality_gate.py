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
_GATE = _ROOT / "core/hooks/quality-gate.sh"
_MCP_PR_TOOL = "mcp__github__create_pull_request"


@unittest.skipUnless(shutil.which("jq"), "jq is required by the quality gate")
class QualityGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        temporary = Path(self._temporary.name)
        self._repo = temporary / "repo"
        self._cache = temporary / "cache"
        self._repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "gate-test@example.com")
        self._git("config", "user.name", "Gate Test")
        self._repo.joinpath("tracked.txt").write_text("content\n", encoding="utf-8")
        self._git("add", "tracked.txt")
        self._git("commit", "-q", "-m", "initial commit")

    def tearDown(self) -> None:
        self._temporary.cleanup()

    # ---- the eight cases from #126 -------------------------------------------------

    def test_untrusted_repository_defers_without_running_commands(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()

        self.assertEqual("", self._run_gate())

    def test_trusted_repository_with_clean_pushed_head_runs_every_discovered_check(
        self,
    ) -> None:
        self._configure_and_commit(format="true", lint="true", typecheck="true", test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate())

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("format lint typecheck test", decision["permissionDecisionReason"])

    def test_trusted_repository_denies_when_a_discovered_check_fails(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("FAILED at test", decision["permissionDecisionReason"])

    def test_dirty_working_tree_asks_instead_of_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("tracked.txt").write_text("uncommitted change\n", encoding="utf-8")

        decision = self._decision(self._run_gate())

        self.assertEqual("ask", decision["permissionDecision"])
        self.assertIn("uncommitted changes", decision["permissionDecisionReason"])

    def test_unpushed_head_asks_instead_of_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._trust_repository()
        # No remote configured: the branch has no upstream at all.

        decision = self._decision(self._run_gate())

        self.assertEqual("ask", decision["permissionDecision"])
        self.assertIn("has not been pushed", decision["permissionDecisionReason"])

    def test_explicit_bypass_allows_without_repository_trust(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()

        decision = self._decision(self._run_gate("OMH_GATE=off gh pr create --fill"))

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("NOT verified", decision["permissionDecisionReason"])

    def test_non_pr_command_defers_without_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        self.assertEqual("", self._run_gate("gh issue create --title x"))

    def test_heredoc_mentioning_gh_pr_create_does_not_trigger_the_gate(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        command = 'cat <<\'EOF\' > README.md\nExample:\ngh pr create --fill\nEOF'

        self.assertEqual("", self._run_gate(command))

    # ---- MCP PR-creation path --------------------------------------------------

    def test_mcp_pr_creation_tool_runs_the_same_checks_as_gh_pr_create(self) -> None:
        self._configure_and_commit(format="true", lint="true", typecheck="true", test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate_mcp())

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("format lint typecheck test", decision["permissionDecisionReason"])

    def test_mcp_pr_creation_tool_asks_on_dirty_working_tree(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("tracked.txt").write_text("uncommitted change\n", encoding="utf-8")

        decision = self._decision(self._run_gate_mcp())

        self.assertEqual("ask", decision["permissionDecision"])
        self.assertIn("uncommitted changes", decision["permissionDecisionReason"])

    def test_mcp_pr_creation_tool_bypass_requires_the_environment_variable(self) -> None:
        # The MCP call carries no command string, so the `OMH_GATE=off <cmd>` prefix form
        # cannot apply to it; only the hook's own environment can bypass this path.
        self._configure_and_commit(test="false")
        self._push_current_head()

        decision = self._decision(
            self._run_gate_mcp(extra_env={"OMH_GATE": "off"})
        )

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("NOT verified", decision["permissionDecisionReason"])

    # ---- helpers ----------------------------------------------------------------

    def _configure_and_commit(self, **commands: str) -> None:
        config = self._repo / ".claude/quality-gate.json"
        config.parent.mkdir()
        config.write_text(json.dumps(commands), encoding="utf-8")
        self._git("add", str(config.relative_to(self._repo)))
        self._git("commit", "-q", "-m", "configure quality gate")

    def _push_current_head(self) -> None:
        remote = Path(self._temporary.name) / "origin.git"
        subprocess.run(
            ("git", "init", "-q", "--bare", str(remote)), check=True, capture_output=True
        )
        self._git("remote", "add", "origin", str(remote))
        branch = self._git("rev-parse", "--abbrev-ref", "HEAD")
        self._git("push", "-q", "-u", "origin", branch)

    def _trust_repository(self) -> None:
        common_dir = self._git("rev-parse", "--path-format=absolute", "--git-common-dir")
        signature = hashlib.sha256(common_dir.encode()).hexdigest()[:12]
        marker = self._cache / "omh-quality-gate/trusted" / signature
        marker.parent.mkdir(parents=True)
        marker.touch()

    def _run_gate(
        self, command: str = "gh pr create --fill", extra_env: dict[str, str] | None = None
    ) -> str:
        payload = {"cwd": str(self._repo), "tool_name": "Bash", "tool_input": {"command": command}}
        return self._invoke(payload, extra_env)

    def _run_gate_mcp(self, extra_env: dict[str, str] | None = None) -> str:
        payload = {
            "cwd": str(self._repo),
            "tool_name": _MCP_PR_TOOL,
            "tool_input": {"title": "test PR", "head": "feature", "base": "main"},
        }
        return self._invoke(payload, extra_env)

    def _invoke(self, payload: dict[str, object], extra_env: dict[str, str] | None) -> str:
        env = {**os.environ, "XDG_CACHE_HOME": str(self._cache)}
        env.update(extra_env or {})
        completed = subprocess.run(
            ("bash", str(_GATE)),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            env=env,
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
