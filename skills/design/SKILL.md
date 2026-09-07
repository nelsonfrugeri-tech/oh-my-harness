---
name: design
description: >-
  Produce or challenge a falsifiable software architecture decision from repository evidence,
  constraints, alternatives, boundary analysis, and a reversible migration. Use for material
  architecture choices, ADRs, decomposition, module seams, or costly-to-reverse structural change.
  Do not use merely to explain a pattern, implement a local change, design an API contract, or
  perform a security threat model.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Architecture Decision Design

Turn a material architecture choice into an inspectable decision whose assumptions, migration, and
failure conditions can be tested.

## Guard the boundary

- Do not create an ADR for a local, reversible implementation choice with no cross-boundary effect.
- If the request is generic concept recall, answer it without this workflow unless a decision is
  also required.
- Route API behavior and compatibility to `api-design`; route adversarial analysis to `security`.
- Supply domain observations to `review` when reviewing a change. Do not assign finding severity
  or issue a merge recommendation here.
- Resolve material ambiguity from repository evidence first. Ask one discriminating question only
  when different answers would change the decision.

## Resolve evidence

Inspect the repository before selecting a pattern. Prefer, in order:

1. deployed boundaries, dependency direction, public interfaces, data ownership, and call paths;
2. tests and consumers that reveal behavioral contracts;
3. version history, change clusters, incidents, and measured operational constraints;
4. project ADRs and current organizational knowledge with provenance.

Classify observed facts, hypotheses, assumptions, unknowns, and estimates through `evidence`. For protocol,
framework, vendor, or current standard behavior, use `research` against current primary sources;
record source, revision or inspection date, and limitation. If a required source is unavailable,
keep the claim unknown and choose a smaller reversible step.

## Analyze the decision

1. **Frame the outcome.** State the behavior or quality attribute that must change, affected
   consumers, non-functional constraints, operational blast radius, and why the choice is costly
   to reverse.
2. **Map the current system.** Identify deploy and data boundaries, ownership, dependency direction,
   public seams, failure propagation, and the smallest replaceable unit. Use a diagram only when it
   clarifies a relationship needed for the decision.
3. **Test module shape when relevant.** Inspect what callers must know, what behavior the module
   hides, where change spreads, and whether tests use the public seam. Apply the boundary probes in
   [module-boundaries.md](references/module-boundaries.md); do not infer quality from line counts.
4. **Build real alternatives.** Include the status quo and at least one viable alternative only
   when a material choice exists. Give the strongest evidence-backed case against the preferred
   option. Do not select a named pattern because its label matches the task.
5. **Choose proportionally.** Compare effects on the stated constraints, reversibility, deletion or
   replacement cost, data compatibility, observability, and operating burden. Do not invent scores,
   effort, traffic, cost, or probability.
6. **Design the transition.** Prefer an incremental path with compatibility windows, checkpoints,
   rollback triggers, ownership, and an explicit point at which temporary paths are removed.
7. **Pre-register validation.** Define observable acceptance checks, guardrails, a result that
   falsifies the decision, and events that require reconsideration.

## Produce the decision

Use [decision-record.md](references/decision-record.md) for a material decision. A concise response
is enough for exploratory work, but it must still distinguish evidence from assumptions and state
what observation would decide the open trade-off.

Do not silently convert a proposal into an accepted decision. Record the decision owner and status.
An accepted record is historical evidence; changing it creates a superseding record instead of
rewriting the prior context.

## Verify and stop

Before finishing, verify that:

- each alternative satisfies the hard constraints or is explicitly rejected for a cited reason;
- quantitative drivers include unit, population, window, source, and method;
- the migration preserves required data and consumer compatibility through rollback;
- checks exercise the public seam and at least one important failure mode;
- the falsifier could genuinely overturn the choice.

Stop when the decision is actionable and remaining unknowns cannot change the next reversible step.
Do not add diagrams, pattern catalogs, or speculative abstractions to make the artifact look complete.

## Provenance

The module-depth, seam, interface/test-surface, and deletion-test probes are adapted mechanisms from
Matt Pocock's `codebase-design` skill, revision
`3cca18b368ae95cdbdebbff572ccafa662551015`, MIT License, inspected 2026-09-07. OHM does not adopt
its vocabulary as a mandatory ontology; repository language and observed contracts take priority.
Re-evaluate the adaptation when the pinned upstream changes or package evals expose a regression.
