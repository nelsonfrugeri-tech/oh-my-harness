# Note body contracts

Select by knowledge_type, never free-form OKF type. Include only informative sections.

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
