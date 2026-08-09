---
version: 2.0.0
name: feature
description: |
  Creates a feature end to end across Claude Code and Codex. Runs interactive technical
  refinement with architect or ai-engineer, persists the approved refinement, and orchestrates
  user history, implementation, parallel QA and SRE validation, fix iterations, and PR/MR creation.
  Use when the user wants to start a new feature through refinement_tech, user_history,
  development, validation, and PR/MR delivery.
  Triggers: /feature, create feature, new feature, start feature.
type: workflow
---

# Feature — End-to-End Feature Creation

Orchestrate a new feature from technical refinement through PR/MR delivery. Preserve every phase
and gate below. Do not invent names, technical decisions, or repositories; obtain missing choices
from the user.

## Portable orchestration contract

This skill describes behavior, not literal tool calls. Resolve each primitive through the active
harness:

- **ask** — collect a user decision through the harness-native input mechanism; if none exists,
  ask directly in the conversation.
- **delegate(role, task, context)** — run the named installed agent/role through the harness-native
  agent or subagent mechanism. If delegation is unavailable, load that role's instructions and
  perform the bounded phase inline.
- **parallel(tasks)** — schedule independent tasks concurrently when the harness supports it;
  otherwise run them sequentially while preserving independent results.
- **persist(path, content)** — write a product artifact to the declared feature path.
- **code-host** — use the concrete tool mapped to this capability in the active global
  instructions. If it is not configured, preserve the prepared issue or PR/MR content and report
  the pending external action.
- **memory** — index a summary only when this optional capability is configured. Persistence on
  disk must still succeed when memory is unavailable.

These names are conceptual primitives and must not be treated as concrete tool names.

### Harness adapters

- **Claude Code:** after refinement, prefer the bundled
  [create-feature TypeScript adapter](../../../claude-code/workflows/create-feature.ts) when the
  Workflow runtime is available. Pass the contract in **Workflow input** below.
- **Codex:** execute **Portable pipeline** with native task delegation. Keep the orchestration loop
  in the parent agent; delegate bounded role tasks, run QA and SRE concurrently when possible, and
  collect their structured handoffs before advancing.
- **Other harnesses:** execute the same portable pipeline using the contract above. Missing native
  orchestration is a performance limitation, not permission to skip phases or gates.

## Initial setup

1. **Feature name** — if the user did not provide one, ask for it. Derive a kebab-case
   `featureSlug` for directories and branches, then confirm it with the user.
2. **Implementation track** — ask whether to use `developer` (default) or `ai-engineer`. Recommend
   `ai-engineer` when the initial description involves LLMs, RAG, embeddings, agents, prompts,
   models, NLP, classification, or recommendation; otherwise recommend `developer`.
3. **Target repository** — ask which `owner/name` repository will receive the final PR/MR. If it is
   not known yet, record `repo` as `null`; the tech-pm and implementer may later resolve it from the
   Git remote.

## Phase 1 — `refinement_tech` (interactive)

Use `architect` by default. Use `ai-engineer` when the selected track is `ai-engineer` and the
focus is AI architecture. Mixed features may consult both roles at different points.

### Refinement loop

1. Delegate one specialist round requesting an initial analysis and three to five critical
   questions for the user.
2. Ask the questions through **ask**, one at a time when dense or grouped when brief.
3. Append the answers to the chronological refinement buffer.
4. Ask whether the user wants to deepen a point, switch specialist, or consolidate the refinement.
5. If more depth is requested, repeat with the complete accumulated context.
6. If consolidation is approved, continue below.

### Consolidation

Delegate the final synthesis to the current specialist, using this structure:

```markdown
# Refinement Tech — <feature name>

## Context and problem
## Technical goals
## Architecture decisions
## Components and responsibilities
## Evaluated trade-offs
## Technical risks and mitigations
## AI components (if applicable)
## Open questions

---

## Discussion history
<chronological dump of refinement questions and answers in pt-BR>
```

Present the complete content or an accurate summary for user approval. Only after approval, persist
it to `<featureSlug>/refinement_tech.md`. If **memory** is configured, index a summary too.

## Workflow input

The approved refinement produces this harness-neutral input:

```yaml
featureName: <human-readable name>
featureSlug: <kebab-case slug>
refinementContent: <complete refinement_tech.md content>
track: developer | ai-engineer
repo: <owner/name | null>
```

Claude Code passes these fields to the `create-feature` adapter. Codex and other harnesses use them
as the immutable input to the portable pipeline below.

## Portable pipeline

### Phase 2 — `user_history`

Delegate to `tech-pm` with the workflow input. Require:

- an INVEST user story with title, `As a / I want / So that`, three to six Given/When/Then
  acceptance scenarios, and Definition of Done;
- an issue/ticket created through **code-host** when available;
- the complete Markdown persisted to `<featureSlug>/user_history/user_history.md`;
- a structured handoff containing the Markdown, Definition of Done, and `issueUrl` (empty when the
  external action could not be completed).

Do not block local work solely because **code-host** is unavailable. Record the pending action.

### Phase 3 — `development`

Delegate to the selected implementation role (`developer` or `ai-engineer`) with the refinement,
user history, acceptance criteria, and Definition of Done. Require the role to:

1. create `feature/<featureSlug>` when branch creation is appropriate and authorized;
2. implement the feature and its tests according to the repository's engineering rules;
3. discover and pass the repository quality gates;
4. return a structured handoff with `verdict`, summary, changed files, verification commands,
   branch name, and an explicit `blockedReason` when blocked.

If the verdict is `blocked`, stop with status `blocked_at_development` and ask the user how to
resolve the stated blocker.

### Phase 4 — `validation_loop`

Run at most three iterations. In each iteration:

1. Run these independent validations through **parallel**:
   - `qa` validates functional and end-to-end behavior against every acceptance criterion;
   - `sre` validates applicable infrastructure, performance, load/stress, observability, and SLOs.
2. Each validator persists Markdown evidence under `<featureSlug>/validation/` and returns a
   structured handoff with `verdict: pass | fail`, summary, evidence paths, and issues with
   severity and reproduction details when applicable.
3. Append both handoffs to the immutable validation history for that iteration.
4. Advance only when both verdicts are `pass`.
5. When either verdict is `fail`, delegate one bounded fix task to the implementer with both
   reports, then repeat validation. If the fix task is blocked, stop with `blocked_at_fix`.

After three unsuccessful iterations, stop with `failed_max_iterations`. Show the complete QA/SRE
issue history and return control to the user; do not open a PR/MR.

### Phase 5 — `open_pr`

Only after both validators pass, delegate final preparation to the implementer. Require:

- a concise title and standardized body summarizing the refinement, user story, implementation,
  verification, and evidence paths;
- creation of the PR/MR through **code-host** when available;
- a structured handoff containing `prUrl`, title, and body.

If **code-host** is unavailable, return `blocked_at_open_pr` with the prepared title and body so the
user can complete the external action without repeating prior work. Otherwise return `success`.

## Final report

- `success` — show the PR/MR URL and evidence paths.
- `blocked_at_development`, `blocked_at_fix`, or `blocked_at_open_pr` — show the exact reason and
  the preserved handoff, then ask how the user wants to unblock it.
- `failed_max_iterations` — show all three validation iterations and ask whether the user wants to
  take over manually.

## Interruption and resume

At every phase boundary, retain the workflow input, completed handoffs, validation history, current
iteration, and pending next phase. If the user interrupts, persist the current feature state outside
the product repository unless the project explicitly defines a versioned feature-state artifact.
On resume, verify persisted outputs and continue from the first incomplete gate instead of replaying
completed external actions.

## Invariants

- Never persist `refinement_tech.md` before the user approves its content or an accurate summary.
- Never create an issue or PR/MR before the approved refinement is persisted.
- Never open a PR/MR unless development is complete and both QA and SRE pass in the same iteration.
- Always obtain user choices through **ask**; do not silently select track, repository, slug, or
  refinement approval.
- Keep user interaction in pt-BR. Source code, comments, docstrings, schemas, and repository
  documentation follow the repository language contract (English).
- Do not duplicate an external side effect when resuming; verify issue, branch, and PR/MR state
  before retrying.
