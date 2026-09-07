# Non-Code Evidence Audit

Use this adapter for claims, reports, research, architecture decisions, benchmarks, and other
non-code artifacts. It is separate from code review: do not invent a merge base, file location,
Standards/Spec axis, or merge recommendation.

Apply the `evidence` claim taxonomy and independent review rubric. For each material claim, inspect
its source, revision or date, scope, method, uncertainty, and whether it can support the action being
proposed. Preserve contradictory sources and unavailable evidence instead of averaging or filling
the gap.

Use this finding shape when a defect is actionable:

```markdown
[<SEVERITY>] <claim or decision at risk>

**Locator:** <claim ID, section, source, or decision record>
**Status:** <unsupported | overstated | stale | non-falsifiable | decision-gap>
**Evidence inspected:** <source or exact observation>
**Why it matters:** <decision impact>
**Smallest correction:** <relabel, measure, test, narrow scope, or add alternative>
**What would resolve it:** <specific evidence>
```

Finish with exactly one evidence verdict:

- `approve` when no material claim exceeds its support;
- `approve-with-explicit-uncertainty` when the decision remains proportionate and reversible despite
  named uncertainty;
- `block-pending-evidence` when missing or invalid evidence controls a material, hard-to-reverse
  decision.

List inspected evidence, unresolved uncertainty, and the observation that would change the verdict.
Do not let a presentation-quality judgment suppress a factuality or provenance finding.
