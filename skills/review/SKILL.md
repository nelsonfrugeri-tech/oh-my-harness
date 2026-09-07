---
name: review
description: >-
  Independently reviews a code diff, branch, pull request, or implementation artifact against both
  observable engineering Standards and its stated Spec, then emits evidence-anchored findings and
  a mechanical merge recommendation. Use for code review and quality-gate decisions. Do not use
  for an author's self-check, implementation, or a non-code evidence audit.
metadata:
  type: capability
  version: 2.0.0
  origin: native
  last_verified: 2026-09-06
---

# Review

Produce an independent, read-only assessment in which Standards defects and Spec mismatches remain
visible as separate evidence paths. Apply `evidence` to every material claim and limitation.

## Guard the boundary

- Review code and implementation artifacts; do not modify them unless the user separately assigns
  correction work to an authoring agent.
- An author self-check is useful input, never independent approval. State the independence limit if
  the reviewer authored the change or cannot establish reviewer separation.
- Use the canonical code-review contract below for merge or production decisions. For claims,
  reports, research, or architecture decisions, read
  [evidence-audit.md](references/evidence-audit.md) instead; do not invent Standards/Spec axes.
- Load a language risk reference only when that language is in the diff and repository tooling does
  not already decide the question: [Python](references/checklist-python.md) or
  [TypeScript](references/checklist-typescript.md).
- Keep project rules authoritative. Do not impose vendor preferences, generic style doctrine, or
  thresholds absent from the repository or measured workload.

## Establish the review frame

Record the exact fixed point, reviewed head or artifact, scope, and available evidence before
forming a verdict.

1. Resolve a user-supplied patch or range exactly as supplied unless it is internally inconsistent.
2. For a branch or pull request, identify the intended target branch from explicit task or remote
   metadata, resolve its merge base with the reviewed head, and inspect the three-dot diff. Do not
   assume a branch name or substitute the current checkout silently.
3. For staged or working-tree review, distinguish `HEAD..index`, `index..working tree`, and
   untracked files. State which sets are included.
4. If the base, head, diff, generated source, or required artifact cannot be resolved, stop the
   affected pass and report it as not assessed. Never approve a diff you could not inspect.
5. Read the complete diff, then only the surrounding code, tests, contracts, generated sources, and
   callers needed to understand behavior. Separate generated or lock-file noise from source-owned
   behavior without ignoring dependency or supply-chain changes.

Keep review commands read-only by default. Discover project-native check commands, inspect their
effects, and prefer check/dry-run modes. Do not install packages or invoke package executors such as
`npx` merely to obtain a reviewer tool. A missing tool is an explicit limitation, not permission to
mutate the environment or replace the gate silently.

## Resolve the two evidence axes

### Standards

Discover binding standards from repository instructions, public contracts, configured lint/type/
test/build gates, CI, nearby conventions, and risk-specific skills. Inspect observable correctness,
security, data integrity, compatibility, reliability, tests, maintainability, performance, and
architecture. A formatter-owned preference is not a finding unless observed output violates a
project contract or the formatter is missing from the effective gate.

### Spec

Discover intent in this order: explicit user request; issue or pull-request body; acceptance
criteria; ADR or design document; compatibility/migration contract; then tests or stable public
behavior that clearly encode intent. Record sources used and artifacts absent.

Tests may establish an inferable Spec when their intent is unambiguous. If required intent remains
materially ambiguous or unavailable, mark the Spec pass `not assessed`; do not infer conformance
from Standards quality. An explicit Standards-only request is the sole mode where Spec is not
required.

Run each pass independently: neither pass may treat the other's success as evidence. A defect found
by both passes is one finding with one primary axis and the other as `Related axis`; preserve both
evidence paths and the higher supported severity.

## Classify supported findings

- **BLOCKER:** an observed security vulnerability, data-loss risk, critical correctness defect, or
  breaking compatibility change without its required migration/versioning. Blocks merge.
- **MAJOR:** an observed material reliability, performance, testing, error-handling, or architecture
  defect that requires explicit disposition before production.
- **MINOR:** a non-blocking maintainability or quality defect with a concrete impact.
- **NIT:** an optional preference or trivial consistency improvement. Never present it as required.

Severity follows demonstrated impact in this repository, not a generic category. Unsupported
security claims, hypothetical scale problems without a relevant workload, and style preferences
must be verified, narrowed, downgraded, or omitted. Do not hide an uncertain claim inside confident
language; retain its uncertainty and identify what observation would resolve it.

Every finding uses this canonical shape:

```markdown
[<SEVERITY>][<PRIMARY AXIS>] <short actionable title>

**Related axis:** <Standards | Spec | None>
**File:** <path>:<line or smallest inspectable range>
**Evidence:** <diff/context/command/spec observation; distinguish observed from inferred>
**Issue:** <specific defect or mismatch>
**Impact:** <observable consequence if it ships>
**Smallest correction:** <minimal viable remediation>
**Verify:** <test, inspection, or evidence that resolves the finding>
```

Suggested code is optional and must be checked against surrounding context. Findings without an
inspectable location, evidence, impact, correction, or verification are incomplete and cannot
control the recommendation.

## Derive the recommendation mechanically

Apply these conditions in order:

1. Any supported BLOCKER in either assessed axis: `BLOCK MERGE`.
2. Otherwise, if a required diff/base is unavailable, or Spec is required but unavailable or
   materially ambiguous: `INCOMPLETE — SPEC NOT ASSESSED`.
3. Otherwise, any MAJOR in either axis: `APPROVE WITH CAVEATS`; list the explicit disposition needed
   before production.
4. Otherwise, when both required axes were assessed: `APPROVE`.
5. In explicit Standards-only mode, apply the same severity rules to Standards and state
   `Scope: Standards only`; never imply Spec conformance.

Keep each axis verdict visible even when an earlier condition determines the overall result. Count
deduplicated findings once under their primary axis. Write `No findings.` only when every axis
required by the declared scope was assessed.

## Emit the canonical result

```markdown
# Code Review

**Recommendation:** <BLOCK MERGE | APPROVE WITH CAVEATS | APPROVE | INCOMPLETE — SPEC NOT ASSESSED>
**Scope:** <Standards + Spec | Standards only | explicitly limited scope>
**Comparison base:** <merge-base...head, staged/working-tree sets, or inspected artifact>
**Evidence:** <diff, files, tests, commands, issue/spec inspected and unavailable artifacts>
**Independence:** <independent reviewer identity or explicit limitation>

## Standards verdict

<Pass, findings, or not assessed, with one-sentence reason>

## Spec verdict

<Pass, findings, not assessed, or not requested, with one-sentence reason>

## Findings

<Findings ordered by BLOCKER, MAJOR, MINOR, NIT using the canonical finding template.
Write “No findings.” only when every required axis was assessed.>

## Summary

**Counts:** <n> BLOCKER, <n> MAJOR, <n> MINOR, <n> NIT
**Required before merge:** <actions or “None”>
**Required before production:** <actions or “None”>
**Residual risk / unverified:** <material limitations or “None identified in assessed scope”>
```

Positive highlights may follow the findings when useful, but never replace scope, axis verdicts,
counts, limitations, or required actions.

## Stop and report

Finish when the complete scoped diff has two independent passes (or explicit Standards-only scope),
every material finding is evidence-complete, duplicates preserve axis provenance, project-native
read-only checks have run or are named as unavailable, and the recommendation follows the table.
Report partial coverage honestly; more prose cannot compensate for an unreadable base or missing
required Spec.

## Maintenance triggers

Re-evaluate this skill when a review incident exposes axis masking or severity drift, repository
platforms change comparison-base semantics, project tooling takes ownership of a repeated check, or
paired evaluations show that an external mechanism improves defect detection without losing the
canonical output contract.
