---
name: python
description: >-
  Inspect and change a Python project when compatibility, typed data boundaries, imports,
  async behavior, resource lifetime, or exception semantics affect correctness. Use for concrete
  Python implementation or diagnosis; do not load for generic programming advice, framework
  selection, or tasks that merely mention Python without changing Python artifacts.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Python project engineering

Produce a project-compatible change whose boundary, lifetime, and failure behavior is verified by
the repository's own tools.

## Discover before deciding

Inspect the nearest project files before suggesting syntax or commands. Resolve the supported Python
version, package/import layout, dependency workflow, configured formatter/linter/type checker/test
runner, generated artifacts, and conventions in adjacent code. Project configuration and executable
behavior outrank this skill; never introduce a preferred tool, framework, syntax level, or layout by
default.

Read [project and boundary checks](references/project-boundaries.md) when signals conflict or the
change crosses data, async, resource, error, generated-code, or package boundaries.

## Protect failure-prone seams

- Validate untrusted values at the first owned runtime boundary. Annotations do not validate JSON,
  environment variables, database rows, messages, or deserialized objects.
- Keep precise types at public seams. Do not widen to `Any`, untyped containers, or unchecked casts
  merely to silence a diagnostic.
- Give mutable fields and parameters independent state.
- In async code, identify blocking calls, cancellation points, spawned-task ownership, and
  concurrency limits.
- Acquire and release files, locks, clients, transactions, and streams in one visible lifetime;
  preserve the primary exception when cleanup also fails.
- Catch only errors this layer can recover from or translate, preserving causal context.
- Verify imports through the project's installed or deployed entry point, not only a convenient cwd.
- Edit generated artifacts only through the authoritative source and documented regeneration path.

## Verify and report

Implementation owns delivery sequencing and review owns finding severity. Run the discovered format,
lint, type-check, and test gates that cover the change. If a configured tool is unavailable, report
the exact missing command and unverified behavior instead of silently substituting another tool.

For version-sensitive syntax, checker behavior, packaging rules, or framework APIs, inspect current
official documentation for the detected version. Cite the source and inspection date when it affects
the result; if unavailable, preserve compatible local behavior or state the uncertainty.

Report project signals, seams checked, commands and outcomes, and remaining gaps. Stop at the
requested Python boundary rather than broadening the task into project-wide modernization.
