# Module Boundary Analysis

Load this reference when the decision concerns decomposition, a public interface, testability, or a
candidate abstraction.

## Inspect before proposing

Map actual callers, dependencies, tests, ownership, and recent changes. Treat a module as any unit
with an observable interface and hidden implementation; use the repository's domain language in the
final design.

Record:

- what every caller must know: types, invariants, ordering, errors, configuration, and performance;
- behavior hidden behind the interface;
- files and teams that change together;
- external side effects and failure propagation;
- tests that cross the same interface as production callers.

## Probe the shape

**Interface leverage:** does a small stable surface hide meaningful behavior, or do callers still
coordinate the implementation?

**Locality:** when one policy changes, is the change concentrated or repeated across callers?

**Deletion test:** mentally remove the module. If its complexity disappears, it may be pass-through
indirection. If required behavior spreads back into callers, the seam is earning its place.

**Replacement test:** identify what must change to replace the implementation. A seam is useful when
replacement or testing is an observed requirement, not merely imaginable.

**Test-surface test:** prefer tests through the public interface. A need to reach through it may
indicate missing behavior, the wrong seam, or an implementation-detail test.

## Decide whether to introduce a seam

A second real implementation, a deterministic test substitute for a costly external dependency, or
an owned remote transport can justify a seam. One production implementation alone does not prove an
abstraction is needed. Record the concrete variation and why direct dependency would make a tested
requirement harder.

Keep internal test seams private when callers do not need them. Do not expose every dependency only
to make mocking convenient.

## Compare candidates

Compare candidates by observable constraint fit, interface knowledge required by callers, change
locality, failure isolation, test surface, migration cost, and ease of deletion. Do not use
implementation-lines/interface-lines or a universal method count as a depth score.
