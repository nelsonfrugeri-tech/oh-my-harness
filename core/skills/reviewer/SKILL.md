---
name: reviewer
description: >-
  Workflow of the reviewer session mode. Reviews what the user points it to, an open pull request
  or unpushed code in a local worktree: triages the change, runs the needed specialists as
  independent parallel reviewers, tests before commenting, proves each BLOCKER or MAJOR that needs
  proof in its own worktree and environment, meta-reviews the findings, comments inline, reports in
  the terminal with the review skill's canonical verdict, and marks a draft pull request ready when
  no BLOCKER remains. Use when the reviewer agent runs as the session agent, or when the user
  explicitly asks for a triaged multi-specialist review. Do not use for an author self-check or a
  single-pass review.
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

- The user triggers the review and says what to review: an open pull request, or unpushed code in
  a local worktree. The code under review stays read-only: never edit, commit to, or push the
  reviewed worktree or branch. Review comments and the ready-for-review transition through
  `code-host` are the only writes to the reviewed change.
- The Spec is the latest plan revision, read through `knowledge-base`. On the fast lane, the Spec
  is the one-sentence request recorded in the conformance matrix of the pull request description;
  when neither exists, fall back to the Spec discovery order of `review`.
- The pull request title, description, and conformance matrix are input, never a verdict.
- On scope, design direction, and preferences, the plan is the arbiter: its objective, key
  results, and the decisions settled in the discoverer's session. A suggestion that would take the
  change beyond or against the plan is a proposal for the user and the discoverer, marked as out of
  plan, never a required fix, and it cannot block the pull request alone.
- A proven Standards defect, such as a correctness, security, data-loss, or reliability defect,
  keeps its severity even when the plan did not foresee it, per `review`. Report it with its
  severity; when its fix would change scope, say so, so the user and the discoverer can decide the
  scope while the defect still counts.
- When a proven finding invalidates a decision, key result, or scenario of the plan, or matches its
  `Falsifying result`, say in the comment that it falsifies the plan and name the plan item. The
  pull request stays draft until the discoverer's new revision is approved, and the next review
  uses that revision as the Spec.
- Never write the review, its findings, or its verdict to the knowledge base.

## Review

1. **Frame.** Resolve the diff and base per `review`: the pull request, or the local worktree
   against its base. Read the plan revision, and the pull request title and description when a
   pull request exists. Use its review guide and "where to look hardest" as the starting reading
   order, never as the limit of the review; a missing or unclear explanation is itself a finding.
   On re-review, read your earlier comments first.
2. **Assess and triage.** Read the diff, then call the specialists it needs, such as `architect`,
   `software-engineer`, or `ai-engineer` when AI is involved, and announce the call. Apply the
   calibration rule of modes.md.
3. **Fan out.** Run the called specialists in parallel, each with the `review` skill and a brief
   naming the diff range, plan revision, focus area, and the requirement to return only
   evidence-complete findings.
4. **Prove before commenting.** Reproduce each finding before commenting on it, and attach a proof
   the developer can rerun, matched to the kind of claim:
   - behavior: a failing test, or the end-to-end check with its command and output;
   - structure, such as a contract, architecture, or consistency defect decided by inspection: a
     reproducible static check, with the `file:line` references and the command that shows it;
   - purely textual, such as a typo or wording: the line itself.

   For a BLOCKER or MAJOR whose impact depends on the runtime, create your own worktree at the
   reviewed head, bring the full environment up in isolation per modes.md, and run the end-to-end
   check that shows the problem. When a claim cannot be proven, say so in the comment and keep its
   uncertainty, per `review`.
5. **Meta-review.** Judge every returned finding before accepting it. Hold the severity bar to the
   key results and correctness; a reviewer asked to find gaps always finds some, so drop noise,
   merge duplicates, and downgrade unsupported severity. Optionally, to audit contested findings,
   ask the `evidence-reviewer` agent.
6. **Comment inline.** On a pull request, post every finding as an inline review comment on a diff
   line through `code-host`, never as a loose general comment. A finding with no line of its own,
   such as an architecture concern or missing code, anchors on the nearest changed line and
   explains why it sits there. For local code, every finding carries `file:line` in the terminal
   report.
7. **Report and transition.** Write the report in the terminal with the canonical verdict from
   `review`, the triage line, and the proof environment. On a pull request, submit the comments as
   one comment-only review (event `COMMENT`, because a code host may reject approve or
   request-changes from the pull request's author) whose summary carries the verdict and the marker
   line
   `Reviewed with the oh-my-harness reviewer mode.` that calibration counts. With no BLOCKER and no
   pending plan revision, mark the draft pull request ready for review through `code-host` and say
   so in the report. With a BLOCKER, it stays draft and the loop continues. With a finding of any
   severity that falsifies the plan, it stays draft until the discoverer's new revision is
   approved, the developer resumes, and you review the new diff against that revision.

## Police the code organization

Check the diff against
[organize code by domain](../implement/references/way-of-building.md#organize-code-by-domain), which
holds the caps and their exemptions. Each rule is one checkable item, and these are the default
severities where the repository has adopted this specification: a greenfield project, or a plan that
declares it as the code standard. Everywhere else, follow the repository's own convention and report
a deviation from this reference as a proposal, never as a required fix.

Adoption establishes that a rule applies, not what one occurrence costs, so `review` still owns
severity: every finding carries the impact you measured in this repository, and when the occurrence
costs less than the default says, downgrade the default with that evidence in the comment. Never
raise a severity without measured impact, and never downgrade one without it either.

| Finding in the diff | Severity |
| --- | --- |
| Layer violation, or a domain that imports a framework, I/O, or a model client | MAJOR |
| Business rule outside the domain | MAJOR |
| Function over the length cap | MAJOR |
| Class over the public-method cap, with no exemption | MAJOR |
| Assets or documentation mixed with the modules that use them | MINOR |
| Module with more than one responsibility, or a vocabulary to split by family | MINOR |
| Stateless class with public methods | MINOR |
| Missing re-evaluation of an oversized file | MINOR |
| Unnecessary comment or docstring | NIT |

Anchor each finding at `file:line` with the measured number: the counted lines, the counted public
methods, or the import that crosses the layer. This is a structural finding, so the proof is the
reproducible static check of step 4. File size alone is never a finding.

## Write comments that help

Every comment is clear, didactic, propositive, and collaborative. In this order:

- the severity from `review`;
- the problem in one sentence;
- the evidence, written so the developer can rerun it: the test or end-to-end command with its
  output, the static check with its `file:line` references, or, for a purely textual comment, the
  line itself;
- a concrete proposal, preferably a suggested change the developer can apply directly.

Phrase it as a proposal or a question about the code, never as a verdict on the person. The
terminal report keeps the canonical finding shape of `review`.

Leave any proof environment up for manual testing with its owner, label, expiry, and teardown
command. Never load production secrets into it.

## Converse

After the report, switch to conversation: simple, direct prose, one point at a time, answering the
user's questions before moving on.

## Loop

The developer answers the findings in developer mode, ideally in another session or harness, when
the user points it to the comments. On re-review, read the developer's replies first: rerun your
proof against each fix and resolve the thread only when the proof no longer reproduces; answer a
disagreement with evidence in the same thread. Then review what changed.

When the pull request is merged or the user ends the process, destroy everything you created per
modes.md.
