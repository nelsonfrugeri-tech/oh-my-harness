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

    def test_dirty_working_tree_denies_instead_of_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("tracked.txt").write_text("uncommitted change\n", encoding="utf-8")

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("uncommitted changes", decision["permissionDecisionReason"])

    def test_unpushed_head_denies_instead_of_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._trust_repository()
        # No remote configured: the branch has no upstream at all.

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("has not been pushed", decision["permissionDecisionReason"])

    def test_explicit_bypass_allows_without_repository_trust(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()

        decision = self._decision(self._run_gate("OMH_GATE=off gh pr create --fill"))

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("NOT verified", decision["permissionDecisionReason"])

    #: Commands that must never reach the gate. `gh pr list/view/merge/checkout` are
    #: read-only; gating them would run the whole project suite under a 600 s timeout
    #: and refuse to *read* a pull request when a test fails. The remaining rows pin
    #: the word boundary the trigger depends on.
    _NON_PR_CREATE_COMMANDS = (
        "gh issue create --title x",
        "gh pr list",
        "gh pr view 135",
        "gh pr merge 135",
        "gh pr checkout 135",
        "gh pr create-foo",
        "gh pr",
        "gh pr create-something",
        "git push && gh pr view 135",
        "gh prcreate",
    )

    def test_non_pr_create_commands_defer_without_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        for command in self._NON_PR_CREATE_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("", self._run_gate(command))

    def test_heredoc_mentioning_gh_pr_create_does_not_trigger_the_gate(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        command = 'cat <<\'EOF\' > README.md\nExample:\ngh pr create --fill\nEOF'

        self.assertEqual("", self._run_gate(command))

    # ---- trigger width, review findings on #135 --------------------------------

    #: Every form the reviewer showed escaping the first-line-anchored regex. `deny`
    #: proves the gate ran: the configured `test` command is `false`.
    _CHAINED_PR_CREATE_COMMANDS = (
        "gh pr create --fill",
        "git push -u origin main && gh pr create --fill",
        "git push; gh pr create --fill",
        "(gh pr create --fill)",
        "/opt/homebrew/bin/gh pr create --fill",
        "cd . && gh pr create --fill",
        "command gh pr create",
        "env gh pr create",
        "FOO=1 gh pr create --fill",
        "gh pr create --fill || true",
        "echo x | gh pr create --fill",
    )

    def test_chained_and_prefixed_pr_creation_still_runs_the_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        for command in self._CHAINED_PR_CREATE_COMMANDS:
            with self.subTest(command=command):
                decision = self._decision(self._run_gate(command))

                self.assertEqual("deny", decision["permissionDecision"])
                self.assertIn("FAILED at test", decision["permissionDecisionReason"])

    def test_quoted_bypass_mention_does_not_grant_the_bypass(self) -> None:
        # OMH_GATE=off counts only as a real assignment prefix of the command being
        # run; inside a PR title it is a quoted argument.
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(
            self._run_gate("gh pr create --title 'mentions OMH_GATE=off' --fill")
        )

        self.assertEqual("deny", decision["permissionDecision"])

    def test_bypass_prefix_is_honoured_after_a_chained_command(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(
            self._run_gate("git push && OMH_GATE=off gh pr create --fill")
        )

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("NOT verified", decision["permissionDecisionReason"])

    # ---- MCP PR-creation path --------------------------------------------------

    def test_mcp_pr_creation_tool_runs_the_same_checks_as_gh_pr_create(self) -> None:
        self._configure_and_commit(format="true", lint="true", typecheck="true", test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate_mcp())

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("format lint typecheck test", decision["permissionDecisionReason"])

    def test_mcp_pr_creation_tool_denies_on_dirty_working_tree(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("tracked.txt").write_text("uncommitted change\n", encoding="utf-8")

        decision = self._decision(self._run_gate_mcp())

        self.assertEqual("deny", decision["permissionDecision"])
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

    # ---- selected PR origin, review findings on #135 ---------------------------

    def test_head_flag_for_another_branch_denies(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate("gh pr create --head other-branch --fill"))

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("other-branch", decision["permissionDecisionReason"])
        self.assertIn(
            "differs from the branch currently checked out", decision["permissionDecisionReason"]
        )

    def test_head_flag_cross_fork_denies(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate("gh pr create --head someone:other-branch --fill"))

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("another fork", decision["permissionDecisionReason"])

    def test_head_flag_matching_current_branch_runs_normally(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()
        branch = self._git("rev-parse", "--abbrev-ref", "HEAD")

        decision = self._decision(self._run_gate(f"gh pr create --head {branch} --fill"))

        self.assertEqual("allow", decision["permissionDecision"])

    #: `--head` mentioned inside another flag's value is not the head flag. A regex
    #: over the raw command line extracted `support'` from the first row — dangling
    #: quote included — and refused to open a PR whose title mentions the flag.
    _HEAD_MENTIONING_COMMANDS = (
        "gh pr create --title 'add --head support' --fill",
        "gh pr create --body 'use -H to pick the head' --fill",
        "gh pr create --body-file '--head notes.md' --fill",
        "gh pr create -t 'about --head' -b 'and -H too' --fill",
        'gh pr create --title "quoted --head other" --fill',
    )

    def test_head_mentioned_inside_a_quoted_argument_is_not_the_head_flag(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        for command in self._HEAD_MENTIONING_COMMANDS:
            with self.subTest(command=command):
                decision = self._decision(self._run_gate(command))

                # The reason may be the pass cache from a previous subtest; the
                # decision is what this case is about.
                self.assertEqual("allow", decision["permissionDecision"])

    def test_head_flag_forms_are_all_recognised(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        for command in (
            "gh pr create --head other-branch --fill",
            "gh pr create --head=other-branch --fill",
            "gh pr create -H other-branch --fill",
            "gh pr create --title 'mentions --head' --head other-branch --fill",
        ):
            with self.subTest(command=command):
                decision = self._decision(self._run_gate(command))

                self.assertEqual("deny", decision["permissionDecision"])
                self.assertIn("other-branch", decision["permissionDecisionReason"])

    def test_mcp_head_for_another_branch_denies(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        decision = self._decision(self._run_gate_mcp(head="other-branch"))

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("other-branch", decision["permissionDecisionReason"])

    def test_mcp_owner_repo_mismatch_denies(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()
        # Only a URL in a form `normalize_owner_repo` can parse exercises the mismatch
        # branch; the bare-repo path used elsewhere in this suite deliberately can't.
        self._git("remote", "set-url", "origin", "https://github.com/nelsonfrugeri-tech/oh-my-harness.git")

        decision = self._decision(self._run_gate_mcp(owner="someone-else", repo="unrelated"))

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("someone-else/unrelated", decision["permissionDecisionReason"])

    def test_remote_diverged_after_force_push_denies(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()
        self._diverge_remote_without_fetching()

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("moved since the last local fetch", decision["permissionDecisionReason"])

    def test_remote_unreachable_denies_without_running_checks(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._git(
            "remote", "set-url", "origin", str(Path(self._temporary.name) / "does-not-exist.git")
        )

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("could not be verified", decision["permissionDecisionReason"])

    def test_local_commit_ahead_of_the_remote_denies(self) -> None:
        # The common unpushed case, distinct from "no upstream at all": the branch is
        # tracked and pushed, but HEAD carries a commit the remote does not have.
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("tracked.txt").write_text("ahead of the remote\n", encoding="utf-8")
        self._git("commit", "-aq", "-m", "local commit ahead")

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("has not been pushed", decision["permissionDecisionReason"])
        self.assertIn("HEAD differs from origin/", decision["permissionDecisionReason"])

    def test_branch_tracking_another_remote_denies_when_origin_lacks_it(self) -> None:
        # `@{upstream}` is not necessarily the remote the pull request targets: a branch
        # tracking `upstream/feat` while `origin` has no `feat` would open the PR against
        # a remote that does not have the branch.
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._git("checkout", "-q", "-b", "feat")
        elsewhere = Path(self._temporary.name) / "upstream.git"
        subprocess.run(
            ("git", "init", "-q", "--bare", str(elsewhere)), check=True, capture_output=True
        )
        self._git("remote", "add", "upstream", str(elsewhere))
        self._git("push", "-q", "-u", "upstream", "feat")

        decision = self._decision(self._run_gate())

        reason = decision["permissionDecisionReason"]
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("feat tracks upstream", reason)
        self.assertIn("opened against origin", reason)
        self.assertIn("OMH_GATE=off", reason)

    def test_detached_head_denies_with_an_accurate_reason(self) -> None:
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._git("checkout", "-q", "--detach", "HEAD")

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("HEAD is detached", decision["permissionDecisionReason"])
        self.assertNotIn("no upstream", decision["permissionDecisionReason"])

    def test_untracked_files_get_their_own_reason(self) -> None:
        # "uncommitted changes" is not a true description of a stray .DS_Store.
        self._configure_and_commit(test="false")
        self._push_current_head()
        self._trust_repository()
        self._repo.joinpath("graphify-out").mkdir()
        self._repo.joinpath("graphify-out/graph.json").write_text("{}\n", encoding="utf-8")

        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("Untracked files are present", decision["permissionDecisionReason"])
        self.assertIn("graphify-out/", decision["permissionDecisionReason"])
        self.assertNotIn("uncommitted changes", decision["permissionDecisionReason"])

    def test_pass_cache_invalidates_when_the_gate_configuration_changes(self) -> None:
        # The configuration is reachable without a new commit whenever it is ignored
        # rather than tracked, so HEAD alone is not a sufficient cache key.
        self._repo.joinpath(".gitignore").write_text(".claude/\n", encoding="utf-8")
        self._git("add", ".gitignore")
        self._git("commit", "-q", "-m", "ignore the gate configuration")
        config = self._repo / ".claude/quality-gate.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"test": "true"}), encoding="utf-8")
        self._push_current_head()
        self._trust_repository()

        self.assertEqual("allow", self._decision(self._run_gate())["permissionDecision"])

        config.write_text(json.dumps({"test": "false"}), encoding="utf-8")
        decision = self._decision(self._run_gate())

        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn("FAILED at test", decision["permissionDecisionReason"])

    def test_pass_cache_short_circuits_an_unchanged_head_and_configuration(self) -> None:
        self._configure_and_commit(test="true")
        self._push_current_head()
        self._trust_repository()

        self.assertEqual("allow", self._decision(self._run_gate())["permissionDecision"])
        decision = self._decision(self._run_gate())

        self.assertEqual("allow", decision["permissionDecision"])
        self.assertIn("already passed", decision["permissionDecisionReason"])

    def test_no_guard_decision_uses_ask(self) -> None:
        # `ask` is not portable: Codex parses it, marks the hook run as failed and
        # continues the tool call, so an `ask` guard would open the PR there while
        # blocking under Claude Code. The two hook descriptors are byte-identical and
        # a contract test pins that equality, so the semantics must match too.
        self.assertNotIn("decide ask", _GATE.read_text(encoding="utf-8"))

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

    def _diverge_remote_without_fetching(self) -> None:
        # Simulate another actor force-pushing after this checkout's last fetch: clone
        # the bare "origin" through a second, independent path, amend its history, and
        # push -f there. self._repo's own refs/remotes/origin/* stay stale because it
        # never fetches — the exact state a stale local comparison can't see.
        remote = Path(self._temporary.name) / "origin.git"
        clone = Path(self._temporary.name) / "other-clone"
        subprocess.run(("git", "clone", "-q", str(remote), str(clone)), check=True, capture_output=True)
        subprocess.run(
            ("git", "-C", str(clone), "config", "user.email", "other@example.com"), check=True
        )
        subprocess.run(("git", "-C", str(clone), "config", "user.name", "Other Actor"), check=True)
        branch = subprocess.run(
            ("git", "-C", str(clone), "rev-parse", "--abbrev-ref", "HEAD"),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        clone.joinpath("tracked.txt").write_text("diverged upstream\n", encoding="utf-8")
        subprocess.run(("git", "-C", str(clone), "commit", "-aq", "-m", "diverge"), check=True)
        subprocess.run(("git", "-C", str(clone), "push", "-qf", "origin", branch), check=True)

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

    def _run_gate_mcp(
        self,
        head: str | None = None,
        owner: str = "nelsonfrugeri-tech",
        repo: str = "oh-my-harness",
        extra_env: dict[str, str] | None = None,
    ) -> str:
        if head is None:
            head = self._git("rev-parse", "--abbrev-ref", "HEAD")
        payload = {
            "cwd": str(self._repo),
            "tool_name": _MCP_PR_TOOL,
            "tool_input": {
                "title": "test PR",
                "head": head,
                "base": "main",
                "owner": owner,
                "repo": repo,
            },
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
