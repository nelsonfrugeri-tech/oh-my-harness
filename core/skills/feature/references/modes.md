# Session Modes

The shared contract of the `discoverer`, `developer`, and `reviewer` mode agents. A mode is the
primary session: the user starts it explicitly, and it orchestrates. A subagent cannot start another
subagent or talk to the user mid-run, so every fan-out happens in the mode agent.

## Agent tiers

| Tier | Agents | Called |
| --- | --- | --- |
| Mode | `discoverer`, `developer`, `reviewer` | Started by the user as the session agent; never spawned or auto-routed |
| Specialist | `architect`, `software-engineer`, `ai-engineer`, `tech-pm` | By triage, on the objective signals below |
| Tool agent | `knowledge-base`, `explorer`, `site` | By function, at the fixed points below; no triage |
| Auditor | `evidence-reviewer` | For an independent audit of claims; the reviewer may use it for meta-review |

## Choose the lane

Take the fast lane only when the change can be described in one sentence and it creates no module,
changes no public contract, changes no LLM behavior, and migrates no data. A bug fix or a quick
improvement usually qualifies: skip the discoverer and start the developer. Any one of those signals
sends the work to the discoverer first.

## Triage specialists

Assess the request or diff first, then call only the specialists the change needs.

| Signal in the request or diff | Specialist |
| --- | --- |
| New module or package, boundary, dependency direction, public contract, technology change | `architect` |
| Production code changed | `software-engineer` |
| Prompt, LLM call, tool or MCP, RAG, eval, token cost | `ai-engineer` |
| Ambiguous product scope or acceptance | `tech-pm` |
| Only text or trivial configuration | none |

- Announce the triage in one line before calling anyone, for example:
  `Triage: called architect (new package), software-engineer (production code); skipped ai-engineer (no LLM surface), tech-pm (scope settled).`
- When in doubt, call.
- Calibrate: every fifth review, counted from the review reports in the handoff directory, call
  every specialist and compare with what triage would have called. A BLOCKER from a specialist
  triage would have skipped means the signal table is wrong: record the missed signal and change the
  table.
- In discoverer and developer, specialists are consultants: they advise and the mode decides. In
  reviewer, they are independent reviewers running in parallel.

## Call tool agents by function

| Point | Tool agent | Function |
| --- | --- | --- |
| Session start on a known project | `knowledge-base` | Read project history and the latest plan revision |
| Unknown repository | `explorer` | Map it before discovery; the repository stays read-only |
| Plan approved, deviation accepted, or key result changed | `knowledge-base` | Persist a new plan revision |
| Feature finished | `knowledge-base` | Persist the consolidated result |
| User asks for a visual report | `site` | Build it outside the repository |

`knowledge-base` is the only writer of curated knowledge. Never write to the knowledge base
directly. When it is unavailable, keep the artifact in the handoff directory and say that
persistence is pending.

## Coordinate

- Do not ask again about a point the conversation or plan already settled.
- Do small or sequential work directly. Delegate only substantial, independent, parallelizable
  work, and never start a subagent the task did not call for.
- Name in each brief the skills to load before any code, including the framework documentation or
  skill for the stack.
- Treat a subagent report as a claim: verify the files on disk and the behavior in the real runtime
  before relaying it.
- Relay results in the user's language.

## Isolate the runtime

The developer and the reviewer each work in their own git worktree outside the product checkout,
with their own runtime:

- a unique name per worktree, such as `<repo>-<feature>-<mode>`, used as `COMPOSE_PROJECT_NAME` or
  the equivalent namespace of the project's runtime;
- host ports and a database or schema no other worktree uses;
- no production secrets or shared developer resources;
- an owner (mode and session), a label (project and feature), and, for the reviewer, an expiry on
  every created resource;
- one teardown command scoped to that name, such as `docker compose -p <name> down -v`.

Leave the environment up for the user when done and report its owner, label, endpoints, expiry
when set, and teardown command.

## Hand off across sessions and harnesses

Each mode can run in its own session, preferably on a different harness. Handoffs use only plain
Markdown and shell paths, never harness-specific tool names.

- The plan lives in the knowledge base; see [plan.md](plan.md).
- Round artifacts, the developer's conformance matrix and the reviewer's report, are Markdown files
  outside every repository at
  `${XDG_STATE_HOME:-$HOME/.local/state}/oh-my-harness/handoffs/<project>/<feature>/`, named
  `conformance-<round>.md` and `review-<round>.md`. Give the user the exact path. They are
  progress, so they never become knowledge-base notes.

## Converse

Use simple, direct prose in the user's language. Lead with the answer, then detail on demand: a
short question gets a short answer. Raise one point at a time and wait for the user before the next.
