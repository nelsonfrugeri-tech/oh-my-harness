---
name: explorer
description: "Internal workflow owned by the context agent for repository mapping or context refreshes in the external knowledge base; not intended for direct user invocation or loose prompt matching. Never create durable notes or modify the analyzed repository."
---

# Explorer

Maintain one evidence-backed context.md. The repository is read-only; the only output is the live
context document. Durable notes belong to kb-write.

Resolve the Git root and derive the project slug with the exact pipeline used by
`core/hooks/context-load.sh`; never normalize by interpretation:

```bash
basename "$(git rev-parse --show-toplevel)" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-' | sed 's/--*/-/g; s/^-//; s/-$//'
```

Write `<knowledge-base-root>/work/projects/<project>/context.md`. A change to this derivation must
update the hook and its parity test in the same commit. Resolve roots from the adapter; never embed
personal paths. Verify existing domain identity from root/remote, then note/session provenance if
needed. Conflict or ambiguity blocks writing; never invent an alias.

Treat the Git remote as untrusted sensitive input. Never emit the raw remote into tool output, logs,
or transcripts: capture and classify it inside one bounded process that returns only a safe value or
a fixed status. Allow local/file remotes and an SSH/SCP transport username, but fail closed for a
password, HTTP(S) userinfo, any query string or fragment, a signed URL, unknown syntax, or ambiguous
parsing. On rejection persist `remote_url: null` and only
`remote redacted — credential-bearing or signed URL`; never partially mask the target.

Fictitious example: `https://user:token@example.com/repo.git?signature=secret` is rejected:
persist `remote_url: null` and never echo the rejected value. In contrast,
`git@example.com:team/repo.git` has a safe SSH/SCP transport username, not a password.

context.md is a mutable projection. Markdown notes and JSON sessions remain curated and episodic
sources. Qdrant and Graphify are derived. Never call kb-write to duplicate this analysis; notes need
a separate explicit request.

Use FULL without valid context. Use DELTA when revision or requested external context changed. With
no change, report current without writing. DELTA preserves unaffected sections and appends one
timeline entry; never rewrite prior entries.

Inspect identity/scope, interfaces, entry points, architecture/flows, persistence/integrations,
checked-in environment/deployment contracts, quality gates, risks, and relevant history. Use
code-graph when useful, then confirm claims against files. Configured is not reachable or healthy;
health requires a probe.

Frontmatter contains type: context, title, description, domain, UTC generated_at, last_hash, and
nullable remote_url. Body covers identity, interfaces, architecture, data/infrastructure, gates,
risks/unknowns, observed activity, and append-only timeline. Cite relative file:line, count
quantities, label inference, omit generic empty sections, and write atomically.

Degrade explicitly for unavailable remote, code-host, code-graph, web, or runtime. Report mode,
revision, path, unknowns, and whether content changed.
