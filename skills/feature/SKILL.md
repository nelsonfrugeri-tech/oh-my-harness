---
name: feature
description: >-
  Orchestrates an end-to-end feature request by resolving material scope, preserving resumable
  state, handing bounded implementation to implement and test, and coordinating explicit external
  handoffs. Use when the user asks to build a feature across multiple phases or sessions. Do not use
  for a single local edit, automatic QA/SRE certification, or an author-issued review verdict.
metadata:
  type: workflow
  version: 3.0.0
  origin: native
  last_verified: 2026-09-06
---

# Feature

Coordinate feature state and handoffs without duplicating implementation, testing, product,
operations, or review skills.

## Guard the boundary

- Apply `evidence` to material claims and decisions.
- Delegate repository change execution to `implement`; it invokes `test` where verification design
  is material and produces the author self-check.
- Use product, architecture, AI, QA, SRE, security, or independent review capabilities only when the
  feature's scope and risk require them. Their absence does not authorize this workflow to invent
  their verdicts.
- Do not create planning directories, refinement drafts, validation reports, or workflow-state files
  in the product repository unless the user or repository explicitly defines them as versioned
  product artifacts. Keep temporary state in the harness scratch space.
- Do not create an issue, branch, commit, pull request, deployment, or other external side effect
  unless the user requested that outcome and the active capability is authorized.

## Keep resumable state

Maintain one compact feature record outside the product tree unless the repository defines an
authoritative equivalent:

- feature identifier and requested outcome;
- acceptance criteria and explicit non-goals;
- verified evidence, hypotheses, unknowns, and decisions;
- repository, revision, worktree, and authority boundary;
- completed phases with evidence locators;
- external side-effect identifiers such as issue, branch, or pull request;
- current phase, blocker, and next safe action.

On resume, inspect the repository and every recorded external identifier. Reuse a completed phase
only when its artifact and preconditions still hold. Verify before retrying any side effect so issue,
branch, commit, or pull-request creation remains idempotent.

## Orchestrate adaptively

```text
DISCOVER_EXISTING_STATE
  -> CLARIFY_MATERIAL_SCOPE
  -> DEFINE_EXECUTION_HANDOFF
  -> IMPLEMENT_AND_TEST
  -> COLLECT_EXPLICIT_HANDOFFS
  -> REPORT_OR_RESUME
```

### DISCOVER_EXISTING_STATE

Resolve the current feature record, repository instructions, worktree state, related issue or design
artifact, existing branch/PR identifiers, and completed implementation evidence. Treat historical
records as leads and revalidate mutable state.

### CLARIFY_MATERIAL_SCOPE

Derive observable acceptance criteria and non-goals from the request and repository context. Ask one
focused question only when an unresolved product or contract choice would materially change the
implementation. Do not force a refinement ceremony, document template, fixed question count, or
user approval checkpoint for facts already established.

If a material decision needs architecture, product, AI, security, or evidence review, make a bounded
handoff with the question, known facts, alternatives, and required output. Preserve returned
uncertainty; a specialist response is evidence for its scope, not automatic implementation authority.

### DEFINE_EXECUTION_HANDOFF

Pass `implement` a self-contained task containing the requested outcome, acceptance criteria,
non-goals, relevant artifacts, repository and authority boundary, known risks, and required external
handoffs. Select `feature` mode plus any justified modifiers such as migration, generated, or async.

### IMPLEMENT_AND_TEST

Let `implement` own discovery, red-capable observation, changes, focused and broad gates, author
self-check, and execution report. Do not restate its procedure here and do not mark implementation
complete when its status is `partially-completed`, `blocked`, or `unable-to-reproduce`.

There is no fixed iteration count. Repeat a bounded implementation step only while new evidence
identifies an in-scope correction, the next attempt is safe, and a stop condition remains explicit.
Stop on a material decision, unavailable authority, repeated unchanged failure, or user-defined
budget rather than inventing a universal retry limit.

### COLLECT_EXPLICIT_HANDOFFS

Request only the independent checks required by the task or repository. QA, SRE, security, product,
and independent review each own their own evidence and verdict. Keep actor identity and execution
evidence distinct from the author. The author self-check can prepare context but can never become a
merge recommendation.

If independent review is required, hand off the task and acceptance criteria, diff/revision,
decisions, focused and broad command evidence, limitations, and unresolved risks to the review
capability. [Review](../review/SKILL.md) defines that contract; the
[agent routing manifest](../../agents/routing.json) defines routing and role separation.

### REPORT_OR_RESUME

Return the feature status, completed phases and evidence, changed files, implementation status,
explicit independent handoffs and their real outcomes, blockers, residual risk, external side-effect
identifiers, and next safe action. Do not fabricate missing validator, reviewer, CI, deployment, or
release results.

Persist an updated resumable record only in the approved harness or project-defined location. A
conversation summary is sufficient when no durable state capability is configured; do not pollute
the product repository to compensate.

## Terminal states

- `completed`: acceptance criteria are implemented, applicable gates passed, and every explicitly
  required independent handoff returned its own satisfactory outcome.
- `partially-completed`: useful implementation exists but named gates or handoffs remain.
- `blocked`: a material decision, capability, authority, or dependency prevents safe progress.
- `cancelled`: the user ended the workflow; preserve already completed evidence and side-effect IDs.

## Maintenance triggers

Re-evaluate this workflow when resume duplicates an external action, product scratch artifacts enter
a repository, orchestration implicitly manufactures a specialist verdict, or agent routing changes
the review and agent-routing handoff contracts.
