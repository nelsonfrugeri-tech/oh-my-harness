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

    def test_report_for_another_repository_is_not_loaded(self) -> None:
        self._write_report(self._head(), Path("/different/repository"))

        output = self._run_hook()

        self.assertIn("context collision", output)
        self.assertIn("não carregue nem escreva", output)
        self.assertNotIn("Architecture: portable core", output)

    def test_equivalent_remote_forms_identify_the_same_repository(self) -> None:
        self._git("remote", "add", "origin", "git@github.com:example/project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "https://github.com/example/project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_quoted_yaml_remote_identifies_the_same_repository(self) -> None:
        self._git("remote", "add", "origin", "https://github.com/example/project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            '\"https://github.com/example/project.git\"',
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_remote_host_is_case_insensitive_but_path_is_preserved(self) -> None:
        self._git("remote", "add", "origin", "git@github.com:Example/Project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "https://GitHub.com/Example/Project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_explicit_default_ssh_port_identifies_the_same_repository(self) -> None:
        self._git("remote", "add", "origin", "git@github.com:example/project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "ssh://git@github.com:22/example/project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_explicit_default_https_port_identifies_the_same_repository(self) -> None:
        self._git("remote", "add", "origin", "https://github.com/example/project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "https://github.com:443/example/project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_divergent_remote_blocks_even_when_checkout_path_matches(self) -> None:
        self._git("remote", "add", "origin", "https://github.com:new/project.git")
        self._write_report(
            self._head(),
            self._repository,
            "https://github.com/old/project.git",
        )

        output = self._run_hook()

        self.assertIn("context collision", output)
        self.assertNotIn("Architecture: portable core", output)

    def test_local_remote_url_forms_identify_the_same_repository(self) -> None:
        self._git("remote", "add", "origin", "/tmp/example-project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "file:///tmp/example-project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_localhost_file_url_identifies_the_same_local_repository(self) -> None:
        self._git("remote", "add", "origin", "/tmp/example-project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "file://localhost/tmp/example-project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_nonlocal_file_authority_is_stable_across_checkouts(self) -> None:
        self._git("remote", "add", "origin", "file://server/path/project.git")
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "file://server/path/project.git",
        )

        output = self._run_hook()

        self.assertIn("Architecture: portable core", output)
        self.assertNotIn("context collision", output)

    def test_relative_local_remotes_are_resolved_per_checkout(self) -> None:
        other_repository = Path(self._temporary.name) / "other/Example Project"
        other_repository.mkdir(parents=True)
        self._git("remote", "add", "origin", "../origin.git")
        self._write_report(self._head(), other_repository, "../origin.git")

        output = self._run_hook()

        self.assertIn("context collision", output)
        self.assertNotIn("Architecture: portable core", output)

    def test_collision_diagnostic_does_not_expose_remote_credentials(self) -> None:
        userinfo_secret = "userinfo-secret"
        query_secret = "query-secret"
        self._git(
            "remote",
            "add",
            "origin",
            "https://user:"
            f"{userinfo_secret}@github.com/new/project.git?access_token={query_secret}",
        )
        self._write_report(
            self._head(),
            Path("/obsolete/checkout"),
            "https://github.com/old/project.git",
        )

        output = self._run_hook()

        self.assertIn("context collision", output)
        self.assertIn("github.com/new/project", output)
        self.assertNotIn(userinfo_secret, output)
        self.assertNotIn(query_secret, output)

    def test_stale_report_injects_snapshot_and_requests_delta_analysis(self) -> None:
        previous = self._head()
        self._write_report(previous)
        self._repository.joinpath("change.txt").write_text("changed\n", encoding="utf-8")
        self._commit("change")

        output = self._run_hook()

        self.assertIn("DRIFT: 1 commit", output)
        self.assertIn("modo **DELTA**", output)
        self.assertIn("Architecture: portable core", output)

    def test_stale_report_pluralizes_multiple_commits(self) -> None:
        previous = self._head()
        self._write_report(previous)
        self._repository.joinpath("first.txt").write_text("first\n", encoding="utf-8")
        self._commit("first change")
        self._repository.joinpath("second.txt").write_text("second\n", encoding="utf-8")
        self._commit("second change")

        output = self._run_hook()

        self.assertIn("DRIFT: 2 commits", output)
        self.assertNotIn("commit(s)", output)

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

    def _write_report(
        self,
        last_hash: str,
        repository: Path | None = None,
        remote_url: str = "null",
    ) -> None:
        report = self._knowledge_base / "work/projects/example-project/context.md"
        report.parent.mkdir(parents=True)
        resolved_repository = repository or self._repository
        report.write_text(
            "---\n"
            f"last_hash: {last_hash}\n"
            "generated_at: 2026-08-09T00:00:00Z\n"
            f"remote_url: {remote_url}\n"
            "---\n\n"
            f"> Repository: {resolved_repository}\n\n"
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
