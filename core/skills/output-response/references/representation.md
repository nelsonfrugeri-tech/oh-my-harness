# Representation

Choose the smallest representation that materially reduces cognitive effort without changing any
fact, label, provenance, uncertainty, or decision already established by the claim record.

Representation is presentation only. It must not acquire evidence, introduce a claim, alter
certainty, resolve a conflict, invent a metric, or choose the underlying decision. If the claim
record is not complete, do not format uncertain content into apparent authority.

## Apply the visual guard

Use prose when the answer is one fact, one direct mapping, or one sentence with no relationship that
a visual clarifies. Use a list only for parallel items or a short sequence where connectors add no
meaning. A request for a large diagram does not override this guard; if the user explicitly asked
for a visual, briefly explain why omitting it is clearer.

Otherwise select exactly one primary form with this rubric:

| Relationship in established content | Representation | Activation test |
| --- | --- | --- |
| Repeated items with the same fields | Table | Readers would otherwise scan the same labels three or more times. |
| Dependent steps or state transitions | Flow | Three or more steps depend on prior outcomes or branch. |
| Change ordered by time | Timeline | Event order or elapsed intervals determine meaning. |
| Ownership, containment, or nesting | Tree | Parent-child structure is harder to recover from prose. |
| Screen or spatial arrangement | Wireframe | Position, grouping, or interaction zones are part of the explanation. |
| None of these | Prose or list | A visual would only decorate the answer. |

Use a second form only when it explains a different material relationship. Do not turn simple prose
into a table merely because several nouns appear. In a long answer, use at least one useful visual
when it shows a sequence, hierarchy, comparison, dependencies among three or more elements, or
quantitative data; length alone never justifies one.

## Render without semantic drift

1. Lead with the conclusion.
2. Preserve the exact label and source boundaries of every claim.
3. Include every material node, branch, field, or state required to understand the relationship.
4. Mark unknown, conflicting, unavailable, and not-applicable values explicitly.
5. Keep labels short, define unfamiliar abbreviations once, and add one sentence interpreting the
   visual.
6. For quantitative content, render only values whose provenance already satisfies the evidence
   contract, including unit, population or denominator, observation window, source, and method;
   preserve scale and proportionality and never infer causality from visual proximity.

Prefer terminal-native ASCII for text conversations. Use a wireframe only for spatial questions, not
as a generic box diagram. Tables and diagrams do not count toward the character budget, so move
repeated fields into a table instead of cutting material content.

## Verify the representation

Before sending, check:

- removing the visual would make the relationship materially harder to understand;
- every visual element maps to established content;
- no formatting changed certainty or hid a limitation;
- branch direction, time order, hierarchy, and table fields are unambiguous;
- prose, list, table, flow, timeline, tree, or wireframe was chosen by the rubric rather than style.

Keep progressive disclosure: direct answer, essential representation, then limitations or action.
Explainability means exposing the concise evidence-to-conclusion mechanism, never private
chain-of-thought.
