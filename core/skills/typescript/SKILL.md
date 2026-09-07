---
name: typescript
description: >-
  Inspect and change a TypeScript project when compiler/runtime configuration, external-data types,
  promises, module semantics, or server/client boundaries affect correctness. Use for concrete
  TypeScript implementation or diagnosis; do not load for generic JavaScript advice, framework
  selection, or tasks that merely mention TypeScript without changing TypeScript artifacts.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# TypeScript project engineering

Produce a runtime-correct change that respects the repository's compiler, module, framework, and
execution boundaries.

## Discover before deciding

Inspect the nearest package before proposing syntax, imports, or commands. Resolve the effective
compiler configuration, runtime/module loader, package manager and workspace, framework/build
pipeline, generated sources, and project-native gates. A root `tsconfig` may be extended, overridden,
or irrelevant to a nested package.

Read [project and runtime boundaries](references/project-boundaries.md) when the execution model is
unclear or the change crosses external data, async control, module interop, generated code, or a
server/client boundary.

## Protect type/runtime seams

- Treat external values as `unknown` until runtime validation or narrowing establishes the contract.
  Assertions, generic response parameters, and generated interfaces do not validate data.
- Preserve discriminants and exhaustive handling for closed unions; do not hide new states behind a
  permissive fallback.
- Await, return, deliberately supervise, or cancel every started operation. Preserve rejection cause
  and cleanup.
- Confirm imports against compiler options, package metadata, transforms, exports, and runtime loader.
  Type-check success alone does not prove runtime resolution.
- Keep secrets, privileged APIs, filesystem access, and trusted environment data server-side. Values
  crossing to client code become public and must satisfy framework serialization rules.
- Edit generated clients, route types, and build artifacts only through their authoritative source.

## Verify and report

Implementation owns sequencing and review owns finding severity. Run the package's discovered format,
lint, type-check, test, and relevant build/runtime command. In a non-strict project, protect the
changed seam without silently enabling project-wide flags.

Retrieve current official documentation when a decision depends on TypeScript, runtime, framework,
module-loader, or browser version behavior. Cite the detected version, source, and inspection date;
if unavailable, preserve local behavior or mark it unverified.

Report project signals, checks, commands, and runtime uncertainty. Stop at the requested package
boundary rather than turning a local change into a toolchain migration.
