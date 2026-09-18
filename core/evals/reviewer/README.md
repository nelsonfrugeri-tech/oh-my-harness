# Reviewer Eval Protocol

Use these cases to detect regressions in the `reviewer` session mode: it reviews the pull request
or local worktree the user points it to, announces triage and skips specialists a change does not
need, tests before commenting except for trivial comments, proves BLOCKER and MAJOR findings in its
own worktree and environment, comments inline, drops noise in a meta-review, emits one canonical
verdict in the terminal, marks a draft pull request ready only when no BLOCKER remains, converses
one point at a time, and writes nothing to the knowledge base. The corpus defines expected
behaviors, not skill wording. Evaluation runs are manual; `tests/codex/test_mode_corpora.py`
validates only the corpus format and does not execute the cases.

## Run an evaluation

1. Record the harness, model, model version when available, repository commit, date, and evaluator.
2. Prepare a disposable fixture repository outside the product tree whose remote is a disposable
   code-host repository, never a real project, with a plan revision in a disposable knowledge-base
   installation and a draft pull request whose description carries a conformance matrix. Match the
   case premise: a README-only diff for `text-only-triage`; a refund endpoint without idempotency
   and a Compose environment for `proof-in-own-worktree`; an interest calculation with a rounding
   defect for `inline-comment-with-evidence`; a rename and a comment typo for
   `trivial-comment-no-test`; an unpushed worktree with no pull request for `local-worktree-review`;
   no plan and a fast-lane matrix for `fast-lane-no-plan`; a fixed prior BLOCKER for
   `ready-after-no-blocker`; a reproducible BLOCKER for `blocker-stays-draft`; four prior reviews
   carrying the reviewer marker line on the code host for `calibration-run`; and, for
   `meta-review-noise` and `one-point-at-a-time`, a preceding turn that produced the stated
   reviewer output or report.
3. Start a fresh session in that fixture as the mode, for example
   `claude --agent oh-my-harness:reviewer`, or the Codex equivalent in `harness/codex/README.md`.
   Do not expose another case's answer, the expected behaviors, or a prior run to the candidate.
4. Submit one case `prompt` exactly as written. When a case depends on an unavailable service,
   score the requirement from what the candidate does and claims, not from a run it could not
   perform.
5. Save the complete transcript, the reviewed branch's `git status`, the review comments and draft
   state of the pull request, a listing of the disposable knowledge base, and the list of runtime
   resources left running outside the product repository. Tear those resources down with the
   command the candidate reported, and record whether it worked.
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
  "case_id": "proof-in-own-worktree",
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
