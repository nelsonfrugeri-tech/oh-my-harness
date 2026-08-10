# Independent Evidence Review Rubric

Review the claims and decision record without modifying the implementation. Scale the review to the
decision's impact; trivial and easily reversible choices do not need ceremony.

## Checks

1. **Traceability** — Can every material factual and quantitative claim be traced to an inspectable
   source, exact command, or reproducible derivation?
2. **Scope** — Does each claim stay within the observed revision, environment, population, and time
   window?
3. **Classification** — Are inference, hypothesis, estimate, unknown, and decision distinguished
   from verified fact?
4. **Falsifiability** — Does each causal or predictive hypothesis name an observation that could
   disprove it?
5. **Alternatives** — Were viable alternatives and the status quo compared under the same criteria?
6. **Decision quality** — Are reversibility, blast radius, cost of delay, and cost of error explicit?
7. **Critical collaboration** — Does criticism identify evidence and risk, steelman the proposal,
   offer an alternative, and state what would change the conclusion?
8. **Validation** — Are success, guardrail, rollback, and follow-up observations defined before the
   result is known?

## Finding format

```markdown
[SEVERITY] Claim or decision at risk

Status: {unsupported | overstated | stale | non-falsifiable | decision gap}
Evidence inspected: {source or exact observation}
Why it matters: {decision impact}
Smallest correction: {relabel, measure, test, narrow scope, or add alternative}
What would resolve it: {specific evidence}
```

Approve when no material claim is overstated and the remaining uncertainty is explicit and
proportionate to the decision. Do not demand extra research that cannot plausibly change the choice.
