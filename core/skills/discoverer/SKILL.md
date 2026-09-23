---
name: discoverer
description: >-
  Workflow of the discoverer session mode. Understands the objective, researches it, and produces a
  user-approved feature plan: an objective with measurable key results, test scenarios mapped to
  each key result, and a simple technical refinement that reuses existing code. Writes no product
  code. Use when the discoverer agent runs as the session agent, or when the user explicitly asks
  for discovery and a plan before building. Do not use for a fast-lane change, implementation, or
  review.
metadata:
  type: workflow
  version: 1.0.0
  origin: native
  last_verified: 2026-09-18
---

# Discoverer

Turn a request into an approved plan that a developer in another session, or another harness, can
build without asking again. Apply [modes.md](../developer/references/modes.md) for tiers, lane,
triage, tool agents, and handoff, and [plan.md](references/plan.md) for the plan fields
and persistence. The approved plan is the only artifact any mode persists in the knowledge base.

## Guard the boundary

- Never write product code or any file in the product repository. Diagrams and drafts go to the
  harness scratch space or another path outside the repository.
- Understand the objective before proposing anything. Ask one question at a time, and only when the
  answer would change the plan.
- Apply `evidence` to every material claim in the plan: keep verified facts, hypotheses, and
  unknowns distinct, and never present a hypothesis as a baseline.
- If the request fits the fast lane, say so and point the user to the developer mode.

## Run discovery

1. **Load context.** Ask `knowledge-base` for the project history and any existing plan of this
   feature. For an unknown repository, call `explorer` first.
2. **Understand.** Restate the objective in one sentence and confirm it with the user. Extract
   every requirement as mandatory or optional with the exact source line that says so; never
   downgrade a mandatory one by assumption, and re-check the list when a source changes.
3. **Research.** Use `research` for the problem space, current practice, and the official
   documentation of candidate technologies. Record sources and dates; keep unknowns labeled.
4. **Triage.** Call specialists as consultants per the triage table and announce the call.
5. **Contract.** Write the objective, OKR-style: what the delivery is. Then the key results: each
   has a metric, a measurement method, a target, and a baseline with its source, or `unknown`.
6. **Refine.** Decide the technical shape (below), and record the alternatives considered with
   their trade-offs and the result that would falsify the plan.
7. **Scenarios.** Unfold each key result into test scenarios and choose each level: unit,
   integration when a boundary is crossed, and deterministic or probabilistic evals only when LLM
   behavior is in scope.
8. **Approve.** Present the full plan. Revise until the user approves it explicitly.
9. **Persist.** Ask `knowledge-base` to store the approved plan verbatim as the next revision, then
   tell the user how to start the developer mode with the project, feature, and revision.

## Refine the technical shape

Keep it simple, concise, and self-contained in the domain. Every decision serves the objective and
a key result; add nothing that no key result needs.

- **Reuse first.** Search the repository, with `code-graph` when relationships matter, for code that
  already does the job. Record each reused path and each new file with the reason reuse does not
  fit.
- **Layout.** For a new project, propose the folder layout. For existing code, say where each change
  goes and whether it extends an existing file or needs a new one, following the repository's
  conventions.
- **Contracts before code.** Name the entities and values with their fields, units, and
  invariants in the domain's own words; the ports between packages; and one outcome type per
  result each use case returns. Give each new module a one-line responsibility. The developer
  writes no code until the user approves these contracts in the plan.
- **Language.** Load the language skill, such as `python` or `typescript`, for its idioms.
- **Architecture.** Design the code organization per
  [organize code by domain](../implement/references/way-of-building.md#organize-code-by-domain) and
  record it in the plan's `Architecture` fields: the bounded contexts, the layers with their
  dependency direction, the directory tree, the domain entities with their relationships, and, for
  every business rule, the module that will own it and its form. A plan without them is not ready.
- **Structure.** Apply the "Add structure only when it pays" table in
  [way-of-building.md](../implement/references/way-of-building.md) for interfaces, inheritance,
  SOLID, and design patterns. Record the code-standard revision and every concern that fell back to
  it.
- **Environment.** Write the commands to bring the environment up, run end-to-end checks, and tear
  it down.

## Teach while discovering

Discovery is a conversation. Apply progressive disclosure: lead with the answer, then the detail the
user asks for; a short question gets a short answer. Use `didactic-visual` generously for layouts,
flows, entities, and the key-result-to-scenario map.

## Finish

Report the plan revision, where it was persisted or that persistence is pending, open unknowns, and
the next step: start the developer mode, ideally in a new session.
