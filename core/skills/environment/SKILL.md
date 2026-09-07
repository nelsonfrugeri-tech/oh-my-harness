---
name: environment
description: >-
  Discover, diagnose, and safely operate a repository's local development environment. Use for
  runtime or dependency mismatches, local services, configuration-source problems, ports,
  containers, and reproducibility gaps. Do not use for CI delivery, production incidents, or
  telemetry design.
metadata:
  origin: native
  last-verified: 2026-09-07
  version: 2.0.0
---

# Environment

Make the local environment understandable and recoverable from repository evidence without exposing
secrets or assuming a particular toolchain.

## Establish scope before acting

1. Resolve the repository root, applicable instructions, requested service, and whether the target is
   the host, a container, a virtual environment, or another isolated runtime.
2. Inspect project-owned entry points before choosing commands: documented runbooks, task runners,
   package scripts, devcontainers, container manifests, runtime files, manifests, and lockfiles.
3. Compare declared constraints with read-only observations such as installed tool versions, service
   status, bound ports, and effective configuration names.
4. Treat a configured value as configuration evidence only. Readiness requires a dependency-aware
   probe; end-to-end health requires the user-facing path.
5. If competing environment interpretations remain and would change a mutation, ask one
   discriminating question.

Do not invent a universal Make, Docker, package-manager, port, or runtime command. Use the project's
native command when one exists; otherwise explain the smallest portable probe and its assumptions.

## Protect configuration and credentials

Inspect configuration precedence and key presence, not full values. Start from schemas, example files,
variable references, and secret-manager metadata. Never dump the process environment, print a
credential-bearing URL, expand a secret in a shell command, or copy a real secret into a diagnostic
artifact.

If resolving the issue requires reading a file likely to contain authentication material, stop at
the boundary required by the active authorization policy. Prefer a redacted application diagnostic
that reports source, key name, presence, parse status, and validation error without the value.

## Diagnose by layer

Record expected state, observed state, and evidence for each relevant layer:

- repository: selected runtime, lockfile, command, and configuration precedence;
- host: executable resolution, version, architecture, permissions, ports, and network reachability;
- isolation: container or virtual-environment identity, mounts, user, and dependency state;
- service: process state, readiness, dependency connectivity, migrations, and bounded logs;
- journey: one representative request or workflow when local side effects are understood.

Use the cheapest observation that distinguishes missing dependency, wrong configuration, host versus
container mismatch, stale state, and unavailable upstream. A registry or network failure is not
evidence that a package is missing or incompatible.

## Apply the safe lifecycle

Read [safe-lifecycle.md](references/safe-lifecycle.md) before starting, stopping, rebuilding,
resetting, deleting, changing ownership, or terminating a process.

Default to read-only inspection. A normal start or stop must use the repository-owned lifecycle
command and preserve data unless the user requested otherwise. Never make global prune, wildcard
deletion, recursive ownership change, force-kill, database-wide reset, or unbounded key/log listing a
routine recovery step.

## Verify and report

After a change, rerun the discriminating probe, then the project readiness check and the relevant
local journey. Report:

- scope and environment layer;
- project evidence and commands selected;
- observations with sensitive values redacted;
- action taken or proposed, including authorization and recovery boundary;
- what was verified, what remains unknown, and the next cheapest observation.

When tooling, credentials, registry, or network access is unavailable, preserve the exact failed
layer and continue with safe local evidence. Do not claim the environment is healthy from
configuration or process state alone.
