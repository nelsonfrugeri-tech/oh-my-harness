---
name: didactic-visual
description: >-
  Chooses the clearest final representation for an already established explanation: prose, list,
  table, flow, timeline, tree, or wireframe. Use when relationships, sequence, hierarchy, repeated
  fields, or spatial layout would be materially easier to understand visually. Do not use for
  decoration, fact finding, claim reclassification, or repository documentation.
metadata:
  type: capability
  version: 2.0.0
  origin: native
  last_verified: 2026-09-06
---

# Didactic Visual

Choose the smallest representation that materially reduces cognitive effort without changing any
fact, status, provenance, uncertainty, or decision established by `evidence`.

## Prerequisite: evidence first

Load `oh-my-harness:evidence` before representation. In a plugin-only installation, the absence of
a global evidence contract is not a blocker when the evidence skill itself is available. If evidence
is unavailable, do not format uncertain content into apparent authority; report the missing
prerequisite.

This skill owns presentation only. It must not acquire evidence, introduce a claim, alter certainty,
resolve a conflict, invent a metric, or choose the underlying decision.

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
into a table merely because several nouns appear.

## Render without semantic drift

1. Lead with the conclusion.
2. Preserve the exact claim status and source boundaries from `evidence`.
3. Include every material node, branch, field, or state required to understand the relationship.
4. Mark unknown, conflicting, unavailable, and not-applicable values explicitly.
5. Keep labels short, define unfamiliar abbreviations once, and add one sentence interpreting the
   visual.
6. For quantitative content, render only values whose provenance already satisfies the evidence
   contract, including unit, population or denominator, observation window, source, and method;
   preserve scale and proportionality and never infer causality from visual proximity.

Prefer terminal-native ASCII for text conversations. Use a wireframe only for spatial questions, not
as a generic box diagram.

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
