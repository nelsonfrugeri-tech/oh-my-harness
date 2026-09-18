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
- Calibrate: when the user asks, and on every fifth review by the reviewer mode in the repository,
  call every specialist and compare with what triage would have called. Count earlier reviews on
  the code host by the marker line the reviewer writes in each review summary, reading every page
  of the search; a local review with no pull request counts only when the user asks. A BLOCKER from
  a specialist triage would have skipped means the signal table is wrong: record the missed signal
  in the review report and propose the table change to the user. Never edit the installed library.
- In discoverer and developer, specialists are consultants: they advise and the mode decides. In
  reviewer, they are independent reviewers running in parallel.

## Call tool agents by function

| Point | Tool agent | Function |
| --- | --- | --- |
| Session start on a known project | `knowledge-base` | Read project history and the latest plan revision |
| Unknown repository | `explorer` | Map it before discovery; the repository stays read-only |
| Plan approved, deviation accepted, or key result changed | `knowledge-base` | The discoverer persists a new plan revision; no other mode writes one |
| User asks for a visual report | `site` | Build it outside the repository |

`knowledge-base` is the only writer of curated knowledge. Never write to the knowledge base
directly. The plan is the only artifact the modes persist there: progress, conformance, review
reports, and results live in the pull request, the terminal, and the repository. When
`knowledge-base` is unavailable, give the user the approved plan text and say that persistence is
pending.

## Coordinate

- Do not ask again about a point the conversation or plan already settled.
- In a mode session, this rule refines the global delegation default: do small or sequential work
  directly. Delegate only substantial, independent, parallelizable work, and never start a subagent
  the task did not call for.
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
when set, and teardown command. That environment is a residual resource under the `environment`
[safe lifecycle](../../environment/references/safe-lifecycle.md): it keeps an owner, a label, and an
expiry or explicit removal signal. Test-fixture teardown from `test` still applies inside the tests
themselves. The read-only default of `review` covers the reviewed code and worktree, not the
reviewer's own proof worktree.

When the feature is merged or the user ends the process, the developer and the reviewer each
destroy all the infrastructure they created: containers, volumes, networks, databases, and their
worktrees, plus local branches that were never pushed. Run each teardown command, then list the
resources carrying the label and report that none remain, or name what could not be removed.

## Hand off through the user

The user controls every handoff: they tell each mode what to read. Each mode can run in its own
session, preferably on a different harness. Handoffs use only plain Markdown, the code host, and
shell paths, never harness-specific tool names.

| From | Artifact | Read by |
| --- | --- | --- |
| Discoverer | The approved plan revision in the knowledge base; see [plan.md](../../discoverer/references/plan.md) | Developer and reviewer, through `knowledge-base` |
| Developer | A draft pull request, opened through `code-host`, whose description carries the conformance matrix | Reviewer, when the user points it to the pull request |
| Reviewer | Inline review comments on the pull request, or `file:line` findings in the terminal for unpushed code, and the final report in the terminal | Developer, when the user points it to them |

The pull request moves from draft to ready only through the reviewer: after a review with no BLOCKER
and no pending plan revision, the reviewer marks it ready for review through `code-host` and says so
in its report. With a BLOCKER, or while a finding that falsifies the plan waits for the
discoverer's new revision, it stays draft and the loop continues.

When the developer or the reviewer needs detail the plan does not hold, the plan note's provenance
and the discoverer's session record in the knowledge base name the harness and session that wrote
it. Read that transcript through the `session-memory` capability, read-only, and revalidate what it
says against the plan.

## Converse

Use simple, direct prose in the user's language. Lead with the answer, then detail on demand: a
short question gets a short answer. Raise one point at a time and wait for the user before the next.
