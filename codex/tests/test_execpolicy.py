from __future__ import annotations

import ast
import json
import shutil
import subprocess
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, cast


_ROOT = Path(__file__).resolve().parents[2]
_RULES = _ROOT / "codex/rules/destructive.rules"
_DESTRUCTIVE_COMMANDS = (
    ("git", "reset", "--hard"),
    ("git", "clean", "-fd"),
    ("git", "push", "origin", "--force", "main"),
    ("git", "push", "origin", "--force-with-lease", "main"),
    ("git", "push", "--force", "origin", "main"),
    ("git", "push", "--force-with-lease", "origin", "main"),
    ("git", "push", "--delete", "origin", "obsolete"),
    ("git", "push", "origin", "--delete", "obsolete"),
    ("docker", "system", "prune"),
    ("docker", "builder", "prune"),
    ("docker", "image", "prune"),
    ("docker", "container", "prune"),
    ("docker", "volume", "prune"),
    ("docker", "network", "prune"),
    ("kubectl", "delete", "pod", "example"),
)
_NORMAL_COMMANDS = (
    ("git", "status"),
    ("git", "fetch", "origin"),
    ("docker", "info"),
    ("docker", "system", "info"),
    ("docker", "image", "ls"),
    ("kubectl", "get", "pods"),
)
_BEHAVIORAL_ONLY_COMMANDS = (
    ("git", "-C", "/tmp", "reset", "--hard"),
    ("git", "--work-tree=/tmp", "clean", "-fd"),
    ("git", "push", "origin", "main", "--force"),
    ("docker", "--context", "remote", "system", "prune"),
    ("kubectl", "--context", "dev", "delete", "pod", "example"),
)


@dataclass(frozen=True)
class _Rule:
    pattern: tuple[str | tuple[str, ...], ...]
    decision: str


class ExecPolicyContractTest(unittest.TestCase):
    def test_destructive_command_variants_prompt(self) -> None:
        for command in _DESTRUCTIVE_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("prompt", _decision(command))

    def test_normal_commands_remain_unmatched(self) -> None:
        for command in _NORMAL_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("unmatched", _decision(command))

    def test_prefix_engine_limit_defers_to_behavioral_policy(self) -> None:
        for command in _BEHAVIORAL_ONLY_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("unmatched", _decision(command))

    def test_fallback_evaluator_enforces_the_same_contract(self) -> None:
        for command in _DESTRUCTIVE_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("prompt", _fallback_decision(command))
        for command in _NORMAL_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("unmatched", _fallback_decision(command))
        for command in _BEHAVIORAL_ONLY_COMMANDS:
            with self.subTest(command=command):
                self.assertEqual("unmatched", _fallback_decision(command))


def _decision(command: tuple[str, ...]) -> str:
    executable = shutil.which("codex")
    if executable and _supports_execpolicy(executable):
        return _codex_decision(executable, command)
    return _fallback_decision(command)


def _supports_execpolicy(executable: str) -> bool:
    completed = subprocess.run(
        (executable, "execpolicy", "check", "--help"),
        capture_output=True,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def _codex_decision(executable: str, command: tuple[str, ...]) -> str:
    completed = subprocess.run(
        (executable, "execpolicy", "check", "--rules", str(_RULES), *command),
        capture_output=True,
        check=True,
        text=True,
    )
    result = cast(dict[str, object], json.loads(completed.stdout))
    return str(result.get("decision", "unmatched"))


def _fallback_decision(command: tuple[str, ...]) -> str:
    decisions = (
        rule.decision for rule in _load_rules() if _matches(rule.pattern, command)
    )
    return max(decisions, key=_severity, default="unmatched")


def _load_rules() -> tuple[_Rule, ...]:
    tree = ast.parse(_RULES.read_text(encoding="utf-8"))
    calls = (
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "prefix_rule"
    )
    return tuple(_parse_rule(call) for call in calls)


def _parse_rule(call: ast.Call) -> _Rule:
    arguments = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg}
    raw_pattern = cast(
        List[Union[str, List[str]]], ast.literal_eval(arguments["pattern"])
    )
    pattern = tuple(
        tuple(element) if isinstance(element, list) else element
        for element in raw_pattern
    )
    decision = cast(str, ast.literal_eval(arguments["decision"]))
    return _Rule(pattern, decision)


def _matches(
    pattern: tuple[str | tuple[str, ...], ...], command: tuple[str, ...]
) -> bool:
    if len(command) < len(pattern):
        return False
    return all(
        actual in expected if isinstance(expected, tuple) else actual == expected
        for expected, actual in zip(pattern, command)
    )


def _severity(decision: str) -> int:
    return {"unmatched": 0, "allow": 1, "prompt": 2, "forbidden": 3}[decision]


if __name__ == "__main__":
    unittest.main()
