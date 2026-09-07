---
name: kb-session
description: "Maintain live JSON session records for episodic memory and retrieve session history through Deja or a bounded transcript fallback."
---

# KB Session

Session records are mutable JSON discovery records. Transcripts remain raw episodic memory; Markdown
notes remain curated memory written only by kb-write.

Store `<knowledge-base-root>/<domain>/sessions/<session-id>.json` using the shared Git-root slug and
collision gate. For a repository, run `git -C <cwd> rev-parse --show-toplevel` and normalize the Git
root basename, never the `cwd` basename, including sessions started in a subdirectory. Outside Git,
reuse the registered canonical project slug; never divert a session record to another domain. Apply
the same collision gate as `kb-write` before creating a directory or file. Resolve roots from the
adapter; never embed personal paths.

Schema:

```json
{
  "harness": "codex",
  "session_id": "<session-uuid>",
  "session_name": null,
  "app_name": null,
  "domain": "work/projects/<project>",
  "name": "<curated-session-subject>",
  "description": "<current-session-description>",
  "resume": "<dense-200-800-character-summary>",
  "cwd": "/absolute/observed/cwd",
  "transcript_path": null,
  "machine_id": "<stable-uuid>",
  "machine_label": "<operational-label>",
  "hostname": "<observed-hostname>",
  "username": "<observed-username>",
  "created_at": "<ISO-8601-UTC>",
  "updated_at": "<ISO-8601-UTC>"
}
```

The required non-null fields are `harness`, `session_id`, `cwd`, `machine_id`, `machine_label`,
`hostname`, and `username`. The `session_name`, `app_name`, and `transcript_path` fields always
exist but may be `null`; reject required values that are empty or whitespace-only. `cwd` and every
non-null path must be absolute. Session ID is the filename and Qdrant point ID. Missing required
identity blocks writing; a null transcript path is allowed only in declared degraded mode.

Legacy records remain readable and reindexable. Project each missing Qdrant payload field as `null`,
report the record as legacy, never rewrite historical JSON, and never assign the current machine to
a past session. Promote only the current session to schema v3 and only with values observed during
that update, preserving `created_at`. If a required value remains unavailable, preserve the legacy
record unchanged and report the missing field.

Discover Codex rollouts from harness metadata and dated state inventory by session ID; never derive
paths from project or cwd. Update atomically, preserving created_at. Session end is a final update,
not a note. Upsert kind: session. Qdrant failure leaves JSON durable and indexing pending;
configured is not healthy.

Prefer abstract session-memory for narrow topic or exact-file recall, combining file recall with Git
history. Disclose useful recalls and revalidate mutable facts. Without it: select candidate JSON,
verify transcript containment, parse JSONL, search bounded context, redact secrets/personal data,
and never load/export a whole transcript. Report reduced coverage.

This skill never writes notes. Only explicit preservation may pass atomic durable knowledge with real
provenance to kb-write; never duplicate resume, transcript, or context.md.

## Complete session distillation

Complete distillation is distinct from targeted recall and requires an explicit request. Stream the
entire transcript through bounded contiguous chronological intervals; never place the whole corpus
in one prompt. Record total bytes, total raw records, parseable events, parsing failures, first/last
timestamps, and the parser used.

Maintain a coverage ledger outside repositories with interval offsets or IDs, byte and record counts,
classification status, candidates, and redaction status. Every record must end as processed content,
justified noise, a parsing failure, or unclassified; either of the last two is a coverage gap. Claim
complete coverage only when intervals continuously cover the population with no unprocessed
interval, parsing failure, unclassified record, or unintended duplicate.

Detect credentials, tokens, secrets, and personal data before persistence. Irreversibly redact raw
values from the ledger and candidate corpus; if sensitive data is detected or uncertain, present the
redacted plan and obtain human confirmation before writing. Apply the `kb-write` collision gate,
then pass the source window, coverage ledger, and atomic candidates to `kb-write`. The final report
states source, window, method, population, intervals, gaps, candidates, and per-note outcome.
