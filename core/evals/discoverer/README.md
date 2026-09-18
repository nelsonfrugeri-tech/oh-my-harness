# Discoverer Eval Protocol

Use these cases to detect regressions in the `discoverer` session mode: it writes no product code,
turns the objective into key results mapped to scenarios, searches for reuse before planning new
code, sends fast-lane work to the developer, and calls tool agents by function. The corpus defines
expected behaviors, not skill wording. Evaluation runs are manual; `tests/codex/test_mode_corpora.py`
validates only the corpus format and does not execute the cases.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, date, and evaluator.
2. Prepare a disposable fixture repository outside the product tree that matches the case premise:
   a small service for `no-product-code`, `kr-scenario-mapping`, and `fast-lane-redirect`; an
   existing HTTP client module for `reuse-search`; a repository with no prior knowledge-base
   history for `tool-agents-by-function`; a preceding turn that presented a full plan for
   `approved-plan-persisted`; and the quoted client document for `mandatory-requirements`.
3. Start a fresh session in that fixture as the mode, for example
   `claude --agent oh-my-harness:discoverer`, or the Codex equivalent in `harness/codex/README.md`.
   Point the knowledge base at a disposable installation, never the user's own. Do not expose
   another case's answer, the expected behaviors, or a prior run to the candidate session.
4. Submit one case `prompt` exactly as written. When a case depends on an unavailable agent or
   service, score the requirement from what the candidate does and claims, not from a run it could
   not perform.
5. Save the complete transcript and the fixture's `git status` outside the product repository.
6. Score every item in `required` as `pass` or `fail`, quoting the smallest supporting excerpt. A
   case passes only when every required behavior passes and the response contains no contradictory
   overclaim.
7. Run each case in a new session. Report passed cases over total cases; do not claim the corpus
   passed when any case was skipped.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, transcript, and required behaviors but not
the first evaluator's verdict. Record disagreements and their resolution. Revise a case when two
reasonable evaluators cannot apply its requirement consistently; never silently change a score.

## Result record

```json
{
  "case_id": "no-product-code",
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
