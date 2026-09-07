---
name: kb-write
description: "Write durable knowledge as immutable OKF v0.2 Markdown notes with provenance, topic-first placement, supersession, and optional Qdrant indexing. Use only for explicit preservation or update requests."
---

# KB Write

Markdown notes are curated source records. Qdrant is derived; JSON sessions/transcripts are episodic.
Read [references/note-template.md](references/note-template.md).

Write only when explicitly asked to preserve/update durable knowledge. Questions, exploration,
session summaries, and context refreshes do not create notes or duplicate context.md/session records.

Route the body by `knowledge_type`, never `type`: decision (choice/evidence/trade-offs); event
(time/impact/status); procedure (steps/verification/teardown); reference (fact/scope/freshness);
conversation (durable exchange only without a stronger class). `type` is a separate free-form OKF
entity noun and selects neither template nor directory.

Resolve adapter roots and route `scope -> domain -> topic -> concept`, with at most one subtopic.
Project notes use
`work/projects/<project>/<topic>/<YYYY-MM-DD>--<short-slug>.md`. The topic is a stable lowercase
kebab-case subject; the short slug contains 2-6 substantive terms. `type` does not select the
directory. The relative Markdown path is the OKF Concept ID: never move or rename a note during a
normal write; path changes require an explicit migration.

Resolve project identity from an explicit project name, observed Git root, and `remote_url`. Reuse
the canonical slug already registered by `explorer`, `kb-session`, and `context-load.sh`; never
search for another slug to make a write succeed. If stable Git identity is unavailable, ask once for
the canonical name and slug. A canonical-domain collision blocks writing. An existing artifact
without sufficient identity also fails closed; never invent an alias.

Create dated files. To replace one, create a new note with `supersedes`, then change only prior status
to deprecated. Reconcile related notes/chains from disk, not only Qdrant.

Metadata includes OKF type/title/description/domain/created_at/status plus UUID id, closed
knowledge_type, `topic: <stable-subject>`, summary, entities, tags, nullable supersedes, generated,
optional verified/stale_after, and provenance. Summary is self-contained retrieval prose.
Relationships are Markdown links in explanatory sentences.

Generated records writer/time. Verified requires human confirmation. Provenance requires observed
`provenance.harness.name`, `provenance.harness.session_id`, `provenance.execution.cwd`,
`provenance.machine.id`, `provenance.machine.label`, `provenance.machine.hostname`, and
`provenance.machine.username`. Read machine identity from `~/.local/share/omh-kb/identity.json`;
never derive it from a raw MAC address. `provenance.harness.session_name`,
`provenance.harness.app_name`, and `provenance.execution.transcript_path` are present but nullable.
If required provenance is missing, do not write the note; Qdrant failure does not relax this gate.

Validate ownership; retrieve; choose knowledge_type/template; validate metadata/paths/provenance;
write without overwrite; update navigation; deprecate old only after new is durable; append log;
upsert Qdrant. Disk success plus Qdrant failure means indexing pending. Reconcile partial state from
Markdown before retrying.

Derive idempotency from harness, session, topic, knowledge_type, and concept, checking disk first.
Equivalent content is skipped; changed knowledge is supersession. Report created, superseded,
skipped, or partial with path, ID, provenance gaps, and index state.

For explicit complete-session distillation, require `kb-session`'s coverage report and build an
atomic note plan with `create | supersede | skip`. Keep one knowledge item per note. Derive
`distillation_key` as SHA-256 over canonical UTF-8 JSON with sorted keys, compact separators, NFC
strings, LF line endings, and algorithm `omh-kb-distillation-v1`; include sorted evidence,
`harness`, `session_id`, `knowledge_type`, `topic`, and `concept_key`.

Search disk exactly for the key before semantic retrieval. An existing key or equivalent knowledge
is a `skip`, but first reconcile the topic index, ancestor indexes, and pending Qdrant state. Only
mutable or derived structures may be reconciled; the note remains immutable. Publish a relationship
only after its target exists. Re-running the same corpus must reconcile and then `skip`, even when
Qdrant is unavailable. Report every candidate and pending repair.
