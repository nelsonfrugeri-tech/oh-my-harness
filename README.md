<div align="center">

# oh-my-harness

**A portable, harness-agnostic library of expert agents, skills, and workflows for AI coding assistants.**

Write the config once. Plug the tools per machine. Run it on Claude Code today — and on Codex or Cursor tomorrow — without changing a line.

[![License](https://img.shields.io/badge/license-Apache%202.0-4CAF50?style=flat-square)](LICENSE)
[![Harness](https://img.shields.io/badge/harness-Claude%20Code-8A63D2?style=flat-square)](https://claude.com/claude-code)
[![Agents](https://img.shields.io/badge/agents-9-2496ED?style=flat-square)](#whats-inside)
[![Skills](https://img.shields.io/badge/skills-23-DC5F00?style=flat-square)](#whats-inside)
[![Docs](https://img.shields.io/badge/docs-pt--BR-009C3B?style=flat-square)](#language-contract)

</div>

---

## The problem

Harness config is born coupled. One MCP tool hardcoded here, a `~/.config/...` path there, a reference to a specific service somewhere else. Switch machines — GitHub at home, GitLab at work — or switch assistants, and it breaks. You re-wire the same plumbing on every setup.

**oh-my-harness decouples _what the agent does_ from _which tool it does it with._** The same `developer` opens a Pull Request through GitHub on your personal machine and through GitLab on the company laptop — the files are byte-for-byte identical. Only one small table changes.

---

## Table of contents

- [How it works](#how-it-works)
- [Core ideas](#core-ideas)
  - [Capabilities — the tool plug](#capabilities--the-tool-plug)
  - [Progressive disclosure](#progressive-disclosure)
  - [code-craft — inviolable rules](#code-craft--inviolable-rules)
  - [Language contract](#language-contract)
- [Quick start](#quick-start)
- [What's inside](#whats-inside)
- [Knowledge base](#knowledge-base)
- [Portability across harnesses](#portability-across-harnesses)
- [Extending the library](#extending-the-library)
- [Why](#why)
- [License](#license)

---

## How it works

This repository is the **source**. You sync it into your harness's **global state** (`~/.claude`), and agents resolve their tools per machine through a single capability table.

```
┌───────────────────────────────────────────────────────────────────┐
│  oh-my-harness · SOURCE (this git repo)                            │
│                                                                     │
│  agents/                    skills/                  claude-code/  │
│  ├── engineers/  (6)        ├── engineers/ (17)       CLAUDE.md     │
│  ├── harness/    (1)        ├── harness/    (1)       settings.json │
│  └── tools/      (2)        └── tools/      (5)       workflows/    │
│      (themed; discovery         (themed source; flattened on       │
│       is recursive)              install — leaf name only)         │
└──────────────────────────────┬──────────────────────────────────────┘
                                │  "ask the harness to sync"
                                ▼  (agent `claude-code`)
┌───────────────────────────────────────────────────────────────────┐
│  ~/.claude/ · GLOBAL harness state                                  │
│  agents/<theme>/<name>.md   skills/<leaf>/   workflows/   CLAUDE.md │
└──────────────────────────────┬──────────────────────────────────────┘
                                │  capability plug (per machine)
                   ┌────────────┴─────────────┐
                   ▼                           ▼
          code-host → mcp__github__*   code-host → mcp__gitlab__*
          (personal machine)           (work machine)

┌───────────────────────────────────────────────────────────────────┐
│  ~/knowledge-base/ · outside any repo                               │
│  {project}/context.md — living context (`context` agent on each     │
│    session start; `explorer` runs only on FULL/DELTA)               │
│  {project}/notes/ — immutable notes (`knowledge-base` agent →       │
│    kb-write/kb-retrieval), indexed in local Qdrant via BGE-M3       │
│  {project}/sessions/ — living session records (`kb-session`),       │
│    pointing at the harness's raw transcripts for deep search        │
└───────────────────────────────────────────────────────────────────┘
```

- **agents** are symlinked mirroring their theme (`agents/<theme>/<name>.md`) — discovery is
  recursive, so subfolders work natively and a `git pull` on the source updates them everywhere.
- **skills** are symlinked **flattened** to `~/.claude/skills/<leaf>/` — skill discovery is
  *not* recursive in `~/.claude/skills/`, so each skill must be a direct child of that folder
  even though the source keeps them themed.
- **CLAUDE.md** carries the timeless rules and the per-machine capability table.
- The agent **`claude-code`** (backed by the `claude-code` skill) is the runbook the harness
  runs to sync (see [Quick start](#quick-start)).
- The agent **`context`**, invoked on every `SessionStart`, keeps a living knowledge base of
  the *current* project at `~/knowledge-base/{project}/context.md` — built and updated by the
  `explorer` skill, entirely outside the project's own working tree.
- The agent **`knowledge-base`** manages the persistent knowledge base: infra (local Qdrant +
  BGE-M3 embeddings via `kb-infra`), immutable notes (`kb-write`), 3-step retrieval
  (`kb-retrieval`) and the harness's session memory — living session records plus deep search
  inside raw transcripts (`kb-session`) — see [Knowledge base](#knowledge-base).

---

## Core ideas

### Capabilities — the tool plug

Agents and skills reference **abstract capabilities**, never a concrete tool. A single table (in `claude-code/CLAUDE.md`) maps each capability to the tool available on _this_ machine. Change environment, change only the table.

| Capability  | Role                                   | Example per machine        |
| ----------- | -------------------------------------- | -------------------------- |
| `code-host` | Pull/Merge Requests, issues            | `mcp__github__*` / GitLab  |
| `ci`        | CI/CD pipelines                        | GitHub Actions / GitLab CI |
| `memory`    | Persistent project notes (optional)    | any memory MCP             |
| `web`       | Search and fetch                       | `WebSearch`, `WebFetch`    |

### Progressive disclosure

Each skill is a lean `SKILL.md` (overview + when to use) that points to `references/` loaded **on demand**. Context only pays for the depth a task actually needs — the ~140 reference files stay out of the window until required.

### code-craft — inviolable rules

The non-negotiable code-quality rules — total typing, immutability, small cohesive units, guard clauses over nesting, a design pattern instead of `if/elif` chains, a final quality gate — live in [`skills/engineers/implement/references/code-craft.md`](skills/engineers/implement/references/code-craft.md) as a **single source of truth**, referenced by `implement` and reused by `review`.

### Language contract

Instructional prose is **pt-BR**; code, comments, docstrings, and technical terms stay **English**. You talk to the harness in your language; what ships to a codebase is written in the code's language.

---

## Quick start

```bash
git clone https://github.com/nelsonfrugeri-tech/oh-my-harness.git
cd oh-my-harness
```

Then **ask the harness to sync**. On a brand-new machine the library isn't installed yet, so
[`INSTRUCTIONS.md`](INSTRUCTIONS.md) is the bootstrap entrypoint: it points the harness at the
agent `claude-code` (`agents/harness/claude-code.md`, backed by the `claude-code` skill), which
resolves everything interactively — themed symlink for agents, flattened symlink for skills,
diff of `CLAUDE.md`/`settings.json`, MCP detection and capability wiring, orphan cleanup:

> _"Read INSTRUCTIONS.md and sync this library with my ~/.claude."_

Finally, edit the **Ambiente & Tools** table in `~/.claude/CLAUDE.md` to plug this machine's
tools. From then on, every session start triggers the `context` agent, which builds (first run)
or refreshes (later runs) the project's living knowledge base at
`~/knowledge-base/{project}/context.md`.

---

## What's inside

### Agents

Agents are grouped by theme under `agents/<theme>/`. Discovery is recursive — the theme folder
is only organizational, the agent's real name comes from its frontmatter `name:`.

| Theme       | Agent         | Role                                                | Model  |
| ----------- | ------------- | ---------------------------------------------------- | ------ |
| `engineers` | `architect`   | System design, ADRs, C4, trade-offs, API design       | opus   |
| `engineers` | `developer`   | Implementation, bug fixes, refactoring, testing       | sonnet |
| `engineers` | `ai-engineer` | LLM/RAG/embeddings, data pipelines, evaluation         | sonnet |
| `engineers` | `qa`          | Test strategy, E2E, performance, accessibility        | sonnet |
| `engineers` | `sre`         | Observability, SLO/SLI, incident response              | sonnet |
| `engineers` | `tech-pm`     | User stories, backlog, roadmap, PRDs                   | sonnet |
| `harness`   | `claude-code` | Installs/syncs the library into `~/.claude`             | sonnet |
| `tools`     | `context`     | Loads/refreshes the project's living knowledge base at `~/knowledge-base/{project}/context.md` | sonnet |
| `tools`     | `knowledge-base` | Manages the knowledge base: infra (Qdrant + BGE-M3), immutable notes, 3-step retrieval, session memory + deep search | sonnet |

### Skills

Skills are grouped by theme under `skills/<theme>/<name>/`, but the **install step flattens
them** to `~/.claude/skills/<name>/` — skill discovery is not recursive at the target, so each
skill must land as a direct child.

**Knowledge (languages & domains) — `engineers`:** `python` · `typescript` · `ai-engineer` · `api-design` · `frontend-ui` · `security` · `observability`

**Capability (method & process) — `engineers`:** `implement` · `design` · `test` · `review` · `research` · `operate` · `manage` · `environment` · `ci-cd`

**Command & workflow — `engineers`:** `feature`

**Harness tooling — `harness`:** `claude-code` (the sync runbook behind the `claude-code` agent)

**Tools agents — `tools`:** `explorer` (deep repo analysis behind the `context` agent) · `kb-infra` (Qdrant + embedding infra) · `kb-write` (the scribe — immutable notes) · `kb-retrieval` (3-step retrieval: hybrid semantic search → disk navigation → session deep search) · `kb-session` (living session records + deep search inside the harness's raw transcripts). Invoked by the `context` and `knowledge-base` agents, not directly by the user.

Each skill ships a `SKILL.md` and, where applicable, a `references/` folder with the deep dives.

### Workflows

| Workflow         | What it does                                                                       |
| ---------------- | ---------------------------------------------------------------------------------- |
| `create-feature` | End-to-end pipeline: user story → dev → parallel `qa`+`sre` loop → PR via `code-host` |

---

## Knowledge base

Knowledge lives on disk at `~/knowledge-base/` — outside every repo, portable, readable by any
Markdown tool. Qdrant is only a derived index, rebuilt from disk at any time.

```
~/knowledge-base/
  {project}/
    context.md              # living context: snapshot (rewritten) + append-only timeline
    notes/
      <date>--<slug>.md     # immutable notes: frontmatter (id, type, summary, ...) + body
    sessions/
      <session_id>.json     # living session records: name, description, resume, transcript_path
  .qdrant/                  # local Qdrant volume (docker, port 6333)
  .venv/                    # embedding environment
```

- **Notes are immutable** — corrections are new notes carrying `supersedes`; the old note stays
  archived. Types: `decision · event · procedure · reference · conversation`.
- **Session records are living documents** — one JSON per harness session, rewritten in place
  (a named exception to note immutability), pointing at the harness's raw transcript so
  retrieval can deep-search what was actually said in past sessions.
- **Search is hybrid, retrieval is a 3-step ladder** — note summaries and session resumes are
  embedded with **`BAAI/bge-m3`** (dense 1024-dim + lexical sparse in one forward pass) and
  queried in Qdrant with dense+sparse prefetch fused by Reciprocal Rank Fusion; no Qdrant means
  structured disk navigation; and when neither answers, `kb-session` grep-dives the raw
  transcript of the most relevant sessions.
- **Infra is one command away** — the `kb-infra` skill ships a pinned `docker-compose.yml`
  (`qdrant/qdrant:v1.18.0`, container `oh-my-harness-qdrant`) and the embedding setup.

---

## Portability across harnesses

`agents/` and `skills/` are the reusable base. Everything Claude-Code-specific (`CLAUDE.md`, `settings.json`, `workflows/`) is isolated under `claude-code/` — so adapting to another harness means adding a sibling folder, not rewriting the library.

| Primitive   | Claude Code | Codex        | Cursor           |
| ----------- | :---------: | :----------: | :--------------: |
| agents      | ✅ native   | ⚙️ `AGENTS.md` | ⚙️ rules + AGENTS.md |
| skills      | ✅ native   | 📄 as docs    | 📄 as docs        |
| workflows   | ✅ native   | —            | —                |

---

## Extending the library

**Add a skill** → create `skills/<theme>/<name>/SKILL.md` with `name` + `description` in the frontmatter; put deep content in `references/` and link it from the `## Reference Files` section. The install step flattens it to `~/.claude/skills/<name>/`, so `<name>` must stay unique across the whole tree.

**Add an agent** → create `agents/<theme>/<name>.md` with `name`, `description`, `tools` (least-privilege) and a `skills:` list. Discovery is recursive, so the theme is purely organizational — `<name>` (frontmatter) must still be unique across the whole tree.

**Add a workflow** → create `claude-code/workflows/<name>.ts` following the Workflow API (`meta`, phases, `agent()` / `parallel()` / `pipeline()`).

Then sync (see [Quick start](#quick-start)).

---

## Why

Most tooling promises a smarter assistant. oh-my-harness promises a **portable** one.

Your setup today is welded to one machine and one provider: an MCP tool hardcoded, a path assumed, a service named. Move, and you rebuild. oh-my-harness makes the config outlive the environment — the agents describe intent, the capability table describes the machine, and the two meet at runtime. Clone it on a new laptop, plug four tools into one table, and your whole engineering toolkit is back — same behavior, same standards, same voice.

The library is only as good as the discipline encoded in it. This one encodes portability, progressive disclosure, and a hard code-craft bar — so the investment compounds instead of resetting every time you switch context.

---

## License

Apache License 2.0. See [LICENSE](LICENSE).
