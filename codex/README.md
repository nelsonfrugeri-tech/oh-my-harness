# Codex adapter

This directory is the versioned Codex-native adapter for oh-my-harness. It prevents machine setup
from depending on a future agent translating Claude Code configuration again.

## Install the native plugin

Install shared skills and lifecycle hooks directly from the Git-backed marketplace:

```bash
codex plugin marketplace add nelsonfrugeri-tech/oh-my-harness
codex plugin add oh-my-harness@oh-my-harness
codex plugin list
```

Start a new Codex session so the plugin capabilities are discovered. Then open `/hooks`, review
the bundled commands, and trust their exact definitions. Codex skips new or changed non-managed
hooks until that explicit review is complete.

The commit quality gate has a separate per-repository trust because it executes commands discovered
from that repository. From a checkout you have reviewed, opt in once with:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

Hook trust authorizes the plugin hook definition; this repository trust authorizes the discovered
project commands. Without both, the gate deliberately defers and the normal commit flow continues.

The context hook works with the bundled `explorer` skill on a plugin-only installation. The global
adapter additionally provides the custom `context` agent that can orchestrate the same workflow.

## Install the global adapter

The plugin format does not package Codex custom-agent TOMLs, global `AGENTS.md` guidance, or
machine-local MCP configuration. Clone the repository and run the adapter when you need those
additional surfaces:

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
| shared `skills/<name>/` | `~/.agents/skills/<name>/` | Directory symlink |
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

The installer wires Deja when its CLI is present, registers Graphify when its MCP executable can be
resolved, and adds the public read-only X Docs MCP. The authenticated X API MCP remains opt-in
because it requires `xurl`, explicit OAuth approval, and a paid X API plan.

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
