---
name: operate
description: >-
  Make bounded SRE decisions for incidents, operational changes, service-level objectives, error
  budgets, alerts, mitigation, and rollback. Use when production or shared-service impact drives an
  operational decision. Observability owns instrumentation mechanics; CI/CD owns pipeline
  implementation.
metadata:
  origin: native
  last-verified: 2026-09-07
  version: 2.0.0
---

# Operate

Restore or change service safely while preserving evidence, limiting blast radius, and separating
mitigation from verified root cause.

## Establish the operating record

For an incident or risky change, record:

- user-visible symptom, affected population, start time, and current scope;
- service journey and applicable SLI/SLO, including source and measurement window;
- timeline and recent changes;
- verified facts, hypotheses, unknowns, and current owner;
- action authority, exact targets, concurrent responders, and communication cadence;
- success, guardrail, rollback, and follow-up conditions.

Severity and response targets come from the organization's policy and observed impact. Do not invent
severity thresholds, paging cadences, staffing rules, or recovery-time promises.

## Follow the evidence ladder

Proceed through:

    symptom -> scope -> timeline -> recent change -> hypotheses
            -> discriminating observation -> reversible mitigation
            -> user-journey verification -> residual risk
            -> root-cause evidence -> durable follow-up

Prefer the cheapest observation that separates plausible causes. Absence of a symptom after a
mitigation proves recovery only for the observed population and window; it does not prove cause.
Keep contradictory evidence and update the timeline as actions occur.

During active impact, prefer a bounded, reversible mitigation with known recovery over a speculative
permanent fix. For data-writing systems, stop or isolate the smallest writer, preserve evidence,
verify read/write and consistency implications, and establish replay or reconciliation before
resuming.

## Control operational changes

Read [incident-change.md](references/incident-change.md) before executing a production or shared
mutation. Resolve the exact target and current state, preview when possible, estimate blast radius,
confirm ownership and authority, preserve a recovery path, then apply one coordinated change.
Never offer broad prune, wildcard deletion, recursive ownership change, force-kill, cache-wide flush,
or database-wide reset as a routine mitigation.

A rollback is a new operational change. Check artifact availability, schema and data compatibility,
traffic state, dependency compatibility, permissions, and whether rollback would discard writes.
When those preconditions fail, choose bounded forward recovery and say why.

## Define and use reliability objectives

Read [slo-error-budget.md](references/slo-error-budget.md) whenever calculating or changing an SLI,
SLO, error budget, burn rate, or alert threshold.

Start from a user journey and classify eligible events consistently. Preserve numerator,
denominator, unit, population, exact window, query/source revision, collection method, exclusions,
and missing-data behavior. Do not use infrastructure utilization as a substitute for user success.

Use symptom and error-budget alerts to trigger operational decisions. Supporting cause signals aid
diagnosis but do not independently establish user impact. Choose paging and ticket thresholds from
the service's objective window, response capacity, traffic distribution, and tested alert behavior;
do not copy universal numbers.

Observability supplies signal semantics and verifies the telemetry path. Operate owns the objective,
policy, alert action, incident decision, and residual risk.

## Close with bounded claims

Declare recovery only after the representative user journey and relevant guardrails recover for a
stated observation window. Declare root cause only when evidence supports the causal mechanism and
competing hypotheses have been addressed.

The handoff includes impact and timeline, evidence and unknowns, hypotheses tested, actions with
owners, verification window and queries, rollback or forward-recovery state, consumed error budget
with provenance, residual risk, and next review event. If telemetry, credentials, provider, or
network access is unavailable, state exactly which layer could not be verified.
