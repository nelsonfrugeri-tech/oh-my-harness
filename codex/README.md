# Codex adapter

This directory is the versioned Codex-native adapter for oh-my-harness. It prevents machine setup
from depending on a future agent translating Claude Code configuration again.

## Bootstrap a machine

Clone the repository and run from its root:

```bash
python3 codex/install.py
python3 codex/install.py --check
```

The operation is idempotent. Repository-backed artifacts are symlinked so a later `git pull`
updates them immediately. Editable global files use managed sections so personal configuration is
preserved.

When migrating a known legacy oh-my-harness `~/.codex/AGENTS.md` that predates ownership markers,
run the first installation with `--replace-global-agents`. The original file is preserved as
`AGENTS.md.omh.bak`. Do not use this flag for an unrelated personal instruction file.

## Installed surfaces

| Source | Global destination | Strategy |
| --- | --- | --- |
| shared `skills/**/<name>/` and `codex/skills/**/<name>/` | `~/.agents/skills/<name>/` | Flattened directory symlink |
| `codex/agents/*.toml` | `~/.codex/agents/*.toml` | File symlink |
| `codex/AGENTS.md` | managed block in `~/.codex/AGENTS.md` | Merge |
| `codex/hooks.json` | managed entries in `~/.codex/hooks.json` | Merge |
| shared `hooks/*.sh` | `~/.codex/hooks/<name>.sh` | File symlink |
| `codex/` | `~/.codex/oh-my-harness` | Directory symlink |
| generated ownership manifest | `~/.codex/oh-my-harness-links.json` | Atomic rewrite |

The installer preserves unrelated hooks, machine-specific capability mappings, global
instructions, MCP servers, plugins, and personal skills. It removes stale symlinks only when the
ownership manifest proves they were created by a previous run, and stops instead of replacing an
unmanaged path.

## MCP integrations

The installer wires Deja when its CLI is present and registers Graphify when its MCP executable can
be resolved.

Run `python3 codex/install.py --skip-integrations` to synchronize only filesystem artifacts.

## Validation

```bash
python3 codex/install.py --check
codex mcp list
```

Start a new Codex session after installation so global agents, skills, hooks, and instructions are
rediscovered.

The installed global guidance applies the shared software-evidence contract to engineering work.
Use the `evidence` skill for claim provenance and decision mechanics, and delegate a read-only audit
to `evidence-reviewer` when a decision is consequential, difficult to reverse, or controlled by an
uncertain metric or causal claim.
