# Falsifiable Architecture Decision Record

Load this reference only when a material choice needs a durable decision record.

# ADR-{id}: {decision}

## Status and ownership

- Status: proposed | accepted | superseded | rejected
- Decision owner:
- Date:
- Supersedes:
- Review events:

## Context and decision scope

State the desired outcome, affected consumers, current behavior, hard constraints, non-functional
requirements, operational blast radius, and why this decision is costly to reverse. Link repository
evidence instead of reproducing it.

## Evidence record

### Verified observations

For each material observation, cite the file, command, trace, measurement, or primary source and
state its scope. Quantitative evidence includes unit, population, time window, source, and method.

### Assumptions and unknowns

For each assumption or unknown, state its decision impact and the cheapest observation that would
resolve it. Do not turn a missing measurement into a score.

## Alternatives

Include the status quo and only viable alternatives.

### {alternative}

- Strongest case for it:
- Constraint fit:
- Failure and operating consequences:
- Migration, replacement, and deletion cost:
- Evidence gaps:

## Decision and trade-off

State the selected alternative, why its evidence outweighs the strongest objection, what cost is
accepted, and which stakeholder or system bears that cost. Preserve dissent or unresolved evidence
that could change the decision.

## Transition and rollback

- Incremental stages and owner:
- Compatibility strategy for data and consumers:
- Observable checkpoint after each stage:
- Rollback trigger and recoverable state:
- Temporary path deletion condition:

Do not use dual writes or backfills without declaring conflict resolution, reconciliation, and the
authority of each data copy.

## Validation and falsification

- Acceptance checks:
- Guardrail:
- Failure-path check:
- Result that falsifies this decision:
- Event that triggers reconsideration:

A validation command proves only the cases and environment it exercised. Record untested risks as
residual risk, not as passing evidence.

## Consequences

List positive consequences, accepted costs, residual risks, and follow-up ownership. Do not duplicate
the code-review verdict or severity taxonomy.
