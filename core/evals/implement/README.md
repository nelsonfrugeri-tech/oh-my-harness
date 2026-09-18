# Implement Eval Protocol

Use these cases to detect regressions in how `implement` applies
[way-of-building.md](../../skills/implement/references/way-of-building.md): the reference must shape
greenfield and silent repositories, and must yield to a repository convention. The corpus defines
expected behaviors, not reference wording. Evaluation runs are manual;
`tests/codex/test_implement_corpus.py` validates only the corpus format and does not execute the
cases.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, date, and evaluator.
2. Prepare a disposable fixture repository outside the product tree that matches the case premise:
   empty for a greenfield case, or containing the stated convention and `CONTRIBUTING.md` for an
   existing-repository case.
3. Start a fresh session in that fixture with the adapter under test installed. Do not expose
   another case's answer, the expected behaviors, or a prior run to the candidate session.
4. Submit one case `prompt` exactly as written. Allow only the tools the scenario naturally needs;
   when a case depends on an unavailable service, score the requirement from what the candidate
   claims about it, not from a run it could not perform.
5. Save the complete transcript and resulting diff outside the product repository.
6. Score every item in `required` as `pass` or `fail`, quoting the smallest supporting excerpt from
   the transcript or diff. A case passes only when every required behavior passes and the response
   contains no contradictory overclaim.
7. Run each case in a new session. Report passed cases over total cases; do not claim the corpus
   passed when any case was skipped.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, transcript, diff, and required behaviors
but not the first evaluator's verdict. Record disagreements and their resolution. Revise a case when
two reasonable evaluators cannot apply its requirement consistently; never silently change a score.

## Result record

```json
{
  "case_id": "greenfield-closed-categories",
  "harness": "claude-code",
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
