---
name: manage
description: >-
  Turn a product or platform problem into a decision-ready feature contract with evidenced outcomes,
  explicit scope, relevant constraints, prioritization rationale, and observable acceptance. Use for
  product refinement, backlog or sequencing decisions, acceptance criteria, and product handoff to
  feature. Do not use for generic product-management teaching, technical design, implementation
  planning, test strategy, or release execution.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Product Decision

Produce the smallest product contract that lets downstream work proceed without inventing user
needs, priority, scope, or acceptance.

## Guard the boundary

- Apply `evidence` to material claims and decisions. A stakeholder statement establishes that
  person's judgment or request; it does not by itself establish user behavior, impact, effort, or
  organizational consensus.
- For a small, well-specified change, confirm the outcome and observable acceptance directly. Do not
  force a user story, PRD, prioritization framework, roadmap, or refinement ceremony.
- Use this capability when a product choice, outcome, scope boundary, sequencing decision, or
  acceptance contract is missing. Abstain for generic concept explanations and purely technical
  choices inside an already accepted contract.
- Own product intent and acceptance only. Route architecture to `design`, implementation and test
  execution to `feature` or `implement`, independent verification to `review`, and release or
  operational execution to their owning capabilities.
- Ask one focused question only when its answer can change scope, safety, architecture, acceptance,
  or sequencing. Otherwise preserve the issue as an assumption or unknown and continue with the
  next reversible decision.

## Resolve inputs and authority

Start with the user request, repository-defined product artifacts, observed behavior, and existing
decisions. Separate:

- **evidence:** observed user behavior, support records, telemetry, experiments, contractual or
  regulatory constraints, and repository facts, each bounded by its actual source and scope;
- **stakeholder judgment:** desired outcome, priority, risk tolerance, policy choice, or trade-off,
  attributed to its speaker or decision owner;
- **engineering input:** feasibility, dependencies, operational risk, reversibility, and effort
  estimates with assumptions;
- **unknowns and hypotheses:** missing evidence and falsifiable beliefs that could change the choice.

For material quantities, retain metric and unit, population or denominator, observation window,
source, and collection or derivation method. Never create a baseline, target, reach, impact, effort,
confidence, cost, or date to complete a template.

Resolve current public facts through `research` using primary sources. Resolve project facts from the
repository, organizational policy and curated decisions from the knowledge base, and prior discussion
from session memory; revalidate mutable facts before relying on them. If a required source or
capability is unavailable, mark the affected claim unknown and state the degraded mode rather than
substituting generic practice.

## Frame the product decision

1. **Problem and user.** State who is affected, what observable problem or opportunity exists, and
   what evidence establishes it. Keep a requested solution separate from the problem it proposes to
   solve.
2. **Outcome.** Define the change in user or system behavior sought and the evidence that would show
   progress. If no defensible success signal exists, record the measurement decision as unresolved.
3. **Constraints.** Identify genuine limits on the solution: contracts, policy, safety, privacy,
   compatibility, budget, operations, or other fixed boundaries. Do not promote preferences to hard
   constraints without the decision owner's judgment.
4. **Scope.** State the smallest coherent in-scope outcome and explicit non-goals. Acceptance criteria
   confirm that scope; they must not silently add adjacent features.
5. **Assumptions and unknowns.** Name each item that could alter the decision, its impact, and the
   cheapest useful observation. Give a hypothesis a falsifier, not a confidence adjective.
6. **Decision.** Attribute the choice and its status to the actual owner. Record alternatives only
   when a real choice exists, including the status quo or a smaller reversible step when relevant.

## Prioritize without manufactured precision

Define criteria before comparing alternatives. Choose only criteria that matter to the stated
outcome, such as expected outcome contribution, urgency or cost of delay, hard dependencies, risk,
reversibility, evidence strength, and engineering investment.

- Compare qualitatively by default. Numeric scoring is valid only when inputs are measured or
  explicitly attributed stakeholder judgments, scales are defined and comparable, and the
  calculation cannot hide a hard constraint or unresolved conflict.
- Obtain effort and feasibility from responsible engineering input. Preserve ranges, assumptions,
  and unknowns; never invent estimates or convert uncertainty into dates.
- Test sensitivity by varying uncertain inputs or stakeholder weights across their defensible range.
  If the preferred option changes, report the ranking as conditional and identify the deciding
  evidence or judgment.
- Do not average conflicting evidence or stakeholder priorities into apparent consensus. Name the
  conflict and the owner who must decide.
- Use `Now / Next / Later` only when communicating sequence under different confidence levels is
  useful. It expresses intent and dependencies, not promised dates. Use INVEST or a user-story form
  only when it exposes a concrete slicing or handoff problem; neither is a completion checklist.

The output is a decision with rationale, not a RICE, MoSCoW, impact-effort, or other framework score.
A framework may be used when the organization already defines its inputs and decision semantics, but
the framework never supplies missing evidence or authority.

## Write observable acceptance

Acceptance criteria describe externally observable product behavior, including material failure
paths and boundaries. Cover only behavior relevant to the feature:

- initiating actor, precondition, action, and observable result;
- invalid, unauthorized, unavailable, duplicate, cancelled, or partial outcomes when they affect the
  contract;
- state retained or changed after failure;
- relevant limits and compatibility behavior;
- evidence or signal that product acceptance can inspect.

Use `Given / When / Then` when preconditions and state transitions would otherwise be ambiguous.
Plain statements are better for simple invariants. Do not prescribe classes, endpoints, database
shape, test layers, or deployment mechanics unless one is an actual product constraint.

Add non-functional requirements only when they materially constrain acceptance or design. State the
user journey or protected asset, operating condition, metric, threshold or policy source, and
verification signal for relevant security, privacy, accessibility, latency, capacity, availability,
compatibility, data retention, or operability requirements. If the threshold is undecided, keep it
unknown instead of choosing a conventional value.

Keep these contracts distinct:

| Contract | Owner | Product handoff content |
| --- | --- | --- |
| Product acceptance | Product decision owner | Observable outcome, boundary, and failure behavior |
| Technical design | Architecture or engineering | Constraints and unresolved questions only |
| Implementation plan | `feature` / `implement` | Requested outcome and authority boundary |
| Test strategy | Test or implementation capability | Behaviors and required evidence, not test structure |
| Release verification | Operations or release owner | Product success signal and applicable guardrails |

## Control scope and respond to new evidence

Treat a newly requested behavior as a scope change unless it is necessary to satisfy an existing
criterion. Record its outcome contribution, dependency and risk impact, displaced work, and decision
owner; do not relabel it as acceptance to bypass prioritization.

If implementation, testing, or operations falsifies an assumption, pause only the affected decision.
Record the new evidence and its scope, identify which outcome, constraint, criterion, or priority is
invalidated, and return the smallest decision to the product owner. The owner may preserve scope,
revise acceptance, split or defer work, or stop it. Downstream agents must not silently choose a new
product contract.

## Produce the handoff

Scale the artifact to the decision. A tiny change may need only the outcome, observable acceptance,
and one material boundary. A material feature contract includes:

- problem, affected user, and evidence with provenance;
- desired outcome and success evidence;
- scope and non-goals;
- constraints and relevant non-functional requirements;
- assumptions, unknowns, falsifiers, risks, and dependencies;
- alternatives, prioritization criteria, decision status, rationale, and owner;
- observable acceptance criteria with material failure paths;
- product validation signal and release guardrails, when known;
- a compact log of material decisions and superseding evidence.

Hand this contract to `feature` as intent. Do not duplicate its repository discovery, resumable state,
technical design, implementation, testing, review, or release orchestration. Mark omitted fields as
not applicable only when that distinction matters; do not fill every heading for appearance.

## Verify and stop

Before handoff, verify that downstream agents can act without inventing a product requirement, every
quantity has required provenance, stakeholder judgments are attributed, acceptance covers the
important failure behavior, and no criterion expands the stated scope. Stop when remaining unknowns
cannot change the next reversible step; otherwise return the unresolved decision and its owner.

Re-evaluate this skill when product facts are stored as timeless doctrine, priority arithmetic hides
uncertainty, small requests accumulate ceremony, acceptance repeatedly causes scope growth, or the
`feature` input contract changes. Refresh volatile and organizational facts at use time rather than
on a calendar.
