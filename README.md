<div align="center">

# oh-my-harness

**A portable, harness-agnostic library of expert agents, skills, and workflows for AI coding assistants.**

Write the config once. Plug the tools per machine. Run it on Claude Code today — and on Codex or Cursor tomorrow — without changing a line.

[![License](https://img.shields.io/badge/license-Apache%202.0-4CAF50?style=flat-square)](LICENSE)
[![Harness](https://img.shields.io/badge/harness-Claude%20Code-8A63D2?style=flat-square)](https://claude.com/claude-code)
[![Agents](https://img.shields.io/badge/agents-8-2496ED?style=flat-square)](#whats-inside)
[![Skills](https://img.shields.io/badge/skills-18-DC5F00?style=flat-square)](#whats-inside)
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
- [Portability across harnesses](#portability-across-harnesses)
- [Extending the library](#extending-the-library)
- [Why](#why)
- [License](#license)

---

## How it works

This repository is the **source**. You sync it into your harness's **global state** (`~/.claude`), and agents resolve their tools per machine through a single capability table.

```
┌────────────────────────────────────────────────────────────┐
│  oh-my-harness  ·  SOURCE (this git repo)                  │
│                                                            │
│   agents/            skills/            claude-code/       │
│   expert subagents   knowledge base     CLAUDE.md          │
│                      (SKILL.md +        SETUP.md           │
│                       references/)      workflows/         │
└───────────────────────────┬────────────────────────────────┘
                            │   "read INSTRUCTIONS.md and sync"
                            │        (or ./install.sh)
                            ▼
┌────────────────────────────────────────────────────────────┐
│  ~/.claude/  ·  GLOBAL harness state                       │
│   agents/    skills/    workflows/    CLAUDE.md            │
└───────────────────────────┬────────────────────────────────┘
                            │   capability plug (per machine)
               ┌────────────┴─────────────┐
               ▼                          ▼
      code-host → mcp__github__*   code-host → mcp__gitlab__*
      (personal machine)           (work machine)
```

- **agents / skills / workflows** are symlinked into `~/.claude/` — a `git pull` on the source updates them everywhere.
- **CLAUDE.md** carries the timeless rules and the per-machine capability table.
- **SETUP.md** is the runbook the harness executes to sync (see [Quick start](#quick-start)).

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

The non-negotiable code-quality rules — total typing, immutability, small cohesive units, guard clauses over nesting, a design pattern instead of `if/elif` chains, a final quality gate — live in [`skills/implement/references/code-craft.md`](skills/implement/references/code-craft.md) as a **single source of truth**, referenced by `implement` and reused by `review`.

### Language contract

Instructional prose is **pt-BR**; code, comments, docstrings, and technical terms stay **English**. You talk to the harness in your language; what ships to a codebase is written in the code's language.

---

## Quick start

```bash
git clone https://github.com/nelsonfrugeri-tech/oh-my-harness.git
cd oh-my-harness
```

Then **ask the harness to sync** — it reads [`INSTRUCTIONS.md`](INSTRUCTIONS.md), runs the [`claude-code/SETUP.md`](claude-code/SETUP.md) runbook, and resolves everything interactively (symlink the library, diff the configs, detect local MCPs and wire the capability table, handle orphans):

> _"Read INSTRUCTIONS.md and sync this library with my ~/.claude."_

Prefer a deterministic one-shot? Use the installer:

```bash
./install.sh                        # symlink agents/ and skills/ into ~/.claude/
CLAUDE_HOME=/path ./install.sh      # custom home
```

Finally, edit the **Ambiente & Tools** table in `~/.claude/CLAUDE.md` to plug this machine's tools.

---

## What's inside

### Agents

| Agent         | Role                                             | Model  |
| ------------- | ------------------------------------------------ | ------ |
| `architect`   | System design, ADRs, C4, trade-offs, API design  | opus   |
| `developer`   | Implementation, bug fixes, refactoring, testing  | sonnet |
| `ai-engineer` | LLM/RAG/embeddings, data pipelines, evaluation    | sonnet |
| `qa`          | Test strategy, E2E, performance, accessibility   | sonnet |
| `sre`         | Observability, SLO/SLI, incident response        | sonnet |
| `tech-pm`     | User stories, backlog, roadmap, PRDs             | sonnet |
| `explorer`    | Deep repo analysis → `context.md`                | opus   |
| `context`     | Loads the project's living context into a session| sonnet |

### Skills

**Knowledge (languages & domains):** `python` · `typescript` · `ai-engineer` · `api-design` · `frontend-ui` · `security` · `observability`

**Capability (method & process):** `implement` · `design` · `test` · `review` · `research` · `operate` · `manage` · `environment` · `ci-cd`

**Command & workflow:** `feature` · `drink-context`

Each skill ships a `SKILL.md` and, where applicable, a `references/` folder with the deep dives.

### Workflows

| Workflow         | What it does                                                                       |
| ---------------- | ---------------------------------------------------------------------------------- |
| `create-feature` | End-to-end pipeline: user story → dev → parallel `qa`+`sre` loop → PR via `code-host` |

---

## Portability across harnesses

`agents/` and `skills/` are the reusable base. Everything Claude-Code-specific (`CLAUDE.md`, `settings.json`, `workflows/`, `SETUP.md`) is isolated under `claude-code/` — so adapting to another harness means adding a sibling folder, not rewriting the library.

| Primitive   | Claude Code | Codex        | Cursor           |
| ----------- | :---------: | :----------: | :--------------: |
| agents      | ✅ native   | ⚙️ `AGENTS.md` | ⚙️ rules + AGENTS.md |
| skills      | ✅ native   | 📄 as docs    | 📄 as docs        |
| workflows   | ✅ native   | —            | —                |

---

## Extending the library

**Add a skill** → create `skills/<name>/SKILL.md` with `name` + `description` in the frontmatter; put deep content in `references/` and link it from the `## Reference Files` section.

**Add an agent** → create `agents/<name>.md` with `name`, `description`, `tools` (least-privilege) and a `skills:` list.

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
