---
name: developer
description: >-
  Workflow of the developer session mode. Builds the latest approved plan revision, or a fast-lane
  change, in an isolated git worktree and runtime: writes the plan's test scenarios first,
  implements in thin slices, runs end-to-end checks in the real runtime, and finishes with a
  conformance matrix against the plan. Use when the developer agent runs as the session agent, or
  when the user explicitly asks to build an approved plan. Do not use for discovery or an
  independent review verdict.
metadata:
  type: workflow
  version: 1.0.0
  origin: native
  last_verified: 2026-09-18
---

# Developer

Build exactly what the plan asks, prove it in the real runtime, and hand the evidence to the
reviewer. Apply [modes.md](../feature/references/modes.md) for tiers, lane, triage, isolation, and
handoff, and [plan.md](../feature/references/plan.md) for the plan contract. `implement` and `test`
own execution and verification; this skill sequences them.

## Start

1. Ask `knowledge-base` for the latest non-deprecated plan revision of the project and feature, and
   cite it. Without a plan, confirm the fast lane: one sentence, no new module, no public contract
   change, no LLM behavior change, no data migration. Any of those sends the user to the discoverer.
2. Create a git worktree outside the product checkout and an isolated runtime per modes.md.
3. Triage specialists as consultants and announce the call.
4. Load the framework documentation and stack skills before writing any code.

## Build test-first in thin slices

1. For new code, start with a walking skeleton: the thinnest end-to-end path through the real entry
   point, the real external services, and observability, seen running.
2. Write the plan's scenarios as tests first and observe them fail for the intended reason. Derive
   expected values from the plan or the dataset, never from what the code returns.
3. Add one thin vertical slice at a time with `implement`, applying its code-craft and
   way-of-building references. Run the slice's unit and integration tests and the gates, then run
   it against the real system before the next slice.
4. Run the repository's broad gates.

Do small or sequential work directly. Delegate only substantial, independent, parallelizable work,
and name in the brief the skills to load before code.

## Prove it end to end

Bring the environment up with the plan's commands and run the end-to-end check. Evidence is an
observation from the real runtime: an HTTP response, a database record, a trace in the backend, or
an eval score. "The code calls the SDK" is not evidence.

- If an external dependency blocks the end-to-end check, the status is `partially-completed` with
  the gap named. Never mask it with a mock.
- A flaky end-to-end check is a defect to fix, not a retry to hide.

## Never deviate silently

A change to the objective, a key result, a scenario, the layout, or the scope is a deviation.
Record it and return it to the user, or to the discoverer, before continuing. An accepted deviation
or a changed key result becomes a new plan revision through `knowledge-base`.

## Declare done with a conformance matrix

The matrix is an author self-check and input to review, never a verdict.

```markdown
# Conformance: <project> / <feature> - plan revision <n> - round <r>

| Plan item | Expected | Observed | Evidence |
| --- | --- | --- | --- |
| Objective | <objective> | <met / not met> | <observation> |
| KR1 | <target> | <observed value> | <method, command, output> |
| S1 | <scenario> | <pass / fail> | <test name and run output> |
| AC1 | <criterion> | <pass / fail> | <command and result> |

**Nothing beyond the plan:** <none, or each extra change with its justification>
**Deviations:** <none, or each one with the user's decision>
**Environment:** <owner, label, endpoints, teardown command>
**Status:** <completed | partially-completed | blocked>
```

Remove any change the plan does not ask for unless it is justified in the matrix. Save the matrix in
the handoff directory and give the user its path.

## Hand off and iterate

Leave the environment up for the user with its owner, label, and one-command teardown. Suggest
starting the reviewer mode, ideally in another session or harness. When a review report arrives,
read it from the handoff directory, fix each finding, and produce the next round's matrix.

Talk with the user in simple, direct language with progressive disclosure.
