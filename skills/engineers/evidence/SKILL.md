---
name: evidence
description: Apply evidence-driven reasoning to software engineering claims and decisions. Use for feature design, bug diagnosis, root-cause analysis, architecture, prioritization, implementation, review, delivery, operations, metrics, estimates, benchmarks, and trade-offs whenever facts must be separated from hypotheses or a material choice needs defensible evidence.
---

# Evidence-driven Software Engineering

Make software claims traceable and decisions testable without blocking safe progress when evidence
is incomplete. Treat the global software-evidence contract as binding.

## Apply the workflow

1. **Frame the claim or decision.** Define its scope, affected population, time window, and impact.
2. **Inventory the current record.** Separate verified facts, derived results, inferences,
   hypotheses, estimates, unknowns, and decisions.
3. **Inspect the strongest available evidence.** Prefer direct repository observations, executed
   tests, telemetry, reproducible commands, and versioned primary sources.
4. **Check provenance and scope.** Reject or relabel claims that exceed what the evidence proves.
5. **Reduce decision-relevant uncertainty.** Select the cheapest observation that distinguishes
   competing hypotheses or materially changes the trade-off.
6. **Decide proportionately.** Compare alternatives, reversibility, blast radius, cost of delay,
   and cost of error. Weak evidence calls for smaller, observable, reversible steps.
7. **Pre-register validation.** Define success, guardrail, falsification, rollback, and review
   conditions before observing the result.
8. **Communicate status.** Cite evidence near each material claim and label what remains uncertain.

## Preserve useful uncertainty

Do not manufacture certainty to make an answer look complete. A safe hypothesis can support an
experiment or reversible implementation when it includes a falsifiable prediction. An estimate can
support planning when its assumptions and uncertainty are visible. An unknown becomes actionable
when its decision impact and next observation are stated.

Do not claim root cause from correlation, a fixed bug from one passing test, production health from
configuration, or current truth from session history. Narrow the statement or obtain the missing
observation.

## Challenge decisions collaboratively

For a material proposal, identify the strongest evidence-backed risk, present the strongest
reasonable case in its favor, offer a viable alternative, and state what evidence would change the
recommendation. Request an independent `evidence-reviewer` when impact, irreversibility, or
uncertainty makes self-review insufficient.

Treat a decision as material when it can affect production users, security, privacy, data integrity,
significant spend, multiple teams, or a difficult rollback, or when an unsupported metric or causal
claim controls the outcome. Routine reversible choices do not require independent review.

## Load the relevant reference

- Use [claim-taxonomy.md](references/claim-taxonomy.md) to classify claims and validate provenance.
- Use [decision-protocol.md](references/decision-protocol.md) for material trade-offs and hotfix
  decisions.
- Use [review-rubric.md](references/review-rubric.md) for independent evidence review.
