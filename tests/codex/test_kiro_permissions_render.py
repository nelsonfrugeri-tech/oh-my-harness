from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "installers"))

from policy.permissions import load_policy  # noqa: E402
from policy.render import render_kiro  # noqa: E402

_KIRO = _ROOT / "harness/kiro/permissions.yaml"


def _rules(text: str) -> list:
    """Parse the generated YAML subset: a list of {capability, match[], effect} mappings."""
    rules: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "rules:":
            continue
        if stripped.startswith("- capability: "):
            rules.append({"capability": stripped.split(": ", 1)[1], "match": []})
        elif stripped.startswith("effect: "):
            rules[-1]["effect"] = stripped.split(": ", 1)[1]
        elif stripped.startswith("- "):
            rules[-1]["match"].append(json.loads(stripped[2:]))
        elif stripped != "match:":
            raise AssertionError(f"unexpected YAML line: {line!r}")
    return rules


class KiroPermissionsRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._text = _KIRO.read_text(encoding="utf-8")

    def test_checked_in_yaml_matches_the_render(self) -> None:
        self.assertEqual(render_kiro(load_policy()), self._text)

    def test_header_marks_the_file_as_generated(self) -> None:
        self.assertTrue(self._text.startswith("# Generated from core/policies/permissions.json"))

    def test_allow_all_comes_first_then_ask_and_deny(self) -> None:
        rules = _rules(self._text)
        self.assertEqual({"capability": "all", "match": [], "effect": "allow"}, rules[0])
        effects = [rule["effect"] for rule in rules[1:]]
        self.assertEqual(sorted(effects, key=("ask", "deny").index), effects)
        self.assertEqual({"fs_read", "shell"}, {rule["capability"] for rule in rules[1:]})

    def test_patterns_cover_the_validation_cases(self) -> None:
        patterns = {
            (rule["capability"], rule["effect"]): rule["match"] for rule in _rules(self._text)
        }
        reads = [p for (cap, eff), match in patterns.items() if cap == "fs_read" for p in match]
        self.assertIn("**/.env", reads)
        self.assertIn("~/.aws/credentials", reads)
        self.assertIn("~/.ssh/**", reads)
        ask = [p for rule in _rules(self._text) if rule["effect"] == "ask" for p in rule["match"]]
        deny = [p for rule in _rules(self._text) if rule["effect"] == "deny" for p in rule["match"]]
        for pattern in ("rm *", "unlink *", "find * -delete", "git push origin main"):
            self.assertIn(pattern, ask)
        for pattern in ("rm -rf /", "sudo *", "git push --force *"):
            self.assertIn(pattern, deny)
        self.assertFalse(any(re.search(r"/\*$", pattern) and pattern.startswith("rm ") for pattern in deny))


if __name__ == "__main__":
    unittest.main()
