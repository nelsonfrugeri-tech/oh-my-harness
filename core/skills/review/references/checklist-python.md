# Python Review Risks

Load this reference only for Python changes and only after discovering repository rules and
configured tooling. It highlights semantic risks that syntax, formatting, or generic lint results
may not decide.

## Boundary and state risks

- Check whether sync calls block an async path, and whether cancellation and cleanup preserve the
  public contract.
- Trace ownership of files, connections, locks, generators, tasks, and context managers across
  success and exception paths.
- Distinguish `None`, missing keys, empty collections, false values, and exceptions according to the
  local API contract.
- Inspect mutable defaults, shared class state, caches, and fixtures for state leaked across calls or
  tests.
- At typed boundaries, verify runtime validation separately from type annotations. A type checker
  does not validate untrusted runtime input.

## Correctness and compatibility risks

- Inspect exception translation and `raise ... from ...`; broad catches are findings only when they
  hide an error, violate the contract, or make recovery unsafe.
- Check iterator/generator exhaustion, lazy side effects, ordering assumptions, timezone handling,
  decimal precision, and equality/hash contracts when touched by the diff.
- Verify serialization and schema changes against existing consumers and stored data.
- Treat framework and Python-version behavior as volatile: consult the project's pinned version and
  current official documentation when the result depends on it.

## Verification

Use the repository's existing environment and project-native check commands in read-only or check
mode. Never install `mypy`, `ruff`, `pytest`, a security scanner, or another tool during review just
because this reference names a risk. Classify findings by observed impact, not by a universal
coverage, complexity, function-length, or typing threshold.
