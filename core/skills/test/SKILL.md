---
name: test
description: >-
  Designs and executes risk-based, red-capable verification for repository changes, including
  deterministic data and resource lifecycles, focused-to-broad gates, and explicit error, async,
  and flaky paths. Use when test strategy or implementation materially affects confidence. Do not
  use for an independent code-review, release, QA, or SRE verdict.
metadata:
  type: capability
  version: 2.0.0
  origin: native
  last_verified: 2026-09-06
---

# Test

Produce the smallest verification set that can expose the material failure modes of the requested
change and whose execution evidence can be reproduced.

## Guard the boundary

- Testing supplies observations; it does not certify that no defects exist, approve a merge, or
  substitute for an independent reviewer, QA owner, SRE owner, or release authority.
- Derive commands, frameworks, layout, naming, coverage policy, and test levels from the repository.
  Use the `implement` discovery ladder during change execution rather than prescribing a universal
  runner or test pyramid.
- Retrieve current syntax from official tool documentation only when the project actually uses that
  tool or must choose one. Do not keep volatile Playwright, Pact, k6, Locust, or similar setup
  instructions in this skill.
- Never use production data, credentials, accounts, endpoints, queues, buckets, databases, or
  shared developer resources as implicit test fixtures.

## Build a risk model

Before adding a test, identify:

1. the observable behavior or invariant;
2. the failure consequence and affected boundary;
3. the stable public seam that can expose it;
4. existing coverage and the regression that would escape it;
5. required data, clock, randomness, concurrency, process, network, and service state;
6. who owns creation and cleanup of every resource;
7. the narrowest check whose failure would be diagnostic.

Select test levels from this model. Pure transformation may need a small unit test; persistence,
serialization, process entry points, network boundaries, and browser behavior may require an
integration, subprocess, contract, or end-to-end observation. Do not add every level by default.

## Make verification red-capable

A test is useful for a change only when it can fail for the target defect or missing behavior.

- Assert one coherent behavior at a time.
- Compute expected values independently; do not call the implementation under test to construct its
  own expected output.
- Prefer public inputs, outputs, state transitions, and side effects over private call sequences.
- Run the check before the fix when safe and feasible. Confirm that it fails for the intended reason,
  then run the unchanged check after implementation.
- If a proposed regression test passes before the fix, improve the stimulus or assertion; it is not
  a reproduction.
- If pre-change red is infeasible, record the exact reason and use the strongest safe validator,
  parser/build check, invariant comparison, or reviewed diff available.

Generated artifacts should normally be verified by changing generator inputs, regenerating, and
checking deterministic output. Configuration should use the repository's parser, schema, dry-run,
or check mode. Documentation should validate links, examples, rendering, or declared structure only
where the project has an applicable mechanism.

## Keep tests deterministic

Control or record all dimensions that can change the result: clock and timezone, randomness and
seed, locale, ordering, scheduler/concurrency, retry policy, environment variables, filesystem
layout, network responses, and external service versions.

- Wait for an observable condition or bounded completion signal; do not use arbitrary sleeps as a
  correctness mechanism.
- Make failures explain the expected behavior, actual observation, and relevant controlled inputs.
- Keep tests independent. Shared fixtures may provide immutable reference data, but no test may
  depend on another test's order or leftovers.
- Do not hide nondeterminism with broad retries. A retry can collect evidence only when every attempt,
  seed/order, and outcome remains visible.

## Own the resource lifecycle

The fixture or harness that creates a resource owns its teardown. Use unique per-run or per-test
namespaces and delete only resources recorded as created by that owner. Ensure cleanup executes on
success, assertion failure, setup failure, and cancellation when the framework supports it.

Prefer transactions, temporary directories, disposable processes, isolated containers, and scoped
keys. Database-wide `drop_all`, `TRUNCATE ... CASCADE`, cache-wide flush, broad Compose volume or
orphan cleanup, and recursive deletion are prohibited unless the environment is proven ephemeral
and exclusively owned, the exact scope is previewed, the user has authorized the destructive step,
and recovery is understood.

Verify teardown when leakage is a material risk. A cleanup command succeeding does not prove the
intended resource set was removed; inspect the scoped postcondition.

## Exercise failure-sensitive paths

### Error paths

Trigger the real boundary condition and assert the public error contract plus relevant side effects:
status or exception, message/code where stable, no partial write, resource release, retry behavior,
and observability when required. A setup error is not evidence that the application error path works.

### Async and concurrent paths

Define the event or state transition that signals completion. Exercise timeout, cancellation,
ordering, duplicate delivery, race, and cleanup only where the risk model makes them material. Use
controlled schedulers, barriers, fake clocks, or deterministic event sources when the project
supports them; otherwise record the remaining nondeterminism.

### Flaky failures

Preserve the exact command, seed, order, environment, attempt count, and all outcomes. Reproduce the
suspected dimension, isolate the mechanism, and size repetitions or stress conditions to that
mechanism and decision risk; there is no universal retry count. One passing attempt cannot establish
that a flaky failure is fixed. Quarantine may limit disruption but is not a fix and must retain an
owner and observable follow-up condition.

## Run focused, then broad

1. Run the narrowest test or validator that exercises the changed behavior.
2. Confirm its exit status and inspect failures/skips rather than relying on a success label.
3. Run the applicable repository-defined suites and static/build gates discovered by `implement`.
4. Scope mutating commands and environment teardown to owned files and resources.
5. If a required runner, service, network path, or dependency is unavailable, report the gate as
   unexecuted or blocked. Do not silently replace it with a weaker tool.

When comparing a pre-existing failure baseline, use an immutable reference or a separate disposable
worktree. Do not stash or checkout the active shared worktree to manufacture a clean baseline.

## Report evidence

For each executed check record behavior covered, command source, exact command, working directory,
environment or seed, start/end or attempt window when relevant, exit status, pass/fail/skip counts,
and material output. Separate newly observed failures from known baseline failures only when both
were measured under comparable conditions.

List untested paths, skipped checks, unavailable capabilities, nondeterminism, and resource cleanup
limitations. Bound every conclusion to the revision, environment, data, attempts, and assertions
actually exercised.

## Maintenance triggers

Re-evaluate this skill when the repository changes its test entry points, a flaky or leaked-resource
incident escapes the lifecycle rules, an official tool contract changes, or paired fixtures show an
execution mechanism that catches more target failures at acceptable cost.
