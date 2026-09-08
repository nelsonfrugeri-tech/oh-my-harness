---
version: 2.2.0
name: claude-code
description: |
  Runbook for installing the oh-my-harness library in Claude Code **as a native plugin**.
  Covers: the `.claude-plugin/plugin.json` manifest (shared skills in `core/skills/` and
  specific skills in `harness/claude/skills/`), agents declared from `harness/claude/agents/`,
  the plugin hooks in `harness/claude/hooks/hooks.json`
  with `${CLAUDE_PLUGIN_ROOT}`, the marketplace for versioned Git distribution (version,
  ref, sha), the two surfaces the plugin **does not** cover (`CLAUDE.md` and `permissions` in
  `settings.json`), and migration from the old symlink layout—including removal of duplicate hooks
  that would fire twice. Also covers the third-party plugins routed by the agents and not vendored
  here: `langchain-skills` and `langchain-mcp` (marketplace
  `langchain-ai/langchain-plugins`), routed by `ai-engineer`, `architect`, and `software-engineer`;
  and `evals` (marketplace `ai-evals-course`), routed by `ai-engineer`.
  Use when: (1) installing the library on a machine, (2) updating after a push,
  (3) migrating from symlink sync to the plugin, (4) diagnosing a skill/agent/hook that does not
  load, or (5) installing or diagnosing third-party plugins.
  Triggers: install, synchronize, sync, setup, configure harness, update library, plugin,
  langchain, langgraph, deep agents, evals, error analysis, llm-as-judge.
type: capability
---

# Claude Code — Native Plugin Installation

The library is a **Claude Code plugin**. Installation, updates, versioning, and namespacing
are handled by the harness itself; there is no longer a symlink runbook to execute manually.

## Rules of Conduct (this repository is a SOURCE, not a development project)

1. **Do not develop this repository.** Do not create, edit, or scaffold files here
   — **except** when the user **explicitly** asks to change the library itself.
2. **Harness configuration belongs in the global environment** — never inside this repository or
   any project.
3. **Never pollute a project with files that are not part of the product** — one-off scripts,
   analysis `.md` files, scratch data, and intermediate output belong in `/tmp` or the session scratchpad.
4. **Never do anything the user did not explicitly request.**
5. **Do nothing destructive without explicit confirmation.**

---

## Step 1 — Install

Three paths, from most permanent to most ephemeral:

```bash
# Git distribution (the normal path)
claude plugin marketplace add nelsonfrugeri-tech/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness

# from a local clone
claude plugin marketplace add /path/to/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness

# development: load the repository directly without installing
claude --plugin-dir /path/to/oh-my-harness
```

Confirm the state:

```bash
claude plugin list                      # Status must be "✔ enabled"
claude plugin details oh-my-harness@oh-my-harness
```

`details` prints the inventory and the **projected context cost**. Two points about the output
that prevent surprises:

- **Agents are declared explicitly.** Their manifests live in themed subfolders under
  `harness/claude/agents/` and load with the scoped name `oh-my-harness:<theme>:<name>`.
- **`Hooks` consume no context** — they run in the harness, outside the model's context window.

## Step 2 — What the plugin DOES NOT cover

A plugin does not provide global instructions or user preferences. These two surfaces still
require manual installation, which is what the source's `harness/claude/` still supports:

| Surface | Why | What to do |
| --- | --- | --- |
| `~/.claude/CLAUDE.md` | A plugin cannot provide global instructions—only skills, agents, and hooks | **Merge** `harness/claude/CLAUDE.md`, preserving the machine capability table and any local block |
| `~/.claude/settings.json` → `permissions` | A plugin's `settings.json` accepts only `agent` and `subagentStatusLine` | Merge `harness/claude/settings.json`, preserving `model`, `theme`, `autoMode`, and user permissions |

**Hooks no longer go in `settings.json`.** They belong to the plugin. See Step 3.

## Step 3 — Migrate from the old layout

On a machine that previously used symlink sync, the old content **coexists** with the plugin and
causes duplication. Diagnose before removing anything:

```bash
find ~/.claude/agents ~/.claude/skills ~/.claude/hooks -maxdepth 2 -type l -exec ls -l {} \; 2>/dev/null
```

1. **Duplicate hooks are the most visible symptom.** If `~/.claude/settings.json` still has the
   `PreToolUse → quality-gate.sh` handler, it fires **alongside** the plugin handler and the quality
   gate runs twice. Remove **only** that handler; preserve third-party handlers for the same event
   (Deja installs `SessionStart`, `PreCompact`, and `UserPromptSubmit`). A manually registered
   `SessionStart` handler pointing to this library comes from an old installation and must also be
   removed: the plugin now provides the content-free KB pointer, and retaining the manual copy would
   run it twice.
2. **Agent and skill symlinks** pointing to this repository are now redundant: the plugin provides
   the same components under a namespace. Remove them **one at a time and with confirmation**—never
   in bulk. Skills and agents installed by other tools (`deja-history`, and any external capability
   provider) **are not** orphaned and must not be removed.
3. **`~/.claude/CLAUDE.md` and `permissions` remain**—they belong to Step 2 and are not residue.

## Step 4 — Capabilities / MCP

The plugin provides behavior; the machine owns the **capability table**, which lives in
`~/.claude/CLAUDE.md`:

1. List MCP servers with `claude mcp list` (or by reading `~/.claude.json`).
2. Propose the mapping: Git hosting → `code-host`; CI → `ci`; graph → `code-graph`;
   session memory → `session-memory`; no provider → leave it **empty**.
3. Show the change as a diff and apply it after confirmation.
4. Use the server prefix (`mcp__github__*`), never an individual tool.

### Optional — `code-graph` provider

The `code-graph` capability remains in the table, but its provider is **not** vendored here. The
table row is a claim about an **installed and registered MCP server**, never about the skill:
`graphify install --platform claude` copies the skill and writes instructions to `CLAUDE.md`; it
does not register an MCP server. These are three distinct steps:

```bash
pipx install 'graphifyy[mcp]'
graphify install --platform claude
claude mcp add --env GRAPHIFY_PROJECT_DIR=. graphify -- graphify-mcp
```

The `[mcp]` extra is not decorative: in `graphifyy` 0.9.27, the `mcp` dependency is included only
through that extra, and the published server executable is `graphify-mcp`—`graphify-mcp-server`
does not exist.

`graphify install --platform claude` **writes to `CLAUDE.md`**, where `omh` also maintains a
managed block. After running it, reconcile the file: reread `~/.claude/CLAUDE.md`, confirm that the
`omh` block remains intact, and reapply Step 2 if it was displaced.

Add the provider row (`mcp__graphify__*`) to the capability table **only** after the server is
registered and responding: confirm with `claude mcp list` and a real call. A table row without a
registered server is a phantom provider—the `code-graph` capability fails while the configuration
claims it exists.

## Step 5 — Third-party plugins routed by the agents

Some agents in this library route to skills that **are not ours**: they live in third-party
marketplaces and are never vendored here. Their content is maintained upstream and arrives through
the normal plugin update flow, with no work in this repository—in exchange, without the plugins
installed, the prose in those agents points to skills that do not exist.

Install the two marketplaces below. For both, disclose the always-on cost to the user instead of
installing silently: these tokens are added to **every** session, even when the topic does not arise.

### LangChain, LangGraph, and Deep Agents

```bash
claude plugin marketplace add langchain-ai/langchain-plugins
claude plugin install langchain-skills@langchain-plugins
claude plugin install langchain-mcp@langchain-plugins
```

Routed by the *LangChain Ecosystem* section of the `ai-engineer`, `architect`, and `software-engineer`
agents. Measured with `claude plugin details` in the reference installation:

| Plugin | Provides | Always-on cost |
| --- | --- | --- |
| `langchain-skills` | 22 LangChain, LangGraph, and Deep Agents skills | ~2.1k tokens per session |
| `langchain-mcp` | 2 MCP servers: `langchain-docs` and `langchain-reference` | ~0 (schema resolved at runtime) |

The ~2.1k is the cost of keeping all 22 descriptions available for routing; each skill body loads
only when invoked.

The same marketplace publishes `langsmith-skills` and `langsmith-mcp`, which we **do not** install
by default: they require a LangSmith account and OAuth authorization. Install them from the same
marketplace if the user has an account and asks for them.

### LLM Evaluation

```bash
claude plugin marketplace add ai-evals-course/evals-skills
claude plugin install evals@ai-evals-course
```

Routed by the *LLM Evaluation (evals)* section of the `ai-engineer` agent. It provides **8 skills**
for error analysis, LLM-as-judge, evaluator calibration, and RAG evaluation, at an always-on cost
of **~862 tokens**, with no MCP server. The marketplace name (`ai-evals-course`) differs from the
repository name (`evals-skills`)—the installation ID uses the marketplace name.

> Observed in both installations: `marketplace add` clones over **SSH** (`git@github.com:…`). On a
> machine without SSH access to GitHub, the step fails there—diagnose the clone before suspecting
> the marketplace.

Verification: `claude plugin list` shows all three as `✔ enabled`; `claude plugin details <id>`
lists the skills (22 and 8 in the reference installation—upstream may add more); and, in a new
session, `/langchain-skills:ecosystem-primer` and `/evals:evals-start` respond. Routing requires
`evals >= 0.3.1`; old installations that still expose `/evals:start` must run
`claude plugin update evals@ai-evals-course` and restart Claude Code.

## Step 6 — Update

```bash
claude plugin marketplace update oh-my-harness
claude plugin update oh-my-harness@oh-my-harness
```

The user receives a new version only when `version` in `plugin.json` is incremented—this makes the
update a decision rather than a side effect of `git pull`. To pin an exact version, the marketplace
accepts `ref` (branch/tag) and `sha` (commit); when both are present, `sha` takes precedence.

`CLAUDE.md` and `permissions` **are not** updated by the plugin: when the source changes, redo the
merge from Step 2.

## Step 7 — Verification

### Package migration: 2.0.0 to 2.0.1

Agent and hook paths move into `harness/claude/`; shared scripts move into `core/hooks/`.
After reinstalling, start a new session and inspect plugin loading and hook execution again.
Review any approval requested by Claude for the changed package. Codex's `/hooks` trust
requirement applies to Codex separately; do not assume both runtimes share a trust mechanism.
Manually created symlinks to old source paths are not owned by the installer: inspect and
migrate them individually while preserving user-owned files.

```bash
claude plugin validate <source>    # manifest and marketplace
claude plugin list                 # enabled, with no load errors
```

Then open a **new session** and confirm by observation, not assumption:

- a plugin skill responds at `/oh-my-harness:<name>`;
- an agent appears as `oh-my-harness:<theme>:<name>`;
- `/context` lists `CLAUDE.md` under **Memory files**.

> `claude plugin validate` validates the manifests, **not** loading. A duplicate-hook or path error
> appears in `plugin list` only after installation. Run both commands.

---

## Final report

Report: installed version, actual skill and agent counts (from execution, not the counter), hook
state, what was migrated from the old layout, what was preserved because it belongs to a third
party, and what remains pending.
