from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "installers"))

from policy.permissions import (  # noqa: E402
    CAPABILITIES,
    EFFECTS,
    evaluate,
    load_policy,
    parse_policy,
)

_POLICY_FILE = _ROOT / "core/policies/permissions.json"
_HOME = "/home/user"


def _raw() -> dict:
    return json.loads(_POLICY_FILE.read_text(encoding="utf-8"))


class CanonicalPolicySchemaTest(unittest.TestCase):
    def test_checked_in_policy_is_valid(self) -> None:
        policy = load_policy(_POLICY_FILE)
        self.assertEqual(1, policy.version)
        self.assertEqual("allow", policy.default_effect)
        self.assertGreaterEqual(len(policy.rules), 11)

    def test_every_rule_has_a_reason_and_every_shell_rule_an_example(self) -> None:
        for rule in load_policy(_POLICY_FILE).rules:
            with self.subTest(rule=rule.id):
                self.assertTrue(rule.reason.strip())
                if rule.capability == "shell":
                    self.assertTrue((rule.example or "").strip())

    def test_effects_and_capabilities_are_closed_sets(self) -> None:
        self.assertEqual(("ask", "deny"), EFFECTS)
        self.assertEqual(("fs_read", "shell"), CAPABILITIES)
        for rule in load_policy(_POLICY_FILE).rules:
            with self.subTest(rule=rule.id):
                self.assertIn(rule.effect, EFFECTS)
                self.assertIn(rule.capability, CAPABILITIES)

    def test_schema_rejects_values_outside_the_closed_sets(self) -> None:
        mutations = {
            "unknown effect": lambda data: data["rules"][0].update(effect="allow"),
            "unknown capability": lambda data: data["rules"][0].update(capability="network"),
            "missing reason": lambda data: data["rules"][1].pop("reason"),
            "missing example": lambda data: data["rules"][1].pop("example"),
            "unknown key": lambda data: data["rules"][1].update(note="x"),
            "default not allow": lambda data: data.update(default_effect="ask"),
            "absolute home path": lambda data: data["rules"][0]["paths"].append(
                {"scope": "home", "path": "/etc/passwd", "kind": "file"}
            ),
            "glob with slash": lambda data: data["rules"][0]["paths"].append(
                {"scope": "any", "glob": "a/b"}
            ),
            "duplicate id": lambda data: data["rules"].append(copy.deepcopy(data["rules"][0])),
            "example outside rule": lambda data: data["rules"][1].update(example="ls -la"),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                data = _raw()
                mutate(data)
                with self.assertRaises(ValueError):
                    parse_policy(data)

    def test_force_push_is_denied_and_push_to_default_branch_only_asks(self) -> None:
        rules = {rule.id: rule for rule in load_policy(_POLICY_FILE).rules}
        self.assertEqual("deny", rules["deny-force-push"].effect)
        self.assertEqual("ask", rules["ask-push-default-branch"].effect)


class ReferenceEvaluatorTest(unittest.TestCase):
    """The six validation cases, as the canonical semantics define them."""

    def setUp(self) -> None:
        self._policy = load_policy(_POLICY_FILE)

    def _command(self, command: str) -> str:
        return evaluate(self._policy, command=command).effect

    def _read(self, path: str) -> str:
        return evaluate(self._policy, path=path, home=_HOME).effect

    def test_case_1_reading_or_editing_a_normal_file_is_allowed(self) -> None:
        self.assertEqual("allow", self._read("/work/project/src/app.py"))

    def test_case_2_routine_commands_are_allowed(self) -> None:
        for command in ("ls", "ls -la", "git status", "npm test", "git push origin feature"):
            with self.subTest(command=command):
                self.assertEqual("allow", self._command(command))

    def test_case_3_removing_a_test_file_asks(self) -> None:
        self.assertEqual("ask", self._command("rm tests/tmp_fixture.txt"))

    def test_case_4_reading_a_dotenv_file_asks(self) -> None:
        for path in ("/work/project/.env", "/work/project/config/.env.local"):
            with self.subTest(path=path):
                self.assertEqual("ask", self._read(path))

    def test_case_5_reading_home_credentials_asks(self) -> None:
        for path in ("~/.aws/credentials", "~/.ssh/id_ed25519", "/home/user/.ssh/config"):
            with self.subTest(path=path):
                self.assertEqual("ask", self._read(path))
        self.assertEqual("allow", self._read("~/.aws/config"))

    def test_case_6_deleting_without_rm_asks(self) -> None:
        for command in ("unlink a.txt", "find . -name '*.tmp' -delete", "git clean -fd"):
            with self.subTest(command=command):
                self.assertEqual("ask", self._command(command))

    def test_deny_wins_over_ask_for_the_same_command(self) -> None:
        decision = evaluate(self._policy, command="rm -rf /")
        self.assertEqual("deny", decision.effect)
        self.assertEqual(("deny-wipe-root-home",), decision.rule_ids)

    def test_compound_commands_are_checked_per_segment(self) -> None:
        self.assertEqual("ask", self._command("cd build && rm out.o"))
        self.assertEqual("deny", self._command("ls; sudo ls"))

    def test_push_variants(self) -> None:
        self.assertEqual("ask", self._command("git push origin main"))
        self.assertEqual("ask", self._command("git push -u origin master"))
        self.assertEqual("deny", self._command("git push --force origin feature"))
        self.assertEqual("deny", self._command("git push origin feature --force"))
        self.assertEqual("deny", self._command("git push origin +feature"))


if __name__ == "__main__":
    unittest.main()
