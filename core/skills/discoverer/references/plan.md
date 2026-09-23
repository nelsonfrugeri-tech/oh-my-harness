# Feature Plan

The plan is the contract between the session modes. The `discoverer` writes it, the `developer`
builds against it, and the `reviewer` uses it as the Spec. It is written OKR-style: the objective
says what the delivery is, the key results say how its success is measured. Every plan has the same
fields in the same order. A field with no content says `none`; a value not yet known says
`unknown`. Never invent a baseline.

## Template

```markdown
# Plan: <project> / <feature> - revision <n>

- **Project:** <canonical project name>
- **Feature:** <feature slug>
- **Revision:** <n>, supersedes <n-1 or none>
- **Fast lane:** <yes | no> - <the signal that decided it>
- **Approved by:** <the user who approved this revision, or pending>

## Objective
<what the delivery is: one outcome, stated for the user of the feature>

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

## Alternatives
- <option considered> - <trade-off against the objective and key results> - <why it was not chosen>

## Folder layout and reuse
- Reused: <path> - <what it provides>
- New: <path> - <one-line responsibility>; <why reuse does not fit>

## Architecture
- Bounded contexts: <name> - <what it owns, and what it does not>
- Layers: <layer> may import <layer>; the domain imports no framework, I/O, or model client
- Directory tree: <every directory and file, one file type per directory, with each component's asset subdirectory>
- Business rules:
  | Rule | Module that owns it | Form |
  | --- | --- | --- |
  | <rule in the domain's language> | <path> | <function | class | data type> |

## Domain entities
- <entity or value>: <fields with units, and invariant>; relates to <entity> as <relationship>
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

## Falsifying result
- <the observation that would show this plan is wrong, and what it triggers: a deviation returned to the user, or a new discovery>
```

The `Architecture` fields and the relationships between domain entities are required, designed
against [organize code by domain](../../implement/references/way-of-building.md#organize-code-by-domain):
a plan without them is not ready.

Every requirement from the sources is an acceptance criterion marked mandatory or optional with the
exact line that says so. Never downgrade a mandatory one by assumption; re-check the list when a
source changes. Every key result maps to at least one scenario, and every scenario names its key
result. Use an integration scenario when behavior crosses persistence, network, or process
boundaries. Use an eval only when LLM behavior is in scope: deterministic when the output has a
checkable property, probabilistic when quality needs a judge or a sample.

## Persist and read

- Only `knowledge-base` persists the plan, and the plan is the only thing the modes persist there.
  Brief it with the full plan as an immutable note of `knowledge_type: decision`, project
  `<project>`, topic `<feature>`, and tags `plan` and `revision-<n>`.
- The note body follows the decision body contract of `kb-write`: a brief context paragraph, then
  the approved plan verbatim inside one fenced `markdown` code block, so its tables stay within the
  minimal formatting that contract allows. The plan's fields cover that contract: the objective and
  refinement are the choice; `Alternatives` holds the alternatives and trade-offs; key-result
  baselines hold the evidence; `Approved by`, scenarios, and acceptance criteria hold the owner and
  validation; revision and supersession hold the review path; and `Falsifying result` holds the
  falsifier.
- Create a new revision only at a milestone: plan approved, deviation accepted, or key result
  changed. The new note supersedes the previous revision through `supersedes`.
- Readers ask `knowledge-base` for the latest non-deprecated plan of the project and feature, read
  back the fenced plan exactly as approved, and cite its revision number in every artifact that
  depends on it.
- Progress, conformance, review rounds, and the final result are not written to the knowledge
  base. They live in the pull request, the terminal, and the repository.
