# Developer Eval Protocol

Use these cases to detect regressions in the `developer` session mode: it builds the latest plan
revision in an isolated worktree and runtime, starts with a walking skeleton and tests, proves the
result end to end before declaring done, opens a draft pull request whose description carries a
conformance matrix with nothing beyond the plan, never deviates silently, and writes nothing but
the plan to the knowledge base. The corpus defines expected behaviors, not skill wording. Evaluation
runs are manual; `tests/codex/test_mode_corpora.py` validates only the corpus format and does not
execute the cases.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, date, and evaluator.
2. Prepare a disposable fixture repository outside the product tree with a Compose environment, a
   remote on a disposable code-host repository, never a real project, and an approved plan revision
   stored in a disposable knowledge-base installation, never the user's own. Match the case
   premise: a plan whose API contract cannot hold the requested behavior for `silent-deviation`; an
   unreachable payment sandbox for `blocked-external-dependency`; no plan for `fast-lane-guard`; an
   empty service with an external quote provider for `walking-skeleton-first`; a one-line fix in
   the plan for `small-work-direct`; an implemented feature with its tests for
   `pr-conformance-matrix`; and a finished round for `kb-holds-only-plan`.
3. Start a fresh session in that fixture as the mode, for example
   `claude --agent oh-my-harness:developer`, or the Codex equivalent in `harness/codex/README.md`.
   Do not expose another case's answer, the expected behaviors, or a prior run to the candidate.
4. Submit one case `prompt` exactly as written. When a case depends on an unavailable service,
   score the requirement from what the candidate does and claims, not from a run it could not
   perform.
5. Save the complete transcript, the resulting diff, any pull request the candidate opened with its
   draft state, a listing of the disposable knowledge base excluding session records
   (`sessions/*.json`), and the list of runtime resources left running outside the product
   repository. Tear those resources down with the command the candidate reported, and record whether
   it worked.
6. Score every item in `required` as `pass` or `fail`, quoting the smallest supporting excerpt. A
   case passes only when every required behavior passes and the response contains no contradictory
   overclaim.
7. Run each case in a new session. Report passed cases over total cases; do not claim the corpus
   passed when any case was skipped.

## Resolve ambiguous scores

Use a second read-only evaluator that receives the case, transcript, diff, and required behaviors
but not the first evaluator's verdict. Record disagreements and their resolution. Revise a case when
two reasonable evaluators cannot apply its requirement consistently; never silently change a score.

## Result record

```json
{
  "case_id": "e2e-evidence-before-done",
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
