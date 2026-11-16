from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "installers"))

from policy.permissions import glob_matches, load_policy  # noqa: E402
from policy.render import (  # noqa: E402
    check_claude_settings,
    main,
    render_claude,
    render_claude_text,
)

_SETTINGS = _ROOT / "harness/claude/settings.json"
_BASH = re.compile(r"^Bash\((.+)\)$")


def _first_match(entries: list, command: str) -> bool:
    """Approximate Claude Code Bash matching: '*' is any text; 'p *' also matches bare 'p'."""
    for entry in entries:
        match = _BASH.match(entry)
        if not match:
            continue
        pattern = match.group(1)
        if glob_matches(pattern, command):
            return True
        if pattern.endswith(" *") and pattern.count("*") == 1 and command == pattern[:-2]:
            return True
    return False


class ClaudePermissionsRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._policy = load_policy()
        self._permissions = render_claude(self._policy)["permissions"]

    def test_checked_in_settings_match_the_render(self) -> None:
        self.assertEqual(render_claude_text(self._policy), _SETTINGS.read_text(encoding="utf-8"))

    def test_bypass_is_the_default_and_there_is_no_allow_block(self) -> None:
        self.assertEqual("bypassPermissions", self._permissions["defaultMode"])
        self.assertNotIn("allow", self._permissions)

    def test_read_rules_use_an_absolute_or_home_anchor(self) -> None:
        reads = [
            entry
            for effect in ("ask", "deny")
            for entry in self._permissions[effect]
            if entry.startswith("Read(")
        ]
        self.assertTrue(reads)
        for entry in reads:
            with self.subTest(entry=entry):
                self.assertRegex(entry, r"^Read\((?://|~/)")
                self.assertNotRegex(entry, r"^Read\(/[^/]")
        self.assertIn("Read(//**/.env)", self._permissions["ask"])
        self.assertIn("Read(~/.aws/credentials)", self._permissions["ask"])
        self.assertIn("Read(~/.ssh/**)", self._permissions["ask"])

    def test_root_wipe_is_denied_even_though_rm_asks(self) -> None:
        self.assertIn("Bash(rm *)", self._permissions["ask"])
        self.assertTrue(_first_match(self._permissions["deny"], "rm -rf /"))
        self.assertTrue(_first_match(self._permissions["ask"], "rm -rf /"))

    def test_routine_commands_match_no_rule(self) -> None:
        for command in ("ls", "git status", "npm test", "rm-helper", "git push origin feature"):
            with self.subTest(command=command):
                for effect in ("ask", "deny"):
                    self.assertFalse(_first_match(self._permissions[effect], command))

    def test_literal_star_tokens_are_not_rendered_as_wildcards(self) -> None:
        deny = self._permissions["deny"]
        self.assertNotIn("Bash(rm -rf /*)", deny)
        self.assertFalse(_first_match(deny, "rm -rf /tmp/build"))
        self.assertTrue(_first_match(self._permissions["ask"], "rm -rf /tmp/build"))

    def test_push_to_default_branch_asks_and_force_push_is_denied(self) -> None:
        self.assertTrue(_first_match(self._permissions["ask"], "git push origin main"))
        self.assertFalse(_first_match(self._permissions["deny"], "git push origin main"))
        self.assertTrue(_first_match(self._permissions["deny"], "git push --force origin x"))

    def test_check_claude_accepts_a_merged_user_settings_file(self) -> None:
        user = {
            "model": "opus",
            "permissions": {
                "defaultMode": "bypassPermissions",
                "ask": list(self._permissions["ask"]),
                "deny": ["Bash(curl * | sh)", *self._permissions["deny"]],
            },
        }
        self.assertEqual((), check_claude_settings(self._policy, user))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps(user), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["--check-claude", str(path)]))

    def test_check_claude_reports_missing_entries_and_mode(self) -> None:
        user = {"permissions": {"defaultMode": "default", "ask": [], "deny": ["Bash(sudo *)"]}}
        problems = check_claude_settings(self._policy, user)
        self.assertTrue(any("defaultMode" in problem for problem in problems))
        self.assertTrue(any("Read(//**/.env)" in problem for problem in problems))
        self.assertFalse(any(problem.endswith("Bash(sudo *)") for problem in problems))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps(user), encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(1, main(["--check-claude", str(path)]))

    def test_cli_check_passes_for_the_checked_in_files(self) -> None:
        with redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(0, main(["--check"]))
        self.assertEqual("", errors.getvalue())

    def test_cli_check_detects_drift_in_a_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "harness/claude").mkdir(parents=True)
            (root / "harness/claude/settings.json").write_text("{}\n", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(1, main(["--check", "--root", str(root)]))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["--write", "--root", str(root)]))
            with redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(["--check", "--root", str(root)]))


if __name__ == "__main__":
    unittest.main()
