# Note template

Use this complete frontmatter shape; replace placeholders with observed values, use empty arrays
when no material items exist, and omit optional `verified` and `stale_after` when inapplicable.
`okf_version: "0.2"` belongs only in the bundle-root `index.md`, never in a note.

```yaml
---
type: <entity-or-concept-noun>
title: <short-specific-title>
description: <one-sentence-description>
tags: []
status: stable
generated:
  by: <producer/version>
  at: <ISO-8601-UTC>
provenance:
  harness:
    name: <observed-harness>
    session_id: <real-session-id>
    session_name: null
    app_name: null
  execution:
    cwd: /absolute/observed/cwd
    transcript_path: null
  machine:
    id: <stable-machine-uuid>
    label: <operational-label>
    hostname: <observed-hostname>
    username: <observed-username>
verified:
  - by: human:<id>
    at: <ISO-8601-UTC>
stale_after: <YYYY-MM-DD>
id: <uuid4>
distillation_key: null
knowledge_type: reference
domain: work/projects/<project>
topic: <stable-subject>
created_at: <ISO-8601-UTC>
entities: [<canonical-name>]
aliases: []
entity_refs:
  - kind: project
    name: <canonical-name>
    aliases: []
references:
  - kind: repository-url
    label: <source-label>
    target: https://example.com/team/repo
    entity: <canonical-name>
    status: observed
occurred_at: null
temporal_refs:
  - value: <ISO-8601-date-time-or-interval>
    timezone: unknown
    meaning: <temporal-significance>
supersedes: null
summary: >-
  <Self-contained retrieval prose of 200-800 characters, distinct from title and description.>
---
```

`type` is a free-form entity noun; `knowledge_type` selects one body contract below. Status is
`stable | draft | deprecated`. `generated` identifies the actual writer and time; `verified` is a
list added only after real human confirmation, with the mandatory `human:` prefix in each `by`.
Never fill it from the example alone. `created_at` is immutable; do not add the old `timestamp` field.
Preserve observed nullable provenance; missing required provenance blocks writing per `kb-write`.
Use `distillation_key` only for session distillation, otherwise `null`; `supersedes` is the prior
note's UUID or `null`. `stale_after` is optional when validity is known.

Keep source `occurred_at` as an observed ISO 8601 instant, date, or `null`. Only timezone-aware
RFC 3339 instants populate indexed `occurred_at`; date-only and unknown-timezone values remain
retrievable through `temporal_values`, with `occurred_at: null` in the index.

## Body contracts

Select by knowledge_type, never free-form OKF type. Start with a brief context explaining why the
note exists; retain the required content below and omit optional sections when inapplicable.

- decision: context/choice, alternatives, evidence/trade-offs, owner/validation, rollback/review,
  and a falsifying result.
- event: time/actors, occurrence, impact, response/status, unresolved follow-up.
- procedure: purpose/prerequisites, ordered steps, verification, failure handling, teardown/rollback.
- reference: fact/constraint, scope/evidence, consequences, freshness/version boundary.
- conversation: participants/context, positions, durable outcome, open questions.

If conversation produced another class, use that stronger knowledge_type. Express relationships as
Markdown links in sentences naming the relationship. Use bundle-rooted paths; omit related-link dumps.

A source with a material address also requires a structured `references` entry, even when the body
mentions it. Preserve canonical entities and observed aliases in `entity_refs`. Never include
credentials, HTTP(S) userinfo, secret query parameters, or signed URLs; a reference that cannot be
made safe is `redacted` and has no target.

Keep exact safe targets and absolute local paths; reference status is
`verified | observed | unverified | redacted`, based on actual validation, not plausibility.
Do not copy the summary into the body or paste raw transcripts unless the transcript itself is the
knowledge. Date facts that can drift, such as versions, costs, and policy values. State an event's
root cause only when established; otherwise link the investigation. Use executable procedure steps
with expected outputs. Keep Markdown formatting minimal: headings, paragraphs, and code blocks.
