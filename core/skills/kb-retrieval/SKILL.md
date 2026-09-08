---
name: kb-retrieval
description: "Internal retrieval workflow owned by the knowledge-base agent, also used by kb-write, through Qdrant, structured disk navigation, and targeted session-memory; not intended for direct user invocation or loose prompt matching."
---

# KB Retrieval

Curated memory is Markdown notes. Episodic memory is raw transcripts plus
mutable JSON sessions. Qdrant and Graphify are derived, not sources.

## Resolve exact entities and addresses first

When a request names an entity or asks for an address, repository, path, URL, owner, or time, perform
exact lookup before semantic search. Extract the requested name or observed alias and the desired
property; embeddings must never choose among homonyms.

For project/repository lookup, inspect the active `knowledge_type: project` note under
`work/projects/*/identity/` first. Match directory, `name`, `aliases`, and safe repository name; use
`repository_path`, `remote_url`, and `default_branch` from its frontmatter only as candidates. Revalidate legacy stored remotes before responding. Reject a password, HTTP(S)
userinfo, any query string or fragment, signed URLs, or ambiguous parsing; an SSH/SCP transport
username is allowed. Treat a rejected value as `remote_url: null`, report `redacted`, and never echo
the sensitive target, even partially.

For notes and sessions, compare `entity_refs.name`, `entities`, `aliases`, and
`references.target` on disk; use `entity_kinds`, `entity_keys`, and `reference_targets` in Qdrant. Normalize lookup
keys with NFKC, Unicode casefold, and whitespace collapse while preserving source spelling in the
answer. Resolve time through `occurred_at`, `temporal_refs`, and `temporal_values` without inventing
timezone.

A unique match answers directly from the source record. Multiple matches require disambiguation and
never select the first match. Zero matches transitions to the retrieval ladder and declares that
transition. An `unverified`, `redacted`, or unsafe address returns only its status. If the user asks
to open a safe result, this skill resolves and cites it; a caller with the appropriate capability
performs the external action.

## Run the retrieval ladder

For topics use: (1) hybrid Qdrant, (2) structured disk, (3) targeted session-memory. Descend when
unavailable/incomplete and disclose layer/degradation. For a repository path, start with file-aware
session-memory plus git log --follow.

Probe Qdrant, embed with fixed bge-m3, prefetch dense/sparse, fuse with RRF, and filter inside both
prefetches. Filter `kind`, `domain`, `topic`, date, archived state, and exact provenance fields: `harness`,
`session_id`, `session_name`, `machine_id`, and `machine_label`. Legacy points may carry null
topic or provenance; an exact filter deliberately excludes them and that limitation must be
reported. `type` is entity class; `knowledge_type` is epistemic class. Do not confuse them. RRF is
ranking, not calibrated relevance. Inspect source records. Missing collection means missing index,
not missing knowledge.

On disk navigate bundle/domain/topic indexes into the topic folder. For a recursive newest-first
timeline that excludes reserved files, use:
`find ~/knowledge-base/<domain> -type f -name '*.md' ! -name index.md ! -name log.md -print | awk -F/ '{print $NF "\t" $0}' | sort -r | cut -f2- | head`.

Parse only the first YAML frontmatter block for metadata with `yaml.safe_load`; never grep bodies for
keys. An ephemeral filter may receive `~/knowledge-base/<domain> type system`, split the file into
lines, require the first line to be `---`, and locate the closing delimiter with
`lines.index("---", 1)`. Invalid or non-mapping YAML is reported and skipped. `index.md` and `log.md`
are reserved navigation, not notes. Search JSON structurally. Follow
relationships/supersession; prefer the newest active note unless history is requested. Report broken
or conflicting chains.

Use Deja through abstract session-memory: narrow recall, concise context, then revalidate mutable
facts. If unavailable, use kb-session's bounded fallback; never load a whole transcript.

Cite exact source/provenance. Separate fact, derived ordering, inference, and unknown. No result means
none in searched scope. Report domains, filters, time window, providers, and degradation.
