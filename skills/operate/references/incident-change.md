# Incident and operational change contract

## Before mutation

- Name the incident or change owner and coordinate concurrent responders.
- Resolve the exact resource, environment, region, tenant, process, or data partition.
- Capture bounded current state and preserve evidence needed for later analysis.
- State the hypothesis or operational purpose and the observation that would support or falsify it.
- Preview the delta, dependencies, blast radius, and user journeys at risk.
- Confirm authority at the boundary required by active policy.
- Select one smallest reversible action.
- Record success, guardrail, abort, rollback, and observation-window conditions.

For data-writing changes, include consistency model, in-flight writes, backup or replay point,
reconciliation owner, and proof that recovery is possible. If these are unknown, isolate or pause the
smallest writer rather than deleting or rewriting data.

## During and after mutation

Record timestamps and observed results; do not run uncoordinated competing changes. Abort on a
pre-registered guardrail. Verify both the user journey and the internal state needed to sustain it.
If rollback is selected, re-check its preconditions immediately before execution.

After recovery, distinguish temporary mitigation, durable correction, and unverified causal theory.
Assign ownership and a removal signal to temporary mitigations. Close with residual risk, evidence
gaps, and the next observation or review event.
