---
name: implement
description: >-
  Executes bounded repository changes through project discovery, mode selection, red-capable
  verification, incremental implementation, focused and broad gates, and an author self-check.
  Use for feature, bug, refactor, configuration, documentation, migration, generated-code, and
  flaky or asynchronous implementation work. Do not use it to issue an independent review or merge
  recommendation.
metadata:
  type: capability
  version: 2.0.0
  origin: native
  last_verified: 2026-09-06
---

# Implement

Produce the smallest repository-native change whose behavior and validation can be inspected. Apply
`evidence` to material claims and decisions, and use `test` when verification design or test
lifecycle behavior is material.

## Guard the boundary

- This skill owns change execution, not product prioritization, independent code review, release
  approval, QA certification, or production operation.
- Read the applicable repository instructions before changing code. Repository conventions define
  style, typing, layout, commands, and artifacts unless they conflict with safety or the user's task.
- Keep temporary probes, reports, generated patches, and scratch notes outside the product tree.
  Add only code, tests, configuration, and documentation intended for version control.
- Retrieve live official documentation when current framework, dependency, or vendor syntax is
  required. Do not rely on examples embedded in this skill as a version contract.
- Preserve unrelated work in a shared or dirty worktree. Never make cleanup or baseline operations
  rewrite someone else's changes.

## Run the adaptive state machine

```text
DISCOVER
  -> CLARIFY or BLOCKED
  -> SELECT_MODE
  -> OBSERVE_OR_DEFINE
  -> RED_CAPABILITY when feasible
  -> IMPLEMENT
  -> FOCUSED_GATE
  -> BROAD_GATES
  -> AUTHOR_SELF_CHECK
  -> REPORT or INDEPENDENT_REVIEW_HANDOFF
```

States may loop when new evidence invalidates an assumption. Resume from the first state whose
evidence is absent or stale; do not repeat completed external side effects merely because a session
was interrupted.

### DISCOVER

1. Resolve the repository root, current revision, worktree status, applicable instructions, task
   scope, and user authority.
2. Read the relevant implementation, tests, documentation, configuration, and recent history. Use
   project memory only when prior work is material, then revalidate mutable facts in the repository.
3. Identify the observable behavior, affected consumers, compatibility constraints, generated
   boundaries, and likely failure surface.
4. Discover project commands in this order:
   1. an explicit user-provided command for this task;
   2. repository entry points such as Make, Just, Task, or checked-in scripts;
   3. package manifests, workspace configuration, and lockfiles;
   4. CI workflows as corroboration of exact invocation and environment;
   5. a language default only when the repository defines no stronger convention.
5. For every command considered, record its source and working directory and classify:
   - filesystem effect: read-only, check-only, or mutating;
   - connectivity: offline or networked;
   - state: ephemeral local, persistent local, shared service, or external system;
   - risk: non-destructive, scoped destructive, or broad/irreversible.

Do not run a command merely because its name resembles `check` or `test`. Inspect what the target
does when its effects are unclear. A user-provided command has discovery precedence, not permission
to exceed the user's authority or bypass a safety boundary.

### CLARIFY or BLOCKED

Inspect available evidence before asking. Ask one focused question only when unresolved ambiguity
would materially change behavior, public contract, data handling, migration direction, or blast
radius. Continue with an explicit, reversible assumption when the choice is low risk and within
scope; report it as an assumption.

Enter `BLOCKED` when required authority, credentials, source artifacts, runtime access, or a
material product decision is unavailable and no safe partial result remains. Name the missing item,
why it matters, what was still completed, and the smallest unblock action.

### SELECT_MODE

| Mode | Required emphasis |
| --- | --- |
| `feature` | Observable acceptance criteria, a public seam, compatibility, and the thinnest useful slice. |
| `bug` | Expected versus actual behavior, a reproducible failing observation, hypothesis isolation, and regression protection. |
| `refactor` | Declared unchanged behavior, characterization at public seams, and focused equivalence checks. |
| `configuration` | Schema or parser validation, precedence and environment effects, dry-run/check mode, and rollback. |
| `documentation` | Audience-visible claim, links/examples/rendering where applicable, and no invented runtime result. |
| `migration` | Pre/post invariants, compatibility window, rehearsal, data ownership, rollback, and resumability. |
| `generated` | Source template/schema/generator ownership; change inputs and regenerate instead of hand-editing output. |
| `flaky/async` | Timing, ordering, concurrency, retries, cancellation, seeds, and repeated evidence sized to the failure mechanism. |

Use the primary mode plus only the modifiers that change execution. A documentation-only typo
should remain lightweight; a generated migration may require both `generated` and `migration`.

### OBSERVE_OR_DEFINE

- For a bug, capture the smallest reliable reproduction with environment, input, expected result,
  actual result, and frequency. Keep root-cause explanations as hypotheses until discriminating
  evidence supports them. Load [workflow-bug-fix.md](references/workflow-bug-fix.md).
- For a feature, turn the request into observable acceptance criteria. Prefer behavior visible
  through a stable public seam over assertions about private calls or internal structure.
- For a refactor, state the behavior that must remain unchanged and characterize weakly protected
  seams before structural edits.
- For configuration, documentation, migration, or generated output, define an executable validator,
  parser/build check, invariant comparison, or precise reviewable diff as the observation.

If current behavior cannot be observed, report `unable-to-reproduce` or the applicable degraded
mode. Do not silently switch from diagnosis to speculative repair.

### RED_CAPABILITY when feasible

Create or identify a check that can fail for the missing behavior or defect. Run it before the fix
when safe and feasible, and record the observed failure rather than asserting that it was red.

A useful red-capable check:

- isolates one behavior at a time;
- derives expected values independently of the implementation under test;
- exercises a public seam at the lowest level that can expose the risk;
- fails for the intended reason, not because setup, syntax, or an unrelated dependency is broken;
- covers the relevant error, async, ordering, or lifecycle path when that is the defect.

Test-first ordering is not mandatory when the artifact is non-executable, generated elsewhere, the
reproduction would be destructive, or the required environment is unavailable. Use the strongest
safe alternative and record why a pre-change red observation was infeasible. A test that already
passes does not reproduce the defect.

### IMPLEMENT

1. Choose the smallest sufficient design and apply
   [code-craft.md](references/code-craft.md) to the changed code.
2. Change one coherent behavior at a time. Re-run the focused observation after each meaningful
   increment so diagnosis remains tight.
3. Preserve established public contracts unless the task explicitly changes them. Update consumers
   and migration paths when a contract changes.
4. Do not hand-edit generated files unless the repository explicitly treats them as source. Run the
   discovered generator and inspect the resulting diff.
5. Do not mix unrelated cleanup with the task. Never overwrite, stash, checkout, reset, or discard
   another contributor's work to obtain a clean baseline.

For history isolation or regression search, use a separate disposable worktree and an automated,
side-effect-bounded predicate. Do not run bisect in the active dirty worktree. For API probes,
derive the method, route, payload, authentication boundary, and target environment from the project;
never substitute a hardcoded mutating request.

### FOCUSED_GATE

Run the narrowest discovered check that exercises the changed behavior. Record command, discovery
source, working directory, exit status, observed counts or output, environment limitations, and the
behavior it actually proves. For a flaky check, one pass is not evidence of resolution; vary or
repeat the dimensions implicated by the failure and preserve every attempt.

### BROAD_GATES

Run the applicable project-defined format, lint, type, build, test, and integration gates after the
focused check passes. Follow project ordering when defined. Otherwise order cheap diagnostic gates
before expensive or stateful ones.

- Scope mutating formatters to owned files when unrelated changes exist; use check mode when scope
  cannot be isolated.
- Inspect setup and teardown before running integration or environment targets. Teardown may remove
  only resources whose ownership was established by this run.
- Missing tools, network denial, absent services, and pre-existing failures are limitations, not
  passes. Record the failed command and do not silently replace a project gate with a weaker default.
- A passing broad suite proves only the exercised revision, environment, and cases; it does not prove
  the absence of defects.

### AUTHOR_SELF_CHECK

Before handoff, inspect the task, acceptance criteria, final diff, focused and broad evidence,
security-sensitive boundaries, generated artifacts, documentation impact, and code-craft alignment.
Confirm that every changed file is in scope and that no temporary artifact entered the repository.

This is an author self-check. Report corrections made and unresolved risks, but never issue an
independent review verdict, approval, or merge recommendation. When independent review is required,
handoff the task, diff scope, decisions, executed commands, evidence, and limitations to a distinct
reviewer governed by the review capability.

## Command safety

Resolve exact targets before any destructive or state-changing operation. Prefer a preview,
check-only mode, isolated fixture, transaction, unique namespace, disposable worktree, or recoverable
operation. Broad container/volume cleanup, database-wide drop or cascade truncation, snapshot
overwrite, active-worktree checkout/stash, and unscoped recursive formatting are not routine gates.
Run them only when the exact owned target, necessity, authorization, and recovery plan are explicit.

## Report the outcome

Use one status:

- `completed`: requested change is implemented and all applicable available gates passed;
- `partially-completed`: useful in-scope work is done, with named remaining work or unavailable gate;
- `blocked`: progress requires a named external decision, authority, or dependency;
- `unable-to-reproduce`: the reported behavior was not observed after the documented attempts.

Report the status, mode, changed files, observed behavior or acceptance criteria, red-capable evidence
or exception, focused and broad commands with source/cwd/exit status, author self-check findings,
limitations, residual risk, and next handoff. Do not claim commands or reviews that were not run.

## Maintenance triggers

Re-evaluate this skill when project command-discovery fixtures fail, a safety incident exposes an
unclassified side effect, the independent-review boundary drifts, or paired evaluations show that a
narrower external mechanism improves execution without unacceptable cost.
