# Pipeline integrity checklist

## Trigger and trust

- Events and branch/path filters match the intended population.
- Untrusted code cannot inherit secrets or a privileged token.
- Job permissions are explicit and minimal.
- Concurrency prevents incompatible deployments from racing.
- Required jobs cannot be skipped or ignored by a permissive condition.

## Inputs and caches

- Third-party actions and executable images resolve to reviewed immutable revisions.
- Runtime and dependencies come from project constraints and lockfiles.
- A cache key includes every compatibility boundary that changes the cached bytes: platform,
  architecture when relevant, runtime/toolchain, dependency manager, and lockfile content.
- Restore prefixes cannot cross an incompatible boundary.
- A cold-cache run remains correct; cache hits affect speed, not semantics.

## Artifact and delivery

- Build output has an immutable digest and source/build provenance.
- Promotion reuses the same digest.
- Downloads verify identity before execution or deployment.
- Deploy scope, approval, state compatibility, health evidence, and observation window are explicit.
- Rollback has a reachable last-known-good artifact, state preconditions, authority, trigger, and
  verification path.
- Temporary artifacts and environments have retention and ownership.

Validate the actual provider schema and current action interface from official sources at execution
time; this checklist does not pin vendor syntax or versions.
