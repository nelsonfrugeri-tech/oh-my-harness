# Bug-Fix Workflow

Use this reference for `bug` mode. Keep observations, hypotheses, and claims distinct throughout.

```text
OBSERVE -> REPRODUCE -> ISOLATE -> RED -> FIX -> VERIFY -> PREVENT
```

## Observe and reproduce

Record the environment and revision, input or event sequence, expected behavior, actual behavior,
frequency, and the smallest command or interaction that exhibits the defect. A report, log, or
passing test may motivate investigation but does not by itself reproduce the behavior.

If reproduction is unavailable, inspect the strongest existing evidence and vary one plausible
dimension at a time. End as `unable-to-reproduce` when further progress would require guessing;
report attempts, observations, remaining hypotheses, and the next discriminating input needed.

For an intermittent failure, preserve every attempt plus seed, order, timing, load, environment, and
dependency state that could affect it. One pass cannot establish a flaky defect is fixed.

## Isolate

Form competing hypotheses and choose the cheapest safe observation that distinguishes them. Narrow
the code path, data boundary, timing window, or dependency without changing multiple dimensions at
once. Do not claim root cause until evidence rules out material alternatives at the scope of the
claim.

If commit-history isolation is useful, run the predicate in a separate disposable worktree with
bounded side effects and deterministic setup/teardown. Never stash, checkout, reset, or bisect the
active shared worktree as a diagnostic shortcut.

## Create red-capable regression evidence

Prefer a regression check that fails on the affected revision for the intended reason and exercises
the stable public seam. Keep the expected value independent of the implementation. Include the error,
async, ordering, cancellation, or cleanup behavior when it is part of the defect.

If a pre-fix red check is unsafe or infeasible, record why and use the strongest safe alternative:
a captured reproduction, parser/build failure, invariant comparison, isolated runtime probe, or a
test proven red against an equivalent fixture. A test that passes before the fix is not regression
evidence for that defect.

## Fix and verify

Change the smallest coherent cause supported by the evidence. Keep unrelated refactoring separate.
Run the unchanged focused reproduction or regression check, then the applicable broader project
gates. Re-run the original user-visible observation when it is safe and distinct from the automated
check.

A passing command establishes only its exercised revision, environment, data, and assertions. Report
the corrected observation; call it a root-cause fix only when the isolation evidence supports that
causal scope.

## Prevent recurrence

Retain the regression check when it is stable and proportionate. Inspect adjacent instances only
when they share the evidenced mechanism. Consider a type, schema, lint, invariant, telemetry, or
process guard when it prevents the same failure class more directly than duplicating tests.

For urgent mitigation, separate the reversible containment step from the durable correction. Define
the rollback signal and post-change observation before applying any production-affecting action.
