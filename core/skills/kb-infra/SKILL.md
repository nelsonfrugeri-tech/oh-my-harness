---
name: kb-infra
description: "Internal workflow owned by the knowledge-base agent for Qdrant, BAAI/bge-m3 embeddings, machine identity, collection schema, reindexing, and scoped teardown; not intended for direct user invocation or loose prompt matching."
---

# KB Infra

Approved Markdown notes are source of truth; raw transcripts stay in their harness. Qdrant and embeddings are derived. Keep the
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

One collection indexes approved notes and frozen versions; it creates no new episodic points.
Embedding text is `title + description + summary`; point ID is uuid5 of the fixed namespace and
`f"{id}:{version}"`. Current and frozen versions have distinct stable IDs. Pending never enters
Qdrant. On approval, upsert current and set the old point status/path to superseded/.history/.

Create keyword indexes for `kind`, `scope`, `domain`, `entity_path`, `type`, `status`, `legacy`,
`tags`, all thirteen `entities.<kind>` keys, `path_prefixes`, and `url_hosts` with
`PayloadSchemaType.KEYWORD`. Index `version` as integer and `created_at`, `updated_at`,
`occurred_at`, and `dates[].at` with `PayloadSchemaType.DATETIME`. For Figures, validate the nested
float filter in the isolated Qdrant instance; if unsupported, use the approved flattened
`amount_<currency>` fallback. Do not infer query support from an index declaration.

| Record | Payload fields |
| --- | --- |
| Note point (`kind: "note"`) | id, version, path, title, description, summary, type, status, scope, domain, entity_path, tags, entities, path_prefixes, url_hosts, dates, figures, created_at, updated_at, occurred_at |

Derive scope/domain/entity_path from the validated note path; derive path_prefixes and url_hosts
from declared safe paths/URLs. Dates and Figures are structured from validated tables; never invent
a timezone or midnight. Live upsert and full reindex use this same mapping. Every dense and sparse
prefetch and the final RRF query exclude superseded and legacy by default. History and legacy flags
relax only their own exclusion. Never make pending searchable as an outage fallback.

Reconcile from disk with the CLI: validate active notes, frozen history, and links; repair derived
indexes without modifying source evidence. Do not delete a point merely because its old path moved:
look under backup/ and .history/ first. Reindexing never modifies source JSON or Markdown or assigns
current provenance to historical data. Invalid sources are reported and skipped. No automatic
legacy snapshot migration is performed.

At the explicitly reviewed cutover, `backup --dry-run` inventories local files and reports iCloud
files without downloaded bytes; blocked files prevent apply. Review the SHA-256 manifest before
`backup --apply`. Preserve .obsidian/ and .trash/; move the remaining legacy files byte for byte.
Generate backup/INSTRUCTION.md in pt-BR idempotently with date, reason, plan, counts, manifest hash
reference, and legacy point state. Existing legacy points receive legacy=true and backup/ paths
without re-embedding; repeated or resumed marking never doubles the prefix. Partial failures report
completed and remaining points. Preserve historical payloads rather than manufacturing new fields.
Legacy reads begin with backup/INSTRUCTION.md. Never treat backup sources as stale garbage.

Normal teardown stops only owned compose resources and preserves data. Volume/cache deletion is
destructive and requires confirmation. Never delete the knowledge bundle. Without Qdrant, write can save provenance-valid pending notes and disk navigation continues.
Approval requires the index and embedder; publication remains pending until they are available.
