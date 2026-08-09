---
version: 1.0.0
name: codex
description: |
  Installs and synchronizes oh-my-harness into Codex global state. Covers personal skills,
  custom agents, global AGENTS.md managed content, lifecycle hooks, MCP integration checks,
  conflict handling, and post-install validation. Use for first-time Codex setup, sync after a
  repository update, or diagnosis of a partial Codex installation.
type: capability
---

# Codex — Global Installation and Sync

Use the versioned adapter under `codex/`; do not reinterpret Claude Code files during installation.
The installer is the executable source of truth and preserves user-owned global configuration.

## Install or sync

From the repository root, run:

```bash
python3 codex/install.py
python3 codex/install.py --check
```

The installer:

1. links shared skills into `~/.agents/skills/<name>/`, excluding the Claude-only installer skill;
2. links Codex custom-agent TOMLs into `~/.codex/agents/`;
3. links the complete adapter at `~/.codex/oh-my-harness`;
4. replaces only the `omh-managed` block inside global `~/.codex/AGENTS.md`;
5. replaces only the managed context hook inside `~/.codex/hooks.json`, preserving unrelated hooks;
6. wires Deja and supported MCP integrations when their executables are available;
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
