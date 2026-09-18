# Pull Request

The pull request is how the developer explains the delivery. Contextual explainability comes first:
a reviewer who never saw the plan or the session must understand what changed, why, how it was
proven, and where to look, without asking. Write with extreme didactics in the user's language:
answer first, then detail in layers; short paragraphs; a table or diagram per `didactic-visual`
wherever sequence, comparison, or structure is easier to see than to read.

## Title

The outcome for the user of the feature in one line, naming what it replaces when it replaces
something. Never the list of files touched.

## Description

Use these sections in this order. Keep a section short when the change is small, and drop a section
only when it would be empty; on the fast lane, sections 3 to 5 are usually one or two lines.

1. **TL;DR.** What changes, in two or three sentences, and anything breaking.
2. **Why.** The problem, with the evidence that shows it: the plan objective and key results, an
   incident, a failing run, a measured cost. Say where each fact comes from.
3. **Design.** The approach in plain prose, with a diagram when components or a flow change. Say
   what each new piece produces and where it lives.
4. **Decisions.** One table: decision, why, alternative rejected. Include every choice a reviewer
   could reasonably question.
5. **Review guide.** The reading order, from contract to details, grouping files by step. Mark
   generated files and name their source, so the reviewer reads the source instead.
6. **Where to look hardest.** One table: risk, where, what to check. Put the riskiest assumptions
   here, not in a footnote.
7. **How to verify.** The exact commands to run the gates and the environment locally.
8. **Verification done.** The conformance matrix below, and each command actually run with its
   result. Never list a command that did not run.
9. **Not verified.** Every open gap, unexecuted check, and hypothesis, with the cheapest observation
   that would settle it.

## Conformance matrix

The matrix is an author self-check and input to independent review. Explain each row in words a
reviewer can check, not only a status.

```markdown
## Conformance: <project> / <feature> - plan revision <n | fast lane> - round <r>

| Plan item | Expected | Observed | Evidence |
| --- | --- | --- | --- |
| Objective | <objective, or the one-sentence request on the fast lane> | <met / not met> | <observation> |
| KR1 | <target> | <observed value> | <method, command, output> |
| S1 | <scenario> | <pass / fail> | <test name and run output> |
| AC1 | <criterion> | <pass / fail> | <command and result> |

**Nothing beyond the plan:** <none, or each extra change with its justification>
**Deviations:** <none, or each one with the user's decision>
**Environment:** <owner, label, endpoints, teardown command>
**Status:** <completed | partially-completed | blocked>
```

## Each round

After fixing review findings, update the description rather than appending to it: the TL;DR, the
matrix with the next round number, and the verification and gaps sections must describe the pull
request as it is now.
