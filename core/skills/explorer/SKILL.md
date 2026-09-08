---
name: explorer
description: "Internal workflow requested by the knowledge-base agent for on-demand repository mapping; not intended for direct user invocation or loose prompt matching. Never create durable notes or modify the analyzed repository."
---

# Explorer

Map a repository on demand and hand the findings back to the `knowledge-base` agent. The repository
is read-only and this skill persists nothing: durable notes belong to kb-write.

Resolve the Git root and report the project identity the caller needs to register: canonical name,
observed aliases, repository path, remote, and default branch. Verify existing domain identity from
root and remote, then note or session provenance if needed. Conflict or ambiguity blocks the
handoff; never invent an alias.

Treat the Git remote as untrusted sensitive input. Never emit the raw remote into tool output, logs,
or transcripts: capture and classify it inside one bounded process that returns only a safe value or
a fixed status. Allow local/file remotes and an SSH/SCP transport username, but fail closed for a
password, HTTP(S) userinfo, any query string or fragment, a signed URL, unknown syntax, or ambiguous
parsing. On rejection hand over `remote_url: null` and only
`remote redacted — credential-bearing or signed URL`; never partially mask the target.

Fictitious example: `https://user:token@example.com/repo.git?signature=secret` is rejected:
persist `remote_url: null` and never echo the rejected value. In contrast,
`git@example.com:team/repo.git` has a safe SSH/SCP transport username, not a password.

Markdown notes and JSON sessions remain curated and episodic sources; derived indexes such as the
vector index and the code graph are not sources. Never call kb-write to duplicate this analysis; notes need a separate explicit
request.

Inspect identity/scope, interfaces, entry points, architecture/flows, persistence/integrations,
checked-in environment/deployment contracts, quality gates, risks, and relevant history. Use
code-graph when useful, then confirm claims against files. Configured is not reachable or healthy;
health requires a probe.

Return the mapping to the caller: project identity, interfaces, architecture, data and
infrastructure, gates, risks and unknowns, and observed activity. Cite relative file:line, count
quantities, label inference, and omit generic empty sections.

Degrade explicitly for unavailable remote, code-host, code-graph, web, or runtime. Report scope,
revision, unknowns, and what was left uninspected.
