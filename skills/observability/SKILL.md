---
name: observability
description: >-
  Design and verify telemetry semantics and instrumentation health across logs, metrics, traces,
  propagation, cardinality, sampling, and privacy. Use for signal design or broken telemetry paths.
  Do not own incident command, SLO policy, deployment, or local environment lifecycle.
metadata:
  origin: native
  last-verified: 2026-09-07
  version: 2.0.0
---

# Observability

Produce telemetry that answers an operational question and prove that representative signals travel
from application behavior to a queryable backend without unsafe data capture.

## Start from the decision

Name the user journey, operational question, consumer, required latency or freshness, and action the
signal informs. Then choose the signal:

- metrics for bounded-dimension aggregates, rates, distributions, and alert inputs;
- traces for causal paths and cross-service latency;
- logs for discrete events and detailed bounded diagnosis;
- profiles only when code-path resource attribution is the actual question.

Operate owns the SLO and incident action. Observability implements and validates the measurements
needed for them. A dashboard without a decision or journey is not a deliverable.

## Discover before configuring

Inspect language or runtime constraints, lockfiles, existing telemetry bootstrap, semantic
conventions, collector or agent configuration, backend capabilities, privacy policy, and deployment
topology. Use the project's pinned SDK and schemas. For API syntax, semantic-convention status,
exporters, or vendor configuration that may change, consult current official documentation and
record source, version or revision, and inspection date.

Do not copy a universal SDK setup. Validate generated configuration with the exact pinned binary or
provider parser where available. If the backend, credentials, or network is unavailable, keep local
structural and emission evidence separate from unverified delivery.

## Specify signal semantics

For each signal define name, type, unit, event boundary, population, aggregation, required
attributes, optional attributes, missing-data meaning, temporality, retention consumer, and owner.
Align SLI signals with the good, bad, excluded, and total events defined by Operate.

Normalize route templates and bounded error classes. Never use raw URLs, query strings, user IDs,
request IDs, email addresses, arbitrary exception text, payloads, prompts, or database statements as
metric labels. Before adding dimensions, estimate the cross-product of possible values; reject an
unbounded or unknown dimension or move it to a redacted log or trace.

Default to an attribute allowlist. Classify and redact sensitive fields before export, constrain
baggage because it propagates across trust boundaries, and test that dropped data cannot reappear in
another signal or exporter. Route threat-model or authorization design to the security capability.

## Preserve context and rare failures

Define propagation across HTTP or RPC, queues, scheduled work, async tasks, threads, and process
boundaries that the journey crosses. Test parent or child linkage and log correlation at each
boundary; a valid local span does not prove end-to-end context.

Choose sampling from traffic, backend capacity, investigation needs, and rare-event risk. Record what
can be invisible. Verify that critical errors and low-frequency paths remain observable under the
actual policy; do not assume head or tail sampling captures them. Sampling must not alter metric
denominators silently.

## Prove instrumentation health

Read [telemetry-health.md](references/telemetry-health.md) for the end-to-end evidence ladder.
Configuration or SDK initialization proves neither emission nor backend availability.

Use a uniquely identifiable, non-sensitive test operation and verify its expected metric, trace, and
log relationships. Check instrumentation and collector self-telemetry for refused, dropped, queued,
retried, and failed exports. Compare signal timestamps and resource identity to detect stale or
misrouted data.

## Deliver a verifiable contract

Report the question and journey, signal specification, attribute or cardinality and privacy
decisions, propagation and sampling behavior, configuration validation, end-to-end evidence by
layer, self-telemetry health, missing layers, and rollback or removal plan.

Treat numeric claims as measured only when unit, population, window, source, and method are present.
If only local emission was observed, say so; do not claim backend ingestion or dashboard health.
