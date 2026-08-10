# Evidence-driven Decision Protocol

Use this protocol when a software decision has meaningful user impact, operational risk,
irreversibility, or non-trivial cost.

## 1. Frame the decision

Write the decision, the deadline, the affected system and population, and the cost of delay. List
constraints separately from preferences.

## 2. Build the evidence record

Capture:

```yaml
verified_facts: []
derived_results: []
inferences: []
hypotheses: []
estimates: []
unknowns: []
alternatives: []
decision_criteria: []
```

Every verified fact, derived result, and inference links to inspectable evidence; without that
support, relabel it. Hypotheses and estimates cite any available evidence and explicitly record
when none exists. Unknowns name the missing evidence and its decision impact. Keep contradictory
evidence rather than averaging it away.

## 3. Choose the cheapest decisive observation

Rank possible investigations by decision value, cost, and latency. Prefer a reproduction, targeted
test, small measurement, or reversible experiment that distinguishes competing hypotheses. Stop
collecting evidence when another observation is unlikely to change the choice enough to justify its
cost.

## 4. Compare alternatives

For each viable alternative, state expected benefit, failure mode, reversibility, implementation
cost, and supporting evidence. Do not fabricate scores. A weighted matrix is valid only when its
weights and scores have defined evidence or are clearly labeled stakeholder judgments.

Treat the presented option set as a claim, not a boundary. Check the status quo, staged or reversible
steps, and combinations of options before accepting a binary choice.

## 5. Decide and pre-register validation

Record:

- the selected alternative and owner;
- the evidence and criteria that controlled the choice;
- rejected alternatives and material trade-offs;
- leading and guardrail metrics with provenance requirements;
- a result that would falsify the chosen assumptions;
- rollback or review conditions and the next observation time.

When evidence is weak and failure is expensive, reduce blast radius, add instrumentation, or choose
a reversible step. For an urgent hotfix, distinguish the immediate mitigation from the durable fix
and record the evidence required before claiming root cause.
