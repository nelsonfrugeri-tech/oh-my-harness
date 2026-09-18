---
name: reviewer
description: >-
  Workflow of the reviewer session mode. Triages the change, runs the needed specialists as
  independent parallel reviewers, proves each BLOCKER or MAJOR that needs proof in its own worktree
  and environment, meta-reviews the findings, and compiles one report with the review skill's
  canonical verdict for the developer in another session or harness. Use when the reviewer agent
  runs as the session agent, or when the user explicitly asks for a triaged multi-specialist review.
  Do not use for an author self-check or a single-pass review.
metadata:
  type: workflow
  version: 1.0.0
  origin: native
  last_verified: 2026-09-18
---

# Reviewer

Give the user one trustworthy review of a change and a conversation about it. Apply
[modes.md](../developer/references/modes.md) for tiers, triage, isolation, and handoff, and
[review](../review/SKILL.md) for the frame, severities, finding shape, and canonical verdict.

## Guard the boundary

- The user triggers the review. The code under review stays read-only: never edit the reviewed
  worktree or branch.
- The latest plan revision, read through `knowledge-base`, is the Spec. The developer's conformance
  matrix is input, never a verdict.

## Review

1. **Frame.** Resolve the diff and base per `review`, the plan revision, and the latest conformance
   matrix and prior review report in the handoff directory.
2. **Assess and triage.** Read the diff, then call the specialists it needs, such as `architect`,
   `software-engineer`, or `ai-engineer` when AI is involved, and announce the call. Apply the
   calibration rule on every fifth review.
3. **Fan out.** Run the called specialists in parallel, each with the `review` skill and a brief
   naming the diff range, plan revision, focus area, and the requirement to return only
   evidence-complete findings.
4. **Prove.** For a BLOCKER or MAJOR whose impact needs proof, create your own worktree at the
   reviewed head, bring the full environment up in isolation per modes.md, and run the end-to-end
   check that shows the problem. A simpler finding needs no infrastructure.
5. **Meta-review.** Judge every returned finding before accepting it. Hold the severity bar to the
   key results and correctness; a reviewer asked to find gaps always finds some, so drop noise,
   merge duplicates, and downgrade unsupported severity. Optionally ask `evidence-reviewer` to audit
   contested findings.
6. **Compile.** Write one report with the canonical verdict from `review`, add the triage line and
   the proof environment, save it as the next `review-<round>.md` in the handoff directory, and give
   the user its path.

Leave any proof environment up for manual testing with its owner, label, expiry, and teardown
command. Never load production secrets into it.

## Converse

After the report, switch to conversation: simple, direct prose, one point at a time, answering the
user's questions before moving on.

## Loop

The developer fixes the findings in developer mode, ideally in another session or harness, reading
the report by path. On re-review, check each prior finding against the new diff first, then review
what changed.
