from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "installers/codex"))

from lib.exec_rules import ManagedExecRules  # noqa: E402
from lib.layout import InstallLayout  # noqa: E402
from lib.shared_policy import RULES_HEADER  # noqa: E402
from lib.sync import InstallConflict  # noqa: E402

_CODEX = shutil.which("codex")


class ManagedExecRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        root = Path(self._temporary.name)
        source = root / "source"
        policy = source / "core/policies/permissions.json"
        policy.parent.mkdir(parents=True)
        shutil.copyfile(_ROOT / "core/policies/permissions.json", policy)
        self._layout = InstallLayout(source, root / "codex-home", root / "agents-home")
        self._rules = ManagedExecRules(self._layout, InstallConflict)
        self._target = self._layout.rules_file

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_install_writes_the_managed_rules_file(self) -> None:
        self.assertTrue(self._rules.install().startswith("atualizado: "))

        content = self._target.read_text(encoding="utf-8")
        self.assertEqual(self._layout.codex_home / "rules/oh-my-harness.rules", self._target)
        self.assertEqual(RULES_HEADER, content.splitlines()[0])
        self.assertIn('pattern = ["rm"]', content)
        self.assertIn('decision = "forbidden"', content)
        self.assertIn("oh-my-harness deny-sudo: ", content)
        self.assertNotIn("find * -delete", content)
        self.assertTrue(self._rules.install().startswith("ok: "))
        self.assertTrue(self._rules.validate().startswith("ok: "))

    def test_install_refuses_an_unmanaged_rules_file(self) -> None:
        self._target.parent.mkdir(parents=True)
        self._target.write_text('prefix_rule(pattern=["ls"], decision="allow")\n', encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._rules.preflight()
        with self.assertRaises(InstallConflict):
            self._rules.install()

        self.assertIn('pattern=["ls"]', self._target.read_text(encoding="utf-8"))
        self.assertFalse(self._target.with_suffix(".rules.omh.bak").exists())

    def test_install_backs_up_a_stale_managed_file_once(self) -> None:
        self._target.parent.mkdir(parents=True)
        stale = RULES_HEADER + "\n\n# stale\n"
        self._target.write_text(stale, encoding="utf-8")

        self._rules.install()

        backup = self._target.with_suffix(".rules.omh.bak")
        self.assertEqual(stale, backup.read_text(encoding="utf-8"))

    def test_validate_detects_missing_and_stale_rules(self) -> None:
        with self.assertRaises(InstallConflict):
            self._rules.validate()
        self._rules.install()
        content = self._target.read_text(encoding="utf-8")
        self._target.write_text(content.replace('"forbidden"', '"prompt"'), encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._rules.validate()

    def test_validate_follows_policy_changes(self) -> None:
        self._rules.install()
        policy = json.loads(self._layout.policy_file.read_text(encoding="utf-8"))
        policy["rules"] = [rule for rule in policy["rules"] if rule["id"] != "deny-sudo"]
        self._layout.policy_file.write_text(json.dumps(policy), encoding="utf-8")

        with self.assertRaises(InstallConflict):
            self._rules.validate()


@unittest.skipIf(_CODEX is None, "codex CLI is not installed")
class CodexExecPolicyTest(unittest.TestCase):
    """Validate the rendered rules with the installed Codex execpolicy engine."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory()
        root = Path(cls._temporary.name)
        layout = InstallLayout(_ROOT, root / "codex-home", root / "agents-home")
        ManagedExecRules(layout, InstallConflict).install()
        cls._rules_file = layout.rules_file

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def _decision(self, *command: str) -> str:
        result = subprocess.run(
            [str(_CODEX), "execpolicy", "check", "--rules", str(self._rules_file), "--", *command],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout).get("decision", "allow")

    def test_rules_file_parses_and_examples_validate(self) -> None:
        self.assertEqual("allow", self._decision("true"))

    def test_case_2_routine_commands_are_not_matched(self) -> None:
        for command in (("ls",), ("git", "status"), ("npm", "test")):
            with self.subTest(command=command):
                self.assertEqual("allow", self._decision(*command))

    def test_case_3_rm_of_a_test_file_prompts(self) -> None:
        self.assertEqual("prompt", self._decision("rm", "tests/tmp_fixture.txt"))

    def test_case_6_delete_without_rm_prompts(self) -> None:
        self.assertEqual("prompt", self._decision("unlink", "a.txt"))
        self.assertEqual("prompt", self._decision("git", "clean", "-fd"))

    def test_push_to_default_branch_prompts_and_irreversible_actions_are_forbidden(self) -> None:
        self.assertEqual("prompt", self._decision("git", "push", "origin", "main"))
        self.assertEqual("forbidden", self._decision("git", "push", "--force", "origin", "x"))
        self.assertEqual("forbidden", self._decision("rm", "-rf", "/"))
        self.assertEqual("forbidden", self._decision("sudo", "ls"))


if __name__ == "__main__":
    unittest.main()
