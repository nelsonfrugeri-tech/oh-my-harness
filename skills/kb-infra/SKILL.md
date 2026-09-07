---
name: kb-infra
description: "Operate and verify derived knowledge-base infrastructure: Qdrant, BAAI/bge-m3 embeddings, machine identity, collection schema, reindexing, and scoped teardown."
---

# KB Infra

OKF v0.2 Markdown and JSON sessions are source of truth. Qdrant and embeddings are derived. Keep the
bundle outside repositories and runtime outside the bundle. Resolve roots from the adapter; never
hardcode personal paths. Use this skill's [docker-compose.yml](docker-compose.yml).

The fixed model is BAAI/bge-m3: dense 1024-dimensional plus lexical sparse vectors from one pass.
Changing it requires explicit decision, collection rebuild, and full reindex.

Maintain runtime identity.json with stable UUID, chosen label, and creation time. Create atomically
with mode 0600, preserve UUID, reject invalid content, and never store MAC addresses. Invalid
identity blocks writes because provenance cannot be reconstructed.

Verify independently: owned container running; Qdrant health; collection knowledge-base with named
dense/sparse vectors; dense size/cosine distance; payload indexes; and a valid short embedding.
Configured never proves healthy. Container presence never proves Qdrant health.

One collection uses kind for note/session. Index `created_at` as datetime. Create keyword payload
indexes for `kind`, `domain`, `topic`, `type`, `knowledge_type`, `harness`, `session_id`,
`session_name`, `machine_id`, `machine_label`, and `distillation_key`, using
`PayloadSchemaType.KEYWORD`.

| Record | Payload fields |
| --- | --- |
| Session point (`kind: "session"`) | `kind`, `harness`, `session_id`, `session_name`, `app_name`, `domain`, `name`, `created_at`, `updated_at`, `cwd`, `transcript_path`, `machine_id`, `machine_label`, `hostname`, `username` |

Reconcile from disk: safely parse YAML/JSON; exclude indexes, logs, and context.md from notes;
validate fields; resolve supersession; embed; upsert deterministic IDs; remove stale points only
after proving no disk source. Be resumable and report counts/failures. For legacy records, project
missing fields as null, report the record, and continue the batch. Reindexing never modifies source
JSON or assigns the current machine's identity to a historical session.

Normal teardown stops only owned compose resources and preserves data. Volume/cache deletion is
destructive and requires confirmation. Never delete the Markdown/JSON bundle. Missing Qdrant leaves
indexing pending but does not block provenance-valid disk writes/navigation.
