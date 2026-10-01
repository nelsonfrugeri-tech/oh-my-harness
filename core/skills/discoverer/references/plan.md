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
| S1 | KR1 | <given, when, then> | <unit, integration, eval-deterministic, or eval-probabilistic> |

## Acceptance criteria
- <mandatory | optional> <observable criterion> - source: "<exact source line>" - proof: <command or check>

## Out of scope
- <what this feature will not do>

## Alternatives
- <option considered> - <trade-off against the objective and key results> - <why it was not chosen>

## Reuse
- Reused: <path> - <what it provides>
- New: <path> - <one-line responsibility>; <why reuse does not fit>

## Architecture
- Bounded contexts: <name> - <what it owns, and what it does not>
- Layers: <layer> may import <layer>; the domain imports no framework, I/O, or model client
- Directory tree: <every directory and file the change creates, with each component's asset subdirectory and no asset inside a module directory>
- Business rules:
  | Rule | Module that owns it | Form |
  | --- | --- | --- |
  | <rule in the domain's language> | <path> | <function, class, or data type> |

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

- Only `knowledge-base` persists the plan, and the plan is the only mode artifact stored there.
  Use `<scope>/<domain>/plans/<feature>/<feature>.md`, `type: decision`, tags identifying the plan,
  and the schema's required decision sections. Preserve the approved plan verbatim inside a fenced
  Markdown block in the appropriate section; supply the surrounding schema sections meaningfully.
- Persist through kb-write pending review. The principal shows the full note or diff and asks for
  explicit approval; approval of a plan supplies its path, not permission to publish unseen changes.
- Create revisions only at milestones: plan approved, deviation accepted, or key result changed.
  An update keeps id and created_at, increments version, and freezes the prior version in .history/
  with superseded_reason only when the pending revision is approved.
- Readers ask knowledge-base for the latest active approved plan, read its fenced content exactly,
  and cite the revision in dependent artifacts. Pending changes are not the implementation contract.
- Progress, conformance, review rounds, and final results live in the PR, terminal, and repository,
  never as derivative session JSON in the knowledge bundle.
