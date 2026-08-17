# Codex adapter

This directory is the versioned Codex-native adapter for oh-my-harness. It prevents machine setup
from depending on a future agent translating Claude Code configuration again.

## Bootstrap a machine

Clone the repository and run from its root:

```bash
python3 codex/install.py
python3 codex/install.py --check
```

`CODEX_HOME` and `AGENTS_HOME` are honored when set; otherwise the defaults are `~/.codex` and
`~/.agents`. Pass both paths explicitly in migration automation so the target is auditable.

The operation is idempotent. Repository-backed artifacts are symlinked so a later `git pull`
updates them immediately. Editable global files use managed sections so personal configuration is
preserved.

When migrating a known legacy oh-my-harness `~/.codex/AGENTS.md` that predates ownership markers,
run the first installation with `--replace-global-agents`. The original file is preserved as
`AGENTS.md.omh.bak`. Do not use this flag for an unrelated personal instruction file.

Legacy v1 installations may also have regular agent TOMLs owned by
`agents/.oh-my-harness-managed.json`. Migrate only those manifest-owned files with the explicit
`--migrate-legacy-agents` flag. Each original is moved to a timestamped backup before its managed
symlink is installed; unrelated agent TOMLs are never touched.

Machine-only instructions belong in `$CODEX_HOME/AGENTS.local.md`. When present, the installer
composes that file after the portable rules inside the managed block. Keep credentials out of both
files; use the local overlay only for provider mappings and private environment policy.

## Installed surfaces

| Source | Global destination | Strategy |
| --- | --- | --- |
| shared `skills/**/<name>/` and `codex/skills/**/<name>/` | `~/.agents/skills/<name>/` | Flattened directory symlink |
| `codex/agents/*.toml` | `~/.codex/agents/*.toml` | File symlink |
| `codex/AGENTS.md` | managed block in `~/.codex/AGENTS.md` | Merge |
| `codex/hooks.json` | managed entries in `~/.codex/hooks.json` | Merge |
| shared `hooks/*.sh` | `~/.codex/hooks/<name>.sh` | File symlink |
| `codex/rules/*.rules` | `~/.codex/rules/<name>.rules` | File symlink |
| `codex/` | `~/.codex/oh-my-harness` | Directory symlink |
| generated ownership manifest | `~/.codex/oh-my-harness-links.json` | Atomic rewrite |

The installer preserves unrelated hooks, machine-specific capability mappings, global
instructions, MCP servers, plugins, and personal skills. It removes stale symlinks only when the
ownership manifest proves they were created by a previous run, and stops instead of replacing an
unmanaged path.

## MCP integrations

The installer registers Deja without indexing transcripts, registers Graphify when either the
current `graphify-mcp` executable or the legacy server name can be resolved, registers the official
open-source Excalidraw MCP App endpoint, and adds the public read-only X Docs MCP. Excalidraw scene
creation works through standard MCP tools, while inline app rendering or model-side visual
inspection may remain degraded until the active Codex client supports the full MCP Apps extension.
Transcript indexing remains a separate explicit user decision. The
authenticated X API MCP remains opt-in because it requires `xurl`, explicit OAuth approval, and a
paid X API plan. Every Codex subprocess receives the selected `CODEX_HOME`.

Run `python3 codex/install.py --skip-integrations` to synchronize only filesystem artifacts.

Importing legacy Claude MCP definitions is also explicit and never part of normal installation:

```bash
python3 codex/import_mcps.py --dry-run
python3 codex/import_mcps.py --check
python3 codex/import_mcps.py
```

The core installer does not import a TOML parser. Python 3.11 and newer use the standard library
for the opt-in importer. On older Python versions, bootstrap the pinned full parser explicitly:

```bash
python3 -m pip install --requirement codex/requirements-mcp-import.txt
```

Without that optional dependency, the importer exits before reading or changing `config.toml` and
prints the bootstrap command. It never installs packages automatically and never falls back to a
partial text parser.

The importer preserves existing names, compares HTTP transports by URL and stdio transports by
`command + args + cwd`, creates a permission-restricted backup before writing, and never prints
environment values.

## Validation

```bash
python3 codex/install.py --check
codex mcp list
```

Start a new Codex session after installation so global agents, skills, hooks, and instructions are
rediscovered.
