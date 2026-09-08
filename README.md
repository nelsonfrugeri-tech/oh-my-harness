<div align="center">

# oh-my-harness

**Your engineering system, portable across AI coding harnesses.**

Keep the agents, skills, policies, evaluations, workflows, tools, and knowledge that define how you
work—even when you change AI coding assistants, machines, or providers.

[![License](https://img.shields.io/badge/license-Apache%202.0-4CAF50?style=flat-square)](LICENSE)
[![Harness](https://img.shields.io/badge/harness-Claude%20Code-8A63D2?style=flat-square)](https://claude.com/claude-code)
[![Harness](https://img.shields.io/badge/harness-Codex-111111?style=flat-square)](https://openai.com/codex/)
[![Agents](https://img.shields.io/badge/agents-9-2496ED?style=flat-square)](#agents)
[![Skills](https://img.shields.io/badge/skills-28-DC5F00?style=flat-square)](#skills)

[Explore the interactive guide](https://nelsonfrugeri-tech.github.io/oh-my-harness/)
· [Website development and recording](website/README.md)

</div>

---

## Why this project exists

An AI coding harness becomes useful long before it becomes portable.

Here, a **harness** is the host runtime around a model: the application that discovers agents and
skills, exposes tools, runs hooks and workflows, and injects global instructions.

You tune agents, collect skills, define review standards, wire tools, add hooks, build workflows,
and teach the model how to reason and communicate. Most of that investment ends up coupled to one
harness's file format, one machine's paths, and one provider's tool names. Moving from Claude Code
to Codex—or using both—means rebuilding the same operating system around the model.

oh-my-harness makes that operating system a versioned project:

- **Shared intent lives once.** Engineering methods, behavioral policies, eval cases, and role
  contracts have one source of truth.
- **Harness-native adapters preserve fidelity.** Claude Code uses its native Markdown agents and
  Workflow API; Codex uses native TOML agents and its own installer. Portability does not mean
  flattening every harness into the lowest common denominator.
- **Tools are replaceable.** Agents ask for capabilities such as `code-host`, `ci`,
  `code-graph`, or `session-memory`; each machine maps those capabilities to its installed
  providers.
- **Knowledge outlives sessions and assistants.** Curated knowledge is stored outside product
  repositories in a readable, syncable bundle with provenance. Its vector index is derived state.
- **Behavior has a shared contract.** The same evidence discipline and progressive-disclosure
  response policy are designed for both supported harnesses; runtime equivalence remains something
  to evaluate, not assume.

The result is leverage: improve a shared capability once, adapt only what is harness-specific, and
carry your way of working to the next assistant instead of starting over.

## What you get

| Benefit | Mechanism | Practical effect |
| --- | --- | --- |
| Change harnesses without rebuilding your setup | Shared contracts plus native adapters | Roles, standards, and knowledge remain familiar |
| Change providers without rewriting agents | Abstract capability table | GitHub, GitLab, Graphify, Deja, and other providers stay machine-local |
| Reduce unsupported model claims | Evidence status, provenance, and independent review | Facts, inference, uncertainty, and decisions remain distinguishable |
| Keep prompts focused | Progressive disclosure in skills and responses | Deep references load only when the task needs them |
| Preserve engineering quality | Repository-first implementation and a PR quality gate | Project-native checks run against the revision that will open the PR |
| Reuse knowledge across machines | Markdown source of truth plus rebuildable Qdrant index | Memory is inspectable and not locked to one harness |
| Use upstream expertise without owning its drift | Explicit routes to external plugins | Framework-specific knowledge stays with its maintainers |

## Quick start

| Goal | Path |
| --- | --- |
| Install on Claude Code | [Claude Code quick start](#claude-code) |
| Install on Codex | [Codex quick start](#codex) |
| Understand what remains portable | [Architecture](#architecture) |
| Inspect the packaged capabilities | [Agents and skills](#whats-inside) |
| Add another capability or harness | [Extending oh-my-harness](#extending-oh-my-harness) |

## Architecture

```text
                         oh-my-harness repository
                  one versioned source for how you work
                                      |
          +---------------------------+---------------------------+
          |                           |                           |
          v                           v                           v
   portable contracts          behavioral system          shared runtime pieces
   core/agents/routing.json     core/skills/               core/hooks/
   role responsibilities       core/policies/             core/evals/
          |                           |                           |
          +---------------------------+---------------------------+
                                      |
                         harness-native representation
                    +-----------------+-----------------+
                    |                                   |
                    v                                   v
             harness/claude/                     harness/codex/
             Markdown agents                     TOML agents
             Workflow TypeScript                 managed adapter
             plugin manifest                     plugin manifest
                    |                                   |
                    +-----------------+-----------------+
                                      |
                         machine capability adapter
             code-host · ci · web · code-graph · session-memory · tunnel
                                      |
                    +-----------------+-----------------+
                    |                                   |
                    v                                   v
          provider-owned tools                  ~/knowledge-base/
          and external plugins                  portable OKF bundle
```

The repository separates three kinds of state deliberately:

1. **Portable source** belongs in `core/`: behavior and contracts that should survive a harness
   switch.
2. **Native representation** belongs in `harness/<name>/`: manifests, agents, hooks, workflows,
   global guidance, and installer behavior required by that harness.
3. **Machine and user state** stays outside the repository: credentials, provider mappings,
   installed executables, transcripts, and the knowledge base.

## Design principles

### One source of intent, native execution

The shared routing catalog defines portable roles and their skill dependencies. Each adapter renders
that responsibility in the harness's native format. Shared semantics are aligned and tested;
harness-specific capabilities remain explicit instead of being hidden behind a fictional universal
schema.

### Capabilities, not hardcoded tools

Agents and skills refer to abstract capabilities. The active harness's global guidance is the only
place that maps those capabilities to providers on a machine.

| Capability | Purpose | Example provider |
| --- | --- | --- |
| `code-host` | Pull Requests, issues, and remote reviews | GitHub or GitLab |
| `ci` | Pipeline inspection and operation | GitHub Actions or GitLab CI |
| `web` | Current public research | Harness-native web access |
| `code-graph` | Code graph query, path, and explanation | Graphify or another graph provider |
| `session-memory` | Search past raw session transcripts | Deja or another transcript index |
| `tunnel` | Temporary authenticated report exposure | An approved tunnel provider |

An empty mapping is an honest degraded capability. The harness must report what remains unavailable;
it must not invent a provider.

### Progressive disclosure is an operating model

A skill is a capability, not an encyclopedia. Its `SKILL.md` defines ownership, activation,
workflow, boundaries, and output. Stable deep detail lives in task-specific references and loads on
demand. Volatile vendor facts come from current primary sources instead of being copied into a skill
and left to age.

The same principle shapes responses: lead with the answer, reveal reasoning and edge cases in
layers, and use a visual only when it materially reduces cognitive effort.

### Evidence and provenance before presentation

The project treats “anti-hallucination” as an engineering discipline, not a promise that a model can
never be wrong.

```text
retrieve or observe
        |
        v
classify the claim  --> fact · derived result · inference · hypothesis · estimate · unknown
        |
        v
record provenance  --> source · revision · command · environment · time · limitation
        |
        v
make the decision  --> alternatives · trade-off · falsifier · validation · rollback
        |
        v
present clearly    --> progressive prose · table · flow · timeline · tree · wireframe
```

The `evidence` skill governs claims, uncertainty, and decisions. The `evidence-reviewer`
independently audits consequential work under a read-only contract. Codex enforces that boundary
with `sandbox_mode = "read-only"`; Claude Code removes direct write/edit tools but still permits
Bash, so its boundary is behavioral rather than equivalent filesystem isolation. The
`didactic-visual` skill then chooses the smallest useful representation; it cannot turn weak
evidence into a stronger claim.

Knowledge writes follow the same rule. Notes and session records carry real harness, session,
working-directory, and machine provenance. Missing required provenance blocks the write instead of
being guessed.

### Engineering standards are repository-first

The mandatory implementation constraints live in
[`code-craft.md`](core/skills/implement/references/code-craft.md) and are applied through
`implement`. They preserve the project's own contracts, type system, layout, and quality gates.
Project contracts override generic preferences. Do not split by a universal line or symbol count,
and do not force a pattern where the repository provides no evidence that it helps.

### Language contract

Language follows the artifact's role:

| Artifact | Language |
| --- | --- |
| Skills, roles, agents, references, and `routing.json` | English |
| Code, comments, docstrings, test messages, and repository documentation | English |
| `harness/claude/CLAUDE.md` and `harness/codex/AGENTS.md` | pt-BR |
| Text injected into a user session by hooks | pt-BR |
| `prompt` and `required` fields in `core/evals/*/cases.json` | pt-BR |
| Evaluation protocol README files | English |
| Installer error messages shown to users | pt-BR |
| Public website and video-guide prose in `website/` | pt-BR (approved presentation-language exception) |
| Vendored third-party content | Original upstream language |

The response contract is independent of repository prose: respond in the user's language while
keeping established technical terms in English.

## Supported harnesses

Claude Code and Codex are first-class today. The shared source is designed to admit more adapters,
but a harness is not supported until its native representation, installer path, and contract tests
exist.

| Surface | Claude Code | Codex |
| --- | --- | --- |
| Shared skills | Native plugin | Native plugin |
| Custom agents | Native Markdown agents in the plugin | Native TOML agents through the full adapter |
| Global policy | Merge the managed `CLAUDE.md` guidance | Installer-managed `AGENTS.md` block |
| Hooks | Native plugin descriptor | Native plugin descriptor; explicit hook trust required |
| Feature workflow | Shared `feature` skill; TypeScript prototype is source-only | `feature` skill with Codex-native orchestration |
| Tool providers | Machine capability table | Machine capability table |
| Knowledge base | `knowledge-base` agent | `knowledge-base` agent |
| Behavioral evals | Fresh-session protocol | Fresh-session protocol |

## Installation

### Claude Code

Install the native plugin:

```bash
claude plugin marketplace add nelsonfrugeri-tech/oh-my-harness
claude plugin install oh-my-harness@oh-my-harness
claude plugin list
```

The plugin provides shared skills, Claude-native agents, and the PR quality-gate hook. Global
instructions and user permissions are intentionally not plugin-owned. Merge
[`harness/claude/CLAUDE.md`](harness/claude/CLAUDE.md) and the permissions from
[`harness/claude/settings.json`](harness/claude/settings.json), or follow the
[`claude-code` runbook](harness/claude/skills/claude-code/SKILL.md).

### Codex

Install the native plugin:

```bash
codex plugin marketplace add nelsonfrugeri-tech/oh-my-harness
codex plugin add oh-my-harness@oh-my-harness
codex plugin list
```

Start a new session, open `/hooks`, inspect the bundled definitions, and trust them before relying
on the PR gate. The plugin supplies shared skills, the Codex runbook, and hooks.

For custom agents, managed global guidance, permissions, and optional local integrations, install
the full adapter from a clone. It requires Codex `0.138.0+`, selects the managed oh-my-harness
permission profile, and adds the knowledge-base runtime directories as writable roots.

```bash
git clone https://github.com/nelsonfrugeri-tech/oh-my-harness.git
cd oh-my-harness
python3 installers/codex/install.py --skip-integrations  # conservative first pass
python3 installers/codex/install.py --check
```

Without `--skip-integrations`, the installer also attempts the declared LangChain and Evals plugin
setup plus available Deja/Graphify integration. Inspect
[`harness/codex/README.md`](harness/codex/README.md) before choosing that broader path.

The installer preserves unrelated user configuration and refuses ownership conflicts. Passing its
test suite proves the exercised filesystem states, not every possible local configuration.

For a new machine, [`INSTRUCTIONS.md`](INSTRUCTIONS.md) is the bootstrap entrypoint.

## The PR quality gate

The shared `PreToolUse` hook moves validation to the moment a Pull Request is opened, leaving
commits and pushes free. In a trusted repository it:

1. identifies the selected PR head and verifies that local `HEAD` matches the live remote branch;
2. refuses dirty, foreign, unpushed, divergent, or unverifiable content;
3. discovers format, lint, typecheck, and test commands from project configuration, Make targets,
   or language manifests;
4. runs those checks and denies PR creation when a discovered check fails.

Repository trust is separate from hook trust because discovered commands are repository-controlled.
From a checkout you have reviewed, opt in once with:

```bash
common_git_dir=$(git rev-parse --path-format=absolute --git-common-dir)
if command -v shasum >/dev/null 2>&1; then
  repo_sig=$(printf '%s' "$common_git_dir" | shasum -a 256 | cut -d' ' -f1 | cut -c1-12)
else
  repo_sig=$(printf '%s' "$common_git_dir" | sha256sum | cut -d' ' -f1 | cut -c1-12)
fi
trust_dir="${XDG_CACHE_HOME:-$HOME/.cache}/omh-quality-gate/trusted"
mkdir -p "$trust_dir"
touch "$trust_dir/$repo_sig"
```

The common Git directory makes that decision apply to every worktree of the reviewed repository.
Without this marker, the gate deliberately defers and the normal PR flow continues unverified.
The gate covers `gh pr create` and the configured GitHub MCP creation tool. It does not cover a PR
opened in a browser, later pushes, or every possible provider API. `OMH_GATE=off` is an explicit,
reported emergency bypass—not an access-control boundary.

## What's inside

### Agents

Eight portable roles are represented natively in both harnesses. Each adapter adds its own ninth,
harness-specific installation agent:

| Theme | Agent | Responsibility |
| --- | --- | --- |
| Engineering | `architect` | System design, ADRs, C4, API design, and explicit trade-offs |
| Engineering | `software-engineer` | End-to-end implementation with scalability, resilience, responsiveness, quality, and cost constraints |
| Engineering | `ai-engineer` | LLM integration, RAG, embeddings, data pipelines, and AI evaluation |
| Engineering | `tech-pm` | Product discovery, observable acceptance criteria, prioritization, roadmaps, and PRDs |
| Policy | `evidence-reviewer` | Independent read-only audit of claims, metrics, decisions, and validation evidence |
| Harness | `claude-code` / `codex` | Install and synchronize the active harness adapter |
| Tool | `knowledge-base` | Operate persistent knowledge, retrieval, session records, and project identity |
| Tool | `site` | Produce cited visual reports outside the analyzed repository and optionally expose them |
| Tool | `explorer` | Onboard into unfamiliar repositories with a site report, a CLAUDE.md proposal, and a knowledge handoff |

The canonical routing contract is
[`core/agents/routing.json`](core/agents/routing.json). Claude manifests live under
`harness/claude/agents/`; Codex manifests live under `harness/codex/agents/`.

### Skills

The package contains 28 skills: 26 shared skills and one adapter skill for each harness. The catalog
below is intentionally complete and is checked against both plugin manifests.

**Reasoning and presentation:** `evidence` · `didactic-visual`

**Software delivery:** `implement` · `design` · `test` · `review` · `research` · `manage` · `environment` · `ci-cd` · `operate` · `feature`

**Engineering knowledge:** `python` · `typescript` · `ai-engineer` · `api-design` · `frontend-ui` · `security` · `observability`

**Knowledge and tool capabilities:** `explorer` · `kb-infra` · `kb-write` · `kb-retrieval` · `kb-session` · `site-report` · `site-expose`

**Harness adapters:** `claude-code` · `codex`

### Workflows

The shared `feature` skill resolves material scope, keeps resumable state outside the product
tree, delegates implementation and testing, and requests independent handoffs only when required.
The repository also contains a more prescriptive Claude-native `create-feature.ts` prototype. It is
source-only today: neither the native plugin manifest nor the synchronization runbook installs it,
and there is no versioned runtime-discovery test. Treat the shared `feature` skill as the delivered
contract, not the prototype as evidence of an equivalent cross-harness workflow runtime.

### Policies

Two shared policy blocks are embedded into each harness's global guidance:

- `software-evidence-contract.md` defines claim status, uncertainty, provenance, and decision
  discipline.
- `response-format-contract.md` applies `evidence → didactic-visual → specific output format`
  and enforces progressive disclosure without decorative formatting.

### Evals

`core/evals/` contains behavioral corpora for `evidence` and `didactic-visual`. They are manual,
fresh-session protocols: repository tests validate corpus structure, while an evaluation run must
record harness, model, configuration, commit, observation time, evaluator, and per-requirement
evidence. A local test passing does not claim that a model behavior passed.

## Knowledge base

The knowledge base is deliberately outside every product repository. This repository ships the
operational skills, schemas, templates, and local Qdrant Compose contract; the
`knowledge-base` agent executes that lifecycle. It is not a bundled always-running knowledge
daemon or a finished cross-harness CLI.

```text
~/knowledge-base/                 # OKF v0.2 Markdown bundle; source of truth
  index.md
  <scope>/
    <domain>/
      <topic>/
        index.md
        <date>--<short-slug>.md    # immutable note
      sessions/
        <session-id>.json          # living session record

~/.local/share/omh-kb/            # machine runtime; derived or local state
  identity.json
  qdrant/
  venv/
```

Routing is topic-first: scope → domain → topic → concept. Project identity is itself an immutable
`knowledge_type: project` note; legacy `context.md` files can be migrated once and are preserved,
not deleted.

The collision at the canonical domain blocks writes until a persistent resolver shared by note and
session writers is defined; a local alias is never created. This prevents two writers from silently
creating different knowledge universes for the same project.

Key properties:

- **Markdown is authoritative.** Qdrant is a rebuildable local index, not the knowledge source.
- **Notes are immutable.** Corrections create a new note with `supersedes`; session records are
  named mutable exceptions.
- **Retrieval is address-first, then semantic.** Exact entities, aliases, paths, repository URLs,
  and temporal fields are resolved before hybrid dense+sparse search.
- **Search degrades truthfully.** Without Qdrant, retrieval falls back to structured disk
  navigation; session-memory can then inspect relevant raw transcripts.
- **Embeddings are fixed by contract.** `BAAI/bge-m3` produces the dense and lexical sparse
  representations; changing it requires an explicit reindex decision.
- **Secrets fail closed.** Credential-bearing or signed remote URLs persist as `remote_url: null`
  and are never echoed.
- **Project mapping is on demand.** The `explorer` agent inspects a repository read-only and returns a
  cited map to the knowledge-base owner; durable notes require a separate `kb-write` request.

Today the agent invokes KB content retrieval explicitly. `SessionStart` automatically emits only a
content-free pointer; automatic content retrieval and end-of-session distillation are not current
runtime behavior.

## Optional ecosystem integrations

Every plugin an installer installs is declared in `catalog_contract` of `core/agents/routing.json`,
and so is every plugin deliberately left out. The always-on cost is paid on every session, whether or
not the topic comes up:

| Plugin | Brings | Always-on cost | Installed by default |
| --- | --- | --- | --- |
| `langchain-skills` | 22 skills for LangChain, LangGraph, and Deep Agents | ~2.1k tokens per session | yes |
| `langchain-mcp` | 2 MCP servers, `langchain-docs` and `langchain-reference`, behind the `framework-docs` capability | resolved at runtime, not measured as a session cost | yes |
| `evals` | 8 evaluation skills | ~862 tokens per session | yes |
| `langsmith-skills` | 3 skills: `langsmith-trace`, `langsmith-dataset`, `langsmith-evaluator` | not measured, not installed | no |
| `langsmith-mcp` | 1 OAuth MCP server for LangSmith traces, datasets, prompts, and experiments | not measured, not installed | no |

`langchain-mcp` provides the `framework-docs` capability: live documentation the routes consult for
every volatile LangChain fact — version, API surface, SDK behaviour — because the skills carry the
knowledge frozen at their own release. On Codex, installing the plugin is not proof that its MCP
servers were registered; confirm with `codex mcp list`.

oh-my-harness does not vendor third-party expertise that has an active upstream owner.

- **LangChain, LangGraph, and Deep Agents:** agents route relevant work to the official
  `langchain-skills` plugin and its live documentation integrations when installed.
- **AI evaluation:** `ai-engineer` routes framework-agnostic evaluation work to the external
  `evals` plugin. `evals >= 0.3.1` is required because the entry skill is
  `evals:evals-start`. If an old installation exposes `evals:start`, run
  `claude plugin update evals@ai-evals-course`.
- **Code graph:** Graphify can provide `code-graph`, but remains externally installed and
  machine-configured.
- **Session memory:** Deja can provide transcript retrieval; it does not become a second writer of
  curated knowledge.

Unavailable optional integrations produce explicit degraded routing. Installation does not prove
authentication, reachability, or health.

## Project status

The project is distributed from this Git repository. The current implementation supports Claude
Code and Codex; it is not yet a general-purpose harness framework.

Only behavior represented in the repository and bounded above is part of the current product.
Future work remains outside this README until it becomes installable and verifiable.

## Extending oh-my-harness

Add portable behavior to `core/`; add representation to a harness adapter only when its runtime
requires it.

- **Skill:** create `core/skills/<name>/SKILL.md`, keep the name globally unique, and put only
  task-relevant stable detail in `references/`.
- **Agent:** add the portable role to `core/agents/routing.json`, then provide both native
  manifests and contract fixtures.
- **Hook:** keep executable behavior in `core/hooks/` and use native descriptors under each
  adapter.
- **Workflow:** define the portable contract first, then implement the strongest native
  representation each harness supports.
- **Capability:** add abstract intent to global guidance; provider installation and credentials
  remain machine-local.
- **Eval:** define observable behaviors rather than reference wording, and scope every result to the
  recorded harness, model, configuration, revision, and time.

Machine paths, credentials, account identifiers, and personal configuration never belong in the
repository. Third-party content remains upstream unless there is an explicit vendoring and
provenance decision.

## Boundaries

- This project improves consistency; it does not guarantee identical model output across harnesses
  or sessions.
- A passing test proves the exercised cases on one revision and environment, not the absence of
  defects.
- A configured MCP or plugin does not prove authentication, reachability, or health.
- The knowledge base is designed for a single user's cross-machine workflow; current plans do not
  claim multi-user concurrency.
- Provider-neutral roles still depend on the capabilities actually available on each machine.

## License

Apache License 2.0. See [LICENSE](LICENSE).
