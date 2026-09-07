---
name: api-design
description: >-
  Derive, evolve, or verify a behavioral API contract across REST, RPC, GraphQL, events, or internal
  interfaces, including errors, retries, idempotency, pagination, authorization, and compatibility.
  Use when consumers cross a versioned or independently deployed boundary. Do not use solely for
  SDK syntax, generic HTTP explanations, or implementation behind an unchanged private interface.
metadata:
  origin: native
  last_verified: 2026-09-07
---

# Behavioral API Contract

Make consumer-visible behavior explicit and verify that retries, failures, authorization, and
evolution preserve it.

## Guard the boundary

- Start from consumer behavior and deployment independence, not from a fashionable protocol.
- For a purely local interface with no compatibility burden, use the project's implementation
  workflow unless the public behavior itself is under design.
- Route structural architecture choices to `design` and abuse-path analysis to `security`.
- When supplying observations to `review`, do not assign severity or duplicate its final template.
- Retrieve current framework, provider, SDK, specification, and validator behavior from official
  sources at use time. If unavailable, state the unverified portion and do not invent syntax.

## Extract the current contract

Inspect specifications, handlers, schemas, consumer code, generated clients, contract tests,
telemetry, and release history. Reconcile differences explicitly; a spec file proves declared
behavior, not runtime conformance.

For each operation or event, capture:

- identity, actor, resource or operation, and authorization subject;
- request/event schema, field presence, nullability, defaults, and validation;
- success, error, timeout, cancellation, and partial-failure behavior;
- side effects, consistency boundary, ordering, replay, and concurrency;
- retry and idempotency semantics;
- pagination or streaming continuation;
- versioning, deprecation, and known consumers.

Use [behavioral-contract.md](references/behavioral-contract.md) when a durable matrix is useful.

## Design and verify behavior

1. **Choose the interaction shape.** Compare resource, RPC, query, event, or stream semantics against
   consumer needs, failure model, ownership, latency, and compatibility. Do not choose by naming
   convention alone.
2. **Define absence precisely.** Distinguish omitted, explicit `null`, empty, defaulted, unknown,
   and deleted values in both requests and responses.
3. **Define errors as behavior.** Specify machine-readable identity, retryability, user-safe detail,
   correlation, and whether a failed batch is atomic or returns item-level outcomes. Do not leak
   secrets or internal stack details.
4. **Bind authorization to the object.** Authentication is not object authorization. State the
   principal, action, resource, tenant, ownership rule, and enforcement point for every protected
   operation.
5. **Make retries safe.** Bind an idempotency key to principal, operation, and canonical request
   semantics; persist outcome atomically with the side effect; define concurrent duplicate,
   mismatch, expiry, and partial-failure behavior. Never claim idempotency from the HTTP method or
   key presence alone.
6. **Make continuation stable.** A cursor must encode or reference a deterministic total order with
   a unique tie-breaker and declared snapshot/change semantics. Define invalid, expired, and
   filter-mismatched cursor behavior.
7. **Plan evolution per consumer.** Classify field and operation changes against actual protocol and
   consumer behavior. Use expand/migrate/observe/contract stages, a compatibility window, rollback,
   and a removal signal. Never reuse event field numbers or silently change field meaning.
8. **Validate mechanically.** Use the repository's pinned parser, schema validator, compatibility
   checker, and consumer tests. Exercise accepted and rejected values for regex or format rules;
   parse examples; resolve references; and test old consumers against the candidate contract where
   risk warrants it.

### Narrow User API OpenAPI 3.1 example

This narrow document is retained as a mechanically validated regression fixture, not as a general
OpenAPI template. Resolve current OpenAPI and validator behavior from their official sources before
using a similar contract in production.

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "User API",
    "version": "1.0.0",
    "description": "API for user management."
  },
  "servers": [
    {"url": "https://api.example.com/v1", "description": "Production"},
    {"url": "https://api.staging.example.com/v1", "description": "Staging"}
  ],
  "paths": {
    "/users/{id}": {
      "get": {
        "operationId": "getUser",
        "summary": "Get a user by ID",
        "tags": ["users"],
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {"$ref": "#/components/schemas/User/properties/id"}
          }
        ],
        "responses": {
          "200": {
            "description": "User found",
            "content": {
              "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
            }
          },
          "404": {"$ref": "#/components/responses/NotFound"}
        }
      }
    }
  },
  "components": {
    "schemas": {
      "User": {
        "type": "object",
        "required": ["id", "name", "email", "created_at"],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^usr_[a-zA-Z0-9]{20}$",
            "example": "usr_a1b2c3d4e5f6g7h8i9j0"
          },
          "name": {"type": "string", "minLength": 1, "maxLength": 100},
          "email": {"type": "string", "format": "email"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      },
      "Error": {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
          "code": {"type": "string", "example": "not_found"},
          "message": {"type": "string", "example": "Resource not found"}
        }
      }
    },
    "responses": {
      "NotFound": {
        "description": "Resource not found",
        "content": {
          "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
        }
      }
    },
    "securitySchemes": {
      "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
  }
}
```

## Produce the contract

Report the selected interaction shape, contract matrix, incompatible changes, migration stages,
verification evidence, assumptions, unknowns, and residual risks. Include examples only when they
are parsed or executed by a declared check.

## Verify and stop

Stop when every material consumer-visible behavior maps to a contract field and a check or explicit
unknown. A passing schema parser alone does not prove runtime behavior, authorization, retry safety,
or consumer compatibility.

Refresh this skill when package evals fail. Refresh external facts when the protocol specification,
provider contract, framework, validator, or consumer environment changes.
