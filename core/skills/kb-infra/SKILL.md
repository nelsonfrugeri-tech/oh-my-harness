---
name: kb-infra
description: "Internal workflow owned by the knowledge-base agent for Qdrant, BAAI/bge-m3 embeddings, machine identity, collection schema, reindexing, and scoped teardown; not intended for direct user invocation or loose prompt matching."
---

# KB Infra

OKF v0.2 Markdown and JSON sessions are source of truth. Qdrant and embeddings are derived. Keep the
bundle outside repositories and runtime outside the bundle. Resolve roots from the adapter; never
hardcode personal paths. Use this skill's [docker-compose.yml](docker-compose.yml).

The fixed model is BAAI/bge-m3: dense 1024-dimensional plus lexical sparse vectors from one pass.
Changing it requires explicit decision, collection rebuild, and full reindex.

## Bootstrap the runtime

Keep the dedicated environment outside projects and the Markdown bundle. Resolve one runtime path
and reuse it for every command:

```bash
KB_RUNTIME="${OMH_KB_RUNTIME:-$HOME/.local/share/omh-kb}"
KB_VENV="$KB_RUNTIME/venv"
mkdir -p "$KB_RUNTIME"
if command -v uv >/dev/null 2>&1; then
  test -x "$KB_VENV/bin/python" || uv venv "$KB_VENV"
  uv pip install --python "$KB_VENV/bin/python" FlagEmbedding qdrant-client PyYAML
else
  test -x "$KB_VENV/bin/python" || python3 -m venv "$KB_VENV"
  "$KB_VENV/bin/python" -m pip install FlagEmbedding qdrant-client PyYAML
fi
```

Resolve current compatible package versions from official package metadata when installation is
required. Warn before the first network-backed model download and report its current published size
rather than freezing that volatile value here.

Smoke-test imports and the exact dense/sparse contract from the same interpreter:

```bash
"$KB_VENV/bin/python" - <<'PY'
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel(
    "BAAI/bge-m3",
    use_fp16=False,
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=False,
)
output = model.encode(["health"], return_dense=True, return_sparse=True)
weights = output["lexical_weights"][0]
indices = [int(token) for token in weights]
values = [float(weight) for weight in weights.values()]
assert len(output["dense_vecs"][0]) == 1024
assert len(indices) == len(values) and len(indices) > 0
PY
```

The production embedder lazy-loads one `BGEM3FlagModel` instance and converts each
`lexical_weights` mapping into parallel integer `indices` and float `values` for Qdrant.

Start Qdrant with `docker compose -f <resolved-skill-dir>/docker-compose.yml up -d`; resolve the
skill directory from the installed plugin rather than a personal path. Diagnose in this order:
`docker info`, the owned `oh-my-harness-qdrant` container via `docker ps`, `curl -fsS http://127.0.0.1:6333/healthz` with
bounded retry, collection/vector/index schema, then a short embedding from the dedicated venv.
Report the first failed boundary and its repair; never infer health from configuration.

Maintain runtime identity.json with stable UUID, chosen label, and creation time. Create atomically
with mode 0600, preserve UUID, reject invalid content, and never store MAC addresses. Invalid
identity blocks writes because provenance cannot be reconstructed.

Verify independently: owned container running; Qdrant health; collection knowledge-base with named
dense/sparse vectors; dense size/cosine distance; payload indexes; and a valid short embedding.
Configured never proves healthy. Container presence never proves Qdrant health.

One collection uses kind for note/session. Index `created_at` and `occurred_at` with
`PayloadSchemaType.DATETIME`. Create keyword indexes for `kind`, `domain`, `topic`, `type`,
`knowledge_type`, `harness`, `session_id`, `session_name`, `machine_id`, `machine_label`,
`distillation_key`, `entities`, `aliases`, `entity_kinds`, `entity_keys`,
`reference_targets`, and `temporal_values` with `PayloadSchemaType.KEYWORD`. Reapplying indexes is
idempotent; adding exact-lookup fields to an existing collection requires a full reindex, not
destructive recreation.

| Record | Payload fields |
| --- | --- |
| Note point (`kind: "note"`) | `kind`, `id`, `title`, `type`, `knowledge_type`, `domain`, `topic`, `distillation_key`, `created_at`, `summary`, `path`, `supersedes`, `archived`, `entities`, `aliases`, `entity_kinds`, `entity_keys`, `reference_targets`, `occurred_at`, `temporal_values`, `harness`, `session_id`, `session_name`, `app_name`, `cwd`, `transcript_path`, `machine_id`, `machine_label`, `hostname`, `username` |
| Session point (`kind: "session"`) | `kind`, `harness`, `session_id`, `session_name`, `app_name`, `domain`, `name`, `created_at`, `updated_at`, `entities`, `aliases`, `entity_kinds`, `entity_keys`, `reference_targets`, `temporal_values`, `cwd`, `transcript_path`, `machine_id`, `machine_label`, `hostname`, `username` |

Reconcile from disk: safely parse YAML/JSON; exclude indexes and logs from notes;
validate fields; resolve supersession; embed; upsert deterministic IDs; remove stale points only
after proving no disk source. Derive payload fields deterministically from source metadata:

- `entity_kinds` from `entity_refs[*].kind`; legacy flat entities never manufacture kinds;
- `entity_keys` from `entity_refs[*].name` and observed aliases, falling back to legacy
  `entities`/`aliases`, using NFKC + Unicode casefold + whitespace collapse;
- `reference_targets` from safe, present `references[*].target` values; redacted references without
  a target contribute nothing;
- `temporal_values` from `temporal_refs[*].value` plus a valid `occurred_at`;
- indexed `occurred_at` only from a timezone-aware RFC 3339 timestamp, never invented midnight or
  timezone.

Live upsert and full reindex use this same mapping.

Project missing multi-value fields as `[]` and nullable scalar fields as `null`, report each legacy
record, and continue the batch. Structured `entity_refs`, `references`, and `temporal_refs` remain
disk-only. Reindexing never modifies source JSON or source Markdown, manufactures historical metadata,
or assigns the current machine to a past session. Be resumable and report counts, failures, and
whether a full reindex remains pending.

Normal teardown stops only owned compose resources and preserves data. Volume/cache deletion is
destructive and requires confirmation. Never delete the Markdown/JSON bundle. Missing Qdrant leaves
indexing pending but does not block provenance-valid disk writes/navigation.
