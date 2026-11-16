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

When upgrading from 2.0.0 to 2.0.1, review the hooks again: the descriptor and command paths
move into `harness/codex/hooks/` and `core/hooks/`. Previous trust must not be assumed to carry
over. Verify the PR gate in `/hooks` before relying on it.
`install.py --check` checks the global adapter files, not runtime hook trust.
It checks expected and recorded OMH assets, not every third-party skill directory. If the link
manifest is lost, restore a known-good backup or inspect conflicting links individually before
migrating them; their ownership cannot be inferred safely from a familiar filename.

Older installations made with relative `--codex-home` or `--agents-home` arguments may have
relative targets in `oh-my-harness-links.json`. Those manifests now fail validation before any
changes. They do not record the original working directory, so the installer cannot safely
infer absolute targets during an upgrade. Back up the manifest, establish the original install
directory, and review each target and live symlink before converting those records to absolute
paths. If that directory is unknown, preserve the conflicting links for individual inspection.
New CLI installations normalize both home arguments before recording ownership.

The PR quality gate has a separate per-repository trust because it executes commands discovered
from that repository. From a checkout you have reviewed, opt in once with:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

Hook trust authorizes the plugin hook definition; this repository trust authorizes the discovered
project commands. Without both, the gate deliberately defers and the normal PR flow continues.


## Install the global adapter

The plugin format does not package Codex custom-agent TOMLs, global `AGENTS.md` guidance, or
machine-local MCP configuration. Clone the repository and run the adapter when you need those
additional surfaces:

Clone the repository and run from its root:

```bash
python3 installers/codex/install.py
python3 installers/codex/install.py --check
```

The global adapter requires Codex `0.167.0` or later. Managed permission profiles need `0.138.0`,
and the granular approval policy plus the filesystem read denies were verified only on `0.167.0`,
so that is the minimum. The installer checks this before writing any global state.

The operation is idempotent. Repository-backed artifacts are symlinked so a later `git pull`
updates them immediately. Editable global files use managed sections so personal configuration is
preserved.

When migrating a known legacy oh-my-harness `~/.codex/AGENTS.md` that predates ownership markers,
run the first installation with `--replace-global-agents`. The original file is preserved as
`AGENTS.md.omh.bak`. Do not use this flag for an unrelated personal instruction file.

## Installed surfaces

| Source | Global destination | Strategy |
| --- | --- | --- |
| shared `core/skills/<name>/` | `~/.agents/skills/<name>/` | Directory symlink |
| Codex-only `harness/codex/skills/<name>/` | `~/.agents/skills/<name>/` | Directory symlink |
| `harness/codex/agents/*.toml` | `~/.codex/agents/*.toml` | Managed file copy |
| `harness/codex/AGENTS.md` | managed block in `~/.codex/AGENTS.md` | Merge |
| `harness/codex/adapter-hooks-removal.json` | removes obsolete adapter-owned context hook | Merge |
| generated permissions profile | `~/.codex/config.toml` | Managed sections |
| generated from `core/policies/permissions.json` | `~/.codex/rules/oh-my-harness.rules` | Managed file |
| `harness/codex/` | `~/.codex/oh-my-harness` | Directory symlink |
| generated ownership manifest | `~/.codex/oh-my-harness-links.json` | Atomic rewrite |

Separately, the native plugin manifest declares `harness/codex/hooks/hooks.json`. The installer
does not install or trust these plugin hooks.

The installer preserves unrelated hooks, machine-specific capability mappings, global
instructions, MCP servers, plugins, and personal skills. It removes stale symlinks only when the
ownership manifest proves they were created by a previous run, and stops instead of replacing an
unmanaged path.

The managed `oh-my-harness` permissions profile extends Codex's `:workspace` profile and adds
`~/knowledge-base/` and `~/.local/share/omh-kb/` as reusable workspace roots. The installer stops
instead of replacing an existing user-owned sandbox or permissions selection.

### Permission policy

Both Codex surfaces below are rendered at install time from the canonical policy in
`core/policies/permissions.json`. Nothing with an absolute path is checked in.

- **Command rules.** `~/.codex/rules/oh-my-harness.rules` holds one `prefix_rule` per policy prefix:
  `decision = "prompt"` for ask rules and `"forbidden"` for deny rules. The file starts with an
  `omh-managed` header; the installer refuses to overwrite a rules file without it and backs up a
  managed file once as `oh-my-harness.rules.omh.bak`. Shell globs, such as `find * -delete`, have no
  execpolicy equivalent and are skipped.
- **Secret reads.** The profile adds `[permissions.oh-my-harness.filesystem]`, which denies sandboxed
  reads of the home secret paths with `HOME` expanded at install time, and a `:workspace_roots`
  table that keeps `"." = "write"` and denies `**/<glob>` for each secret file name. Codex has no
  "ask" for reads: a denied read fails inside the sandbox, and the model must request escalation.
- **Approvals.** `approval_policy` is the granular form with every category enabled, so prompts from
  `prompt` rules, sandbox escalations, MCP elicitations, `request_permissions`, and skill scripts
  all reach a reviewer. `approvals_reviewer = "user"` replaces the earlier `auto_review`, which let a
  reviewer model approve deletions. Expect more prompts, including network escalations.

The global `AGENTS.md` contains no rule about destructive operations or credentials; enforcement
comes only from these managed surfaces. Inspect the remaining gaps with
`python3 -m installers.policy.render --gaps codex`, and check one command against the installed
rules with:

```bash
codex execpolicy check --rules ~/.codex/rules/oh-my-harness.rules -- rm tests/tmp_fixture.txt
```

Known issue, independent of this policy: `codex-cli 0.167.0` rejects symlinked writable roots. When
`~/knowledge-base` is a symlink, every sandboxed command fails with `symlinked writable roots are not
supported`.

The global adapter removes the legacy adapter-owned `SessionStart` registration of earlier versions.
The native plugin now supplies the content-free KB pointer, so retaining the old registration would
run it twice; unrelated third-party session hooks remain untouched.

Custom-agent TOMLs are copied instead of symlinked because current Codex releases do not discover
symlinked files reliably. A content manifest permits safe upgrades while refusing to overwrite a
managed copy that the user changed locally.

## Start a session mode

Claude Code starts a mode with `claude --agent oh-my-harness:<mode>`. Codex has no equivalent flag:
its documentation describes custom agents only as spawned subagents, and `codex --help` in
`codex-cli 0.155.0` lists no agent selector. The closest equivalent injects the installed mode
TOML's `developer_instructions` into the main session through the `-c` config override:

```bash
omh_mode() {
  codex -c "developer_instructions=$(python3 -c 'import json, sys; t = open(sys.argv[1], encoding="utf-8").read(); print(json.dumps(t.split("\"\"\"\n", 1)[1].rsplit("\n\"\"\"", 1)[0]))' "${CODEX_HOME:-$HOME/.codex}/agents/$1.toml")" "${@:2}"
}
omh_mode discoverer   # or developer, reviewer
```

It requires the global adapter, which installs the mode TOMLs. The extraction relies on the
`developer_instructions = """..."""` shape that the adapter renderer emits and on the absence of
backslash escapes in that body.

Verified on 2026-09-18 with `codex-cli 0.155.0` through `codex exec`: with the reviewer TOML
injected, the main session identified itself as the reviewer mode, and without it, as the default
agent. Known gaps against Claude Code:

- The override replaces any `developer_instructions` already set in the user's config for that
  session.
- The mode's skills are not preloaded as Claude's `skills:` frontmatter does; the instructions name
  them, and the user can invoke one explicitly, for example `$developer`.
- The model and reasoning effort stay those of the user's config.
- Spawning specialists from this main session follows Codex's documented subagent behavior; it was
  not exercised by this probe.
- The adapter installs the modes as custom agents under `~/.codex/agents/`, so Codex can also spawn
  them as subagents. Their instructions forbid that use, but nothing in Codex enforces it.
- Hypothesis, untested: Codex's default `workspace-write` sandbox may block writes to sibling
  worktrees outside the workspace, which the developer and reviewer create, and network access
  that `code-host` needs through a CLI such as `gh` to open, comment on, or mark a pull request
  ready.

## MCP integrations

The installer wires Deja when its CLI is present. It also installs the official LangChain marketplace and its `langchain-skills` and
`langchain-mcp` plugins. They cover LangChain, LangGraph, and Deep Agents skills plus live
documentation and API reference. The optional LangSmith plugins are not installed because they
require a LangSmith account and OAuth authorization.

It also installs the official AI Evals Course marketplace and its `evals` plugin. It provides
eight skills for error discovery, eval-pipeline audits, synthetic data, RAG evaluation, human
review interfaces, LLM-as-Judge prompts, and judge calibration. The local `ai-engineer`,
`software-engineer`, and `architect` agents first verify that `evals:*` is available at runtime;
when installation is pending, they report that state and do not claim to use unavailable skills.

The upstream marketplace publishes skills and MCP servers, not Codex custom agents. The local
`ai-engineer`, `software-engineer`, and `architect` agents route matching framework work through
`langchain-skills:ecosystem-primer` and the relevant official skills; they do not copy or fork
upstream guidance.

Run `python3 installers/codex/install.py --skip-integrations` to synchronize only filesystem artifacts.

## Validation

```bash
python3 installers/codex/install.py --check
codex mcp list
```

Start a new Codex session after installation so global agents, skills, hooks, and instructions are
rediscovered.

The installed global guidance applies the shared software-evidence contract to every response.
Use the `evidence` skill for claim provenance and decision mechanics, and delegate a read-only audit
to `evidence-reviewer` when a decision is consequential, difficult to reverse, or controlled by an
uncertain metric or causal claim.
