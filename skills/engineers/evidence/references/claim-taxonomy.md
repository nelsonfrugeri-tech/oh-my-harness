# Claim Taxonomy and Provenance

Use the narrowest status the available evidence supports. A label is useful only when a reader can
inspect the supporting record and reproduce the reasoning.

## Status tests

| Status | Required support | Common failure |
| --- | --- | --- |
| Verified fact | Direct observation, source, scope, and observation time | Generalizing beyond the observed scope |
| Derived result | Cited inputs, formula or procedure, and reproducible output | Hiding assumptions in arithmetic |
| Inference | Cited facts plus the reasoning that connects them | Calling correlation a cause |
| Hypothesis | Falsifiable prediction and a discriminating test | Writing an unfalsifiable explanation |
| Estimate | Assumptions, range or error model, and intended use | Reporting a point value as measured |
| Unknown | The missing information and its decision impact | Silently filling the gap |
| Decision | Alternatives, criteria, evidence, owner, and validation plan | Presenting a preference as a fact |

## Quantitative provenance

For every material number, record:

- metric name and unit;
- population or denominator;
- time window and observation time;
- source revision, query, command, dashboard, or primary document;
- collection and calculation method;
- exclusions, assumptions, and known limitations.

Do not transform ordinal labels such as low, medium, and high into numeric probabilities. Use a
numeric confidence only when a calibration procedure maps that value to observed outcomes.

## Evidence semantics

- A file read supports claims about the inspected content and revision.
- A search count supports the exact query, included paths, and exclusions.
- A benchmark supports its hardware, dataset, configuration, warm-up, and repetitions.
- Telemetry supports its instrumented population and window, subject to sampling and data quality.
- Documentation supports the documented contract at its cited version, not runtime health.
- A transcript supports what was said. Revalidate any claim that may have become stale.

Prefer primary sources for behavior and specifications. Use secondary sources to discover primary
evidence or to compare interpretations, not to erase a primary-source conflict.

A premise supplied by a user or stakeholder is direct evidence that the premise was reported, not
that its underlying software claim is true. Until corroborated, classify the underlying statement
as a hypothesis, estimate, or unknown according to its form, and preserve the reporter and time as
provenance. Do not demand revalidation when the premise is explicitly declared as an assumption for
a hypothetical exercise.

A quantitative prediction can contain both an estimate and a hypothesis. Use **Hypothesis** as the
primary status when the statement predicts a relationship or outcome to be tested; record the
numeric value and its assumptions as the estimate inside that hypothesis. Use **Estimate** alone
for an approximate planning quantity that does not assert a causal or predictive relationship.
