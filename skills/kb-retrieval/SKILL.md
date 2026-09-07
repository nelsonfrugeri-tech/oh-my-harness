---
name: kb-retrieval
description: "Retrieve curated notes and episodic sessions from the external OKF knowledge base through hybrid Qdrant, structured disk navigation, and targeted Deja/session-memory."
---

# KB Retrieval

Curated memory is Markdown notes plus mutable context.md. Episodic memory is raw transcripts plus
mutable JSON sessions. Qdrant and Graphify are derived, not sources.

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
`find ~/knowledge-base/<domain> -type f -name '*.md' ! -name index.md ! -name log.md ! -name context.md -print | awk -F/ '{print $NF "\t" $0}' | sort -r | cut -f2- | head`.

Parse only the first YAML frontmatter block for metadata with `yaml.safe_load`; never grep bodies for
keys. An ephemeral filter may receive `~/knowledge-base/<domain> type system`, split the file into
lines, require the first line to be `---`, and locate the closing delimiter with
`lines.index("---", 1)`. Invalid or non-mapping YAML is reported and skipped. `index.md`, `log.md`,
and `context.md` are reserved navigation/live context, not notes. Search JSON structurally. Follow
relationships/supersession; prefer the newest active note unless history is requested. Report broken
or conflicting chains.

Use Deja through abstract session-memory: narrow recall, concise context, then revalidate mutable
facts. If unavailable, use kb-session's bounded fallback; never load a whole transcript.

Cite exact source/provenance. Separate fact, derived ordering, inference, and unknown. No result means
none in searched scope. Report domains, filters, time window, providers, and degradation.
