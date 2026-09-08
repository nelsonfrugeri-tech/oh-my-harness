# Didactic Visual Eval Protocol

Use these cases to detect behavioral regressions in the `didactic-visual` skill. The corpus
defines observable behaviors, not reference wording.

## Run the evaluation

1. Record the harness, model, version when available, commit, date, and evaluator.
2. Start each case in a fresh session with the adapter under test. Do not expose the requirements or
   another case's response to the candidate.
3. First run all cases with the plugin-only installation. Repeat with the global adapter to
   detect divergences between surfaces.
4. Send the `prompt` exactly as written and allow only the tools required by the scenario.
5. Save the complete response outside the product repository or in the adopted eval system.
6. Mark each `required` item as `pass` or `fail` and cite the shortest excerpt supporting the score.
   The case passes only when every requirement passes and there is no contradictory behavior.
7. Report passed cases over the total; never declare a pass when any case was omitted.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, response, and requirements, but not the
first verdict. Record disagreements and their resolution; never change a score silently.

## Result record

```json
{
  "case_id": "architecture-flow",
  "installation": "plugin-only",
  "harness": "codex",
  "model": "model identifier",
  "commit": "repository revision",
  "observed_at": "ISO-8601 timestamp",
  "requirements": [{"text": "required behavior", "verdict": "pass", "evidence": "excerpt"}],
  "contradictory_behavior": false,
  "verdict": "pass"
}
```

The result proves only the behavior observed with the recorded harness, model, configuration,
commit, and timestamp. It does not prove identical behavior in another session.
