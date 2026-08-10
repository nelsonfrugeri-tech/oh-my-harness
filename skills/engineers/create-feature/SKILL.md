---
name: create-feature
description: |
  Run the create-feature workflow after technical refinement: tech-pm user story,
  developer or ai-engineer implementation, qa and sre validation loop up to 3 iterations,
  then open a Pull/Merge Request or escalate. Use when the user asks to build a feature
  from an existing refinement or requests the create-feature pipeline.
---

# Create Feature

Orchestrate a refined feature through delivery without binding the workflow to one harness,
code host, or memory provider.

## Required inputs

- `featureName`: human-readable name.
- `featureSlug`: branch-safe slug derived from the name when absent.
- `refinementContent`: the approved technical refinement.
- `track`: `developer` by default, or `ai-engineer` for AI/ML work.
- `repo`: repository identity inferred from Git when absent.

Do not start implementation until the name, slug, and refinement are available.

## Portable orchestration

Resolve roles through the harness agent mechanism. Use `tech-pm` for the user story,
`developer` or `ai-engineer` for implementation, and `qa` plus `sre` for validation.
When a role cannot be delegated, stop and report the missing capability instead of silently
changing ownership.

Resolve remote issues and Pull/Merge Requests through the abstract `code-host` capability.
If it is unavailable, continue only through the reversible local phases and report remote
publication as pending. Never invent a provider-specific command or tool.

Persist curated stories and evidence through the abstract `memory` capability or the
`knowledge-base` agent. If neither is available, keep the material in the workflow result and
report persistence as pending. Never write directly into the knowledge-base bundle.

## Workflow

1. **User story** — `tech-pm` produces an INVEST story, 3–6 Given/When/Then acceptance
   criteria, and a Definition of Done. Create the remote issue only through `code-host`.
2. **Development** — the selected implementer creates `feature/<featureSlug>`, implements the
   refinement, adds focused tests, and runs the repository's discovered quality commands.
3. **Validation** — run `qa` and `sre` in parallel for up to three iterations. Both must pass.
   Store evidence only through `memory`; otherwise retain it in the result.
4. **Fix iteration** — return concrete QA/SRE findings to the same implementer and branch.
   Stop when a decision requires user input.
5. **Publication** — after validation passes, request explicit authorization for any outward
   action required by the applicable policy, then open the Pull/Merge Request through
   `code-host`.

## Result states

- `success`: the Pull/Merge Request was created.
- `ready_for_remote`: local work passed but `code-host` is unavailable or unauthorized.
- `blocked_at_development`: implementation needs a user decision.
- `blocked_at_fix`: a validation finding needs a user decision.
- `failed_max_iterations`: three validation iterations completed without joint approval.

## Pull/Merge Request body

Include a short summary, the main changes, acceptance criteria, QA/SRE evidence references,
verification commands, and an explicit checklist. Never claim evidence was persisted or a
remote action succeeded without a returned identifier.

## Legacy contract

`references/create-feature.ts` contains a provider-neutral schema reference. It is not a
standalone executable workflow and must not be treated as a harness adapter.
