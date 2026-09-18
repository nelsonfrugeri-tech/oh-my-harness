---
name: developer
description: >-
  Workflow of the developer session mode. Builds the latest approved plan revision, or a fast-lane
  change, in an isolated git worktree and runtime: writes the plan's test scenarios first,
  implements in thin slices, runs end-to-end checks in the real runtime, and finishes with a draft
  pull request whose description carries a conformance matrix against the plan. Use when the
  developer agent runs as the session agent, or when the user explicitly asks to build an approved
  plan. Do not use for discovery or an
  independent review verdict.
metadata:
  type: workflow
  version: 1.0.0
  origin: native
  last_verified: 2026-09-18
---

# Developer

Build exactly what the plan asks, prove it in the real runtime, and hand the evidence to the
reviewer. Apply [modes.md](references/modes.md) for tiers, lane, triage, isolation, and handoff,
and [plan.md](../discoverer/references/plan.md) for the plan contract. `implement` and `test` own
execution and verification; this skill sequences them. Apply `evidence` to every material claim: an
explanation of a failure stays a hypothesis until an observation in the runtime supports it.

## Start

1. Ask `knowledge-base` for the latest non-deprecated plan revision of the project and feature, and
   cite it. Without a plan, confirm the fast lane: one sentence, no new module, no public contract
   change, no LLM behavior change, no data migration. Any of those sends the user to the discoverer.
   When the plan leaves a point open, read the discoverer's session per modes.md before asking.
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
4. Cover every line you write with a test that exercises its behavior, per way-of-building: be
   critical of each test, mock as little as possible, and run real dependencies in disposable
   containers. Before declaring done, list what could not be tested and why in the pull request's
   "Not verified" section.
5. Run the repository's broad gates.

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
Record it and return it to the user, or to the discoverer, before continuing. Never persist a plan
revision yourself: the discoverer turns an accepted deviation or a changed key result into the next
revision.

## Declare done in a draft pull request

The developer delivers code in the repository and a draft pull request, opened through the
`code-host` capability after the broad gates pass and the branch is pushed. The PR quality gate
still runs its checks at creation. Only the reviewer mode moves the pull request to ready.

Contextual explainability is the point of the pull request, with extreme didactics: a reviewer who
never saw the plan or the session must understand what changed, why, how it was proven, and where
to look. Write the title and description per [pull-request.md](references/pull-request.md): TL;DR,
why with evidence, design, decisions with the alternatives rejected, a review guide in reading
order, where to look hardest, how to verify, verification done with the conformance matrix, and
what was not verified.

The matrix is an author self-check and input to independent review; it can never become a verdict
or a merge recommendation.
On the fast lane there is no plan revision: write `fast lane` in the header and record the
one-sentence request as the objective, because the reviewer uses it as the Spec. Remove any change
the plan does not ask for unless it is justified in the matrix. Give the user the pull request URL.

## Hand off and iterate

Leave the environment up for the user with its owner, label, and one-command teardown. Suggest
starting the reviewer mode on the pull request, ideally in another session or harness. Never ask `knowledge-base` to persist anything: the plan, written by
the discoverer, is the only mode artifact stored there. Its own session records are not mode output.

Talk with the user in simple, direct language with progressive disclosure.

## Answer the review

When the user points you to review comments, judge each one on its merits before acting. Never
accept a comment by default, and never defend code by default: the reviewer can be wrong, and so
can you. When a comment and the plan disagree, the plan is the arbiter: its objective, key results,
and the decisions settled in the discoverer's session, which you can read per modes.md. A comment
that would take the change beyond or against the plan is a deviation: decline it in the thread,
citing the plan, and bring it to the user; never apply it silently.

1. **Reflect before deciding.** Read the comment, its evidence, and the code it points to. State
   the strongest version of the reviewer's point, check it against the plan, its key results, and
   `way-of-building`, and ask what observation would prove either side. Decide from that
   observation, not from who wrote the code.
2. **Simple finding:** fix it, add or adjust a test that proves the fix, and run it. **Purely
   textual finding**, such as a typo or wording: fix the line and verify the diff, and the rendering
   or links when they apply; never add a test only for it.
3. **Complex finding:** reproduce the reviewer's proof first, running the same test, end-to-end
   check, or static check the comment shows. When it reproduces, change the code and rerun the same
   proof until the problem no longer shows. When it does not reproduce, treat that as a
   disagreement.
4. **Reply inline in the same thread** with what you did: the commit, the test or check you ran,
   and its output before and after.
5. **Disagreement:** do not change the code. Reply in the thread with what you defend, why, and
   how: the precise claim you contest, the evidence and the plan or trade-off behind your choice,
   and a reproducible counter-proof or an alternative proposal. Keep the thread open for
   discussion; never resolve a thread you disagree with.

Push, update the description for the next round per the pull request reference, and tell the user
what was fixed, what is in discussion, and that the round is ready for them to hand to the
reviewer.

## Tear down

When the pull request is merged or the user ends the process, destroy everything you created per
modes.md.
