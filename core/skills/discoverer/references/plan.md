# Feature Plan

The plan is the contract between the session modes. The `discoverer` writes it, the `developer`
builds against it, and the `reviewer` uses it as the Spec. Every plan has the same fields in the
same order. A field with no content says `none`; a value not yet known says `unknown`. Never invent
a baseline.

## Template

```markdown
# Plan: <project> / <feature> - revision <n>

- **Project:** <canonical project name>
- **Feature:** <feature slug>
- **Revision:** <n>, supersedes <n-1 or none>
- **Fast lane:** <yes | no> - <the signal that decided it>

## Objective
<one outcome, stated for the user of the feature>

## Key results
| KR | Metric | Method | Target | Baseline |
| --- | --- | --- | --- | --- |
| KR1 | <unit and population> | <how it is measured> | <value> | <value with source, or unknown> |

## Scenarios
| ID | KR | Scenario | Level |
| --- | --- | --- | --- |
| S1 | KR1 | <given, when, then> | <unit | integration | eval-deterministic | eval-probabilistic> |

## Acceptance criteria
- <mandatory | optional> <observable criterion> - source: "<exact source line>" - proof: <command or check>

## Out of scope
- <what this feature will not do>

## Folder layout and reuse
- Reused: <path> - <what it provides>
- New: <path> - <one-line responsibility>; <why reuse does not fit>

## Domain entities
- <entity or value>: <fields with units, and invariant>
- Port <name>: <operations the consumer needs>
- Outcomes of <use case>: <one named type per result the caller handles differently>

## Code standard
- Way-of-building revision: <oh-my-harness version or commit that supplied way-of-building.md>
- Concerns that fell back to it: <list, or none>

## Environment contract
- Up: <command>
- E2E: <command and the evidence it produces>
- Down: <command>

## Open unknowns
- <unknown, its impact, and the cheapest observation that resolves it>
```

Every requirement from the sources is an acceptance criterion marked mandatory or optional with the
exact line that says so. Never downgrade a mandatory one by assumption; re-check the list when a
source changes. Every key result maps to at least one scenario, and every scenario names its key
result. Use an
integration scenario when behavior crosses persistence, network, or process boundaries. Use an eval
only when LLM behavior is in scope: deterministic when the output has a checkable property,
probabilistic when quality needs a judge or a sample.

## Persist and read

- Only `knowledge-base` persists the plan. Brief it with the full plan as an immutable note of
  `knowledge_type: decision`, project `<project>`, topic `<feature>`, and tags `plan` and
  `revision-<n>`.
- Create a new revision only at a milestone: plan approved, deviation accepted, or key result
  changed. The new note supersedes the previous revision through `supersedes`.
- Readers ask `knowledge-base` for the latest non-deprecated plan of the project and feature, and
  cite its revision number in every artifact that depends on it.
- Progress, such as slices, test runs, and review rounds, is not versioned in the knowledge base.
  When the feature ends, persist one consolidated result as `knowledge_type: reference`: the final
  plan revision, the conformance summary, the final review verdict, and accepted deviations.
