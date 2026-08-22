<div align="center">

# oh-my-harness

**A portable, harness-agnostic library of expert agents, skills, and workflows for AI coding assistants.**

Share the behavior once. Keep harness-native adapters where representation differs. Run the same
library on Claude Code and Codex today.

[![License](https://img.shields.io/badge/license-Apache%202.0-4CAF50?style=flat-square)](LICENSE)
[![Harness](https://img.shields.io/badge/harness-Claude%20Code-8A63D2?style=flat-square)](https://claude.com/claude-code)
[![Harness](https://img.shields.io/badge/harness-Codex-111111?style=flat-square)](https://openai.com/codex/)
[![Agents](https://img.shields.io/badge/agents-13-2496ED?style=flat-square)](#whats-inside)
[![Skills](https://img.shields.io/badge/skills-29-DC5F00?style=flat-square)](#whats-inside)
[![Docs](https://img.shields.io/badge/docs-pt--BR-009C3B?style=flat-square)](#language-contract)

</div>

---

## The problem

Harness config is born coupled. One MCP tool hardcoded here, a `~/.config/...` path there, a reference to a specific service somewhere else. Switch machines — GitHub at home, GitLab at work — or switch assistants, and it breaks. You re-wire the same plumbing on every setup.

**oh-my-harness decouples _what the agent does_ from _which tool it does it with._** The same
`developer` responsibility opens a Pull Request through GitHub on your personal machine and through
GitLab on the company laptop. Harness-native manifests represent that behavior, while only the
machine capability mapping changes providers.

---

## Table of contents

- [How it works](#how-it-works)
- [Core ideas](#core-ideas)
  - [Capabilities — the tool plug](#capabilities--the-tool-plug)
  - [Progressive disclosure](#progressive-disclosure)
  - [Evidence-driven decisions](#evidence-driven-decisions)
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

This repository is the **source**. Shared skills and behavior stay harness-neutral; each sibling
adapter owns the manifests, hooks, global guidance, and lifecycle integration required by its
harness. Capabilities are resolved through that harness's machine-local table.

```
┌───────────────────────────────────────────────────────────────────┐
│  oh-my-harness · SOURCE (this git repo)                            │
│                                                                     │
│  shared behavior                 harness adapters                    │
│  ├── skills/                     ├── claude-code/                    │
│  ├── hooks/                      │   CLAUDE.md · settings · workflow │
│  └── agents/ (Claude manifests)  └── codex/                          │
│                                      AGENTS.md · TOML agents · hooks │
└──────────────────────────────┬──────────────────────────────────────┘
                                │ harness-native installer
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
   ~/.claude/ global state                ~/.codex/ + ~/.agents/
   Markdown agents · workflows            TOML agents · shared skills
   CLAUDE.md · settings/hooks              AGENTS.md · hooks · MCPs
                                │  capability plug (per machine)
                   ┌────────────┴─────────────┐
                   ▼                           ▼
          code-host → mcp__github__*   code-host → mcp__gitlab__*
          (personal machine)           (work machine)

┌───────────────────────────────────────────────────────────────────┐
│  ~/knowledge-base/ · outside any repo · an OKF v0.2 bundle          │
│  <domain>/context.md — living context (`context` agent on each      │
│    session start; `explorer` runs only on FULL/DELTA)               │
│  <domain>/<entity-type>/ — immutable notes (`knowledge-base` agent  │
│    → kb-write/kb-retrieval), indexed in local Qdrant via BGE-M3     │
│  <domain>/sessions/ — living session records (`kb-session`),        │
│    pointing at the harness's raw transcripts for deep search        │
└───────────────────────────────────────────────────────────────────┘
```

- **agents** share responsibilities and skill dependencies, while their executable manifests stay
  harness-native: Claude Markdown under `agents/`, Codex TOML under `codex/agents/`.
- **skills** are the shared semantic layer and are flattened by each installer to the discovery
  location required by that harness.
- **global guidance and capability tables** live in `claude-code/CLAUDE.md` and `codex/AGENTS.md`;
  their common rules must remain semantically aligned, not byte-identical.
- The agent **`claude-code`** (backed by the `claude-code` skill) is the runbook the harness
  runs to sync (see [Quick start](#quick-start)).
- The agent **`context`**, invoked on every `SessionStart`, keeps a living knowledge base of
  the *current* project at `~/knowledge-base/work/projects/{project}/context.md` — built and updated by the
  `explorer` skill, entirely outside the project's own working tree.
- The agent **`knowledge-base`** manages the persistent knowledge base: infra (local Qdrant +
  BGE-M3 embeddings via `kb-infra`), immutable notes (`kb-write`), 3-step retrieval
  (`kb-retrieval`) and the harness's session memory — living session records plus deep search
  inside raw transcripts (`kb-session`) — see [Knowledge base](#knowledge-base).
- The agent **`x-social`** reads and publishes on X (Twitter) through the `social-x` capability.
  The library hosts no server and stores no credentials: X publishes its own hosted MCP, and
  each user's account is resolved at runtime via OAuth — so the same files work on any machine,
  for any account, on any MCP-speaking harness.
- The agent **`site`** turns cited technical analysis into a self-contained visual report outside
  the source repository and exposes it only through an explicitly configured `tunnel` capability.

---

## Core ideas

### Capabilities — the tool plug

Agents and skills reference **abstract capabilities**, never a concrete tool. Each harness adapter
owns one machine-local capability table (`claude-code/CLAUDE.md` or `codex/AGENTS.md`). Change the
environment, change only the active harness's table.

| Capability  | Role                                   | Example per machine        |
| ----------- | -------------------------------------- | -------------------------- |
| `code-host`  | Pull/Merge Requests, issues           | `mcp__github__*` / GitLab  |
| `ci`         | CI/CD pipelines                       | GitHub Actions / GitLab CI |
| `memory`     | Persistent project notes (optional)   | any memory MCP             |
| `web`        | Search and fetch                      | `WebSearch`, `WebFetch`    |
| `code-graph` | Query a built codebase knowledge graph | `mcp__graphify__*`        |
| `social-x`   | Read and publish on X (Twitter)       | X's hosted MCP via `xurl`  |
| `tunnel`     | Temporary authenticated site exposure | cloudflared / ngrok / equivalent |

### Progressive disclosure

Each skill is a lean `SKILL.md` (overview + when to use) that points to `references/` loaded **on demand**. Context only pays for the depth a task actually needs — the ~140 reference files stay out of the window until required.

### Evidence-driven decisions

Software work uses a shared evidence contract across Claude Code and Codex. Material claims are
classified as verified facts, derived results, inferences, hypotheses, estimates, unknowns, or
decisions. Quantitative claims carry reproducible provenance, and material decisions record
alternatives, uncertainty, falsification, and rollback conditions. The `evidence` skill provides
the detailed protocol, while the read-only `evidence-reviewer` independently audits consequential
claims without turning routine work into ceremony.

### code-craft — inviolable rules

The non-negotiable code-quality rules — total typing, immutability, small cohesive units, guard clauses over nesting, a design pattern instead of `if/elif` chains, a final quality gate — live in [`skills/implement/references/code-craft.md`](skills/implement/references/code-craft.md) as a **single source of truth**, referenced by `implement` and reused by `review`.

### Language contract

Instructional prose is **pt-BR**; code, comments, docstrings, and technical terms stay **English**. You talk to the harness in your language; what ships to a codebase is written in the code's language.

---

## Quick start

**Claude Code** installs the library as a native plugin — no clone required:

```bash
claude plugin marketplace add nelsonfrugeri-tech/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness
claude plugin list        # Status: ✔ enabled
```

Skills arrive namespaced (`/oh-my-harness:review`), agents as
`oh-my-harness:<theme>:<name>`, and the `SessionStart` and commit-gate hooks come with them.
Updates are a decision, not a side effect of `git pull`: users receive a new version only when
`version` in the manifest is bumped, and a marketplace entry can pin `ref` or an exact `sha`.

Two surfaces a plugin cannot provide — global instructions and user preferences — still install
by merge: `claude-code/CLAUDE.md` into `~/.claude/CLAUDE.md`, and the `permissions` block of
`claude-code/settings.json`. Ask the `claude-code` agent to do it, or follow its skill.

**Codex** also installs the shared library as a native plugin — no clone required:

```bash
codex plugin marketplace add nelsonfrugeri-tech/oh-my-harness
codex plugin add oh-my-harness@oh-my-harness
codex plugin list
```

Start a new Codex session, open `/hooks`, review the plugin-bundled commands, and trust the exact
definitions before relying on them. Codex skips new or changed non-managed hooks until this review
is complete.

The commit gate has an additional per-repository trust because its discovered quality commands are
repository-controlled. From a checkout you have reviewed, opt in once:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

The `/hooks` decision trusts the plugin hook; this marker separately trusts the current Git
repository. Without both, the gate deliberately defers and does not run project commands.

The native plugin supplies shared skills, the Codex installation skill, and lifecycle hooks. The
context hook can run the shared `explorer` skill directly; installing the optional adapter adds the
custom `context` agent that can orchestrate it. Codex custom agents, global
`AGENTS.md` guidance, and machine-local MCP integrations are not plugin components, so install the
adapter from a clone when you need those additional surfaces:

```bash
git clone https://github.com/nelsonfrugeri-tech/oh-my-harness.git
cd oh-my-harness
python3 codex/install.py
python3 codex/install.py --check
```

On a brand-new machine, [`INSTRUCTIONS.md`](INSTRUCTIONS.md) is the bootstrap entrypoint.

Finally, configure the capability table in the active harness's managed global guidance. From then
on, every session start loads the project snapshot and requests `context` FULL or DELTA analysis
when required, maintaining the living knowledge base at
`~/knowledge-base/work/projects/{project}/context.md`.

---

## What's inside

### Agents

Canonical Claude manifests are grouped under `agents/<theme>/`; Codex-native representations live
under `codex/agents/`. Both adapters preserve the responsibilities in this catalog.

| Theme       | Agent         | Role                                                | Model  |
| ----------- | ------------- | ---------------------------------------------------- | ------ |
| `engineers` | `architect`   | System design, ADRs, C4, trade-offs, API design       | opus   |
| `engineers` | `developer`   | Implementation, bug fixes, refactoring, testing       | sonnet |
| `engineers` | `ai-engineer` | LLM/RAG/embeddings, data pipelines, evaluation         | sonnet |
| `engineers` | `qa`          | Test strategy, E2E, performance, accessibility        | sonnet |
| `engineers` | `sre`         | Observability, SLO/SLI, incident response              | sonnet |
| `engineers` | `tech-pm`     | User stories, backlog, roadmap, PRDs                   | sonnet |
| `engineers` | `evidence-reviewer` | Read-only audit of software claims, metrics, and decisions | opus |
| `harness`   | `claude-code` | Installs/syncs the library into `~/.claude`             | sonnet |
| `tools`     | `context`     | Loads/refreshes the project's living knowledge base at `~/knowledge-base/work/projects/{project}/context.md` | sonnet |
| `tools`     | `knowledge-base` | Manages the knowledge base: infra (Qdrant + BGE-M3), immutable notes, 3-step retrieval, session memory + deep search | sonnet |
| `tools`     | `graphify`    | Builds and queries a codebase knowledge graph (`graphify-out/`) | opus   |
| `tools`     | `x-social`    | Reads and publishes on X (Twitter) — writes require explicit confirmation | sonnet |
| `tools`     | `site`        | Creates cited visual analysis sites; exposure requires explicit approval | opus |

### Skills

Skills live directly under `skills/<name>/` because that is the common native-plugin discovery
contract. The catalog below keeps the logical themes without adding another filesystem layer, and
each skill name remains globally unique.

**Knowledge (languages & domains) — `engineers`:** `python` · `typescript` · `ai-engineer` · `api-design` · `frontend-ui` · `security` · `observability`

**Capability (method & process) — `engineers`:** `evidence` · `implement` · `design` · `test` · `review` · `research` · `operate` · `manage` · `environment` · `ci-cd`

**Command & workflow — `engineers`:** `feature`

**Harness tooling — `harness`:** `claude-code` (the sync runbook behind the `claude-code` agent)

**Tools agents — `tools`:** `explorer` (deep repo analysis behind the `context` agent) · `kb-infra` (Qdrant + embedding infra) · `kb-write` (the scribe — immutable notes) · `kb-retrieval` (3-step retrieval: hybrid semantic search → disk navigation → session deep search) · `kb-session` (living session records + deep search inside raw transcripts) · `graphify` (build/query the codebase knowledge graph) · `x-setup` and `x-ops` (X connection and operations) · `site-report` and `site-expose` (cited visual reports and opt-in authenticated exposure). Invoked by the corresponding tool agents, not directly by the user.

Each skill ships a `SKILL.md` and, where applicable, a `references/` folder with the deep dives.

### Workflows

| Workflow         | What it does                                                                       |
| ---------------- | ---------------------------------------------------------------------------------- |
| `create-feature` | Shared feature contract with a Claude TypeScript adapter and Codex-native orchestration |

---

## Knowledge base

Knowledge lives on disk at `~/knowledge-base/` — outside every repo, portable, readable by any
Markdown tool. Qdrant is only a derived index, rebuilt from disk at any time.

```
~/knowledge-base/           # OKF v0.2 bundle — markdown only, syncable across machines
  index.md                  # bundle root: declares okf_version, lists bounded contexts
  person/                   # a bounded context
    people/  finances/      # one folder per entity type
  work/
    ifood/                  # a bounded context
      systems/  teams/  rituals/
    projects/
      <repo>/               # a bounded context
        context.md          # living context: snapshot (rewritten) + append-only timeline
        decisions/
          <date>--<slug>.md # immutable notes: frontmatter (type, knowledge_type, ...) + body
        sessions/
          <id>.json         # living session records: name, description, resume, transcript_path

~/.local/share/omh-kb/      # runtime, OUTSIDE the bundle — derived and rebuildable
  qdrant/                   # local Qdrant volume (docker, port 6333)
  venv/                     # embedding environment
```

The directory tree is a deliberate ontology, not accretion: a **bounded context** (the
`domain` field) holds **one folder per entity type**, and relationships live as markdown
links in the body — never as folders. Every note carries two axes: `type` (the domain
noun, required by OKF) and `knowledge_type` (`decision · event · procedure · reference ·
conversation`).

- **Notes are immutable** — corrections are new notes carrying `supersedes`; the old note stays
  archived. The only edit ever allowed on an existing note is flipping its `status` to
  `deprecated` during a supersede.
- **Provenance is never faked** — every agent-written note carries `generated: {by, at}`;
  `verified: [{by: human:…}]` appears only when the user actually confirmed it. Retrieval
  surfaces the difference instead of hiding it.
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

`skills/`, shared hooks, and agent responsibilities form the reusable base. Claude-specific
representation stays under `agents/` and `claude-code/`; Codex-specific representation stays under
`codex/`. Supporting another harness means adding an adapter, not forcing foreign syntax into the
shared layer.

| Primitive | Claude Code | Codex | Cursor |
| --- | :---: | :---: | :---: |
| agents | ✅ native Markdown | ✅ custom-agent TOML adapter | ⚙️ rules + AGENTS.md |
| skills | ✅ native | ✅ native shared skills | 📄 as docs |
| workflows | ✅ Workflow TypeScript | ✅ portable `feature` orchestration | — |
| hooks | ✅ native plugin | ✅ native plugin (trust required) + adapter | — |
| global rules | ✅ `CLAUDE.md` | ✅ managed global `AGENTS.md` | ⚙️ rules |

Codex native-plugin packaging is defined by [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json)
and [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). The adapter under
[`codex/`](codex/README.md) adds custom agents, managed global guidance, and available MCP
integrations without overwriting unrelated personal configuration.

---

## Extending the library

**Add a skill** → create `skills/<name>/SKILL.md` with `name` + `description` in the frontmatter;
put deep content in `references/` and link it from the `## Reference Files` section. Keep `<name>`
unique across the whole tree so both native plugin hosts expose the same stable namespace.

**Add an agent** → define its shared responsibility and Claude manifest under `agents/<theme>/`,
then add the equivalent Codex TOML under `codex/agents/`. Keep behavior aligned while preserving
each harness's native schema and tool-binding rules.

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
