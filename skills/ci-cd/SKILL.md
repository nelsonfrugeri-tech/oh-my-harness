---
name: ci-cd
description: >-
  Design or modify continuous-integration and delivery pipelines using repository-native commands,
  least privilege, immutable inputs, compatible caches, traceable artifacts, promotion, and
  recoverable deployment. Use for pipeline configuration and release flow; not for local
  environment diagnosis, incident command, or application instrumentation.
metadata:
  origin: native
  last-verified: 2026-09-07
  version: 2.0.0
---

# CI/CD

Produce a structurally valid pipeline whose gates, artifacts, permissions, and rollback behavior can
be inspected before it changes an environment.

## Discover the delivery contract

1. Resolve repository instructions, workflow files, protected branches, deployment manifests,
   package manifests, lockfiles, and release runbooks.
2. Derive format, lint, typecheck, test, build, and packaging commands from project entry points.
   Preserve their arguments and working directories; do not replace them with ecosystem defaults.
3. Map the pipeline DAG, trust boundaries, changed-path rules, artifacts, environments, credentials,
   and failure propagation.
4. Retrieve current provider syntax or action inputs from official documentation only when the
   checked-in schema and pinned project configuration do not answer the question. Record the source
   and inspection date.

If the provider, credentials, network, or remote state is unavailable, validate what can be proven
locally and name the unverified remote behavior. Configuration presence is not execution evidence.

## Enforce pipeline integrity

Read [pipeline-integrity.md](references/pipeline-integrity.md) when changing a workflow.

Every required gate must fail closed. Conditional skips need an explicit scope and must not turn a
failed check green. Parallelize only independent jobs and order checks by measured feedback value,
not copied duration estimates.

For third-party execution, use an immutable artifact digest or full commit identifier that was
reviewed, or a documented trusted update mechanism that resolves and reviews immutable revisions.
Human-readable tags may be retained only as annotations. Pin language dependencies through the
project lockfile and preserve lockfile verification.

Grant the minimum permission per job. Untrusted pull-request code must not receive deployment
credentials, write tokens, protected environment access, or an execution path that evaluates
attacker-controlled text as code.

## Build, promote, and recover

Build once and identify the output by immutable digest. Attach source revision, build identity,
dependency/lock evidence, and required attestations. Promote the same digest between environments;
do not rebuild a nominally identical release.

Before deployment, define:

- exact environment and artifact digest;
- concurrency and serialization rules;
- database or state compatibility;
- pre-deploy checks and approval boundary;
- user-facing success and guardrail signals;
- rollback trigger, last-known-good artifact, authority, and rollback preconditions;
- forward-recovery path when rollback is unsafe.

A rollback command without state, schema, traffic, and dependency preconditions is not a rollback
plan. Preview mutations where the provider supports it, limit rollout blast radius, verify the
selected journey after deployment, and retain the prior recoverable state until the observation
window closes.

## Validate and hand off

Use provider-native parsers, schema validation, shell linting, and repository checks where available.
Validate cache behavior against a changed lockfile or toolchain, artifact download against its digest,
and deployment logic against a non-production or simulated target when authorized.

Report changed files, discovered native commands, DAG and permissions, immutable pins, cache
boundaries, artifact identity, deployment/rollback contract, local validation results, remote
unknowns, and residual risk. Never claim a deployment ran when only local validation ran.
