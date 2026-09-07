# Code Craft

Apply these constraints to changed code after reading the repository's own instructions, nearby
code, and configured gates. Project contracts override generic preferences unless they would make
the requested change unsafe or incorrect.

## Keep the design sufficient

- Implement the smallest design that satisfies the observed behavior and acceptance criteria.
- Keep related behavior together and split code when cohesion, ownership, testability, or change
  rate gives a concrete reason. Do not split by a universal line or symbol count.
- Keep the public surface no larger than current consumers require. A module may expose multiple
  related concepts when that is the cohesive project convention.
- Add an abstraction or pattern only when observed variation, duplication, coupling, or a required
  extension point justifies it. Conditional count alone does not require a pattern.
- Prefer guard clauses when they make edge cases and the happy path clearer; do not impose a fixed
  nesting limit or force early returns when the project idiom is clearer.

## Make contracts explicit

- Follow the repository's configured type system and strictness. Type changed boundaries and avoid
  weakening existing guarantees; do not impose a new language-wide typing policy from this skill.
- Represent absence explicitly. `None`, `null`, an option/result type, an empty collection, or an
  exception can each be correct when its meaning is documented by the local contract.
- Never use a shared mutable default. Prefer immutable values where they simplify reasoning, and
  keep necessary mutation local with a clear lifecycle owner.
- Validate untrusted inputs at the boundary that has enough context to decide validity. Preserve
  established error semantics unless the task changes them.
- Keep resource acquisition and release paired. Make ownership of files, locks, connections,
  processes, containers, and test data inspectable.

## Preserve readability and intent

- Match nearby naming, module layout, error handling, and API conventions.
- Comments and docstrings should explain contracts, constraints, or non-obvious reasons. Remove
  narration that merely repeats the code.
- Avoid unrelated cleanup in the same change. Record worthwhile out-of-scope work separately when
  the project's workflow supports it.
- Add a dependency only when the repository has no sufficient mechanism and the benefit exceeds
  lifecycle, security, and maintenance cost. Resolve current package syntax and versions from live
  official sources when a dependency change is actually required.

## Verify through the repository

Discover formatting, lint, type, build, and test commands through the `implement` workflow. Run the
smallest relevant gates first and broader project gates afterward. A formatter is a mutating command:
scope it to owned files or use check mode when unrelated work is present. Record the command source,
working directory, exit status, and any unexecuted or unavailable gate.

This reference defines author implementation constraints. It does not authorize an author to issue
an independent code-review or merge recommendation.
