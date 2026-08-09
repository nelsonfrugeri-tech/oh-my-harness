# AGENTS.md

Binding rules for this environment. They apply to every Codex session and subagent.

<!-- Keep this file focused on rules that must apply to every session. Operational detail
     belongs in skills and is loaded on demand. Before adding a rule, ask whether removing it
     would make Codex behave incorrectly. -->

---

## Language

- User-facing conversation, instructions, headings, and explanations use Brazilian Portuguese.
- Engineering terms and proper names remain in English inline, such as *guard clause*, RAG, and OAuth.
- Repository content uses English, including code, comments, docstrings, and documentation.
- Skill, agent, and trigger names use English kebab-case. Frontmatter keys use the convention of
  their ecosystem, normally kebab-case or snake_case.
- Vendored third-party content remains in its original language and records its provenance and
  `upstream_version`; translating it would create an implicit fork that drifts from upstream.

---

## Never pollute a project with non-product files

**HARD RULE.** Inside a repository, create or edit only files that are part of the product: source
code, tests, configuration, and documentation intended for version control.

Auxiliary or temporary artifacts, including one-off scripts, analysis reports, scratch files,
intermediate output, and drafts, never belong in the repository. Put them in the session scratchpad
or `/tmp`. Prefer an ephemeral command over creating a file. If an artifact's status is ambiguous,
ask before creating it.

---

## Environment and capability adapters

Agents and skills refer to abstract capabilities, never to concrete tool identifiers. This table is
the machine adapter and is the only place that should bind a capability to an installed provider.
The installer may fill empty entries without changing agents or skills.

| Capability | Purpose | Codex provider on this machine |
| --- | --- | --- |
| `code-host` | Pull requests, issues, and remote reviews | _(configure during installation)_ |
| `ci` | CI/CD pipelines | _(configure during installation)_ |
| `memory` | Persistent project and personal context | _(empty means the `knowledge-base` agent)_ |
| `web` | Web search and page retrieval | Codex web capability |
| `code-graph` | Query, path, and explain over a code knowledge graph | Graphify MCP with CLI fallback |
| `social-x` | Read and publish on X | _(optional; configure an authenticated provider)_ |
| `session-memory` | Search past session transcripts by topic or file | Deja CLI or MCP when installed |

Codex built-ins for filesystem access, repository search, shell execution, and patch application do
not need adapter entries.

Resolve a requested capability through this table. If its provider is missing, complete the work
that remains possible and state exactly what is pending. Never invent a provider or concrete tool.

---

## Tool agents

A tool agent operates shared infrastructure consumed by other agents.

| Agent | Responsibility | Skills |
| --- | --- | --- |
| `context` | Maintain the current project's live context in `~/knowledge-base/work/projects/{project}/context.md` | `explorer` |
| `knowledge-base` | Operate Qdrant and embeddings, immutable notes, three-step retrieval, and session records | `kb-infra`, `kb-write`, `kb-retrieval`, `kb-session` |
| `graphify` | Build or update a code graph outside the product tree, then query, trace, or explain it | `graphify` |
| `x-social` | Read X and publish only after explicit confirmation | `x-setup`, `x-ops` |

Routing belongs in agent descriptions and mechanics belong in skills. Do not duplicate either here.

### Binding environment facts

1. The knowledge base is an OKF v0.2 bundle rooted at `~/knowledge-base/`, always outside user
   repositories. Its runtime belongs under `~/.local/share/omh-kb/`; the Markdown bundle is the
   source of truth and every binary index is rebuildable.
2. The embedding model is fixed to `BAAI/bge-m3`. Changing it invalidates the whole index and
   requires an explicit user decision.
3. When Deja is installed, `DEJA_INCLUDE_SUBAGENTS=1` is required so subagent transcripts are not
   omitted. Deja transcript redaction is a minimum safeguard; review content before exporting it.
4. Deja owns its own MCP and hook wiring. Harness synchronization must preserve Deja-managed hooks
   and its installed history skill. Use Deja only for retrieval; its note-writing features must not
   create a second curated knowledge store.
5. The Graphify skill is vendored upstream and is installed under `~/.agents/skills/graphify/`.
   Reconcile upstream upgrades before synchronizing the vendored copy again.
6. The library is account-agnostic. Client IDs, secrets, tokens, handles, and machine-specific
   executable paths never enter the repository.

### Two memory layers, two owners

| Layer | Storage | Writer | Reader |
| --- | --- | --- | --- |
| Raw and episodic: what was said | Codex transcripts and the Deja index | Automatic ingestion only | `session-memory` capability |
| Distilled and curated: what remains valid | OKF bundle under `~/knowledge-base/` | `kb-write` only | `kb-retrieval` |

### Codex session transcripts

Codex stores active transcripts under
`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-<timestamp>-<session-id>.jsonl`; the default
`CODEX_HOME` is `~/.codex`. Session-memory logic must discover the matching rollout rather than
assuming a project-munged directory. If the transcript cannot be resolved, write the session record
without `transcript_path` and report the degraded mode.

### Knowledge rules

1. Tool agents never write to the user's repository. Knowledge writes go to `~/knowledge-base/`;
   Codex adapter installation writes only to `$CODEX_HOME` and `~/.agents/`.
2. Without Qdrant, disk writes continue and indexing remains pending. Retrieval falls back to
   structured disk navigation and explicitly reports degraded mode.
3. Notes are immutable. Corrections create a new note with `supersedes`; session records and
   `context.md` are named mutable documents and are rewritten in place.

---

## Self-evaluation before answering

When uncertain, search before answering. Never answer private or episodic questions from memory.

Evaluate a candidate answer for relevance, freshness, and factuality. If any dimension is not
solid, search first:

- Public facts, documentation, versions, and news use the `web` capability.
- Private, episodic, project-history, and process questions use the knowledge base, including the
  session-memory step of `kb-retrieval` when needed.

After searching, cite the source. If evidence remains incomplete, state what is missing instead of
inventing an answer.

---

## Mandatory code standards

Before writing, modifying, or reviewing code, follow the complete inviolable standards in the
`implement` skill and `implement/references/code-craft.md`. This includes total typing, immutable
defaults, small cohesive functions and files, guard clauses, patterns instead of long conditional
chains, explicit absence semantics, comments that explain why, and the final quality gate.

---

## Commit gate

When the user asks for a commit:

1. Run format and lint first because they may modify files.
2. In parallel, have a Codex review subagent inspect the staged diff using the `review` skill and
   code-craft rules, and run the project's test suite.
3. Commit only when the review has no blocker and tests pass. Otherwise fix the findings and repeat.

Discover project commands from Makefile targets, project configuration, and then language defaults.
Never hardcode a test or lint command.

---

## Long-running work

Delegate a substantial, well-scoped, non-interactive task to a background subagent and remain
available to the user. Keep quick or interaction-heavy work inline. A subagent does not spawn
another subagent or communicate with the user mid-task; work that needs either stays in the main
loop.
