---
version: 1.1.0
name: codex
description: |
  Installs and synchronizes oh-my-harness into Codex. Covers the native Git-backed plugin,
  custom agents, global AGENTS.md managed content, lifecycle hooks, MCP integration checks,
  conflict handling, and post-install validation. Use for first-time Codex setup, sync after a
  repository update, or diagnosis of a partial Codex installation.
type: capability
---

# Codex — Global Installation and Sync

Use the native plugin for shared skills, the Codex-only installation skill, and lifecycle hooks.
Use the versioned adapter under `codex/` for custom agents, global guidance, and machine-local
integrations; do not reinterpret Claude Code files during installation. The installer preserves
user-owned global configuration.

## Install or update the native plugin

```bash
codex plugin marketplace add nelsonfrugeri-tech/oh-my-harness
codex plugin add oh-my-harness@oh-my-harness
codex plugin list
```

Use `codex plugin marketplace upgrade oh-my-harness` to refresh the Git-backed catalog before
installing a newer manifest version. Start a new session after installation or upgrade. Open
`/hooks`, review the bundled commands, and trust their exact definitions; Codex skips new or
changed non-managed hooks until that explicit review is complete.

The commit quality gate requires a second, per-repository opt-in because it executes commands
discovered from the repository. From a checkout whose code you reviewed, run once:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

Trust through `/hooks` authorizes the plugin hook definition. The marker above separately
authorizes repository-controlled format, lint, typecheck, and test commands. Without both, the
gate deliberately defers instead of executing project code.

The plugin-only context hook instructs Codex to run the bundled `explorer` skill directly. When the
global adapter is also present, its custom `context` agent can orchestrate that workflow.

## Install or sync the global adapter

From the repository root, run:

```bash
python3 codex/install.py
python3 codex/install.py --check
```

The installer:

1. links shared and Codex-only skills into `~/.agents/skills/<name>/`, excluding the Claude-only
   installer skill;
2. links Codex custom-agent TOMLs into `~/.codex/agents/`;
3. links the complete adapter at `~/.codex/oh-my-harness`;
4. replaces only the `omh-managed` block inside global `~/.codex/AGENTS.md`;
5. replaces only the managed context hook inside `~/.codex/hooks.json`, preserving unrelated hooks;
6. wires Deja, Graphify, and the official LangChain skills and documentation integrations;
7. reports account-bound integrations that still require human authorization.

Run with `--skip-integrations` when only filesystem artifacts should be synchronized.
Use `--replace-global-agents` only when migrating a confirmed legacy oh-my-harness global file;
the installer creates `AGENTS.md.omh.bak` before replacing it.

## Conflict policy

Never overwrite a user-owned file or directory where a managed symlink is expected. Stop and show
the exact path. The user must decide whether to preserve, move, or replace it. Managed text blocks
and managed hook entries are safe to update because their ownership markers are explicit.

Before changing an editable global file, the installer creates a one-time `.omh.bak` sibling.

## Validation

`--check` is read-only and must pass before reporting the setup complete. Then verify the active
MCP inventory through the Codex MCP configuration surface. Account-bound providers may remain
pending, but the report must distinguish missing software from missing authorization.

## Repository conduct

This repository is the source of truth. Installation writes only to Codex global state and the
personal skills directory. Temporary diagnostics belong in `/tmp`, never in the repository.
