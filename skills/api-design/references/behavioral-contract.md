# Behavioral Contract Matrix

Load this reference for a durable API, RPC, event, stream, or independently deployed interface.

## Scope

- Contract owner and change approver:
- Producers and known consumers:
- Protocol and independently deployed boundary:
- Current specification revision:
- Evidence inspected:
- Unknown consumers or runtime differences:

## Operation or event

| Concern | Contract | Evidence or check |
| --- | --- | --- |
| Identity | Stable operation, resource, or event name | Spec and consumer discovery |
| Principal | Actor, tenant, delegated identity | Authentication test |
| Authorization | Action, object, ownership, enforcement point | Cross-object negative test |
| Input | Required, omitted, null, empty, default, invalid | Schema and boundary tests |
| Success | Status/result, side effects, consistency | Integration test |
| Error | Stable code, retryability, safe detail, correlation | Failure-path test |
| Timeout/cancel | Deadline and partial-effect semantics | Timeout/cancellation test |
| Idempotency | Key binding, atomic outcome, conflict, expiry | Duplicate/concurrent retry test |
| Continuation | Total order, tie-breaker, snapshot/filter binding | Concurrent-write pagination test |
| Event delivery | Ordering, duplicate, replay, poison item | Consumer/replay test |
| Evolution | Compatibility class, window, telemetry, removal | Old-consumer compatibility check |

Use fields appropriate to the interaction; do not force HTTP concepts onto events or streams.

## Compatibility change

For each changed field or behavior, record:

- old and candidate semantics;
- known and unknown consumers;
- whether the protocol permits the structural change;
- whether deployed consumers tolerate the semantic change;
- rollout order and compatibility window;
- observation proving migration;
- rollback path and removal condition.

A structurally legal change can still break a consumer. A parser passing proves structure only.

## Idempotency invariants

The same principal, operation, and canonical request under the same valid key returns the persisted
outcome without repeating the side effect. A reused key with different request semantics fails
deterministically. Concurrent duplicates converge on one outcome. Persistence failure does not
silently leave an untracked side effect.

## Cursor invariants

The order is total and deterministic, including a unique tie-breaker. The cursor is bound to filters
and declared consistency semantics. Concurrent inserts, updates, and deletes have specified effects;
invalid or expired cursors fail explicitly rather than restarting silently.
