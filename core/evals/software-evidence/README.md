# Software Evidence Eval Protocol

Use these cases to detect regressions in the evidence contract across harnesses and model updates.
The corpus defines expected behaviors, not reference wording.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, date, and evaluator.
2. Start a fresh session with the adapter under test installed. Do not expose another case's answer,
   the expected behaviors, or a prior run to the candidate session.
3. Submit one case `prompt` exactly as written. Allow only the tools the scenario naturally needs.
4. Save the complete response outside the product repository or in the evaluation system of record.
5. Score every item in `required` as `pass` or `fail`, quoting the smallest supporting response
   excerpt. A case passes only when every required behavior passes and the response contains no
   contradictory overclaim.
6. Run each case in a new session. Report passed cases over total cases; do not claim the corpus
   passed when any case was skipped.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, response, and required behaviors but not
the first evaluator's verdict. Record disagreements and their resolution. Revise a case when two
reasonable evaluators cannot apply its requirement consistently; never silently change a score.

## Result record

```json
{
  "case_id": "unsupported-number",
  "harness": "codex",
  "model": "model identifier",
  "commit": "repository revision",
  "observed_at": "ISO-8601 timestamp",
  "requirements": [{"text": "required behavior", "verdict": "pass", "evidence": "excerpt"}],
  "contradictory_overclaim": false,
  "verdict": "pass"
}
```

Treat an eval result as evidence only for the recorded harness, model, configuration, commit, and
observation time. It does not prove identical behavior in another session.
