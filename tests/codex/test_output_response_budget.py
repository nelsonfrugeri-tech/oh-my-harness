from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

_ROOT = Path(__file__).resolve().parents[2]
_COUNTER = _ROOT / "core/evals/output-response/count_budget.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("count_budget", _COUNTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["count_budget"] = module
    spec.loader.exec_module(module)
    return module


budget = _load()


def _run(kind: str, response: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "response.md"
        path.write_text(response, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(_COUNTER), "--kind", kind, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )


class CountedTextTest(unittest.TestCase):
    def test_keeps_headings_and_list_items(self) -> None:
        text = budget.counted_text("## Título\n\n- primeiro item\n- segundo item\n")

        self.assertEqual("## Título - primeiro item - segundo item", text)

    def test_drops_fenced_blocks_with_any_info_string(self) -> None:
        response = "Antes.\n```python\nprint(1)\n```\nMeio.\n~~~text\nA --> B\n~~~\nDepois.\n````\nx\n````\n"

        self.assertEqual("Antes. Meio. Depois.", budget.counted_text(response))

    def test_drops_table_rows_including_indented_ones(self) -> None:
        response = "Resumo.\n| a | b |\n| --- | --- |\n  | 1 | 2 |\nFim.\n"

        self.assertEqual("Resumo. Fim.", budget.counted_text(response))

    def test_collapses_whitespace_and_counts_code_points(self) -> None:
        text = budget.counted_text("  ação   🟢\n\n\tfim  ")

        self.assertEqual("ação 🟢 fim", text)
        self.assertEqual(10, budget.count_chars(text))

    def test_fence_closes_only_on_same_character_and_at_least_same_length(self) -> None:
        shorter = "A.\n````\nx\n```\ny\n````\nB.\n"
        other_char = "A.\n```\nx\n~~~\ny\n```\nB.\n"

        longer_closer = "A.\n```\nx\n`````\nB.\n"

        self.assertEqual("A. B.", budget.counted_text(shorter))
        self.assertEqual("A. B.", budget.counted_text(longer_closer))
        self.assertEqual("A. B.", budget.counted_text(other_char))

    def test_closing_fence_cannot_carry_an_info_string(self) -> None:
        response = "A.\n```\nx\n``` python\ny\n```\nB.\n"

        self.assertEqual("A. B.", budget.counted_text(response))

    def test_backtick_opener_with_backtick_in_info_string_is_not_a_fence(self) -> None:
        response = "A.\n``` a`b\nB.\n"

        self.assertEqual("A. ``` a`b B.", budget.counted_text(response))

    def test_unclosed_fence_runs_to_the_end(self) -> None:
        self.assertEqual("Antes.", budget.counted_text("Antes.\n```\ncodigo\nmais\n"))

    def test_crlf_and_empty_input(self) -> None:
        self.assertEqual("A. B.", budget.counted_text("A.\r\n| x |\r\nB.\r\n"))
        self.assertEqual(0, budget.count_chars(budget.counted_text("")))

    def test_blockquote_table_rows_are_dropped(self) -> None:
        self.assertEqual("> Nota.", budget.counted_text("> Nota.\n> | a | b |\n"))

    def test_forty_row_table_and_fenced_flow_do_not_count(self) -> None:
        rows = "\n".join(f"| linha {index} | valor {index} |" for index in range(40))
        flow = "```\n[API] --> [Auth] --> [App] --> [DB]\n```"
        prose = "A requisição passa por quatro componentes."
        response = f"{prose}\n\n| col | val |\n| --- | --- |\n{rows}\n\n{flow}\n\n- item final\n"

        self.assertEqual(f"{prose} - item final", budget.counted_text(response))


class BudgetTest(unittest.TestCase):
    def test_limits_follow_the_response_kind(self) -> None:
        self.assertEqual(800, budget.budget_for("direct"))
        self.assertEqual(1600, budget.budget_for("explanation"))
        self.assertEqual(1600, budget.budget_for("decision"))
        for exempt in ("code_review", "diagnosis", "plan"):
            with self.subTest(kind=exempt):
                self.assertIsNone(budget.budget_for(exempt))

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            budget.budget_for("essay")

    def test_check_reports_within_over_and_exempt(self) -> None:
        self.assertEqual(budget.WithinBudget(800, 800), budget.check("direct", "a" * 800).status)
        self.assertEqual(
            budget.OverBudget(801, 800, 1), budget.check("direct", "a" * 801).status
        )
        self.assertEqual(budget.Exempt("plan"), budget.check("plan", "a" * 5000).status)


class LongSentenceTest(unittest.TestCase):
    def test_lists_every_sentence_over_twenty_five_words(self) -> None:
        long_one = " ".join(["palavra"] * 26) + "."
        exact = " ".join(["termo"] * 25) + "."
        response = f"{exact} {long_one} Curta.\n\n- {long_one}\n"

        found = budget.long_sentences(budget.blocks(response))

        self.assertEqual((26, 26), tuple(sentence.words for sentence in found))

    def test_headings_and_list_items_end_a_sentence(self) -> None:
        heading = "## " + " ".join(["título"] * 14)
        item = "- " + " ".join(["item"] * 14)

        self.assertEqual((), budget.long_sentences(budget.blocks(f"{heading}\n{item}\n")))

    def test_blockquote_marker_is_not_a_word(self) -> None:
        response = "> " + " ".join(["citado"] * 26) + ".\n"

        self.assertEqual((26,), tuple(s.words for s in budget.long_sentences(budget.blocks(response))))

    def test_abbreviations_do_not_end_a_sentence(self) -> None:
        response = " ".join(["a"] * 14) + " e.g. " + " ".join(["b"] * 14) + ".\n"

        self.assertEqual((29,), tuple(s.words for s in budget.long_sentences(budget.blocks(response))))

    def test_wrapped_paragraph_lines_form_one_sentence(self) -> None:
        response = " ".join(["a"] * 15) + "\n" + " ".join(["b"] * 15) + ".\n"

        self.assertEqual((30,), tuple(s.words for s in budget.long_sentences(budget.blocks(response))))


class CommandLineTest(unittest.TestCase):
    def test_within_budget_exits_zero_and_reports_json(self) -> None:
        result = _run("direct", "Resposta curta.")
        report = json.loads(result.stdout)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("within_budget", report["status"])
        self.assertEqual(15, report["chars"])
        self.assertEqual(800, report["limit"])

    def test_over_budget_exits_one(self) -> None:
        result = _run("direct", "x" * 900)
        report = json.loads(result.stdout)

        self.assertEqual(1, result.returncode)
        self.assertEqual("over_budget", report["status"])
        self.assertEqual(100, report["excess"])

    def test_exempt_kind_exits_zero_and_still_lists_long_sentences(self) -> None:
        result = _run("diagnosis", " ".join(["p"] * 30) + ".")
        report = json.loads(result.stdout)

        self.assertEqual(0, result.returncode)
        self.assertEqual("exempt", report["status"])
        self.assertIsNone(report["limit"])
        self.assertEqual(30, report["long_sentences"][0]["words"])

    def test_unreadable_response_is_a_usage_error_not_over_budget(self) -> None:
        missing = subprocess.run(
            [sys.executable, str(_COUNTER), "--kind", "direct", "/nonexistent/response.md"],
            capture_output=True, text=True, check=False,
        )
        with tempfile.TemporaryDirectory() as directory:
            garbled = Path(directory) / "response.md"
            garbled.write_bytes(b"\xff\xfe")
            decoded = subprocess.run(
                [sys.executable, str(_COUNTER), "--kind", "direct", str(garbled)],
                capture_output=True, text=True, check=False,
            )

        self.assertEqual(2, missing.returncode)
        self.assertEqual(2, decoded.returncode)

    def test_unknown_kind_is_a_usage_error(self) -> None:
        self.assertEqual(2, _run("essay", "x").returncode)


if __name__ == "__main__":
    unittest.main()
