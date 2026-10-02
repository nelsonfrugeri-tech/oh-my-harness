# Output Response Eval Protocol

Use these cases to detect regressions in the output contract, the `output-response` skill and the
global prompt essence, across harnesses and model updates. The corpus defines observable behaviors,
not reference wording. It merges the former evidence (12) and didactic-visual (6) corpora, whose
cases keep their `prompt` and `required` items verbatim except for the skill name, and adds cases
for labels on every assertion, the character budget, questions to the user, and sentence length.

Runs are manual. `tests/codex/test_output_response_corpus.py` validates only the corpus format;
`tests/codex/test_output_response_budget.py` tests the budget counter. Neither executes a case.

## Case fields

| Field | Meaning |
| --- | --- |
| `id` | Stable case identifier. |
| `kind` | One of `direct`, `explanation`, `decision`, `code_review`, `diagnosis`, `plan`; it selects the budget. |
| `prompt` | The exact user message, in pt-BR. |
| `required` | Behaviors the evaluator scores, in pt-BR. |

Label cases are the cases whose `kind` is `direct` or `explanation`. Question cases are the cases
whose `id` starts with `question-`.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, installation, date,
   and evaluator.
2. Start a fresh session for every case. Do not expose another case's answer, the required
   behaviors, or a prior run to the candidate session.
3. Run every case with the global adapter installed. Repeat the cases whose `id` contains
   `plugin-only` with the plugin-only installation, where no global prompt is loaded.
4. Isolate the candidate from global prompts that are not under test. In Claude Code, a separate
   `CLAUDE_CONFIG_DIR` that holds only the worktree `harness/claude/CLAUDE.md` is the intended
   isolation; confirm with `/memory` that no other global file loads before scoring. In Codex, use a
   temporary `CODEX_HOME` populated by `installers/codex/install.py`.
5. Submit the `prompt` exactly as written. Allow only the tools the scenario naturally needs.
6. Save the complete response outside the product repository or in the evaluation system of record.
7. Run `python3 core/evals/output-response/count_budget.py --kind <kind> <saved-response.md>`. It
   prints the counted characters, the budget status, and every sentence over 25 words. A response of
   an exempt kind (`code_review`, `diagnosis`, `plan`) is recorded as `exempt` and its budget is not
   scored.
8. Score every item in `required` as `pass` or `fail`, quoting the smallest supporting excerpt.
   A case passes only when every required behavior passes and the response contains no
   contradictory overclaim.
9. Report passed cases over total cases per harness; never claim the corpus passed when any case
   was skipped.

## Score labels and sentences

- A label passes only when it is one of the seven labels written exactly as in
  `core/policies/software-evidence-contract.md`, emoji, bold, and casing included.
- Every assertion needs a label. A transitional sentence or an instruction to the user must carry
  none; a label on either is a failure.
- The counter lists sentences over 25 words. The evaluator classifies each remaining sentence as
  procedural or descriptive and fails a procedural sentence over 20 words.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, response, and required behaviors but not
the first evaluator's verdict. Record disagreements and their resolution. Revise a case when two
reasonable evaluators cannot apply its requirement consistently; never silently change a score.

## Result record

```json
{
  "case_id": "budget-direct",
  "kind": "direct",
  "installation": "global",
  "harness": "codex",
  "model": "model identifier",
  "commit": "repository revision",
  "observed_at": "ISO-8601 timestamp",
  "budget": {"status": "within_budget", "chars": 612, "limit": 800},
  "long_sentences": [],
  "requirements": [{"text": "required behavior", "verdict": "pass", "evidence": "excerpt"}],
  "contradictory_overclaim": false,
  "verdict": "pass"
}
```

Treat an eval result as evidence only for the recorded harness, model, installation,
configuration, commit, and observation time. It does not prove identical behavior in another
session.
