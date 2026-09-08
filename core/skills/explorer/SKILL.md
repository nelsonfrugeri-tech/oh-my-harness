---
name: explorer
description: "Use when onboarding into an unfamiliar repository — mapping an unknown project, understanding how it works, or preparing a first CLAUDE.md — and internally by the knowledge-base agent to resolve project identity for a KB write. The repository stays read-only; this skill persists nothing itself."
---

# Explorer

Map a repository on demand and produce three outputs: a navigable site report, a proposed project
`CLAUDE.md`, and a handoff of project identity and candidate notes to the `knowledge-base` agent.
The repository is read-only and this skill persists nothing on its own: durable notes and the
project identity note belong to `kb-write`, called only by `knowledge-base`. Never call kb-write to
duplicate this analysis; notes need a separate explicit request from the caller.

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
vector index and the code graph are not sources.

Inspect identity/scope, interfaces, entry points, architecture/flows, persistence/integrations,
checked-in environment/deployment contracts, quality gates, risks, and relevant history. Use
code-graph when useful, then confirm claims against files. Configured is not reachable or healthy;
health requires a probe.

## Three onboarding outputs

1. **Site report.** Route the mapping to `site-report` to produce a navigable, cited site outside
   the analyzed repository — the DeepWiki-style entry point for "how does this project work."
2. **`CLAUDE.md` proposal.** In the spirit of the Claude Code `/init` command, propose only what is
   not derivable by re-reading the code: commands absent from the Makefile or scripts, conventions
   that diverge from the language's or framework's default, and known pitfalls. Present the full
   proposal to the user and require explicit approval before it is written; the calling thread
   writes the approved proposal, this skill never does — it has no write access to the analyzed
   repository, only to the external site. Absent approval, keep the proposal in the response only.
3. **Handoff to `knowledge-base`.** Return the project identity (the same fields as the project
   note: name, aliases, repository path, remote, default branch, with the remote guard above) and
   any candidate decision/procedure notes found during mapping, in one explicit block, to the main
   thread. This skill and the `explorer` agent never write to the knowledge base themselves — a
   subagent does not call another subagent, and `knowledge-base` is the only curated-knowledge
   writer; the calling thread routes the handoff to it.

Return the mapping to the caller: project identity, interfaces, architecture, data and
infrastructure, gates, risks and unknowns, and observed activity. Cite relative file:line, count
quantities, label inference, and omit generic empty sections.

Degrade explicitly for unavailable remote, code-host, code-graph, web, or runtime. Report scope,
revision, unknowns, and what was left uninspected.
